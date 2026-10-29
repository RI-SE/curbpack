"""Shape checks for Packs v2 objects.

A draft and a sealed object share this shape. `published=True` additionally
requires a publisher release: `signed` present, `origin` absent.
"""

from __future__ import annotations

from common.errors import ModelError

REQUIREMENT_FIELDS = {
    "id",
    "pack_id",
    "strength",
    "responsible",
    "applicability",
    "exceptions",
    "scope",
    "remediation_hint",
    "source",
    "references",
    "note",
    "discovery_hints",
    "origin",
    "signed",
}

# Old PoC fields and fields packs2.md explicitly removed.
FORBIDDEN_REQUIREMENT_FIELDS = {
    "law_text",
    "search",
    "claim",
    "description",
    "expected",
    "severity",
    "statement",
    "limitations",
    "mandatory",
    "verification",
    "source_digest",
    "locus",
}

PACK_FIELDS = {
    "id",
    "name",
    "version",
    "assurance_class",
    "description",
    "jurisdiction",
    "source",
    "signed",
}

CLAIM_FIELDS = {
    "id",
    "requirement_id",
    "source",
    "args",
    "description",
    "severity",
    "checks",
    "signed",
}

FORBIDDEN_CLAIM_FIELDS = {"remediation", "expected", "settlement", "law_text", "search"}

SOURCE_FIELDS = {"framework", "instrument", "identifier", "edition", "language", "url"}
SOURCE_REQUIRED = ("framework", "instrument", "identifier", "language", "url")

STRENGTHS = {"MUST", "SHOULD", "MAY"}
SEVERITIES = {"high", "medium", "critical"}


def _expect(object_name: str, field: str, expected: str) -> None:
    raise ModelError(object_name, field, expected)


def _require_dict(obj: object, object_name: str) -> dict:
    if not isinstance(obj, dict):
        _expect(object_name, "(root)", "object")
    return obj


def _nonempty_str(obj: dict, object_name: str, field: str, *, required: bool) -> None:
    if field not in obj:
        if required:
            _expect(object_name, field, "non-empty string")
        return
    value = obj[field]
    if not isinstance(value, str) or not value.strip():
        _expect(object_name, field, "non-empty string")


def _reject_unknown(obj: dict, object_name: str, allowed: set[str]) -> None:
    unknown = sorted(set(obj) - allowed)
    if unknown:
        _expect(object_name, unknown[0], f"one of {sorted(allowed)}")


def _validate_signed_block(obj: dict, object_name: str, *, required: bool) -> None:
    if "signed" not in obj:
        if required:
            _expect(object_name, "signed", "seal with at, name, and signature")
        return
    signed = obj["signed"]
    if not isinstance(signed, dict):
        _expect(object_name, "signed", "object")
    _reject_unknown(signed, f"{object_name}.signed", {"at", "name", "signature"})
    for field in ("at", "name", "signature"):
        _nonempty_str(signed, f"{object_name}.signed", field, required=True)


def _validate_source(source: object, object_name: str, *, require_edition: bool) -> None:
    if not isinstance(source, dict):
        _expect(object_name, "source", "object")
    _reject_unknown(source, f"{object_name}.source", SOURCE_FIELDS)
    for field in SOURCE_REQUIRED:
        _nonempty_str(source, f"{object_name}.source", field, required=True)
    if require_edition or "edition" in source:
        _nonempty_str(source, f"{object_name}.source", "edition", required=True)


def _string_list(value: object, object_name: str, field: str) -> None:
    if not isinstance(value, list) or not value:
        _expect(object_name, field, "non-empty list of strings")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            _expect(object_name, f"{field}[{index}]", "non-empty string")


def _validate_discovery_hints(hints: object, object_name: str) -> None:
    if not isinstance(hints, dict):
        _expect(object_name, "discovery_hints", "object")
    _reject_unknown(
        hints,
        f"{object_name}.discovery_hints",
        {"concepts", "path_hints", "sources", "expected_evidence"},
    )
    for field in ("concepts", "path_hints", "expected_evidence"):
        if field in hints:
            _string_list(hints[field], f"{object_name}.discovery_hints", field)
    if "sources" not in hints:
        return
    sources = hints["sources"]
    if not isinstance(sources, list) or not sources:
        _expect(object_name, "discovery_hints.sources", "non-empty list of source objects")
    for index, item in enumerate(sources):
        where = f"{object_name}.discovery_hints.sources[{index}]"
        if not isinstance(item, dict):
            _expect(object_name, f"discovery_hints.sources[{index}]", "object with source")
        _reject_unknown(item, where, {"source", "args"})
        _nonempty_str(item, where, "source", required=True)
        if "args" in item and not isinstance(item["args"], dict):
            _expect(object_name, f"discovery_hints.sources[{index}].args", "object")


