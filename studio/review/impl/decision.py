"""Record a human decision and sign the saved review report."""

from __future__ import annotations

import copy
from pathlib import Path

from common.errors import ModelError
from common.signing import read_signature, sign_object
from review.gitseal import git_commit_signature
from studio.compile.impl import load_report, validate_report, write_report


def save_report_decision(path: Path, text: str) -> dict:
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; create a report first")
    decided = record_decision(load_report(path), text)
    write_report(path, decided)
    return decided


def save_report_assessments(path: Path, assessments: list[dict]) -> dict:
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; create a report first")
    updated = record_assessments(load_report(path), assessments)
    write_report(path, updated)
    return updated


def save_report_update(
    path: Path,
    *,
    decision: str,
    assessments: list[dict] | None,
) -> dict:
    """Write decision and assessments together. A failed check leaves the file unchanged."""
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; create a report first")
    updated = record_review_update(load_report(path), decision=decision, assessments=assessments)
    write_report(path, updated)
    return updated


def save_report_signature(
    path: Path,
    *,
    name: str,
    private_key: bytes,
    at: str,
    assessments: list[dict] | None = None,
) -> dict:
    if not path.is_file():
        raise ModelError("review report", "path", "a saved report; create a report first")
    current = load_report(path)
    if assessments is not None:
        current = record_assessments(current, assessments)
        validate_report(current)
    sealed = sign_report(current, name=name, private_key=private_key, at=at)
    write_report(path, sealed)
    return sealed


def record_review_update(report: dict, *, decision: str, assessments: list[dict] | None) -> dict:
    """Apply a decision and assessments in memory. Does not write."""
    _reject_if_signed(report)
    out = copy.deepcopy(report)
    out.pop("signed", None)
    if assessments is not None:
        if assessments:
            out["assessments"] = assessments
        else:
            out.pop("assessments", None)
    if isinstance(decision, str) and decision.strip():
        out["decision"] = decision.strip()
    elif assessments is None:
        raise ModelError("review report", "decision", "the reviewer's own words")
    return out


def record_decision(report: dict, text: str) -> dict:
    _reject_if_signed(report)
    if not isinstance(text, str) or not text.strip():
        raise ModelError("review report", "decision", "the reviewer's own words")
    out = copy.deepcopy(report)
    out.pop("signed", None)
    out["decision"] = text.strip()
    return out


def record_assessments(report: dict, assessments: list[dict]) -> dict:
    """Replace assessments on an unsigned report. An empty list clears them."""
    _reject_if_signed(report)
    out = copy.deepcopy(report)
    out.pop("signed", None)
    if assessments:
        out["assessments"] = assessments
    else:
        out.pop("assessments", None)
    return out


def assessments_from_form(form: dict) -> list[dict] | None:
    """Read posted deviation assessments. Absent fields mean the form did not include them."""
    if "assess_kind" not in form:
        return None
    names = (
        "assess_kind",
        "assess_claim_id",
        "assess_claim_digest",
        "assess_index",
        "assess_namespace",
        "assess_pack_id",
        "assess_requirement_id",
        "assess_requirement_digest",
        "assess_binding",
        "assess_disposition",
        "assess_text",
    )
    columns = {name: [str(value) for value in (form.get(name) or [])] for name in names}
    count = len(columns["assess_kind"])
    if any(len(values) != count for values in columns.values()):
        raise ModelError("review report", "assessments", "one value for each deviation field")
    built = []
    for index in range(count):
        disposition = columns["assess_disposition"][index].strip()
        text = columns["assess_text"][index].strip()
        if disposition == "":
            if text:
                raise ModelError(
                    "review report",
                    "assessments",
                    "Not assessed, or Accept deviation / Must be fixed with text",
                )
            continue
        kind = columns["assess_kind"][index].strip()
        shared = {
            "claim_id": columns["assess_claim_id"][index].strip(),
            "claim_digest": columns["assess_claim_digest"][index].strip(),
            "disposition": disposition,
            "text": text,
        }
        if kind == "check":
            raw_index = columns["assess_index"][index].strip()
            if not raw_index.isdigit():
                raise ModelError("review report", "assessments", "the Check index on the run")
            built.append({"kind": "check", "index": int(raw_index), **shared})
        elif kind == "binding":
            built.append(
                {
                    "kind": "binding",
                    "namespace": columns["assess_namespace"][index].strip(),
                    "pack_id": columns["assess_pack_id"][index].strip(),
                    "requirement_id": columns["assess_requirement_id"][index].strip(),
                    "requirement_digest": columns["assess_requirement_digest"][index].strip(),
                    "binding": columns["assess_binding"][index].strip(),
                    **shared,
                }
            )
        else:
            raise ModelError("review report", "assessments", "check or binding")
    return built


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
