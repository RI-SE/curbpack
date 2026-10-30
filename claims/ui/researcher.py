"""Researcher overview, requirement findings, and the product-file view."""

from __future__ import annotations

import html
import json
from urllib.parse import quote

from app.pages import page
from checks.labels import CAPTIONS, check_caption
from claims.bind import law_passages
from discovery.present import merge_findings

COLUMN_HELP = {
    "Evidence Source": "A product file that may support this requirement. The name opens the file.",
        "Motivation": (
        "The saved claim motivation. When this discovery sentence differs, "
        "the saved text is red and struck through, and the new sentence is green. "
        "Click the red text to keep it. Click the green text to use it."
    ),
    "Checks": "Checks on this file. Saving a check writes the claim.",
    "Review": "Useful or poor is a mark on this finding. It is not stored on the claim.",
}
SCORE_HELP = (
    "A model reads the requirement text and the first 12,000 characters of this evidence source, "
    "at temperature 0. It returns a number from 0 to 1 and a rank: High, Medium, or Low. "
    "The program does not convert the number into the rank; the model chooses both. "
    "Current product material scores higher than planned, roadmap, or FUTURE_ material. "
    "A source that assesses risks, such as a table, STRIDE, or residual risk, scores higher than one that only mentions security. "
    "The number is that judgment of support. It is not a check result and not a decision that the product complies. "
    "A score of 0, or rank None, is left off this list."
)
from discovery.search import highlight_verified, verify_excerpt


def overview_page(model: dict) -> bytes:
    rows = []
    for item in model.get("rows") or []:
        findings = "—" if item.get("findings") is None else str(item["findings"])
        high = "—" if item.get("high") is None else str(item["high"])
        href = _req_href(model, item["id"])
        rows.append(
            "<tr>"
            f'<td><a href="{href}"><code>{html.escape(item["id"])}</code></a></td>'
            f"<td>{html.escape(item.get('locator') or '')}</td>"
            f"<td>{findings}</td>"
            f"<td>{int(item.get('claims') or 0)}</td>"
            f"<td>{high}</td>"
            f"<td>{_signature_cell(str(item.get('signing') or ''))}</td>"
            f"<td>{item.get('useful') or 0}</td>"
            f"<td>{item.get('poor') or 0}</td>"
            "</tr>"
        )
    section = html.escape(str(model.get("section_name") or model.get("source_id") or "this section"))
    repo = html.escape(str(model.get("repo_name") or model.get("repo_id") or ""))
    if model.get("pack_id"):
        place = f"Requirements in this pack for <strong>{repo}</strong>."
    else:
        copy = html.escape(str(model.get("timestamp") or ""))
        place = f"Requirements in this section for <strong>{repo}</strong>, copy <code>{copy}</code>."
    gap = (
        "<p class=\"muted\">Only requirements that have no Claim yet.</p>"
        if model.get("gap")
        else ""
    )
    body = f"""
<p class="muted"><a href="/discover">Discovery &amp; Claims</a></p>
<h1>{section}</h1>
<p class="muted">{place}
A <strong>finding</strong> is a product file Discover suggests for a requirement. It is not a Claim.
Open a requirement and <strong>add a check</strong> to make a Claim for that file.
<strong># Claims</strong> is how many Claims are saved for that requirement.
A human <strong>signs</strong> each Claim. <strong>Signature</strong> is that seal.
<strong>Source reference</strong> is the legal place on the requirement, such as the locator in the row.</p>
{gap}
{model.get('error_html') or ''}
<table>
<thead><tr><th>Requirement</th><th>Source reference</th><th>Findings</th><th># Claims</th><th>High</th><th>Signature</th><th>Useful</th><th>Poor</th></tr></thead>
<tbody>{''.join(rows) or '<tr><td colspan="8">No requirements in this working copy.</td></tr>'}</tbody>
</table>
"""
    return page(str(model.get("section_name") or "Discover claims"), body)


