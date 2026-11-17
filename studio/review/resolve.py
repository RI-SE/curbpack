"""Read-only resolution of the Requirement and Claim a Run Result recorded."""

from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path

from curbcheck.api import _pack_version_dir, claims_dir, packs_dir
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.signing import verify_object
from common.store import load_pack_directory
from common.validate import validate_claim, validate_curbpack_config, validate_requirement

_GIT_ENV_DROP = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
)


def resolve_chain(repo: Path, run_result: dict, trust: dict | None = None) -> dict:
    """Return the recorded objects. A current file is not substituted for a different digest."""
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    requirements = _current_requirements(repo, config)
    claims = _current_claims(repo, config)
    known = trust or {}
    return {
        "claims": [
            _resolve_row(repo, row, requirements, claims, known)
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


def _resolve_row(repo: Path, row: dict, requirements: list, claims: list[dict], trust: dict) -> dict:
    requirement = _requirement_result(repo, row, requirements, trust)
    claim_result, claim = _claim_result(repo, row, claims, trust)
    return {
        "requirement": requirement,
        "claim": claim_result,
        "checks": _checks(claim, row),
        "binding": _row_binding(claim, row),
    }


def _requirement_result(repo: Path, row: dict, loaded: list, trust: dict) -> dict:
    recorded = row.get("requirement_digest")
    current = _matching_requirement(row, loaded)
    identity = _identity_requirement(row, loaded)
    if current is not None:
        return _with_signature(repo, _found("current", recorded, current), trust, kind="requirement")
    found = _historical_requirement(repo, row)
    if found == "unavailable":
        result = _found("unresolved", recorded, None)
        result["history"] = "unavailable"
        return _with_signature(repo, result, trust, kind="requirement")
    if found is None:
        return _with_signature(repo, _found("unresolved", recorded, None), trust, kind="requirement")
    commit, obj = found
    result = _found("historical", recorded, obj)
    result["commit"] = commit
    if identity is not None:
        actual = version_digest(identity)
        if actual != recorded:
            result["current_digest"] = actual
        result["differences"] = _requirement_differences(obj, identity)
    return _with_signature(repo, result, trust, kind="requirement")


def _claim_result(repo: Path, row: dict, claims: list[dict], trust: dict):
    recorded = row.get("digest")
    current = _matching_claim(row, claims)
    if current is not None:
        return _with_signature(repo, _found("current", recorded, current), trust, kind="claim"), current
    found = _historical_claim(repo, row)
    if found == "unavailable":
        result = _found("unresolved", recorded, None)
        result["history"] = "unavailable"
        return _with_signature(repo, result, trust, kind="claim"), None
    if found is None:
        return _with_signature(repo, _found("unresolved", recorded, None), trust, kind="claim"), None
    commit, obj = found
    result = _found("historical", recorded, obj)
    result["commit"] = commit
    same_id = next((item for item in claims if item.get("id") == row.get("id")), None)
    if same_id is not None:
        actual = version_digest(same_id)
        if actual != recorded:
            result["current_digest"] = actual
    return _with_signature(repo, result, trust, kind="claim"), obj


def _historical_requirement(repo: Path, row: dict):
    requirement_id = row.get("requirement_id")
    if not isinstance(requirement_id, str) or "/" in requirement_id or not requirement_id.strip():
        return None

    def accept(obj: dict) -> bool:
        return (
            obj.get("namespace") == row.get("namespace")
            and obj.get("pack_id") == row.get("pack_id")
            and obj.get("id") == requirement_id
            and version_digest(obj) == row.get("requirement_digest")
        )

    return _historical_object(repo, f"/{requirement_id}.json", _requirement_blob, accept)


def _historical_claim(repo: Path, row: dict):
    claim_id = row.get("id")
    if not isinstance(claim_id, str) or "/" in claim_id or not claim_id.strip():
        return None

    def accept(obj: dict) -> bool:
        return obj.get("id") == claim_id and version_digest(obj) == row.get("digest")

    return _historical_object(repo, f"/{claim_id}.json", _claim_blob, accept)


def _historical_object(repo: Path, suffix: str, parse, accept):
    log = _git(repo, "log", "--all", "--pretty=format:%H", "--name-only")
    if log is None:
        return "unavailable"
    commit = None
    for line in log.splitlines():
        text = line.strip()
        if not text:
            commit = None
            continue
        if len(text) == 40 and all(char in "0123456789abcdef" for char in text):
            commit = text
            continue
        if commit is None or not text.endswith(suffix):
            continue
        raw = _git(repo, "show", f"{commit}:{text}", decode=False)
        if raw is None:
            continue
        obj = parse(raw)
        if obj is not None and accept(obj):
            return commit, obj
    return None


def _requirement_blob(raw: bytes):
    parsed = _parsed_blob(raw)
    if parsed is None:
        return None
    try:
        return validate_requirement(parsed)
    except ModelError:
        return None


def _claim_blob(raw: bytes):
    parsed = _parsed_blob(raw)
    if parsed is None:
        return None
    try:
        return validate_claim(parsed)
    except ModelError:
        return None


def _parsed_blob(raw: bytes):
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _git(repo: Path, *args: str, decode: bool = True):
    env = os.environ.copy()
    for key in _GIT_ENV_DROP:
        env.pop(key, None)
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            env=env,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    if decode:
        return result.stdout.decode("utf-8", errors="replace")
    return result.stdout


def _requirement_differences(historical: dict, current: dict) -> list[dict]:
    from requirements.compare import _changed_fields
    from requirements.editing import EDITABLE

    fields = []
    for name in _changed_fields(historical, current):
        if name not in EDITABLE:
            continue
        fields.append(
            {
                "name": name,
                "historical": historical.get(name),
                "current": current.get(name),
            }
        )
    return fields


def _with_signature(repo: Path, result: dict, trust: dict, *, kind: str) -> dict:
    result["signature"] = _signature(
        result.get("object"), repo, result.get("commit"), trust, kind=kind, current=result.get("location") == "current"
    )
    return result


def _signature(obj: object, repo: Path, commit: object, trust: dict, *, kind: str, current: bool) -> dict:
    if isinstance(obj, dict) and isinstance(obj.get("signed"), dict):
        reading = verify_object(version_digest(obj), obj.get("signed"), trust)
        reading["verifiable"] = reading.get("status") == "valid"
        return reading
    if isinstance(commit, str) and commit:
        git_reading = _commit_signature(repo, commit)
        if git_reading is not None:
            return git_reading
    if current and isinstance(obj, dict):
        git_reading = _current_file_signature(repo, obj, kind)
        if git_reading is not None:
            return git_reading
    return {
        "status": "unsigned",
        "method": "none",
        "verifiable": False,
        "reason": "No signed block and no signed Git commit. The object is unsigned.",
    }


def _current_file_signature(repo: Path, obj: dict, kind: str):
    from review.gitseal import git_commit_signature

    try:
        config = validate_curbpack_config(read_json(repo / "curbpack.json"))
        if kind == "claim":
            path = claims_dir(repo, config) / f"{obj.get('id')}.json"
        else:
            path = _pack_version_dir(packs_dir(repo, config), str(obj.get("pack_id") or "")) / f"{obj.get('id')}.json"
        relative = str(path.resolve().relative_to(repo.resolve()))
    except (ModelError, OSError, ValueError):
        return None
    reading = git_commit_signature(repo, relative)
    if reading is None:
        return None
    verifiable = bool(reading.get("verifiable"))
    return {
        "status": "valid" if verifiable else "invalid",
        "method": "git",
        "signer": reading.get("who"),
        "version": reading.get("version"),
        "verifiable": verifiable,
    }


def _commit_signature(repo: Path, commit: str):
    text = _git(repo, "log", "-1", "--format=%G?%n%GS%n%H", commit)
    if not isinstance(text, str):
        return None
    lines = text.splitlines()
    if len(lines) < 3:
        return None
    status, signer, found = lines[0], lines[1], lines[2]
    if status == "N" or not signer.strip():
        return None
    verifiable = status == "G"
    return {
        "status": "valid" if verifiable else "invalid",
        "method": "git",
        "signer": signer.strip(),
        "version": found.strip(),
        "verifiable": verifiable,
    }


def _identity_requirement(row: dict, loaded: list):
    namespace = row.get("namespace")
    pack_id = row.get("pack_id")
    requirement_id = row.get("requirement_id")
    for pack, items in loaded:
        if pack.get("id") != pack_id or pack.get("namespace") != namespace:
            continue
        for item in items:
            if item.get("id") == requirement_id and item.get("namespace") == namespace:
                return item
    return None


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
    recorded = {
        item.get("index"): item
        for item in row.get("checks") or []
        if isinstance(item, dict)
    }
    compared = []
    for index, item in enumerate((claim or {}).get("checks") or []):
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
    seen = {item["index"] for item in compared}
    for index, found in recorded.items():
        if index in seen or not isinstance(index, int):
            continue
        compared.append(
            {
                "index": index,
                "check": found.get("check"),
                "args": found.get("args"),
                "corresponds": False,
            }
        )
    return compared


def _row_binding(claim: dict | None, row: dict) -> str:
    if claim is None or not row.get("requirement_digest"):
        return "unresolved"
    same = (
        claim.get("namespace") == row.get("namespace")
        and claim.get("pack_id") == row.get("pack_id")
        and claim.get("requirement_id") == row.get("requirement_id")
        and claim.get("requirement_digest") == row.get("requirement_digest")
    )
    return "match" if same else "mismatch"
