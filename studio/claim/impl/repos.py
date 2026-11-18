"""Product repositories Discover can search.

Operational UI state, like the requirements catalog. Not a Pack, not a Claim,
and not a store of candidates.
"""

from __future__ import annotations

import re
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json

REPOS_NAME = "product_repos.json"


def repos_path(root: Path) -> Path:
    return root / REPOS_NAME


def load_repos(root: Path) -> dict:
    path = repos_path(root)
    if not path.is_file():
        return {"repos": []}
    data = read_json(path)
    if not isinstance(data, dict):
        return {"repos": []}
    repos = data.get("repos")
    if not isinstance(repos, list):
        return {"repos": []}
    return {"repos": [row for row in repos if isinstance(row, dict)]}


def save_repos(root: Path, data: dict) -> None:
    repos = data.get("repos") if isinstance(data, dict) else None
    if not isinstance(repos, list):
        raise ModelError("repo", "repos", "a list")
    write_json(repos_path(root), {"repos": repos})


def resolve_repo_path(root: Path, path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def add_repo(root: Path, data: dict, *, name: str, path: str) -> dict:
    """Append one product repository. The path must already be a directory."""
    name = (name or "").strip()
    raw = (path or "").strip()
    if not name:
        raise ModelError("repo", "name", "a repository name")
    if not raw:
        raise ModelError("repo", "path", "a directory path")
    repo_id = _repo_id(name)
    for row in data.get("repos") or []:
        if row.get("id") == repo_id:
            raise ModelError("repo", "id", f"a new repository, not existing {repo_id}")
    resolved = resolve_repo_path(root, raw)
    if not resolved.is_dir():
        raise ModelError("repo", "path", f"an existing directory, not {resolved}")
    data.setdefault("repos", []).append(
        {
            "id": repo_id,
            "name": name,
            "path": raw,
            "last_status": "idle",
        }
    )
    return data


def find_repo(data: dict, repo_id: str) -> dict | None:
    for row in data.get("repos") or []:
        if row.get("id") == repo_id:
            return row
    return None


def set_repo_status(root: Path, repo_id: str, status: str) -> None:
    data = load_repos(root)
    row = find_repo(data, repo_id)
    if row is None:
        return
    row["last_status"] = status
    save_repos(root, data)


def _repo_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ModelError("repo", "name", "a repository name")
    return slug
