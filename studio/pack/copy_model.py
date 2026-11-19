"""Working-copy view-model and select POST. The URL stays on the old server."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode

from common.errors import ModelError
from common.keystore import trust_store
from common.store import load_pack_directory
from requirements.catalog import load_catalog
from requirements.workspace import (
    load_working_copy,
    mark_selected,
    mark_source_adapter,
    read_selection,
    resolve_selected_pack,
    selected_copy,
    selected_source_adapter,
)

if TYPE_CHECKING:
    from app.server import Workspace


def _document_for_adapter(root: Path, adapter_id: str) -> dict | None:
    """The pack source for this adapter, when the catalog names exactly one."""
    if not adapter_id:
        return None
    matches = [
        row
        for row in load_catalog(root).get("documents") or []
        if isinstance(row, dict) and str(row.get("adapter_id") or "") == adapter_id
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _copy_document(root: Path, adapter_id: str) -> dict:
    document = _document_for_adapter(root, adapter_id)
    if document is None:
        return {"document_id": "", "document_name": ""}
    return {
        "document_id": str(document.get("id") or ""),
        "document_name": str(document.get("name") or ""),
    }


def _requirement_in_section(requirement: dict, section: str, section_ids: list[str]) -> bool:
    from app.server import _locator_section, _requirement_locators

    locators = _requirement_locators(requirement)
    if not section_ids:
        return section in locators
    return any(_locator_section(locator, section_ids) == section for locator in locators)


def _repo_pack_copy_model(ws: Workspace, query: dict, pack_id: str) -> dict:
    from app.server import (
        _adapter_for_url,
        _adapter_section_ids,
        _locate_repo_pack,
        _pack_query,
        _requirement_rows,
    )

    repo_id = (query.get("repo") or [""])[0].strip()
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    found_repo, pack_dir, _listed = located
    pack, requirements = load_pack_directory(pack_dir)
    section = (query.get("section") or [""])[0].strip()
    if section:
        source = pack.get("source") if isinstance(pack.get("source"), dict) else {}
        matched = _adapter_for_url(str(source.get("url") or ""))
        section_ids = _adapter_section_ids(matched) if matched else []
        requirements = [
            item
            for item in requirements
            if isinstance(item, dict) and _requirement_in_section(item, section, section_ids)
        ]
    trust = trust_store(ws.keys)
    query_string = _pack_query({"repo": [found_repo], "pack": [pack_id]})
    if section:
        query_string = f"{query_string}&section={quote(section, safe='')}"
    extracted_at = ""
    links: dict[str, str] = {}
    addition_ids: set[str] = set()
    if section:
        extracted_at, links, addition_ids = _overlay_section_extract(
            ws, found_repo, pack_id, section, pack_dir, requirements
        )
    rows = _requirement_rows(pack_dir, requirements, trust)
    for item in rows:
        href = links.get(str(item.get("id") or ""), "")
        if href:
            item["changes_href"] = href
            if item["id"] in addition_ids:
                item["changes_only"] = True
    return {
        "adapter_id": "",
        "timestamp": pack_id,
        "pack_dir": str(pack_dir.resolve()),
        "pack_kind": "pack",
        "read_only": False,
        "requirements": rows,
        "comparison": any(item.get("changes_href") for item in rows),
        "coverage_detail": None,
        "message": "",
        "document_id": pack_id,
        "document_name": str(pack.get("name") or pack_id),
        "repo_id": found_repo,
        "pack_id": pack_id,
        "section": section,
        "extracted_at": extracted_at,
        "requirement_query": f"?{query_string}",
    }


def _overlay_section_extract(
    ws: Workspace,
    repo_id: str,
    pack_id: str,
    section: str,
    pack_dir: Path,
    requirements: list,
) -> tuple[str, dict[str, str], set[str]]:
    """Add this section's latest extract beside the pack requirements."""
    from app.server import _registered_repo_path
    from requirements.compare import extraction_review
    from requirements.workspace import load_working_copy
    from studio.pack.section_extract import read_section_extract

    found = read_section_extract(_registered_repo_path(ws, repo_id), pack_id, section)
    if found is None:
        return "", {}, set()
    slot, extracted_at = found
    review = extraction_review(pack_dir, slot)
    addition_ids = {str(item.get("id") or "") for item in review.get("additions") or []}
    present = {item.get("id") for item in requirements if isinstance(item, dict)}
    _proposal_pack, proposed = load_working_copy(slot)
    for item in proposed:
        if isinstance(item, dict) and item.get("id") in addition_ids and item.get("id") not in present:
            requirements.append(item)
    links = {}
    for kind in ("updates", "additions"):
        for item in review.get(kind) or []:
            requirement_id = str(item.get("id") or "")
            if requirement_id:
                links[requirement_id] = "/requirements/compare/form?" + urlencode(
                    [
                        ("requirement", requirement_id),
                        ("pack", pack_id),
                        ("repo", repo_id),
                        ("section", section),
                    ]
                )
    return extracted_at, links, addition_ids


