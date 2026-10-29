"""Try-discovery dialog for one Requirement: pick repo, GO, inspect hits."""

from __future__ import annotations

import html
from urllib.parse import quote

from app.pages import progress_dialog
from discovery.search import glob_hit, highlight_verified, verify_excerpt

SCORE_HELP = (
    "A model reads the requirement text and the first 12,000 characters, "
    "at temperature 0. Score and rank are that judgment of support — not a check result. "
    "Score 0 / rank None are omitted from the list."
)


def dialog_html(model: dict) -> str:
    requirement_id = html.escape(str(model.get("requirement_id") or ""))
    plain_id = str(model.get("requirement_id") or "")
    repos = list(model.get("repos") or [])
    try_repo = str(model.get("try_repo_id") or "")
    open_flag = ' data-open="1"' if model.get("try_open") else ""
    options = ['<option value="">Choose a product repo</option>']
    for row in repos:
        repo_id = str(row.get("id") or "")
        name = str(row.get("name") or repo_id)
        selected = " selected" if repo_id == try_repo else ""
        options.append(
            f'<option value="{html.escape(repo_id)}"{selected}>{html.escape(name)}</option>'
        )
    add_btn = (
        '<button type="button" id="try-add-repo-open" class="secondary">Add repo</button>'
    )
    if len(options) == 1:
        repo_field = (
            f'<p class="muted">No product repos yet.</p>'
            f'<p class="actions">{add_btn}</p>'
        )
        go_disabled = " disabled"
    else:
        repo_field = (
            f'<label>Product repo<select name="repo_id" required>{"".join(options)}</select></label>'
            f'<p class="actions">{add_btn}</p>'
        )
        go_disabled = ""
    results = _results(model)
    error = model.get("try_error")
    error_html = f'<p class="err">{html.escape(str(error))}</p>' if error else ""
    job = model.get("try_job")
    job_html = _job_dialog(job, plain_id) if job else ""
    next_href = f"/requirements/requirement/{quote(plain_id, safe='')}?try_open=1"
    bound_repo = str(model.get("repo_id") or "")
    bound_pack = str(model.get("bound_pack") or "")
    if bound_repo and bound_pack:
        next_href += f"&repo={quote(bound_repo, safe='')}&pack={quote(bound_pack, safe='')}"
    next_href = html.escape(next_href)
    bound_fields = ""
    if bound_repo and bound_pack:
        bound_fields = (
            f'<input type="hidden" name="repo" value="{html.escape(bound_repo)}">'
            f'<input type="hidden" name="pack" value="{html.escape(bound_pack)}">'
        )
    title = f"Discovery test run for {plain_id}" if plain_id else "Discovery test run"
    return f"""
<dialog id="try-discovery-dialog" class="try-discovery"{open_flag}>
<div class="head">
  <h2>{html.escape(title)}</h2>
  <button type="button" id="try-discovery-close" class="secondary">Close</button>
</div>
<div class="body">
{_law_box(model)}
{error_html}
<form method="post" action="/requirements/requirement/{requirement_id}/try-discovery">
{bound_fields}
{repo_field}
<label>Assess up to
<input type="number" name="assess_limit" value="{html.escape(str(model.get('try_assess_limit') or 5))}"
 min="0" max="20"></label>
<p><button type="submit"{go_disabled}>GO</button></p>
</form>
{results}
</div>
</dialog>
{_add_repo_dialog(next_href, str(model.get("workspace_root") or ""))}
{job_html}
<script>
(function () {{
  const dialog = document.getElementById("try-discovery-dialog");
  const openBtn = document.getElementById("try-discovery-open");
  const closeBtn = document.getElementById("try-discovery-close");
  const addOpen = document.getElementById("try-add-repo-open");
  const addDialog = document.getElementById("try-add-repo");
  const addCancel = document.getElementById("try-add-repo-cancel");
  const browseBtn = document.getElementById("try-browse-path");
  const pathInput = document.getElementById("try-repo-path");
  const nameInput = document.querySelector('#try-add-repo input[name="name"]');
  if (openBtn) openBtn.addEventListener("click", () => dialog.showModal());
  if (closeBtn) closeBtn.addEventListener("click", () => dialog.close());
  dialog.addEventListener("cancel", (event) => {{ event.preventDefault(); dialog.close(); }});
  if (dialog.dataset.open === "1" && !document.getElementById("try-job")) dialog.showModal();
  if (addOpen && addDialog) {{
    addOpen.addEventListener("click", () => addDialog.showModal());
  }}
  if (addCancel && addDialog) {{
    addCancel.addEventListener("click", () => addDialog.close());
  }}
  if (browseBtn && pathInput && typeof window.openRepoBrowse === "function") {{
    browseBtn.addEventListener("click", () => window.openRepoBrowse(pathInput, nameInput));
  }}
  dialog.querySelectorAll("tr.hit-row").forEach((row) => {{
    row.addEventListener("click", (event) => {{
      if (event.target.closest("a")) return;
      const detail = document.getElementById(row.dataset.detail);
      if (!detail) return;
      const open = detail.hasAttribute("hidden");
      detail.toggleAttribute("hidden", !open);
      row.classList.toggle("open", open);
    }});
  }});
}})();
</script>
"""


