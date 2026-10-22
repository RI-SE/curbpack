"""Workspace catalog of registered regulatory sources for the Requirements UI.

This is operational UI state: which adapter+section rows appear on /requirements.
It is not Packs v2 and not a revival of PoC1 `sources.json` as a domain schema.
Adapters remain the authority for instrument metadata and section readiness.
"""

from __future__ import annotations

import re
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json
from requirements.extract.adapter import list_adapters

CATALOG_NAME = "registered_sources.json"

_DEFAULT_ROWS = (
    ("cra-xml", "VII", "CRA Annex VII"),
    ("nis", "Art.21", "NIS2 Article 21"),
)


def catalog_path(root: Path) -> Path:
    return root / CATALOG_NAME


def load_catalog(root: Path) -> dict:
    path = catalog_path(root)
    if not path.is_file():
        return {"documents": [], "sources": []}
    data = read_json(path)
    if not isinstance(data, dict):
        return {"documents": [], "sources": []}
    documents = data.get("documents")
    sources = data.get("sources")
    loaded = {
        "documents": [row for row in documents if isinstance(row, dict)]
        if isinstance(documents, list)
        else [],
        "sources": [row for row in sources if isinstance(row, dict)]
        if isinstance(sources, list)
        else [],
    }
    return attach_documents(loaded)


def save_catalog(root: Path, data: dict) -> None:
    sources = data.get("sources") if isinstance(data, dict) else None
    documents = data.get("documents") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        raise ModelError("catalog", "sources", "a list")
    if not isinstance(documents, list):
        documents = []
    write_json(catalog_path(root), {"documents": documents, "sources": sources})


def ensure_catalog(root: Path) -> dict:
    """Load the catalog, seeding default formex rows when the file is missing."""
    path = catalog_path(root)
    if path.is_file():
        return load_catalog(root)
    data = attach_documents({"documents": [], "sources": default_sources()})
    save_catalog(root, data)
    return data


def default_sources() -> list[dict]:
    adapters = {item["id"]: item for item in list_adapters() if item.get("source_format") == "formex"}
    rows = []
    for adapter_id, section_id, name in _DEFAULT_ROWS:
        adapter = adapters.get(adapter_id)
        if adapter is None:
            continue
        section = _section(adapter, section_id)
        if section is None:
            continue
        legal = adapter.get("source") or {}
        rows.append(
            {
                "id": make_id(adapter_id, section_id),
                "name": name,
                "official_name": str(section.get("title") or ""),
                "url": str(legal.get("url") or ""),
                "adapter_id": adapter_id,
                "section_id": section_id,
            }
        )
    return rows


def make_id(adapter_id: str, section_id: str) -> str:
    adapter = adapter_id.strip().lower()
    section = re.sub(r"[^a-z0-9]+", "-", section_id.strip().lower()).strip("-")
    return f"{adapter}-{section}"


def make_document_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "document"


def attach_documents(data: dict) -> dict:
    """Give each section row a document. Older catalogs stored only section rows."""
    documents = data.setdefault("documents", [])
    if not isinstance(documents, list):
        documents = []
        data["documents"] = documents
    by_id = {row.get("id"): row for row in documents if isinstance(row, dict)}
    for source in data.get("sources") or []:
        if not isinstance(source, dict):
            continue
        adapter_id = str(source.get("adapter_id") or "")
        existing_id = source.get("document_id")
        if existing_id in by_id and by_id[existing_id].get("adapter_id") == adapter_id:
            continue
        doc_id = _document_id_for(str(source.get("name") or ""), adapter_id, by_id)
        if doc_id not in by_id:
            document = {
                "id": doc_id,
                "name": str(source.get("name") or ""),
                "official_name": str(source.get("official_name") or ""),
                "url": str(source.get("url") or ""),
                "adapter_id": adapter_id,
            }
            documents.append(document)
            by_id[doc_id] = document
        source["document_id"] = doc_id
    return data


def _document_id_for(name: str, adapter_id: str, existing: dict) -> str:
    base = make_document_id(name)
    current = existing.get(base)
    if current is None or current.get("adapter_id") == adapter_id:
        return base
    return f"{base}-{make_document_id(adapter_id)}"


def find_document(data: dict, document_id: str) -> dict | None:
    for row in data.get("documents") or []:
        if row.get("id") == document_id:
            return row
    return None


