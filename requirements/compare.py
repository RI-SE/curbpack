"""Read-only differences between two Pack snapshots, plus an explicit transfer."""

from __future__ import annotations

import copy
import functools
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.store import save_requirement
from common.validate import validate_requirement
from requirements.editing import EDITABLE, apply_edits, save_working_requirement
from requirements.workspace import load_working_copy


def compare_copies(left: Path, right: Path) -> dict:
    """Return a transient diff. Neither directory is written."""
    _left_pack, left_requirements = load_working_copy(left)
    _right_pack, right_requirements = load_working_copy(right)
    left_by_id = {item["id"]: item for item in left_requirements}
    right_by_id = {item["id"]: item for item in right_requirements}
    unchanged = []
    changed = []
    for requirement_id in sorted(set(left_by_id) & set(right_by_id)):
        fields = _changed_fields(left_by_id[requirement_id], right_by_id[requirement_id])
        if fields:
            changed.append({"id": requirement_id, "fields": fields})
        else:
            unchanged.append(requirement_id)
    leftover_left = {key: value for key, value in left_by_id.items() if key not in right_by_id}
    leftover_right = {key: value for key, value in right_by_id.items() if key not in left_by_id}
    ambiguous, edges = _locator_edges(leftover_left, leftover_right)
    possible_split, possible_consolidation, paired_left, paired_right = _group_edges(edges)
    return {
        "left": str(left),
        "right": str(right),
        "unchanged": unchanged,
        "changed": changed,
        "only_left": sorted(set(leftover_left) - paired_left),
        "only_right": sorted(set(leftover_right) - paired_right),
        "possible_split": possible_split,
        "possible_consolidation": possible_consolidation,
        "ambiguous": ambiguous,
    }


def extraction_review(working: Path, proposal: Path) -> dict:
    """Field differences between the copy being edited and one extraction.

    Read-only. ``working`` is the copy the person is editing. ``proposal`` is
    the extraction. A requirement only in the working copy is listed under
    ``kept`` and is not a deletion.
    """
    diff = compare_copies(working, proposal)
    _working_pack, working_reqs = load_working_copy(working)
    _proposal_pack, proposal_reqs = load_working_copy(proposal)
    working_by_id = {item["id"]: item for item in working_reqs}
    proposal_by_id = {item["id"]: item for item in proposal_reqs}
    updates = []
    for item in diff["changed"]:
        requirement_id = item["id"]
        current = working_by_id[requirement_id]
        incoming = proposal_by_id[requirement_id]
        fields = []
        for name in item["fields"]:
            if name not in EDITABLE:
                continue
            fields.append(
                {
                    "name": name,
                    "current": current.get(name),
                    "proposed": incoming.get(name),
                }
            )
        if not fields:
            continue
        updates.append(
            {
                "id": requirement_id,
                "source_digest": version_digest(incoming),
                "destination_digest": version_digest(current),
                "fields": fields,
                "left": _review_object(current),
                "right": _review_object(incoming),
            }
        )
    additions = []
    for requirement_id in diff["only_right"]:
        incoming = proposal_by_id[requirement_id]
        additions.append(
            {
                "id": requirement_id,
                "source_digest": version_digest(incoming),
                "destination_digest": None,
                "right": _review_object(incoming),
            }
        )
    return {
        "updates": updates,
        "additions": additions,
        "kept": list(diff["only_left"]),
        "unchanged": list(diff["unchanged"]),
    }


def apply_extraction_choices(
    working: Path,
    proposal: Path,
    choices: list[dict],
) -> None:
    """Copy the chosen proposal fields into the working copy.

    Each choice is ``id``, ``fields`` (names to take from the proposal),
    ``source_digest``, and ``destination_digest``. An empty ``fields`` list
    with ``destination_digest`` None adds the whole proposal requirement.
    """
    _proposal_pack, proposal_reqs = load_working_copy(proposal)
    proposal_by_id = {item["id"]: item for item in proposal_reqs}
    for choice in choices:
        requirement_id = choice["id"]
        incoming = proposal_by_id.get(requirement_id)
        if incoming is None:
            raise ModelError(
                f"requirement {requirement_id}",
                "id",
                "a requirement in the extraction",
            )
        names = list(choice.get("fields") or [])
        partial = dict(choice.get("partial") or {})
        if not names and not partial:
            apply_transfer(
                proposal,
                working,
                requirement_id,
                {"requirement": incoming},
                source_digest=choice["source_digest"],
                destination_digest=None,
            )
            continue
        unknown = sorted((set(names) | set(partial)) - EDITABLE)
        if unknown:
            raise ModelError(
                f"requirement {requirement_id}",
                unknown[0],
                "an editable field",
            )
        current = _by_id(load_working_copy(working)[1], requirement_id)
        if current is None:
            raise ModelError(
                f"requirement {requirement_id}",
                "id",
                "a requirement in the working copy",
            )
        for name, value in partial.items():
            if not _is_blend(current.get(name), incoming.get(name), value):
                raise ModelError(
                    f"requirement {requirement_id}",
                    name,
                    "a value taken from the current text or the new definition",
                )
        edits = dict(partial)
        for name in names:
            if name in edits:
                continue
            edits[name] = incoming[name] if name in incoming else None
        apply_transfer(
            proposal,
            working,
            requirement_id,
            edits,
            source_digest=choice["source_digest"],
            destination_digest=choice["destination_digest"],
        )


