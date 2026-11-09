"""Legacy Publish view-model. The URL stays on the old server.

EP-11 retires the separate Publish lifecycle. This module preserves the
current page. It does not rebuild or extend that lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.keystore import trust_store
from requirements.editing import read_pack_seal
from requirements.workspace import list_publication_blockers, load_working_copy, selected_copy

if TYPE_CHECKING:
    from app.server import Workspace


def _publication_model(ws: Workspace, query: dict) -> dict:
    from app.server import _active_adapter, _coverage_detail, _requirement_rows

    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return {"timestamp": None, "blockers": [], "requirements": []}
    pack, requirements = load_working_copy(directory)
    trust = trust_store(ws.keys)
    message = ""
    if (query.get("sealed") or [""])[0]:
        message = "Pack directory sealed."
    return {
        "timestamp": directory.name,
        "pack_version": pack.get("version"),
        "requirements": _requirement_rows(directory, requirements, trust),
        "seal": read_pack_seal(directory, trust),
        "blockers": list_publication_blockers(ws.root, directory, trust),
        "coverage_detail": _coverage_detail(directory),
        "message": message,
    }
