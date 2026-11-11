"""Pack sections view-model and catalog POST. The URL stays on the old server."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from common.errors import ModelError
from common.store import load_pack_directory
from requirements.catalog import (
    add_section,
    ensure_catalog,
    find_document,
    list_formex_adapter_choices,
    make_id,
    save_catalog,
)
from requirements.workspace import selected_copy

if TYPE_CHECKING:
    from app.server import Workspace


def _requirement_section(requirement: dict) -> str:
    from app.server import _requirement_locators

    locators = _requirement_locators(requirement)
    return locators[0] if locators else ""


def _sections_with_requirements(requirements: list[dict], section_ids: list[str]) -> list[str]:
    from app.server import _locator_section, _requirement_locators

    found: list[str] = []
    seen: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        for locator in _requirement_locators(requirement):
            section_id = _locator_section(locator, section_ids)
            if not section_id or section_id in seen:
                continue
            seen.add(section_id)
            found.append(section_id)
    return found


def _sections_named_by_locators(requirements: list[dict]) -> list[str]:
    """Section names written in locator when the pack has no adapter."""
    names = []
    seen = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        section_id = _requirement_section(requirement)
        if not section_id or section_id in seen:
            continue
        seen.add(section_id)
        names.append(section_id)
    return sorted(names)


def _pack_has_requirements(pack_dir: Path) -> bool:
    return any(path.name != "pack.json" for path in pack_dir.glob("*.json"))


def _repo_pack_sections_model(ws: Workspace, query: dict, pack_id: str) -> dict:
    """Sections of a pack named in curbpack.json. Not a registered_sources document."""
    from app.server import (
        _adapter_for_url,
        _adapter_section_ids,
        _catalog_job,
        _catalog_message,
        _door_path_fields,
        _listed_repos,
        _load_adapter,
        _locate_repo_pack,
    )

    repo_id = (query.get("repo") or [""])[0].strip()
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("catalog", "document", f"a known document, not {pack_id}")
    found_repo, pack_dir, pack = located
    source = pack.get("source") if isinstance(pack.get("source"), dict) else {}
    url = str(source.get("url") or "")
    adapter = _adapter_for_url(url)
    if adapter is None:
        _adapter_dir, adapter = _load_adapter("manual")
    has_requirements = _pack_has_requirements(pack_dir)
    document = {
        "id": pack_id,
        "name": str(pack.get("name") or pack_id),
        "official_name": str(source.get("instrument") or ""),
        "url": url,
        "adapter_id": str(adapter.get("id") or ""),
        "repo_id": found_repo,
    }
    ready_sections = [
        section
        for section in adapter.get("sections") or []
        if isinstance(section, dict)
        and section.get("ready") is True
        and section.get("in_scope") is True
    ]
    ready_ids = {str(section.get("id") or "") for section in ready_sections}
    manual = adapter.get("id") == "manual"
    shown: set[str] = set()
    sources: list[dict] = []
    requirements: list[dict] = []
    if has_requirements:
        _loaded, requirements = load_pack_directory(pack_dir)
    if manual:
        for section_id in _sections_named_by_locators(requirements):
            if section_id in shown:
                continue
            shown.add(section_id)
            extractable = section_id in ready_ids
            sources.append(
                {
                    "adapter_id": str(adapter.get("id") or ""),
                    "source_id": make_id("section", section_id),
                    "section_id": section_id,
                    "url": url,
                    "extract_enabled": extractable,
                    "section_ready": True if extractable else None,
                    "source_format": adapter.get("source_format") or "",
                    "document_id": pack_id,
                    "pack_dir": str(pack_dir.resolve()),
                    "copies": [],
                    "repo_id": found_repo,
                    "edit_repo": found_repo,
                    "edit_pack": pack_id,
                    "edit_section": section_id,
                    "signed_count": None,
                    "unsigned_count": None,
                }
            )
    else:
        section_ids = _adapter_section_ids(adapter)
        for section_id in _sections_with_requirements(requirements, section_ids):
            if section_id in shown:
                continue
            shown.add(section_id)
            extractable = section_id in ready_ids
            sources.append(
                {
                    "adapter_id": str(adapter.get("id") or ""),
                    "source_id": f"{adapter.get('id')}-{section_id}",
                    "section_id": section_id,
                    "url": url,
                    "extract_enabled": extractable,
                    "section_ready": True if extractable else False,
                    "source_format": adapter.get("source_format") or "",
                    "document_id": pack_id,
                    "pack_dir": str(pack_dir.resolve()),
                    "copies": [],
                    "repo_id": found_repo,
                    "edit_repo": found_repo,
                    "edit_pack": pack_id,
                    "edit_section": section_id,
                    "signed_count": None,
                    "unsigned_count": None,
                }
            )
    catalog = ensure_catalog(ws.root)
    for row in catalog.get("sources") or []:
        if not isinstance(row, dict) or row.get("document_id") != pack_id:
            continue
        section_id = str(row.get("section_id") or "")
        if not section_id or section_id in shown or section_id not in ready_ids:
            continue
        shown.add(section_id)
        sources.append(
            {
                "adapter_id": str((adapter or {}).get("id") or ""),
                "source_id": str(row.get("id") or section_id),
                "section_id": section_id,
                "url": str(row.get("url") or url),
                "section_ready": True,
                "source_format": (adapter or {}).get("source_format") or "",
                "document_id": pack_id,
                "pack_dir": str(pack_dir.resolve()),
                "copies": [],
                "repo_id": found_repo,
                "signed_count": None,
                "unsigned_count": None,
            }
        )
    legal = adapter.get("source") if isinstance(adapter, dict) and isinstance(adapter.get("source"), dict) else {}
    adapters = []
    if adapter is not None:
        adapters.append(
            {
                "id": adapter.get("id"),
                "instrument": legal.get("instrument") or adapter.get("id"),
                "url": url,
                "sections": [
                    section for section in ready_sections if str(section.get("id") or "") not in shown
                ],
            }
        )
    return {
        "document": document,
        "sources": sources,
        "adapters": adapters,
        "repos": _listed_repos(ws),
        "repo_id": found_repo,
        "repo_pack": True,
        "edit_repo": "",
        "edit_pack": "",
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Section added."),
        "error": (query.get("error") or [""])[0],
        **_door_path_fields(ws, found_repo),
    }


def _catalog_model(ws: Workspace, query: dict, document_id: str) -> dict:
    from app.server import (
        _catalog_job,
        _catalog_message,
        _door_path_fields,
        _formex_sources,
        _listed_repos,
        _locate_repo_pack,
        _registered_sources,
        _shown_pack_dir,
        _sync_open_repo,
    )

    repo_id = _sync_open_repo(ws, query)
    if not repo_id:
        return {
            "document": {},
            "sources": [],
            "adapters": [],
            "repos": _listed_repos(ws),
            "repo_id": "",
            "job": None,
            "message": "",
            "error": "",
        }
    if _locate_repo_pack(ws, document_id, repo_id) is not None:
        return _repo_pack_sections_model(ws, query, document_id)
    catalog = ensure_catalog(ws.root)
    document = find_document(catalog, document_id)
    if document is None:
        return _repo_pack_sections_model(ws, query, document_id)
    adapter_id = str(document.get("adapter_id") or "")
    adapters = []
    for item in list_formex_adapter_choices():
        if item.get("id") != adapter_id:
            continue
        adapters.append(
            {
                **item,
                "sections": [
                    section
                    for section in item.get("sections") or []
                    if section.get("ready") and section.get("in_scope")
                ],
            }
        )
    sources = [
        row for row in _registered_sources(ws) if row.get("document_id") == document_id
    ]
    pack_id = ""
    for item in _formex_sources():
        if item.get("id") == adapter_id:
            pack_id = str(item.get("pack_id") or "")
            break
    pack_dir = ""
    if pack_id:
        chosen = selected_copy(ws.root, pack_id)
        pack_dir = _shown_pack_dir(ws, pack_id, chosen)
    for row in sources:
        row["pack_dir"] = pack_dir
    document = dict(document)
    document["repo_id"] = repo_id
    return {
        "document": document,
        "sources": sources,
        "adapters": adapters,
        "repos": _listed_repos(ws),
        "repo_id": repo_id,
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Section added."),
        "error": (query.get("error") or [""])[0],
        **_door_path_fields(ws, repo_id),
    }


def _add_catalog_section(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    catalog = ensure_catalog(ws.root)
    document_id = (form.get("document_id") or [""])[0].strip()
    section_id = (form.get("section_id") or [""])[0]
    repo_id = (form.get("repo") or [""])[0].strip()
    if find_document(catalog, document_id) is None:
        _add_pack_section(ws, document_id, repo_id, section_id)
    else:
        add_section(
            catalog,
            document_id=document_id,
            section_id=section_id,
        )
        save_catalog(ws.root, catalog)
    located = f"document={quote(document_id, safe='')}&added=1"
    if repo_id:
        located += f"&repo={quote(repo_id, safe='')}"
    return f"/requirements?{located}"


def _add_pack_section(ws: Workspace, pack_id: str, repo_id: str, section_id: str) -> None:
    """Remember a section on this Pack. Does not write a Requirement."""
    from app.server import _adapter_for_url, _locate_repo_pack

    section_id = (section_id or "").strip()
    if not section_id:
        raise ModelError("pack", "section_id", "a section id")
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    _repo_id, _pack_dir, pack = located
    source = pack.get("source") if isinstance(pack.get("source"), dict) else {}
    url = str(source.get("url") or "")
    adapter = _adapter_for_url(url)
    if adapter is None:
        raise ModelError("pack", "adapter", "an adapter for this pack")
    match = next(
        (
            item
            for item in adapter.get("sections") or []
            if isinstance(item, dict)
            and item.get("id") == section_id
            and item.get("ready") is True
            and item.get("in_scope") is True
        ),
        None,
    )
    if match is None:
        raise ModelError("pack", "section_id", "a section that can be extracted")
    catalog = ensure_catalog(ws.root)
    for row in catalog.get("sources") or []:
        if (
            isinstance(row, dict)
            and row.get("document_id") == pack_id
            and row.get("section_id") == section_id
        ):
            return
    catalog.setdefault("sources", []).append(
        {
            "id": make_id(str(adapter.get("id") or ""), section_id),
            "document_id": pack_id,
            "name": str(pack.get("name") or pack_id),
            "official_name": str(match.get("title") or ""),
            "url": url,
            "adapter_id": adapter.get("id"),
            "section_id": section_id,
        }
    )
    save_catalog(ws.root, catalog)
