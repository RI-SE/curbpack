"""Project page: choose, add, create, and edit the open product repository."""

from __future__ import annotations

import html
from pathlib import Path

from app.pages import page
from checks.defaults import created_curbpack
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.validate import validate_curbpack_config
from discovery.door import open_repo_id, save_directory_fields, set_open_repo
from discovery.repos import add_repo, find_repo, load_repos, resolve_repo_path, save_repos


def ensure_repos_populated(workspace: Path) -> dict:
    """When product_repos.json is missing or empty, scan for curbpack.json.

    Looks at immediate children of the workspace and of its parent (siblings).
    """
    data = load_repos(workspace)
    repos = data.get("repos") or []
    if repos:
        return data
    ws = workspace.resolve()
    roots = [ws]
    # Skip looking into parent dirs for now! 
    #  parent = ws.parent
    #  if parent != ws and parent.is_dir():
    #   roots.append(parent) 
    changed = False
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            resolved = child.resolve()
            if resolved == ws or str(resolved) in seen:
                continue
            if not (resolved / "curbpack.json").is_file():
                continue
            seen.add(str(resolved))
            try:
                add_repo(workspace, data, name=child.name, path=str(resolved))
                changed = True
            except ModelError:
                continue
    if changed:
        save_repos(workspace, data)
    return data


def project_model(workspace: Path, *, message: str = "", error: str = "") -> dict:
    data = ensure_repos_populated(workspace)
    repos = [row for row in (data.get("repos") or []) if isinstance(row, dict)]
    repo_id = open_repo_id(workspace) or ""
    editor = {
        "repo_id": repo_id,
        "file_absent": False,
        "packs_dir_value": "",
        "claims_dir_value": "",
        "results_dir_value": "",
        "reports_dir_value": "",
        "curbpack_file": "",
        "path": "",
        "name": "",
    }
    if repo_id:
        row = find_repo(data, repo_id) or {}
        editor["name"] = str(row.get("name") or repo_id)
        editor["path"] = str(row.get("path") or "")
        repo = resolve_repo_path(workspace, str(row.get("path") or ""))
        config_path = repo / "curbpack.json"
        editor["curbpack_file"] = str(config_path.resolve())
        if not config_path.is_file():
            editor["file_absent"] = True
            defaults = created_curbpack()
            editor["packs_dir_value"] = str(defaults["packs_dir"])
            editor["claims_dir_value"] = str(defaults["claims_dir"])
            editor["results_dir_value"] = str(defaults["results_dir"])
            editor["reports_dir_value"] = str(defaults["reports_dir"])
        else:
            config = validate_curbpack_config(read_json(config_path))
            editor["packs_dir_value"] = str(config["packs_dir"])
            editor["claims_dir_value"] = str(config["claims_dir"])
            editor["results_dir_value"] = str(config["results_dir"])
            editor["reports_dir_value"] = str(config["reports_dir"])
    return {
        "repos": repos,
        "repo_id": repo_id,
        "editor": editor,
        "message": message,
        "error": error,
    }


