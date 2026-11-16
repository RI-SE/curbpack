"""Read-only resolution of the Requirement and Claim a Run Result recorded."""

from __future__ import annotations

import copy
from pathlib import Path

from checks.run import _pack_version_dir, claims_dir, packs_dir
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.store import load_pack_directory
from common.validate import validate_claim, validate_curbpack_config


def resolve_chain(repo: Path, run_result: dict) -> dict:
    """Return the current objects whose identity and digest match the run. Nothing is written."""
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    requirements = _current_requirements(repo, config)
    claims = _current_claims(repo, config)
    return {
        "claims": [
            _resolve_row(row, requirements, claims)
            for row in run_result.get("claims") or []
            if isinstance(row, dict)
        ]
    }


def _current_requirements(repo: Path, config: dict) -> list:
    root = packs_dir(repo, config)
    loaded = []
    for pack_id in config.get("packs") or []:
        try:
            loaded.append(load_pack_directory(_pack_version_dir(root, pack_id)))
        except (ModelError, OSError, ValueError):
            continue
    return loaded


def _current_claims(repo: Path, config: dict) -> list[dict]:
    folder = claims_dir(repo, config)
    if not folder.is_dir():
        return []
    claims = []
    for path in sorted(folder.glob("*.json")):
        try:
            claims.append(validate_claim(read_json(path)))
        except (ModelError, OSError, ValueError):
            continue
    return claims


def _resolve_row(row: dict, requirements: list, claims: list[dict]) -> dict:
    requirement = _matching_requirement(row, requirements)
    claim = _matching_claim(row, claims)
    return {
        "requirement": _found("current", row.get("requirement_digest"), requirement),
        "claim": _found("current", row.get("digest"), claim),
        "checks": _checks(claim, row),
    }


def _matching_requirement(row: dict, loaded: list):
    namespace = row.get("namespace")
    pack_id = row.get("pack_id")
    requirement_id = row.get("requirement_id")
    recorded = row.get("requirement_digest")
    for pack, items in loaded:
        if pack.get("id") != pack_id or pack.get("namespace") != namespace:
            continue
        for item in items:
            if item.get("id") != requirement_id or item.get("namespace") != namespace:
                continue
            if version_digest(item) == recorded:
                return item
    return None


def _matching_claim(row: dict, claims: list[dict]):
    recorded = row.get("digest")
    for claim in claims:
        if claim.get("id") == row.get("id") and version_digest(claim) == recorded:
            return claim
    return None


def _found(location: str, digest: object, obj: dict | None) -> dict:
    if obj is None:
        return {"location": "unresolved", "digest": digest, "object": None}
    return {"location": location, "digest": digest, "object": copy.deepcopy(obj)}


def _checks(claim: dict | None, row: dict) -> list[dict]:
    if claim is None:
        return []
    recorded = {
        item.get("index"): item
        for item in row.get("checks") or []
        if isinstance(item, dict)
    }
    compared = []
    for index, item in enumerate(claim.get("checks") or []):
        found = recorded.get(index)
        corresponds = (
            isinstance(found, dict)
            and found.get("check") == item.get("check")
            and found.get("args") == item.get("args")
        )
        compared.append(
            {
                "index": index,
                "check": item.get("check"),
                "args": item.get("args"),
                "corresponds": corresponds,
            }
        )
    return compared
