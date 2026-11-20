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


def same_run(report: dict, run_result: dict) -> bool:
    if not isinstance(report, dict) or not isinstance(run_result, dict):
        return False
    return report.get("run_result") == run_result


def unchecked_requirement_ids(selected_ids: list[str], report: dict) -> list[str]:
    checked = {
        claim.get("requirement_id")
        for claim in (report.get("claims") or [])
        if isinstance(claim, dict) and isinstance(claim.get("requirement_id"), str)
    }
    return [requirement_id for requirement_id in selected_ids if requirement_id not in checked]


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
    chain: dict | None = None,
) -> dict:
    grouped: dict[str, list[dict]] = {}
    order: list[str] = []
    unresolved: list[dict] = []
    links = list(chain.get("claims") or []) if isinstance(chain, dict) else []
    for index, row in enumerate(run_result.get("claims") or []):
        if not isinstance(row, dict):
            continue
        claim_id = str(row.get("id") or "")
        current = claims_by_id.get(claim_id)
        link = links[index] if index < len(links) else None
        item = _claim_item(row, current, claim_readings.get(claim_id), repo=repo, chain=link)
        recorded_id = str(row.get("requirement_id") or "")
        live_id = str(current.get("requirement_id") or "") if isinstance(current, dict) else ""
        requirement_id = recorded_id or live_id
        fallback = requirements_by_id.get(requirement_id) if requirement_id else None
        _apply_requirement_context(item, row, link, fallback if isinstance(fallback, dict) else None)
        if current is None and not recorded_id:
            unresolved.append(item)
            continue
        if not requirement_id or (requirement_id not in requirements_by_id and not recorded_id):
            item["requirement_id"] = requirement_id
            unresolved.append(item)
            continue
        if requirement_id not in requirements_by_id:
            item["requirement_id"] = requirement_id
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
                passages=_group_passages(claims, requirements_by_id.get(requirement_id)),
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
    chain: dict | None = None,
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
    links = list(chain.get("claims") or []) if isinstance(chain, dict) else []
    for index, row in enumerate(run_result.get("claims") or []):
        if not isinstance(row, dict):
            continue
        claim_id = str(row.get("id") or "")
        embedded = embedded_claims.get(claim_id)
        current = current_claims_by_id.get(claim_id)
        link = links[index] if index < len(links) else None
        item = _claim_item(
            row, current, claim_readings.get(claim_id), embedded=embedded, repo=repo, chain=link
        )
        requirement_id_for_hint = str(embedded.get("requirement_id") or "") if isinstance(embedded, dict) else ""
        fallback = embedded_requirements.get(requirement_id_for_hint)
        _apply_requirement_context(item, row, link, fallback if isinstance(fallback, dict) else None)
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
                passages=_group_passages(claims, embedded_requirements.get(requirement_id)),
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
    chain: dict | None = None,
) -> dict:
    changed = False
    sentences: list[str] = []
    requirement_location = ""
    if isinstance(chain, dict) and isinstance(chain.get("requirement"), dict):
        requirement_location = str(chain["requirement"].get("location") or "")
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
            sentences = [CHANGED, NEW_RUN]
            if requirement_location not in {"current", "historical"}:
                sentences.append(PREVIOUS_UNKNOWN)
        else:
            sentences = [UNCHANGED]
    described = embedded if isinstance(embedded, dict) else current
    description = str(described.get("description") or "") if isinstance(described, dict) else ""
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
        hint = check.get("remediation_hint")
        if isinstance(hint, str) and hint:
            entry["remediation_hint"] = hint
        if "dep_ban" in adapted:
            entry["dep_ban"] = adapted["dep_ban"]
        checks.append(entry)
    described_pack = str(described.get("pack_id") or "") if isinstance(described, dict) else ""
    described_requirement = str(described.get("requirement_id") or "") if isinstance(described, dict) else ""
    return {
        "id": str(row.get("id") or ""),
        "digest": str(row.get("digest") or ""),
        "status": str(row.get("status") or ""),
        "description": description,
        "binding": row.get("binding") if row.get("binding") in {"match", "stale", "missing"} else "",
        "namespace": str(row.get("namespace") or ""),
        "pack_id": str(row.get("pack_id") or described_pack),
        "recorded_requirement_id": str(row.get("requirement_id") or ""),
        "inspect_requirement_id": str(row.get("requirement_id") or described_requirement),
        "requirement_digest": str(row.get("requirement_digest") or ""),
        "changed": changed,
        "requirement_id": "",
        "sentences": sentences,
        "seal": reading,
        "seal_label": seal_label(reading),
        "checks": checks,
        **_chain_fields(chain),
    }


