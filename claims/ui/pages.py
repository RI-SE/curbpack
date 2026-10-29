"""Discover page: product repos, a working copy, and a progress popup."""

from __future__ import annotations

import html
import json
from urllib.parse import quote

from app.pages import page, progress_dialog


def discover_page(model: dict) -> bytes:
    pilot = model.get("mode") != "product"
    err = str(model.get("error") or "")
    flash = f'<p class="err">{html.escape(err)}</p>' if err else ""
    repo_id = quote(str(model.get("repo_id") or ""))
    repo_query = f"?repo={repo_id}" if repo_id else ""
    if pilot:
        intro = (
            "<p class=\"muted\">This page is the pilot. It lists every section from the Pack editor. "
            "Pick a repository, then a working copy or a published release. "
            "Hunt settings come from the repository's <code>curbpack.json</code>. "
            f'<a href="/discover/repo{repo_query}">The selected repo</a> uses the copy already chosen there.</p>'
        )
    else:
        name = html.escape(str(model.get("repo_name") or "the selected repo"))
        intro = (
            f"<p class=\"muted\">Repo <strong>{name}</strong>. "
            "Sections for the packs named in this repo's <code>curbpack.json</code>. "
            "The copy is the one already chosen in the Pack editor. "
            f'<a href="/discover{repo_query}">Pilot</a>.</p>'
        )
    body = f"""
<h1>Discovery &amp; Claims</h1>
{intro}
{flash}
<div class="card discover-wrap">{_repo_picker(model, pilot)}{_section_table(model, pilot)}</div>
"""
    if pilot:
        body += _add_repo_dialog(str(model.get("workspace_root") or ""))
    body += _section_script(list(model.get("reviewable") or []))
    if model.get("job"):
        body += _job_dialog(model["job"])
    return page("Discovery & Claims", body)