def requirement_page(model: dict) -> bytes:
    requirement = model.get("requirement") or {}
    requirement_id = str(requirement.get("id") or "")
    locator = _locator(requirement) or requirement_id
    source = requirement.get("source") if isinstance(requirement.get("source"), dict) else {}
    source_url = str(source.get("url") or "")
    instrument = str(source.get("instrument") or "").strip()
    identifier = str(source.get("identifier") or "").strip()
    law = "\n\n".join(law_passages(requirement))
    findings = _with_claims(
        _ordered(merge_findings(model.get("candidates") or [], model.get("marks") or {})),
        model.get("claims") or [],
        requirement_id,
    )
    model = {**model, "source_ids": _source_ids(requirement)}
    rows = []
    for index, item in enumerate(findings):
        rows.append(_hit_row(model, requirement_id, item, index))
    claim_count = sum(1 for item in findings if isinstance(item, dict) and item.get("has_claim"))
    has_candidates = any(isinstance(item, dict) and not item.get("has_claim") for item in findings)
    # Saved Claims stay visible. Candidates are opt-in so Discover noise does not hide them.
    checked = ""
    table_class = "hits-table"
    candidate_toggle = ""
    if has_candidates:
        candidate_toggle = (
            f'<label class="show-suggestions"><input type="checkbox" id="show-suggestions"{checked}> '
            "Show discovered claim candidates</label>"
        )
    hits = (
        f"{candidate_toggle}"
        f'<div class="hits"><table class="{table_class}"><thead><tr>'
        f"<th></th><th>Evidence Source{_tip(COLUMN_HELP['Evidence Source'])}</th>"
        f"<th>Score{_tip(SCORE_HELP)}</th>"
        f"<th>Motivation{_tip(COLUMN_HELP['Motivation'])}</th>"
        f"<th>Checks{_tip(COLUMN_HELP['Checks'])}</th>"
        f"<th>Review{_tip(COLUMN_HELP['Review'])}</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + _add_row(model, requirement_id)
        + "</tbody></table></div>"
        + (
            '<p class="muted">Click a row to expand the excerpt. The name opens the source.</p>'
            if findings
            else _empty_findings(model)
        )
    )
    notice = f"<p class='err'>{html.escape(model['notice'])}</p>" if model.get("notice") else ""
    outcomes = _outcomes(model.get("outcomes") or [])
    body = f"""
<div class="req-desk">
<p class="muted"><a href="{_overview_href(model)}">← Claims</a> · <code>{html.escape(str(model.get('repo_id') or ''))}</code></p>
<div class="req-head">
  <div>
    <h1>Claims Editor</h1>
  </div>
  <div class="req-badges">
    {_seal(str(model.get('signing') or ''))}
    <span class="pill">{html.escape(str(model.get('model') or 'not scored'))}</span>
  </div>
</div>
{_identity_card(model, instrument, identifier, locator, requirement_id, law, source_url)}
{notice}
{outcomes}
<h2>Claims ({claim_count})</h2>
<p class="muted">Saved Claims for this requirement are listed first. Discovered claim candidates come from Discover for the same requirement; they are suggestions, not Claims, until you add a check.</p>
{hits}
{_add_dialog(model, requirement_id)}
</div>
<script>
document.querySelectorAll("tr.hit-row").forEach((row) => {{
  row.addEventListener("click", (event) => {{
    if (event.target.closest("a, button, input, select, textarea, dialog, label")) return;
    const detail = document.getElementById(row.dataset.hit);
    if (!detail) return;
    const opening = detail.hidden;
    detail.hidden = !opening;
    row.classList.toggle("open", opening);
    const mark = row.querySelector(".col-toggle");
    if (mark) mark.textContent = opening ? "▾" : "▸";
  }});
}});
function fillCheckForm(form, values, index) {{
  const stored = form.querySelector('[name="edit_index"]');
  if (stored) stored.value = index == null ? "" : String(index);
  const kind = form.querySelector(".check-kind");
  if (kind) kind.value = (values && values.check) || kind.options[0].value;
  form.querySelectorAll("input[name]").forEach((input) => {{
    if (input.type === "hidden") return;
    if (input.type === "checkbox") {{
      input.checked = !!(values && values[input.name] === "1");
      return;
    }}
    input.value = (values && values[input.name]) || "";
  }});
  syncCheckForm(form);
}}
document.querySelectorAll(".check-open").forEach((button) => {{
  button.addEventListener("click", () => {{
    const dialog = button.parentElement.querySelector("dialog.checks");
    const form = dialog.querySelector("form.check-form");
    fillCheckForm(form, null, null);
    dialog.showModal();
  }});
}});
document.querySelectorAll(".check-edit").forEach((button) => {{
  button.addEventListener("click", () => {{
    const dialog = button.closest(".checks-wrap").querySelector("dialog.checks");
    const form = dialog.querySelector("form.check-form");
    fillCheckForm(form, JSON.parse(button.dataset.values || "{{}}"), button.dataset.index);
    dialog.showModal();
  }});
}});
document.querySelectorAll(".check-close").forEach((button) => {{
  button.addEventListener("click", () => button.closest("dialog").close());
}});
const addDialog = document.getElementById("add-candidate");
document.querySelectorAll(".add-open").forEach((button) => {{
  button.addEventListener("click", () => {{ if (addDialog) addDialog.showModal(); }});
}});
document.querySelectorAll(".add-close").forEach((button) => {{
  button.addEventListener("click", () => button.closest("dialog").close());
}});
function syncCheckForm(form) {{
  const check = form.querySelector(".check-kind");
  const selected = check ? check.value : "";
  form.querySelectorAll("[data-for]").forEach((el) => {{
    el.hidden = !el.dataset.for.split(/\\s+/).includes(selected);
  }});
}}
document.querySelectorAll("form.check-form").forEach((form) => {{
  syncCheckForm(form);
  form.addEventListener("change", () => syncCheckForm(form));
  form.addEventListener("input", (event) => {{
    if (event.target.classList) event.target.classList.remove("invalid");
  }});
  form.addEventListener("submit", (event) => {{
    form.querySelectorAll("input.invalid").forEach((el) => el.classList.remove("invalid"));
    const bad = illegalCheckFields(form);
    if (!bad.length) return;
    event.preventDefault();
    bad.forEach((input) => input.classList.add("invalid"));
    bad[0].focus();
  }});
}});
document.querySelectorAll("dialog.checks[data-reopen]").forEach((dialog) => dialog.showModal());
const suggestions = document.getElementById("show-suggestions");
const hitsTable = document.querySelector(".hits-table");
if (suggestions && hitsTable) {{
  suggestions.addEventListener("change", () => {{
    hitsTable.classList.toggle("show-suggestions", suggestions.checked);
  }});
}}
function illegalCheckFields(form) {{
  const kind = form.querySelector(".check-kind").value;
  const field = (name) => form.querySelector('[name="' + name + '"]');
  const shown = (name) => {{
    const input = field(name);
    if (!input) return null;
    const group = input.closest("[data-for]");
    if (group && group.hidden) return null;
    return input;
  }};
  const bad = [];
  const integer = (name) => {{
    const input = shown(name);
    if (!input || !input.value.trim()) return false;
    if (!/^-?\\d+$/.test(input.value.trim())) {{
      bad.push(input);
      return false;
    }}
    return true;
  }};
  if (kind === "text_forbid") {{
    const input = shown("pattern");
    let ok = input && input.value.trim().length > 0;
    if (ok) {{
      try {{ new RegExp(input.value); }} catch (error) {{ ok = false; }}
    }}
    if (!ok && input) bad.push(input);
  }}
  if (kind === "contents") {{
    const bytes = integer("min_bytes");
    const words = integer("min_words");
    const headers = shown("require_headers");
    const token = field("fp_bind_repo_token");
    const hasToken = token && token.checked && shown("fp_bind_repo_token");
    if (!bytes && !words && !(headers && headers.value.trim()) && !hasToken && !bad.length) {{
      ["min_bytes", "min_words", "require_headers"].forEach((name) => {{
        const input = shown(name);
        if (input) bad.push(input);
      }});
    }}
  }}
  if (kind === "fresh") integer("max_age_days");
  if (kind === "dep_ban") {{
    const input = shown("package");
    if (input && !input.value.trim()) bad.push(input);
  }}
  return bad;
}}
</script>
"""
    return page("Claims Editor", body)