def preview_transfer(destination: Path, requirement_id: str, fields: dict) -> dict:
    """Build the destination Requirement that a transfer would write."""
    _refuse_published(destination)
    try:
        pack, requirements = load_working_copy(destination)
        existing = _by_id(requirements, requirement_id)
        requirement = _transferred(pack, requirements, existing, requirement_id, fields)
    except ModelError as exc:
        return {"requirement": None, "errors": [str(exc)]}
    return {"requirement": requirement, "errors": []}


def apply_transfer(
    source: Path,
    destination: Path,
    requirement_id: str,
    fields: dict,
    *,
    source_digest: str,
    destination_digest: str | None,
) -> None:
    """Write one confirmed transfer into the destination working copy."""
    _refuse_published(destination)
    _source_pack, source_requirements = load_working_copy(source)
    source_requirement = _by_id(source_requirements, requirement_id)
    if source_requirement is None or version_digest(source_requirement) != source_digest:
        raise ModelError(
            f"requirement {requirement_id}",
            "version",
            "the source digest read before this transfer",
        )
    pack, requirements = load_working_copy(destination)
    existing = _by_id(requirements, requirement_id)
    if existing is None:
        if destination_digest is not None:
            raise ModelError(
                f"requirement {requirement_id}",
                "version",
                "no destination requirement",
            )
    elif version_digest(existing) != destination_digest:
        raise ModelError(
            f"requirement {requirement_id}",
            "version",
            "the destination digest read before this transfer",
        )
    transferred = _transferred(pack, requirements, existing, requirement_id, fields)
    if existing is None:
        save_requirement(destination, transferred)
        return
    save_working_requirement(destination, transferred, expected_digest=destination_digest)


_MISSING = object()


def _is_blend(current: object, proposed: object, merged: object) -> bool:
    """True when every part of merged is the current value or the proposed value."""
    if merged is None:
        return proposed in (None, "", [], {})
    if proposed is None:
        return merged == current
    return _blend(current, proposed, merged)


def _blend(current: object, proposed: object, merged: object) -> bool:
    if merged == current or merged == proposed:
        return True
    if isinstance(current, dict) and isinstance(proposed, dict) and isinstance(merged, dict):
        keys = set(current) | set(proposed) | set(merged)
        return all(
            _slot(current.get(key, _MISSING), proposed.get(key, _MISSING), merged.get(key, _MISSING))
            for key in keys
        )
    if isinstance(current, list) and isinstance(proposed, list) and isinstance(merged, list):
        if len(current) == len(proposed) == len(merged) and all(
            _slot(left, right, item) for left, right, item in zip(current, proposed, merged)
        ):
            return True
        return _blend_sequence(current, proposed, merged)
    return False


def _slot(current: object, proposed: object, merged: object) -> bool:
    if merged is _MISSING:
        return current is _MISSING or proposed is _MISSING
    if current is _MISSING and proposed is _MISSING:
        return False
    if current is _MISSING:
        return merged == proposed
    if proposed is _MISSING:
        return merged == current
    return _blend(current, proposed, merged)


def _blend_sequence(current: list, proposed: list, merged: list) -> bool:
    """A merged list may keep, drop, or take items without inventing text."""

    @functools.lru_cache(maxsize=None)
    def can(i: int, j: int, k: int) -> bool:
        if k == len(merged):
            return True
        if i == len(current) and j == len(proposed):
            return False
        if i < len(current) and can(i + 1, j, k):
            return True
        if j < len(proposed) and can(i, j + 1, k):
            return True
        if i < len(current) and merged[k] == current[i] and can(i + 1, j, k + 1):
            return True
        if j < len(proposed) and merged[k] == proposed[j] and can(i, j + 1, k + 1):
            return True
        if (
            i < len(current)
            and j < len(proposed)
            and _blend(current[i], proposed[j], merged[k])
            and can(i + 1, j + 1, k + 1)
        ):
            return True
        return False

    return can(0, 0, 0)


