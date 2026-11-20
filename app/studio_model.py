"""Studio settings view-model and POST. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.errors import ModelError
from common.jsonio import read_json
from discovery.studio import (
    created_studio_config,
    editor_values,
    effective_studio,
    project_from_form,
    save_project_studio,
    save_user_studio,
    studio_file,
    user_from_form,
    user_studio_file,
)

if TYPE_CHECKING:
    from app.server import Workspace


def _home(ws: Workspace):
    return getattr(ws, "studio_home", None)


def _studio_model(ws: Workspace, query: dict) -> dict:
    from app.server import _door_chrome, _registered_repo_path

    door = _door_chrome(ws, query)
    repo_id = str(door.get("repo_id") or "")
    home = _home(ws)
    user_path = user_studio_file(home)
    user_present = user_path.is_file()
    user_raw = read_json(user_path) if user_present else created_studio_config()
    project = {}
    project_present = False
    project_path = ""
    repo = None
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        project_path = str(studio_file(repo).resolve())
        project_present = studio_file(repo).is_file()
        if project_present:
            project = read_json(studio_file(repo))
    chosen = effective_studio(repo, home)
    sends = bool(chosen.pop("api_key_for_call"))
    chosen["model"]["api_key"]["value"] = "" if user_raw.get("model", {}).get("api_key") in (None, "") else str(user_raw["model"]["api_key"])
    return {
        "door": door,
        "user_values": editor_values(user_raw if isinstance(user_raw, dict) else created_studio_config()),
        "user_present": user_present,
        "user_path": str(user_path),
        "project": project if isinstance(project, dict) else {},
        "project_present": project_present,
        "project_path": project_path,
        "effective": chosen,
        "sends_api_key": sends,
    }


def _save_studio(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path, _sync_open_repo

    repo_id = _sync_open_repo(ws, form)
    if not repo_id:
        raise ModelError("studio", "repo", "a chosen repository")
    action = (form.get("action") or [""])[0].strip()
    repo = _registered_repo_path(ws, repo_id)
    quoted = quote(repo_id, safe="")
    if action == "save_user":
        save_user_studio(user_from_form(form), _home(ws))
        return f"/studio?repo={quoted}&saved=user"
    if action == "save_project":
        save_project_studio(repo, project_from_form(form))
        return f"/studio?repo={quoted}&saved=project"
    return f"/studio?repo={quoted}"