def _chain_fields(chain: dict | None) -> dict:
    if not isinstance(chain, dict):
        return {}
    requirement = chain.get("requirement") if isinstance(chain.get("requirement"), dict) else {}
    claim = chain.get("claim") if isinstance(chain.get("claim"), dict) else {}
    signature = requirement.get("signature") if isinstance(requirement.get("signature"), dict) else {}
    if not signature and isinstance(claim.get("signature"), dict):
        signature = claim["signature"]
    return {
        "requirement_location": str(requirement.get("location") or ""),
        "requirement_commit": str(requirement.get("commit") or ""),
        "recorded_digest": str(requirement.get("digest") or ""),
        "current_digest": str(requirement.get("current_digest") or ""),
        "signature_method": str(signature.get("method") or ""),
        "signature_status": str(signature.get("status") or ""),
        "differences": requirement.get("differences") if isinstance(requirement.get("differences"), list) else [],
        "claim_location": str(claim.get("location") or ""),
        "claim_commit": str(claim.get("commit") or ""),
        "claim_recorded_digest": str(claim.get("digest") or ""),
        "claim_recovered_digest": str(claim.get("digest") or "") if claim.get("location") == "historical" else "",
        "claim_current_digest": str(claim.get("current_digest") or "")
        or (str(claim.get("digest") or "") if claim.get("location") == "current" else ""),
        "claim_signature_method": str((claim.get("signature") or {}).get("method") or "") if isinstance(claim.get("signature"), dict) else "",
        "claim_signature_status": str((claim.get("signature") or {}).get("status") or "") if isinstance(claim.get("signature"), dict) else "",
        "chain_binding": str(chain.get("binding") or ""),
    }


def _apply_requirement_context(item: dict, row: dict, chain: dict | None, fallback: dict | None) -> None:
    """Attach the Requirement hint and passages from the version this run recorded."""
    recorded = row.get("requirement_digest")
    if not isinstance(recorded, str) or not recorded:
        described = fallback if isinstance(fallback, dict) else None
        recorded = ""
        if isinstance(described, dict):
            try:
                recorded = version_digest(described)
            except (TypeError, ValueError):
                recorded = ""
    found = chain.get("requirement") if isinstance(chain, dict) else None
    obj = found.get("object") if isinstance(found, dict) and isinstance(found.get("object"), dict) else None
    location = str(found.get("location") or "") if isinstance(found, dict) else ""
    chosen = None
    chosen_from = ""
    if isinstance(recorded, str) and recorded:
        if obj is not None and version_digest(obj) == recorded:
            chosen = obj
            chosen_from = location or "historical"
        elif isinstance(fallback, dict):
            try:
                if version_digest(fallback) == recorded:
                    chosen = fallback
                    chosen_from = "current"
            except (TypeError, ValueError):
                chosen = None
    else:
        chosen = obj if obj is not None else fallback if isinstance(fallback, dict) else None
        chosen_from = location if obj is not None else ("current" if isinstance(chosen, dict) else "")
    if chosen is None:
        item["requirement_hint"] = ""
        item["requirement_hint_from"] = "unresolved" if row.get("requirement_digest") else ""
        item["requirement_passages"] = []
        return
    hint = chosen.get("remediation_hint")
    item["requirement_hint"] = hint if isinstance(hint, str) else ""
    item["requirement_hint_from"] = chosen_from
    item["requirement_passages"] = _passages(chosen)


def _group_passages(claims: list[dict], fallback: dict | None) -> list:
    contextual = [claim for claim in claims if "requirement_hint_from" in claim]
    if not contextual:
        return _passages(fallback if isinstance(fallback, dict) else None)
    for claim in contextual:
        if claim.get("requirement_hint_from") == "unresolved":
            continue
        return claim.get("requirement_passages") or []
    return []


def _passages(requirement: dict | None) -> list[dict]:
    if not isinstance(requirement, dict):
        return []
    rows = []
    for ref in requirement.get("references") or []:
        if not isinstance(ref, dict):
            continue
        text = str(ref.get("law_text") or "").strip()
        if not text:
            continue
        rows.append({"locator": str(ref.get("locator") or ""), "law_text": text})
    return rows


def _group(
    group_id: str,
    claims: list[dict],
    seal: dict | None,
    expanded: set[str] | None,
    initially_open: bool = False,
    *,
    force_open: bool = False,
    passages: list | None = None,
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
        "passages": passages or [],
        "claims": claims,
    }


def _attention(claims: list[dict], seal: dict | None = None) -> bool:
    if seal_forces_open(seal):
        return True
    for claim in claims:
        if claim.get("binding") in {"stale", "missing"}:
            return True
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
