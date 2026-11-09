"""Studio settings view-model and POST. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.errors import ModelError
from common.jsonio import read_json
from discovery.studio import created_studio_config, editor_values, save_studio_config, studio_file, studio_from_form

if TYPE_CHECKING:
    from app.server import Workspace


def _studio_model(ws: Workspace, query: dict) -> dict:
    from app.server import _door_chrome, _registered_repo_path

    door = _door_chrome(ws, query)
    repo_id = str(door.get("repo_id") or "")
    values = editor_values(created_studio_config())
    present = False
    path = ""
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        path = str(studio_file(repo).resolve())
        if studio_file(repo).is_file():
            present = True
            values = editor_values(read_json(studio_file(repo)))
    return {"door": door, "values": values, "present": present, "path": path}


def _save_studio(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path, _sync_open_repo

    repo_id = _sync_open_repo(ws, form)
    if not repo_id:
        raise ModelError("studio", "repo", "a chosen repository")
    action = (form.get("action") or [""])[0].strip()
    if action == "save":
        save_studio_config(_registered_repo_path(ws, repo_id), studio_from_form(form))
        return f"/studio?repo={quote(repo_id, safe='')}&saved=1"
    return f"/studio?repo={quote(repo_id, safe='')}"
