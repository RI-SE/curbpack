"""Check page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html
from urllib.parse import quote

from app.pages import _flash, page, repo_config_panel
from checks.labels import check_caption


def check_page(
    result: dict | None,
    exit_code: int | None,
    message: str = "",
    error: str = "",
    editor: dict | None = None,
) -> bytes:
    if result is None:
        shown = "<p>No run yet.</p>"
    else:
        git = ""
        if result.get("worktree") == "dirty":
            git = "<p class=\"err\">The worktree was dirty. This result is not verification of that commit's exact content.</p>"
        elif result.get("commit"):
            git = f"<p class=\"muted\">commit <code>{html.escape(result['commit'])}</code> · worktree {html.escape(result['worktree'])}</p>"
        rows = []
        for row in result.get("claims") or []:
            nested = row.get("checks") or []
            if not nested:
                rows.append(
                    "<tr>"
                    f"<td><code>{html.escape(row.get('id', ''))}</code></td>"
                    f"<td></td><td></td>"
                    f"{_status_cell(row.get('status', ''))}{_binding_cell(row)}<td></td>"
                    "</tr>"
                )
            for item in nested:
                rows.append(
                    "<tr>"
                    f"<td><code>{html.escape(row.get('id', ''))}</code></td>"
                    f"<td>{item.get('index', '')}</td>"
                    f"<td>{html.escape(check_caption(item))}</td>"
                    f"{_status_cell(item.get('status', ''))}{_binding_cell(row)}"
                    f"<td>{html.escape(item.get('detail') or '')}</td>"
                    "</tr>"
                )
        table = "<p>No claim rows. This is not a successful verification.</p>" if not rows else (
            "<table><tr><th>Claim</th><th>Index</th><th>Check</th><th>Status</th><th>Binding</th><th>Detail</th></tr>"
            + "".join(rows)
            + "</table>"
        )
        shown = git + f"<p>exit {exit_code}</p>" + table
    door = editor or {}
    panel = repo_config_panel(
        door,
        action="/check",
        show=("config", "packs", "claims", "results", "reports"),
    )
    body = f"""
<h1>Check</h1>
<p class="muted">Check reads this repository's <code>curbpack.json</code>.
The file is not signed. A green check row is not a legal conclusion.
Edit paths on <a href="/project">Project</a>.</p>
{panel}
{_flash(message, error)}
{_curbpack_editor(door)}
<h2>Report</h2>
<div class="card">{shown}</div>
"""
    return page("Check", body)


def _status_cell(status: object) -> str:
    text = html.escape(str(status or ""))
    return f'<td data-check-status="{text}">{text}</td>'


def _binding_cell(row: dict) -> str:
    binding = row.get("binding")
    if binding not in {"match", "stale", "missing"}:
        return "<td></td>"
    lines = [html.escape(str(binding))]
    if binding in {"stale", "missing"}:
        lines.extend(
            html.escape(str(row.get(key) or ""))
            for key in ("namespace", "pack_id", "requirement_id")
        )
        lines.append("requirement " + html.escape(str(row.get("requirement_digest") or "")))
    if binding == "stale":
        lines.append("actual " + html.escape(str(row.get("actual_digest") or "")))
    return f'<td data-binding="{html.escape(str(binding))}">{"<br>".join(lines)}</td>'


def _curbpack_editor(editor: dict) -> str:
    repo_id = str(editor.get("repo_id") or "")
    if not repo_id:
        return (
            '<div class="card discover-wrap">'
            '<p class="muted">Select a project to run Check.</p></div>'
        )
    rows = []
    for pack in editor.get("packs") or []:
        if not isinstance(pack, dict):
            continue
        pack_id = str(pack.get("id") or "")
        state = "present" if pack.get("present") else "missing"
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(pack_id)}</code></td>"
            f"<td>{html.escape(state)}</td>"
            f"<td><code>{html.escape(str(pack.get('pack_dir') or ''))}</code></td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="3" class="muted">No packs named in curbpack.json.</td></tr>')
    selection = str(editor.get("selection") or "")
    selection_html = (
        f"<p>Selection <code>{html.escape(selection)}</code></p>" if selection else ""
    )
    result_path = str(editor.get("run_result_path") or "")
    result_html = ""
    if result_path:
        result_html = f"<p>Run result <code>{html.escape(result_path)}</code></p>"
        if repo_id:
            href = f"/review?repo={quote(repo_id, safe='')}&result={quote(result_path, safe='')}"
            result_html += f'<p><a href="{html.escape(href)}">Review this run</a></p>'
    return f"""
<div class="card discover-wrap">
{selection_html}
{result_html}
<table><thead><tr><th>Pack</th><th>Status</th><th>Path</th></tr></thead><tbody>
{"".join(rows)}
</tbody></table>
<form method="post" action="/check">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<p class="actions">
<button type="submit" name="action" value="check">Check</button>
</p>
</form>
</div>
"""
