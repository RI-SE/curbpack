"""Suggest overlapping Requirements and merge them only after confirmation."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.validate import validate_requirement
from requirements.editing import assign_reference_numbers, save_working_requirement
from requirements.workspace import load_working_copy, work_directory

_CONFLICT_KEYS = (
    "strength",
    "responsible",
    "applicability",
    "exceptions",
    "scope",
    "note",
    "remediation_hint",
    "discovery_hints",
    "source",
)


def suggest_consolidations(directory: Path) -> list[dict]:
    """Rank overlapping Requirements. The directory is not written."""
    _pack, requirements = load_working_copy(directory)
    suggestions = []
    for index, left in enumerate(requirements):
        for right in requirements[index + 1 :]:
            shared_locators = sorted(_locators(left) & _locators(right))
            shared_passages = _shared_passages(left, right)
            same_instrument = _identifier(left) == _identifier(right) and _identifier(left) is not None
            if not ((same_instrument and shared_locators) or shared_passages):
                continue
            if shared_locators:
                reason = "shared locator " + ", ".join(shared_locators)
            else:
                reason = f"shared passage {shared_passages[0]}"
            suggestions.append(
                {
                    "ids": sorted([left["id"], right["id"]]),
                    "reason": reason,
                    "_locators": len(shared_locators),
                    "_passages": len(shared_passages),
                }
            )
    suggestions.sort(key=lambda item: (-item["_locators"], -item["_passages"], item["ids"]))
    for item in suggestions:
        item.pop("_locators")
        item.pop("_passages")
    return suggestions


def preview_consolidation(
    directory: Path,
    ids: list[str],
    retained_id: str,
    fields: dict,
    references: list[dict],
) -> dict:
    """Validate one merged Requirement and list unresolved conflicts. No write."""
    _pack, requirements = load_working_copy(directory)
    selected = [item for item in requirements if item.get("id") in set(ids)]
    if len(selected) != len(set(ids)):
        raise ModelError("requirement", "id", "each selected requirement")
    retained = next((item for item in selected if item.get("id") == retained_id), None)
    if retained is None:
        raise ModelError("requirement", "id", retained_id)
    conflicts = []
    for key in _CONFLICT_KEYS:
        if key in fields:
            continue
        values = {_freeze(item.get(key)) for item in selected}
        if len(values) > 1:
            conflicts.append(key)
    merged = copy.deepcopy(retained)
    merged.pop("signed", None)
    for key in _CONFLICT_KEYS:
        if key in fields:
            value = fields[key]
            if value is None or value == "" or value == [] or value == {}:
                merged.pop(key, None)
            else:
                merged[key] = copy.deepcopy(value)
        elif key in conflicts:
            merged.pop(key, None)
    merged["references"] = assign_reference_numbers(references)
    checked = validate_requirement(merged, published=False)
    return {"requirement": checked, "conflicts": conflicts}


def apply_consolidation(
    directory: Path,
    ids: list[str],
    retained_id: str,
    fields: dict,
    references: list[dict],
    *,
    digests: dict[str, str],
) -> dict:
    """Save one unsigned Requirement and remove the other unsigned drafts, or write nothing."""
    if "published" in Path(directory).parts:
        raise ModelError(
            "working copy",
            "path",
            "a dated working copy, not a published release",
        )
    _pack, requirements = load_working_copy(directory)
    selected = [item for item in requirements if item.get("id") in set(ids)]
    if len(selected) != len(set(ids)):
        raise ModelError("requirement", "id", "each selected requirement")
    for item in selected:
        if digests.get(item["id"]) != version_digest(item):
            raise ModelError(
                f"requirement {item['id']}",
                "version",
                "the digest read before this merge",
            )
    for item in selected:
        if "signed" in item:
            raise ModelError(
                f"requirement {item['id']}",
                "signed",
                "absent before a redundant draft is removed",
            )
    preview = preview_consolidation(directory, ids, retained_id, fields, references)
    if preview["conflicts"]:
        raise ModelError(
            f"requirement {retained_id}",
            "conflicts",
            ", ".join(preview["conflicts"]),
        )
    merged = preview["requirement"]
    txn = work_directory(directory) / "txn"
    if txn.exists():
        shutil.rmtree(txn)
    txn.mkdir(parents=True)
    try:
        for item in selected:
            source = directory / f"{item['id']}.json"
            shutil.copy2(source, txn / source.name)
        save_working_requirement(directory, merged, expected_digest=digests[retained_id])
        for item in selected:
            if item["id"] == retained_id:
                continue
            if "signed" in item:
                raise ModelError(
                    f"requirement {item['id']}",
                    "signed",
                    "absent before a redundant draft is removed",
                )
            (directory / f"{item['id']}.json").unlink()
    except Exception:
        for path in txn.glob("*.json"):
            shutil.copy2(path, directory / path.name)
        raise
    finally:
        shutil.rmtree(txn, ignore_errors=True)
    return merged


def _identifier(requirement: dict):
    source = requirement.get("source") or {}
    return source.get("identifier") if isinstance(source, dict) else None


def _locators(requirement: dict) -> set[str]:
    found = set()
    for ref in requirement.get("references") or []:
        if isinstance(ref, dict) and isinstance(ref.get("locator"), str):
            found.add(ref["locator"])
    return found


def _passages(requirement: dict) -> list[str]:
    passages = []
    for ref in requirement.get("references") or []:
        if isinstance(ref, dict) and isinstance(ref.get("law_text"), str):
            passages.append(" ".join(ref["law_text"].split()))
    return passages


def _shared_passages(left: dict, right: dict) -> list[str]:
    return sorted(set(_passages(left)) & set(_passages(right)))


def _freeze(value: object):
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze(item)) for key, item in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value
