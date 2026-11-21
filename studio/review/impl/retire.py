"""Remove retired Checks from live Claims after the review report is signed.

The report stays the record of the run. This module only writes Claim files
the signed report named, and only when `remove_retired_checks` is true.
"""

from __future__ import annotations

import copy
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.signing import read_signature
from common.store import save_claim
from common.validate import validate_claim
from studio.claim.impl.bind import sign_claim


def pending_claim_ids(report: dict, claims_dir: Path, trust: dict[str, bytes]) -> list[str]:
    """Claim ids whose selected retirement is not finished. Empty when removal is off."""
    if report.get("remove_retired_checks") is not True:
        return []
    return [claim_id for claim_id, state in _classified(report, claims_dir, trust) if state != "applied"]


def refuse_conflicts(report: dict, claims_dir: Path, trust: dict[str, bytes]) -> None:
    """Raise before any write when a live Claim is not the one the report recorded."""
    if report.get("remove_retired_checks") is not True:
        return
    conflicts = [claim_id for claim_id, state in _classified(report, claims_dir, trust) if state == "conflict"]
    if conflicts:
        raise _not_updated(conflicts)


def apply_pending(
    report: dict,
    claims_dir: Path,
    trust: dict[str, bytes],
    *,
    name: str,
    private_key: bytes,
    at: str,
) -> None:
    """Write Pending Claims. A Conflict blocks every remaining write."""
    if report.get("remove_retired_checks") is not True:
        return
    classified = _classified(report, claims_dir, trust)
    conflicts = [claim_id for claim_id, state in classified if state == "conflict"]
    pending = [claim_id for claim_id, state in classified if state == "pending"]
    if conflicts:
        raise _not_updated(conflicts + pending)
    for offset, claim_id in enumerate(pending):
        try:
            _write_claim(report, claims_dir, claim_id, name=name, private_key=private_key, at=at)
        except (ModelError, OSError) as exc:
            rest = pending[offset:]
            raise _not_updated(rest) from exc


def _not_updated(claim_ids: list[str]) -> ModelError:
    return ModelError("review report", "claims", "not updated: " + ", ".join(claim_ids))


def _classified(
    report: dict, claims_dir: Path, trust: dict[str, bytes]
) -> list[tuple[str, str]]:
    found = []
    for claim_id, embedded, indexes in _retirements(report):
        found.append((claim_id, _state(claims_dir, claim_id, embedded, indexes, trust)))
    return found


def _retirements(report: dict) -> list[tuple[str, dict | None, list[int]]]:
    embedded = {
        claim["id"]: claim
        for claim in report.get("claims") or []
        if isinstance(claim, dict) and isinstance(claim.get("id"), str)
    }
    order: list[str] = []
    indexes: dict[str, list[int]] = {}
    for item in report.get("assessments") or []:
        if not isinstance(item, dict) or item.get("kind") != "check" or item.get("disposition") != "retire":
            continue
        claim_id = item.get("claim_id")
        index = item.get("index")
        if not isinstance(claim_id, str) or not isinstance(index, int):
            continue
        if claim_id not in indexes:
            order.append(claim_id)
            indexes[claim_id] = []
        if index not in indexes[claim_id]:
            indexes[claim_id].append(index)
    return [(claim_id, embedded.get(claim_id), indexes[claim_id]) for claim_id in order]


def _state(
    claims_dir: Path,
    claim_id: str,
    embedded: dict | None,
    indexes: list[int],
    trust: dict[str, bytes],
) -> str:
    if not isinstance(embedded, dict):
        return "conflict"
    checks = embedded.get("checks") if isinstance(embedded.get("checks"), list) else None
    if checks is None or any(index < 0 or index >= len(checks) for index in indexes):
        return "conflict"
    remaining = [_pair(check) for index, check in enumerate(checks) if index not in set(indexes)]
    path = _claim_path(claims_dir, claim_id)
    if not remaining:
        if path is None or not path.is_file():
            return "applied"
    elif path is None or not path.is_file():
        return "conflict"
    try:
        live = validate_claim(read_json(path))
    except (ModelError, OSError, ValueError):
        return "conflict"
    if remaining and _same(live.get("checks"), remaining) and _signed_ok(live, trust):
        return "applied"
    if version_digest(live) != version_digest(embedded):
        return "conflict"
    live_checks = live.get("checks") if isinstance(live.get("checks"), list) else []
    for index in indexes:
        if index >= len(live_checks) or _pair(live_checks[index]) != _pair(checks[index]):
            return "conflict"
    return "pending"


def _write_claim(
    report: dict,
    claims_dir: Path,
    claim_id: str,
    *,
    name: str,
    private_key: bytes,
    at: str,
) -> None:
    embedded = next(
        claim
        for claim_id_, claim, _indexes in _retirements(report)
        if claim_id_ == claim_id and isinstance(claim, dict)
    )
    indexes = next(indexes for claim_id_, _claim, indexes in _retirements(report) if claim_id_ == claim_id)
    checks = embedded["checks"]
    remaining = [check for index, check in enumerate(checks) if index not in set(indexes)]
    path = _claim_path(claims_dir, claim_id)
    if path is None:
        raise ModelError("claim", "id", "letters, digits, dot, underscore, or hyphen")
    if not remaining:
        if path.is_file():
            path.unlink()
        return
    updated = copy.deepcopy(embedded)
    updated.pop("signed", None)
    updated["checks"] = remaining
    save_claim(claims_dir, sign_claim(updated, name=name, private_key=private_key, at=at))


def _claim_path(claims_dir: Path, claim_id: str) -> Path | None:
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
    if not claim_id or any(ch not in allowed for ch in claim_id):
        return None
    return claims_dir / f"{claim_id}.json"


def _pair(check: object) -> tuple:
    if not isinstance(check, dict):
        return ("", None)
    return (check.get("check"), check.get("args"))


def _same(checks: object, remaining: list[tuple]) -> bool:
    if not isinstance(checks, list) or len(checks) != len(remaining):
        return False
    return [_pair(check) for check in checks] == remaining


def _signed_ok(claim: dict, trust: dict[str, bytes]) -> bool:
    if not isinstance(claim.get("signed"), dict):
        return False
    return bool(read_signature(claim, trust, what="claim").get("verifiable"))
