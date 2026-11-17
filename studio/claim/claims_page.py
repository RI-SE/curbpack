"""Claims editor HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html
import json

from app.pages import _flash, page, repo_config_panel


def claims_page(model: dict, message: str = "", error: str = "") -> bytes:
    """Claims editor. Domain logic stays in claims.bind / server helpers."""
    blocks = []
    for item in model.get("claims") or []:
        claim = item.get("claim") or {}
        claim_id = str(claim.get("id") or "")
        requirement_id = str(claim.get("requirement_id") or "")
        args = json.dumps(claim.get("args") or {}, indent=2, ensure_ascii=False)
        checks = json.dumps(claim.get("checks") or [], indent=2, ensure_ascii=False)
        reading = item.get("reading") or {}
        seal_html = _claim_seal_html(reading)
        law_html = _passages_html(item.get("passages") or [])
        signed = isinstance(claim.get("signed"), dict)
        save_note = (
            '<p class="err">This Claim is sealed. Saving a changed payload clears the seal. '
            "It is then an unsigned draft until signed again.</p>"
            if signed
            else '<p class="muted">Unsigned draft. Selecting a Discovery path or saving does not approve evidence.</p>'
        )
        hidden = _claim_context(model)
        warning = str(item.get("retire_warning") or "")
        warning_html = f'<p class="err">{html.escape(warning)}</p>' if warning else ""
        confirm = "Retire this Claim? The file is removed."
        if warning:
            confirm = f"{warning} {confirm}"
        sign_form = ""
        if not signed:
            sign_form = f"""
<form method="post" action="/claims/{html.escape(claim_id)}/sign">
{hidden}
<label>Signer name</label>
<input type="text" name="name" placeholder="Ada Jurist" required>
<button type="submit">Sign claim</button>
</form>
"""
        proposed = model.get("proposed_requirement") if isinstance(model.get("proposed_requirement"), dict) else {}
        proposed_html = ""
        target_html = ""
        if proposed:
            proposed_html = (
                f'<p data-proposed-namespace="{html.escape(str(proposed.get("namespace") or ""))}"'
                f' data-proposed-pack="{html.escape(str(proposed.get("pack_id") or ""))}"'
                f' data-proposed-requirement="{html.escape(str(proposed.get("id") or ""))}"'
                f' data-proposed-digest="{html.escape(str(proposed.get("digest") or ""))}">'
                f'Proposed binding {html.escape(str(proposed.get("namespace") or ""))}'
                f' {html.escape(str(proposed.get("pack_id") or ""))}'
                f' {html.escape(str(proposed.get("id") or ""))}'
                f' {html.escape(str(proposed.get("digest") or ""))}</p>'
            )
            target_html = (
                f'<input type="hidden" name="namespace" value="{html.escape(str(proposed.get("namespace") or ""))}">'
                f'<input type="hidden" name="pack_id" value="{html.escape(str(proposed.get("pack_id") or ""))}">'
            )
        recorded_html = (
            f'<p data-recorded-namespace="{html.escape(str(claim.get("namespace") or ""))}"'
            f' data-recorded-pack="{html.escape(str(claim.get("pack_id") or ""))}"'
            f' data-recorded-requirement="{html.escape(str(claim.get("requirement_id") or ""))}"'
            f' data-recorded-digest="{html.escape(str(claim.get("requirement_digest") or ""))}">'
            f'Recorded binding {html.escape(str(claim.get("namespace") or ""))}'
            f' {html.escape(str(claim.get("pack_id") or ""))}'
            f' {html.escape(str(claim.get("requirement_id") or ""))}'
            f' {html.escape(str(claim.get("requirement_digest") or ""))}</p>'
        )
        blocks.append(
            f"""<div class="card" id="claim-{html.escape(claim_id)}">
{seal_html}
<p><code>{html.escape(claim_id)}</code> → <code>{html.escape(requirement_id)}</code></p>
{recorded_html}
{proposed_html}
{law_html}
{save_note}
<form method="post" action="/claims/{html.escape(claim_id)}">
{hidden}
<input type="hidden" name="requirement_id" value="{html.escape(requirement_id)}">
<label>Source</label>
<input type="text" name="source" value="{html.escape(claim.get('source', ''))}" required>
<label>Severity</label>
<input type="text" name="severity" value="{html.escape(claim.get('severity', ''))}">
<label>Description</label>
<input type="text" name="description" value="{html.escape(claim.get('description', ''))}" required>
<label>Source args JSON</label>
<textarea name="args">{html.escape(args)}</textarea>
<label>Checks JSON</label>
<textarea name="checks">{html.escape(checks)}</textarea>
<button type="submit">Save claim</button>
</form>
<form method="post" action="/claims/{html.escape(claim_id)}/rebind">
{hidden}
{target_html}
<label>Requirement</label>
<select name="requirement_id">
{_rebind_options(model, requirement_id, proposed)}
</select>
<button type="submit">Rebind</button>
</form>
{sign_form}
{warning_html}
<form method="post" action="/claims/{html.escape(claim_id)}/retire"
 onsubmit="return confirm({html.escape(json.dumps(confirm))});">
{hidden}
<button type="submit">Retire</button>
</form>
</div>"""
        )
    empty = (
        '<p class="muted">No Claims yet. Create them from '
        '<a href="/discover">Discovery &amp; Claims</a> '
        "(add a check on a finding).</p>"
        if not blocks
        else ""
    )
    panel = repo_config_panel(
        model,
        action="/claims",
        show=("config", "packs", "claims"),
    )
    body = f"""
