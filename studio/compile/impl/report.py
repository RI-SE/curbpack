"""Assemble and validate one review report. Decision and signature stay in Review."""

from __future__ import annotations

import copy
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.validate import validate_claim, validate_requirement, validate_run_result
from review.gitseal import read_claim_signature

REPORT_FIELDS = {
    "run_result",
    "requirements",
    "claims",
    "appendix",
    "assessments",
    "remove_retired_checks",
    "decision",
    "items_digest",
    "signed",
}
_CHECK_ASSESSMENT = {"kind", "claim_id", "claim_digest", "index", "disposition", "text"}
_BINDING_ASSESSMENT = {
    "kind",
    "claim_id",
    "claim_digest",
    "namespace",
    "pack_id",
    "requirement_id",
    "requirement_digest",
    "binding",
    "disposition",
    "text",
}


def unmet_compile_conditions(
    *,
    run_result: dict,
    requirements: list[dict],
    claims: list[dict],
    repo: Path | None = None,
) -> list[str]:
    """Conditions that stop a report, one sentence each. Empty when compile can proceed."""
    try:
        checked = validate_run_result(copy.deepcopy(run_result))
    except ModelError:
        return ["The selected file must be a Check run result."]
    claim_gaps = _claim_file_gaps(checked, claims)
    if claim_gaps:
        return claim_gaps
    ordered = _claims_for_rows(checked, claims)
    return _requirement_version_gaps(ordered, requirements, repo)


def _claim_file_gaps(run_result: dict, claims: list[dict]) -> list[str]:
    """Each Claim file must still be the Claim that this run executed."""
    by_id: dict[str, dict] = {}
    for claim in claims:
        if isinstance(claim, dict) and isinstance(claim.get("id"), str):
            by_id.setdefault(claim["id"], claim)
    gaps = []
    for row in run_result.get("claims") or []:
        claim_id = row.get("id")
        label = claim_id if isinstance(claim_id, str) and claim_id else "?"
        claim = by_id.get(claim_id) if isinstance(claim_id, str) else None
        if not isinstance(claim, dict):
            gaps.append(f"Claim {label} must be the Claim file that ran. That file is not loaded.")
            continue
        if version_digest(claim) != row.get("digest"):
            gaps.append(
                f"Claim {label} must be the Claim that ran. "
                "The Claim file has changed since this Check run."
            )
            continue
        if not _checks_match(claim, row):
            gaps.append(f"Claim {label} must have the Checks that ran.")
    return gaps


def _checks_match(claim: dict, row: dict) -> bool:
    configured = claim.get("checks") or []
    for item in row.get("checks") or []:
        index = item.get("index")
        if not isinstance(index, int) or index < 0 or index >= len(configured):
            return False
        configured_item = configured[index]
        if configured_item.get("check") != item.get("check") or configured_item.get("args") != item.get("args"):
            return False
    return True


def _requirement_version_gaps(
    claims: list[dict],
    requirements: list[dict],
    repo: Path | None,
) -> list[str]:
    """Each recorded Requirement version must be readable. A different current version is not a substitute."""
    gaps = []
    for claim in claims:
        if not isinstance(claim.get("requirement_digest"), str):
            gaps.append(
                f"Claim {claim.get('id') or '?'} must record the Requirement version that was checked."
            )
    for requirement_id, recorded, claim in _recorded_requirement_versions(claims):
        match = _supplied_requirement(requirements, requirement_id, recorded)
        if match is None and repo is not None:
            match = _recovered_requirement(repo, claim, recorded)
        if match is None or version_digest(match) != recorded:
            gaps.append(_missing_version_sentence(requirement_id, recorded))
    return gaps


def _missing_version_sentence(requirement_id: str, recorded: str) -> str:
    return (
        f"Requirement {requirement_id} must be the recorded version {recorded}. "
        "That version was not found. The current Requirement is a different version "
        "and was not substituted. Recover that version in this repository, or bind "
        "the Claim to the current Requirement and run Checks again."
    )


