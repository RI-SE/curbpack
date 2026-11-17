"""Read which Claims were bound to a Requirement before its digest changed.

The functions return new dicts. They do not write Claims, Requirements, or reports.
"""

from __future__ import annotations

from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.validate import validate_curbpack_config


def claims_affected_by_requirement(claims: list, before: dict, after: dict) -> list[dict]:
    """Claims bound to `before` when `after` has a different payload digest."""
    if version_digest(before) == version_digest(after):
        return []
    found = []
    for claim in claims:
        if not isinstance(claim, dict) or not _bound_to(claim, before):
            continue
        found.append(
            {
                "id": claim.get("id"),
                "recorded": {
                    "namespace": claim.get("namespace"),
                    "pack_id": claim.get("pack_id"),
                    "requirement_id": claim.get("requirement_id"),
                    "requirement_digest": claim.get("requirement_digest"),
                },
                "current": {
                    "namespace": after.get("namespace"),
                    "pack_id": after.get("pack_id"),
                    "requirement_id": after.get("id"),
                    "digest": version_digest(after),
                },
            }
        )
    return found


def claims_unresolved_for_requirement(claims: list, requirement: dict) -> list[dict]:
    """Claims for this Requirement whose recorded digest is not the current payload."""
    current = version_digest(requirement)
    found = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if claim.get("namespace") != requirement.get("namespace"):
            continue
        if claim.get("pack_id") != requirement.get("pack_id"):
            continue
        if claim.get("requirement_id") != requirement.get("id"):
            continue
        if claim.get("requirement_digest") == current:
            continue
        found.append(
            {
                "id": claim.get("id"),
                "recorded": {
                    "namespace": claim.get("namespace"),
                    "pack_id": claim.get("pack_id"),
                    "requirement_id": claim.get("requirement_id"),
                    "requirement_digest": claim.get("requirement_digest"),
                },
                "current": {
                    "namespace": requirement.get("namespace"),
                    "pack_id": requirement.get("pack_id"),
                    "requirement_id": requirement.get("id"),
                    "digest": current,
                },
            }
        )
    return found


def claims_after_ownership(claims: list, owned: dict) -> dict:
    """Source Claims stay bound to origin. Claims for the new Pack stay in their own list."""
    origin = owned.get("origin") if isinstance(owned.get("origin"), dict) else {}
    source_namespace = origin.get("namespace")
    source_pack = origin.get("pack")
    source_requirement = origin.get("requirement")
    source = []
    owned_rows = []
    if not source_namespace or not source_pack or not source_requirement:
        return {"source": [], "owned": []}
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if (
            claim.get("namespace") == source_namespace
            and claim.get("pack_id") == source_pack
            and claim.get("requirement_id") == source_requirement
        ):
            source.append(_identity_row(claim))
        elif (
            claim.get("namespace") == owned.get("namespace")
            and claim.get("pack_id") == owned.get("pack_id")
            and claim.get("requirement_id") == owned.get("id")
        ):
            owned_rows.append(_identity_row(claim))
    return {"source": source, "owned": owned_rows}


def _identity_row(claim: dict) -> dict:
    return {
        "id": claim.get("id"),
        "namespace": claim.get("namespace"),
        "pack_id": claim.get("pack_id"),
        "requirement_id": claim.get("requirement_id"),
        "requirement_digest": claim.get("requirement_digest"),
    }


def requirement_for_binding(repo: Path, namespace: str, pack_id: str, requirement_id: str) -> dict | None:
    """The Requirement with this namespace, pack id, and requirement id. None when it is absent."""
    from checks.run import _pack_version_dir, packs_dir
    from common.store import load_pack_directory

    path = repo / "curbpack.json"
    if not path.is_file():
        return None
    try:
        config = validate_curbpack_config(read_json(path))
        root = packs_dir(repo, config)
    except (ModelError, OSError, ValueError):
        return None
    for listed in config.get("packs") or []:
        try:
            directory = _pack_version_dir(root, str(listed))
            pack, requirements = load_pack_directory(directory)
        except (ModelError, OSError, ValueError):
            continue
        if pack.get("id") != pack_id or pack.get("namespace") != namespace:
            continue
        for item in requirements:
            if (
                item.get("id") == requirement_id
                and item.get("namespace") == namespace
                and item.get("pack_id") == pack_id
            ):
                return item
    return None


def _bound_to(claim: dict, requirement: dict) -> bool:
    return (
        claim.get("namespace") == requirement.get("namespace")
        and claim.get("pack_id") == requirement.get("pack_id")
        and claim.get("requirement_id") == requirement.get("id")
        and claim.get("requirement_digest") == version_digest(requirement)
    )