def _add_repo_dialog(next_href: str, workspace_root: str) -> str:
    """Same Add-repo form as Discovery & Claims; returns here via hidden next."""
    from discovery.browse_ui import browse_dialog_and_script, path_field_with_browse

    start = workspace_root.strip() or "/"
    return f"""
<dialog id="try-add-repo">
<div class="head"><h2>Add repo</h2></div>
<div class="body">
<form method="post" action="/discover/repos">
<input type="hidden" name="next" value="{next_href}">
<label>Name<input type="text" name="name" required autocomplete="off" placeholder="cyberready-test-product"></label>
{path_field_with_browse(path_id="try-repo-path", browse_id="try-browse-path")}
<p class="actions">
<button type="button" class="secondary" id="try-add-repo-cancel">Cancel</button>
<button type="submit">Save</button>
</p>
</form>
</div>
</dialog>
{browse_dialog_and_script(start_path=start)}
"""


def _job_dialog(job: dict, requirement_id: str) -> str:
    job_id = html.escape(str(job.get("job_id") or ""))
    repo_id = quote(str(job.get("repo_id") or ""), safe="")
    req = quote(requirement_id, safe="")
    done_href = f"/requirements/requirement/{req}?try_repo={repo_id}&try_open=1"
    status = str(job.get("status") or "")
    if status == "running":
        dismiss = '<button type="button" class="secondary" disabled>Running…</button>'
        note = '<p class="muted">Keep this window open while discovery runs.</p>'
    else:
        dismiss = f'<a href="{html.escape(done_href)}"><button type="button">OK</button></a>'
        note = ""
    job = {**job, "title": job.get("title") or "Discovery test run"}
    return progress_dialog(
        job,
        poll=f"/requirements/try-discovery/jobs/{job_id}",
        dismiss=dismiss,
        done_href=done_href,
        dialog_id="try-job",
        note=note,
    )


def file_page(model: dict) -> bytes:
    from app.pages import page

    title = str(model.get("path") or "File")
    if model.get("error"):
        body = (
            f"<h1><code>{html.escape(title)}</code></h1>"
            f"<p class='err'>{html.escape(str(model['error']))}</p>"
            f"<p><a href=\"{html.escape(str(model.get('back') or ''))}\">← {html.escape(_back_label(model))}</a></p>"
        )
        return page(title, body)
    rendered, note = _marked(
        model.get("body") or "",
        model.get("model_excerpt") or "",
        model.get("excerpt") or "",
    )
    back_label = _back_label(model)
    body = f"""
<p class="muted"><a href="{html.escape(str(model.get('back') or ''))}">← {html.escape(back_label)}</a></p>
<h1><code>{html.escape(title)}</code></h1>
<p>{html.escape(note)}</p>
<pre>{rendered}</pre>
"""
    return page(title, body)


def _back_label(model: dict) -> str:
    requirement_id = str(model.get("requirement_id") or "").strip()
    if requirement_id:
        return f"Back to the discovery test run for {requirement_id}"
    return "Back to the discovery test run"


