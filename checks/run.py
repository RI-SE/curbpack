"""Run exist and contents. Write the one Packs v2 run result."""

from __future__ import annotations

import copy
import json
import math
import os
import re
import stat
import subprocess
from pathlib import Path

from checks.schema import parse_rfc3339, validate_check_args
from common.canonical import pack_directory_digest, version_digest
from common.errors import CheckError, ModelError
from common.jsonio import read_json
from common.store import load_claims, load_pack_directory, save_run_result
from common.validate import validate_curbpack_config, validate_run_result
from common.version import TOOL, TOOL_VERSION

# A contents/placeholder probe fails when one of these is present.
# This is the PoC list, not a claim that it matches every curbcheck build.
_PLACEHOLDERS = (
    re.compile(r"(?i)\blorem ipsum\b"),
    re.compile(r"(?i)\bTODO\b"),
    re.compile(r"(?i)\bTBD\b"),
    re.compile(r"(?i)\bFIXME\b"),
    re.compile(r"(?i)\bplaceholder\b"),
    re.compile(r"(?i)<placeholder>"),
)


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


def _inside(repo: Path, relative: str) -> Path:
    root = repo.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise ModelError("check", "args.path", "a path inside the repository")
    return path


def _targets(args: dict) -> list[str]:
    if "paths" in args:
        return list(args["paths"])
    return [args["path"]]


def run_exist(repo: Path, args: dict) -> dict:
    missing = [rel for rel in _targets(args) if not _inside(repo, rel).is_file()]
    if missing:
        return {"status": "fail", "detail": "; ".join(f"{rel} is absent" for rel in missing)}
    return {"status": "pass"}


def _compare(actual: int, op: str, expected: int) -> bool:
    if op == ">":
        return actual > expected
    if op == ">=":
        return actual >= expected
    if op == "<":
        return actual < expected
    if op == "<=":
        return actual <= expected
    raise ModelError("contents", "op", "> >= < or <=")


def repo_tokens(repo: Path) -> list[str]:
    tokens = [repo.resolve().name]
    package = repo / "package.json"
    if package.is_file():
        try:
            name = json.loads(package.read_text(encoding="utf-8")).get("name")
        except json.JSONDecodeError:
            name = None
        if isinstance(name, str) and name.strip():
            tokens.append(name.strip())
    gomod = repo / "go.mod"
    if gomod.is_file():
        for line in gomod.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("module "):
                module = line.split(None, 1)[1].strip()
                if module:
                    tokens.append(module)
                break
    unique = []
    for token in tokens:
        if token not in unique:
            unique.append(token)
    return unique


def _probe_failure(repo: Path, path: Path, relative: str, probe: dict) -> str | None:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    kind = probe["kind"]
    if kind == "size":
        if not _compare(len(data), probe["op"], probe["bytes"]):
            return f"{relative} is {len(data)} bytes, not {probe['op']} {probe['bytes']}"
        return None
    if kind == "words":
        count = len(text.split())
        if not _compare(count, probe["op"], probe["n"]):
            return f"{relative} has {count} words, not {probe['op']} {probe['n']}"
        return None
    if kind == "headers":
        missing = [header for header in probe["headers"] if header not in text]
        if missing:
            return f"{relative} is missing header {missing[0]!r}"
        return None
    if kind == "token":
        tokens = repo_tokens(repo)
        if not any(token and token in text for token in tokens):
            return f"{relative} does not contain the repo token ({', '.join(tokens)})"
        return None
    if kind == "pattern":
        try:
            found = re.search(probe["pattern"], text) is not None
        except re.error as exc:
            raise ModelError("contents", "probes.pattern", f"a valid regular expression ({exc})") from exc
        if found:
            return f"{relative} matches forbidden pattern {probe['pattern']!r}"
        return None
    if kind == "placeholder":
        for compiled in _PLACEHOLDERS:
            match = compiled.search(text)
            if match:
                return f"{relative} contains placeholder text {match.group(0)!r}"
        return None
    raise CheckError(f"unknown probe kind {kind!r}")


def run_contents(repo: Path, args: dict) -> dict:
    missing = [rel for rel in _targets(args) if not _inside(repo, rel).is_file()]
    if missing:
        return {"status": "fail", "detail": "; ".join(f"{rel} is absent" for rel in missing)}
    failures = []
    for rel in _targets(args):
        path = _inside(repo, rel)
        for probe in args["probes"]:
            failure = _probe_failure(repo, path, rel, probe)
            if failure:
                failures.append(failure)
    if failures:
        return {"status": "fail", "detail": "; ".join(failures)}
    return {"status": "pass"}


def _git_run(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            env=_git_child_env(),
            input=input_text,
        )
    except FileNotFoundError:
        return None


def _entry_path(repo: Path, relative: str) -> Path:
    """Worktree path without resolving a final symlink."""
    root = repo.resolve()
    path = root / relative
    parent = path.parent.resolve()
    if parent != root and root not in parent.parents:
        raise ModelError("check", "args.path", "a path inside the repository")
    return path


def _head_mode_and_blob(repo: Path, relative: str) -> tuple[str, str] | None:
    """Mode and blob at HEAD. None if Git failed. Empty strings when the path is absent."""
    head = _git_run(repo, "ls-tree", "HEAD", "--", relative)
    if head is None or head.returncode != 0:
        return None
    parts = head.stdout.split()
    if len(parts) < 3:
        return "", ""
    return parts[0], parts[2]


def _worktree_blob(repo: Path, relative: str) -> str | None:
    """Blob id Git would record for the worktree entry. None if Git failed."""
    path = _entry_path(repo, relative)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return ""
    if stat.S_ISLNK(info.st_mode):
        hashed = _git_run(repo, "hash-object", "--stdin", input_text=os.readlink(path))
    elif stat.S_ISREG(info.st_mode):
        hashed = _git_run(repo, "hash-object", "--", relative)
    else:
        return ""
    if hashed is None or hashed.returncode != 0:
        return None
    return hashed.stdout.strip()


