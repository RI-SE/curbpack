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
from review.compile import save_report_decision, save_report_signature
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

    repo_id = _sync_open_repo(ws, form)
    if not repo_id:
        raise ModelError("review", "repo", "a chosen repository")
    repo = _registered_repo_path(ws, repo_id)
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    requested = (form.get("result") or [""])[0]
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
    report = compile_report(
        run_result=load_run_result(Path(run_path)),
        requirements=requirements,
        claims=claims,
        trust=trust_store(ws.keys),
        repo=repo,
    )
    out = _new_review_report_path(reports_dir(repo, config))
    write_report(out, report)
    return (
        f"/review?repo={quote(repo_id, safe='')}&compiled=1"
        f"&report={quote(str(out.resolve()), safe='')}"
    )


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
    save_report_decision(Path(report_path), (form.get("decision") or [""])[0])
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
    save_report_signature(
        Path(report_path),
        name=name,
        private_key=private,
        at=_now(),
    )
    return (
        f"/review?repo={quote(repo_id, safe='')}&signed=1"
        f"&report={quote(report_path, safe='')}"
    )


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
    return review_page(
        report,
        reading,
        message=_review_message(query),
        error=error,
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
