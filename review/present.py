"""Group a raw run result by the current Requirement. No HTML."""

from __future__ import annotations

from pathlib import Path

from common.canonical import version_digest

UNRESOLVED = "Unresolved Claims"
UNCHANGED = "The Claim is unchanged since the Check run."
CHANGED = "Claim changed since Check"
NEW_RUN = "A new curbcheck run is required."
PREVIOUS_UNKNOWN = (
    "The previous Requirement relationship cannot be established from the raw run result."
)
RELATIONSHIP_CHANGED = "The current relationship changed."
UNSIGNED = "Unsigned"
VERIFICATION_UNAVAILABLE = "Verification unavailable"
UNTRUSTED_SIGNER = "Untrusted signer"
INVALID_SEAL = "Invalid seal"
CERT_IDENTITY = (
    "The certificate does not verify the signature, or name is not the identity on that certificate."
)
CERT_UNAVAILABLE = "The certificate for name is not available"
NO_SIGNED = "No signed block and no signed Git commit"
BYTES_CHANGED = "The current bytes are not the digest that was signed"


def seal_label(reading: dict | None) -> str:
    if not isinstance(reading, dict):
        return ""
    if reading.get("verifiable"):
        return ""
    reason = str(reading.get("reason") or "")
    what = str(reading.get("what") or "")
    if reason == CERT_IDENTITY:
        return INVALID_SEAL
    if reason.startswith(BYTES_CHANGED):
        return INVALID_SEAL
    if reason.startswith(CERT_UNAVAILABLE):
        return VERIFICATION_UNAVAILABLE
    if reason.startswith(NO_SIGNED):
        return UNSIGNED
    if what == "Git commit":
        if "signature status U," in reason:
            return UNTRUSTED_SIGNER
        if "signature status B," in reason:
            return INVALID_SEAL
        if "signature status E," in reason:
            return VERIFICATION_UNAVAILABLE
        return ""
    return ""


def seal_forces_open(reading: dict | None) -> bool:
    return seal_label(reading) == INVALID_SEAL


def path_adapter(check: str, args: dict) -> dict:
    """Pilot path contract for exist, contents, and dep_ban only. No HTML."""
    if check == "exist":
        paths = args.get("paths")
        if isinstance(paths, list):
            return {"paths": [item for item in paths if isinstance(item, str)]}
        return {"paths": []}
    if check == "contents":
        if isinstance(args.get("path"), str):
            return {"paths": [args["path"]]}
        paths = args.get("paths")
        if isinstance(paths, list):
            return {"paths": [item for item in paths if isinstance(item, str)]}
        return {"paths": []}
    if check == "dep_ban":
        package = args.get("package")
        banned = args.get("banned_versions")
        if isinstance(package, str) and isinstance(banned, list):
            return {
                "dep_ban": {
                    "package": package,
                    "banned_versions": [item for item in banned if isinstance(item, str)],
                }
            }
    return {}


def path_state(repo: Path, relative: str) -> str:
    if not relative or relative.startswith("/") or ".." in Path(relative).parts:
        return "invalid"
    try:
        target = (repo / relative).resolve()
        target.relative_to(repo.resolve())
    except ValueError:
        return "invalid"
    if target.is_file():
        return "present"
    return "missing"


def present_raw_run(
    *,
    run_result: dict,
    claims_by_id: dict,
    requirements_by_id: dict,
    claim_readings: dict,
    requirement_readings: dict,
    expanded: set[str] | None,
    repo: Path | None = None,
) -> dict:
    grouped: dict[str, list[dict]] = {}
    order: list[str] = []
    unresolved: list[dict] = []
    for row in run_result.get("claims") or []:
        if not isinstance(row, dict):
            continue
        claim_id = str(row.get("id") or "")
        current = claims_by_id.get(claim_id)
        item = _claim_item(row, current, claim_readings.get(claim_id), repo=repo)
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