def _worktree_differs_from_head(repo: Path, relative: str) -> bool | None:
    """True when the worktree entry is not the blob at HEAD. None if Git failed."""
    head = _head_mode_and_blob(repo, relative)
    blob = _worktree_blob(repo, relative)
    if head is None or blob is None:
        return None
    mode, head_blob = head
    if not head_blob or not blob:
        return True
    path = _entry_path(repo, relative)
    if stat.S_ISLNK(path.lstat().st_mode):
        return mode != "120000" or blob != head_blob
    if mode == "120000" or blob != head_blob:
        return True
    if not _filemode_tracked(repo):
        return False
    recorded = "100755" if path.lstat().st_mode & 0o111 else "100644"
    return recorded != mode


def _filemode_tracked(repo: Path) -> bool:
    probed = _git_run(repo, "config", "--get", "core.filemode")
    if probed is None or probed.returncode != 0:
        return True
    return probed.stdout.strip().lower() != "false"


def _last_change(repo: Path, relative: str) -> tuple[str, str] | None:
    """Commit id and committer instant for the last commit that changes the path."""
    log = _git_run(repo, "log", "-1", "--format=%H%n%cI", "HEAD", "--", relative)
    if log is None or log.returncode != 0:
        return None
    lines = [line.strip() for line in log.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    return lines[0], lines[1]


def _fail_with_commit(repo: Path, relative: str, cause: str) -> dict:
    found = _last_change(repo, relative)
    if found is None:
        return {"status": "fail", "detail": cause}
    return {"status": "fail", "detail": f"{cause}; commit {found[0]}"}


def run_git_fresh(repo: Path, args: dict) -> dict:
    """Age of the last commit that changed path, measured from args.as_of."""
    relative = args["path"]
    probe = _git_run(repo, "rev-parse", "--is-inside-work-tree")
    if probe is None:
        return {"status": "fail", "detail": "git is unavailable"}
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return {"status": "fail", "detail": f"{relative} has no Git metadata"}
    try:
        entry = _entry_path(repo, relative)
        try:
            info = entry.lstat()
        except FileNotFoundError:
            return _fail_with_commit(repo, relative, f"{relative} is absent")
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
            return _fail_with_commit(repo, relative, f"{relative} is absent")
        listed = _git_run(repo, "ls-files", "--", relative)
        if listed is None:
            return {"status": "fail", "detail": "git is unavailable"}
        if listed.returncode != 0:
            return {"status": "fail", "detail": f"{relative} has no Git metadata"}
        if not listed.stdout.strip():
            return {"status": "fail", "detail": f"{relative} is untracked"}
        differs = _worktree_differs_from_head(repo, relative)
        if differs is None:
            return {"status": "fail", "detail": "git is unavailable"}
        if differs:
            return _fail_with_commit(repo, relative, f"{relative} differs from HEAD")
        found = _last_change(repo, relative)
        if found is None:
            return {"status": "fail", "detail": f"{relative} has no commit"}
        commit, stamp = found
        try:
            committer = parse_rfc3339(stamp)
            as_of = parse_rfc3339(args["as_of"])
        except ModelError as exc:
            return {"status": "fail", "detail": str(exc)}
        if committer > as_of:
            return {"status": "fail", "detail": f"{relative} commit {commit} is after as_of"}
        age = math.floor((as_of - committer).total_seconds() / 86400)
        if age <= args["max_age_days"]:
            return {"status": "pass"}
        return {
            "status": "fail",
            "detail": f"{relative} commit {commit} is {age} days old, max {args['max_age_days']}",
        }
    except ModelError as exc:
        return {"status": "fail", "detail": str(exc)}


def _execute_check(repo: Path, check: str, args: dict) -> dict:
    try:
        validate_check_args(check, args)
    except (CheckError, ModelError) as exc:
        return {"status": "fail", "detail": str(exc)}
    if check == "exist":
        return run_exist(repo, args)
    if check == "contents":
        return run_contents(repo, args)
    if check == "git_fresh":
        return run_git_fresh(repo, args)
    return {"status": "fail", "detail": f"check {check!r} is not implemented"}


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


def selected_requirement_ids(loaded: list[tuple[dict, list[dict]]], config: dict) -> set[str]:
    present = {requirement["id"] for _pack, requirements in loaded for requirement in requirements}
    if "requirements" in config:
        unknown = sorted(set(config["requirements"]) - present)
        if unknown:
            raise ModelError("curbpack.json", "requirements", f"ids present in the selected packs, not {unknown[0]}")
        return set(config["requirements"])
    excluded = set(config.get("exclude_requirements") or [])
    return present - excluded


def run_repository(repo: Path, packs_root: Path, *, skip: dict[str, str] | None = None) -> tuple[dict, int]:
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    loaded = []
    pack_rows = []
    for pack_id in config["packs"]:
        pack_dir = packs_root / pack_id
        if not (pack_dir / "pack.json").is_file():
            raise ModelError("curbpack.json", "packs", f"a pack directory at {pack_dir}")
        pack, requirements = load_pack_directory(pack_dir)
        loaded.append((pack, requirements))
        pack_rows.append(
            {"id": pack["id"], "version": pack["version"], "digest": pack_directory_digest(pack_dir)}
        )
    selected = selected_requirement_ids(loaded, config)
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


def run_and_write(repo: Path, packs_root: Path, out: Path, *, skip: dict[str, str] | None = None) -> tuple[dict, int]:
    result, code = run_repository(repo, packs_root, skip=skip)
    save_run_result(out, result)
    return result, code
