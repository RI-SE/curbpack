"""Consolidate view-model and merge. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.canonical import version_digest
from common.errors import ModelError
from requirements.consolidate import apply_consolidation, suggest_consolidations
from requirements.workspace import load_working_copy, selected_copy

if TYPE_CHECKING:
    from app.server import Workspace


def _consolidate_model(ws: Workspace) -> dict:
    from app.server import _active_adapter

    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return {"suggestions": [], "requirements": [], "digests": {}}
    _pack, requirements = load_working_copy(directory)
    return {
        "suggestions": suggest_consolidations(directory),
        "requirements": requirements,
        "digests": {item["id"]: version_digest(item) for item in requirements},
    }


def _apply_consolidation_form(ws: Workspace, form: dict) -> str:
    from app.server import _active_adapter

    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        raise ModelError("working copy", "timestamp", "a selected working copy")
    ids = form.get("ids") or []
    digest_ids = form.get("digest_id") or []
    digest_values = form.get("digest_value") or []
    if len(digest_ids) != len(digest_values):
        raise ModelError("requirement", "version", "a digest for each selected requirement")
    locators = form.get("ref_locator") or []
    texts = form.get("ref_law_text") or []
    apply_consolidation(
        directory,
        ids,
        (form.get("retained_id") or [""])[0],
        {"note": (form.get("note") or [""])[0].strip()},
        [{"locator": locator, "law_text": text} for locator, text in zip(locators, texts)],
        digests=dict(zip(digest_ids, digest_values)),
    )
    return "/requirements/consolidate?merged=1"