def _section_table(model: dict, pilot: bool) -> str:
    repo_id = str(model.get("repo_id") or "")
    reviewable = list(model.get("reviewable") or [])
    rows = []
    sections = list(model.get("sections") or [])
    if sections:
        rows.extend(_section_row(repo_id, section, reviewable, pilot) for section in sections)
    elif not pilot:
        rows.append('<tr><td colspan="8" class="muted">No sections for the packs in curbpack.json.</td></tr>')
    if pilot:
        rows.append(
            '<tr><td colspan="8"><button type="button" id="add-repo-open">Add repo</button></td></tr>'
        )
    return (
        "<table><thead><tr>"
        "<th>Pack</th><th>Section</th><th>Copy</th>"
        '<th class="num"># Req</th><th class="num"># Claims</th>'
        '<th class="num wrap"># Req without<br>claims</th>'
        "<th>Limit</th><th>Actions</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _repo_picker(model: dict, pilot: bool) -> str:
    repo_id = str(model.get("repo_id") or "")
    action = "/discover" if pilot else "/discover/repo"
    options = ['<option value="">Choose a repo</option>']
    for repo in list(model.get("repos") or []):
        if not isinstance(repo, dict):
            continue
        row_id = str(repo.get("id") or "")
        name = str(repo.get("name") or row_id)
        selected = " selected" if row_id == repo_id else ""
        options.append(
            f'<option value="{html.escape(row_id)}"{selected}>{html.escape(name)}</option>'
        )
    return (
        f'<form method="get" class="repo-picker" action="{action}">'
        '<label>Repo <select name="repo" id="discover-repo" onchange="this.form.submit()">'
        + "".join(options)
        + "</select></label></form>"
    )


def _section_row(repo_id: str, section: dict, reviewable: list, pilot: bool) -> str:
    source_id = str(section.get("source_id") or "")
    name = str(section.get("name") or source_id)
    section_id = str(section.get("section_id") or "")
    copies = [copy for copy in section.get("copies") or [] if isinstance(copy, dict)]
    chosen = next((copy for copy in copies if copy.get("chosen")), copies[0] if copies else None)
    value = str((chosen or {}).get("value") or "")
    form_id = "discover-" + html.escape(source_id)
    counts = {
        str(copy.get("value") or ""): {
            "requirements": int(copy.get("requirements") or 0),
            "claims": int(copy.get("claims") or 0),
            "unclaimed": int(copy.get("unclaimed") or 0),
        }
        for copy in copies
    }
    requirements = int((chosen or {}).get("requirements") or 0)
    claims = int((chosen or {}).get("claims") or 0)
    unclaimed = int((chosen or {}).get("unclaimed") or 0)
    discover_disabled = "" if value and repo_id else " disabled"
    edit = ""
    if _row_reviewable(repo_id, source_id, value, reviewable):
        edit = f'<a class="edit-review" href="{html.escape(_overview_href(repo_id, source_id, value))}">Edit</a>'
    return (
        f'<tr class="section-row" data-repo="{html.escape(repo_id)}" '
        f'data-source="{html.escape(source_id)}" data-counts="{html.escape(json.dumps(counts))}">'
        f"<td>{html.escape(name)}</td>"
        f"<td><code>{html.escape(section_id)}</code></td>"
        f"<td>{_copy_cell(form_id, copies, chosen, pilot)}</td>"
        f'<td class="num">{_count_link("req-link", _overview_href(repo_id, source_id, value), requirements, "Requirements in this copy")}</td>'
        f'<td class="num">{_count_link("claims-link", _overview_href(repo_id, source_id, value), claims, "Claims on those requirements")}</td>'
        f'<td class="num">{_count_link("unclaimed-link", _overview_href(repo_id, source_id, value, gap=True), unclaimed, "Requirements with no claim")}</td>'
        "<td>"
        f'<input type="number" name="assess_limit" form="{form_id}" value="5" min="0" max="20" '
        'aria-label="Limit">'
        "</td>"
        '<td class="actions">'
        f'<form id="{form_id}" method="post" action="/discover/run">'
        f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">'
        f'<input type="hidden" name="source_id" value="{html.escape(source_id)}"></form>'
        f'<button type="submit" class="discover" form="{form_id}"{discover_disabled}>Discover</button>'
        f"{edit}"
        "</td></tr>"
    )


def _count_link(css: str, href: str, count: int, title: str) -> str:
    return (
        f'<a class="{css}" href="{html.escape(href)}" title="{html.escape(title)}">{count}</a>'
    )


def _copy_cell(form_id: str, copies: list, chosen: dict | None, pilot: bool) -> str:
    if not pilot:
        if not chosen:
            return '<span class="muted">No working copy</span>'
        return html.escape(str(chosen.get("label") or "")) + (
            f'<input type="hidden" name="timestamp" form="{form_id}" '
            f'value="{html.escape(str(chosen.get("value") or ""))}">'
        )
    if not copies:
        return (
            f'<select class="copy-select" name="timestamp" form="{form_id}" aria-label="Copy" disabled>'
            '<option value="">No working copy</option></select>'
        )
    options = []
    for copy in copies:
        selected = " selected" if copy is chosen or copy.get("chosen") else ""
        options.append(
            f'<option value="{html.escape(str(copy.get("value") or ""))}"{selected}>'
            f'{html.escape(str(copy.get("label") or ""))}</option>'
        )
    return (
        f'<select class="copy-select" name="timestamp" form="{form_id}" aria-label="Copy">'
        + "".join(options)
        + "</select>"
    )


def _overview_href(repo_id: str, source_id: str, ref: str, *, gap: bool = False) -> str:
    if not repo_id or not source_id or not ref:
        return "/discover/claims"
    href = (
        "/discover/claims?repo="
        + quote(repo_id)
        + "&source="
        + quote(source_id)
        + "&timestamp="
        + quote(ref)
    )
    if gap:
        href += "&gap=1"
    return href


def _row_reviewable(repo_id: str, source_id: str, ref: str, reviewable: list) -> bool:
    if not repo_id or not source_id or not ref:
        return False
    return any(
        item.get("repo_id") == repo_id
        and item.get("source_id") == source_id
        and item.get("timestamp") == ref
        for item in reviewable
        if isinstance(item, dict)
    )


def _section_script(reviewable: list) -> str:
    marks = json.dumps(reviewable)
    return f"""
<script type="application/json" id="discover-reviewable">{marks}</script>
<script>
const discoverReviewable = JSON.parse(document.getElementById("discover-reviewable").textContent || "[]");
function sectionHref(row, value, gap) {{
  const href = "/discover/claims?repo=" + encodeURIComponent(row.dataset.repo)
    + "&source=" + encodeURIComponent(row.dataset.source)
    + "&timestamp=" + encodeURIComponent(value);
  return gap ? href + "&gap=1" : href;
}}
function applySection(row) {{
  const select = row.querySelector(".copy-select");
  if (!select) return;
  const value = select.value;
  const counts = JSON.parse(row.dataset.counts || "{{}}");
  const count = counts[value] || {{requirements: 0, claims: 0, unclaimed: 0}};
  const reqs = row.querySelector("a.req-link");
  const claims = row.querySelector("a.claims-link");
  const gap = row.querySelector("a.unclaimed-link");
  if (reqs) {{
    reqs.textContent = String(count.requirements || 0);
    reqs.href = sectionHref(row, value, false);
  }}
  if (claims) {{
    claims.textContent = String(count.claims || 0);
    claims.href = sectionHref(row, value, false);
  }}
  if (gap) {{
    gap.textContent = String(count.unclaimed || 0);
    gap.href = sectionHref(row, value, true);
  }}
  const button = row.querySelector("button.discover");
  if (button) button.disabled = !value;
}}
document.querySelectorAll("tr.section-row").forEach((row) => {{
  const select = row.querySelector(".copy-select");
  if (select) select.addEventListener("change", () => applySection(row));
}});
const addOpen = document.getElementById("add-repo-open");
const addDialog = document.getElementById("add-repo");
if (addOpen && addDialog) {{
  addOpen.addEventListener("click", () => addDialog.showModal());
  document.getElementById("add-repo-cancel").addEventListener("click", () => addDialog.close());
}}
const browseBtn = document.getElementById("discover-browse-path");
const pathInput = document.getElementById("discover-repo-path");
const nameInput = document.querySelector('#add-repo input[name="name"]');
if (browseBtn && pathInput && typeof window.openRepoBrowse === "function") {{
  browseBtn.addEventListener("click", () => window.openRepoBrowse(pathInput, nameInput));
}}
</script>
"""


def _add_repo_dialog(workspace_root: str) -> str:
    from discovery.browse_ui import browse_dialog_and_script, path_field_with_browse

    start = workspace_root.strip() or "/"
    return f"""
<dialog id="add-repo">
<div class="head"><h2>Add repo</h2></div>
<div class="body">
<form method="post" action="/discover/repos">
<label>Name<input type="text" name="name" required autocomplete="off" placeholder="cyberready-test-product"></label>
{path_field_with_browse(path_id="discover-repo-path", browse_id="discover-browse-path")}
<p class="actions">
<button type="button" class="secondary" id="add-repo-cancel">Cancel</button>
<button type="submit">Save</button>
</p>
</form>
</div>
</dialog>
{browse_dialog_and_script(start_path=start)}
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
