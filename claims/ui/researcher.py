"""Researcher overview, requirement findings, and the product-file view."""

from __future__ import annotations

import html
from urllib.parse import quote

from app.pages import page
from checks.labels import CAPTIONS, check_caption
from claims.bind import law_passages
from discovery.present import merge_findings

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
            f"<td>{high}</td>"
            f"<td>{item.get('useful') or 0}</td>"
            f"<td>{item.get('poor') or 0}</td>"
            f"<td>{html.escape(item.get('signing') or '')}</td>"
            "</tr>"
        )
    body = f"""
<h1>Discover claims</h1>
<p class="muted">Researcher view for <code>{html.escape(model.get('repo_id') or '')}</code>
· <code>{html.escape(model.get('source_id') or '')}</code>
· <code>{html.escape(model.get('timestamp') or '')}</code>.</p>
<p><a href="/discover">Back to Discover</a></p>
{model.get('error_html') or ''}
<table>
<thead><tr><th>Requirement</th><th>Section</th><th>Findings</th><th>High</th><th>Useful</th><th>Poor</th><th>Claims</th></tr></thead>
<tbody>{''.join(rows) or '<tr><td colspan="7">No requirements in this working copy.</td></tr>'}</tbody>
</table>
"""
    return page("Discover claims", body)


def requirement_page(model: dict) -> bytes:
    requirement = model.get("requirement") or {}
    requirement_id = str(requirement.get("id") or "")
    locator = _locator(requirement) or requirement_id
    source = requirement.get("source") if isinstance(requirement.get("source"), dict) else {}
    source_url = str(source.get("url") or "")
    instrument = str(source.get("instrument") or "CRA")
    law = "\n\n".join(law_passages(requirement))
    findings = _ordered(merge_findings(model.get("candidates") or [], model.get("marks") or {}))
    model = {**model, "source_ids": _source_ids(requirement)}
    rows = []
    for index, item in enumerate(findings):
        rows.append(_hit_row(model, requirement_id, item, index))
    hits = (
        '<div class="hits"><table class="hits-table"><thead><tr>'
        "<th></th><th>Evidence Source</th>"
        f'<th>Score <span class="score-help" tabindex="0">?<span class="tip">{html.escape(SCORE_HELP)}</span></span></th>'
        "<th>Rationale</th><th>Checks</th><th>Review</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + _add_row(model, requirement_id)
        + "</tbody></table></div>"
        + (
            '<p class="muted">Click a row to expand the excerpt. The name opens the source.</p>'
            if findings
            else '<p class="muted">No discovered candidates yet. Run Discover, or add one with +.</p>'
        )
    )
    source_html = (
        f'<a href="{html.escape(source_url)}" target="_blank" rel="noopener">{html.escape(source_url)}</a>'
        if source_url
        else "(missing)"
    )
    notice = f"<p class='err'>{html.escape(model['notice'])}</p>" if model.get("notice") else ""
    outcomes = _outcomes(model.get("outcomes") or [])
    body = f"""
<div class="req-desk">
<p class="muted"><a href="{_overview_href(model)}">← Claims</a> · <code>{html.escape(str(model.get('repo_id') or ''))}</code></p>
<div class="req-head">
  <div>
    <h1>{html.escape(locator)}</h1>
    <p class="muted">{html.escape(instrument)} · <code>{html.escape(requirement_id)}</code></p>
  </div>
  <div class="req-badges">
    {_seal(str(model.get('signing') or ''))}
    <span class="pill">{html.escape(str(model.get('model') or 'not scored'))}</span>
  </div>
</div>
<p class="muted">Legal source: {source_html}</p>
{notice}
{outcomes}
<h2>Requirement text</h2>
<div class="law">{html.escape(law) if law else 'No law text on this Requirement.'}</div>
<h2>Discovered evidence source candidates ({len(findings)})</h2>
<p class="muted">A candidate is a product file that may support this Requirement. Adding a check makes a Claim for that source.</p>
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
document.querySelectorAll(".check-open").forEach((button) => {{
  button.addEventListener("click", () => button.parentElement.querySelector("dialog.checks").showModal());
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
    el.hidden = el.dataset.for !== selected;
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
    return page(locator, body)


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
        f'<span class="check-chip">{html.escape(check_caption(entry))}</span>'
        for entry in checks
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
    return f"""
<tr class="hit-row{vote_class}{covered_class}" data-hit="{hit_id}" data-path="{html.escape(path)}">
  <td class="col-toggle">▸</td>
  <td class="col-file"><a class="file-link" href="{_file_href(model, requirement_id, path)}"><code>{html.escape(path)}</code></a>{covered_note}</td>
  <td class="col-score">{_score(item)}</td>
  <td class="col-why"><div class="why-cell">{_why(item)}</div></td>
  <td class="col-checks"><div class="checks-wrap">{chips}
    <button type="button" class="check-open check-pick">Add check</button>
    <dialog class="checks"{_reopen(model, path)}>
      <div class="head"><h2>What to check for {html.escape(path)}</h2></div>
      <div class="body">
        <form method="post" action="/discover/feedback/checks" class="check-form">
          {_hidden(model, requirement_id)}
          {_source_fields(model.get("source_ids") or [])}
          <input type="hidden" name="path" value="{html.escape(path)}">
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
            <label>Require tree paths<input type="text" name="require_tree_paths" placeholder="docs/a.md, docs/b.md" value="{_val(model, path, "require_tree_paths")}"></label>
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
<tr class="detail-row" id="{hit_id}" hidden>
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
    return "".join(
        f'<input type="hidden" name="{html.escape(key)}" value="{html.escape(str(value))}">'
        for key, value in fields.items()
    )


def _q(model: dict) -> str:
    return (
        f"repo={quote(str(model.get('repo_id') or ''))}"
        f"&source={quote(str(model.get('source_id') or ''))}"
        f"&timestamp={quote(str(model.get('timestamp') or ''))}"
    )


def _overview_href(model: dict) -> str:
    return f"/discover/claims?{_q(model)}"


def _req_href(model: dict, requirement_id: str) -> str:
    return f"/discover/claims/{quote(requirement_id)}?{_q(model)}"


def _file_href(model: dict, requirement_id: str, path: str) -> str:
    return f"/discover/claims/{quote(requirement_id)}/file?{_q(model)}&path={quote(path)}"


def _locator(requirement: dict) -> str:
    references = requirement.get("references") or []
    if references and isinstance(references[0], dict):
        return str(references[0].get("locator") or "")
    return ""