def file_page(model: dict) -> bytes:
    title = str(model.get("path") or "File")
    if model.get("error"):
        body = f"<h1><code>{html.escape(title)}</code></h1><p class='err'>{html.escape(model['error'])}</p>"
        return page(title, body)
    rendered, note = _marked(model.get("body") or "", model.get("model_excerpt") or "", model.get("excerpt") or "")
    body = f"""
<h1><code>{html.escape(title)}</code></h1>
<p>{html.escape(note)}</p>
<p><a href="{_req_href(model, model.get('requirement_id') or '')}">Back to findings</a></p>
<pre>{rendered}</pre>
"""
    return page(title, body)


def _hit_row(model: dict, requirement_id: str, item: dict, index: int) -> str:
    path = str(item.get("path") or "")
    hit_id = f"hit-{index}"
    vote = str(item.get("vote") or "")
    vote_class = f" vote-{vote}" if vote in {"useful", "poor"} else ""
    covered = path in set(model.get("covered_paths") or [])
    covered_class = " covered" if covered else ""
    covered_note = (
        '<p class="covered-note">Already covered — passed in the selected Check run</p>'
        if covered
        else ""
    )
    up = "up selected" if vote == "useful" else "up"
    down = "down selected" if vote == "poor" else "down"
    checks = [entry for entry in item.get("checks") or [] if isinstance(entry, dict)]
    chips = "".join(
        f'<button type="button" class="check-chip check-edit" data-index="{index}" '
        f'data-values="{html.escape(json.dumps(_check_editor_values(entry, path)))}">'
        f"{html.escape(check_caption(entry))}</button>"
        for index, entry in enumerate(checks)
    ) or '<span class="muted">—</span>'
    options = "".join(
        f'<option value="{html.escape(key)}"{_selected(model, path, key)}>{html.escape(CAPTIONS[key])}</option>'
        for key in (
            "exist",
            "contents",
            "text_forbid",
            "anti_placeholder",
            "fresh",
            "owned",
            "dep_ban",
        )
    )
    excerpt = str(item.get("model_excerpt") or item.get("excerpt") or "")
    if not excerpt:
        excerpt = "No excerpt stored for this finding."
    suggestion_row = "" if item.get("has_claim") else " suggestion-row"
    return f"""
<tr class="hit-row{suggestion_row}{vote_class}{covered_class}" data-hit="{hit_id}" data-path="{html.escape(path)}">
  <td class="col-toggle">▸</td>
  <td class="col-file">{_evidence_cell(model, requirement_id, item)}{covered_note}</td>
  <td class="col-score">{_score(item)}</td>
  <td class="col-why"><div class="why-cell">{_motivation(model, requirement_id, item)}</div></td>
  <td class="col-checks"><div class="checks-wrap">{chips}
    <button type="button" class="check-open check-pick">Add check</button>
    <dialog class="checks"{_reopen(model, path)}>
      <div class="head"><h2>What to check for {html.escape(path)}</h2></div>
      <div class="body">
        <form method="post" action="/discover/feedback/checks" class="check-form"{_check_confirm(item)}>
          {_hidden(model, requirement_id)}
          {_source_fields(model.get("source_ids") or [])}
          <input type="hidden" name="path" value="{html.escape(path)}">
          <input type="hidden" name="edit_index" value="">
          {_unsign_field(item)}
          <label>Check
            <select name="check" class="check-kind">
              {options}
            </select>
          </label>
          <div data-for="contents" hidden>
            <label>Min bytes<input type="text" name="min_bytes" inputmode="numeric" value="{_val(model, path, "min_bytes")}" class="{_bad(model, path, "min_bytes")}"></label>
            <label>Min words<input type="text" name="min_words" inputmode="numeric" value="{_val(model, path, "min_words")}" class="{_bad(model, path, "min_words")}"></label>
            <label>Require headers<input type="text" name="require_headers" placeholder="# Title, ## Section" value="{_val(model, path, "require_headers")}" class="{_bad(model, path, "require_headers")}"></label>
            <label class="check-inline"><input type="checkbox" name="fp_bind_repo_token" value="1"{_checked(model, path, "fp_bind_repo_token")}> Bind repo token</label>
          </div>
          <div data-for="exist contents" hidden>
            <label>Also require paths<input type="text" name="require_tree_paths" placeholder="docs/a.md, docs/b.md" value="{_val(model, path, "require_tree_paths")}"></label>
          </div>
          <div data-for="text_forbid" hidden>
            <label>Pattern<input type="text" name="pattern" placeholder="regular expression" value="{_val(model, path, "pattern")}" class="{_bad(model, path, "pattern")}"></label>
          </div>
          <div data-for="dep_ban" hidden>
            <p class="muted">Running checks does not evaluate this yet.</p>
            <label>Package<input type="text" name="package" value="{_val(model, path, "package")}" class="{_bad(model, path, "package")}"></label>
            <label>Banned versions<input type="text" name="banned_versions" placeholder="1.2.3, 2.0.0" value="{_val(model, path, "banned_versions")}"></label>
          </div>
          <div data-for="fresh" hidden>
            <p class="muted">Running checks does not evaluate this yet.</p>
            <label>Max age days<input type="text" name="max_age_days" inputmode="numeric" value="{_val(model, path, "max_age_days")}" class="{_bad(model, path, "max_age_days")}"></label>
            <label>Since ref<input type="text" name="since_ref" placeholder="HEAD or a ref" value="{_val(model, path, "since_ref")}"></label>
          </div>
          <div data-for="owned" hidden>
            <p class="muted">Running checks does not evaluate this yet.</p>
            <label class="check-inline"><input type="checkbox" name="owned_bind_repo_token" value="1"{_checked(model, path, "owned_bind_repo_token")}> Bind repo token</label>
            <label>Require git author email<input type="text" name="require_git_author_email" value="{_val(model, path, "require_git_author_email")}"></label>
            <label>Require git author name<input type="text" name="require_git_author_name" value="{_val(model, path, "require_git_author_name")}"></label>
          </div>
          <p class="actions"><button type="submit" class="save-check">Save check</button>
          <button type="button" class="secondary check-close">Close</button></p>
        </form>
      </div>
    </dialog>
  </div></td>
  <td class="col-vote"><div class="votes">
    <form method="post" action="/discover/feedback/vote">
      {_hidden(model, requirement_id)}
      <input type="hidden" name="path" value="{html.escape(path)}">
      <button class="{up}" name="vote" value="useful" type="submit">Useful</button>
      <button class="{down}" name="vote" value="poor" type="submit">Poor</button>
    </form>
  </div></td>
</tr>
<tr class="detail-row{suggestion_row}" id="{hit_id}" hidden>
  <td colspan="6"><div class="detail-inner"><pre class="excerpt">{html.escape(excerpt)}</pre></div></td>
</tr>
"""