def _law_box(model: dict) -> str:
    blocks = []
    for item in model.get("law_passages") or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("law_text") or "").strip()
        if not text:
            continue
        locator = str(item.get("locator") or "").strip()
        label = f"Law text · {locator}" if locator else "Law text"
        blocks.append(
            '<div class="card">'
            f'<p class="muted">{html.escape(label)}</p>'
            f'<pre class="ref-law">{html.escape(text)}</pre>'
            "</div>"
        )
    return "".join(blocks)


def _results(model: dict) -> str:
    candidates = list(model.get("try_candidates") or [])
    if not model.get("try_repo_id"):
        return ""
    if not candidates and not model.get("try_ran"):
        return ""
    if not candidates:
        return '<p class="muted">No candidates. Adjust path hints or concepts, save, then GO again.</p>'
    rows = []
    for index, item in enumerate(candidates):
        rows.append(_hit_row(model, item, index))
    return (
        '<div class="hits try-hits"><table class="hits-table"><thead><tr>'
        "<th></th><th>Evidence source</th><th>Found on</th>"
        f'<th>Score <span class="score-help" tabindex="0">?<span class="tip">{html.escape(SCORE_HELP)}</span></span></th>'
        "<th>Rationale</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
        + '<p class="muted">Click a row for the excerpt. The path opens the file with marking.</p>'
    )


def _hit_row(model: dict, item: dict, index: int) -> str:
    path = str(item.get("path") or "")
    detail_id = f"try-hit-{index}"
    href = _file_href(model, path)
    excerpt = str(item.get("model_excerpt") or item.get("excerpt") or "") or "No excerpt."
    return f"""
<tr class="hit-row" data-detail="{detail_id}">
  <td class="col-toggle">▸</td>
  <td class="col-file"><a href="{html.escape(href)}"><code>{html.escape(path)}</code></a></td>
  <td class="col-found">{_found_on(model, item)}</td>
  <td class="col-score">{_score(item)}</td>
  <td class="col-why"><div class="why-cell">{_why(item)}</div></td>
</tr>
<tr class="detail-row" id="{detail_id}" hidden>
  <td colspan="5"><div class="detail-inner"><pre class="excerpt">{html.escape(excerpt)}</pre></div></td>
</tr>
"""


def _score(item: dict) -> str:
    state = str(item.get("assessment_state") or "")
    if state in {"assessed", "reused"}:
        try:
            number = f"{float(item.get('score')):.2f}"
        except (TypeError, ValueError):
            number = "—"
        rank = html.escape(str(item.get("rank") or ""))
        return f'{number} <span class="rank-{rank}">{rank}</span>'
    if state == "failed":
        return '<span class="muted">failed</span>'
    if state == "not_assessed":
        return '<span class="muted">not assessed</span>'
    return '<span class="muted">—</span>'


def _found_on(model: dict, item: dict) -> str:
    stored = item.get("matched_hints")
    if isinstance(stored, list) and any(str(hint).strip() for hint in stored):
        labels = [str(hint) for hint in stored if str(hint).strip()]
    else:
        labels = _hints_for_path(str(item.get("path") or ""), model.get("discovery_hints") or {})
    if not labels:
        return '<span class="muted">—</span>'
    return "<br>".join(f"<code>{html.escape(label)}</code>" for label in labels)


def _hints_for_path(path: str, hints: dict) -> list[str]:
    path_hints = [item for item in (hints.get("path_hints") or []) if isinstance(item, str) and item.strip()]
    return [hint for hint in path_hints if glob_hit(path, hint)]


def _why(item: dict) -> str:
    if item.get("why"):
        return html.escape(str(item["why"]))
    if item.get("assessment_error"):
        return f'<span class="err">{html.escape(str(item["assessment_error"]))}</span>'
    return ""


def _file_href(model: dict, path: str) -> str:
    requirement_id = quote(str(model.get("requirement_id") or ""), safe="")
    repo_id = quote(str(model.get("try_repo_id") or ""), safe="")
    return (
        f"/requirements/requirement/{requirement_id}/try-discovery/file"
        f"?repo={repo_id}&path={quote(path)}"
    )


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
