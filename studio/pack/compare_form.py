"""One Requirement comparison for the form page. Read-only."""

from __future__ import annotations

from typing import TYPE_CHECKING

from urllib.parse import urlencode

from common.canonical import version_digest
from common.errors import ModelError
from requirements.compare import extraction_review
from requirements.workspace import load_working_copy, select_working_copy

if TYPE_CHECKING:
    from app.server import Workspace


def comparison_list(ws: Workspace, query: dict) -> dict | None:
    """The destination copy and Changes links for this Extract or Import pair."""
    proposal_name = (query.get("proposal") or [""])[0].strip()
    destination_name = (query.get("destination") or [""])[0].strip()
    if not proposal_name or not destination_name:
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


def compare_form_model(ws: Workspace, query: dict) -> dict:
    """Current and proposed values for one Requirement. Neither directory is written."""
    destination, proposal = _pair(ws, query)
    review = extraction_review(destination, proposal)
    requirement_id = (query.get("requirement") or [""])[0].strip()
    if not requirement_id:
        raise ModelError("requirement", "id", "a requirement id")
    current = _requirement(destination, requirement_id)
    proposed = _requirement(proposal, requirement_id)
    if current is None or proposed is None:
        raise ModelError("requirement", "id", "a requirement in both copies")
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