def _score(item: dict) -> str:
    if item.get("assessment_state") not in {"assessed", "reused"}:
        return '<span class="muted">—</span>'
    rank = str(item.get("rank") or "")
    try:
        number = f"{float(item.get('score')):.2f}"
    except (TypeError, ValueError):
        number = ""
    return (
        f'<span class="rank-{html.escape(rank)}" title="{html.escape(SCORE_HELP)}">{html.escape(rank)}</span> '
        f'<span class="muted" title="{html.escape(SCORE_HELP)}">{html.escape(number)}</span>'
    )


def _tip(text: str) -> str:
    return (
        f' <span class="score-help" tabindex="0">?'
        f'<span class="tip">{html.escape(text)}</span></span>'
    )


def _with_claims(findings: list, claims: list, requirement_id: str) -> list:
    """Saved claims first (multi-path above single-path), then candidates beside them.

    Pilot: no merge. A Claim and a discovery candidate for the same file stay as
    separate rows; new checks on a candidate still get their own Claim id.
    """
    owned = [
        claim
        for claim in claims
        if isinstance(claim, dict) and claim.get("requirement_id") == requirement_id
    ]

    def claim_sort_key(claim: dict) -> tuple:
        paths = _claim_paths(claim)
        multi = 0 if len(paths) > 1 else 1
        label = paths[0] if paths else str(claim.get("id") or "")
        return (multi, label, str(claim.get("id") or ""))

    rows = [_claim_row(claim) for claim in sorted(owned, key=claim_sort_key)]
    for item in findings:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["has_claim"] = False
        rows.append(row)
    return rows


