"""Try-discovery file view-model. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.errors import ModelError
from discovery.repos import find_repo, load_repos, resolve_repo_path
from discovery.try_run import candidate_for_path, load_try_result, read_try_file

if TYPE_CHECKING:
    from app.server import Workspace


def _try_discovery_file_model(ws: Workspace, requirement_id: str, query: dict) -> dict:
    repo_id = (query.get("repo") or [""])[0].strip()
    path = (query.get("path") or [""])[0].strip()
    back = f"/requirements/requirement/{requirement_id}?try_repo={repo_id}&try_open=1"
    data = load_repos(ws.root)
    row = find_repo(data, repo_id)
    if row is None:
        return {
            "path": path,
            "error": f"Unknown repo {repo_id}",
            "back": back,
            "requirement_id": requirement_id,
        }
    repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
    document = load_try_result(ws.root / "jobs", requirement_id, repo_id)
    candidate = candidate_for_path(document, path)
    try:
        body = read_try_file(repo, path)
    except ModelError as exc:
        return {"path": path, "error": str(exc), "back": back, "requirement_id": requirement_id}
    return {
        "path": path,
        "body": body,
        "excerpt": str((candidate or {}).get("excerpt") or ""),
        "model_excerpt": str((candidate or {}).get("model_excerpt") or ""),
        "back": back,
        "requirement_id": requirement_id,
    }
