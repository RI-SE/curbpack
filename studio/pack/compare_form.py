"""One Requirement comparison for the form page. Read-only."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from common.canonical import version_digest
from common.errors import ModelError
from requirements.compare import extraction_review
from requirements.workspace import load_working_copy, select_working_copy

if TYPE_CHECKING:
    from app.server import Workspace


def copy_list_target(query: dict) -> str:
    """The Requirements list for this Extract or Import pair."""
    pairs = []
    for key in ("proposal", "destination", "pack", "repo"):
        value = (query.get(key) or [""])[0]
        if value:
            pairs.append((key, value))
    if not pairs:
        return "/requirements/copy"
    return "/requirements/copy?" + urlencode(pairs)


def comparison_list(ws: Workspace, query: dict) -> dict | None:
    """The destination copy and Changes links for this Extract or Import pair."""
    proposal_name = (query.get("proposal") or [""])[0].strip()
    destination_name = (query.get("destination") or [""])[0].strip()
    pack_id = (query.get("pack") or [""])[0].strip()
    if not proposal_name or not (destination_name or pack_id):
        return None
    destination, proposal = _pair(ws, query)
    review = extraction_review(destination, proposal)
    _pack, requirements = load_working_copy(destination)
    _proposal_pack, proposed = load_working_copy(proposal)
    linked = {str(item.get("id") or "") for item in review["updates"]}
    linked.update(str(item.get("id") or "") for item in review["additions"])
    by_id = {item.get("id"): item for item in requirements}
    for item in proposed:
        if item.get("id") in linked and item.get("id") not in by_id:
            requirements.append(item)
    return {
        "directory": destination,
        "requirements": requirements,
        "links": {
            requirement_id: _form_href(requirement_id, query)
            for requirement_id in linked
            if requirement_id
        },
    }


def _form_href(requirement_id: str, query: dict) -> str:
    pairs = [
        ("requirement", requirement_id),
        ("proposal", (query.get("proposal") or [""])[0]),
        ("destination", (query.get("destination") or [""])[0]),
    ]
    for key in ("pack", "repo"):
        value = (query.get(key) or [""])[0].strip()
        if value:
            pairs.append((key, value))
    return "/requirements/compare/form?" + urlencode(pairs)


def apply_compare_form(ws: Workspace, form: dict) -> str | bytes:
    """Write the selected New leaves, or ask for ownership first."""
    import json

    from requirements.compare import apply_extraction_choices
    from requirements.ownership import in_target_namespace, take_ownership
    from requirements.workspace import mark_selected
    from studio.pack.pages import ownership_confirmation_page
    from studio.pack.requirement_editor import _namespace_base_for_edit

    namespace_base, packs = _namespace_base_for_edit(ws, form)
    destination, proposal = _pair(ws, form)
    requirement_id = (form.get("requirement") or [""])[0].strip()
    if not requirement_id:
        raise ModelError("requirement", "id", "a requirement id")
    raw = (form.get("choice") or ["{}"])[0] or "{}"
    try:
        choice = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModelError("compare", "choice", "a JSON object of old or new") from exc
    if not isinstance(choice, dict):
        raise ModelError("compare", "choice", "a JSON object of old or new")
    current = _requirement(destination, requirement_id)
    proposed = _requirement(proposal, requirement_id)
    if proposed is None:
        raise ModelError("requirement", "id", "a requirement in the proposal")
    adding = current is None
    if adding and choice.get("requirement") != "new":
        return _list_href(form)
    if adding:
        fields, partial = [], {}
    else:
        fields, partial = _choice_edits(current, proposed, choice)
    pack, _requirements = load_working_copy(destination)
    if not in_target_namespace(pack, namespace_base):
        if (form.get("take_ownership") or [""])[0] != "1":
            return ownership_confirmation_page(
                requirement_id,
                form,
                _list_href(form),
                action="/requirements/compare/form/apply",
            )
        if adding:
            proposal_pack, _proposed_requirements = load_working_copy(proposal)
            copied = take_ownership(
                destination,
                ws.root,
                namespace_base=namespace_base,
                requirement_id=requirement_id,
                edits={},
                also_search=(packs,),
                addition=proposed,
                addition_pack=proposal_pack,
            )
        else:
            edits = dict(partial)
            for name in fields:
                edits[name] = proposed.get(name)
            copied = take_ownership(
                destination,
                ws.root,
                namespace_base=namespace_base,
                requirement_id=requirement_id,
                edits=edits,
                also_search=(packs,),
            )
        mark_selected(ws.root, str(pack["id"]), copied.name)
        return f"/requirements/requirement/{requirement_id}"
    if adding:
        if choice.get("requirement") == "new":
            apply_extraction_choices(
                destination,
                proposal,
                [
                    {
                        "id": requirement_id,
                        "fields": [],
                        "partial": {},
                        "source_digest": version_digest(proposed),
                        "destination_digest": None,
                    }
                ],
            )
        else:
            return _list_href(form)
    elif fields or partial:
        apply_extraction_choices(
            destination,
            proposal,
            [
                {
                    "id": requirement_id,
                    "fields": fields,
                    "partial": partial,
                    "source_digest": version_digest(proposed),
                    "destination_digest": version_digest(current),
                }
            ],
        )
    return _editor_href(ws, form, requirement_id, destination, pack)


def _editor_href(ws: Workspace, form: dict, requirement_id: str, destination, pack: dict) -> str:
    """Open the editor on the copy that was just written."""
    from requirements.workspace import mark_selected

    pack_query = (form.get("pack") or [""])[0].strip()
    repo_id = (form.get("repo") or [""])[0].strip()
    if pack_query:
        pairs = [("pack", pack_query)]
        if repo_id:
            pairs.append(("repo", repo_id))
        return f"/requirements/requirement/{requirement_id}?" + urlencode(pairs)
    mark_selected(ws.root, str(pack["id"]), destination.name)
    return f"/requirements/requirement/{requirement_id}"


def _list_href(form: dict) -> str:
    pairs = []
    for key in ("proposal", "destination", "pack", "repo"):
        value = (form.get(key) or [""])[0]
        if value:
            pairs.append((key, value))
    if not pairs:
        return "/requirements/copy"
    return "/requirements/copy?" + urlencode(pairs)


def _choice_edits(current: dict, proposed: dict, choice: dict) -> tuple[list[str], dict]:
    fields: list[str] = []
    parents: dict[str, dict] = {}
    chosen_new: set[str] = set()
    for name, side in choice.items():
        if side not in {"old", "new"}:
            raise ModelError("compare", "choice", "old or new")
        if "." not in name:
            if side == "new":
                fields.append(str(name))
            continue
        parent, key = str(name).split(".", 1)
        if parent not in {"source", "discovery_hints"}:
            raise ModelError("compare", "choice", "an editor field")
        if parent not in parents:
            original = current.get(parent) or {}
            parents[parent] = copy.deepcopy(original) if isinstance(original, dict) else {}
        if side != "new":
            continue
        chosen_new.add(parent)
        proposed_parent = proposed.get(parent) or {}
        if isinstance(proposed_parent, dict) and key in proposed_parent:
            parents[parent][key] = copy.deepcopy(proposed_parent[key])
        else:
            parents[parent].pop(key, None)
    partial = {parent: value for parent, value in parents.items() if parent in chosen_new}
    return fields, partial


def compare_form_model(ws: Workspace, query: dict) -> dict:
    """Current and proposed values for one Requirement. Neither directory is written."""
    destination, proposal = _pair(ws, query)
    review = extraction_review(destination, proposal)
    requirement_id = (query.get("requirement") or [""])[0].strip()
    if not requirement_id:
        raise ModelError("requirement", "id", "a requirement id")
    current = _requirement(destination, requirement_id)
    proposed = _requirement(proposal, requirement_id)
    if proposed is None:
        raise ModelError("requirement", "id", "a requirement in the proposal")
    if current is None:
        return {
            "id": requirement_id,
            "current": {},
            "proposed": proposed,
            "source_digest": version_digest(proposed),
            "destination_digest": None,
            "changed": ["requirement"],
            "addition": True,
        }
    changed = []
    for item in review["updates"]:
        if item.get("id") == requirement_id:
            changed = [str(field.get("name") or "") for field in item.get("fields") or []]
            break
    return {
        "id": requirement_id,
        "current": current,
        "proposed": proposed,
        "source_digest": version_digest(proposed),
        "destination_digest": version_digest(current),
        "changed": changed,
    }


def _pair(ws: Workspace, query: dict):
    """The same destination and proposal directories extract review already uses."""
    from app.server import _active_adapter, _locate_repo_pack

    adapter = _active_adapter(ws)
    proposal_name = (query.get("proposal") or [""])[0]
    destination_name = (query.get("destination") or [""])[0]
    pack_id = (query.get("pack") or [""])[0].strip()
    repo_id = (query.get("repo") or [""])[0].strip()
    proposal = select_working_copy(ws.root, adapter["pack_id"], proposal_name)
    if pack_id:
        found = _locate_repo_pack(ws, pack_id, repo_id)
        if found is None:
            raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
        _repo, destination, _pack = found
        return destination, proposal
    destination = select_working_copy(ws.root, adapter["pack_id"], destination_name)
    return destination, proposal


def _requirement(directory, requirement_id: str) -> dict | None:
    _pack, requirements = load_working_copy(directory)
    for item in requirements:
        if item.get("id") == requirement_id:
            return item
    return None
