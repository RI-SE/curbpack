"""Assemble and validate one review report. Decision and signature stay in Review."""

from __future__ import annotations

import copy
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import write_json
from common.validate import validate_claim, validate_requirement, validate_run_result
from review.gitseal import read_claim_signature

REPORT_FIELDS = {"run_result", "requirements", "claims", "appendix", "decision", "signed"}


def compile_report(
    *,
    run_result: dict,
    requirements: list[dict],
    claims: list[dict],
    trust: dict[str, bytes] | None = None,
    repo: Path | None = None,
) -> dict:
    checked = copy.deepcopy(validate_run_result(run_result))
    embedded_claims = [
        validate_claim(copy.deepcopy(claim)) for claim in _claims_for_rows(checked, claims)
    ]
    report = {
        "run_result": checked,
        "requirements": _requirements_for_claims(embedded_claims, requirements),
        "claims": embedded_claims,
        "appendix": signature_appendix(checked, embedded_claims, trust or {}, repo=repo),
    }
    return validate_report(report)


def validate_report(obj: object) -> dict:
    if not isinstance(obj, dict):
        raise ModelError("review report", "(root)", "object")
    unknown = sorted(set(obj) - REPORT_FIELDS)
    if unknown:
        raise ModelError("review report", unknown[0], f"one of {sorted(REPORT_FIELDS)}")
    run_result = validate_run_result(obj.get("run_result"))
    requirements = obj.get("requirements")
    claims = obj.get("claims")
    appendix = obj.get("appendix")
    if not isinstance(requirements, list):
        raise ModelError("review report", "requirements", "list")
    if not isinstance(claims, list):
        raise ModelError("review report", "claims", "list")
    if not isinstance(appendix, list):
        raise ModelError("review report", "appendix", "list")
    ordered = _claims_for_rows(run_result, claims)
    if [claim.get("id") for claim in claims] != [claim.get("id") for claim in ordered]:
        raise ModelError("review report", "claims", "one Claim per run row, in row order")
    for claim in claims:
        validate_claim(claim)
    expected_ids = _first_requirement_ids(ordered)
    actual_ids = [requirement.get("id") if isinstance(requirement, dict) else None for requirement in requirements]
    if actual_ids != expected_ids:
        raise ModelError(
            "review report",
            "requirements",
            "the Requirements named by the Claims, in first-seen order",
        )
    for requirement in requirements:
        validate_requirement(requirement)
    for index, item in enumerate(appendix):
        _validate_appendix_item(item, index)
    if "decision" in obj and (not isinstance(obj["decision"], str) or not obj["decision"].strip()):
        raise ModelError("review report", "decision", "the reviewer's own words")
    if "signed" in obj:
        _validate_signed(obj["signed"])
        if not isinstance(obj.get("decision"), str) or not obj["decision"].strip():
            raise ModelError("review report", "decision", "words recorded before review-sign")
    return obj


def write_report(path: Path, report: dict) -> None:
    write_json(path, validate_report(report))


def signature_appendix(
    run_result: dict,
    claims: list[dict],
    trust: dict[str, bytes],
    *,
    repo: Path | None = None,
) -> list[dict]:
    """Unsigned and unverifiable Claims that were executed. Not a check result."""
    by_id = {claim.get("id"): claim for claim in claims if isinstance(claim, dict)}
    rows = []
    for result_row in run_result.get("claims") or []:
        claim = by_id.get(result_row.get("id"))
        if not isinstance(claim, dict) or not claim.get("checks"):
            continue
        relative = f"claims/{claim['id']}.json" if repo is not None else None
        reading = read_claim_signature(claim, trust, repo=repo, relative=relative)
        if reading.get("verifiable"):
            continue
        rows.append(
            {
                "id": claim["id"],
                "requirement_id": claim.get("requirement_id", ""),
                "reason": reading.get("reason") or "not verifiable",
            }
        )
    return rows


def _claims_for_rows(run_result: dict, claims: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for claim in claims:
        if isinstance(claim, dict) and isinstance(claim.get("id"), str):
            by_id.setdefault(claim["id"], claim)
    ordered = []
    for row in run_result.get("claims") or []:
        claim_id = row.get("id")
        claim = by_id.get(claim_id) if isinstance(claim_id, str) else None
        if not isinstance(claim, dict):
            raise ModelError(f"claim {claim_id or '?'}", "id", "the Claim file that ran")
        if version_digest(claim) != row.get("digest"):
            raise ModelError(f"claim {claim.get('id', '?')}", "digest", "the digest of the Claim that ran")
        configured = claim.get("checks") or []
        for item in row.get("checks") or []:
            index = item.get("index")
            if not isinstance(index, int) or index < 0 or index >= len(configured):
                raise ModelError(f"claim {claim.get('id', '?')}", "checks", "the checks that ran")
            configured_item = configured[index]
            if configured_item.get("check") != item.get("check") or configured_item.get("args") != item.get("args"):
                raise ModelError(f"claim {claim.get('id', '?')}", "checks", "the checks that ran")
        ordered.append(claim)
    return ordered


def _requirements_for_claims(claims: list[dict], requirements: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for requirement in requirements:
        if isinstance(requirement, dict) and isinstance(requirement.get("id"), str):
            by_id.setdefault(requirement["id"], requirement)
    chosen = []
    for requirement_id in _first_requirement_ids(claims):
        requirement = by_id.get(requirement_id)
        if not isinstance(requirement, dict):
            raise ModelError(
                f"requirement {requirement_id}",
                "id",
                "the Requirement named by a Claim that ran",
            )
        chosen.append(validate_requirement(copy.deepcopy(requirement)))
    return chosen


def _first_requirement_ids(claims: list[dict]) -> list[str]:
    order = []
    for claim in claims:
        requirement_id = claim.get("requirement_id")
        if isinstance(requirement_id, str) and requirement_id not in order:
            order.append(requirement_id)
    return order


def _validate_appendix_item(item: object, index: int) -> None:
    if not isinstance(item, dict):
        raise ModelError("review report", f"appendix[{index}]", "object")
    unknown = sorted(set(item) - {"id", "requirement_id", "reason"})
    if unknown:
        raise ModelError("review report", f"appendix[{index}].{unknown[0]}", "absent")
    for field in ("id", "requirement_id", "reason"):
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ModelError("review report", f"appendix[{index}].{field}", "non-empty string")


def _validate_signed(signed: object) -> None:
    if not isinstance(signed, dict):
        raise ModelError("review report", "signed", "object")
    unknown = sorted(set(signed) - {"at", "name", "signature"})
    if unknown:
        raise ModelError("review report", f"signed.{unknown[0]}", "absent")
    for field in ("at", "name", "signature"):
        value = signed.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ModelError("review report", f"signed.{field}", "non-empty string")
