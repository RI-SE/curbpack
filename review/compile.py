"""Compile a review report from the run that actually happened, then record a human decision."""

from __future__ import annotations

from studio.compile.impl import (
    compile_report,
    load_report,
    replace_saved_report,
    validate_report,
    write_report,
)
from studio.compile.impl.report import signature_appendix
from studio.review.impl import (
    assessments_from_form,
    read_report_signature,
    record_assessments,
    record_decision,
    record_review_update,
    removal_choice,
    save_report_assessments,
    save_report_decision,
    save_report_signature,
    save_report_update,
    sign_report,
)
from studio.common.presentation import NO_CRA_FIELD, NOT_A_LEGAL_CONCLUSION, worktree_sentence
from studio.review.impl.path import durable_report_path
from studio.review.impl.present import same_run, unchecked_requirement_ids