<h1>Claim editor</h1>
<p class="muted">Edit, sign, or retire Claims already in the product repo.
New Claims come from <a href="/discover">Discovery &amp; Claims</a>.
Editing a sealed Claim clears its seal.</p>
{panel}
{_flash(message, error)}
{''.join(blocks) or empty}
"""
    return page("Claim editor", body)


def _rebind_options(model: dict, requirement_id: str, proposed: dict) -> str:
    choices = [
        item for item in (model.get("rebind_requirements") or []) if isinstance(item, dict)
    ]
    if not choices:
        choices = [{"id": req_id} for req_id in model.get("requirement_ids") or []]
    selected_id = str(proposed.get("id") or requirement_id)
    options = []
    for choice in choices:
        req_id = str(choice.get("id") or "")
        namespace = str(choice.get("namespace") or "")
        pack_id = str(choice.get("pack_id") or "")
        label = f"{namespace} {pack_id} {req_id}".strip() if namespace and pack_id else req_id
        selected = " selected" if req_id == selected_id else ""
        options.append(
            f'<option value="{html.escape(req_id)}"{selected}>{html.escape(label)}</option>'
        )
    return "".join(options)


def _claim_context(model: dict) -> str:
    fields = []
    for key in ("repo_id", "source_id", "timestamp", "return_to"):
        value = str(model.get(key) or "")
        if value:
            fields.append(f'<input type="hidden" name="{key}" value="{html.escape(value)}">')
    return "".join(fields)


def _claim_seal_html(reading: dict) -> str:
    if reading.get("verifiable"):
        return (
            f'<p><strong>Signed · verifiable</strong> · who {html.escape(str(reading.get("who") or "—"))}'
            f' · when {html.escape(str(reading.get("when") or "—"))}</p>'
        )
    if isinstance(reading.get("who"), str) and reading.get("who"):
        reason = html.escape(str(reading.get("reason") or "signature does not verify"))
        return (
            f'<p class="err"><strong>Signed · not verifiable</strong> · who '
            f'{html.escape(str(reading.get("who")))} · {reason}</p>'
        )
    reason = html.escape(str(reading.get("reason") or "unsigned draft"))
    return f'<p class="muted"><strong>Unsigned draft</strong> · {reason}</p>'


def _passages_html(passages: list) -> str:
    if not passages:
        return '<p class="muted">No law_text available for this Requirement in the selected Pack.</p>'
    blocks = []
    for text in passages:
        blocks.append(f"<pre>{html.escape(str(text))}</pre>")
    return "<p>Requirement text</p>" + "".join(blocks)
