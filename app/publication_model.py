"""Legacy Publish view-model, seal POST, and publish POST.

The URLs stay on the old server. EP-11 retires the separate Publish lifecycle.
This module preserves the current page and the existing seal and publish calls.
It does not rebuild or extend that lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.errors import ModelError
from common.keystore import load_or_create_key, trust_store
from requirements.editing import read_pack_seal, seal_pack_directory
from requirements.workspace import (
    list_publication_blockers,
    load_working_copy,
    publish_pack,
    selected_copy,
)

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


def _seal_selected(ws: Workspace, form: dict) -> str:
    from app.server import _active_adapter, _now

    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        raise ModelError("working copy", "timestamp", "a selected working copy")
    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    seal_pack_directory(directory, name=name, private_key=private, at=_now())
    return "/requirements/publish?sealed=1"


def _publish_selected(ws: Workspace, form: dict) -> str:
    from app.server import _active_adapter

    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        raise ModelError("working copy", "timestamp", "a selected working copy")
    version = (form.get("version") or [""])[0].strip()
    publish_pack(ws.root, directory, version=version, trust=trust_store(ws.keys))
    return "/requirements?published=1"
