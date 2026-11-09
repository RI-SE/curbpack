"""Studio settings view-model. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.jsonio import read_json
from discovery.studio import created_studio_config, editor_values, studio_file

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