def _validate_references(refs: object, object_name: str) -> None:
    if not isinstance(refs, list) or not refs:
        _expect(object_name, "references", "non-empty list")
    numbers = []
    for index, ref in enumerate(refs):
        where = f"{object_name}.references[{index}]"
        if not isinstance(ref, dict):
            _expect(object_name, f"references[{index}]", "object")
        _reject_unknown(ref, where, {"nr", "locator", "law_text"})
        if not isinstance(ref.get("nr"), int):
            _expect(object_name, f"references[{index}].nr", "integer")
        _nonempty_str(ref, where, "locator", required=True)
        _nonempty_str(ref, where, "law_text", required=True)
        numbers.append(ref["nr"])
    if numbers != list(range(1, len(numbers) + 1)):
        _expect(object_name, "references[].nr", "1, 2, 3, … in array order")


def _validate_origin(origin: object, object_name: str) -> None:
    if not isinstance(origin, dict):
        _expect(object_name, "origin", "object")
    _reject_unknown(origin, f"{object_name}.origin", {"pack", "version"})
    _nonempty_str(origin, f"{object_name}.origin", "pack", required=True)
    _nonempty_str(origin, f"{object_name}.origin", "version", required=True)


def validate_requirement(obj: object, *, published: bool = False) -> dict:
    requirement = _require_dict(obj, "requirement")
    name = f"requirement {requirement.get('id', '?')}"
    forbidden = sorted(set(requirement) & FORBIDDEN_REQUIREMENT_FIELDS)
    if forbidden:
        _expect(name, forbidden[0], "absent on a requirement")
    _reject_unknown(requirement, name, REQUIREMENT_FIELDS)
    _nonempty_str(requirement, name, "id", required=True)
    _nonempty_str(requirement, name, "pack_id", required=True)
    if "source" not in requirement:
        _expect(name, "source", "legal instrument")
    _validate_source(requirement["source"], name, require_edition=published)
    if "references" not in requirement:
        _expect(name, "references", "non-empty list")
    _validate_references(requirement["references"], name)
    if "strength" in requirement and requirement["strength"] not in STRENGTHS:
        _expect(name, "strength", "MUST, SHOULD, or MAY")
    for field in ("responsible", "applicability", "exceptions", "scope", "remediation_hint", "note"):
        if field in requirement:
            _nonempty_str(requirement, name, field, required=True)
    if "discovery_hints" in requirement:
        _validate_discovery_hints(requirement["discovery_hints"], name)
    if "origin" in requirement:
        if published:
            _expect(name, "origin", "absent on the publisher's requirement")
        _validate_origin(requirement["origin"], name)
    _validate_signed_block(requirement, name, required=published)
    return requirement


def validate_pack(obj: object, *, sealed: bool = False) -> dict:
    pack = _require_dict(obj, "pack")
    name = f"pack {pack.get('id', '?')}"
    _reject_unknown(pack, name, PACK_FIELDS)
    _nonempty_str(pack, name, "id", required=True)
    _nonempty_str(pack, name, "version", required=True)
    for field in ("name", "assurance_class", "description", "jurisdiction"):
        if field in pack:
            _nonempty_str(pack, name, field, required=True)
    if "source" in pack:
        source = pack["source"]
        if not isinstance(source, dict):
            _expect(name, "source", "object")
        _reject_unknown(source, f"{name}.source", {"framework", "instrument", "url"})
        for field in source:
            _nonempty_str(source, f"{name}.source", field, required=True)
    _validate_signed_block(pack, name, required=sealed)
    return pack


