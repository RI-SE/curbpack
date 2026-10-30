"""Discover page: product repos, a working copy, and a progress popup."""

from __future__ import annotations

import html
import json
from urllib.parse import quote

from app.pages import page, progress_dialog, repo_config_panel


def discover_page(model: dict) -> bytes:
    pilot = model.get("mode") != "product"
    err = str(model.get("error") or "")
    flash = f'<p class="err">{html.escape(err)}</p>' if err else ""
    repo_id = quote(str(model.get("repo_id") or ""))
    repo_query = f"?repo={repo_id}" if repo_id else ""
    if pilot:
        intro = (
            "<p class=\"muted\">Packs named in the selected repository's <code>curbpack.json</code>. "
            "Claims are read only from that file's claims directory.</p>"
        )
    else:
        name = html.escape(str(model.get("repo_name") or "the selected repo"))
        intro = (
            f"<p class=\"muted\">Repo <strong>{name}</strong>. "
            "Packs and claims come from its <code>curbpack.json</code>. "
            f'<a href="/discover{repo_query}">Pilot</a>.</p>'
        )
    add_repo = (
        '<p class="actions"><button type="button" id="add-repo-open">Add repo</button></p>'
        if pilot
        else ""
    )
    panel = repo_config_panel(
        model,
        action="/discover" if pilot else "/discover/repo",
        show=("config", "packs", "claims"),
        beside=add_repo,
    )
    body = f"""
<h1>Discovery &amp; Claims</h1>
{intro}
{flash}
{panel}
<div class="card discover-wrap">{_pack_table(model)}</div>
"""
    if pilot:
        body += _add_repo_dialog(str(model.get("workspace_root") or ""))
    body += _section_script(list(model.get("reviewable") or []))
    if model.get("job"):
        body += _job_dialog(model["job"])
    return page("Discovery & Claims", body)


def _pack_table(model: dict) -> str:
    repo_id = str(model.get("repo_id") or "")
    rows = [
        _pack_row(repo_id, pack)
        for pack in model.get("pack_rows") or []
        if isinstance(pack, dict)
    ]
    if not rows and repo_id:
        rows.append('<tr><td colspan="6" class="muted">No packs named in curbpack.json.</td></tr>')
    return (
        "<table><thead><tr>"
        "<th>Pack</th>"
        '<th class="num"># Req</th><th class="num"># Claims</th>'
        '<th class="num wrap"># Req without<br>claims</th>'
        "<th>Limit</th><th>Actions</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _pack_row(repo_id: str, pack: dict) -> str:
    pack_id = str(pack.get("pack_id") or "")
    name = str(pack.get("name") or pack_id)
    requirements = int(pack.get("requirements") or 0)
    claims = int(pack.get("claims") or 0)
    unclaimed = int(pack.get("unclaimed") or 0)
    form_id = "discover-" + html.escape(pack_id)
    href = _pack_href(repo_id, pack_id)
    gap_href = href + ("&gap=1" if "?" in href else "")
    edit = ""
    if claims and repo_id and pack_id:
        edit = f'<a class="edit-review" href="{html.escape(href)}">Edit</a>'
    discover_disabled = "" if repo_id and pack_id and requirements else " disabled"
    return (
        f'<tr class="section-row" data-repo="{html.escape(repo_id)}" data-pack="{html.escape(pack_id)}">'
        f"<td>{html.escape(name)}</td>"
        f'<td class="num">{_count_link("req-link", href, requirements, "Requirements in this pack")}</td>'
        f'<td class="num">{_count_link("claims-link", href, claims, "Claims on those requirements")}</td>'
        f'<td class="num">{_count_link("unclaimed-link", gap_href, unclaimed, "Requirements with no claim")}</td>'
        "<td>"
        f'<input type="number" name="assess_limit" form="{form_id}" value="5" min="0" max="20" '
        'aria-label="Limit">'
        "</td>"
        '<td class="actions">'
        f'<form id="{form_id}" method="post" action="/discover/run">'
        f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">'
        f'<input type="hidden" name="pack_id" value="{html.escape(pack_id)}"></form>'
        f'<button type="submit" class="discover" form="{form_id}"{discover_disabled}>Discover</button>'
        f"{edit}"
        "</td></tr>"
    )


def _pack_href(repo_id: str, pack_id: str) -> str:
    if not repo_id or not pack_id:
        return "/discover/claims"
    return "/discover/claims?repo=" + quote(repo_id) + "&pack=" + quote(pack_id)


def _count_link(css: str, href: str, count: int, title: str) -> str:
    return (
        f'<a class="{css}" href="{html.escape(href)}" title="{html.escape(title)}">{count}</a>'
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
    done = _claims_done_href(job)
    if status == "running":
        dismiss = (
            f'<form method="post" action="/discover/jobs/{job_id}/abort">'
            '<button type="submit" class="secondary">Abort</button></form>'
        )
        note = '<p class="muted">Keep this window open while discovery runs.</p>'
    elif done:
        dismiss = f'<a href="{html.escape(done)}"><button type="button">OK</button></a>'
        note = ""
    else:
        dismiss = '<form method="get" action="/discover"><button type="submit">OK</button></form>'
        note = ""
    job = {**job, "title": job.get("title") or "Discover"}
    return progress_dialog(
        job,
        poll=f"/discover/jobs/{job_id}",
        dismiss=dismiss,
        done_href=done,
        note=note,
    )


def _claims_done_href(job: dict) -> str:
    """Where a finished Discover run opens the shared claims page."""
    repo_id = str(job.get("repo_id") or "")
    pack_id = str(job.get("pack_id") or "")
    if repo_id and pack_id:
        return "/discover/claims?repo=" + quote(repo_id) + "&pack=" + quote(pack_id)
    source_id = str(job.get("source_id") or "")
    timestamp = str(job.get("timestamp") or "")
    if repo_id and source_id and timestamp:
        return (
            "/discover/claims?repo="
            + quote(repo_id)
            + "&source="
            + quote(source_id)
            + "&timestamp="
            + quote(timestamp)
        )
    return ""
