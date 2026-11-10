"""Source-details GET model and source POST. The URLs stay on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.errors import ModelError
from requirements.extract.adapter import section_provisions, stage00
from requirements.workspace import mark_source_adapter

if TYPE_CHECKING:
    from pathlib import Path

    from app.server import Workspace


def _adapter_from_query(ws: Workspace, query: dict) -> tuple[Path, dict]:
    from app.server import _load_adapter

    adapter_id = (query.get("adapter") or [""])[0].strip()
    if not adapter_id:
        raise ModelError("source", "adapter", "an adapter id")
    return _load_adapter(adapter_id)


def _inspect_model(ws: Workspace, query: dict) -> dict:
    adapter_dir, adapter = _adapter_from_query(ws, query)
    listed = stage00(adapter, adapter_dir=adapter_dir)
    ready_sections = [
        item
        for item in listed["sections"]
        if item.get("ready") is True and item.get("in_scope") is True
    ]
    inspect_section = (query.get("section") or [""])[0].strip()
    provisions_preview = None
    provision_diagnostics = []
    if inspect_section and any(item["id"] == inspect_section for item in ready_sections):
        extracted = section_provisions(adapter_dir, adapter, inspect_section)
        provisions_preview = extracted["provisions"]
        provision_diagnostics = list(extracted.get("diagnostics") or [])
    sections = []
    for item in listed["sections"]:
        match = next(
            (section for section in adapter.get("sections") or [] if section.get("id") == item.get("id")),
            {},
        )
        sections.append(
            {
                "id": item.get("id"),
                "title": match.get("title") or "",
                "ready": item.get("ready"),
                "in_scope": item.get("in_scope"),
            }
        )
    return {
        "adapter_id": adapter.get("id"),
        "status": adapter.get("status"),
        "source_format": adapter.get("source_format") or "text",
        "source": adapter.get("source") or {},
        "sections": sections,
        "inventory": listed.get("inventory"),
        "inspect_section": inspect_section,
        "provisions_preview": provisions_preview,
        "provision_diagnostics": provision_diagnostics,
    }


def _select_source(ws: Workspace, form: dict) -> str:
    from app.server import _load_adapter

    adapter_id = (form.get("adapter_id") or [""])[0].strip()
    mark_source_adapter(ws.root, adapter_id)
    _load_adapter(adapter_id)
    return f"/requirements/inspect?adapter={adapter_id}"
