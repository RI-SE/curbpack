"""Demo requirement page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html

from app.pages import _flash, _reading, page


def _lines(values) -> str:
    if not values:
        return ""
    return "\n".join(str(item) for item in values)


def requirement_page(requirement: dict, reading: dict, message: str = "", error: str = "") -> bytes:
    source = requirement.get("source") or {}
    hints = requirement.get("discovery_hints") or {}
    law = ""
    locator = ""
    if requirement.get("references"):
        law = requirement["references"][0].get("law_text") or ""
        locator = requirement["references"][0].get("locator") or ""
    sources = "\n".join(item.get("source", "") for item in (hints.get("sources") or []) if isinstance(item, dict))
    body = f"""
<h1>{html.escape(requirement.get('id', 'Requirement'))}</h1>
{_flash(message, error)}
{_reading(reading)}
<div class="card">
<p>Locator <code>{html.escape(locator)}</code></p>
<pre>{html.escape(law)}</pre>
</div>
<form method="post" action="/requirement">
<label>Edition</label>
<input type="text" name="edition" value="{html.escape(source.get('edition', ''))}">
<label>Remediation hint</label>
<textarea name="remediation_hint">{html.escape(requirement.get('remediation_hint', ''))}</textarea>
<label>Note</label>
<textarea name="note">{html.escape(requirement.get('note', ''))}</textarea>
<label>Concepts</label>
<textarea name="concepts">{html.escape(_lines(hints.get('concepts')))}</textarea>
<label>Path hints</label>
<textarea name="path_hints">{html.escape(_lines(hints.get('path_hints')))}</textarea>
<label>Source ids (one per line, no args)</label>
<textarea name="sources">{html.escape(sources)}</textarea>
<label>Expected evidence</label>
<textarea name="expected_evidence">{html.escape(_lines(hints.get('expected_evidence')))}</textarea>
<button type="submit">Save draft</button>
</form>
<form method="post" action="/publish">
<label>Signer name</label>
<input type="text" name="name" placeholder="Ada Jurist">
<button type="submit">Publish and sign</button>
</form>
<form method="post" action="/seal-pack">
<label>Pack sealer name</label>
<input type="text" name="name" placeholder="Ada Jurist">
<button type="submit">Seal pack directory</button>
</form>
<p class="muted">Saving a change drops any previous signature. Publishing refuses a local working copy that already has origin.</p>
"""
    return page(requirement.get("id", "Requirement"), body)
