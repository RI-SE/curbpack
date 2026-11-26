"""Review GET model. The old server still returns the page."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from curbcheck.api import _pack_version_dir, packs_dir, reports_dir, results_dir
from common.errors import ModelError
from common.jsonio import read_json
from common.keystore import trust_store
from common.store import load_claims, load_pack_directory, load_run_result
from discovery.door import claim_file_relative, repo_claims_dir
from review.compile import load_report, read_report_signature, same_run, unchecked_requirement_ids
from studio.review.impl.retire import pending_claim_ids
from studio.review.impl.saved import _dated_entries

if TYPE_CHECKING:
    from app.server import Workspace


def _owned_review_report(results_folder: Path, requested: str) -> str:
    """A Review that lives in its Check directory, not in the reports directory."""
    path = Path((requested or "").strip()).resolve()
    try:
        path.relative_to(Path(results_folder).resolve())
    except ValueError:
        return ""
    if path.is_file() and path.parent.name.startswith("run-result_") and (
        path.name == "review-report.json" or path.name.startswith("review-report_")
    ):
        return str(path)
    return ""


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
    extra["repo_path"] = str(repo.resolve())
    extra["review_fresh"] = (query.get("fresh") or [""])[0] == "1"
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
    _mark_latest(extra)
    requested_report = (query.get("report") or [""])[0]
    requested_result = (query.get("result") or [""])[0]
    if requested_report.strip():
        status, chosen = _requested_dated(reports_folder, requested_report, "review-report")
        if status != "ok":
            owned = _owned_review_report(results_folder, requested_report)
            if owned:
                status, chosen = "ok", owned
        if status != "ok":
            errors.append(f"{chosen} is not a review report in the Reports directory.")
            return None, None, " ".join(errors), False, False, None, [], extra
        try:
            report = load_report(Path(chosen))
        except (ModelError, ValueError):
            errors.append(f"{Path(chosen).name} is not a readable review report.")
            return None, None, " ".join(errors), False, False, None, [], extra
        extra["selected_report"] = chosen
        extra["review_mode"] = "remediation" if (query.get("mode") or [""])[0] == "remediation" else "review"
        if isinstance(report.get("signed"), dict) and extra["review_mode"] != "remediation":
            extra["review_locked"] = True
        if extra["review_mode"] == "remediation":
            from studio.review.impl.items import items_home, load_items, write_items
            from common.jsonio import read_json as _read_items_file

            items_path = items_home(repo, Path(chosen))
            if not items_path.is_file():
                signed_items = Path(chosen).with_name(Path(chosen).stem + ".items.json")
                copied = []
                if signed_items.is_file():
                    document = _read_items_file(signed_items)
                    copied = [row for row in (document.get("items") or []) if isinstance(row, dict)]
                    for row in copied:
                        row.pop("signed", None)
                write_items(items_path, copied)
            extra["review_items"] = load_items(items_path)
            if (query.get("remedy") or [""])[0] == "1":
                write_items(items_path, extra["review_items"], marker={"remedy": True})
                extra["review_items"] = load_items(items_path)
            document = _read_items_file(items_path) if items_path.is_file() else {}
            extra["remedy_ready"] = isinstance(document, dict) and document.get("remedy") is True
            _attach_outside(extra, document)
            from studio.review.impl.items import remedy_report_path

            remedy_path = remedy_report_path(Path(chosen))
            if remedy_path.is_file():
                remedy_document = _read_items_file(remedy_path)
                remedy_signed = remedy_document.get("signed") if isinstance(remedy_document, dict) else None
                if isinstance(remedy_signed, dict):
                    extra["remedy_signed"] = True
                    extra["remedy_signer"] = str(remedy_signed.get("name") or "")
                    extra["remedy_ready"] = True
                    if isinstance(remedy_document.get("outside"), list):
                        extra["outside"] = remedy_document["outside"]
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
        extra["source_result"] = _matching_run_path(results_folder, report)
        embedded = report.get("run_result") if isinstance(report.get("run_result"), dict) else {}
        extra["run_reports"] = _reports_for_run(reports_folder, embedded)
        extra["retirement_pending"] = pending_claim_ids(
            report, repo_claims_dir(repo), trust_store(ws.keys)
        )
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
        extra["review_mode"] = "remediation" if (query.get("mode") or [""])[0] == "remediation" else "review"
        from studio.review.impl.items import (
            carry_history,
            latest_ready_remedy,
            latest_signed_remedy,
            load_items,
            open_review_items,
            remedy_bundle,
            retired_absences,
            studio_temp_dir,
            take_in_remedy,
            with_history,
            workspace_items_path,
            write_items,
        )
        from common.jsonio import read_json as _read_items_file

        temp_dir = studio_temp_dir(repo)
        from studio.review.impl.items import check_directory, items_home, run_stem

        run_path = Path(chosen)
        run_name = run_stem(run_path)
        items_path = items_home(repo, Path(chosen))
        resumed = (query.get("resume") or [""])[0] == "1"
        extra["review_resumed"] = resumed
        choice = ""
        pre = _read_items_file(items_path) if items_path.is_file() else {}
        pre_locked = isinstance(pre, dict) and (
            pre.get("review_locked") is True or isinstance(pre.get("signed"), dict)
        )
        if pre_locked:
            choice = "continue"
            extra["review_fresh"] = False
        elif resumed:
            choice = "continue"
        elif extra["review_fresh"]:
            choice = "start"
        _items, items_state = open_review_items(
            items_path, loaded, choice=choice, repo=repo, run_name=run_name
        )
        if items_state == "ask" and not pre_locked:
            extra["existing_review_items"] = str(items_path)
        source_items: list[dict] = []
        signed_items: list[dict] = []
        stored = _read_items_file(items_path) if items_path.is_file() else {}
        history_from = str(stored.get("history_from") or "") if isinstance(stored, dict) else ""
        query_remedy = (query.get("remedy") or [""])[0].strip()
        reuse_flag = (query.get("reuse") or [""])[0].strip()
        chosen = ""
        if query_remedy and query_remedy != "1":
            chosen = Path(query_remedy).stem
        elif history_from:
            chosen = history_from
        elif items_state != "ask" and not extra["review_fresh"] and not resumed and reuse_flag != "1":
            ready = latest_signed_remedy(
                reports_folder,
                loaded,
                results_dir=results_folder,
                skip_directory=check_directory(run_path),
            )
            if ready is None:
                legacy = latest_ready_remedy(temp_dir, reports_folder, loaded)
                ready = (legacy[0], legacy[1], legacy[1]) if legacy else None
            if ready:
                chosen, source_items, signed_items = ready
                extra["reuse_offer"] = chosen
        if chosen and not source_items:
            source_items, signed_items = remedy_bundle(
                reports_folder, chosen, results_dir=results_folder
            )
            if not source_items:
                source_path = workspace_items_path(temp_dir, chosen)
                if source_path.is_file():
                    source_items = load_items(source_path)
                    signed_items = source_items
        if source_items and not extra.get("reuse_offer"):
            if reuse_flag == "1":
                _items = take_in_remedy(repo, loaded, _items, source_items, signed_items or source_items)
            elif query_remedy:
                _items = carry_history(_items, source_items)
            write_items(items_path, _items, marker={"history_from": chosen})
        extra["review_items"] = with_history(_items, source_items) if source_items else _items
        extra["retired_items"] = retired_absences(source_items, loaded) if source_items else []
        extra["run_reports"] = _reports_for_run(reports_folder, loaded)
        stored_now = _read_items_file(items_path) if items_path.is_file() else {}
        notes = stored_now.get("notes") if isinstance(stored_now, dict) else ""
        report = {"run_result": loaded, "claims": [], "appendix": []}
        if isinstance(stored_now, dict) and stored_now.get("work_saved") is True:
            extra["work_saved"] = True
        if isinstance(stored_now, dict) and (
            stored_now.get("review_locked") is True or isinstance(stored_now.get("signed"), dict)
        ):
            extra["review_locked"] = True
        from studio.review.impl.items import active_remedy_report, remediation_is_sealed

        home = check_directory(run_path)
        remedy_locked = remediation_is_sealed(items_path) if items_path.is_file() else False
        active_remedy = active_remedy_report(home, stored_now)
        view = (query.get("view") or [""])[0]
        if (
            extra.get("review_locked")
            and extra["review_mode"] == "remediation"
            and not remedy_locked
            and view != "report"
        ):
            write_items(items_path, load_items(items_path), marker={"remedy": True})
            extra["remedy_ready"] = True
        _attach_outside(extra, stored_now)
        if remedy_locked:
            extra["remedy_locked"] = True
            extra["remedy_signed"] = True
            if active_remedy is not None and active_remedy.is_file():
                sealed = _read_items_file(active_remedy)
                signed = sealed.get("signed") if isinstance(sealed, dict) else None
                if isinstance(signed, dict):
                    extra["remedy_signer"] = str(signed.get("name") or "")
                    extra["remedy_signed_at"] = str(signed.get("at") or "")
                    extra["remedy_report"] = active_remedy.name
                if isinstance(sealed, dict) and isinstance(sealed.get("outside"), list):
                    extra["outside"] = sealed["outside"]
                if isinstance(sealed, dict) and isinstance(sealed.get("notes"), str):
                    extra["remedy_notes"] = sealed["notes"]
                markdown = active_remedy.with_suffix(".md")
                if markdown.is_file():
                    extra["remedy_md"] = markdown.name
        elif isinstance(stored_now, dict):
            revoked_rows = [row for row in (stored_now.get("remedy_revoked") or []) if isinstance(row, dict)]
            if revoked_rows:
                extra["remedy_revocation"] = revoked_rows[-1]
                report_name = str(revoked_rows[-1].get("report") or "")
                if home is not None and report_name.endswith(".json"):
                    markdown = home / f"{Path(report_name).stem}.md"
                    if markdown.is_file() and markdown.parent.resolve() == home.resolve():
                        extra["remedy_revocation_md"] = markdown.name
        try:
            from studio.review.impl.items import assessments_from_decisions

            saved_assessments = assessments_from_decisions(extra["review_items"], loaded)
        except ModelError:
            saved_assessments = []
        if saved_assessments:
            report["assessments"] = saved_assessments
        if isinstance(notes, str) and notes.strip():
            report["decision"] = notes.strip()
        if not extra.get("remedy_signed"):
            remedy_notes = stored_now.get("remedy_notes") if isinstance(stored_now, dict) else ""
            if isinstance(remedy_notes, str):
                extra["remedy_notes"] = remedy_notes
        snapshot = (query.get("snapshot") or [""])[0].strip()
        if snapshot and check_directory(run_path) is not None:
            snap = Path(snapshot).resolve()
            home = check_directory(run_path)
            if snap.is_file() and home is not None and snap.parent.resolve() == home.resolve():
                try:
                    document = _read_items_file(snap)
                except (OSError, ValueError):
                    document = None
                signed = document.get("signed") if isinstance(document, dict) else None
                if isinstance(signed, dict):
                    extra["viewing_snapshot"] = True
                    extra["remedy_signed"] = True
                    extra["remedy_signer"] = str(signed.get("name") or "")
                    if isinstance(document.get("outside"), list):
                        extra["outside"] = document["outside"]
                    extra["remedy_notes"] = (
                        document.get("notes") if isinstance(document.get("notes"), str) else ""
                    )
        extra["presentation"] = _raw_presentation(ws, repo, config, loaded, query)
        extra["file_view"] = _review_file_view(repo, (query.get("file") or [""])[0])
        return report, None, " ".join(errors), False, False, None, [], extra
    return None, None, " ".join(errors), False, False, None, [], extra


def _attach_outside(extra: dict, document: object) -> None:
    if not isinstance(document, dict):
        return
    pending = document.get("pending_outside")
    if isinstance(pending, dict) and pending.get("checks"):
        extra["pending_outside"] = pending
        extra["outside_can_rollback"] = isinstance(document.get("studio_snapshot"), dict)
    recorded = document.get("outside")
    if isinstance(recorded, list) and recorded:
        extra["outside"] = recorded


def _reports_for_run(folder: Path, run_result: dict) -> list[dict]:
    if not isinstance(run_result, dict) or not folder.is_dir():
        return []
    rows = []
    for path in sorted(folder.glob("review-report_*.json")):
        if not path.is_file():
            continue
        try:
            report = load_report(path)
        except (ModelError, ValueError):
            continue
        if not same_run(report, run_result):
            continue
        signed = report.get("signed") if isinstance(report.get("signed"), dict) else None
        rows.append(
            {
                "name": path.name,
                "path": str(path.resolve()),
                "decision": str(report.get("decision") or "").strip(),
                "signed": signed is not None,
                "signer": str(signed.get("name") or "") if signed else "",
            }
        )
    rows.reverse()
    return rows


def _mark_latest(extra: dict) -> None:
    rows = extra.get("run_results") or []
    if rows and isinstance(rows[-1], dict):
        extra["latest_result"] = str(rows[-1].get("path") or "")


def _matching_run_path(folder: Path, report: dict) -> str:
    if not folder.is_dir():
        return ""
    found = ""
    for path in sorted(folder.glob("run-result_*.json")):
        if not path.is_file():
            continue
        try:
            loaded = load_run_result(path)
        except (ModelError, ValueError):
            continue
        if same_run(report, loaded):
            found = str(path.resolve())
    return found


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


def _same_as_latest_run(results_folder: Path, report: dict):
    if not results_folder.is_dir():
        return None
    from studio.check.check_model import _run_result_files

    dated = _run_result_files(results_folder)
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
