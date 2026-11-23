"""HTTP adapter for Review. The GET model lives in ``studio.review.model``. The URL stays on the old server."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from curbcheck.api import reports_dir, results_dir
from common.errors import ModelError
from common.jsonio import read_json
from common.keystore import load_or_create_key, trust_store
from common.store import load_claims, load_run_result
from discovery.door import repo_claims_dir
from review.compile import (
    assessments_from_form,
    removal_choice,
    save_report_signature,
    save_report_update,
)
from studio.review.impl.saved import _confined_review_report_path
from studio.review.model import _review_view

if TYPE_CHECKING:
    from app.server import Workspace


def _compile_review(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path, _report_sources_for_repo, _requested_dated, _sync_open_repo
    from common.validate import validate_curbpack_config
    from studio.compile.impl import compile_report, write_report
    from studio.compile.impl.path import _new_review_report_path

    repo_id = ""
    requested = (form.get("result") or [""])[0]
    try:
        repo_id = _sync_open_repo(ws, form)
        if not repo_id:
            raise ModelError("review", "repo", "a chosen repository")
        repo = _registered_repo_path(ws, repo_id)
        config = validate_curbpack_config(read_json(repo / "curbpack.json"))
        if not requested.strip():
            raise ModelError("review", "report", "a selected run result")
        status, run_path = _requested_dated(results_dir(repo, config), requested, "run-result")
        if status != "ok":
            raise ModelError(
                "review",
                "report",
                "a run-result file under that repository's results_dir",
            )
        folder = repo_claims_dir(repo)
        claims = load_claims(folder) if folder.is_dir() else []
        _packs, requirements = _report_sources_for_repo(repo, config)
        assessments = assessments_from_form(form)
        report = compile_report(
            run_result=load_run_result(Path(run_path)),
            requirements=requirements,
            claims=claims,
            trust=trust_store(ws.keys),
            repo=repo,
            assessments=assessments,
            remove_retired_checks=removal_choice(form, assessments),
        )
    except ModelError as exc:
        return _refused_review(repo_id, requested, _compile_refusal(exc))
    out = _new_review_report_path(reports_dir(repo, config))
    write_report(out, report)
    nxt = _safe_review_next((form.get("next") or [""])[0])
    if nxt:
        return nxt
    return (
        f"/review?repo={quote(repo_id, safe='')}&compiled=1"
        f"&report={quote(str(out.resolve()), safe='')}"
    )


def _refused_review(repo_id: str, result: str, text: str) -> str:
    """Stay on the run and name the conditions Create New Report did not meet."""
    from urllib.parse import quote

    base = "/review?refused=1"
    if repo_id:
        base += f"&repo={quote(repo_id, safe='')}"
    if result.strip():
        base += f"&result={quote(result, safe='')}"
    return f"{base}&note={quote(text, safe='')}"


def _compile_refusal(exc: ModelError) -> str:
    if exc.field == "conditions":
        return exc.expected
    if exc.object_name == "review" and exc.field == "repo":
        return "A repository must be chosen."
    if exc.object_name == "review" and exc.field == "report":
        if "selected" in exc.expected:
            return "A Check run result must be selected."
        return "The selected file must be a run-result in this repository's results directory."
    if exc.field == "assessments" and "Not assessed" in exc.expected:
        return "A comment needs Accept, Must be fixed, or Retire. Otherwise leave both empty."
    if exc.field.endswith(".text"):
        return "Accept, Must be fixed, and Retire need a comment."
    if exc.field == "remove_retired_checks":
        return (
            "Retire needs the choice of whether signing the report "
            "removes those Checks from the Claims."
        )
    return exc.expected or str(exc)


def _safe_review_next(value: str) -> str:
    """A same-app path. Anything else is ignored so compile cannot redirect elsewhere."""
    text = str(value or "").strip()
    if not text.startswith("/") or text.startswith("//") or "\\" in text or "://" in text:
        return ""
    return text


def _save_review_decision(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path, _sync_open_repo
    from common.validate import validate_curbpack_config

    repo_id = _sync_open_repo(ws, form)
    if not repo_id:
        raise ModelError("review", "repo", "a chosen repository")
    repo = _registered_repo_path(ws, repo_id)
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    report_path = _confined_review_report_path(
        str(reports_dir(repo, config).resolve()),
        (form.get("report") or [""])[0],
    )
    if not report_path:
        raise ModelError("review", "report", "a review-report file under that repository's reports_dir")
    path = Path(report_path)
    save_report_update(
        path,
        decision=(form.get("decision") or [""])[0],
        assessments=assessments_from_form(form),
    )
    return (
        f"/review?repo={quote(repo_id, safe='')}&saved=1"
        f"&report={quote(report_path, safe='')}"
    )


def _sign_review(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _now, _registered_repo_path, _sync_open_repo
    from common.validate import validate_curbpack_config

    repo_id = _sync_open_repo(ws, form)
    if not repo_id:
        raise ModelError("review", "repo", "a chosen repository")
    repo = _registered_repo_path(ws, repo_id)
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    report_path = _confined_review_report_path(
        str(reports_dir(repo, config).resolve()),
        (form.get("report") or [""])[0],
    )
    if not report_path:
        raise ModelError("review", "report", "a review-report file under that repository's reports_dir")
    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    try:
        save_report_signature(
            Path(report_path),
            name=name,
            private_key=private,
            at=_now(),
            assessments=assessments_from_form(form),
            claims_dir=repo_claims_dir(repo),
            trust=trust_store(ws.keys),
        )
    except ModelError as exc:
        if exc.field == "claims":
            return (
                f"/review?repo={quote(repo_id, safe='')}&report={quote(report_path, safe='')}"
                f"&note={quote(str(exc))}"
            )
        raise
    return (
        f"/review?repo={quote(repo_id, safe='')}&signed=1"
        f"&report={quote(report_path, safe='')}"
    )


def _review_error(error: str, query: dict) -> str:
    note = (query.get("note") or [""])[0]
    if not note:
        return error
    return f"{error} {note}".strip() if error else note


def _review_message(query: dict) -> str:
    if (query.get("compiled") or [""])[0]:
        return "Report created."
    if (query.get("saved") or [""])[0]:
        return "Decision saved."
    if (query.get("signed") or [""])[0]:
        return "Report sealed."
    if (query.get("claim_changed") or [""])[0]:
        return (
            "The current Claim has changed. "
            "A new curbcheck run is required for a new run result, and then a new review report."
        )
    return ""


def _review_get(ws: Workspace, query: dict) -> bytes:
    from studio.review.review_page import review_page
    from app.server import _door_chrome, _listed_repos, _sync_open_repo

    try:
        report, reading, error, saved, report_exists, same, unchecked, extra = _review_view(ws, query)
        door = _door_chrome(ws, query)
    except (ModelError, ValueError) as exc:
        if "curbpack.json" not in str(exc):
            raise
        return review_page(
            None,
            None,
            error=str(exc),
            door={"repos": _listed_repos(ws), "repo_id": _sync_open_repo(ws, query)},
        )
    door.update(extra)
    if extra.get("selected_report"):
        door["report_path"] = extra["selected_report"]
    refused = (query.get("refused") or [""])[0] == "1"
    note = (query.get("note") or [""])[0]
    if refused and note:
        door["compile_refusal"] = note
        shown_error = error
    else:
        shown_error = _review_error(error, query)
    return review_page(
        report,
        reading,
        message=_review_message(query),
        error=shown_error,
        discovery={
            "repo_id": (query.get("repo") or query.get("repo_id") or [""])[0],
            "source_id": (query.get("source") or query.get("source_id") or [""])[0],
            "timestamp": (query.get("timestamp") or [""])[0],
        },
        saved=saved,
        report_exists=report_exists,
        same_run_value=same,
        unchecked=unchecked,
        door=door,
    )