def compile_report(
    *,
    run_result: dict,
    requirements: list[dict],
    claims: list[dict],
    trust: dict[str, bytes] | None = None,
    repo: Path | None = None,
    assessments: list[dict] | None = None,
    remove_retired_checks: bool | None = None,
) -> dict:
    gaps = unmet_compile_conditions(
        run_result=run_result,
        requirements=requirements,
        claims=claims,
        repo=repo,
    )
    if gaps:
        raise ModelError("review report", "conditions", "\n".join(gaps))
    checked = copy.deepcopy(validate_run_result(run_result))
    embedded_claims = [
        validate_claim(copy.deepcopy(claim)) for claim in _claims_for_rows(checked, claims)
    ]
    report = {
        "run_result": checked,
        "requirements": _requirements_for_claims(embedded_claims, requirements, repo=repo),
        "claims": embedded_claims,
        "appendix": signature_appendix(checked, embedded_claims, trust or {}, repo=repo),
    }
    if assessments:
        report["assessments"] = assessments
    if remove_retired_checks is not None:
        report["remove_retired_checks"] = remove_retired_checks
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
    expected_versions = [
        (requirement_id, recorded) for requirement_id, recorded, _claim in _recorded_requirement_versions(ordered)
    ]
    actual_versions = [_requirement_version_key(requirement) for requirement in requirements]
    actual_ids = [requirement.get("id") if isinstance(requirement, dict) else None for requirement in requirements]
    unique_ids = len(actual_ids) == len(set(actual_ids))
    if unique_ids:
        expected_ids = []
        for claim in ordered:
            requirement_id = claim.get("requirement_id")
            if isinstance(requirement_id, str) and requirement_id not in expected_ids:
                expected_ids.append(requirement_id)
        if actual_ids != expected_ids:
            raise ModelError(
                "review report",
                "requirements",
                "the Requirement versions recorded by the Claims, in first-seen order",
            )
    elif actual_versions != expected_versions:
        raise ModelError(
            "review report",
            "requirements",
            "the Requirement versions recorded by the Claims, in first-seen order",
        )
    for requirement in requirements:
        validate_requirement(copy.deepcopy(requirement))
    for index, item in enumerate(appendix):
        _validate_appendix_item(item, index)
    if "assessments" in obj:
        _validate_assessments(obj["assessments"], run_result)
    _validate_removal_flag(obj)
    if "decision" in obj and (not isinstance(obj["decision"], str) or not obj["decision"].strip()):
        raise ModelError("review report", "decision", "the reviewer's own words")
    if "items_digest" in obj:
        digest = obj["items_digest"]
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ModelError("review report", "items_digest", "the version digest of the signed review items")
    if "signed" in obj:
        _validate_signed(obj["signed"])
        if not isinstance(obj.get("decision"), str) or not obj["decision"].strip():
            raise ModelError("review report", "decision", "words recorded before review-sign")
    return obj


def write_report(path: Path, report: dict) -> None:
    write_json(path, validate_report(report))


def load_report(path: Path) -> dict:
    return validate_report(read_json(path))


def replace_saved_report(path: Path, report: dict, *, confirm: bool) -> None:
    """Write an unsigned report. An existing file is replaced only after confirmation."""
    if path.is_file() and not confirm:
        raise ModelError("review report", "confirm", "confirmation before replacing the saved report")
    write_report(path, report)


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


def _requirements_for_claims(
    claims: list[dict],
    requirements: list[dict],
    *,
    repo: Path | None = None,
) -> list[dict]:
    """Embed each Requirement version a Claim recorded.

    Two Claims may have recorded different versions of one Requirement id.
    A current Requirement with the same id and a different digest is not a substitute.
    """
    chosen = []
    for requirement_id, recorded, claim in _recorded_requirement_versions(claims):
        match = _supplied_requirement(requirements, requirement_id, recorded)
        if match is None and repo is not None:
            match = _recovered_requirement(repo, claim, recorded)
        if match is None or version_digest(match) != recorded:
            raise ModelError(
                f"requirement {requirement_id}",
                "requirement_digest",
                _missing_version_sentence(requirement_id, recorded),
            )
        embedded = copy.deepcopy(match)
        validate_requirement(copy.deepcopy(embedded))
        chosen.append(embedded)
    return chosen


