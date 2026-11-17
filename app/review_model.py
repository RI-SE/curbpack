"""Review view-model, compile POST, decision POST, and sign POST. The URL stays on the old server."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from curbcheck.api import _pack_version_dir, packs_dir, reports_dir, results_dir
from common.errors import ModelError
from common.jsonio import read_json
from common.keystore import load_or_create_key, trust_store
from common.store import load_claims, load_pack_directory, load_run_result
from discovery.door import claim_file_relative, repo_claims_dir
from review.compile import (
    compile_report,
    load_report,
    read_report_signature,
    same_run,
    save_report_decision,
    save_report_signature,
    unchecked_requirement_ids,
    write_report,
)

if TYPE_CHECKING:
    from app.server import Workspace


def _review_view(ws: Workspace, query: dict | None = None) -> tuple:
    from app.server import _registered_repo_path, _requested_dated, _sync_open_repo

    query = query or {}
    repo_id = _sync_open_repo(ws, query)
    empty = {"run_results": [], "review_reports": [], "results_notice": "", "selected_result": "", "selected_report": ""}
    if not repo_id:
        return None, None, "No repository is chosen.", False, False, None, [], empty
    from common.validate import validate_curbpack_config

    repo = _registered_repo_path(ws, repo_id)
    config_path = repo / "curbpack.json"
    if not config_path.is_file():
        return None, None, "curbpack.json is missing.", False, False, None, [], empty
    try:
        loaded_config = read_json(config_path)
    except ValueError as exc:
        raise ModelError("curbpack.json", "json", f"readable JSON ({exc})") from exc
    config = validate_curbpack_config(loaded_config)
    results_folder = results_dir(repo, config)
    reports_folder = reports_dir(repo, config)
    extra = dict(empty)
    errors: list[str] = []
    if not results_folder.is_dir():
        errors.append(f"Results directory {config['results_dir']} cannot be used.")
    else:
        extra["run_results"] = _dated_entries(results_folder, "run-result")
        if not extra["run_results"]:
            extra["results_notice"] = "There is no run result."
    if not reports_folder.is_dir():
        errors.append(f"Reports directory {config['reports_dir']} cannot be used.")
    else:
        extra["review_reports"] = _dated_entries(reports_folder, "review-report")
    requested_report = (query.get("report") or [""])[0]
    requested_result = (query.get("result") or [""])[0]
    if requested_report.strip():
        status, chosen = _requested_dated(reports_folder, requested_report, "review-report")
        if status != "ok":
            errors.append(f"{chosen} is not a review report in the Reports directory.")
            return None, None, " ".join(errors), False, False, None, [], extra
        try:
            report = load_report(Path(chosen))
        except (ModelError, ValueError):
            errors.append(f"{Path(chosen).name} is not a readable review report.")
            return None, None, " ".join(errors), False, False, None, [], extra
        extra["selected_report"] = chosen
        try:
            report_rel = str(Path(chosen).resolve().relative_to(repo.resolve()))
        except ValueError:
            report_rel = Path(chosen).name
        reading = read_report_signature(
            report, trust_store(ws.keys), repo=repo, relative=report_rel
        )
        same = _same_as_latest_run(results_folder, report)
        extra["presentation"] = _report_presentation(ws, repo, config, report, query, reading)
        extra["file_view"] = _review_file_view(repo, (query.get("file") or [""])[0])
        return report, reading, " ".join(errors), True, True, same, _unchecked_for_repo(repo, config, report), extra
    if requested_result.strip():
        status, chosen = _requested_dated(results_folder, requested_result, "run-result")
        if status != "ok":
            errors.append(f"{chosen} is not a run result in the Results directory.")
            return None, None, " ".join(errors), False, False, None, [], extra
        try:
            loaded = load_run_result(Path(chosen))
        except (ModelError, ValueError):
            errors.append(f"{Path(chosen).name} is not a readable run result.")
            return None, None, " ".join(errors), False, False, None, [], extra
        extra["selected_result"] = chosen
        report = {"run_result": loaded, "claims": [], "appendix": []}
        extra["presentation"] = _raw_presentation(ws, repo, config, loaded, query)
        extra["file_view"] = _review_file_view(repo, (query.get("file") or [""])[0])
        return report, None, " ".join(errors), False, False, None, [], extra
    return None, None, " ".join(errors), False, False, None, [], extra


def _review_file_view(repo: Path, requested: str) -> dict | None:
    wanted = requested.strip()
    if not wanted:
        return None
    if Path(wanted).is_absolute() or ".." in Path(wanted).parts:
        return {"path": wanted, "state": "invalid", "text": ""}
    try:
        path = (repo / wanted).resolve()
        path.relative_to(repo.resolve())
    except ValueError:
        return {"path": wanted, "state": "invalid", "text": ""}
    if not path.is_file():
        return {"path": wanted, "state": "missing", "text": ""}
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_bytes().decode("utf-8", errors="replace")
    return {"path": wanted, "state": "present", "text": text}


def _dated_entries(folder: Path, prefix: str) -> list[dict]:
    rows = []
    for path in sorted(folder.glob(f"{prefix}_*.json")):
        if path.is_file():
            rows.append({"name": path.name, "path": str(path.resolve())})
    return rows


def _same_as_latest_run(results_folder: Path, report: dict):
    if not results_folder.is_dir():
        return None
    dated = [path for path in sorted(results_folder.glob("run-result_*.json")) if path.is_file()]
    if not dated:
        return None
    try:
        return same_run(report, load_run_result(dated[-1]))
    except (ModelError, ValueError):
        return None


def _expanded_query(query: dict) -> set[str] | None:
    if "expanded" in query:
        return {part for part in (query.get("expanded") or [""])[0].split(",") if part}
    return None


def _raw_presentation(ws: Workspace, repo: Path, config: dict, run_result: dict, query: dict) -> dict:
    from app.server import _report_sources_for_repo
    from common.signing import read_signature
    from review.gitseal import read_claim_signature
    from review.present import present_raw_run

    folder = repo_claims_dir(repo)
    claims = load_claims(folder) if folder.is_dir() else []
    claims_by_id = {claim["id"]: claim for claim in claims if isinstance(claim.get("id"), str)}
    _packs, requirements = _report_sources_for_repo(repo, config)
    requirements_by_id = {
        requirement["id"]: requirement for requirement in requirements if isinstance(requirement.get("id"), str)
    }
    trust = trust_store(ws.keys)
    claim_readings = {}
    for claim in claims:
        claim_id = claim.get("id")
        if not isinstance(claim_id, str):
            continue
        relative = claim_file_relative(repo, folder, claim_id)
        claim_readings[claim_id] = read_claim_signature(claim, trust, repo=repo, relative=relative)
    requirement_readings = {}
    root = packs_dir(repo, config)
    for requirement_id, requirement in requirements_by_id.items():
        if isinstance(requirement.get("signed"), dict):
            requirement_readings[requirement_id] = read_signature(requirement, trust, what="requirement")
            continue
        relative = None
        try:
            directory = _pack_version_dir(root, str(requirement.get("pack_id") or ""))
            relative = str((directory / f"{requirement_id}.json").resolve().relative_to(repo.resolve()))
        except (ModelError, ValueError):
            relative = None
        from review.gitseal import git_commit_signature

        git_reading = git_commit_signature(repo, relative) if relative else None
        requirement_readings[requirement_id] = git_reading or read_signature(
            requirement, trust, what="requirement"
        )
    return present_raw_run(
        run_result=run_result,
        claims_by_id=claims_by_id,
        requirements_by_id=requirements_by_id,
        claim_readings=claim_readings,
        requirement_readings=requirement_readings,
        expanded=_expanded_query(query),
        repo=repo,
        chain=_chain_for(repo, run_result, trust),
    )


def _report_presentation(
    ws: Workspace,
    repo: Path,
    config: dict,
    report: dict,
    query: dict,
    report_reading: dict,
) -> dict:
    from common.signing import read_signature
    from review.gitseal import read_claim_signature
    from review.present import present_compiled_report

    folder = repo_claims_dir(repo)
    current = load_claims(folder) if folder.is_dir() else []
    current_by_id = {claim["id"]: claim for claim in current if isinstance(claim.get("id"), str)}
    trust = trust_store(ws.keys)
    claim_readings = {}
    for claim in report.get("claims") or []:
        if not isinstance(claim, dict) or not isinstance(claim.get("id"), str):
            continue
        claim_readings[claim["id"]] = read_claim_signature(claim, trust)
    requirement_readings = {}
    for requirement in report.get("requirements") or []:
        if not isinstance(requirement, dict) or not isinstance(requirement.get("id"), str):
            continue
        requirement_readings[requirement["id"]] = read_signature(requirement, trust, what="requirement")
    return present_compiled_report(
        report=report,
        current_claims_by_id=current_by_id,
        claim_readings=claim_readings,
        requirement_readings=requirement_readings,
        expanded=_expanded_query(query),
        report_reading=report_reading,
        repo=repo,
        chain=_chain_for(
            repo,
            report.get("run_result") if isinstance(report.get("run_result"), dict) else {},
            trust,
        ),
    )


def _chain_for(repo: Path, run_result: dict, trust: dict) -> dict:
    from studio.review.resolve import resolve_chain

    try:
        return resolve_chain(repo, run_result, trust=trust)
    except (ModelError, OSError, ValueError):
        return {"claims": []}


def _unchecked_for_repo(repo: Path, config: dict, report: dict) -> list[str]:
    from curbcheck.api import selected_requirement_ids

    loaded = []
    root = packs_dir(repo, config)
    for pack_id in config.get("packs") or []:
        if not isinstance(pack_id, str) or not pack_id:
            continue
        try:
            directory = _pack_version_dir(root, pack_id)
        except ModelError:
            continue
        try:
            loaded.append(load_pack_directory(directory))
        except ModelError:
            continue
    if not loaded:
        return []
    try:
        selected = sorted(selected_requirement_ids(loaded, config))
    except ModelError:
        return []
    return unchecked_requirement_ids(selected, report)


def _new_dated_json(folder: Path, prefix: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = folder / f"{prefix}_{stamp}.json"
        if not path.exists():
            return path
        time.sleep(1)


def _new_review_report_path(folder: Path) -> Path:
    return _new_dated_json(folder, "review-report")


def _compile_review(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path, _report_sources_for_repo, _requested_dated, _sync_open_repo
    from common.validate import validate_curbpack_config

    repo_id = _sync_open_repo(ws, form)
    if not repo_id:
        raise ModelError("review", "repo", "a chosen repository")
    repo = _registered_repo_path(ws, repo_id)
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    requested = (form.get("result") or [""])[0]
    if not requested.strip():
        raise ModelError("review", "compile", "a selected run result")
    status, run_path = _requested_dated(results_dir(repo, config), requested, "run-result")
    if status != "ok":
        raise ModelError(
            "review",
            "compile",
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


def _confined_review_report_path(reports_folder: str, requested: str) -> str:
    if not reports_folder:
        return ""
    folder = Path(reports_folder).resolve()
    wanted = (requested or "").strip()
    if wanted:
        path = Path(wanted).resolve()
        try:
            path.relative_to(folder)
        except ValueError:
            path = None
        if path is not None and path.is_file() and path.name.startswith("review-report_") and path.name.endswith(".json"):
            return str(path)
    dated = sorted(folder.glob("review-report_*.json"))
    if dated:
        return str(dated[-1].resolve())
    return ""


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
        return "Report compiled."
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
