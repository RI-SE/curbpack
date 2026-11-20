"""Studio config page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html

from app.pages import _current_project_label, _flash, page


def _review_path_chrome(door: dict) -> str:
    if not str(door.get("repo_id") or ""):
        return ""
    parts = []
    if door.get("curbpack_file"):
        parts.append(f"<p>curbpack.json <code>{html.escape(str(door.get('curbpack_file') or ''))}</code></p>")
    if door.get("directory"):
        parts.append(
            f'<p class="muted">Packs directory <code>{html.escape(str(door.get("directory") or ""))}</code>.</p>'
        )
    if door.get("claims_dir"):
        parts.append(
            f'<p class="muted">Claims directory <code>{html.escape(str(door.get("claims_dir") or ""))}</code>.</p>'
        )
    if door.get("results_dir"):
        parts.append(
            f'<p class="muted">Results directory <code>{html.escape(str(door.get("results_dir") or ""))}</code>.</p>'
        )
    if door.get("reports_dir"):
        parts.append(
            f'<p class="muted">Reports directory <code>{html.escape(str(door.get("reports_dir") or ""))}</code>.</p>'
        )
    if door.get("report_path"):
        parts.append(f"<p>Review report <code>{html.escape(str(door.get('report_path') or ''))}</code></p>")
    return "".join(parts)


def studio_page(model: dict, message: str = "") -> bytes:
    door = model.get("door") or {}
    repo_id = str(door.get("repo_id") or "")
    current = _current_project_label(door)
    chrome = _review_path_chrome(door)
    if not repo_id:
        body = f"""
<h1>Studio config</h1>
{current}
<p>No repository is chosen.</p>
"""
        return page("Studio config", body)
    values = model.get("values") or {}
    present = bool(model.get("present"))
    offer = (
        "<p>No curbpack-studio.json. Save writes one with the fields below.</p>"
        if not present
        else f"<p>curbpack-studio.json <code>{html.escape(str(model.get('path') or ''))}</code></p>"
    )
    paths = ""
    if present:
        paths = (
            f'<p class="muted">temp_dir <code>{html.escape(str(values.get("path_temp_dir") or ""))}</code></p>'
            f'<p class="muted">extract_work_dir <code>{html.escape(str(values.get("path_extract_work_dir") or ""))}</code></p>'
            f'<p class="muted">keys_file <code>{html.escape(str(values.get("path_keys_file") or "null"))}</code></p>'
        )
    body = f"""
<h1>Studio config</h1>
<p class="muted">Operator settings for this product repository. Absent file keeps today's bind/model/temp wiring.</p>
{current}
{chrome}
{offer}
{paths}
{_flash(message, "")}
<form method="post" action="/studio">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="save">
<label>bind.host <input type="text" name="bind_host" value="{html.escape(str(values.get("bind_host") or ""))}" required autocomplete="off"></label>
<label>bind.port <input type="text" name="bind_port" value="{html.escape(str(values.get("bind_port") or ""))}" required autocomplete="off"></label>
<label>model.endpoint <input type="text" name="model_endpoint" value="{html.escape(str(values.get("model_endpoint") or ""))}" required autocomplete="off"></label>
<label>model.api_key <input type="text" name="model_api_key" value="{html.escape(str(values.get("model_api_key") or ""))}" required autocomplete="off"></label>
<label>model.name <input type="text" name="model_name" value="{html.escape(str(values.get("model_name") or ""))}" required autocomplete="off"></label>
<label>model.temperature <input type="text" name="model_temperature" value="{html.escape(str(values.get("model_temperature") or ""))}" required autocomplete="off"></label>
<label>prompts.interpret <input type="text" name="prompt_interpret" value="{html.escape(str(values.get("prompt_interpret") or ""))}" autocomplete="off"></label>
<label>prompts.discovery_hints <input type="text" name="prompt_discovery_hints" value="{html.escape(str(values.get("prompt_discovery_hints") or ""))}" autocomplete="off"></label>
<label class="check-inline"><input type="checkbox" name="researcher_mode" value="true"{' checked' if values.get('researcher_mode') == 'true' else ''}> researcher_mode — hide the Review column</label>
<label>paths.temp_dir <input type="text" name="path_temp_dir" value="{html.escape(str(values.get("path_temp_dir") or ""))}" required autocomplete="off"></label>
<label>paths.extract_work_dir <input type="text" name="path_extract_work_dir" value="{html.escape(str(values.get("path_extract_work_dir") or ""))}" required autocomplete="off"></label>
<label>paths.keys_file <input type="text" name="path_keys_file" value="{html.escape(str(values.get("path_keys_file") or ""))}" autocomplete="off"></label>
<p class="actions">
<button type="submit" form="studio-cancel" class="secondary">Cancel</button>
<button type="submit">Save</button>
</p>
</form>
<form method="post" action="/studio" id="studio-cancel">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="cancel">
</form>
"""
    return page("Studio config", body)