def _recorded_requirement_versions(claims: list[dict]) -> list[tuple[str, str, dict]]:
    """(requirement id, recorded digest, one Claim that recorded it), first seen."""
    order = []
    seen: set[tuple[str, str]] = set()
    for claim in claims:
        requirement_id = claim.get("requirement_id")
        recorded = claim.get("requirement_digest")
        if not isinstance(requirement_id, str) or not isinstance(recorded, str):
            continue
        key = (requirement_id, recorded)
        if key in seen:
            continue
        seen.add(key)
        order.append((requirement_id, recorded, claim))
    return order


def _requirement_version_key(requirement: object) -> tuple[str, str] | None:
    if not isinstance(requirement, dict) or not isinstance(requirement.get("id"), str):
        return None
    try:
        return (requirement["id"], version_digest(requirement))
    except (TypeError, ValueError):
        return None


def _supplied_requirement(requirements: list[dict], requirement_id: str, recorded: str) -> dict | None:
    for requirement in requirements:
        if not isinstance(requirement, dict) or requirement.get("id") != requirement_id:
            continue
        try:
            if version_digest(requirement) == recorded:
                return requirement
        except (TypeError, ValueError):
            continue
    return None


def _recovered_requirement(repo: Path, claim: dict, recorded: str) -> dict | None:
    from studio.review.resolve import resolve_chain

    row = {
        "id": claim.get("id"),
        "digest": version_digest(claim),
        "namespace": claim.get("namespace"),
        "pack_id": claim.get("pack_id"),
        "requirement_id": claim.get("requirement_id"),
        "requirement_digest": recorded,
        "status": "pass",
        "checks": [
            {
                "index": index,
                "check": item.get("check"),
                "args": item.get("args") if isinstance(item.get("args"), dict) else {},
                "status": "pass",
            }
            for index, item in enumerate(claim.get("checks") or [])
            if isinstance(item, dict)
        ],
    }
    try:
        chain = resolve_chain(repo, {"claims": [row]})
    except (ModelError, OSError, ValueError):
        return None
    links = chain.get("claims") or []
    if not links or not isinstance(links[0], dict):
        return None
    requirement = links[0].get("requirement")
    if not isinstance(requirement, dict):
        return None
    obj = requirement.get("object")
    if isinstance(obj, dict) and version_digest(obj) == recorded:
        return obj
    return None


def recorded_deviations(run_result: dict) -> list[dict]:
    """Failed and skipped Checks, and stale or missing bindings, in run order."""
    deviations = []
    for row in run_result.get("claims") or []:
        if not isinstance(row, dict):
            continue
        for check in row.get("checks") or []:
            if not isinstance(check, dict) or check.get("status") not in {"fail", "skipped"}:
                continue
            deviations.append(
                {
                    "kind": "check",
                    "claim_id": row.get("id"),
                    "claim_digest": row.get("digest"),
                    "index": check.get("index"),
                    "check": check.get("check"),
                    "status": check.get("status"),
                    "detail": check.get("detail") or "",
                    "remediation_hint": check.get("remediation_hint") or "",
                }
            )
        if row.get("binding") in {"stale", "missing"}:
            deviations.append(
                {
                    "kind": "binding",
                    "claim_id": row.get("id"),
                    "claim_digest": row.get("digest"),
                    "namespace": row.get("namespace"),
                    "pack_id": row.get("pack_id"),
                    "requirement_id": row.get("requirement_id"),
                    "requirement_digest": row.get("requirement_digest"),
                    "binding": row.get("binding"),
                    "actual_digest": row.get("actual_digest") or "",
                }
            )
    return deviations


def assessment_identity(item: dict) -> tuple:
    if item.get("kind") == "binding":
        return (
            "binding",
            item.get("claim_id"),
            item.get("claim_digest"),
            item.get("namespace"),
            item.get("pack_id"),
            item.get("requirement_id"),
            item.get("requirement_digest"),
            item.get("binding"),
        )
    return ("check", item.get("claim_id"), item.get("claim_digest"), item.get("index"))


