"""Compile a review report from the run that actually happened, then record a human decision."""

from __future__ import annotations

from pathlib import Path

from studio.compile.impl import (
    compile_report,
    load_report,
    replace_saved_report,
    validate_report,
    write_report,
)
from studio.compile.impl.report import signature_appendix
from studio.review.impl import (
    read_report_signature,
    record_decision,
    save_report_decision,
    save_report_signature,
    sign_report,
)

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
