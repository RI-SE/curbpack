"""Create and update repo-owned Claims. Does not rewrite the Requirement."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from common.canonical import version_digest
from common.errors import CheckError, ModelError
from common.signing import sign_object
from common.store import load_claim, load_claims, save_claim
from common.validate import validate_claim


def exist_args_for_path(path: str) -> dict:
    """Packs v2 `exist` args for one repo-relative path from Discovery."""
    cleaned = path.strip()
    if not cleaned:
        raise ModelError("claim", "path", "a non-empty repo-relative path")
    return {"paths": [cleaned]}


def require_requirement_id(requirement_id: str, known_ids: list[str]) -> str:
    """Return a Requirement id that exists in the selected Pack. Never invent a default."""
    cleaned = requirement_id.strip()
    if not cleaned:
        raise ModelError("claim", "requirement_id", "a Requirement id from the selected Pack")
    if cleaned not in known_ids:
        raise ModelError(
            "claim",
            "requirement_id",
            f"an id in the selected Pack, not {cleaned}",
        )
    return cleaned


def law_passages(requirement: dict) -> list[str]:
    """Stored `references[].law_text` values for human inspection. Not a search key."""
    passages = []
    for ref in requirement.get("references") or []:
        if not isinstance(ref, dict):
            continue
        text = ref.get("law_text")
        if isinstance(text, str) and text.strip():
            passages.append(text)
    return passages


def build_claim(
    *,
    claim_id: str,
    requirement_id: str,
    source: str,
    args: dict,
    checks: list[dict],
    description: str,
    severity: str | None = None,
) -> dict:
    """One Claim: evidence locator plus zero or more Checks. Unsigned."""
    claim: dict = {
        "id": claim_id,
        "requirement_id": requirement_id,
        "source": source,
        "args": copy.deepcopy(args),
        "description": description,
        "checks": copy.deepcopy(checks),
    }
    if severity:
        claim["severity"] = severity
    return validate_claim(claim)


def rebind(
    claim: dict,
    *,
    source: str | None = None,
    args: dict | None = None,
    checks: list[dict] | None = None,
    severity: str | None = None,
    description: str | None = None,
) -> dict:
    """Return a new claim. A changed payload drops `signed`. Same bytes keep the seal."""
    out = copy.deepcopy(claim)
    if source is not None:
        out["source"] = source
    if args is not None:
        out["args"] = copy.deepcopy(args)
    if checks is not None:
        out["checks"] = copy.deepcopy(checks)
    if severity is not None:
        if severity == "":
            out.pop("severity", None)
        else:
            out["severity"] = severity
    if description is not None:
        out["description"] = description
    if version_digest(out) != version_digest(claim):
        out.pop("signed", None)
    return validate_claim(out)


def rebind_from_fields(
    claim: dict,
    *,
    source: str,
    args_json: str,
    checks_json: str,
    severity: str,
    description: str,
) -> dict:
    name = f"claim {claim.get('id', '?')}"
    try:
        args = json.loads(args_json)
    except json.JSONDecodeError as exc:
        raise ModelError(name, "args", f"JSON object ({exc})") from exc
    if not isinstance(args, dict):
        raise ModelError(name, "args", "JSON object")
    try:
        checks = json.loads(checks_json)
    except json.JSONDecodeError as exc:
        raise ModelError(name, "checks", f"JSON list ({exc})") from exc
    if not isinstance(checks, list):
        raise ModelError(name, "checks", "JSON list")
    return rebind(
        claim,
        source=source.strip(),
        args=args,
        checks=checks,
        severity=severity.strip(),
        description=description.strip(),
    )


_ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")


def suggest_claim_id(requirement_id: str, path: str) -> str:
    """Stable id for one Requirement and one evidence locator."""

    def clean(value: str) -> str:
        return "".join(ch for ch in value.replace("/", "__") if ch in _ID_CHARS)

    ident = f"{clean(requirement_id)}-{clean(path)}"
    if not ident or ident.strip("-") == "":
        raise ModelError("claim", "id", "letters, digits, dot, underscore, or hyphen")
    return ident


def create_configured_claims(
    directory: Path,
    *,
    requirement_id: str,
    known_ids: list[str],
    source: str,
    args: dict,
    checks: list[dict],
    description: str,
    severity: str | None = None,
    claim_id: str | None = None,
) -> list[dict]:
    """Create one Claim for this evidence. An existing id is never overwritten."""
    requirement_id = require_requirement_id(requirement_id, known_ids)
    if not claim_id:
        claim_id = suggest_claim_id(requirement_id, _source_path(args))
    try:
        claim = build_claim(
            claim_id=claim_id,
            requirement_id=requirement_id,
            source=source,
            args=args,
            checks=checks,
            description=description,
            severity=severity,
        )
    except (ModelError, CheckError) as exc:
        return [{"outcome": "blocked", "id": claim_id, "error": str(exc), "signed": False}]
    destination = directory / f"{claim_id}.json"
    if destination.is_file():
        existing = load_claim(destination)
        signed = isinstance(existing.get("signed"), dict)
        same = (
            existing.get("requirement_id") == claim["requirement_id"]
            and existing.get("source") == claim["source"]
            and existing.get("args") == claim["args"]
            and existing.get("checks") == claim["checks"]
            and existing.get("description") == claim["description"]
            and existing.get("severity") == claim.get("severity")
        )
        if same:
            return [{"outcome": "unchanged", "id": claim_id, "signed": signed}]
        return [
            {
                "outcome": "blocked",
                "id": claim_id,
                "signed": signed,
                "error": "an existing claim uses this id",
            }
        ]
    write_claim(directory, claim)
    return [{"outcome": "created", "id": claim_id, "signed": False}]


def _source_path(args: dict) -> str:
    single = args.get("path")
    if isinstance(single, str) and single.strip():
        return single.strip()
    paths = args.get("paths")
    if isinstance(paths, list) and paths and isinstance(paths[0], str) and paths[0].strip():
        return paths[0].strip()
    return "evidence"


def write_claim(directory: Path, claim: dict) -> Path:
    return save_claim(directory, claim)


def read_claims(directory: Path) -> list[dict]:
    return load_claims(directory)


def read_claim(path: Path) -> dict:
    return load_claim(path)


def retire_claim(directory: Path, claim_id: str) -> None:
    path = directory / f"{claim_id}.json"
    if not path.is_file():
        raise ModelError(f"claim {claim_id}", "id", "an existing claim file")
    path.unlink()


def sign_claim(claim: dict, *, name: str, private_key: bytes, at: str) -> dict:
    """Seal a Claim. Thin wrapper over Packs v2 `sign_object`."""
    return sign_object(claim, name=name, private_key=private_key, at=at)


def read_claim_seal(
    claim: dict,
    trust: dict[str, bytes],
    *,
    repo: Path | None = None,
    relative: str | None = None,
) -> dict:
    """Five-fact Claim reading. Git commit seal when `signed` is absent."""
    from review.gitseal import read_claim_signature

    return read_claim_signature(claim, trust, repo=repo, relative=relative)
