"""Pack sources view-model, curbpack POST, and pack-document POST. The URL stays on the old server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from checks.run import _pack_version_dir, claims_dir, packs_dir, reports_dir, results_dir
from common.errors import ModelError
from common.jsonio import read_json, write_json
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import load_repos
from requirements.catalog import list_formex_adapter_choices, make_document_id
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


def _save_pack_document(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    repo_id = (form.get("repo") or [""])[0].strip()
    if not repo_id:
        raise ModelError("pack", "repo", "a chosen repository")
    pack_fields = dict(
        name=(form.get("name") or [""])[0],
        official_name=(form.get("official_name") or [""])[0],
        url=(form.get("url") or [""])[0],
        adapter_id=(form.get("adapter_id") or [""])[0],
    )
    if (form.get("action") or [""])[0].strip() == "update":
        _update_pack_info(
            ws,
            repo_id,
            (form.get("pack") or [""])[0],
            **pack_fields,
        )
        return f"/requirements?repo={quote(repo_id)}&updated=1"
    _add_pack_to_repo(ws, repo_id, **pack_fields)
    return f"/requirements?repo={quote(repo_id)}&added=1"


def _add_pack_to_repo(
    ws: Workspace,
    repo_id: str,
    *,
    name: str,
    official_name: str,
    url: str,
    adapter_id: str = "",
) -> None:
    from app.server import _adapter_for_url, _registered_repo_path, _write_curbpack
    from common.validate import validate_curbpack_config, validate_pack
    from requirements.extract.pipeline import draft_pack

    repo = _registered_repo_path(ws, repo_id)
    config_path = repo / "curbpack.json"
    if not config_path.is_file():
        raise ModelError("curbpack.json", "repo", "a curbpack.json in the chosen repository")
    raw = read_json(config_path)
    config = raw if isinstance(raw, dict) else {}
    pack_id = make_document_id(name)
    checked = validate_curbpack_config(config)
    wanted = (adapter_id or "").strip()
    inferred = _adapter_for_url(url.strip()) if url.strip() else None
    if wanted and (inferred is None or str(inferred.get("id") or "") != wanted):
        raise ModelError("pack", "adapter", "the adapter that matches this URL")
    pack_dir = packs_dir(repo, checked) / pack_id / draft_pack()["version"]
    if (pack_dir / "pack.json").is_file():
        raise ModelError("pack", "id", f"a new pack, not existing {pack_id}")
    pack: dict = {"id": pack_id, "name": name.strip(), "version": draft_pack()["version"]}
    source = {}
    if official_name.strip():
        source["instrument"] = official_name.strip()
    if url.strip():
        source["url"] = url.strip()
    if source:
        pack["source"] = source
    checked_pack = validate_pack(pack)
    pack_dir.mkdir(parents=True, exist_ok=True)
    write_json(pack_dir / "pack.json", checked_pack)
    packs = [item for item in config.get("packs") or [] if isinstance(item, str)]
    if pack_id not in packs:
        packs.append(pack_id)
    _write_curbpack(repo, packs)


def _update_pack_info(
    ws: Workspace,
    repo_id: str,
    pack_id: str,
    *,
    name: str,
    official_name: str,
    url: str,
    adapter_id: str = "",
) -> None:
    """Write name and source on an existing pack.json. Does not add a field for the adapter."""
    from app.server import _adapter_for_url, _locate_repo_pack
    from common.validate import validate_pack

    located = _locate_repo_pack(ws, (pack_id or "").strip(), repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    _chosen, pack_dir, pack = located
    wanted = (adapter_id or "").strip()
    cleaned_url = "" if wanted == "manual" else url.strip()
    inferred = _adapter_for_url(cleaned_url) if cleaned_url else None
    if wanted and wanted != "manual" and (
        inferred is None or str(inferred.get("id") or "") != wanted
    ):
        raise ModelError("pack", "adapter", "the adapter that matches this URL")
    if name.strip():
        pack["name"] = name.strip()
    source = dict(pack["source"]) if isinstance(pack.get("source"), dict) else {}
    official = official_name.strip()
    if official:
        source["instrument"] = official
    else:
        source.pop("instrument", None)
    if cleaned_url:
        source["url"] = cleaned_url
    else:
        source.pop("url", None)
    if source:
        pack["source"] = source
    else:
        pack.pop("source", None)
    write_json(pack_dir / "pack.json", validate_pack(pack))
