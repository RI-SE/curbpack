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
<figure class="workflow">
<img src="/icons/workflow.jpg" alt="Law or an authored pack becomes a pack and requirements, then a claim, then check, review, and remediate." width="1024" height="209">
</figure>
<div class="card">
<dl class="start-steps">
<dt><a href="/requirements">Pack Editor</a></dt>
<dd>Extract requirements from law or source material, or import an authored pack. The pack is the set of requirements the product is checked against.</dd>
<dt><a href="/discover">Discovery &amp; Claims</a></dt>
<dd>Find candidate evidence in the product and save claims. A claim records the evidence and the checks to run for a requirement.</dd>
<dt><a href="/check">Verification Workflow</a></dt>
<dd>Run the checks, review the result, and remediate what failed. Development cycles repeat that loop as the product changes.</dd>
</dl>
</div>
"""
    return page("Curbpack Studio", body, banner=panel)
