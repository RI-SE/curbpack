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


def record_binding(claim: dict, requirement: dict) -> dict:
    """Copy the selected Requirement's identity and payload digest onto the Claim."""
    if not isinstance(requirement, dict):
        raise ModelError("claim", "requirement", "the selected Requirement")
    out = copy.deepcopy(claim)
    name = f"claim {out.get('id', '?')}"
    for field, source in (
        ("namespace", "namespace"),
        ("pack_id", "pack_id"),
        ("requirement_id", "id"),
    ):
        value = requirement.get(source)
        if not isinstance(value, str) or not value.strip():
            raise ModelError(name, field, "the selected Requirement")
        out[field] = value
    out["requirement_digest"] = version_digest(requirement)
    return out


def build_claim(
    *,
    claim_id: str,
    requirement: dict,
    source: str,
    args: dict,
    checks: list[dict],
    description: str,
    severity: str | None = None,
) -> dict:
    """One Claim: evidence locator plus zero or more Checks. Unsigned."""
    claim: dict = {
        "id": claim_id,
        "source": source,
        "args": copy.deepcopy(args),
        "description": description,
        "checks": copy.deepcopy(checks),
    }
    if severity:
        claim["severity"] = severity
    return validate_claim(record_binding(claim, requirement))


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


def rebind_requirement(claim: dict, requirement: dict) -> dict:
    """Explicit rebind. A changed binding drops the previous seal."""
    out = record_binding(claim, requirement)
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
    requirement: dict,
    known_ids: list[str],
    source: str,
    args: dict,
    checks: list[dict],
    description: str,
    severity: str | None = None,
    claim_id: str | None = None,
) -> list[dict]:
    """Create one Claim for this evidence. An existing id is never overwritten."""
    requirement_id = require_requirement_id(str(requirement.get("id") or ""), known_ids)
    if not claim_id:
        claim_id = suggest_claim_id(requirement_id, _source_path(args))
    try:
        claim = build_claim(
            claim_id=claim_id,
            requirement=requirement,
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
            and existing.get("namespace") == claim["namespace"]
            and existing.get("pack_id") == claim["pack_id"]
            and existing.get("requirement_digest") == claim["requirement_digest"]
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
    from common.jsonio import read_json, write_json
    from common.store import _safe_id
    from common.validate import validate_claim

    checked = validate_claim(claim)
    path = directory / f"{_safe_id(checked['id'], 'claim')}.json"
    if path.is_file():
        stored = read_json(path)
        if isinstance(stored, dict) and "format_version" not in stored:
            checked.pop("format_version", None)
            write_json(path, checked)
            return path
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


def claims_sharing_a_source(claim: dict, claims: list) -> list[dict]:
    """Other Claims that name a file this Claim also names.

    A file counts when the Claim or one of its checks names it in `path` or
    `paths`. The Claim itself is omitted. The function does not decide whether
    the checks agree.
    """
    mine = set(_claim_sources(claim))
    if not mine:
        return []
    own_id = str(claim.get("id") or "")
    found: list[dict] = []
    seen: set[str] = set()
    for other in claims:
        if not isinstance(other, dict) or other is claim:
            continue
        other_id = str(other.get("id") or "")
        if own_id and other_id == own_id:
            continue
        if mine.isdisjoint(_claim_sources(other)):
            continue
        key = other_id or str(id(other))
        if key in seen:
            continue
        seen.add(key)
        found.append(other)
    return found


def source_overlap(claim: dict, claims: list) -> list[dict]:
    """One row per shared file: the file, the other Requirement, and its checks there.

    Sorted by file name, then Requirement. A check is listed when it names that
    file, or when it names no file and the Claim's evidence includes it.
    """
    from checks.labels import check_detail

    mine = set(_claim_sources(claim))
    rows = []
    for other in claims_sharing_a_source(claim, claims):
        requirement_id = str(other.get("requirement_id") or "")
        for path in _claim_sources(other):
            if path not in mine:
                continue
            rows.append(
                {
                    "file": path,
                    "requirement_id": requirement_id,
                    "checks": [
                        check_detail(entry)
                        for entry in _check_entries(other)
                        if _check_covers(other, entry, path)
                    ],
                }
            )
    rows.sort(key=lambda row: (row["file"].casefold(), row["requirement_id"].casefold()))
    return rows


def _check_covers(claim: dict, entry: dict, path: str) -> bool:
    named = _paths(entry.get("args"))
    if named:
        return path in named
    return path in _claim_sources(claim)


def _claim_sources(claim: dict) -> list[str]:
    sources = _paths(claim.get("args"))
    for entry in _check_entries(claim):
        for path in _paths(entry.get("args")):
            if path not in sources:
                sources.append(path)
    return sources


def _check_entries(claim: dict) -> list[dict]:
    return [entry for entry in claim.get("checks") or [] if isinstance(entry, dict)]


def _paths(args: object) -> list[str]:
    if not isinstance(args, dict):
        return []
    found: list[str] = []
    single = args.get("path")
    if isinstance(single, str) and single.strip():
        found.append(single.strip())
    listed = args.get("paths")
    if isinstance(listed, list):
        for item in listed:
            if isinstance(item, str) and item.strip() and item.strip() not in found:
                found.append(item.strip())
    return found
