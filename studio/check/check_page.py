"""Check page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html
from urllib.parse import quote

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
<p>Check writes a Result. Review saves decisions on that Result until Sign locks them. Remediation starts from that signed review. A Remedy Report records the work and leaves those decisions unchanged.</p>
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
    for run in runs:
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
        body.append(
            "<tr>"
            f"<td>{label}<br>{html.escape(_outcome(run))}</td>"
            f"<td>{review}</td>"
            f"<td>{remedy_cell}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Check Result</th><th>Review</th><th>Remediation</th></tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


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
