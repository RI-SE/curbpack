"""Empty-folder POST. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from common.errors import ModelError
from discovery.door import set_open_repo
from discovery.repos import add_repo, load_repos, resolve_repo_path, save_repos

if TYPE_CHECKING:
    from app.server import Workspace


def _start_empty_folder(ws: Workspace, folder: str) -> str:
    raw = (folder or "").strip()
    if not raw:
        raise ModelError("curbpack.json", "folder", "a working folder")
    resolved = resolve_repo_path(ws.root, raw)
    resolved.mkdir(parents=True, exist_ok=True)
    target = resolved / "curbpack.json"
    data = load_repos(ws.root)
    name = resolved.name or "repo"
    try:
        data = add_repo(ws.root, data, name=name, path=str(resolved))
        save_repos(ws.root, data)
        repo_id = str((data.get("repos") or [])[-1].get("id") or "")
    except ModelError:
        repo_id = ""
        for row in data.get("repos") or []:
            if resolve_repo_path(ws.root, str(row.get("path") or "")) == resolved:
                repo_id = str(row.get("id") or "")
                break
        if not repo_id:
            raise
    if target.exists() and not target.is_file():
        raise ModelError("curbpack.json", "folder", "a working folder")
    set_open_repo(ws.root, repo_id)
    return f"/requirements?repo={quote(repo_id)}"
