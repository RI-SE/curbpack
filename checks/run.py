"""Run the registered Check command and write the one Packs v2 run result."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from checks.dispatch import run_check_tool
from checks.schema import registry_entry, validate_check_args
from common.canonical import pack_directory_digest, version_digest
from common.errors import CheckError, ModelError
from common.jsonio import read_json
from common.store import load_claims, load_pack_directory, save_run_result
from common.validate import validate_curbpack_config, validate_run_result
from common.version import TOOL, TOOL_VERSION

# These point Git at a different repository or pathspec dialect than the repo argument.
_GIT_ENV_DROP = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_GLOB_PATHSPECS",
        "GIT_NOGLOB_PATHSPECS",
    }
)


def _git_child_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in _GIT_ENV_DROP}
    env["GIT_LITERAL_PATHSPECS"] = "1"
    return env


def git_snapshot(repo: Path) -> dict | None:
    """HEAD and clean/dirty when this directory is a Git checkout with a commit."""
    head = _git_run(repo, "rev-parse", "HEAD")
    if head is None or head.returncode != 0:
        return None
    status = _git_run(repo, "status", "--porcelain")
    if status is None or status.returncode != 0:
        return None
    worktree = "dirty" if status.stdout.strip() else "clean"
    return {"commit": head.stdout.strip(), "worktree": worktree}


def new_run_result_path(folder: Path) -> Path:
    """`<folder>/run-result_<YYYYMMDDTHHMMSSZ>.json`, never an existing file."""
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = folder / f"run-result_{stamp}.json"
        if not path.exists():
            return path
        time.sleep(1)


def process_exit_code(result: dict) -> int:
    """0 only when at least one Check ran and every Claim and Check passed."""
    rows = result.get("claims") or []
    executed = 0
    for row in rows:
        if row.get("status") != "pass":
            return 1
        for item in row.get("checks") or []:
            if item.get("status") != "pass":
                return 1
            executed += 1
    if executed < 1:
        return 1
    return 0


def _git_run(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), "-c", "i18n.logOutputEncoding=utf-8", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=_git_child_env(),
            input=input_text,
        )
    except FileNotFoundError:
        return None


def _execute_check(repo: Path, check: str, args: dict) -> dict:
    try:
        validate_check_args(check, args)
    except (CheckError, ModelError) as exc:
        return {"status": "fail", "detail": str(exc)}
    entry = registry_entry(check)
    command = entry.get("command") if isinstance(entry, dict) else None
    if not isinstance(command, str) or not command.strip():
        return {"status": "fail", "detail": f"check {check!r} has no registered command"}
    return run_check_tool(repo, command, check, args)


def _check_row(index: int, item: dict, outcome: dict) -> dict:
    row = {
        "index": index,
        "check": item["check"],
        "args": copy.deepcopy(item["args"]),
        "status": outcome["status"],
    }
    if outcome["status"] != "pass":
        row["detail"] = outcome["detail"]
    return row


def _aggregate(checks: list[dict]) -> str:
    statuses = [item["status"] for item in checks]
    if "fail" in statuses:
        return "fail"
    if "skipped" in statuses:
        return "skipped"
    return "pass"


def run_claim(repo: Path, claim: dict) -> dict:
    configured = claim.get("checks") or []
    if not configured:
        raise ModelError(f"claim {claim.get('id', '?')}", "checks", "one or more checks to execute")
    results = []
    for index, item in enumerate(configured):
        outcome = _execute_check(repo, item["check"], item["args"])
        results.append(_check_row(index, item, outcome))
    return {
        "id": claim["id"],
        "digest": version_digest(claim),
        "status": _aggregate(results),
        "checks": results,
    }


def build_run_result(repo: Path, claims: list[dict], packs: list[dict], *, skip: dict[str, str] | None = None) -> dict:
    skip = skip or {}
    rows = []
    for claim in claims:
        if not claim.get("checks"):
            continue
        reason = skip.get(claim["id"])
        if reason is not None:
            if not str(reason).strip():
                raise ModelError(f"claim {claim['id']}", "detail", "a reason for skipped")
            detail = str(reason).strip()
            results = [
                _check_row(index, item, {"status": "skipped", "detail": detail})
                for index, item in enumerate(claim["checks"])
            ]
            rows.append(
                {
                    "id": claim["id"],
                    "digest": version_digest(claim),
                    "status": "skipped",
                    "checks": results,
                }
            )
            continue
        rows.append(run_claim(repo, claim))
    result = {
        "packs": packs,
        "tool": TOOL,
        "tool_version": TOOL_VERSION,
        "claims": rows,
    }
    git = git_snapshot(repo)
    if git is not None:
        result["commit"] = git["commit"]
        result["worktree"] = git["worktree"]
    return validate_run_result(result)


def _loaded_config(repo: Path, config: dict | None) -> dict:
    if config is None:
        return validate_curbpack_config(read_json(repo / "curbpack.json"))
    return config


def packs_dir(repo: Path, config: dict | None = None) -> Path:
    return repo / _loaded_config(repo, config)["packs_dir"]


def claims_dir(repo: Path, config: dict | None = None) -> Path:
    return repo / _loaded_config(repo, config)["claims_dir"]


def results_dir(repo: Path, config: dict | None = None) -> Path:
    return repo / _loaded_config(repo, config)["results_dir"]


def reports_dir(repo: Path, config: dict | None = None) -> Path:
    return repo / _loaded_config(repo, config)["reports_dir"]


def curbpack_directory(repo: Path, config: dict | None = None) -> Path:
    """Old Studio/CLI layout root. New I/O uses packs_dir/claims_dir/results_dir/reports_dir."""
    if config is None:
        config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    return repo / (config.get("curbpack") or "curbpack")


def claim_catalog(repo: Path, directory: Path) -> Path:
    """`<directory>/claims` when that catalog exists. Otherwise `<repo>/claims`."""
    catalog = directory / "claims"
    if catalog.is_dir() or not (repo / "claims").is_dir():
        return catalog
    return repo / "claims"


def _pack_version_dir(packs_root: Path, pack_id: str) -> Path:
    root = packs_root / pack_id
    found = sorted(path.parent for path in root.glob("*/pack.json") if path.is_file())
    if not found:
        raise ModelError("curbpack.json", "packs", f"a pack version directory under {root}")
    if len(found) > 1:
        raise ModelError(
            "curbpack.json",
            "packs",
            f"exactly one pack version directory under {root}, not {len(found)}",
        )
    return found[0]


def selected_requirement_ids(loaded: list[tuple[dict, list[dict]]], config: dict) -> set[str]:
    present = {requirement["id"] for _pack, requirements in loaded for requirement in requirements}
    if "requirements" in config:
        unknown = sorted(set(config["requirements"]) - present)
        if unknown:
            raise ModelError("curbpack.json", "requirements", f"ids present in the selected packs, not {unknown[0]}")
        return set(config["requirements"])
    excluded = set(config.get("exclude_requirements") or [])
    return present - excluded


def run_repository(
    repo: Path,
    packs_root: Path | None = None,
    *,
    skip: dict[str, str] | None = None,
    pack_ids: list[str] | None = None,
    requirement_ids: list[str] | None = None,
) -> tuple[dict, int]:
    config = dict(validate_curbpack_config(read_json(repo / "curbpack.json")))
    if pack_ids is not None:
        config["packs"] = pack_ids
    if requirement_ids is not None:
        config.pop("exclude_requirements", None)
        config["requirements"] = requirement_ids
    if packs_root is None:
        packs_root = packs_dir(repo, config)
    loaded = []
    pack_rows = []
    for pack_id in config["packs"]:
        pack_dir = _pack_version_dir(packs_root, pack_id)
        pack, requirements = load_pack_directory(pack_dir)
        loaded.append((pack, requirements))
        pack_rows.append(
            {"id": pack["id"], "version": pack["version"], "digest": pack_directory_digest(pack_dir)}
        )
    selected = selected_requirement_ids(loaded, config)
    claims = [
        claim
        for claim in load_claims(claims_dir(repo, config))
        if claim["requirement_id"] in selected
    ]
    result = build_run_result(repo, claims, pack_rows, skip=skip)
    return result, process_exit_code(result)


def run_pack_directories(
    repo: Path, directories: list[Path], *, skip: dict[str, str] | None = None
) -> tuple[dict, int]:
    """Run Claims in a repo against these Pack directories."""
    loaded = []
    pack_rows = []
    for directory in directories:
        pack, requirements = load_pack_directory(directory)
        loaded.append((pack, requirements))
        pack_rows.append(
            {"id": pack["id"], "version": pack["version"], "digest": pack_directory_digest(directory)}
        )
    selected = selected_requirement_ids(loaded, {"packs": [row["id"] for row in pack_rows]})
    claims = load_claims(repo / "claims")
    for claim in claims:
        if claim["requirement_id"] not in selected:
            raise ModelError(
                f"claim {claim['id']}",
                "requirement_id",
                "a requirement selected in curbpack.json",
            )
    result = build_run_result(repo, claims, pack_rows, skip=skip)
    return result, process_exit_code(result)


def run_and_write(
    repo: Path,
    packs_root: Path | None,
    out: Path,
    *,
    skip: dict[str, str] | None = None,
    pack_ids: list[str] | None = None,
    requirement_ids: list[str] | None = None,
) -> tuple[dict, int]:
    result, code = run_repository(
        repo, packs_root, skip=skip, pack_ids=pack_ids, requirement_ids=requirement_ids
    )
    save_run_result(out, result)
    return result, code
