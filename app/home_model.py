"""Home view-model. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.errors import ModelError
from requirements.workspace import (
    ensure_default_selection,
    list_pack_options,
    read_selection,
    resolve_selected_pack,
)

if TYPE_CHECKING:
    from app.server import Workspace


def _home_model(ws: Workspace) -> dict:
    from app.server import _sync_adapter_for_pack

    try:
        ensure_default_selection(ws.root)
    except ModelError:
        pass
    selection = read_selection(ws.root)
    if selection and isinstance(selection.get("pack_id"), str):
        _sync_adapter_for_pack(ws, selection["pack_id"])
    options = []
    for item in list_pack_options(ws.root):
        selected = False
        if selection and selection.get("kind") == item["kind"] and selection.get("pack_id") == item["pack_id"]:
            if item["kind"] == "working":
                selected = selection.get("timestamp") == item["ref"]
            else:
                selected = selection.get("version") == item["ref"]
        options.append({**{key: value for key, value in item.items() if key != "path"}, "selected": selected})
    return {
        "selection": selection if resolve_selected_pack(ws.root) else None,
        "options": options,
    }