def project_page(model: dict) -> bytes:
    repos = model.get("repos") or []
    repo_id = str(model.get("repo_id") or "")
    editor = model.get("editor") or {}
    rows = []
    for row in repos:
        if not isinstance(row, dict):
            continue
        row_id = str(row.get("id") or "")
        name = str(row.get("name") or row_id)
        path = str(row.get("path") or "")
        current = " current" if row_id and row_id == repo_id else ""
        rows.append(
            "<tr class=\"project-row"
            + current
            + "\">"
            f"<td>{html.escape(name)}</td>"
            f"<td><code>{html.escape(path)}</code></td>"
            "<td>"
            f'<form method="post" action="/project" class="inline">'
            f'<input type="hidden" name="action" value="select">'
            f'<input type="hidden" name="repo_id" value="{html.escape(row_id)}">'
            '<button type="submit">Select</button>'
            "</form>"
            "</td>"
            "</tr>"
        )
    table = (
        "<p class=\"muted\">No projects registered yet. Add one below, or place a "
        "<code>curbpack.json</code> in a sibling of the workspace and reload.</p>"
        if not rows
        else (
            "<table><thead><tr><th>Name</th><th>Path</th><th></th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    )
    flash = _flash(str(model.get("message") or ""), str(model.get("error") or ""))
    body = f"""
<h1>Project</h1>
<p class="muted">Choose the product repository Studio works in. Paths come from that
repository's <code>curbpack.json</code>.</p>
{flash}
<div class="card">
<h2>Registered projects</h2>
{table}
</div>
<div class="card">
<h2>Add project</h2>
<form method="post" action="/project">
<input type="hidden" name="action" value="add">
<label>Name <input type="text" name="name" required autocomplete="off"></label>
<label>Path <input type="text" name="path" required autocomplete="off" placeholder="/absolute/or/relative/path"></label>
<p class="actions"><button type="submit">Add</button></p>
</form>
</div>
{_curbpack_card(editor)}
"""
    return page("Project", body, crumbs=[("/project", "Project")])


def handle_project_post(workspace: Path, form: dict) -> str:
    """Apply a /project POST. Returns redirect location."""
    action = (form.get("action") or [""])[0].strip()
    if action == "select":
        repo_id = (form.get("repo_id") or [""])[0].strip()
        set_open_repo(workspace, repo_id)
        return "/"
    if action == "add":
        data = load_repos(workspace)
        add_repo(
            workspace,
            data,
            name=(form.get("name") or [""])[0],
            path=(form.get("path") or [""])[0],
        )
        save_repos(workspace, data)
        new_id = str((data.get("repos") or [])[-1].get("id") or "")
        if new_id:
            set_open_repo(workspace, new_id)
        return "/project?added=1"
    if action in {"create", "save"}:
        repo_id = (form.get("repo_id") or [""])[0].strip()
        if not repo_id:
            raise ModelError("project", "repo_id", "a chosen repository")
        row = find_repo(load_repos(workspace), repo_id)
        if row is None:
            raise ModelError("project", "repo_id", "a registered repository")
        set_open_repo(workspace, repo_id)
        repo = resolve_repo_path(workspace, str(row.get("path") or ""))
        packs_dir = (form.get("packs_dir") or [""])[0].strip()
        claims_dir = (form.get("claims_dir") or [""])[0].strip()
        results_dir = (form.get("results_dir") or [""])[0].strip()
        reports_dir = (form.get("reports_dir") or [""])[0].strip()
        config_path = repo / "curbpack.json"
        if action == "create" or not config_path.is_file():
            document = created_curbpack(
                packs_dir=packs_dir or created_curbpack()["packs_dir"],
                claims_dir=claims_dir or created_curbpack()["claims_dir"],
                results_dir=results_dir or created_curbpack()["results_dir"],
                reports_dir=reports_dir or created_curbpack()["reports_dir"],
            )
            write_json(config_path, document)
        else:
            save_directory_fields(
                repo,
                packs_dir=packs_dir,
                claims_dir=claims_dir,
                results_dir=results_dir,
                reports_dir=reports_dir,
            )
        return "/project?saved=1"
    if action == "cancel":
        return "/project"
    raise ModelError("project", "action", "select, add, create, save, or cancel")


def _curbpack_card(editor: dict) -> str:
    repo_id = str(editor.get("repo_id") or "")
    if not repo_id:
        return (
            '<div class="card"><h2>curbpack.json</h2>'
            '<p class="muted">Select a project to create or edit its curbpack.json.</p></div>'
        )
    absent = bool(editor.get("file_absent"))
    title = "Create curbpack.json" if absent else "Edit curbpack.json"
    action = "create" if absent else "save"
    path_line = (
        f'<p class="muted">Will write <code>{html.escape(str(editor.get("curbpack_file") or ""))}</code></p>'
        if absent
        else f'<p class="muted"><code>{html.escape(str(editor.get("curbpack_file") or ""))}</code></p>'
    )
    return f"""
<div class="card">
<h2>{html.escape(title)}</h2>
<p>Project <strong>{html.escape(str(editor.get("name") or repo_id))}</strong>
<code>{html.escape(str(editor.get("path") or ""))}</code></p>
{path_line}
<form method="post" action="/project">
<input type="hidden" name="action" value="{html.escape(action)}">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<label>packs_dir <input type="text" name="packs_dir" value="{html.escape(str(editor.get("packs_dir_value") or ""))}" autocomplete="off"></label>
<label>claims_dir <input type="text" name="claims_dir" value="{html.escape(str(editor.get("claims_dir_value") or ""))}" autocomplete="off"></label>
<label>results_dir <input type="text" name="results_dir" value="{html.escape(str(editor.get("results_dir_value") or ""))}" autocomplete="off"></label>
<label>reports_dir <input type="text" name="reports_dir" value="{html.escape(str(editor.get("reports_dir_value") or ""))}" autocomplete="off"></label>
<p class="actions">
<button type="submit" form="project-cancel" class="secondary">Cancel</button>
<button type="submit">Save</button>
</p>
</form>
<form method="post" action="/project" id="project-cancel">
<input type="hidden" name="action" value="cancel">
</form>
</div>
"""


def _flash(message: str, error: str) -> str:
    parts = []
    if error:
        parts.append(f'<p class="err">{html.escape(error)}</p>')
    if message:
        parts.append(f'<p class="ok">{html.escape(message)}</p>')
    return "".join(parts)