def _claim_row(claim: dict) -> dict:
    paths = _claim_paths(claim)
    path = paths[0] if paths else ""
    return {
        "path": path,
        "paths": paths,
        "claim_id": str(claim.get("id") or ""),
        "description": str(claim.get("description") or ""),
        "claim_signed": isinstance(claim.get("signed"), dict),
        "has_claim": True,
        "checks": [item for item in claim.get("checks") or [] if isinstance(item, dict)],
        "assessment_state": "not_assessed",
        "vote": "",
        "excerpt": "",
    }


def _check_confirm(item: dict) -> str:
    if not item.get("claim_signed"):
        return ""
    return (
        " onsubmit=\"return confirm('This claim is signed. "
        "Saving this check removes the signature.')\""
    )


def _unsign_field(item: dict) -> str:
    if not item.get("claim_signed"):
        return ""
    return '<input type="hidden" name="unsign" value="1">'


def _check_editor_values(entry: dict, row_path: str) -> dict:
    """Form values that reopen this saved check."""
    args = entry.get("args") if isinstance(entry.get("args"), dict) else {}
    check = str(entry.get("check") or "")
    probes = [item for item in args.get("probes") or [] if isinstance(item, dict)]
    kinds = {item.get("kind") for item in probes}
    label = str(entry.get("label") or "")
    if label in CAPTIONS:
        kind = label
    elif check == "contents" and kinds == {"pattern"}:
        kind = "text_forbid"
    elif check == "contents" and kinds == {"placeholder"}:
        kind = "anti_placeholder"
    elif check in CAPTIONS:
        kind = check
    else:
        kind = "exist"
    values: dict[str, str] = {"check": kind}
    paths = args.get("paths") if isinstance(args.get("paths"), list) else []
    extra = ", ".join(str(item) for item in paths if str(item) != row_path)
    if kind == "contents":
        for probe in probes:
            if probe.get("kind") == "size" and probe.get("bytes") is not None:
                values["min_bytes"] = str(probe["bytes"])
            elif probe.get("kind") == "words" and probe.get("n") is not None:
                values["min_words"] = str(probe["n"])
            elif probe.get("kind") == "headers":
                values["require_headers"] = ", ".join(str(item) for item in probe.get("headers") or [])
            elif probe.get("kind") == "token":
                values["fp_bind_repo_token"] = "1"
        if extra:
            values["require_tree_paths"] = extra
    elif kind == "text_forbid":
        for probe in probes:
            if probe.get("kind") == "pattern":
                values["pattern"] = str(probe.get("pattern") or "")
    elif kind == "exist" and extra:
        values["require_tree_paths"] = extra
    elif kind == "dep_ban":
        values["package"] = str(args.get("package") or "")
        versions = args.get("banned_versions") if isinstance(args.get("banned_versions"), list) else []
        values["banned_versions"] = ", ".join(str(item) for item in versions)
    elif kind == "fresh":
        if args.get("max_age_days") is not None:
            values["max_age_days"] = str(args["max_age_days"])
        if args.get("since_ref"):
            values["since_ref"] = str(args["since_ref"])
    elif kind == "owned":
        if args.get("bind_repo_token"):
            values["owned_bind_repo_token"] = "1"
        if args.get("email"):
            values["require_git_author_email"] = str(args["email"])
        if args.get("name"):
            values["require_git_author_name"] = str(args["name"])
    return values