def upgrade_stored_claim(document: object) -> dict | None:
    """Turn a retired `{check, args}` file into a Packs v2 claim.

    Returns None when the document is already the current shape. The current
    shape stays strict: `validate_claim` still rejects a top-level `check`.
    """
    if not isinstance(document, dict) or "checks" in document:
        return None
    check = document.get("check")
    if not isinstance(check, str) or not check.strip():
        return None
    check_args = document.get("args") if isinstance(document.get("args"), dict) else {}
    path = ""
    single = check_args.get("path")
    if isinstance(single, str) and single.strip():
        path = single.strip()
    else:
        paths = check_args.get("paths")
        if isinstance(paths, list) and paths and isinstance(paths[0], str) and paths[0].strip():
            path = paths[0].strip()
    claim_id = document.get("id")
    requirement_id = document.get("requirement_id")
    if not isinstance(claim_id, str) or not isinstance(requirement_id, str):
        return None
    source = document.get("source")
    if not isinstance(source, str) or not source.strip():
        source = "git" if check in {"fresh", "owned"} else "documents"
    description = document.get("description")
    if not isinstance(description, str) or not description.strip():
        description = path or check
    upgraded = {
        "id": claim_id,
        "requirement_id": requirement_id,
        "source": source,
        "args": {"path": path} if path else dict(check_args),
        "description": description,
        "checks": [{"check": check, "args": dict(check_args)}],
    }
    if isinstance(document.get("severity"), str) and document["severity"]:
        upgraded["severity"] = document["severity"]
    return validate_claim(upgraded)


def validate_claim(obj: object) -> dict:
    claim = _require_dict(obj, "claim")
    name = f"claim {claim.get('id', '?')}"
    forbidden = sorted(set(claim) & FORBIDDEN_CLAIM_FIELDS)
    if forbidden:
        _expect(name, forbidden[0], "absent on a claim")
    _reject_unknown(claim, name, CLAIM_FIELDS)
    _nonempty_str(claim, name, "id", required=True)
    _nonempty_str(claim, name, "requirement_id", required=True)
    _nonempty_str(claim, name, "source", required=True)
    _nonempty_str(claim, name, "description", required=True)
    if not isinstance(claim.get("args"), dict):
        _expect(name, "args", "object")
    checks = claim.get("checks")
    if not isinstance(checks, list):
        _expect(name, "checks", "a list of check entries")
    from checks.schema import validate_check_args

    for index, item in enumerate(checks):
        where = f"{name}.checks[{index}]"
        if not isinstance(item, dict):
            _expect(name, f"checks[{index}]", "object with check and args")
        _reject_unknown(item, where, {"check", "args"})
        _nonempty_str(item, where, "check", required=True)
        if not isinstance(item.get("args"), dict):
            _expect(name, f"checks[{index}].args", "object")
        validate_check_args(item["check"], item["args"])
    if "severity" in claim and claim["severity"] not in SEVERITIES:
        _expect(name, "severity", "high, medium, or critical")
    _validate_signed_block(claim, name, required=False)
    return claim


CURBPACK_CONFIG_FIELDS = {
    "packs",
    "exclude_requirements",
    "requirements",
    "search_hints",
    "packs_dir",
    "claims_dir",
    "results_dir",
    "reports_dir",
    "unsigned_requirements",
}

UNSIGNED_REQUIREMENTS_VALUES = {"reject", "signed_commit"}


def validate_curbpack_config(obj: object) -> dict:
    config = _require_dict(obj, "curbpack.json")
    _reject_unknown(config, "curbpack.json", CURBPACK_CONFIG_FIELDS)
    _string_list(config.get("packs"), "curbpack.json", "packs")
    if "exclude_requirements" in config and "requirements" in config:
        _expect("curbpack.json", "requirements", "absent when exclude_requirements is set")
    if "exclude_requirements" in config:
        _string_list(config["exclude_requirements"], "curbpack.json", "exclude_requirements")
    if "requirements" in config:
        _string_list(config["requirements"], "curbpack.json", "requirements")
    if "search_hints" not in config:
        _expect("curbpack.json", "search_hints", "object")
    _validate_search_hints(config["search_hints"])
    for field in ("packs_dir", "claims_dir", "results_dir", "reports_dir"):
        _relative_dir(config.get(field), field)
    if config.get("unsigned_requirements") not in UNSIGNED_REQUIREMENTS_VALUES:
        _expect("curbpack.json", "unsigned_requirements", '"reject" or "signed_commit"')
    return config


