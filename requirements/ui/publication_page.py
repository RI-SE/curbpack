"""Legacy Publish HTML. EP-11 retires this flow. This file does not rebuild it."""

from __future__ import annotations

import html

from app.pages import page
from studio.pack.pages import _coverage_label, _flash, _reading_block


def publication_page(model: dict) -> bytes:
    if not model.get("timestamp"):
        body = """
<p class="muted"><a href="/requirements">Pack Sources</a></p>
<h1>Publish</h1>
<p>No working copy is selected. Publish uses one dated copy and creates a new release.</p>
"""
        return page("Publish", body)
    blockers = [str(item) for item in (model.get("blockers") or [])]
    blocker_html = ""
    if blockers:
        blocker_html = (
            "<h2>Publication blockers</h2><ul>"
            + "".join(f"<li>{html.escape(item)}</li>" for item in blockers)
            + "</ul><p>Resolve these on the working copy. Publishing stays unavailable until they are gone.</p>"
        )
    coverage = model.get("coverage_detail") or {}
    coverage_status = str(coverage.get("status") or "")
    coverage_html = ""
    if coverage_status:
        coverage_html = (
            f"<p>Extract coverage: <strong>{html.escape(_coverage_label(coverage_status))}</strong>. "
            "Incomplete legal coverage stays visible and is not a publication blocker.</p>"
        )
    readings = []
    for item in model.get("requirements") or []:
        if item.get("verifiable"):
            state = "signature verifies"
        elif item.get("signed"):
            state = "signature does not verify"
        else:
            state = "unsigned"
        readings.append(
            "<li>"
            f'<a href="/requirements/requirement/{html.escape(str(item.get("id")))}">'
            f"{html.escape(str(item.get('id')))}</a> · {html.escape(state)}</li>"
        )
    requirement_html = "<ul>" + "".join(readings) + "</ul>" if readings else "<p>No requirements.</p>"
    body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a>
 · <a href="/requirements/copy">Requirements list</a></p>
<h1>Publish</h1>
<p>Working copy <code>{html.escape(str(model.get("timestamp") or ""))}</code>.
 A release is a new immutable directory. This copy and earlier releases stay as they are.</p>
{_flash(str(model.get("message") or ""))}
<div class="card">
{coverage_html}
{blocker_html}
<h2>Requirements</h2>
{requirement_html}
{_reading_block("Pack directory", model.get("seal"))}
{_seal_form()}
{_publish_form(model)}
</div>
"""
    return page("Publish", body)


def _seal_form() -> str:
    return (
        '<form method="post" action="/requirements/seal">'
        "<label>Name<input type=\"text\" name=\"name\"></label>"
        "<p><button type=\"submit\">Seal Pack directory</button></p></form>"
    )


def _publish_form(model: dict) -> str:
    version = html.escape(str(model.get("pack_version") or ""))
    disabled = " disabled" if model.get("blockers") else ""
    return (
        '<form method="post" action="/requirements/publish">'
        f'<label>pack.version<input type="text" name="version" value="{version}" readonly></label>'
        f'<p><button type="submit"{disabled}>Publish release</button></p></form>'
    )