def _claim_path(claim: dict) -> str:
    paths = _claim_paths(claim)
    return paths[0] if paths else ""


def _claim_paths(claim: dict) -> list[str]:
    args = claim.get("args") if isinstance(claim.get("args"), dict) else {}
    found: list[str] = []
    single = args.get("path")
    if isinstance(single, str) and single.strip():
        found.append(single.strip())
    listed = args.get("paths")
    if isinstance(listed, list):
        for item in listed:
            if isinstance(item, str) and item.strip() and item.strip() not in found:
                found.append(item.strip())
    return found


def _evidence_cell(model: dict, requirement_id: str, item: dict) -> str:
    paths = [str(p) for p in (item.get("paths") or []) if str(p).strip()]
    if not paths:
        path = str(item.get("path") or "")
        if not path:
            return '<span class="muted">—</span>'
        paths = [path]
    links = []
    for path in paths:
        links.append(
            f'<a class="file-link" href="{_file_href(model, requirement_id, path)}">'
            f"<code>{html.escape(path)}</code></a>"
        )
    return "<br>".join(links)


def _motivation(model: dict, requirement_id: str, item: dict) -> str:
    description = str(item.get("description") or "").strip()
    why = str(item.get("why") or "").strip()
    dismissed = str(item.get("dismissed_why") or "").strip()
    if description and why and description != why and dismissed != why:
        choice = _motivation_choice(
            model,
            requirement_id,
            str(item.get("path") or ""),
            description,
            why,
            bool(item.get("claim_signed")),
        )
        return (
            f'<p class="motivation-current has-suggestion">{html.escape(description)}</p>'
            f'<div class="suggestion">{choice}</div>'
        )
    if description:
        body = html.escape(description)
    elif why:
        body = html.escape(why)
    else:
        return _why(item)
    human = str(item.get("human_why") or "").strip()
    if human and human not in {description, why}:
        body += f"<br><strong>Human rationale</strong> {html.escape(human)}"
    return body


def _motivation_choice(
    model: dict,
    requirement_id: str,
    path: str,
    description: str,
    why: str,
    signed: bool,
) -> str:
    kept = _motivation_button(model, requirement_id, path, "keep", description, why, "motivation-old", False)
    taken = _motivation_button(model, requirement_id, path, "take", why, why, "motivation-new", signed)
    return kept + taken


def _motivation_button(
    model: dict,
    requirement_id: str,
    path: str,
    choice: str,
    label: str,
    why: str,
    css: str,
    signed: bool,
) -> str:
    confirm = ""
    unsign = ""
    if signed:
        confirm = (
            " onsubmit=\"return confirm('This claim is signed. "
            "Saving replaces the motivation and removes the signature.')\""
        )
        unsign = '<input type="hidden" name="unsign" value="1">'
    return (
        f'<form method="post" action="/discover/feedback/motivation" class="motivation-pick"{confirm}>'
        f"{_hidden(model, requirement_id)}"
        f'<input type="hidden" name="path" value="{html.escape(path)}">'
        f'<input type="hidden" name="choice" value="{html.escape(choice)}">'
        f'<input type="hidden" name="why" value="{html.escape(why)}">'
        f"{unsign}"
        f'<button type="submit" class="{css}">{html.escape(label)}</button>'
        "</form>"
    )


def _why(item: dict) -> str:
    parts = []
    if item.get("assessment_state") == "failed":
        parts.append(f"Assessment failed. {html.escape(str(item.get('assessment_error') or ''))}")
    elif item.get("why"):
        parts.append(html.escape(str(item.get("why") or "")))
    elif item.get("assessment_state") not in {"assessed", "reused"}:
        parts.append('<span class="muted">Not assessed</span>')
    if item.get("human_why"):
        parts.append(f"<strong>Human rationale</strong> {html.escape(str(item['human_why']))}")
    return "<br>".join(parts)


