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
