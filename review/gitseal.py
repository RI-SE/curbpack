"""Read a Git commit signature when a claim has no `signed` block.

The Git author string is not the signer. Only `git`'s verification status is.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from common.canonical import version_digest
from common.signing import read_signature


def git_commit_signature(repo: Path, relative: str) -> dict | None:
    """Five-fact reading of the latest commit that touches `relative`, or None when Git has no signature."""
    try:
        log = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%G?%n%GS%n%cI%n%H", "--", relative],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if log.returncode != 0 or not log.stdout.strip():
        return None
    lines = log.stdout.splitlines()
    if len(lines) < 4:
        return None
    status, signer, when, commit = lines[0], lines[1], lines[2], lines[3]
    if status == "N" or not signer.strip():
        return None
    verifiable = status == "G"
    reading = {
        "what": "Git commit",
        "who": signer.strip(),
        "when": when.strip(),
        "version": commit.strip(),
        "verifiable": verifiable,
    }
    if not verifiable:
        reading["reason"] = f"Git reports signature status {status}, which is not a good signature."
    return reading


def read_claim_signature(claim: dict, trust: dict[str, bytes], *, repo: Path | None = None, relative: str | None = None) -> dict:
    if isinstance(claim.get("signed"), dict):
        return read_signature(claim, trust, what="claim")
    if repo is not None and relative:
        git_reading = git_commit_signature(repo, relative)
        if git_reading is not None:
            return git_reading
    return {
        "what": "claim",
        "who": None,
        "when": None,
        "version": version_digest(claim),
        "verifiable": False,
        "reason": "No signed block and no signed Git commit. The object is unsigned.",
    }


def git_content_result(repo: Path, paths: list[str], *, tree_prefix: str | None = None) -> dict:
    """Local Git result for the current bytes of ``paths``. No network and no author name."""
    unsigned = {
        "status": "unsigned",
        "method": "none",
        "signer": None,
        "version": None,
        "reason": "No signed block and no signed Git commit. The object is unsigned.",
    }
    if not paths:
        return unsigned
    try:
        log = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%G?%n%GS%n%H", "--", *paths],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return unsigned
    if log.returncode != 0 or not log.stdout.strip():
        return unsigned
    lines = log.stdout.splitlines()
    if len(lines) < 3:
        return unsigned
    status, signer, commit = lines[0], lines[1].strip(), lines[2].strip()
    if status == "N" or not signer:
        if status == "N":
            return unsigned
        return {
            "status": "invalid",
            "method": "git",
            "signer": None,
            "version": commit,
            "reason": f"Git reports signature status {status}, which is not a good signature.",
        }
    if status != "G":
        return {
            "status": "invalid",
            "method": "git",
            "signer": signer,
            "version": commit,
            "reason": f"Git reports signature status {status}, which is not a good signature.",
        }
    if _git_content_differs(repo, commit, paths, tree_prefix):
        return {
            "status": "invalid",
            "method": "git",
            "signer": signer,
            "version": commit,
            "reason": "The current content differs from the signed commit.",
        }
    return {
        "status": "valid",
        "method": "git",
        "signer": signer,
        "version": commit,
        "reason": None,
    }


def _git_content_differs(repo: Path, commit: str, paths: list[str], tree_prefix: str | None) -> bool:
    import json

    from common.canonical import pack_json_bytes_for_digest

    if tree_prefix is not None:
        listed = subprocess.run(
            ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", commit, "--", tree_prefix],
            capture_output=True,
            text=True,
        )
        committed = {line for line in listed.stdout.splitlines() if line}
        if committed != set(paths):
            return True
    for rel in paths:
        blob = subprocess.run(
            ["git", "-C", str(repo), "show", f"{commit}:{rel}"],
            capture_output=True,
        )
        work = repo / rel
        if blob.returncode != 0 or not work.is_file():
            return True
        if rel == "pack.json" or rel.endswith("/pack.json"):
            try:
                committed_doc = json.loads(blob.stdout.decode("utf-8"))
                work_doc = json.loads(work.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return True
            if pack_json_bytes_for_digest(committed_doc) != pack_json_bytes_for_digest(work_doc):
                return True
        elif blob.stdout != work.read_bytes():
            return True
    return False