def _copy_model(ws: Workspace, _query: dict) -> dict:
    from app.server import (
        _active_adapter,
        _coverage_detail,
        _requirement_rows,
        _shown_pack_dir,
        _sync_adapter_for_pack,
    )

    pack_id = (_query.get("pack") or [""])[0].strip()
    if pack_id and not (_query.get("proposal") or [""])[0].strip():
        return _repo_pack_copy_model(ws, _query, pack_id)
    from studio.pack.compare_form import comparison_list

    compared = comparison_list(ws, _query)
    selection = read_selection(ws.root)
    if selection and isinstance(selection.get("pack_id"), str):
        _sync_adapter_for_pack(ws, selection["pack_id"])
    adapter = _active_adapter(ws)
    adapter_id = str(adapter.get("id") or "")
    document = _copy_document(ws.root, adapter_id)
    if compared is not None:
        directory = compared["directory"]
        requirements = compared["requirements"]
    else:
        directory = resolve_selected_pack(ws.root)
        if directory is None:
            directory = selected_copy(ws.root, adapter["pack_id"])
        if directory is None:
            return {
                "adapter_id": adapter_id,
                "timestamp": None,
                "requirements": [],
                **document,
            }
        _pack, requirements = load_working_copy(directory)
    trust = trust_store(ws.keys)
    kind = (selection or {}).get("kind") or "working"
    rows = None
    shown_pack, shown_requirements = load_working_copy(directory)
    if (_query.get("imported") or [""])[0] == "1":
        from studio.pack.pack_export import _signature_rows

        rows = _signature_rows(directory, shown_pack, shown_requirements, trust)
    listed = _requirement_rows(directory, requirements, trust)
    for item in listed:
        href = (compared or {}).get("links", {}).get(item["id"], "") if compared else ""
        if href:
            item["changes_href"] = href
    pack_query = (_query.get("pack") or [""])[0].strip()
    repo_query = (_query.get("repo") or [""])[0].strip()
    if compared is not None and pack_query:
        pairs = [("pack", pack_query)]
        if repo_query:
            pairs.append(("repo", repo_query))
        for key in ("proposal", "destination"):
            value = (_query.get(key) or [""])[0].strip()
            if value:
                pairs.append((key, value))
        identity = "?" + urlencode(pairs)
        shown_dir = str(directory.resolve())
        shown_kind = "pack"
    elif compared is not None:
        pairs = [("timestamp", directory.name)]
        for key in ("proposal", "destination"):
            value = (_query.get(key) or [""])[0].strip()
            if value:
                pairs.append((key, value))
        identity = "?" + urlencode(pairs)
        shown_dir = str(directory.resolve())
        shown_kind = "working"
    else:
        identity = str(document.get("requirement_query") or "")
        shown_dir = _shown_pack_dir(ws, str(adapter.get("pack_id") or ""), directory)
        shown_kind = kind
    return {
        "adapter_id": adapter_id,
        "timestamp": directory.name,
        "pack_dir": shown_dir,
        "pack_kind": shown_kind,
        "read_only": kind == "published",
        "requirements": listed,
        "comparison": compared is not None,
        "requirement_query": identity,
        "rows": rows,
        "coverage_detail": _coverage_detail(directory) if kind == "working" else None,
        "message": "Published Pack — read-only. Use Compare to copy into a working copy."
        if kind == "published"
        else "",
        **document,
    }


def _select_working_copy(ws: Workspace, form: dict) -> str:
    from app.server import _load_adapter

    adapter_id = (form.get("adapter_id") or [""])[0].strip() or selected_source_adapter(ws.root)
    _adapter_dir, adapter = _load_adapter(adapter_id)
    timestamp = (form.get("timestamp") or [""])[0].strip()
    if not timestamp:
        raise ModelError(adapter_id, "timestamp", "a dated working copy")
    mark_source_adapter(ws.root, adapter_id)
    mark_selected(ws.root, adapter["pack_id"], timestamp)
    nxt = (form.get("next") or [""])[0].strip()
    if nxt == "edit":
        return "/requirements/copy"
    if nxt == "publish":
        return "/requirements/publish"
    return "/requirements?selected=1"
