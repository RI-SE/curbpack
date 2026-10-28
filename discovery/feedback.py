"""Researcher marks for one repository, source, and working copy.

This file is operational state. It is not a Claim, a Requirement, or a signature.
"""

from __future__ import annotations

from pathlib import Path

from checks.schema import validate_check_args
from common.errors import ModelError
from common.jsonio import read_json, write_json
from discovery.search import read_source_text


def feedback_path(workspace: Path, repo_id: str, source_id: str, timestamp: str) -> Path:
    for label, value in (("repo_id", repo_id), ("source_id", source_id), ("timestamp", timestamp)):
        if not value or Path(value).name != value or value in {".", ".."}:
            raise ModelError("feedback", label, "a single file name")
    return workspace / "discover-feedback" / f"{repo_id}__{source_id}__{timestamp}.json"


def load_feedback(workspace: Path, repo_id: str, source_id: str, timestamp: str) -> dict:
    path = feedback_path(workspace, repo_id, source_id, timestamp)
    if not path.is_file():
        return _empty(repo_id, source_id, timestamp)
    document = read_json(path)
    if not isinstance(document, dict):
        return _empty(repo_id, source_id, timestamp)
    document.setdefault("requirements", {})
    return document


def save_vote(
    workspace: Path,
    *,
    repo_id: str,
    source_id: str,
    timestamp: str,
    requirement_id: str,
    path: str,
    vote: str,
    known_ids: list[str],
) -> dict:
    if vote not in {"useful", "poor"}:
        raise ModelError("feedback", "vote", "useful or poor")
    document = _checked(workspace, repo_id, source_id, timestamp, requirement_id, path, known_ids)
    entry = _entry(document, requirement_id, path)
    entry["vote"] = vote
    _write(workspace, repo_id, source_id, timestamp, document)
    return document


def save_check(
    workspace: Path,
    *,
    repo_id: str,
    source_id: str,
    timestamp: str,
    requirement_id: str,
    path: str,
    check: str,
    args: dict,
    known_ids: list[str],
    label: str = "",
) -> dict:
    """Add one validated check. An invalid check leaves the file unchanged."""
    validate_check_args(check, args)
    document = _checked(workspace, repo_id, source_id, timestamp, requirement_id, path, known_ids)
    entry = _entry(document, requirement_id, path)
    checks = [item for item in entry.get("checks") or [] if isinstance(item, dict)]
    proposed = {"check": check, "args": args}
    if label:
        proposed["label"] = label
    if not any(item.get("check") == check and item.get("args") == args for item in checks):
        checks.append(proposed)
    entry["checks"] = checks
    _write(workspace, repo_id, source_id, timestamp, document)
    return document


def dismiss_why(
    workspace: Path,
    *,
    repo_id: str,
    source_id: str,
    timestamp: str,
    requirement_id: str,
    path: str,
    why: str,
    known_ids: list[str],
) -> dict:
    """Remember that this discovery sentence was declined. The claim is untouched."""
    document = _checked(workspace, repo_id, source_id, timestamp, requirement_id, path, known_ids)
    entry = _entry(document, requirement_id, path)
    entry["dismissed_why"] = why.strip()
    _write(workspace, repo_id, source_id, timestamp, document)
    return document


def add_finding(
    workspace: Path,
    *,
    repo: Path,
    repo_id: str,
    source_id: str,
    timestamp: str,
    requirement_id: str,
    path: str,
    rationale: str,
    known_ids: list[str],
) -> dict:
    """Insert a finding for a repository file. A check is not required."""
    text = rationale.strip() or "Added by hand."
    read_source_text(repo, path)
    document = _checked(workspace, repo_id, source_id, timestamp, requirement_id, path, known_ids)
    entry = _entry(document, requirement_id, path)
    entry["added"] = True
    entry["human_why"] = text
    _write(workspace, repo_id, source_id, timestamp, document)
    return document


def _empty(repo_id: str, source_id: str, timestamp: str) -> dict:
    return {
        "repo_id": repo_id,
        "source_id": source_id,
        "timestamp": timestamp,
        "requirements": {},
    }


def _checked(workspace, repo_id, source_id, timestamp, requirement_id, path, known_ids) -> dict:
    if requirement_id not in known_ids:
        raise ModelError(
            "feedback",
            "requirement_id",
            f"an id in the working copy, not {requirement_id}",
        )
    if not isinstance(path, str) or not path.strip():
        raise ModelError("feedback", "path", "a repo-relative path")
    return load_feedback(workspace, repo_id, source_id, timestamp)


def _entry(document: dict, requirement_id: str, path: str) -> dict:
    requirements = document.setdefault("requirements", {})
    bucket = requirements.setdefault(requirement_id, {})
    if not isinstance(bucket, dict):
        bucket = {}
        requirements[requirement_id] = bucket
    entry = bucket.get(path)
    if not isinstance(entry, dict):
        entry = {}
        bucket[path] = entry
    return entry


def _write(workspace: Path, repo_id: str, source_id: str, timestamp: str, document: dict) -> None:
    path = feedback_path(workspace, repo_id, source_id, timestamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, document)
