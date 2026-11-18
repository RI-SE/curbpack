"""Compile a review report from the run that actually happened, then record a human decision."""

from __future__ import annotations

import copy
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json
from common.signing import read_signature, sign_object
from review.gitseal import git_commit_signature
from studio.compile.impl import compile_report, validate_report, write_report
from studio.compile.impl.report import signature_appendix

NOT_A_LEGAL_CONCLUSION = "A passing check does not mean the legal requirement is fulfilled."
NO_CRA_FIELD = "This report has no field for a conclusion that the product meets CRA."


def durable_report_path(repo: Path) -> Path:
    """Conventional product-repo report. Not a configuration setting."""
    return Path(repo) / "docs" / "reports" / "review-report.json"


def worktree_sentence(run_result: dict) -> str:
    """Page copy. It is not stored on the report."""
    if not isinstance(run_result, dict):
        return ""
    if run_result.get("worktree") == "dirty":
        return "This result is not verification of that commit's content."
    if run_result.get("worktree") == "clean":
        return "The worktree was clean."
    return ""


def load_report(path: Path) -> dict:
    return validate_report(read_json(path))


def same_run(report: dict, run_result: dict) -> bool:
    if not isinstance(report, dict) or not isinstance(run_result, dict):
        return False
    return report.get("run_result") == run_result


def replace_saved_report(path: Path, report: dict, *, confirm: bool) -> None:
    """Write an unsigned report. An existing file is replaced only after confirmation."""
    if path.is_file() and not confirm:
        raise ModelError("review report", "confirm", "confirmation before replacing the saved report")
    write_report(path, report)


def save_report_decision(path: Path, text: str) -> dict:
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; compile writes the file")
    decided = record_decision(load_report(path), text)
    write_report(path, decided)
    return decided


def save_report_signature(path: Path, *, name: str, private_key: bytes, at: str) -> dict:
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; compile writes the file")
    current = load_report(path)
    sealed = sign_report(current, name=name, private_key=private_key, at=at)
    write_report(path, sealed)
    return sealed


def unchecked_requirement_ids(selected_ids: list[str], report: dict) -> list[str]:
    checked = {
        claim.get("requirement_id")
        for claim in (report.get("claims") or [])
        if isinstance(claim, dict) and isinstance(claim.get("requirement_id"), str)
    }
    return [requirement_id for requirement_id in selected_ids if requirement_id not in checked]


def record_decision(report: dict, text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ModelError("review report", "decision", "the reviewer's own words")
    out = copy.deepcopy(report)
    out.pop("signed", None)
    out["decision"] = text.strip()
    return out


def sign_report(report: dict, *, name: str, private_key: bytes, at: str) -> dict:
    if not isinstance(report.get("decision"), str) or not report["decision"].strip():
        raise ModelError("review report", "decision", "words recorded before review-sign")
    if "run_result" not in report:
        raise ModelError("review report", "run_result", "the run result that was reviewed")
    return sign_object(report, name=name, private_key=private_key, at=at)


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