def _relative_dir(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _expect("curbpack.json", field, "a relative directory")
    if value.startswith(("/", "\\")) or ".." in value.split("/"):
        _expect("curbpack.json", field, "a relative directory")


def _validate_search_hints(hints: object) -> None:
    if not isinstance(hints, dict):
        _expect("curbpack.json", "search_hints", "object")
    _reject_unknown(hints, "curbpack.json.search_hints", {"sources", "exclude_path_globs", "prefer_path_globs"})
    if "sources" in hints:
        sources = hints["sources"]
        if not isinstance(sources, list):
            _expect("curbpack.json", "search_hints.sources", "list of source objects")
        for index, item in enumerate(sources):
            if not isinstance(item, dict):
                _expect("curbpack.json", f"search_hints.sources[{index}]", "object with source")
            _reject_unknown(item, f"curbpack.json.search_hints.sources[{index}]", {"source", "args"})
            _nonempty_str(item, f"curbpack.json.search_hints.sources[{index}]", "source", required=True)
            if "args" in item and not isinstance(item["args"], dict):
                _expect("curbpack.json", f"search_hints.sources[{index}].args", "object")
    for field in ("exclude_path_globs", "prefer_path_globs"):
        if field in hints:
            if not isinstance(hints[field], list):
                _expect("curbpack.json", f"search_hints.{field}", "list of strings")
            for index, item in enumerate(hints[field]):
                if not isinstance(item, str):
                    _expect("curbpack.json", f"search_hints.{field}[{index}]", "string")


def validate_run_result(obj: object) -> dict:
    result = _require_dict(obj, "run result")
    _reject_unknown(result, "run result", {"commit", "worktree", "packs", "tool", "tool_version", "claims"})
    has_commit = "commit" in result
    has_worktree = "worktree" in result
    if has_commit != has_worktree:
        _expect("run result", "worktree", "present together with commit, or both omitted")
    if has_commit:
        _nonempty_str(result, "run result", "commit", required=True)
        if result["worktree"] not in ("clean", "dirty"):
            _expect("run result", "worktree", "clean or dirty")
    _nonempty_str(result, "run result", "tool", required=True)
    _nonempty_str(result, "run result", "tool_version", required=True)
    packs = result.get("packs")
    if not isinstance(packs, list):
        _expect("run result", "packs", "list")
    for index, pack in enumerate(packs):
        if not isinstance(pack, dict):
            _expect("run result", f"packs[{index}]", "object")
        _reject_unknown(pack, f"run result.packs[{index}]", {"id", "version", "digest"})
        for field in ("id", "version", "digest"):
            _nonempty_str(pack, f"run result.packs[{index}]", field, required=True)
    rows = result.get("claims")
    if not isinstance(rows, list):
        _expect("run result", "claims", "list")
    for index, row in enumerate(rows):
        _validate_run_row(row, index)
    return result


def _validate_run_row(row: object, index: int) -> None:
    where = f"run result.claims[{index}]"
    if not isinstance(row, dict):
        _expect("run result", f"claims[{index}]", "object")
    _reject_unknown(row, where, {"id", "digest", "status", "checks"})
    for field in ("id", "digest", "status"):
        _nonempty_str(row, where, field, required=True)
    status = row.get("status")
    if status not in ("pass", "fail", "skipped"):
        _expect("run result", f"claims[{index}].status", "pass, fail, or skipped")
    checks = row.get("checks")
    if not isinstance(checks, list) or not checks:
        _expect("run result", f"claims[{index}].checks", "one result per configured check")
    for check_index, item in enumerate(checks):
        _validate_check_result(item, index, check_index)


def _validate_check_result(item: object, claim_index: int, check_index: int) -> None:
    where = f"run result.claims[{claim_index}].checks[{check_index}]"
    if not isinstance(item, dict):
        _expect("run result", f"claims[{claim_index}].checks[{check_index}]", "object")
    _reject_unknown(item, where, {"index", "check", "args", "status", "detail"})
    if item.get("index") != check_index:
        _expect("run result", f"claims[{claim_index}].checks[{check_index}].index", str(check_index))
    _nonempty_str(item, where, "check", required=True)
    if not isinstance(item.get("args"), dict):
        _expect("run result", f"claims[{claim_index}].checks[{check_index}].args", "object")
    status = item.get("status")
    if status not in ("pass", "fail", "skipped"):
        _expect("run result", f"claims[{claim_index}].checks[{check_index}].status", "pass, fail, or skipped")
    if status == "pass" and "detail" in item:
        _expect("run result", f"claims[{claim_index}].checks[{check_index}].detail", "absent when status is pass")
    if status in ("fail", "skipped") and (not isinstance(item.get("detail"), str) or not item["detail"].strip()):
        _expect("run result", f"claims[{claim_index}].checks[{check_index}].detail", "non-empty string")
