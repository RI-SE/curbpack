"""Extract-review view-model and apply. The URL stays on the old server."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from urllib.parse import quote

from common.errors import ModelError
from requirements.compare import apply_extraction_choices, extraction_review
from requirements.workspace import select_working_copy

if TYPE_CHECKING:
    from app.server import Workspace


def _extract_review_model(ws: Workspace, query: dict) -> dict:
    from app.server import _active_adapter, _locate_repo_pack

    adapter = _active_adapter(ws)
    proposal = (query.get("proposal") or [""])[0]
    destination = (query.get("destination") or [""])[0]
    pack_id = (query.get("pack") or [""])[0].strip()
    repo_id = (query.get("repo") or [""])[0].strip()
    if pack_id:
        found = _locate_repo_pack(ws, pack_id, repo_id)
        if found is None:
            raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
        found_repo, pack_dir, _pack = found
        review = extraction_review(
            pack_dir,
            select_working_copy(ws.root, adapter["pack_id"], proposal),
        )
        review["proposal"] = proposal
        review["destination"] = pack_id
        review["dest_pack"] = pack_id
        review["dest_repo"] = found_repo
    else:
        review = extraction_review(
            select_working_copy(ws.root, adapter["pack_id"], destination),
            select_working_copy(ws.root, adapter["pack_id"], proposal),
        )
        review["proposal"] = proposal
        review["destination"] = destination
    if (query.get("kept") or [""])[0]:
        review["message"] = "Nothing was brought in. The working copy is unchanged."
    if (query.get("brought") or [""])[0]:
        review["message"] = (
            "Updated the fields you chose. The working copy you were editing stays selected."
        )
    return review


def _apply_extraction_review(ws: Workspace, form: dict) -> str:
    from app.server import _active_adapter, _locate_repo_pack

    adapter = _active_adapter(ws)
    pack_id = adapter["pack_id"]
    proposal_name = (form.get("proposal") or [""])[0]
    destination_name = (form.get("destination") or [""])[0]
    repo_pack_id = (form.get("pack") or [""])[0].strip()
    repo_id = (form.get("repo") or [""])[0].strip()
    return_pack = ""
    return_repo = ""
    if repo_pack_id:
        found = _locate_repo_pack(ws, repo_pack_id, repo_id)
        if found is None:
            raise ModelError("pack", "id", f"a pack named in curbpack.json, not {repo_pack_id}")
        return_repo, destination_dir, _listed = found
        return_pack = repo_pack_id
        proposal_dir = select_working_copy(ws.root, pack_id, proposal_name)
    else:
        destination_dir = select_working_copy(ws.root, pack_id, destination_name)
        proposal_dir = select_working_copy(ws.root, pack_id, proposal_name)
    pairs: dict[str, tuple[str, str | None]] = {}
    for raw in form.get("pair") or []:
        requirement_id, source_digest, destination_digest = raw.split("|", 2)
        pairs[requirement_id] = (source_digest, destination_digest or None)
    grouped: dict[str, list[str]] = {}
    for raw in form.get("field") or []:
        requirement_id, field = raw.split("|", 1)
        grouped.setdefault(requirement_id, []).append(field)
    partials: dict[str, dict] = {}
    raw_parts = (form.get("parts") or [""])[0]
    if raw_parts:
        try:
            parsed = json.loads(raw_parts)
        except json.JSONDecodeError as exc:
            raise ModelError("review", "parts", "a JSON list of chosen values") from exc
        if not isinstance(parsed, list):
            raise ModelError("review", "parts", "a JSON list of chosen values")
        for item in parsed:
            if not isinstance(item, dict):
                raise ModelError("review", "parts", "one object per chosen value")
            requirement_id = str(item.get("id") or "")
            field = str(item.get("field") or "")
            partials.setdefault(requirement_id, {})[field] = item.get("value")
    choices = []
    for requirement_id in sorted(set(grouped) | set(partials)):
        fields = [name for name in grouped.get(requirement_id, []) if name not in partials.get(requirement_id, {})]
        try:
            source_digest, destination_digest = pairs[requirement_id]
        except KeyError:
            raise ModelError(
                f"requirement {requirement_id}",
                "version",
                "the digest read before this transfer",
            ) from None
        choices.append(
            {
                "id": requirement_id,
                "fields": fields,
                "partial": partials.get(requirement_id, {}),
                "source_digest": source_digest,
                "destination_digest": destination_digest,
            }
        )
    for requirement_id in form.get("add") or []:
        try:
            source_digest, _destination_digest = pairs[requirement_id]
        except KeyError:
            raise ModelError(
                f"requirement {requirement_id}",
                "version",
                "the digest read before this transfer",
            ) from None
        choices.append(
            {
                "id": requirement_id,
                "fields": [],
                "source_digest": source_digest,
                "destination_digest": None,
            }
        )
    if not choices:
        if return_pack:
            return (
                "/requirements?document="
                + quote(return_pack, safe="")
                + "&repo="
                + quote(return_repo, safe="")
                + "&kept=1"
            )
        return (
            "/requirements/extract/review?proposal="
            + quote(proposal_name)
            + "&destination="
            + quote(destination_name)
            + "&kept=1"
        )
    apply_extraction_choices(destination_dir, proposal_dir, choices)
    if return_pack:
        return (
            "/requirements?document="
            + quote(return_pack, safe="")
            + "&repo="
            + quote(return_repo, safe="")
            + "&brought=1"
        )
    return (
        "/requirements/extract/review?proposal="
        + quote(proposal_name)
        + "&destination="
        + quote(destination_name)
        + "&brought=1"
    )
