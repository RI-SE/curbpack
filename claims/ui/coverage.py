"""Presentation-only coverage mark. Does not search, filter, or write Claims."""

from __future__ import annotations

from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.store import load_run_result

COVERED_LABEL = "Already covered — passed in the selected Check run"
NO_REPLACEMENT = "No replacement Claim is saved. Retire only removes this Claim."
REPLACEMENT_UNCHECKED = "The replacement has not passed Checks yet."


def load_run(repo: Path) -> dict | None:
    config_path = repo / "curbpack.json"
    if not config_path.is_file():
        return None
    try:
        from checks.run import results_dir
        from common.jsonio import read_json
        from common.validate import validate_curbpack_config

        folder = results_dir(repo, validate_curbpack_config(read_json(config_path)))
    except (ModelError, OSError, ValueError):
        return None
    dated = sorted(folder.glob("run-result_*.json"))
    if not dated:
        return None
    try:
        return load_run_result(dated[-1])
    except (ModelError, OSError, ValueError):
        return None


def covered_paths(claims: list, run_result: dict | None, requirement_id: str) -> set[str]:
    """Repo-relative paths whose matching Claims all passed in this run."""
    verdicts: dict[str, bool] = {}
    for claim in claims:
        if not isinstance(claim, dict) or claim.get("requirement_id") != requirement_id:
            continue
        path = _source_path(claim.get("args"))
        if path is None:
            continue
        passed = claim_passed(claim, run_result)
        if path in verdicts and verdicts[path] != passed:
            verdicts[path] = False
        else:
            verdicts[path] = passed
    return {path for path, passed in verdicts.items() if passed}


def claim_passed(claim: dict, run_result: dict | None) -> bool:
    """True when this Claim's digest matches a run row and every Check passed its own evidence."""
    if not isinstance(claim, dict) or not isinstance(run_result, dict):
        return False
    path = _source_path(claim.get("args"))
    if path is None:
        return False
    row = _row(run_result, claim.get("id"))
    if row is None or row.get("digest") != version_digest(claim) or row.get("status") != "pass":
        return False
    configured = claim.get("checks") or []
    ran = row.get("checks") or []
    if not configured or len(configured) != len(ran):
        return False
    for item in ran:
        if not isinstance(item, dict) or item.get("status") != "pass":
            return False
        if not _checks_this_evidence(item.get("args"), path):
            return False
    return True


def retire_warning(claim: dict, claims: list, run_result: dict | None) -> str:
    """Warn before Retire when a replacement for this Requirement has not passed Checks."""
    requirement_id = claim.get("requirement_id")
    claim_id = claim.get("id")
    others = [
        item
        for item in claims
        if isinstance(item, dict)
        and item.get("id") != claim_id
        and item.get("requirement_id") == requirement_id
    ]
    if not others:
        return NO_REPLACEMENT
    if any(claim_passed(item, run_result) for item in others):
        return ""
    return REPLACEMENT_UNCHECKED


def _row(run_result: dict, claim_id: object) -> dict | None:
    if not isinstance(claim_id, str):
        return None
    for row in run_result.get("claims") or []:
        if isinstance(row, dict) and row.get("id") == claim_id:
            return row
    return None


def _source_path(args: object) -> str | None:
    if not isinstance(args, dict):
        return None
    path = args.get("path")
    if not isinstance(path, str) or not path.strip():
        return None
    path = path.strip()
    if not _repo_relative(path):
        return None
    listed = args.get("paths")
    if isinstance(listed, list) and listed:
        extras = [item.strip() for item in listed if isinstance(item, str) and item.strip()]
        if extras != [path]:
            return None
    return path


def _checks_this_evidence(args: object, source_path: str) -> bool:
    if not isinstance(args, dict):
        return True
    named = []
    single = args.get("path")
    if isinstance(single, str) and single.strip():
        named.append(single.strip())
    listed = args.get("paths")
    if isinstance(listed, list):
        named.extend(item.strip() for item in listed if isinstance(item, str) and item.strip())
    return all(item == source_path for item in named)


def _repo_relative(path: str) -> bool:
    if path.startswith(("/", "\\")):
        return False
    return ".." not in path.replace("\\", "/").split("/")
