"""Compare view-model and transfer. The URL stays on the old server."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from common.errors import ModelError
from requirements.compare import apply_transfer, compare_copies
from requirements.workspace import (
    list_published_versions,
    list_working_copies,
    read_selection,
    select_published_pack,
    select_working_copy,
)

if TYPE_CHECKING:
    from app.server import Workspace


def _compare_pack_id(ws: Workspace) -> str:
    """The selected working copy when it is not the active adapter's pack."""
    from app.server import _active_adapter

    adapter = _active_adapter(ws)
    selection = read_selection(ws.root)
    selected = selection.get("pack_id") if isinstance(selection, dict) else None
    if (
        isinstance(selection, dict)
        and selection.get("kind") == "working"
        and isinstance(selected, str)
        and selected != adapter.get("pack_id")
    ):
        return selected
    return str(adapter["pack_id"])


def _compare_model(ws: Workspace, query: dict) -> dict:
    pack_id = _compare_pack_id(ws)
    options = _compare_options(ws, pack_id)
    left = (query.get("left") or [""])[0]
    right = (query.get("right") or [""])[0]
    values = {str(item.get("value") or "") for item in options}
    if left and left not in values:
        left = ""
    if right and right not in values:
        right = ""
    model = {
        "options": options,
        "copies": [item["value"] for item in options if item.get("kind") == "working"],
        "left": left,
        "right": right,
        "diff": None,
        "can_transfer": False,
    }
    if left and right:
        left_dir = _resolve_compare_ref(ws.root, pack_id, left)
        right_dir = _resolve_compare_ref(ws.root, pack_id, right)
        model["diff"] = compare_copies(left_dir, right_dir)
        model["can_transfer"] = _compare_ref_kind(right) == "working" and _compare_ref_kind(
            left
        ) in {"working", "published"}
    return model


def _compare_options(ws: Workspace, pack_id: str) -> list[dict]:
    """Working copies (selected labeled) plus published releases for Compare."""
    selection = read_selection(ws.root)
    selected_stamp = ""
    if (
        isinstance(selection, dict)
        and selection.get("pack_id") == pack_id
        and selection.get("kind") == "working"
        and isinstance(selection.get("timestamp"), str)
    ):
        selected_stamp = selection["timestamp"]
    options: list[dict] = []
    for stamp in list_working_copies(ws.root, pack_id):
        if stamp == selected_stamp:
            label = f"Working copy · {stamp}"
        else:
            label = f"Copy · {stamp}"
        options.append({"value": stamp, "label": label, "kind": "working"})
    for version in list_published_versions(ws.root, pack_id):
        options.append(
            {
                "value": f"published:{version}",
                "label": f"Published · {version}",
                "kind": "published",
            }
        )
    options.sort(
        key=lambda item: (
            0 if item.get("value") == selected_stamp else 1 if item.get("kind") == "working" else 2,
            str(item.get("value") or ""),
        )
    )
    return options


def _compare_ref_kind(ref: str) -> str:
    raw = (ref or "").strip()
    if raw.startswith("published:"):
        return "published"
    return "working" if raw else ""


def _resolve_compare_ref(root: Path, pack_id: str, ref: str) -> Path:
    raw = (ref or "").strip()
    if raw.startswith("published:"):
        return select_published_pack(root, pack_id, raw.split(":", 1)[1])
    return select_working_copy(root, pack_id, raw)


def _apply_compare_form(ws: Workspace, form: dict) -> str | bytes:
    from urllib.parse import quote

    from common.canonical import version_digest
    from requirements.ownership import in_target_namespace, take_ownership
    from requirements.workspace import load_working_copy, mark_selected
    from studio.pack.pages import ownership_confirmation_page
    from studio.pack.requirement_editor import _namespace_base_for_edit

    namespace_base, packs = _namespace_base_for_edit(ws, form)
    pack_id = _compare_pack_id(ws)
    source_ref = (form.get("source") or [""])[0]
    destination_ref = (form.get("destination") or [""])[0]
    if _compare_ref_kind(destination_ref) != "working":
        raise ModelError("compare", "destination", "a working copy, not a published release")
    source = _resolve_compare_ref(ws.root, pack_id, source_ref)
    destination = _resolve_compare_ref(ws.root, pack_id, destination_ref)
    field = (form.get("field") or [""])[0].strip()
    requirement_id = (form.get("requirement_id") or [""])[0].strip()
    destination_digest = (form.get("destination_digest") or [""])[0]
    pack, requirements = load_working_copy(destination)
    if not in_target_namespace(pack, namespace_base):
        requirement = next((item for item in requirements if item.get("id") == requirement_id), None)
        if requirement is None:
            raise ModelError("requirement", "id", "a requirement in the selected working copy")
        if (form.get("take_ownership") or [""])[0] != "1":
            return ownership_confirmation_page(
                requirement_id,
                form,
                "/requirements/compare",
                action="/requirements/compare/apply",
            )
        if version_digest(requirement) != destination_digest:
            raise ModelError(
                f"requirement {requirement_id}",
                "version",
                "the digest read before this save",
            )
        copied = take_ownership(
            destination,
            ws.root,
            namespace_base=namespace_base,
            requirement_id=requirement_id,
            edits={field: (form.get("value") or [""])[0]},
            also_search=(packs,),
        )
        try:
            mark_selected(ws.root, str(pack["id"]), copied.name)
        except Exception:
            import shutil

            shutil.rmtree(copied, ignore_errors=True)
            raise
        return (
            "/requirements/compare?left="
            + quote(source_ref, safe="")
            + "&right="
            + quote(copied.name, safe="")
        )
    apply_transfer(
        source,
        destination,
        (form.get("requirement_id") or [""])[0].strip(),
        {field: (form.get("value") or [""])[0]},
        source_digest=(form.get("source_digest") or [""])[0],
        destination_digest=destination_digest or None,
    )
    return f"/requirements/compare?left={source_ref}&right={destination_ref}"
