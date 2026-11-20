"""Record a human decision and sign the saved review report."""

from __future__ import annotations

import copy
from pathlib import Path

from common.errors import ModelError
from common.signing import read_signature, sign_object
from review.gitseal import git_commit_signature
from studio.compile.impl import load_report, write_report


def save_report_decision(path: Path, text: str) -> dict:
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; create a report first")
    decided = record_decision(load_report(path), text)
    write_report(path, decided)
    return decided


def save_report_signature(path: Path, *, name: str, private_key: bytes, at: str) -> dict:
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; create a report first")
    current = load_report(path)
    sealed = sign_report(current, name=name, private_key=private_key, at=at)
    write_report(path, sealed)
    return sealed


def record_decision(report: dict, text: str) -> dict:
    _reject_if_signed(report)
    if not isinstance(text, str) or not text.strip():
        raise ModelError("review report", "decision", "the reviewer's own words")
    out = copy.deepcopy(report)
    out.pop("signed", None)
    out["decision"] = text.strip()
    return out


def sign_report(report: dict, *, name: str, private_key: bytes, at: str) -> dict:
    _reject_if_signed(report)
    if not isinstance(report.get("decision"), str) or not report["decision"].strip():
        raise ModelError("review report", "decision", "words recorded before review-sign")
    if "run_result" not in report:
        raise ModelError("review report", "run_result", "the run result that was reviewed")
    return sign_object(report, name=name, private_key=private_key, at=at)


def _reject_if_signed(report: dict) -> None:
    """A review-sign locks that file. A later decision is a new compiled report."""
    if isinstance(report, dict) and isinstance(report.get("signed"), dict):
        raise ModelError(
            "review report",
            "signed",
            "a new report; this signed report is unchanged",
        )


def read_report_signature(
    report: dict,
    trust: dict[str, bytes],
    *,
    repo: Path | None = None,
    relative: str | None = None,
) -> dict:
    if isinstance(report.get("signed"), dict):
        return read_signature(report, trust, what="review report")
    if repo is not None and relative:
        git_reading = git_commit_signature(repo, relative)
        if git_reading is not None:
            return git_reading
    return read_signature(report, trust, what="review report")
