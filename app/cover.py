"""Home page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

from app.pages import _flash, page, repo_config_panel

_CONFIG_FIELDS = ("config", "packs", "claims", "results", "reports")


def cover(model: dict, message: str = "", error: str = "") -> bytes:
    selected = bool(model.get("repo_id"))
    panel = repo_config_panel(
        model,
        show=_CONFIG_FIELDS if selected else (),
        title="Current Project",
        blanks=selected,
    )
    body = f"""
<h1>Curbpack Studio</h1>
<p class="muted">Curbpack Studio turns law text into checkable requirements, grouped in packs.
The pilot workflow: author packs from law text → create claims in your product →
check regularly → review the result and fix what failed.</p>
{_flash(message, error)}
<div class="card">
<p><a href="/requirements">Pack Editor</a></p>
<p><a href="/discover">Discovery &amp; Claims — find candidates, configure checks, create Claims</a></p>
<p><a href="/check">Check — authoritative pack via curbpack.json</a></p>
<p><a href="/review">Review — compile and sign review</a></p>
</div>
"""
    return page("Curbpack Studio", body, banner=panel)