def _ordered(findings: list) -> list:
    def key(item: dict) -> tuple:
        scored = item.get("assessment_state") in {"assessed", "reused"}
        try:
            score = float(item.get("score"))
        except (TypeError, ValueError):
            score = -1.0
        return (0 if scored else 1, -score)

    return sorted(findings, key=key)


def _outcomes(outcomes: list) -> str:
    if not outcomes:
        return ""
    lines = [
        f"<li>{html.escape(str(item.get('outcome') or ''))} "
        f"<code>{html.escape(str(item.get('id') or ''))}</code> "
        f"{html.escape(str(item.get('error') or ''))}</li>"
        for item in outcomes
        if isinstance(item, dict)
    ]
    return "<ul>" + "".join(lines) + "</ul>"


def _signature_cell(signing: str) -> str:
    seal = _seal(signing)
    if seal:
        return seal
    return '<span class="muted">no claim</span>'


def _seal(signing: str) -> str:
    if signing == "verifiable":
        return '<span class="seal seal-ok">signed</span>'
    if signing == "unsigned draft":
        return '<span class="seal seal-open">unsigned</span>'
    if signing == "signed, not verifiable":
        return '<span class="seal seal-open">not verifiable</span>'
    return ""



def _marked(body: str, model_excerpt: str, excerpt: str) -> tuple[str, str]:
    if model_excerpt and verify_excerpt(body, model_excerpt):
        rendered, _found = highlight_verified(body, model_excerpt)
        return rendered, "Model excerpt, found in the file."
    note = ""
    if model_excerpt:
        note = "Model excerpt was not found in the file."
    if excerpt and verify_excerpt(body, excerpt):
        rendered, _found = highlight_verified(body, excerpt)
        extra = " Retrieval excerpt is marked." if note else "Retrieval excerpt is marked."
        return rendered, note + extra
    return html.escape(body), note or "No verified excerpt to mark."


def _source_ids(requirement: dict) -> list[str]:
    hints = requirement.get("discovery_hints") if isinstance(requirement.get("discovery_hints"), dict) else {}
    sources = hints.get("sources") if isinstance(hints, dict) else None
    ids = []
    for item in sources or []:
        if isinstance(item, dict) and isinstance(item.get("source"), str) and item["source"] not in ids:
            ids.append(item["source"])
    return ids


def _source_fields(source_ids: list) -> str:
    if len(source_ids) == 1:
        return f'<input type="hidden" name="claim_source" value="{html.escape(source_ids[0])}">'
    options = "".join(f'<option value="{html.escape(item)}">{html.escape(item)}</option>' for item in source_ids)
    return f'<label>Source<select name="claim_source" required>{options}</select></label>'


def _check_error(model: dict, path: str) -> dict:
    error = model.get("check_error") or {}
    if error.get("path") != path:
        return {}
    return error


def _reopen(model: dict, path: str) -> str:
    if _check_error(model, path) or model.get("open_checks") == path:
        return ' data-reopen="1"'
    return ""


def _empty_findings(model: dict) -> str:
    repo_id = str(model.get("repo_id") or "")
    source_id = str(model.get("source_id") or "")
    timestamp = str(model.get("timestamp") or "")
    disabled = "" if repo_id and source_id and timestamp else " disabled"
    return (
        '<div class="empty-discover">'
        '<p class="muted">No discovered candidates yet.</p>'
        '<form method="post" action="/discover/run">'
        f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">'
        f'<input type="hidden" name="source_id" value="{html.escape(source_id)}">'
        f'<input type="hidden" name="timestamp" value="{html.escape(timestamp)}">'
        f'<button type="submit"{disabled}>Discover</button>'
        "</form>"
        '<p class="muted">If none appear, the requirement\'s search hints may need a change in Details, '
        "or there may be no evidence to claim. You can still add a file with +.</p>"
        "</div>"
    )


def _add_row(model: dict, requirement_id: str) -> str:
    return f"""
<tr class="add-row">
  <td colspan="6">
    <button type="button" class="add-open" title="Add an evidence source candidate">+</button>
  </td>
</tr>
"""


def _add_dialog(model: dict, requirement_id: str) -> str:
    options = "".join(
        f'<option value="{html.escape(path)}"></option>'
        for path in model.get("repo_files") or []
        if isinstance(path, str)
    )
    return f"""
<dialog class="checks" id="add-candidate">
  <div class="head"><h2>Add an evidence source candidate</h2></div>
  <div class="body">
    <p class="muted">Pick a repository file Discover missed. Then add a check to make a Claim.</p>
    <form method="post" action="/discover/feedback/add" class="add-finding">
      {_hidden(model, requirement_id)}
      <label>Repository file
        <input type="text" name="path" list="repo-files" required placeholder="docs/note.md" autocomplete="off">
      </label>
      <datalist id="repo-files">{options}</datalist>
      <label>Rationale
        <textarea name="rationale" rows="3" placeholder="Why this file supports the Requirement, e.g. names the intended purpose in the product overview."></textarea>
      </label>
      <p class="actions"><button type="submit" class="save-check">Add and configure check</button>
      <button type="button" class="secondary add-close">Close</button></p>
    </form>
  </div>
</dialog>
"""


