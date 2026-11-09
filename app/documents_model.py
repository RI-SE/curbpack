"""Pack sources view-model and curbpack POST. The URL stays on the old server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from checks.run import _pack_version_dir, claims_dir, packs_dir, reports_dir, results_dir
from common.errors import ModelError
from common.jsonio import read_json, write_json
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import load_repos
from requirements.catalog import list_formex_adapter_choices
from requirements.extract.adapter import list_adapters

if TYPE_CHECKING:
    from app.server import Workspace


def _documents_model(ws: Workspace, query: dict) -> dict:
    from app.server import (
        _adapter_for_url,
        _catalog_job,
        _catalog_message,
        _registered_repo_path,
        _sync_open_repo,
    )

    repos = [
        row
        for row in (load_repos(ws.root).get("repos") or [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    repo_id = _sync_open_repo(ws, query)
    documents: list[dict] = []
    curbpack_file = ""
    directory = ""
    claims_directory = ""
    file_absent = False
    no_claims = False
    config: dict = {}
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        config_path = repo / "curbpack.json"
        curbpack_file = str(config_path.resolve()) if config_path.is_file() else str(config_path)
        if not config_path.is_file():
            file_absent = True
        else:
            from common.validate import validate_curbpack_config

            config = validate_curbpack_config(read_json(config_path))
            packs_root = packs_dir(repo, config)
            directory = str(packs_root.resolve())
            claims_root = claims_dir(repo, config)
            claims_directory = str(claims_root.resolve())
            no_claims = not claims_root.is_dir() or not any(claims_root.glob("*.json"))
            for pack_id in config["packs"]:
                try:
                    pack_dir = _pack_version_dir(packs_root, pack_id)
                except ModelError:
                    documents.append(
                        {
                            "id": pack_id,
                            "name": pack_id,
                            "missing": True,
                            "adapter_id": "manual",
                            "extract_enabled": False,
                            "pack_dir": str((packs_root / pack_id).resolve()),
                            "repo_id": repo_id,
                        }
                    )
                    continue
                pack_file = pack_dir / "pack.json"
                pack = read_json(pack_file)
                source = pack.get("source") if isinstance(pack, dict) else {}
                if not isinstance(source, dict):
                    source = {}
                if not isinstance(pack, dict):
                    pack = {}
                url = str(source.get("url") or "")
                adapter = _adapter_for_url(url)
                documents.append(
                    {
                        "id": pack_id,
                        "name": str(pack.get("name") or pack_id),
                        "official_name": str(source.get("instrument") or ""),
                        "url": url,
                        "adapter_id": str(adapter.get("id") or "") if adapter else "manual",
                        "extract_enabled": adapter is not None,
                        "pack_dir": str(pack_dir.resolve()),
                        "repo_id": repo_id,
                    }
                )
    return {
        "documents": documents,
        "repos": repos,
        "repo_id": repo_id,
        "curbpack_file": curbpack_file,
        "directory": directory,
        "claims_dir": claims_directory,
        "results_dir": str(results_dir(_registered_repo_path(ws, repo_id), config)) if repo_id and config else "",
        "reports_dir": str(reports_dir(_registered_repo_path(ws, repo_id), config)) if repo_id and config else "",
        "file_absent": file_absent,
        "no_claims": no_claims,
        "curbpack_fields": config if config else created_curbpack(),
        "show_curbpack_dialog": file_absent or (query.get("curbpack") or [""])[0] == "edit",
        "adapters": list_formex_adapter_choices(),
        "edit_adapters": _edit_adapter_choices(),
        "workspace_root": str(ws.root.resolve()),
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Pack added."),
        "error": (query.get("error") or [""])[0],
    }


def _edit_adapter_choices() -> list[dict]:
    """Adapters a pack row can switch to. Manual Content is added by the dialog."""
    rows = []
    for item in list_adapters():
        if str(item.get("id") or "") == "manual":
            continue
        legal = item.get("source") if isinstance(item.get("source"), dict) else {}
        url = str(legal.get("url") or "")
        if not url:
            continue
        rows.append(
            {
                "id": item.get("id"),
                "instrument": str(legal.get("instrument") or item.get("id") or ""),
                "url": url,
            }
        )
    return rows


def _save_curbpack(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path

    repo_id = (form.get("repo") or [""])[0].strip()
    if not repo_id:
        raise ModelError("curbpack.json", "repo", "a chosen repository")
    set_open_repo(ws.root, repo_id)
    if (form.get("action") or [""])[0].strip() == "save":
        _save_curbpack_form(_registered_repo_path(ws, repo_id), form)
    return f"/requirements?repo={quote(repo_id)}"


def _save_curbpack_form(repo: Path, form: dict) -> None:
    from common.validate import validate_curbpack_config

    packs = [
        item.strip()
        for item in ((form.get("packs") or [""])[0]).split(",")
        if item.strip()
    ]
    exclude = [
        item.strip()
        for item in ((form.get("exclude_requirements") or [""])[0]).split(",")
        if item.strip()
    ]
    hints_raw = (form.get("search_hints") or [""])[0]
    try:
        hints = json.loads(hints_raw) if hints_raw.strip() else created_curbpack()["search_hints"]
    except json.JSONDecodeError:
        raise ModelError("curbpack.json", "search_hints", "JSON object")
    document: dict = {
        "packs": packs,
        "search_hints": hints,
        "packs_dir": (form.get("packs_dir") or [""])[0].strip(),
        "claims_dir": (form.get("claims_dir") or [""])[0].strip(),
        "results_dir": (form.get("results_dir") or [""])[0].strip(),
        "reports_dir": (form.get("reports_dir") or [""])[0].strip(),
        "unsigned_requirements": (form.get("unsigned_requirements") or [""])[0].strip(),
    }
    path = repo / "curbpack.json"
    if path.is_file():
        loaded = read_json(path)
        if isinstance(loaded, dict) and "requirements" in loaded and not exclude:
            document["requirements"] = loaded["requirements"]
    if exclude:
        document["exclude_requirements"] = exclude
        document.pop("requirements", None)
    write_json(path, validate_curbpack_config(document))
