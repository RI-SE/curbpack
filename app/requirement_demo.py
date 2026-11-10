"""Demo requirement GET and save POST. The URLs stay on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.requirement_page import requirement_page
from common.store import load_requirement, save_requirement
from requirements.editing import apply_edits
from workflow import snapshot

if TYPE_CHECKING:
    from app.server import Workspace


def _demo_requirement(ws: Workspace) -> bytes:
    from app.server import _require_demo_requirement

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
    from app.server import _require_demo_requirement

    current = load_requirement(_require_demo_requirement(ws))
    edited = apply_edits(current, edits_for_requirement(current, form))
    save_requirement(ws.pack, edited)
    return "/requirement?saved=1"
