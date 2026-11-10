"""Demo requirement GET, save, publish, and pack seal. The URLs stay on the old server."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from studio.pack.requirement_page import requirement_page
from common.errors import ModelError
from common.keystore import load_or_create_key
from common.store import load_requirement, save_requirement
from requirements.editing import apply_edits, publish_requirement, seal_pack_directory
from workflow import snapshot

if TYPE_CHECKING:
    from app.server import Workspace


def _require_demo_requirement(ws: Workspace) -> Path:
    """Legacy Annex VII.3 sample pack used by /requirement and discovery demo steps."""
    path = ws.requirement_path()
    if path.is_file():
        return path
    raise ModelError(
        "demo pack",
        "CRA-ANNEX-VII-RISK.json",
        "a prepared sample under packs/cra-baseline/ "
        "(use Prepare sample workspace on the cover), "
        "or open Requirements catalog for dated extracts from regulation adapters",
    )


def _demo_requirement(ws: Workspace) -> bytes:
    requirement = load_requirement(_require_demo_requirement(ws))
    reading = snapshot(ws.root)["requirement_reading"]
    return requirement_page(requirement, reading)


def edits_for_requirement(requirement: dict, form: dict) -> dict:
    from app.server import _lines

    source = dict(requirement["source"])
    edition = (form.get("edition") or [""])[0].strip()
    if edition:
        source["edition"] = edition
    else:
        source.pop("edition", None)
    hints = {
        "concepts": _lines((form.get("concepts") or [""])[0]),
        "path_hints": _lines((form.get("path_hints") or [""])[0]),
        "expected_evidence": _lines((form.get("expected_evidence") or [""])[0]),
    }
    sources = [{"source": item} for item in _lines((form.get("sources") or [""])[0])]
    if sources:
        hints["sources"] = sources
    hints = {key: value for key, value in hints.items() if value}
    return {
        "source": source,
        "remediation_hint": (form.get("remediation_hint") or [""])[0].strip(),
        "note": (form.get("note") or [""])[0].strip(),
        "discovery_hints": hints,
    }


def _save_demo_requirement(ws: Workspace, form: dict) -> str:
    current = load_requirement(_require_demo_requirement(ws))
    edited = apply_edits(current, edits_for_requirement(current, form))
    save_requirement(ws.pack, edited)
    return "/requirement?saved=1"


def _publish_demo_requirement(ws: Workspace, form: dict) -> str:
    from app.server import _now

    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    current = load_requirement(_require_demo_requirement(ws))
    published = publish_requirement(current, name=name, private_key=private, at=_now())
    save_requirement(ws.pack, published, published=True)
    return "/requirement?published=1"


def _seal_demo_pack(ws: Workspace, form: dict) -> str:
    from app.server import _now

    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    if not (ws.pack / "pack.json").is_file():
        raise ModelError(
            "demo pack",
            "pack.json",
            "a prepared sample under packs/cra-baseline/ "
            "(use Prepare sample workspace on the cover)",
        )
    seal_pack_directory(ws.pack, name=name, private_key=private, at=_now())
    return "/requirement?sealed=1"
