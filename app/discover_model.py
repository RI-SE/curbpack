"""Discover packs view-model and repository POST. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from claims.bind import read_claims
from common.errors import ModelError
from common.jsonio import read_json
from discovery.door import pack_display_name, repo_claims_dir, repo_pack_requirements, set_open_repo
from discovery.jobs import read_job as read_discover_job
from discovery.jobs import reviewable_targets
from discovery.repos import add_repo, find_repo, load_repos, resolve_repo_path, save_repos

if TYPE_CHECKING:
    from app.server import Workspace


def _discover_model(ws: Workspace, query: dict, *, product: bool = False) -> dict:
    from app.server import _door_path_fields, _listed_repos, _sync_open_repo

    job = None
    job_id = (query.get("job") or [""])[0]
    if job_id:
        job = read_discover_job(ws.root / "jobs", job_id)
    repos = _listed_repos(ws)
    repo_id = _sync_open_repo(ws, query)
    repo = find_repo({"repos": repos}, repo_id) if repo_id else None
    fields = _door_path_fields(ws, repo_id) if repo_id else {}
    return {
        "mode": "product" if product else "pilot",
        "repo_id": str((repo or {}).get("id") or ""),
        "repo_name": str((repo or {}).get("name") or ""),
        "repos": repos,
        "pack_rows": _discover_pack_rows(ws, repo) if repo else [],
        "reviewable": reviewable_targets(ws.root),
        "job": job,
        "error": (query.get("error") or [""])[0],
        "workspace_root": str(ws.root.resolve()),
        "curbpack_file": fields.get("curbpack_file") or "",
        "directory": fields.get("directory") or "",
        "claims_dir": fields.get("claims_dir") or "",
        "results_dir": fields.get("results_dir") or "",
        "reports_dir": fields.get("reports_dir") or "",
        "packs_dir_value": fields.get("packs_dir_value") or "",
        "claims_dir_value": fields.get("claims_dir_value") or "",
        "results_dir_value": fields.get("results_dir_value") or "",
        "reports_dir_value": fields.get("reports_dir_value") or "",
    }


def _discover_pack_rows(ws: Workspace, repo: dict | None) -> list[dict]:
    """One row per pack named in the selected repo's curbpack.json.

    Requirement counts come from that file's packs directory. Claim counts come
    from its claims directory. Pack-editor working copies are not consulted.
    """
    if not isinstance(repo, dict):
        return []
    try:
        repo_path = resolve_repo_path(ws.root, str(repo.get("path") or ""))
    except ModelError:
        return []
    config_path = repo_path / "curbpack.json"
    if not config_path.is_file():
        return []
    from common.validate import validate_curbpack_config

    try:
        config = validate_curbpack_config(read_json(config_path))
    except ModelError:
        return []
    try:
        folder = repo_claims_dir(repo_path)
        claims = read_claims(folder) if folder.is_dir() else []
    except ModelError:
        claims = []
    claimed = {
        claim.get("requirement_id")
        for claim in claims
        if isinstance(claim, dict)
    }
    rows = []
    for pack_id in config["packs"]:
        try:
            requirements = repo_pack_requirements(repo_path, pack_id)
        except ModelError:
            requirements = []
        ids = {
            item["id"]
            for item in requirements
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        claim_count = sum(
            1
            for claim in claims
            if isinstance(claim, dict) and claim.get("requirement_id") in ids
        )
        unclaimed = sum(1 for requirement_id in ids if requirement_id not in claimed)
        rows.append(
            {
                "pack_id": pack_id,
                "name": pack_display_name(repo_path, pack_id),
                "requirements": len(ids),
                "claims": claim_count,
                "unclaimed": unclaimed,
            }
        )
    return rows


def _add_discover_repo(ws: Workspace, form: dict) -> str:
    from app.server import _safe_local_next

    data = load_repos(ws.root)
    add_repo(
        ws.root,
        data,
        name=(form.get("name") or [""])[0],
        path=(form.get("path") or [""])[0],
    )
    save_repos(ws.root, data)
    new_id = str((data.get("repos") or [])[-1].get("id") or "")
    if new_id:
        set_open_repo(ws.root, new_id)
    next_url = _safe_local_next((form.get("next") or [""])[0])
    if next_url:
        join = "&" if "?" in next_url else "?"
        if new_id and "try_repo=" not in next_url:
            next_url = f"{next_url}{join}try_repo={quote(new_id, safe='')}"
        return next_url
    return "/discover?added=1"