def _review_object(requirement: dict) -> dict:
    """Requirement JSON for the visual diff. The seal is not a field to review."""
    return {key: value for key, value in requirement.items() if key != "signed"}


def _refuse_published(destination: Path) -> None:
    if "published" in destination.parts:
        raise ModelError("working copy", "path", "a dated working copy, not a published release")


def _by_id(requirements: list[dict], requirement_id: str) -> dict | None:
    return next((item for item in requirements if item.get("id") == requirement_id), None)


def _transferred(pack: dict, requirements: list[dict], existing: dict | None, requirement_id: str, fields: dict) -> dict:
    if "requirement" in fields:
        incoming = copy.deepcopy(fields["requirement"])
        if not isinstance(incoming, dict):
            raise ModelError(f"requirement {requirement_id}", "requirement", "an object")
        incoming.pop("signed", None)
        incoming["pack_id"] = pack["id"]
        incoming_id = incoming.get("id")
        if any(item.get("id") == incoming_id for item in requirements):
            raise ModelError(
                f"requirement {incoming_id}",
                "id",
                "absent, or an in-place field update of that same id",
            )
        return validate_requirement(incoming, published=False)
    if existing is None:
        raise ModelError(f"requirement {requirement_id}", "id", "a requirement in the destination")
    return apply_edits(existing, fields)


def _changed_fields(left: dict, right: dict) -> list[str]:
    fields = []
    for key in sorted(set(left) | set(right)):
        if left.get(key) != right.get(key):
            fields.append(key)
    if _source_args(left) != _source_args(right):
        fields.append("discovery_hints.sources[].args")
    return sorted(fields)


def _source_args(requirement: dict) -> list:
    hints = requirement.get("discovery_hints") or {}
    sources = hints.get("sources") or []
    return [item.get("args") if isinstance(item, dict) else None for item in sources]


def _identifier(requirement: dict):
    source = requirement.get("source") or {}
    return source.get("identifier") if isinstance(source, dict) else None


def _candidates(requirement: dict, locator: object, others: dict[str, dict]) -> list[str]:
    found = []
    for other_id, other in others.items():
        if _identifier(requirement) != _identifier(other):
            continue
        references = other.get("references") or []
        if any(isinstance(item, dict) and item.get("locator") == locator for item in references):
            found.append(other_id)
    return sorted(found)


def _locator_edges(lefts: dict[str, dict], rights: dict[str, dict]):
    ambiguous = []
    blocked: set[tuple[str, str]] = set()
    for left_id, left in lefts.items():
        for ref in left.get("references") or []:
            if not isinstance(ref, dict):
                continue
            candidates = _candidates(left, ref.get("locator"), rights)
            if len(candidates) > 1:
                ambiguous.append(
                    {"locator": ref.get("locator"), "left_id": left_id, "right_ids": candidates}
                )
                for right_id in candidates:
                    blocked.add((left_id, right_id))
    for right_id, right in rights.items():
        for ref in right.get("references") or []:
            if not isinstance(ref, dict):
                continue
            candidates = _candidates(right, ref.get("locator"), lefts)
            if len(candidates) > 1:
                for left_id in candidates:
                    blocked.add((left_id, right_id))
    edges: set[tuple[str, str]] = set()
    for left_id, left in lefts.items():
        for ref in left.get("references") or []:
            if not isinstance(ref, dict):
                continue
            candidates = _candidates(left, ref.get("locator"), rights)
            if len(candidates) != 1:
                continue
            pair = (left_id, candidates[0])
            if pair in blocked:
                continue
            edges.add(pair)
    return ambiguous, edges


def _group_edges(edges: set[tuple[str, str]]):
    by_left: dict[str, set[str]] = {}
    by_right: dict[str, set[str]] = {}
    for left_id, right_id in edges:
        by_left.setdefault(left_id, set()).add(right_id)
        by_right.setdefault(right_id, set()).add(left_id)
    possible_split = []
    paired_left: set[str] = set()
    paired_right: set[str] = set()
    for left_id in sorted(by_left):
        right_ids = sorted(by_left[left_id])
        if len(right_ids) > 1:
            possible_split.append({"left_id": left_id, "right_ids": right_ids})
            paired_left.add(left_id)
            paired_right.update(right_ids)
    possible_consolidation = []
    for right_id in sorted(by_right):
        if right_id in paired_right:
            continue
        left_ids = sorted(by_right[right_id])
        if not left_ids or left_ids[0] in paired_left and len(left_ids) == 1:
            continue
        possible_consolidation.append({"left_ids": left_ids, "right_id": right_id})
        paired_left.update(left_ids)
        paired_right.add(right_id)
    return possible_split, possible_consolidation, paired_left, paired_right
