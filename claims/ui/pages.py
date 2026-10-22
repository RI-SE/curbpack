"""Discover page: product repos, a working copy, and a progress popup."""

from __future__ import annotations

import html
import json
from urllib.parse import quote

from app.pages import page, progress_dialog


def discover_page(model: dict) -> bytes:
    sources = list(model.get("sources") or [])
    repos = list(model.get("repos") or [])
    err = str(model.get("error") or "")
    flash = f'<p class="err">{html.escape(err)}</p>' if err else ""
    body = f"""
<h1>Discovery &amp; Claims</h1>
<p class="muted">Pick a product repository and a working copy, then <strong>Discover</strong>.
The run covers every requirement in that copy. A candidate is not a Claim.
Hunt settings come from the repository's <code>curbpack.json</code>.</p>
<p class="actions"><button type="button" id="add-repo-open">Add repo</button></p>
{flash}
<div class="card discover-wrap">{_repo_table(repos, sources, list(model.get("reviewable") or []))}</div>
{_add_repo_dialog()}
{_sources_script(sources, list(model.get("reviewable") or []))}
"""
    if model.get("job"):
        body += _job_dialog(model["job"])
    return page("Discovery & Claims", body)


def _repo_table(repos: list, sources: list, reviewable: list) -> str:
    if not repos:
        rows = ['<tr><td colspan="6" class="muted">No repos yet. Click Add repo.</td></tr>']
    else:
        rows = [_repo_row(repo, sources, reviewable) for repo in repos]
    return (
        "<table><thead><tr>"
        "<th>Repo</th><th>Path</th><th>Document name</th><th>Section</th>"
        "<th>Working copy</th><th>Actions</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _repo_row(repo: dict, sources: list, reviewable: list) -> str:
    repo_id = str(repo.get("id") or "")
    name = str(repo.get("name") or repo_id)
    path = str(repo.get("path") or "")
    form_id = f"discover-{html.escape(repo_id)}"
    first = sources[0] if sources else None
    section = str(first.get("section_id") or "") if first else ""
    copies = list(first.get("copies") or []) if first else []
    discover_disabled = "" if copies else " disabled"
    return (
        "<tr>"
        f"<td>{html.escape(name)}{_pill(str(repo.get('last_status') or ''))}</td>"
        f'<td class="path-cell" title="{html.escape(path)}"><code>{html.escape(path)}</code></td>'
        f"<td>{_document_select(repo_id, sources)}</td>"
        f'<td><code class="section-cell" data-repo="{html.escape(repo_id)}">{html.escape(section)}</code></td>'
        f"<td>{_copy_select(repo_id, copies)}</td>"
        "<td class=\"actions\">"
        f'<form id="{form_id}" method="post" action="/discover/run">'
        f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}"></form>'
        f'<input type="number" name="assess_limit" form="{form_id}" value="5" min="0" max="20" '
        f'aria-label="Assess up to">'
        f'<button type="submit" class="discover" form="{form_id}" data-repo="{html.escape(repo_id)}"'
        f"{discover_disabled}>Discover</button>"
        f"{_edit_link(repo_id, first, reviewable)}"
        "</td></tr>"
    )


def _document_select(repo_id: str, sources: list) -> str:
    if not sources:
        return '<span class="muted">No source. Add one on Requirements.</span>'
    options = []
    for source in sources:
        source_id = str(source.get("source_id") or "")
        label = str(source.get("name") or source_id)
        section = str(source.get("section_id") or "")
        options.append(
            f'<option value="{html.escape(source_id)}" data-section="{html.escape(section)}">'
            f"{html.escape(label)}</option>"
        )
    return (
        f'<select name="source_id" class="doc-select" data-repo="{html.escape(repo_id)}" '
        f'form="discover-{html.escape(repo_id)}" aria-label="Document name">'
        + "".join(options)
        + "</select>"
    )


