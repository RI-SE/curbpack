"""Which product repository Studio currently has open.

Workspace state only. Directory fields stay in that repository's curbpack.json.
"""

from __future__ import annotations

from pathlib import Path

from checks.defaults import created_curbpack
from checks.run import claims_dir, packs_dir, reports_dir, results_dir
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.validate import validate_curbpack_config
from discovery.repos import find_repo, load_repos, resolve_repo_path

OPEN_NAME = "open-repo.json"
_PATH_FIELDS = ("packs_dir", "claims_dir", "results_dir", "reports_dir")


def open_repo_file(workspace: Path) -> Path:
    return workspace / OPEN_NAME


def set_open_repo(workspace: Path, repo_id: str) -> None:
    repo_id = (repo_id or "").strip()
    if not repo_id or find_repo(load_repos(workspace), repo_id) is None:
        raise ModelError("open-repo.json", "id", "an id already in product_repos.json")
    write_json(open_repo_file(workspace), {"id": repo_id})


def open_repo_id(workspace: Path) -> str | None:
    path = open_repo_file(workspace)
    if not path.is_file():
        return None
    raw = read_json(path)
    if not isinstance(raw, dict):
        return None
    extra = sorted(set(raw) - {"id"})
    if extra:
        return None
    repo_id = raw.get("id")
    if not isinstance(repo_id, str) or not repo_id.strip():
        return None
    if find_repo(load_repos(workspace), repo_id.strip()) is None:
        return None
    return repo_id.strip()


def open_paths(workspace: Path) -> dict | None:
    repo_id = open_repo_id(workspace)
    if repo_id is None:
        return None
    row = find_repo(load_repos(workspace), repo_id)
    if row is None:
        return None
    repo = resolve_repo_path(workspace, str(row.get("path") or ""))
    result = {
        "id": repo_id,
        "path": repo,
        "packs_dir": None,
        "claims_dir": None,
        "results_dir": None,
        "reports_dir": None,
    }
    config_path = repo / "curbpack.json"
    if not config_path.is_file():
        return result
    config = validate_curbpack_config(read_json(config_path))
    result["packs_dir"] = packs_dir(repo, config)
    result["claims_dir"] = claims_dir(repo, config)
    result["results_dir"] = results_dir(repo, config)
    result["reports_dir"] = reports_dir(repo, config)
    return result


def repo_claims_dir(repo: Path) -> Path:
    path = repo / "curbpack.json"
    if not path.is_file():
        raise ModelError("curbpack.json", "claims_dir", "a curbpack.json in the chosen repository")
    return claims_dir(repo, validate_curbpack_config(read_json(path)))


def claim_file_relative(repo: Path, folder: Path, claim_id: str) -> str:
    path = (folder / f"{claim_id}.json").resolve()
    try:
        return path.relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.name


def pack_display_name(repo: Path, pack_id: str) -> str:
    """Name from the pack file named by curbpack.json. The pack id when that file is missing."""
    path = repo / "curbpack.json"
    if not path.is_file():
        return pack_id
    config = validate_curbpack_config(read_json(path))
    if pack_id not in config["packs"]:
        return pack_id
    from checks.run import _pack_version_dir, packs_dir
    from common.store import load_pack_directory

    try:
        directory = _pack_version_dir(packs_dir(repo, config), pack_id)
        pack, _requirements = load_pack_directory(directory)
    except ModelError:
        return pack_id
    name = pack.get("name") if isinstance(pack, dict) else ""
    if isinstance(name, str) and name.strip():
        return name.strip()
    return pack_id


def repo_pack_requirements(repo: Path, pack_id: str) -> list[dict]:
    """Requirements from packs_dir for a pack named in curbpack.json."""
    path = repo / "curbpack.json"
    if not path.is_file():
        raise ModelError("curbpack.json", "packs_dir", "a curbpack.json in the chosen repository")
    config = validate_curbpack_config(read_json(path))
    if pack_id not in config["packs"]:
        return []
    from checks.run import _pack_version_dir
    from common.store import load_pack_directory

    directory = _pack_version_dir(packs_dir(repo, config), pack_id)
    _pack, requirements = load_pack_directory(directory)
    return [item for item in requirements if isinstance(item, dict) and isinstance(item.get("id"), str)]


def save_directory_fields(repo: Path, **fields: str) -> None:
    unknown = sorted(set(fields) - set(_PATH_FIELDS))
    if unknown:
        raise ModelError("curbpack.json", unknown[0], f"one of {list(_PATH_FIELDS)}")
    path = repo / "curbpack.json"
    current = validate_curbpack_config(read_json(path))
    document = dict(current)
    document.update(fields)
    write_json(path, validate_curbpack_config(document))
