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


def _shown(value: object) -> str:
    if value is None:
        return "adapter prompt"
    return str(value)


def _effective_lines(model: dict) -> str:
    chosen = model.get("effective") or {}
    bind = chosen.get("bind") or {}
    settings = chosen.get("model") or {}
    prompts = chosen.get("prompts") or {}
    paths = chosen.get("paths") or {}
    mode = chosen.get("researcher_mode") or {}
    sent = (
        "The API key is sent with the user endpoint."
        if model.get("sends_api_key")
        else "The API key is not sent."
    )
    rows = (
        ("bind.host", (bind.get("host") or {}).get("value"), (bind.get("host") or {}).get("source")),
        ("bind.port", (bind.get("port") or {}).get("value"), (bind.get("port") or {}).get("source")),
        ("model.endpoint", (settings.get("endpoint") or {}).get("value"), (settings.get("endpoint") or {}).get("source")),
        ("model.name", (settings.get("name") or {}).get("value"), (settings.get("name") or {}).get("source")),
        ("model.temperature", (settings.get("temperature") or {}).get("value"), (settings.get("temperature") or {}).get("source")),
        ("prompts.interpret", _shown((prompts.get("interpret") or {}).get("value")), (prompts.get("interpret") or {}).get("source")),
        ("prompts.discovery_hints", _shown((prompts.get("discovery_hints") or {}).get("value")), (prompts.get("discovery_hints") or {}).get("source")),
        ("paths.extract_work_dir", (paths.get("extract_work_dir") or {}).get("value"), (paths.get("extract_work_dir") or {}).get("source")),
        ("researcher_mode", (mode or {}).get("value"), (mode or {}).get("source")),
    )
    lines = [
        f"<li>{html.escape(label)} <code>{html.escape(_shown(value))}</code> <span class=\"muted\">{html.escape(str(source or ''))}</span></li>"
        for label, value, source in rows
    ]
    return "<ul>" + "".join(lines) + f"</ul><p>{html.escape(sent)}</p>"


def _checked(project: dict, block: str, key: str) -> str:
    current = project.get(block)
    if isinstance(current, dict) and key in current:
        return " checked"
    return ""


def _project_value(project: dict, block: str, key: str) -> str:
    current = project.get(block)
    if not isinstance(current, dict) or key not in current or current[key] is None:
        return ""
    return str(current[key])


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
    values = model.get("user_values") or {}
    project = model.get("project") or {}
    user_file = (
        f"<p>No user file yet. Save user settings writes <code>{html.escape(str(model.get('user_path') or ''))}</code>.</p>"
        if not model.get("user_present")
        else f"<p>User file <code>{html.escape(str(model.get('user_path') or ''))}</code></p>"
    )
    project_file = (
        "<p>No project curbpack-studio.json. Save project overrides writes one.</p>"
        if not model.get("project_present")
        else f"<p>curbpack-studio.json <code>{html.escape(str(model.get('project_path') or ''))}</code></p>"
    )
    mode_checked = " checked" if project.get("researcher_mode") is True else ""
    body = f"""
<h1>Studio config</h1>
<p class="muted">User settings apply to every repository. Project overrides apply only to the open repository.</p>
{current}
{chrome}
{user_file}
{project_file}
<h2>Effective</h2>
{_effective_lines(model)}
{_flash(message, "")}
<form method="post" action="/studio">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="save_user">
<h2>User settings</h2>
<label>bind.host <input type="text" name="bind_host" value="{html.escape(str(values.get("bind_host") or ""))}" required autocomplete="off"></label>
<label>bind.port <input type="text" name="bind_port" value="{html.escape(str(values.get("bind_port") or ""))}" required autocomplete="off"></label>
<label>model.endpoint <input type="text" name="model_endpoint" value="{html.escape(str(values.get("model_endpoint") or ""))}" required autocomplete="off"></label>
<label>model.api_key <input type="text" name="model_api_key" value="{html.escape(str(values.get("model_api_key") or ""))}" autocomplete="off"></label>
<label>model.name <input type="text" name="model_name" value="{html.escape(str(values.get("model_name") or ""))}" required autocomplete="off"></label>
<label>model.temperature <input type="text" name="model_temperature" value="{html.escape(str(values.get("model_temperature") or ""))}" required autocomplete="off"></label>
<label>prompts.interpret <input type="text" name="prompt_interpret" value="{html.escape(str(values.get("prompt_interpret") or ""))}" autocomplete="off"></label>
<label>prompts.discovery_hints <input type="text" name="prompt_discovery_hints" value="{html.escape(str(values.get("prompt_discovery_hints") or ""))}" autocomplete="off"></label>
<label>paths.temp_dir <input type="text" name="path_temp_dir" value="{html.escape(str(values.get("path_temp_dir") or ""))}" required autocomplete="off"></label>
<label>paths.extract_work_dir <input type="text" name="path_extract_work_dir" value="{html.escape(str(values.get("path_extract_work_dir") or ""))}" required autocomplete="off"></label>
<label>paths.keys_file <input type="text" name="path_keys_file" value="{html.escape(str(values.get("path_keys_file") or ""))}" autocomplete="off"></label>
<p class="actions"><button type="submit">Save user settings</button></p>
</form>
<form method="post" action="/studio">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="save_project">
<h2>Project overrides</h2>
<label class="check-inline"><input type="checkbox" name="use_model_endpoint" value="true"{_checked(project, "model", "endpoint")}> override model.endpoint</label>
<label>model.endpoint <input type="text" name="project_model_endpoint" value="{html.escape(_project_value(project, "model", "endpoint"))}" autocomplete="off"></label>
<label class="check-inline"><input type="checkbox" name="use_model_name" value="true"{_checked(project, "model", "name")}> override model.name</label>
<label>model.name <input type="text" name="project_model_name" value="{html.escape(_project_value(project, "model", "name"))}" autocomplete="off"></label>
<label class="check-inline"><input type="checkbox" name="use_model_temperature" value="true"{_checked(project, "model", "temperature")}> override model.temperature</label>
<label>model.temperature <input type="text" name="project_model_temperature" value="{html.escape(_project_value(project, "model", "temperature"))}" autocomplete="off"></label>
<label class="check-inline"><input type="checkbox" name="use_prompt_interpret" value="true"{_checked(project, "prompts", "interpret")}> override prompts.interpret</label>
<label>prompts.interpret <input type="text" name="project_prompt_interpret" value="{html.escape(_project_value(project, "prompts", "interpret"))}" autocomplete="off"></label>
<label class="check-inline"><input type="checkbox" name="use_prompt_discovery_hints" value="true"{_checked(project, "prompts", "discovery_hints")}> override prompts.discovery_hints</label>
<label>prompts.discovery_hints <input type="text" name="project_prompt_discovery_hints" value="{html.escape(_project_value(project, "prompts", "discovery_hints"))}" autocomplete="off"></label>
<label class="check-inline"><input type="checkbox" name="use_extract_work_dir" value="true"{_checked(project, "paths", "extract_work_dir")}> override paths.extract_work_dir</label>
<label>paths.extract_work_dir <input type="text" name="project_extract_work_dir" value="{html.escape(_project_value(project, "paths", "extract_work_dir"))}" autocomplete="off"></label>
<label class="check-inline"><input type="checkbox" name="researcher_mode" value="true"{mode_checked}> researcher_mode — hide the Review column</label>
<p class="actions">
<button type="submit" form="studio-cancel" class="secondary">Cancel</button>
<button type="submit">Save project overrides</button>
</p>
</form>
<form method="post" action="/studio" id="studio-cancel">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="cancel">
</form>
"""
    return page("Studio config", body)