def _copy_select(repo_id: str, copies: list) -> str:
    if not copies:
        return (
            f'<select class="copy-select" data-repo="{html.escape(repo_id)}" '
            f'form="discover-{html.escape(repo_id)}" name="timestamp" aria-label="Working copy" disabled>'
            '<option value="">No working copy</option></select>'
        )
    options = []
    for copy in copies:
        chosen = " selected" if copy.get("chosen") else ""
        options.append(
            f'<option value="{html.escape(str(copy.get("timestamp")))}"{chosen}>'
            f"{html.escape(_copy_label(copy))}</option>"
        )
    return (
        f'<select name="timestamp" class="copy-select" data-repo="{html.escape(repo_id)}" '
        f'form="discover-{html.escape(repo_id)}" aria-label="Working copy">'
        + "".join(options)
        + "</select>"
    )


def _copy_label(copy: dict) -> str:
    markers = []
    if copy.get("latest"):
        markers.append("latest")
    if copy.get("selected"):
        markers.append("selected")
    coverage = str(copy.get("coverage_status") or "")
    if coverage and coverage != "none":
        markers.append(coverage)
    label = str(copy.get("timestamp") or "")
    if markers:
        return f"{label} · {' · '.join(markers)}"
    return label


def _edit_link(repo_id: str, source: dict | None, reviewable: list) -> str:
    href = html.escape(_claims_href(repo_id, source))
    hidden = "" if _is_reviewable(repo_id, source, reviewable) else " hidden"
    return (
        f'<a class="edit-review" data-repo="{html.escape(repo_id)}" href="{href}"{hidden}>Edit</a>'
    )


def _is_reviewable(repo_id: str, source: dict | None, reviewable: list) -> bool:
    if not isinstance(source, dict):
        return False
    copies = [copy for copy in source.get("copies") or [] if isinstance(copy, dict)]
    chosen = next((copy for copy in copies if copy.get("chosen")), copies[0] if copies else None)
    if not isinstance(chosen, dict) or not chosen.get("timestamp"):
        return False
    source_id = str(source.get("source_id") or "")
    timestamp = str(chosen.get("timestamp") or "")
    return any(
        item.get("repo_id") == repo_id
        and item.get("source_id") == source_id
        and item.get("timestamp") == timestamp
        for item in reviewable
        if isinstance(item, dict)
    )


def _claims_href(repo_id: str, source: dict | None) -> str:
    if not source:
        return "/discover/claims"
    copies = list(source.get("copies") or [])
    chosen = next((copy for copy in copies if copy.get("chosen")), copies[0] if copies else None)
    if not isinstance(chosen, dict) or not chosen.get("timestamp"):
        return "/discover/claims"
    return (
        "/discover/claims?repo="
        + quote(repo_id)
        + "&source="
        + quote(str(source.get("source_id") or ""))
        + "&timestamp="
        + quote(str(chosen.get("timestamp") or ""))
    )


def _pill(status: str) -> str:
    if status == "done":
        return ' <span class="pill pill-ok">discovered</span>'
    if status == "running":
        return ' <span class="pill">discovering</span>'
    if status == "failed":
        return ' <span class="pill pill-bad">failed</span>'
    if status == "aborted":
        return ' <span class="pill">aborted</span>'
    return ""


def _add_repo_dialog() -> str:
    return """
<dialog id="add-repo">
<div class="head"><h2>Add repo</h2></div>
<div class="body">
<form method="post" action="/discover/repos">
<label>Name<input type="text" name="name" required autocomplete="off" placeholder="cyberready-test-product"></label>
<label>Path<input type="text" name="path" required autocomplete="off" placeholder="/absolute/path/to/repo"></label>
<p class="muted">Absolute path, or a path relative to the workspace.</p>
<p class="actions">
<button type="button" class="secondary" id="add-repo-cancel">Cancel</button>
<button type="submit">Save</button>
</p>
</form>
</div>
</dialog>
"""