def add_document(
    data: dict,
    *,
    name: str,
    url: str,
    adapter_id: str,
    official_name: str = "",
) -> dict:
    """Register a document. The section is chosen later, in Pack Editor."""
    attach_documents(data)
    name = (name or "").strip()
    url = (url or "").strip()
    adapter_id = (adapter_id or "").strip()
    official = (official_name or "").strip()
    if not name:
        raise ModelError("catalog", "name", "a document name")
    if not url:
        raise ModelError("catalog", "url", "a source URL")
    if not adapter_id:
        raise ModelError("catalog", "adapter_id", "an adapter id")
    choices = {item["id"]: item for item in list_formex_adapter_choices()}
    if adapter_id not in choices:
        known = ", ".join(sorted(choices)) or "(none)"
        raise ModelError("catalog", "adapter_id", f"a formex adapter among {known}")
    doc_id = make_document_id(name)
    if find_document(data, doc_id) is not None:
        raise ModelError("catalog", "id", f"a new document, not existing {doc_id}")
    data.setdefault("documents", []).append(
        {
            "id": doc_id,
            "name": name,
            "official_name": official,
            "url": url,
            "adapter_id": adapter_id,
        }
    )
    return data


def add_section(data: dict, *, document_id: str, section_id: str) -> dict:
    """Register one extractable section of the document's adapter."""
    attach_documents(data)
    document = find_document(data, (document_id or "").strip())
    if document is None:
        raise ModelError("catalog", "document_id", "a document in the catalog")
    section_id = (section_id or "").strip()
    if not section_id:
        raise ModelError("catalog", "section_id", "a section id")
    adapter_id = str(document.get("adapter_id") or "")
    choices = {item["id"]: item for item in list_formex_adapter_choices()}
    adapter = choices.get(adapter_id)
    if adapter is None:
        raise ModelError("catalog", "adapter_id", f"a formex adapter, not {adapter_id}")
    section = next((item for item in adapter["sections"] if item["id"] == section_id), None)
    if section is None or not (section.get("ready") and section.get("in_scope")):
        raise ModelError("catalog", "section_id", "a section that can be extracted")
    sid = make_id(adapter_id, section_id)
    for row in data.get("sources") or []:
        if row.get("id") == sid or (
            row.get("adapter_id") == adapter_id and row.get("section_id") == section_id
        ):
            raise ModelError("catalog", "id", f"a new source, not existing {sid}")
    official = str(section.get("title") or document.get("official_name") or "")
    data.setdefault("sources", []).append(
        {
            "id": sid,
            "document_id": document["id"],
            "name": str(document.get("name") or ""),
            "official_name": official,
            "url": str(document.get("url") or ""),
            "adapter_id": adapter_id,
            "section_id": section_id,
        }
    )
    return data


def list_formex_adapter_choices() -> list[dict]:
    """Adapters and sections offered in the Add-source dialog."""
    rows = []
    for item in list_adapters():
        if item.get("source_format") != "formex":
            continue
        legal = item.get("source") or {}
        rows.append(
            {
                "id": item["id"],
                "instrument": str(legal.get("instrument") or item["id"]),
                "url": str(legal.get("url") or ""),
                "sections": [
                    {
                        "id": section["id"],
                        "title": str(section.get("title") or ""),
                        "ready": bool(section.get("ready")),
                        "in_scope": bool(section.get("in_scope")),
                    }
                    for section in item.get("sections") or []
                ],
            }
        )
    return rows


def add_source(
    data: dict,
    *,
    name: str,
    url: str,
    adapter_id: str,
    section_id: str,
    official_name: str = "",
) -> dict:
    """Append one registered source. Adapter and section are fixed for the row."""
    name = (name or "").strip()
    url = (url or "").strip()
    adapter_id = (adapter_id or "").strip()
    section_id = (section_id or "").strip()
    official = (official_name or "").strip()

    if not name:
        raise ModelError("catalog", "name", "a document name")
    if not url:
        raise ModelError("catalog", "url", "a source URL")
    if not adapter_id:
        raise ModelError("catalog", "adapter_id", "an adapter id")
    if not section_id:
        raise ModelError("catalog", "section_id", "a section id")

    choices = {item["id"]: item for item in list_formex_adapter_choices()}
    adapter = choices.get(adapter_id)
    if adapter is None:
        known = ", ".join(sorted(choices)) or "(none)"
        raise ModelError("catalog", "adapter_id", f"a formex adapter among {known}")

    section = next(
        (item for item in adapter["sections"] if item["id"] == section_id),
        None,
    )
    if section is None:
        raise ModelError("catalog", "section_id", f"a section of {adapter_id}")

    sid = make_id(adapter_id, section_id)
    for row in data.get("sources") or []:
        if row.get("id") == sid or (
            row.get("adapter_id") == adapter_id and row.get("section_id") == section_id
        ):
            raise ModelError("catalog", "id", f"a new source, not existing {sid}")

    if not official:
        official = str(section.get("title") or "")

    data.setdefault("sources", []).append(
        {
            "id": sid,
            "name": name,
            "official_name": official,
            "url": url,
            "adapter_id": adapter_id,
            "section_id": section_id,
        }
    )
    return data


def find_source(data: dict, source_id: str) -> dict | None:
    for row in data.get("sources") or []:
        if row.get("id") == source_id:
            return row
    return None


def _section(adapter: dict, section_id: str) -> dict | None:
    for section in adapter.get("sections") or []:
        if section.get("id") == section_id:
            return section
    return None