def _validate_assessments(assessments: object, run_result: dict) -> None:
    if not isinstance(assessments, list):
        raise ModelError("review report", "assessments", "list")
    known = {assessment_identity(item): item for item in recorded_deviations(run_result)}
    seen: set[tuple] = set()
    for index, item in enumerate(assessments):
        where = f"assessments[{index}]"
        if not isinstance(item, dict):
            raise ModelError("review report", where, "object")
        kind = item.get("kind")
        expected = _CHECK_ASSESSMENT if kind == "check" else _BINDING_ASSESSMENT if kind == "binding" else None
        if expected is None:
            raise ModelError("review report", f"{where}.kind", "check or binding")
        unknown = sorted(set(item) - expected)
        if unknown:
            raise ModelError("review report", f"{where}.{unknown[0]}", "absent")
        for field in expected - {"index", "text"}:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ModelError("review report", f"{where}.{field}", "non-empty string")
        text = item.get("text")
        if not isinstance(text, str):
            raise ModelError("review report", f"{where}.text", "string")
        if _comment_required(item, run_result) and not text.strip():
            expected_text = "a comment" if item.get("disposition") == "accept" else "non-empty string"
            raise ModelError("review report", f"{where}.text", expected_text)
        if kind == "check" and not isinstance(item.get("index"), int):
            raise ModelError("review report", f"{where}.index", "the Check index on the run")
        disposition = item.get("disposition")
        identity = assessment_identity(item)
        if identity in seen:
            raise ModelError("review report", where, "one assessment for each recorded deviation")
        if kind == "binding":
            if disposition not in {"accept", "must_fix"}:
                raise ModelError("review report", f"{where}.disposition", "accept or must_fix")
            if identity not in known:
                raise ModelError(
                    "review report",
                    where,
                    "a failed or skipped Check, or a stale or missing binding, on this run",
                )
        elif disposition == "retire":
            if not _check_on_run(run_result, item):
                raise ModelError("review report", where, "a Check on this run")
        elif disposition == "must_fix" and kind == "check":
            if not _check_on_run(run_result, item):
                raise ModelError("review report", where, "a Check on this run")
        elif disposition in {"accept", "must_fix"}:
            if identity not in known:
                raise ModelError(
                    "review report",
                    where,
                    "a failed or skipped Check, or a stale or missing binding, on this run",
                )
        else:
            raise ModelError("review report", f"{where}.disposition", "accept, must_fix, or retire")
        seen.add(identity)


def _comment_required(item: dict, run_result: dict) -> bool:
    """Accept on a failing Check needs text. Retire on an existing report still does."""
    disposition = item.get("disposition")
    if disposition == "retire":
        return True
    if disposition != "accept" or item.get("kind") != "check":
        return False
    return _recorded_status(run_result, item) == "fail"


def _recorded_status(run_result: dict, item: dict) -> str:
    index = item.get("index")
    if not isinstance(index, int):
        return ""
    for row in run_result.get("claims") or []:
        if not isinstance(row, dict):
            continue
        if row.get("id") != item.get("claim_id") or row.get("digest") != item.get("claim_digest"):
            continue
        checks = row.get("checks") or []
        if 0 <= index < len(checks) and isinstance(checks[index], dict):
            return str(checks[index].get("status") or "")
    return ""


def _check_on_run(run_result: dict, item: dict) -> bool:
    index = item.get("index")
    if not isinstance(index, int):
        return False
    for row in run_result.get("claims") or []:
        if not isinstance(row, dict):
            continue
        if row.get("id") != item.get("claim_id") or row.get("digest") != item.get("claim_digest"):
            continue
        checks = row.get("checks") or []
        return 0 <= index < len(checks) and isinstance(checks[index], dict)
    return False


def _validate_removal_flag(obj: dict) -> None:
    has_retire = any(
        isinstance(item, dict) and item.get("disposition") == "retire"
        for item in obj.get("assessments") or []
    )
    if "remove_retired_checks" in obj and not isinstance(obj.get("remove_retired_checks"), bool):
        raise ModelError("review report", "remove_retired_checks", "true or false")
    if has_retire and "remove_retired_checks" not in obj:
        raise ModelError("review report", "remove_retired_checks", "true or false")
    if not has_retire and "remove_retired_checks" in obj:
        raise ModelError("review report", "remove_retired_checks", "absent")


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
