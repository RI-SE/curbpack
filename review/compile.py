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
from studio.common.presentation import NO_CRA_FIELD, NOT_A_LEGAL_CONCLUSION, worktree_sentence
from studio.review.impl.present import same_run, unchecked_requirement_ids


def durable_report_path(repo: Path) -> Path:
    """Conventional product-repo report. Not a configuration setting."""
    return Path(repo) / "docs" / "reports" / "review-report.json"
