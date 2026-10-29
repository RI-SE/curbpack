"""Group a raw run result by the current Requirement. No HTML."""

from __future__ import annotations

from common.canonical import version_digest

UNRESOLVED = "Unresolved Claims"
UNCHANGED = "The Claim is unchanged since the Check run."
CHANGED = "Claim changed since Check"
NEW_RUN = "A new curbcheck run is required."
PREVIOUS_UNKNOWN = (
    "The previous Requirement relationship cannot be established from the raw run result."
)


def present_raw_run(
    *,
    run_result: dict,
    claims_by_id: dict,
    requirements_by_id: dict,
    claim_readings: dict,
    requirement_readings: dict,
    expanded: set[str] | None,
) -> dict:
    grouped: dict[str, list[dict]] = {}
    order: list[str] = []
    unresolved: list[dict] = []
    for row in run_result.get("claims") or []:
        if not isinstance(row, dict):
            continue
        claim_id = str(row.get("id") or "")
        current = claims_by_id.get(claim_id)
        item = _claim_item(row, current, claim_readings.get(claim_id))
        if current is None:
            unresolved.append(item)
            continue
        requirement_id = str(current.get("requirement_id") or "")
        if requirement_id not in requirements_by_id:
            item["requirement_id"] = requirement_id
            unresolved.append(item)
            continue
        if requirement_id not in grouped:
            grouped[requirement_id] = []
            order.append(requirement_id)
        grouped[requirement_id].append(item)
    groups = []
    for requirement_id in order:
        claims = grouped[requirement_id]
        groups.append(
            _group(
                requirement_id,
                claims,
                requirement_readings.get(requirement_id),
                expanded,
            )
        )
    if unresolved:
        groups.append(_group(UNRESOLVED, unresolved, None, expanded, initially_open=True))
    packs = []
    for pack in run_result.get("packs") or []:
        if isinstance(pack, dict):
            packs.append({"id": str(pack.get("id") or ""), "version": str(pack.get("version") or "")})
    return {
        "header": {
            "tool": str(run_result.get("tool") or ""),
            "tool_version": str(run_result.get("tool_version") or ""),
            "commit": str(run_result.get("commit") or ""),
            "worktree": str(run_result.get("worktree") or ""),
            "packs": packs,
        },
        "groups": groups,
    }


def _claim_item(row: dict, current: dict | None, reading: dict | None) -> dict:
    changed = False
    sentences: list[str] = []
    if current is not None:
        changed = version_digest(current) != row.get("digest")
        if changed:
            sentences = [CHANGED, NEW_RUN, PREVIOUS_UNKNOWN]
        else:
            sentences = [UNCHANGED]
    checks = []
    for check in row.get("checks") or []:
        if not isinstance(check, dict):
            continue
        checks.append(
            {
                "index": check.get("index"),
                "check": str(check.get("check") or ""),
                "args": check.get("args") if isinstance(check.get("args"), dict) else {},
                "status": str(check.get("status") or ""),
                "detail": str(check.get("detail") or ""),
            }
        )
    return {
        "id": str(row.get("id") or ""),
        "status": str(row.get("status") or ""),
        "changed": changed,
        "requirement_id": "",
        "sentences": sentences,
        "seal": reading,
        "checks": checks,
    }


def _group(group_id: str, claims: list[dict], seal: dict | None, expanded: set[str] | None, initially_open: bool = False) -> dict:
    if expanded is None:
        opened = initially_open or _attention(claims)
    else:
        opened = group_id in expanded
    return {
        "id": group_id,
        "open": opened,
        "seal": seal,
        "result_summary": "Result " + _result_summary(claims),
        "claims": claims,
    }


def _attention(claims: list[dict]) -> bool:
    for claim in claims:
        if claim.get("changed") or claim.get("status") in {"fail", "skipped"}:
            return True
        for check in claim.get("checks") or []:
            if check.get("status") in {"fail", "skipped"}:
                return True
    return False


def _result_summary(claims: list[dict]) -> str:
    statuses = [str(claim.get("status") or "") for claim in claims]
    for claim in claims:
        statuses.extend(str(check.get("status") or "") for check in claim.get("checks") or [])
    if "fail" in statuses:
        return "fail"
    if "skipped" in statuses:
        return "skipped"
    return "pass"
