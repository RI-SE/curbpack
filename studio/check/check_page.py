"""Check page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html
import re
from urllib.parse import quote

_REPORT = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>'
    '<path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h8"/>'
    "</svg>"
)

_TRASH = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/>'
    '<path d="M10 11v6"/><path d="M14 11v6"/>'
    "</svg>"
)

from app.pages import _flash, page, repo_config_panel


def check_page(
    result: dict | None,
    exit_code: int | None,
    message: str = "",
    error: str = "",
    editor: dict | None = None,
) -> bytes:
    del result, exit_code
    door = editor or {}
    panel = repo_config_panel(
        door,
        action="/check",
        show=("config", "packs", "claims", "results", "reports"),
    )
    body = f"""
<h1>Check</h1>
<p>Check writes a Result. Review saves decisions on that Result until Sign locks them. A signed review opens read-only. Remediation starts from that signed review, and Sign locks that work too. Reports are not generated yet.</p>
{_flash(message, error)}
{_pack_card(door)}
<h2>Checks performed</h2>
{_performed_table(door)}
"""
    return page("Check", body, banner=panel)


def _pack_card(editor: dict) -> str:
    repo_id = str(editor.get("repo_id") or "")
    if not repo_id:
        return '<p class="muted">Select a project to run Check.</p>'
    rows = []
    for pack in editor.get("packs") or []:
        if not isinstance(pack, dict):
            continue
        name = str(pack.get("name") or pack.get("id") or "")
        label = html.escape(name)
        if not pack.get("present"):
            label += ' <span class="muted">missing</span>'
        rows.append(
            "<tr>"
            f"<td>{label}</td>"
            f'<td class="num">{int(pack.get("claims") or 0)}</td>'
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="2" class="muted">No packs named in curbpack.json.</td></tr>')
    table = (
        "<table><thead><tr><th>Pack</th><th class=\"num\">Claims</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )
    return f"""
<div class="card discover-wrap check-run">
{table}
<form method="post" action="/check">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<p class="actions">
<button type="submit" name="action" value="check">Check</button>
</p>
</form>
</div>
"""


def _performed_table(editor: dict) -> str:
    repo_id = str(editor.get("repo_id") or "")
    runs = [row for row in (editor.get("runs") or []) if isinstance(row, dict)]
    if not runs:
        return "<p>No checks performed yet.</p>"
    body = []
    dialogs = []
    for index, run in enumerate(runs):
        when = str(run.get("when") or run.get("name") or "")
        path = str(run.get("path") or "")
        label = html.escape(when)
        if repo_id and path:
            href = html.escape(
                f"/review?repo={quote(repo_id, safe='')}&result={quote(path, safe='')}"
            )
            label = f'<a href="{href}">{label}</a>'
        review = _links(
            (str(run.get("review_label") or ""), str(run.get("review_href") or "")),
            (str(run.get("review_report_label") or ""), str(run.get("review_report_href") or "")),
        )
        remedy_cell = _links(
            (str(run.get("remedy_label") or ""), str(run.get("remedy_href") or "")),
            (str(run.get("remedy_report_label") or ""), str(run.get("remedy_report_href") or "")),
        )
        counts = run.get("remedy_counts")
        if isinstance(counts, dict):
            remedy_cell = f"{remedy_cell}<br>{html.escape(_outcome(counts))}"
        files = [str(name) for name in (run.get("files") or []) if str(name)]
        remove = ""
        dialog_id = "remove-check-" + re.sub(r"[^A-Za-z0-9_-]", "-", str(index))
        if repo_id and path and files:
            remove = (
                f'<button type="button" class="trash" data-remove-open="{html.escape(dialog_id)}" '
                'aria-label="Remove this check result">'
                f"{_TRASH}</button>"
            )
            dialogs.append(_remove_dialog(dialog_id, repo_id, path, files))
        pdf_href = str(run.get("remedy_pdf_href") or "")
        report = ""
        if pdf_href:
            report = (
                f'<a class="report-file" href="{html.escape(pdf_href)}" '
                f'aria-label="Remediation report">{_REPORT}</a>'
            )
        body.append(
            "<tr>"
            f'<td class="remove">{remove}</td>'
            f"<td>{label}<br>{html.escape(_outcome(run))}</td>"
            f"<td>{review}</td>"
            f"<td>{remedy_cell}</td>"
            f'<td class="report">{report}</td>'
            "</tr>"
        )
    script = _remove_script() if dialogs else ""
    return (
        "<table><thead><tr><th class=\"remove\"></th><th>Check Result</th>"
        "<th>Review</th><th>Remedy</th><th class=\"report\"></th></tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
        + "".join(dialogs)
        + script
    )


def _remove_dialog(dialog_id: str, repo_id: str, path: str, files: list[str]) -> str:
    items = "".join(f"<li><code>{html.escape(name)}</code></li>" for name in files)
    return (
        f'<dialog id="{html.escape(dialog_id)}" class="remove-check">'
        '<div class="head"><h2>Remove this check result?</h2></div>'
        '<div class="body"><p>These files will be removed.</p>'
        f"<ul>{items}</ul>"
        '<form method="post" action="/check/remove">'
        f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">'
        f'<input type="hidden" name="result" value="{html.escape(path)}">'
        '<p class="actions"><button type="submit" class="remove-ok">OK</button>'
        '<button type="button" class="secondary" data-close>Cancel</button></p>'
        "</form></div></dialog>"
    )


def _remove_script() -> str:
    return """
<script>
document.querySelectorAll("[data-remove-open]").forEach(function(button) {
  button.addEventListener("click", function() {
    var dialog = document.getElementById(button.getAttribute("data-remove-open"));
    if (dialog && dialog.showModal) dialog.showModal();
  });
});
document.querySelectorAll("dialog.remove-check [data-close]").forEach(function(button) {
  button.addEventListener("click", function() {
    var dialog = button.closest("dialog");
    if (dialog) dialog.close();
  });
});
</script>
"""


def _links(*pairs: tuple[str, str]) -> str:
    shown = [_linked(label, href) for label, href in pairs if label and label != "—"]
    return " ".join(shown) if shown else "—"


def _linked(label: str, href: str) -> str:
    text = html.escape(label)
    if not href or label in {"", "—"}:
        return text
    return f'<a href="{html.escape(href)}">{text}</a>'


def _outcome(run: dict) -> str:
    if run.get("unreadable"):
        return "unreadable"
    text = (
        f'{int(run.get("fail") or 0)} fail · '
        f'{int(run.get("pass") or 0)} pass · '
        f'{int(run.get("skipped") or 0)} skipped'
    )
    extras = []
    for name in ("stale", "missing"):
        count = int(run.get(name) or 0)
        if count:
            extras.append(f"{count} {name}")
    if extras:
        text += " · " + " · ".join(extras)
    return text