def _sources_script(sources: list, reviewable: list) -> str:
    payload = []
    for source in sources:
        payload.append(
            {
                "id": str(source.get("source_id") or ""),
                "name": str(source.get("name") or ""),
                "section_id": str(source.get("section_id") or ""),
                "copies": [
                    {
                        "timestamp": str(copy.get("timestamp") or ""),
                        "label": _copy_label(copy),
                        "chosen": bool(copy.get("chosen")),
                    }
                    for copy in source.get("copies") or []
                    if isinstance(copy, dict)
                ],
            }
        )
    data = json.dumps(payload)
    marks = json.dumps(reviewable)
    return f"""
<script type="application/json" id="discover-sources">{data}</script>
<script type="application/json" id="discover-reviewable">{marks}</script>
<script>
const discoverSources = JSON.parse(document.getElementById("discover-sources").textContent || "[]");
const discoverReviewable = JSON.parse(document.getElementById("discover-reviewable").textContent || "[]");
function syncReview(repo) {{
  const doc = document.querySelector('.doc-select[data-repo="' + repo + '"]');
  const copies = document.querySelector('.copy-select[data-repo="' + repo + '"]');
  const edit = document.querySelector('a.edit-review[data-repo="' + repo + '"]');
  if (!edit || !doc || !copies) return;
  const hit = discoverReviewable.some((item) =>
    item.repo_id === repo && item.source_id === doc.value && item.timestamp === copies.value);
  edit.hidden = !(hit && copies.value);
  if (!edit.hidden) {{
    edit.href = "/discover/claims?repo=" + encodeURIComponent(repo)
      + "&source=" + encodeURIComponent(doc.value)
      + "&timestamp=" + encodeURIComponent(copies.value);
  }}
}}
function discoverCopies(sourceId) {{
  const source = discoverSources.find((item) => item.id === sourceId);
  return source ? source.copies : [];
}}
function fillCopies(select, sourceId) {{
  const copies = discoverCopies(sourceId);
  select.innerHTML = "";
  if (!copies.length) {{
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No working copy";
    select.appendChild(option);
    select.disabled = true;
    return;
  }}
  select.disabled = false;
  for (const copy of copies) {{
    const option = document.createElement("option");
    option.value = copy.timestamp;
    option.textContent = copy.label;
    if (copy.chosen) option.selected = true;
    select.appendChild(option);
  }}
}}
document.querySelectorAll(".doc-select").forEach((doc) => {{
  doc.addEventListener("change", () => {{
    const repo = doc.dataset.repo;
    const source = discoverSources.find((item) => item.id === doc.value);
    const section = document.querySelector('.section-cell[data-repo="' + repo + '"]');
    const copies = document.querySelector('.copy-select[data-repo="' + repo + '"]');
    const button = document.querySelector('button.discover[data-repo="' + repo + '"]');
    if (section) section.textContent = source ? source.section_id : "";
    if (copies) fillCopies(copies, doc.value);
    if (button && copies) button.disabled = copies.disabled;
    syncReview(repo);
  }});
}});
document.querySelectorAll(".copy-select").forEach((copies) => {{
  copies.addEventListener("change", () => syncReview(copies.dataset.repo));
}});
const addOpen = document.getElementById("add-repo-open");
const addDialog = document.getElementById("add-repo");
if (addOpen && addDialog) {{
  addOpen.addEventListener("click", () => addDialog.showModal());
  document.getElementById("add-repo-cancel").addEventListener("click", () => addDialog.close());
}}
</script>
"""


def _job_dialog(job: dict) -> str:
    job_id = html.escape(str(job.get("job_id") or ""))
    status = str(job.get("status") or "")
    if status == "running":
        dismiss = (
            f'<form method="post" action="/discover/jobs/{job_id}/abort">'
            '<button type="submit" class="secondary">Abort</button></form>'
        )
        note = '<p class="muted">Keep this window open while discovery runs.</p>'
    else:
        dismiss = '<form method="get" action="/discover"><button type="submit">OK</button></form>'
        note = ""
    job = {**job, "title": job.get("title") or "Discover"}
    return progress_dialog(
        job,
        poll=f"/discover/jobs/{job_id}",
        dismiss=dismiss,
        note=note,
    )
