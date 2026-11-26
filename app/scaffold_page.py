"""Scaffold page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

from app.pages import _flash, page


def scaffold_page(message: str = "", error: str = "") -> bytes:
    body = f"""
<h1>Scaffold</h1>
<p class="muted">Writes a short stub and refuses to overwrite an existing file. The stub is not approved evidence.</p>
{_flash(message, error)}
<form method="post" action="/scaffold">
<label>Path</label>
<input type="text" name="path" value="docs/annex-vii/risk_assessment.md">
<button type="submit">Write stub</button>
</form>
"""
    return page("Scaffold", body)