def present_compiled_report(
    *,
    report: dict,
    current_claims_by_id: dict,
    claim_readings: dict,
    requirement_readings: dict,
    expanded: set[str] | None,
    report_reading: dict | None = None,
    repo: Path | None = None,
) -> dict:
    run_result = report.get("run_result") if isinstance(report.get("run_result"), dict) else {}
    embedded_claims = {
        claim["id"]: claim
        for claim in (report.get("claims") or [])
        if isinstance(claim, dict) and isinstance(claim.get("id"), str)
    }
    embedded_requirements = {
        requirement["id"]: requirement
        for requirement in (report.get("requirements") or [])
        if isinstance(requirement, dict) and isinstance(requirement.get("id"), str)
    }
    grouped: dict[str, list[dict]] = {}
    order: list[str] = []
    unresolved: list[dict] = []
    for row in run_result.get("claims") or []:
        if not isinstance(row, dict):
            continue
        claim_id = str(row.get("id") or "")
        embedded = embedded_claims.get(claim_id)
        current = current_claims_by_id.get(claim_id)
        item = _claim_item(row, current, claim_readings.get(claim_id), embedded=embedded, repo=repo)
        if embedded is None:
            unresolved.append(item)
            continue
        requirement_id = str(embedded.get("requirement_id") or "")
        if requirement_id not in embedded_requirements:
            item["requirement_id"] = requirement_id
            unresolved.append(item)
            continue
        if requirement_id not in grouped:
            grouped[requirement_id] = []
            order.append(requirement_id)
        grouped[requirement_id].append(item)
    force_open = seal_forces_open(report_reading)
    groups = []
    for requirement_id in order:
        claims = grouped[requirement_id]
        groups.append(
            _group(
                requirement_id,
                claims,
                requirement_readings.get(requirement_id),
                expanded,
                force_open=force_open,
            )
        )
    if unresolved:
        groups.append(
            _group(UNRESOLVED, unresolved, None, expanded, initially_open=True, force_open=force_open)
        )
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
        "decision": str(report.get("decision") or ""),
        "report_seal_label": seal_label(report_reading),
    }


def _claim_item(
    row: dict,
    current: dict | None,
    reading: dict | None,
    *,
    embedded: dict | None = None,
    repo: Path | None = None,
) -> dict:
    changed = False
    sentences: list[str] = []
    if current is not None:
        changed = version_digest(current) != row.get("digest")
        if embedded is not None:
            relationship = str(current.get("requirement_id") or "") != str(embedded.get("requirement_id") or "")
            if relationship:
                changed = True
                sentences = [RELATIONSHIP_CHANGED]
                if version_digest(current) != row.get("digest"):
                    sentences.append(CHANGED)
                sentences.append(NEW_RUN)
            elif changed:
                sentences = [CHANGED, NEW_RUN]
            else:
                sentences = [UNCHANGED]
        elif changed:
            sentences = [CHANGED, NEW_RUN, PREVIOUS_UNKNOWN]
        else:
            sentences = [UNCHANGED]
    digest_matches = current is not None and version_digest(current) == row.get("digest")
    current_checks = current.get("checks") if isinstance(current, dict) else None
    if not isinstance(current_checks, list):
        current_checks = []
    checks = []
    for check in row.get("checks") or []:
        if not isinstance(check, dict):
            continue
        args = check.get("args") if isinstance(check.get("args"), dict) else {}
        name = str(check.get("check") or "")
        adapted = path_adapter(name, args)
        paths = []
        for relative in adapted.get("paths") or []:
            state = path_state(repo, relative) if repo is not None else "missing"
            paths.append({"path": relative, "state": state})
        index = check.get("index")
        edit = "none"
        if current is not None:
            if not digest_matches:
                edit = "unsafe"
            elif not isinstance(index, int) or index < 0 or index >= len(current_checks):
                edit = "unsafe"
            elif not isinstance(current_checks[index], dict) or str(
                current_checks[index].get("check") or ""
            ) != name:
                edit = "unsafe"
            else:
                edit = "ok"
        entry = {
            "index": index,
            "check": name,
            "args": args,
            "status": str(check.get("status") or ""),
            "detail": str(check.get("detail") or ""),
            "paths": paths,
            "edit": edit,
        }
        if "dep_ban" in adapted:
            entry["dep_ban"] = adapted["dep_ban"]
        checks.append(entry)
    return {
        "id": str(row.get("id") or ""),
        "status": str(row.get("status") or ""),
        "changed": changed,
        "requirement_id": "",
        "sentences": sentences,
        "seal": reading,
        "seal_label": seal_label(reading),
        "checks": checks,
    }


def _group(
    group_id: str,
    claims: list[dict],
    seal: dict | None,
    expanded: set[str] | None,
    initially_open: bool = False,
    *,
    force_open: bool = False,
) -> dict:
    if expanded is None:
        opened = initially_open or force_open or _attention(claims, seal)
    else:
        opened = group_id in expanded
    return {
        "id": group_id,
        "open": opened,
        "seal": seal,
        "seal_label": seal_label(seal),
        "result_summary": "Result " + _result_summary(claims),
        "claims": claims,
    }


def _attention(claims: list[dict], seal: dict | None = None) -> bool:
    if seal_forces_open(seal):
        return True
    for claim in claims:
        if claim.get("changed") or claim.get("status") in {"fail", "skipped"}:
            return True
        if seal_forces_open(claim.get("seal")):
            return True
        for check in claim.get("checks") or []:
            if check.get("status") in {"fail", "skipped"}:
                return True
            for path in check.get("paths") or []:
                if isinstance(path, dict) and path.get("state") == "missing":
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