def _selected(model: dict, path: str, key: str) -> str:
    if _check_error(model, path).get("check") == key:
        return " selected"
    return ""


def _val(model: dict, path: str, name: str) -> str:
    values = _check_error(model, path).get("values") or {}
    return html.escape(str(values.get(name) or ""))


def _bad(model: dict, path: str, name: str) -> str:
    if name in (_check_error(model, path).get("invalid") or []):
        return "invalid"
    return ""


def _checked(model: dict, path: str, name: str) -> str:
    if str((_check_error(model, path).get("values") or {}).get(name) or "") in {"1", "true", "on"}:
        return " checked"
    return ""


def _hidden(model: dict, requirement_id: str) -> str:
    fields = {
        "repo_id": model.get("repo_id") or "",
        "source_id": model.get("source_id") or "",
        "timestamp": model.get("timestamp") or "",
        "requirement_id": requirement_id,
    }
    if model.get("pack_id"):
        fields["pack"] = model.get("pack_id") or ""
    return_to = str(model.get("return_to") or "")
    if return_to:
        fields["return_to"] = return_to
    return "".join(
        f'<input type="hidden" name="{html.escape(key)}" value="{html.escape(str(value))}">'
        for key, value in fields.items()
    )


def _q(model: dict) -> str:
    repo = quote(str(model.get("repo_id") or ""))
    pack_id = str(model.get("pack_id") or "")
    if pack_id:
        query = f"repo={repo}&pack={quote(pack_id)}"
    else:
        query = (
            f"repo={repo}"
            f"&source={quote(str(model.get('source_id') or ''))}"
            f"&timestamp={quote(str(model.get('timestamp') or ''))}"
        )
    return_to = str(model.get("return_to") or "")
    if return_to:
        query += f"&return_to={quote(return_to, safe='')}"
    return query


def _overview_href(model: dict) -> str:
    return f"/discover/claims?{_q(model)}"


def _req_href(model: dict, requirement_id: str) -> str:
    return f"/discover/claims/{quote(requirement_id)}?{_q(model)}"


def _file_href(model: dict, requirement_id: str, path: str) -> str:
    return f"/discover/claims/{quote(requirement_id)}/file?{_q(model)}&path={quote(path)}"


def _ro_field(label: str, value: str) -> str:
    if not value:
        return ""
    return (
        f'<div class="ro-field"><span>{html.escape(label)}</span>'
        f"<strong>{html.escape(value)}</strong></div>"
    )


def _identity_card(
    model: dict,
    instrument: str,
    identifier: str,
    locator: str,
    requirement_id: str,
    law: str,
    source_url: str,
) -> str:
    fields = "".join(
        _ro_field(label, value)
        for label, value in (
            ("Instrument", instrument),
            ("Identifier", identifier),
            ("Locator", locator),
        )
    )
    law_html = html.escape(law) if law else "No law text on this Requirement."
    url_html = ""
    if source_url:
        url_html = (
            '<div class="ro-field"><span>URL</span>'
            f'<a href="{html.escape(source_url)}" target="_blank" rel="noopener">'
            f"{html.escape(source_url)}</a></div>"
        )
    ident = (
        f'<p class="muted"><code>{html.escape(requirement_id)}</code></p>'
        if requirement_id
        else ""
    )
    details = ""
    if requirement_id:
        href = "/requirements/requirement/" + quote(requirement_id, safe="")
        repo_id = str(model.get("repo_id") or "")
        pack_id = str(model.get("pack_id") or "")
        if repo_id and pack_id:
            href += "?repo=" + quote(repo_id) + "&pack=" + quote(pack_id)
        details = f'<a class="details" href="{html.escape(href)}">Details</a>'
    return (
        '<div class="card req-identity">'
        '<div class="identity-bar">'
        f'<div class="field-grid">{fields}</div>'
        f"{details}"
        "</div>"
        f"{ident}"
        '<div class="ref-law-head muted">Law text</div>'
        f'<pre class="ref-law law-flow">{law_html}</pre>'
        f"{url_html}"
        "</div>"
    )


def _locator(requirement: dict) -> str:
    references = requirement.get("references") or []
    if references and isinstance(references[0], dict):
        return str(references[0].get("locator") or "")
    return ""
