"""HTTP entry point. Handlers call use cases and hand the results to pages."""

from __future__ import annotations

import copy
import json
import logging
import re
import secrets
import time
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

_LOG = logging.getLogger("poc2.app")

from app import pages
from checks.run import (
    _pack_version_dir,
    claims_dir,
    new_run_result_path,
    packs_dir,
    process_exit_code,
    reports_dir,
    results_dir,
    run_and_write,
)
from claims.bind import (
    build_claim,
    exist_args_for_path,
    law_passages,
    read_claim,
    read_claim_seal,
    read_claims,
    rebind_from_fields,
    require_requirement_id,
    retire_claim,
    sign_claim,
    write_claim,
)
from common.canonical import version_digest
from common.paths import default_workspace, install_root
from common.errors import CheckError, ModelError, SigningUnavailable
from common.jsonio import read_json, write_json
from common.keystore import load_or_create_key, trust_store
from common.signing import read_signature
from common.store import (
    load_claims,
    load_pack,
    load_pack_directory,
    load_requirement,
    load_run_result,
    save_requirement,
)
from claims.ui import http as claim_http
from claims.ui import pages as claim_pages
from demo_setup import prepare_demo
from discovery.jobs import read_job as read_discover_job
from discovery.jobs import reviewable_targets
from discovery.jobs import request_abort as abort_discover_job
from discovery.jobs import start_discover_job
from discovery.browse import list_directories
from discovery.door import (
    claim_file_relative,
    created_curbpack,
    open_paths,
    open_repo_id,
    repo_claims_dir,
    repo_pack_requirements,
    save_directory_fields,
    set_open_repo,
)
from discovery.studio import (
    created_studio_config,
    editor_values,
    save_studio_config,
    studio_file,
    studio_from_form,
)
from discovery.repos import add_repo, find_repo, load_repos, resolve_repo_path, save_repos
from discovery.try_run import (
    candidate_for_path,
    load_try_result,
    read_try_file,
    read_try_job,
    start_try_job,
)
from requirements.editing import (
    apply_edits,
    approve_working_copy,
    assign_reference_numbers,
    publish_requirement,
    read_pack_seal,
    save_working_requirement,
    seal_pack_directory,
)
from requirements.extract.adapter import (
    ADAPTERS,
    list_adapters,
    load_adapter,
    section_provisions,
    stage00,
)
from requirements.extract.pipeline import draft_pack
from requirements.catalog import (
    add_document,
    add_section,
    ensure_catalog,
    find_document,
    list_formex_adapter_choices,
    load_catalog,
    make_document_id,
    make_id,
    save_catalog,
)
from requirements.compare import apply_extraction_choices, apply_transfer, compare_copies, extraction_review
from requirements.consolidate import apply_consolidation, suggest_consolidations
from requirements.jobs import read_job, request_abort, start_extract_job
from requirements.ui import pages as requirement_pages
from requirements.ui import try_discovery as try_discovery_ui
from requirements.workspace import (
    ensure_default_selection,
    list_pack_ids,
    list_pack_options,
    list_published_versions,
    list_working_copies,
    load_working_copy,
    list_publication_blockers,
    mark_published_selected,
    mark_selected,
    mark_source_adapter,
    export_pack,
    publish_pack,
    read_selection,
    resolve_copy_ref,
    resolve_selected_pack,
    select_published_pack,
    select_working_copy,
    selected_copy,
    selected_source_adapter,
    work_directory,
)
from review.compile import (
    compile_report,
    durable_report_path,
    load_report,
    read_report_signature,
    same_run,
    save_report_decision,
    save_report_signature,
    unchecked_requirement_ids,
    write_report,
)
from scaffold.stub import write_stub
from workflow import snapshot

ROOT = install_root()
_VENDOR = {
    "/vendor/jsondiffpatch.js": (
        ROOT / "requirements" / "ui" / "vendor" / "jsondiffpatch" / "jsondiffpatch.umd.js",
        "text/javascript; charset=utf-8",
    ),
    "/vendor/jsondiffpatch.css": (
        ROOT / "requirements" / "ui" / "vendor" / "jsondiffpatch" / "html.css",
        "text/css; charset=utf-8",
    ),
}
DEFAULT_WORKSPACE = default_workspace()


class Workspace:
    def __init__(self, root: Path):
        self.root = root
        self.packs = root / "packs"
        self.pack = self.packs / "cra-baseline"
        self.repo = root / "product"
        self.run_path = self.repo / ".curbpack" / "run-result.json"
        self.report_path = durable_report_path(self.repo)
        self.keys = root / "keys"

    def requirement_path(self) -> Path:
        return self.pack / "CRA-ANNEX-VII-RISK.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def edits_for_requirement(requirement: dict, form: dict) -> dict:
    source = dict(requirement["source"])
    edition = (form.get("edition") or [""])[0].strip()
    if edition:
        source["edition"] = edition
    else:
        source.pop("edition", None)
    hints = {
        "concepts": _lines((form.get("concepts") or [""])[0]),
        "path_hints": _lines((form.get("path_hints") or [""])[0]),
        "expected_evidence": _lines((form.get("expected_evidence") or [""])[0]),
    }
    sources = [{"source": item} for item in _lines((form.get("sources") or [""])[0])]
    if sources:
        hints["sources"] = sources
    hints = {key: value for key, value in hints.items() if value}
    return {
        "source": source,
        "remediation_hint": (form.get("remediation_hint") or [""])[0].strip(),
        "note": (form.get("note") or [""])[0].strip(),
        "discovery_hints": hints,
    }


def _review_message(query: dict) -> str:
    if (query.get("compiled") or [""])[0]:
        return "Report compiled."
    if (query.get("saved") or [""])[0]:
        return "Decision saved."
    if (query.get("signed") or [""])[0]:
        return "Report signed."
    return ""


def _review_view(ws: Workspace, query: dict | None = None) -> tuple:
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
        reading = read_report_signature(report, trust_store(ws.keys))
        same = _same_as_latest_run(results_folder, report)
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
        return report, None, " ".join(errors), False, False, None, [], extra
    return None, None, " ".join(errors), False, False, None, [], extra


def _dated_entries(folder: Path, prefix: str) -> list[dict]:
    rows = []
    for path in sorted(folder.glob(f"{prefix}_*.json")):
        if path.is_file():
            rows.append({"name": path.name, "path": str(path.resolve())})
    return rows


def _requested_dated(folder: Path, requested: str, prefix: str) -> tuple[str, str]:
    wanted = requested.strip()
    path = Path(wanted).resolve()
    try:
        path.relative_to(folder.resolve())
    except ValueError:
        return "outside", wanted
    if path.is_file() and path.name.startswith(prefix + "_") and path.name.endswith(".json"):
        return "ok", str(path)
    return "missing", str(path)


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


def _unchecked_for_repo(repo: Path, config: dict, report: dict) -> list[str]:
    from checks.run import selected_requirement_ids

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


def _report_sources_for_repo(repo: Path, config: dict) -> tuple[list[dict], list[dict]]:
    packs: list[dict] = []
    requirements: list[dict] = []
    root = packs_dir(repo, config)
    for pack_id in config.get("packs") or []:
        if not isinstance(pack_id, str) or not pack_id:
            continue
        try:
            directory = _pack_version_dir(root, pack_id)
        except ModelError:
            continue
        pack, rows = load_pack_directory(directory)
        packs.append(pack)
        requirements.extend(rows)
    return packs, requirements


def _require_demo_requirement(ws: Workspace) -> Path:
    """Legacy Annex VII.3 sample pack used by /requirement and discovery demo steps."""
    path = ws.requirement_path()
    if path.is_file():
        return path
    raise ModelError(
        "demo pack",
        "CRA-ANNEX-VII-RISK.json",
        "a prepared sample under packs/cra-baseline/ "
        "(use Prepare sample workspace on the cover), "
        "or open Requirements catalog for dated extracts from regulation adapters",
    )


def make_handler(ws: Workspace):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            return

        def _send(self, status: int, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _form(self) -> dict:
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8")
            return parse_qs(raw, keep_blank_values=True)

        def _redirect(self, location: str) -> None:
            self.send_response(303)
            self.send_header("Location", location)
            self.end_headers()

        def _fail(self, exc: BaseException) -> None:
            if isinstance(exc, (ModelError, CheckError, SigningUnavailable)):
                message = str(exc)
            else:
                _LOG.error(
                    "request failed method=%s path=%s: %s\n%s",
                    self.command,
                    self.path,
                    exc,
                    traceback.format_exc(),
                )
                message = (
                    "The server could not complete that request. "
                    "See the server log for details."
                )
            self._send(400, pages.page("Error", f'<p class="err">{_escape(message)}</p>'))

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in _VENDOR:
                self._send_vendor(parsed.path)
                return
            if parsed.path.startswith("/requirements/jobs/") and not parsed.path.endswith("/abort"):
                self._send_job(parsed.path[len("/requirements/jobs/") :])
                return
            if parsed.path.startswith("/discover/jobs/") and not parsed.path.endswith("/abort"):
                self._send_discover_job(parsed.path[len("/discover/jobs/") :])
                return
            if parsed.path.startswith("/requirements/try-discovery/jobs/"):
                self._send_try_job(parsed.path[len("/requirements/try-discovery/jobs/") :])
                return
            if parsed.path == "/discover/browse":
                self._send_browse(parse_qs(parsed.query))
                return
            try:
                body = self._get(parsed.path, parse_qs(parsed.query))
                self._send(200, body)
            except Exception as exc:
                self._fail(exc)

        def _send_vendor(self, path: str) -> None:
            file_path, content_type = _VENDOR[path]
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_job(self, job_id: str) -> None:
            try:
                body = json.dumps(read_job(ws.root / "jobs", job_id)).encode("utf-8")
            except Exception as exc:
                self._fail(exc)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_discover_job(self, job_id: str) -> None:
            try:
                body = json.dumps(read_discover_job(ws.root / "jobs", job_id)).encode("utf-8")
            except Exception as exc:
                self._fail(exc)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_browse(self, query: dict) -> None:
            try:
                payload = list_directories(
                    (query.get("dir") or [""])[0],
                    start=ws.root,
                )
                body = json.dumps(payload).encode("utf-8")
            except ModelError as exc:
                body = json.dumps({"error": str(exc)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as exc:
                self._fail(exc)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_try_job(self, job_id: str) -> None:
            try:
                body = json.dumps(read_try_job(ws.root / "jobs", job_id)).encode("utf-8")
            except Exception as exc:
                self._fail(exc)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            form: dict = {}
            try:
                form = self._form()
                self._post(parsed.path, form)
            except ModelError as exc:
                target = _requirement_editor_for_error(exc, form)
                if target:
                    self._redirect(target)
                    return
                self._fail(exc)
            except Exception as exc:
                self._fail(exc)

        def _get(self, path: str, query: dict) -> bytes:
            researcher = claim_http.handle_get(
                ws.root,
                path,
                query,
                sources=_registered_sources(ws),
                trust=trust_store(ws.keys),
            )
            if researcher is not None:
                return researcher
            if path == "/":
                return pages.cover(_home_model(ws), message=_home_message(query))
            if path == "/requirements":
                document_id = (query.get("document") or [""])[0].strip()
                if document_id:
                    return requirement_pages.catalog_page(
                        _catalog_model(ws, query, document_id)
                    )
                return requirement_pages.documents_page(_documents_model(ws, query))
            if path == "/requirements/inspect":
                return requirement_pages.source_page(_inspect_model(ws, query))
            if path == "/requirements/extract/review":
                return requirement_pages.extract_review_page(_extract_review_model(ws, query))
            if path == "/requirements/copy":
                return requirement_pages.copy_page(_copy_model(ws, query))
            if path == "/requirements/export":
                return requirement_pages.export_page(_export_model(ws, query))
            if path == "/requirements/publish":
                return requirement_pages.publication_page(_publication_model(ws, query))
            if path == "/requirements/compare":
                return requirement_pages.compare_page(_compare_model(ws, query))
            if path == "/requirements/consolidate":
                return requirement_pages.consolidate_page(_consolidate_model(ws))
            if path.startswith("/requirements/requirement/") and path.endswith(
                "/try-discovery/file"
            ):
                requirement_id = path[
                    len("/requirements/requirement/") : -len("/try-discovery/file")
                ]
                return try_discovery_ui.file_page(
                    _try_discovery_file_model(ws, requirement_id, query)
                )
            if path.startswith("/requirements/requirement/"):
                requirement_id = path[len("/requirements/requirement/") :]
                return requirement_pages.editor_page(_editor_model(ws, requirement_id, query))
            if path == "/requirement":
                requirement = load_requirement(_require_demo_requirement(ws))
                reading = snapshot(ws.root)["requirement_reading"]
                return pages.requirement_page(requirement, reading)
            if path == "/discover/repo":
                return claim_pages.discover_page(_discover_model(ws, query, product=True))
            if path == "/discover":
                return claim_pages.discover_page(_discover_model(ws, query))
            if path == "/claims":
                message = ""
                if (query.get("saved") or [""])[0]:
                    message = "Claim saved."
                if (query.get("cleared") or [""])[0]:
                    message = "Claim saved. Previous seal cleared; this is an unsigned draft."
                if (query.get("signed") or [""])[0]:
                    message = "Claim signed."
                if (query.get("retired") or [""])[0]:
                    message = "Claim retired."
                return pages.claims_page(_claims_model(ws, query), message=message)
            if path == "/scaffold":
                return pages.scaffold_page()
            if path == "/check":
                editor = _check_editor_model(ws, query)
                result, exit_code = _check_report(ws, query, editor)
                return pages.check_page(
                    result,
                    exit_code,
                    message=_check_message(query),
                    editor=editor,
                )
            if path == "/review":
                try:
                    report, reading, error, saved, report_exists, same, unchecked, extra = _review_view(ws, query)
                    door = _door_chrome(ws, query)
                except (ModelError, ValueError) as exc:
                    if "curbpack.json" not in str(exc):
                        raise
                    return pages.review_page(
                        None,
                        None,
                        error=str(exc),
                        door={"repos": _listed_repos(ws), "repo_id": _sync_open_repo(ws, query)},
                    )
                door.update(extra)
                if extra.get("selected_report"):
                    door["report_path"] = extra["selected_report"]
                return pages.review_page(
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
            if path == "/studio":
                return pages.studio_page(_studio_model(ws, query), message=_studio_message(query))
            return pages.page("Not found", "<p>Unknown page.</p>")

        def _post(self, path: str, form: dict) -> None:
            researcher = claim_http.handle_post(
                ws.root,
                path,
                form,
                sources=_registered_sources(ws),
                trust=trust_store(ws.keys),
            )
            if isinstance(researcher, bytes):
                self._send(200, researcher)
                return
            if isinstance(researcher, str):
                self._redirect(researcher)
                return
            if path == "/prepare":
                prepare_demo(ws.root)
                self._redirect("/?prepared=1")
                return
            if path == "/select-pack":
                _apply_pack_selection(ws, form)
                self._redirect("/?selected=1")
                return
            if path == "/requirements/source":
                adapter_id = (form.get("adapter_id") or [""])[0].strip()
                mark_source_adapter(ws.root, adapter_id)
                _load_adapter(adapter_id)
                self._redirect(f"/requirements/inspect?adapter={adapter_id}")
                return
            if path == "/requirements/start-empty":
                repo_id = _start_empty_folder(ws, (form.get("folder") or [""])[0])
                self._redirect(f"/requirements?repo={quote(repo_id)}")
                return
            if path == "/requirements/curbpack":
                repo_id = (form.get("repo") or [""])[0].strip()
                if not repo_id:
                    raise ModelError("curbpack.json", "repo", "a chosen repository")
                set_open_repo(ws.root, repo_id)
                if (form.get("action") or [""])[0].strip() == "save":
                    _save_curbpack_form(_registered_repo_path(ws, repo_id), form)
                self._redirect(f"/requirements?repo={quote(repo_id)}")
                return
            if path == "/requirements/documents":
                repo_id = (form.get("repo") or [""])[0].strip()
                if not repo_id:
                    raise ModelError("pack", "repo", "a chosen repository")
                pack_fields = dict(
                    name=(form.get("name") or [""])[0],
                    official_name=(form.get("official_name") or [""])[0],
                    url=(form.get("url") or [""])[0],
                    adapter_id=(form.get("adapter_id") or [""])[0],
                )
                if (form.get("action") or [""])[0].strip() == "update":
                    _update_pack_info(
                        ws,
                        repo_id,
                        (form.get("pack") or [""])[0],
                        **pack_fields,
                    )
                    self._redirect(f"/requirements?repo={quote(repo_id)}&updated=1")
                    return
                _add_pack_to_repo(ws, repo_id, **pack_fields)
                self._redirect(f"/requirements?repo={quote(repo_id)}&added=1")
                return
            if path == "/requirements/catalog":
                catalog = ensure_catalog(ws.root)
                document_id = (form.get("document_id") or [""])[0].strip()
                section_id = (form.get("section_id") or [""])[0]
                repo_id = (form.get("repo") or [""])[0].strip()
                if find_document(catalog, document_id) is None:
                    _add_pack_section(ws, document_id, repo_id, section_id)
                else:
                    add_section(
                        catalog,
                        document_id=document_id,
                        section_id=section_id,
                    )
                    save_catalog(ws.root, catalog)
                located = f"document={quote(document_id, safe='')}&added=1"
                if repo_id:
                    located += f"&repo={quote(repo_id, safe='')}"
                self._redirect(f"/requirements?{located}")
                return
            if path == "/requirements/select":
                adapter_id = (form.get("adapter_id") or [""])[0].strip() or selected_source_adapter(ws.root)
                _adapter_dir, adapter = _load_adapter(adapter_id)
                timestamp = (form.get("timestamp") or [""])[0].strip()
                if not timestamp:
                    raise ModelError(adapter_id, "timestamp", "a dated working copy")
                mark_source_adapter(ws.root, adapter_id)
                mark_selected(ws.root, adapter["pack_id"], timestamp)
                nxt = (form.get("next") or [""])[0].strip()
                if nxt == "edit":
                    self._redirect("/requirements/copy")
                elif nxt == "publish":
                    self._redirect("/requirements/publish")
                else:
                    self._redirect("/requirements?selected=1")
                return
            if path == "/requirements/extract":
                adapter_id = (form.get("adapter_id") or [""])[0].strip() or selected_source_adapter(ws.root)
                section_id = (form.get("section_id") or [""])[0].strip()
                adapter_dir, adapter = _load_adapter(adapter_id)
                mark_source_adapter(ws.root, adapter_id)
                if not section_id:
                    raise ModelError(adapter_id, "section_id", "a ready section id")
                ready = next(
                    (
                        item
                        for item in adapter.get("sections") or []
                        if item.get("id") == section_id
                        and item.get("ready") is True
                        and item.get("in_scope") is True
                    ),
                    None,
                )
                if ready is None:
                    raise ModelError(
                        adapter_id,
                        "section_id",
                        f"a ready in-scope section, not {section_id}",
                    )
                job_id = f"extract-{secrets.token_hex(4)}"
                start_extract_job(
                    ws.root / "jobs",
                    job_id=job_id,
                    root=ws.root,
                    adapter_dir=adapter_dir,
                    section_id=section_id,
                    pack=_pack_for_adapter(adapter),
                )
                document_id = (form.get("document_id") or [""])[0].strip()
                located = f"document={document_id}&" if document_id else ""
                repo_id = (form.get("repo") or [""])[0].strip()
                if repo_id:
                    located += f"repo={quote(repo_id, safe='')}&"
                self._redirect(f"/requirements?{located}job={job_id}&adapter={adapter_id}")
                return
            if path.startswith("/requirements/jobs/") and path.endswith("/abort"):
                job_id = path[len("/requirements/jobs/") : -len("/abort")]
                request_abort(ws.root / "jobs", job_id)
                document_id = (form.get("document") or [""])[0].strip()
                located = f"document={document_id}&" if document_id else ""
                self._redirect(f"/requirements?{located}job={job_id}")
                return
            if path.startswith("/requirements/requirement/") and path.endswith("/sign"):
                requirement_id = path[len("/requirements/requirement/") : -len("/sign")]
                _sign_requirement(ws, requirement_id, form)
                extra = _pack_query(form)
                suffix = f"?{extra}&signed=1" if extra else "?signed=1"
                self._redirect(f"/requirements/requirement/{requirement_id}{suffix}")
                return
            if path.startswith("/requirements/requirement/") and path.endswith("/try-discovery"):
                requirement_id = path[
                    len("/requirements/requirement/") : -len("/try-discovery")
                ]
                job_id = _run_try_discovery(ws, requirement_id, form)
                extra = _pack_query(form)
                suffix = f"?{extra}&try_job={job_id}" if extra else f"?try_job={job_id}"
                self._redirect(f"/requirements/requirement/{requirement_id}{suffix}")
                return
            if path.startswith("/requirements/requirement/"):
                requirement_id = path[len("/requirements/requirement/") :]
                _save_requirement_form(ws, requirement_id, form)
                extra = _pack_query(form)
                suffix = f"?{extra}&saved=1" if extra else "?saved=1"
                self._redirect(f"/requirements/requirement/{requirement_id}{suffix}")
                return
            if path == "/requirements/seal":
                _seal_selected(ws, form)
                self._redirect("/requirements/publish?sealed=1")
                return
            if path == "/requirements/consolidate/apply":
                _apply_consolidation_form(ws, form)
                self._redirect("/requirements/consolidate?merged=1")
                return
            if path == "/requirements/extract/review":
                self._redirect(_apply_extraction_review(ws, form))
                return
            if path == "/requirements/compare/apply":
                _apply_compare_form(ws, form)
                source = (form.get("source") or [""])[0]
                destination = (form.get("destination") or [""])[0]
                self._redirect(f"/requirements/compare?left={source}&right={destination}")
                return
            if path == "/requirements/export":
                _export_selected(self, ws, form)
                return
            if path == "/requirements/publish":
                _publish_selected(ws, form)
                self._redirect("/requirements?published=1")
                return
            if path == "/discover/repos":
                data = load_repos(ws.root)
                add_repo(
                    ws.root,
                    data,
                    name=(form.get("name") or [""])[0],
                    path=(form.get("path") or [""])[0],
                )
                save_repos(ws.root, data)
                new_id = str((data.get("repos") or [])[-1].get("id") or "")
                next_url = _safe_local_next((form.get("next") or [""])[0])
                if next_url:
                    join = "&" if "?" in next_url else "?"
                    if new_id and "try_repo=" not in next_url:
                        next_url = f"{next_url}{join}try_repo={quote(new_id, safe='')}"
                    self._redirect(next_url)
                else:
                    self._redirect("/discover?added=1")
                return
            if path == "/discover/run":
                job_id = _start_discover(ws, form)
                self._redirect(f"/discover?job={job_id}")
                return
            if path.startswith("/discover/jobs/") and path.endswith("/abort"):
                job_id = path[len("/discover/jobs/") : -len("/abort")]
                abort_discover_job(ws.root / "jobs", job_id)
                self._redirect(f"/discover?job={job_id}")
                return
            if path == "/requirement":
                current = load_requirement(_require_demo_requirement(ws))
                edited = apply_edits(current, edits_for_requirement(current, form))
                save_requirement(ws.pack, edited)
                self._redirect("/requirement?saved=1")
                return
            if path == "/publish":
                name = (form.get("name") or [""])[0].strip()
                private, _public = load_or_create_key(ws.keys, name)
                current = load_requirement(_require_demo_requirement(ws))
                published = publish_requirement(current, name=name, private_key=private, at=_now())
                save_requirement(ws.pack, published, published=True)
                self._redirect("/requirement?published=1")
                return
            if path == "/seal-pack":
                name = (form.get("name") or [""])[0].strip()
                private, _public = load_or_create_key(ws.keys, name)
                if not (ws.pack / "pack.json").is_file():
                    raise ModelError(
                        "demo pack",
                        "pack.json",
                        "a prepared sample under packs/cra-baseline/ "
                        "(use Prepare sample workspace on the cover)",
                    )
                seal_pack_directory(ws.pack, name=name, private_key=private, at=_now())
                self._redirect("/requirement?sealed=1")
                return
            if path == "/claims":
                known = list(_claims_lookup(ws, form))
                requirement_id = require_requirement_id(
                    (form.get("requirement_id") or [""])[0],
                    known,
                )
                args = json.loads((form.get("args") or ["{}"])[0])
                checks = json.loads((form.get("checks") or ["[]"])[0])
                if not isinstance(args, dict):
                    raise ModelError("claim", "args", "JSON object")
                if not isinstance(checks, list):
                    raise ModelError("claim", "checks", "JSON list")
                claim = build_claim(
                    claim_id=(form.get("id") or [""])[0].strip(),
                    requirement_id=requirement_id,
                    source=(form.get("source") or [""])[0].strip(),
                    args=args,
                    checks=checks,
                    description=(form.get("description") or [""])[0].strip(),
                    severity=(form.get("severity") or [""])[0].strip() or None,
                )
                claims_dir = _claims_directory(ws, form)
                destination = claims_dir / f"{claim['id']}.json"
                if destination.is_file():
                    raise ModelError("claim", "id", "a new id; an existing Claim is edited explicitly")
                write_claim(claims_dir, claim)
                self._redirect(_claims_redirect(form, f"saved=1&requirement_id={requirement_id}"))
                return
            if path.startswith("/claims/") and path.endswith("/retire"):
                claim_id = path[len("/claims/") : -len("/retire")]
                retire_claim(_claims_directory(ws, form), claim_id)
                self._redirect(_claims_redirect(form, "retired=1"))
                return
            if path.startswith("/claims/") and path.endswith("/sign"):
                claim_id = path[len("/claims/") : -len("/sign")]
                claim = read_claim(_claims_directory(ws, form) / f"{claim_id}.json")
                name = (form.get("name") or [""])[0].strip()
                private, _public = load_or_create_key(ws.keys, name)
                sealed = sign_claim(claim, name=name, private_key=private, at=_now())
                write_claim(_claims_directory(ws, form), sealed)
                self._redirect(
                    _claims_redirect(form, f"signed=1&requirement_id={claim.get('requirement_id', '')}")
                )
                return
            if path.startswith("/claims/"):
                claim_id = path[len("/claims/") :]
                claim = read_claim(_claims_directory(ws, form) / f"{claim_id}.json")
                had_signed = isinstance(claim.get("signed"), dict)
                updated = rebind_from_fields(
                    claim,
                    source=(form.get("source") or [""])[0],
                    args_json=(form.get("args") or ["{}"])[0],
                    checks_json=(form.get("checks") or ["[]"])[0],
                    severity=(form.get("severity") or [""])[0],
                    description=(form.get("description") or [""])[0],
                )
                write_claim(_claims_directory(ws, form), updated)
                flag = "cleared=1" if had_signed and "signed" not in updated else "saved=1"
                self._redirect(
                    _claims_redirect(form, f"{flag}&requirement_id={updated.get('requirement_id', '')}")
                )
                return
            if path == "/scaffold":
                write_stub(ws.repo, (form.get("path") or [""])[0].strip())
                self._redirect("/scaffold?wrote=1")
                return
            if path == "/check":
                repo_id = (form.get("repo_id") or form.get("repo") or [""])[0].strip()
                if repo_id:
                    set_open_repo(ws.root, repo_id)
                action = (form.get("action") or [""])[0].strip()
                if repo_id and action == "save":
                    save_directory_fields(
                        _registered_repo_path(ws, repo_id),
                        packs_dir=(form.get("packs_dir") or [""])[0],
                        claims_dir=(form.get("claims_dir") or [""])[0],
                        results_dir=(form.get("results_dir") or [""])[0],
                        reports_dir=(form.get("reports_dir") or [""])[0],
                    )
                    self._redirect(f"/check?repo={quote(repo_id, safe='')}&saved=1")
                    return
                if repo_id and action == "check":
                    repo = _registered_repo_path(ws, repo_id)
                    from common.validate import validate_curbpack_config

                    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
                    out = new_run_result_path(results_dir(repo, config))
                    result, code = run_and_write(repo, None, out)
                    self._redirect(
                        f"/check?repo={quote(repo_id, safe='')}&exit={code}"
                        f"&result={quote(str(out.resolve()), safe='')}"
                    )
                    return
                self._redirect(f"/check?repo={quote(repo_id, safe='')}" if repo_id else "/check")
                return
            if path == "/review/compile":
                repo_id = _sync_open_repo(ws, form)
                if not repo_id:
                    raise ModelError("review", "repo", "a chosen repository")
                from common.store import load_claims, load_run_result
                from common.validate import validate_curbpack_config

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
                self._redirect(
                    f"/review?repo={quote(repo_id, safe='')}&compiled=1"
                    f"&report={quote(str(out.resolve()), safe='')}"
                )
                return
            if path == "/review":
                repo_id = _sync_open_repo(ws, form)
                if not repo_id:
                    raise ModelError("review", "repo", "a chosen repository")
                from common.validate import validate_curbpack_config

                repo = _registered_repo_path(ws, repo_id)
                config = validate_curbpack_config(read_json(repo / "curbpack.json"))
                report_path = _confined_review_report_path(
                    str(reports_dir(repo, config).resolve()),
                    (form.get("report") or [""])[0],
                )
                if not report_path:
                    raise ModelError("review", "report", "a review-report file under that repository's reports_dir")
                save_report_decision(Path(report_path), (form.get("decision") or [""])[0])
                self._redirect(
                    f"/review?repo={quote(repo_id, safe='')}&saved=1"
                    f"&report={quote(report_path, safe='')}"
                )
                return
            if path == "/review/sign":
                repo_id = _sync_open_repo(ws, form)
                if not repo_id:
                    raise ModelError("review", "repo", "a chosen repository")
                from common.validate import validate_curbpack_config

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
                self._redirect(
                    f"/review?repo={quote(repo_id, safe='')}&signed=1"
                    f"&report={quote(report_path, safe='')}"
                )
                return
            if path == "/studio":
                repo_id = _sync_open_repo(ws, form)
                if not repo_id:
                    raise ModelError("studio", "repo", "a chosen repository")
                action = (form.get("action") or [""])[0].strip()
                if action == "save":
                    save_studio_config(_registered_repo_path(ws, repo_id), studio_from_form(form))
                    self._redirect(f"/studio?repo={quote(repo_id, safe='')}&saved=1")
                    return
                self._redirect(f"/studio?repo={quote(repo_id, safe='')}")
                return
            raise ModelError("request", "path", "a known action")

    return Handler


def _load_adapter(adapter_id: str) -> tuple[Path, dict]:
    adapter_id = str(adapter_id or "").strip() or "cra"
    adapter_dir = ADAPTERS / adapter_id
    path = adapter_dir / "adapter.json"
    if not path.is_file():
        raise ModelError("source", "adapter_id", f"a known adapter, not {adapter_id}")
    return adapter_dir, load_adapter(path)


def _active_adapter(ws: Workspace) -> dict:
    _dir, adapter = _load_adapter(selected_source_adapter(ws.root))
    return adapter


def _pack_for_adapter(adapter: dict) -> dict:
    if adapter.get("id") == "cra":
        return draft_pack()
    return {
        "id": adapter["pack_id"],
        "name": f"{adapter['id']} extract",
        "version": "0.1.0",
    }


def _catalog_message(query: dict, *, added: str) -> str:
    if (query.get("added") or [""])[0]:
        return added
    if (query.get("updated") or [""])[0]:
        return "Pack info saved."
    if (query.get("extracted") or [""])[0]:
        return "Extraction finished."
    if (query.get("brought") or [""])[0]:
        return "Updated the fields you chose. The working copy you were editing stays selected."
    if (query.get("aborted") or [""])[0]:
        return "Extraction aborted. Earlier working copies are unchanged."
    if (query.get("published") or [""])[0]:
        return "Published a new release. The working copy was not overwritten."
    if (query.get("selected") or [""])[0]:
        return "Working copy selected."
    return ""


def _home_message(query: dict) -> str:
    if (query.get("selected") or [""])[0]:
        return "Active Pack updated."
    if (query.get("prepared") or [""])[0]:
        return "Sample workspace prepared. It is not the active Pack unless you select it."
    return ""


def _home_model(ws: Workspace) -> dict:
    ensure_default_selection(ws.root)
    selection = read_selection(ws.root)
    if selection and isinstance(selection.get("pack_id"), str):
        _sync_adapter_for_pack(ws, selection["pack_id"])
    options = []
    for item in list_pack_options(ws.root):
        selected = False
        if selection and selection.get("kind") == item["kind"] and selection.get("pack_id") == item["pack_id"]:
            if item["kind"] == "working":
                selected = selection.get("timestamp") == item["ref"]
            else:
                selected = selection.get("version") == item["ref"]
        options.append({**{key: value for key, value in item.items() if key != "path"}, "selected": selected})
    info = snapshot(ws.root)
    return {
        "selection": selection if resolve_selected_pack(ws.root) else None,
        "options": options,
        "report_line": _report_line(info),
    }


def _report_line(info: dict) -> str:
    if info.get("report_error"):
        return str(info["report_error"])
    reading = info.get("report_reading")
    if not isinstance(reading, dict):
        return "No review report."
    verified = "yes" if reading.get("verifiable") else "no"
    text = f"Report: {reading.get('what')} verifiable {verified}."
    if info.get("same_run") is True:
        text += " same run: yes."
    elif info.get("same_run") is False:
        text += " same run: no."
    return text


def _apply_pack_selection(ws: Workspace, form: dict) -> Path:
    packed = (form.get("pack") or [""])[0].strip()
    kind = (form.get("kind") or [""])[0].strip()
    pack_id = (form.get("pack_id") or [""])[0].strip()
    ref = (form.get("ref") or [""])[0].strip()
    if packed and "|" in packed:
        kind, pack_id, ref = packed.split("|", 2)
    if not kind or not pack_id or not ref:
        raise ModelError("active pack", "selection", "kind, pack_id, and ref")
    _sync_adapter_for_pack(ws, pack_id)
    if kind == "working":
        return mark_selected(ws.root, pack_id, ref)
    if kind == "published":
        return mark_published_selected(ws.root, pack_id, ref)
    raise ModelError("active pack", "kind", "working or published")


def _sync_adapter_for_pack(ws: Workspace, pack_id: str) -> None:
    for item in list_adapters():
        if item.get("pack_id") == pack_id:
            mark_source_adapter(ws.root, item["id"])
            return


def _discover_model(ws: Workspace, query: dict, *, product: bool = False) -> dict:
    job = None
    job_id = (query.get("job") or [""])[0]
    if job_id:
        job = read_discover_job(ws.root / "jobs", job_id)
    repos = _listed_repos(ws)
    repo_id = _sync_open_repo(ws, query)
    repo = find_repo({"repos": repos}, repo_id) if repo_id else None
    fields = _door_path_fields(ws, repo_id) if repo_id else {}
    return {
        "mode": "product" if product else "pilot",
        "repo_id": str((repo or {}).get("id") or ""),
        "repo_name": str((repo or {}).get("name") or ""),
        "repos": repos,
        "sections": _discover_sections(ws, repo, product=product) if repo else [],
        "reviewable": reviewable_targets(ws.root),
        "job": job,
        "error": (query.get("error") or [""])[0],
        "workspace_root": str(ws.root.resolve()),
        "curbpack_file": fields.get("curbpack_file") or "",
        "directory": fields.get("directory") or "",
        "claims_dir": fields.get("claims_dir") or "",
        "results_dir": fields.get("results_dir") or "",
        "reports_dir": fields.get("reports_dir") or "",
        "packs_dir_value": fields.get("packs_dir_value") or "",
        "claims_dir_value": fields.get("claims_dir_value") or "",
        "results_dir_value": fields.get("results_dir_value") or "",
        "reports_dir_value": fields.get("reports_dir_value") or "",
    }


def _discover_sections(ws: Workspace, repo: dict | None, *, product: bool) -> list[dict]:
    packs: set[str] | None = None
    repo_path: Path | None = None
    if isinstance(repo, dict):
        try:
            repo_path = resolve_repo_path(ws.root, str(repo.get("path") or ""))
        except ModelError:
            repo_path = None
    if product:
        packs = _curbpack_pack_ids(repo_path)
    sections = []
    for source in _registered_sources(ws):
        pack_id = source.get("pack_id")
        if not isinstance(pack_id, str) or not pack_id:
            continue
        if packs is not None and pack_id not in packs:
            continue
        choices = _copy_choices(ws.root, pack_id)
        for choice in choices:
            requirements, claims, unclaimed = _copy_claim_counts(
                ws.root, repo_path, pack_id, choice["value"]
            )
            choice["requirements"] = requirements
            choice["claims"] = claims
            choice["unclaimed"] = unclaimed
        if product:
            choices = [choice for choice in choices if choice.get("chosen")][:1]
        sections.append(
            {
                "source_id": source.get("source_id") or "",
                "name": source.get("name") or "",
                "section_id": source.get("section_id") or "",
                "pack_id": pack_id,
                "copies": choices,
            }
        )
    return sections


def _curbpack_pack_ids(repo: Path | None) -> set[str]:
    if repo is None:
        return set()
    path = repo / "curbpack.json"
    if not path.is_file():
        return set()
    document = read_json(path)
    if not isinstance(document, dict):
        return set()
    return {item for item in document.get("packs") or [] if isinstance(item, str) and item}


def _copy_choices(root: Path, pack_id: str) -> list[dict]:
    """The selected working copy, or the latest one, plus every published release."""
    selection = read_selection(root)
    stamps = list_working_copies(root, pack_id)
    published = list_published_versions(root, pack_id)
    selected_here = (
        isinstance(selection, dict)
        and selection.get("pack_id") == pack_id
    )
    published_version = ""
    if selected_here and selection.get("kind") == "published" and selection.get("version") in published:
        published_version = selection["version"]
    working_stamp = ""
    if selected_here and selection.get("kind") == "working" and selection.get("timestamp") in stamps:
        working_stamp = selection["timestamp"]
    elif stamps:
        working_stamp = stamps[-1]
    choices = []
    if working_stamp:
        choices.append(
            {
                "value": working_stamp,
                "label": f"Working copy · {working_stamp}",
                "chosen": not published_version,
            }
        )
    for version in published:
        choices.append(
            {
                "value": f"published:{version}",
                "label": f"Published · {version}",
                "chosen": version == published_version,
            }
        )
    return choices


def _copy_claim_counts(root: Path, repo: Path | None, pack_id: str, ref: str) -> tuple[int, int, int]:
    """Requirement count, claim count, and requirements that have no claim."""
    if repo is None:
        return 0, 0, 0
    try:
        offered = repo_pack_requirements(repo, pack_id)
        ids = {item["id"] for item in offered}
    except ModelError:
        ids = set()
    try:
        folder = repo_claims_dir(repo)
        claims = read_claims(folder) if folder.is_dir() else []
    except ModelError:
        claims = []
    claim_count = sum(
        1
        for claim in claims
        if isinstance(claim, dict) and claim.get("requirement_id") in ids
    )
    claimed = {
        claim.get("requirement_id")
        for claim in claims
        if isinstance(claim, dict)
    }
    unclaimed = sum(1 for requirement_id in ids if requirement_id not in claimed)
    return len(ids), claim_count, unclaimed


def _start_discover(ws: Workspace, form: dict) -> str:
    repo_id = (form.get("repo_id") or [""])[0].strip()
    source_id = (form.get("source_id") or [""])[0].strip()
    timestamp = (form.get("timestamp") or [""])[0].strip()
    data = load_repos(ws.root)
    row = find_repo(data, repo_id)
    if row is None:
        raise ModelError("discover", "repo_id", f"a registered repository, not {repo_id}")
    source = next((item for item in _registered_sources(ws) if item.get("source_id") == source_id), None)
    if source is None:
        raise ModelError("discover", "source_id", f"a registered source, not {source_id}")
    pack_id = source.get("pack_id")
    if not isinstance(pack_id, str) or not pack_id:
        raise ModelError("discover", "pack_id", "a pack id on the source")
    if not timestamp:
        raise ModelError("discover", "timestamp", "a working copy or published release")
    resolve_copy_ref(ws.root, pack_id, timestamp)
    repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
    requirements = repo_pack_requirements(repo, pack_id)
    from common.validate import validate_curbpack_config

    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    hunt = {"search_hints": config.get("search_hints") or {}}
    title = f"Discover — {row.get('name') or repo_id} / {source.get('name') or source_id} {source.get('section_id') or ''}"
    raw_limit = (form.get("assess_limit") or ["5"])[0].strip() or "5"
    if not raw_limit.isdigit():
        raise ModelError("discover", "assess_limit", "an integer from 0 to 20")
    job_id = f"discover-{secrets.token_hex(4)}"
    start_discover_job(
        ws.root / "jobs",
        job_id=job_id,
        workspace=ws.root,
        repo_id=repo_id,
        repo=repo,
        requirements=requirements,
        hunt=hunt,
        title=title.strip(),
        source_id=source_id,
        timestamp=timestamp,
        assess_limit=int(raw_limit),
        complete=getattr(ws, "discover_complete", None),
    )
    return job_id


def _formex_sources() -> list[dict]:
    rows = []
    for item in list_adapters():
        if item.get("source_format") != "formex":
            continue
        sections = list(item.get("sections") or [])
        ready = [
            section
            for section in sections
            if section.get("ready") is True and section.get("in_scope") is True
        ]
        rows.append(
            {
                "id": item["id"],
                "status": item["status"],
                "source_format": item["source_format"],
                "pack_id": item.get("pack_id"),
                "source": item.get("source") or {},
                "sections": sections,
                "ready_count": len(ready),
            }
        )
    return rows


def _copy_rows(root: Path, pack_id: str) -> list[dict]:
    stamps = list_working_copies(root, pack_id)
    selected = selected_copy(root, pack_id)
    selected_name = selected.name if selected is not None else None
    chosen = selected_name or (stamps[-1] if stamps else None)
    rows = []
    for index, stamp in enumerate(stamps):
        directory = select_working_copy(root, pack_id, stamp)
        rows.append(
            {
                "timestamp": stamp,
                "latest": index == len(stamps) - 1,
                "selected": stamp == selected_name,
                "chosen": stamp == chosen,
                "coverage_status": _coverage_status(directory),
            }
        )
    return rows


def _coverage_status(directory: Path) -> str:
    document = _coverage_document(directory)
    status = document.get("status") if isinstance(document, dict) else None
    return status if isinstance(status, str) and status else "none"


def _coverage_document(directory: Path) -> dict | None:
    path = work_directory(directory) / "coverage.json"
    if not path.is_file():
        return None
    document = read_json(path)
    return document if isinstance(document, dict) else None


def _coverage_detail(directory: Path) -> dict | None:
    document = _coverage_document(directory)
    if not isinstance(document, dict):
        return None
    return {
        "status": document.get("status"),
        "loci": document.get("loci") if isinstance(document.get("loci"), list) else [],
        "error": document.get("error"),
        "source_diagnostics": document.get("source_diagnostics")
        if isinstance(document.get("source_diagnostics"), list)
        else [],
    }


def _registered_sources(ws: Workspace) -> list[dict]:
    adapters = {item["id"]: item for item in _formex_sources()}
    catalog = ensure_catalog(ws.root)
    sources = []
    for row in catalog.get("sources") or []:
        adapter_id = str(row.get("adapter_id") or "")
        adapter = adapters.get(adapter_id)
        if adapter is None:
            continue
        section_id = str(row.get("section_id") or "")
        section = next(
            (item for item in adapter.get("sections") or [] if item.get("id") == section_id),
            None,
        )
        pack_id = adapter.get("pack_id")
        signed_count, unsigned_count = _signature_counts(
            ws.root, pack_id if isinstance(pack_id, str) else "", trust_store(ws.keys)
        )
        sources.append(
            {
                "source_id": row.get("id"),
                "name": row.get("name") or "",
                "official_name": row.get("official_name") or "",
                "url": row.get("url") or (adapter.get("source") or {}).get("url") or "",
                "document_id": row.get("document_id") or "",
                "adapter_id": adapter_id,
                "section_id": section_id,
                "section_ready": bool(section and section.get("ready") and section.get("in_scope")),
                "status": adapter.get("status"),
                "source_format": adapter.get("source_format"),
                "pack_id": pack_id,
                "source": adapter.get("source") or {},
                "copies": _copy_rows(ws.root, pack_id) if isinstance(pack_id, str) else [],
                "signed_count": signed_count,
                "unsigned_count": unsigned_count,
            }
        )
    return sources


def _export_model(ws: Workspace, query: dict) -> dict:
    document_id = (query.get("document") or [""])[0].strip()
    document, pack_id, directory = _export_document(ws, document_id)
    exported = (query.get("exported") or [""])[0]
    model = {
        "document_id": document_id,
        "document_name": str(document.get("name") or ""),
        "pack_id": pack_id,
        "timestamp": None,
        "signed": 0,
        "unsigned": 0,
        "seal": None,
        "blocked": [],
        "destination": (query.get("destination") or [""])[0],
        "conflict": (query.get("conflict") or [""])[0],
        "message": f"Exported Pack {exported}" if exported else "",
    }
    if directory is None:
        return model
    trust = trust_store(ws.keys)
    pack, requirements = load_working_copy(directory)
    signed = 0
    unsigned = 0
    blocked = []
    for requirement in requirements:
        reading = read_signature(requirement, trust, what="requirement")
        if reading.get("verifiable"):
            signed += 1
        elif isinstance(requirement.get("signed"), dict):
            blocked.append(
                {"title": str(requirement.get("id") or "Requirement"), "reading": reading}
            )
        else:
            unsigned += 1
    model.update(
        {
            "timestamp": directory.name,
            "signed": signed,
            "unsigned": unsigned,
            "seal": read_pack_seal(directory, trust),
            "blocked": blocked,
            "pack_version": pack.get("version"),
        }
    )
    return model


def _export_document(ws: Workspace, document_id: str) -> tuple[dict, str, Path | None]:
    """Catalog document, its adapter pack id, and the selected working copy only."""
    if not document_id:
        raise ModelError("export", "document", "a catalog document")
    document = find_document(ensure_catalog(ws.root), document_id)
    if document is None:
        raise ModelError("catalog", "document", f"a known document, not {document_id}")
    adapters = {item["id"]: item for item in _formex_sources()}
    adapter = adapters.get(str(document.get("adapter_id") or ""))
    pack_id = adapter.get("pack_id") if isinstance(adapter, dict) else None
    if not isinstance(pack_id, str) or not pack_id:
        raise ModelError("export", "pack_id", "one adapter pack id")
    return document, pack_id, selected_copy(ws.root, pack_id)


def _export_selected(handler, ws: Workspace, form: dict) -> None:
    document_id = (form.get("document") or [""])[0].strip()
    destination_text = (form.get("destination") or [""])[0].strip()
    overwrite = (form.get("overwrite") or [""])[0] == "1"
    if not destination_text:
        raise ModelError("export", "destination", "an existing directory")
    _document, pack_id, directory = _export_document(ws, document_id)
    if directory is None:
        raise ModelError(
            "export",
            "selection",
            f"No working copy is selected for {pack_id}",
        )
    try:
        final = export_pack(directory, Path(destination_text), overwrite=overwrite)
    except ModelError as exc:
        if exc.field == "destination" and "free directory, not " in exc.expected:
            conflict = exc.expected.split("free directory, not ", 1)[1]
            handler._redirect(
                "/requirements/export?document="
                + quote(document_id, safe="")
                + "&destination="
                + quote(destination_text, safe="")
                + "&conflict="
                + quote(conflict, safe="")
            )
            return
        raise
    handler._redirect(
        "/requirements/export?document="
        + quote(document_id, safe="")
        + "&exported="
        + quote(str(final), safe="")
    )


def _sync_open_repo(ws: Workspace, query: dict | None = None, repo_id: str = "") -> str:
    chosen = (repo_id or "").strip()
    if not chosen and query:
        chosen = (query.get("repo") or query.get("repo_id") or [""])[0].strip()
    if chosen:
        set_open_repo(ws.root, chosen)
    return open_repo_id(ws.root) or ""


def _listed_repos(ws: Workspace) -> list[dict]:
    return [
        row
        for row in (load_repos(ws.root).get("repos") or [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]


def _studio_message(query: dict) -> str:
    if (query.get("saved") or [""])[0]:
        return "Saved curbpack-studio.json in the repo."
    return ""


def _studio_model(ws: Workspace, query: dict) -> dict:
    door = _door_chrome(ws, query)
    repo_id = str(door.get("repo_id") or "")
    values = editor_values(created_studio_config())
    present = False
    path = ""
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        path = str(studio_file(repo).resolve())
        if studio_file(repo).is_file():
            present = True
            values = editor_values(read_json(studio_file(repo)))
    return {"door": door, "values": values, "present": present, "path": path}


def _door_chrome(ws: Workspace, query: dict | None = None) -> dict:
    repo_id = _sync_open_repo(ws, query)
    fields = _door_path_fields(ws, repo_id) if repo_id else {}
    return {"repos": _listed_repos(ws), "repo_id": repo_id, **fields}


def _door_path_fields(ws: Workspace, repo_id: str) -> dict:
    if not repo_id:
        return {}
    repo = _registered_repo_path(ws, repo_id)
    config_path = repo / "curbpack.json"
    fields = {
        "curbpack_file": str(config_path.resolve()) if config_path.is_file() else str(config_path),
        "directory": "",
        "claims_dir": "",
        "results_dir": "",
        "reports_dir": "",
        "packs_dir_value": "",
        "claims_dir_value": "",
        "results_dir_value": "",
        "reports_dir_value": "",
    }
    opened = open_paths(ws.root)
    if not opened:
        return fields
    if opened.get("packs_dir") is not None:
        fields["directory"] = str(opened["packs_dir"])
    if opened.get("claims_dir") is not None:
        fields["claims_dir"] = str(opened["claims_dir"])
    if opened.get("results_dir") is not None:
        fields["results_dir"] = str(opened["results_dir"])
    if opened.get("reports_dir") is not None:
        fields["reports_dir"] = str(opened["reports_dir"])
    if config_path.is_file():
        from common.validate import validate_curbpack_config

        config = validate_curbpack_config(read_json(config_path))
        fields["packs_dir_value"] = str(config["packs_dir"])
        fields["claims_dir_value"] = str(config["claims_dir"])
        fields["results_dir_value"] = str(config["results_dir"])
        fields["reports_dir_value"] = str(config["reports_dir"])
    return fields


def _save_curbpack_form(repo: Path, form: dict) -> None:
    from common.validate import validate_curbpack_config

    packs = [
        item.strip()
        for item in ((form.get("packs") or [""])[0]).split(",")
        if item.strip()
    ]
    exclude = [
        item.strip()
        for item in ((form.get("exclude_requirements") or [""])[0]).split(",")
        if item.strip()
    ]
    hints_raw = (form.get("search_hints") or [""])[0]
    try:
        hints = json.loads(hints_raw) if hints_raw.strip() else created_curbpack()["search_hints"]
    except json.JSONDecodeError:
        raise ModelError("curbpack.json", "search_hints", "JSON object")
    document: dict = {
        "packs": packs,
        "search_hints": hints,
        "packs_dir": (form.get("packs_dir") or [""])[0].strip(),
        "claims_dir": (form.get("claims_dir") or [""])[0].strip(),
        "results_dir": (form.get("results_dir") or [""])[0].strip(),
        "reports_dir": (form.get("reports_dir") or [""])[0].strip(),
        "unsigned_requirements": (form.get("unsigned_requirements") or [""])[0].strip(),
    }
    path = repo / "curbpack.json"
    if path.is_file():
        loaded = read_json(path)
        if isinstance(loaded, dict) and "requirements" in loaded and not exclude:
            document["requirements"] = loaded["requirements"]
    if exclude:
        document["exclude_requirements"] = exclude
        document.pop("requirements", None)
    write_json(path, validate_curbpack_config(document))


def _documents_model(ws: Workspace, query: dict) -> dict:
    repos = [
        row
        for row in (load_repos(ws.root).get("repos") or [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    repo_id = _sync_open_repo(ws, query)
    documents: list[dict] = []
    curbpack_file = ""
    directory = ""
    claims_directory = ""
    file_absent = False
    no_claims = False
    config: dict = {}
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        config_path = repo / "curbpack.json"
        curbpack_file = str(config_path.resolve()) if config_path.is_file() else str(config_path)
        if not config_path.is_file():
            file_absent = True
        else:
            from common.validate import validate_curbpack_config

            config = validate_curbpack_config(read_json(config_path))
            packs_root = packs_dir(repo, config)
            directory = str(packs_root.resolve())
            claims_root = claims_dir(repo, config)
            claims_directory = str(claims_root.resolve())
            no_claims = not claims_root.is_dir() or not any(claims_root.glob("*.json"))
            for pack_id in config["packs"]:
                try:
                    pack_dir = _pack_version_dir(packs_root, pack_id)
                except ModelError:
                    documents.append(
                        {
                            "id": pack_id,
                            "name": pack_id,
                            "missing": True,
                            "adapter_id": "manual",
                            "extract_enabled": False,
                            "pack_dir": str((packs_root / pack_id).resolve()),
                            "repo_id": repo_id,
                        }
                    )
                    continue
                pack_file = pack_dir / "pack.json"
                pack = read_json(pack_file)
                source = pack.get("source") if isinstance(pack, dict) else {}
                if not isinstance(source, dict):
                    source = {}
                if not isinstance(pack, dict):
                    pack = {}
                url = str(source.get("url") or "")
                adapter = _adapter_for_url(url)
                documents.append(
                    {
                        "id": pack_id,
                        "name": str(pack.get("name") or pack_id),
                        "official_name": str(source.get("instrument") or ""),
                        "url": url,
                        "adapter_id": str(adapter.get("id") or "") if adapter else "manual",
                        "extract_enabled": adapter is not None,
                        "pack_dir": str(pack_dir.resolve()),
                        "repo_id": repo_id,
                    }
                )
    return {
        "documents": documents,
        "repos": repos,
        "repo_id": repo_id,
        "curbpack_file": curbpack_file,
        "directory": directory,
        "claims_dir": claims_directory,
        "results_dir": str(results_dir(_registered_repo_path(ws, repo_id), config)) if repo_id and config else "",
        "reports_dir": str(reports_dir(_registered_repo_path(ws, repo_id), config)) if repo_id and config else "",
        "file_absent": file_absent,
        "no_claims": no_claims,
        "curbpack_fields": config if config else created_curbpack(),
        "show_curbpack_dialog": file_absent or (query.get("curbpack") or [""])[0] == "edit",
        "adapters": list_formex_adapter_choices(),
        "edit_adapters": _edit_adapter_choices(),
        "workspace_root": str(ws.root.resolve()),
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Pack added."),
        "error": (query.get("error") or [""])[0],
    }


def _start_empty_folder(ws: Workspace, folder: str) -> str:
    raw = (folder or "").strip()
    if not raw:
        raise ModelError("curbpack.json", "folder", "a working folder")
    resolved = resolve_repo_path(ws.root, raw)
    resolved.mkdir(parents=True, exist_ok=True)
    target = resolved / "curbpack.json"
    data = load_repos(ws.root)
    name = resolved.name or "repo"
    try:
        data = add_repo(ws.root, data, name=name, path=str(resolved))
        save_repos(ws.root, data)
        repo_id = str((data.get("repos") or [])[-1].get("id") or "")
    except ModelError:
        repo_id = ""
        for row in data.get("repos") or []:
            if resolve_repo_path(ws.root, str(row.get("path") or "")) == resolved:
                repo_id = str(row.get("id") or "")
                break
        if not repo_id:
            raise
    if target.exists() and not target.is_file():
        raise ModelError("curbpack.json", "folder", "a working folder")
    set_open_repo(ws.root, repo_id)
    return repo_id


def _add_pack_to_repo(
    ws: Workspace,
    repo_id: str,
    *,
    name: str,
    official_name: str,
    url: str,
    adapter_id: str = "",
) -> None:
    from common.validate import validate_pack

    repo = _registered_repo_path(ws, repo_id)
    config_path = repo / "curbpack.json"
    if not config_path.is_file():
        raise ModelError("curbpack.json", "repo", "a curbpack.json in the chosen repository")
    raw = read_json(config_path)
    config = raw if isinstance(raw, dict) else {}
    pack_id = make_document_id(name)
    from common.validate import validate_curbpack_config
    from requirements.extract.pipeline import draft_pack

    checked = validate_curbpack_config(config)
    wanted = (adapter_id or "").strip()
    inferred = _adapter_for_url(url.strip()) if url.strip() else None
    if wanted and (inferred is None or str(inferred.get("id") or "") != wanted):
        raise ModelError("pack", "adapter", "the adapter that matches this URL")
    pack_dir = packs_dir(repo, checked) / pack_id / draft_pack()["version"]
    if (pack_dir / "pack.json").is_file():
        raise ModelError("pack", "id", f"a new pack, not existing {pack_id}")
    pack: dict = {"id": pack_id, "name": name.strip(), "version": draft_pack()["version"]}
    source = {}
    if official_name.strip():
        source["instrument"] = official_name.strip()
    if url.strip():
        source["url"] = url.strip()
    if source:
        pack["source"] = source
    checked_pack = validate_pack(pack)
    pack_dir.mkdir(parents=True, exist_ok=True)
    write_json(pack_dir / "pack.json", checked_pack)
    packs = [item for item in config.get("packs") or [] if isinstance(item, str)]
    if pack_id not in packs:
        packs.append(pack_id)
    _write_curbpack(repo, packs)


def _update_pack_info(
    ws: Workspace,
    repo_id: str,
    pack_id: str,
    *,
    name: str,
    official_name: str,
    url: str,
    adapter_id: str = "",
) -> None:
    """Write name and source on an existing pack.json. Does not add a field for the adapter."""
    from common.validate import validate_pack

    located = _locate_repo_pack(ws, (pack_id or "").strip(), repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    _chosen, pack_dir, pack = located
    wanted = (adapter_id or "").strip()
    cleaned_url = "" if wanted == "manual" else url.strip()
    inferred = _adapter_for_url(cleaned_url) if cleaned_url else None
    if wanted and wanted != "manual" and (
        inferred is None or str(inferred.get("id") or "") != wanted
    ):
        raise ModelError("pack", "adapter", "the adapter that matches this URL")
    if name.strip():
        pack["name"] = name.strip()
    source = dict(pack["source"]) if isinstance(pack.get("source"), dict) else {}
    official = official_name.strip()
    if official:
        source["instrument"] = official
    else:
        source.pop("instrument", None)
    if cleaned_url:
        source["url"] = cleaned_url
    else:
        source.pop("url", None)
    if source:
        pack["source"] = source
    else:
        pack.pop("source", None)
    write_json(pack_dir / "pack.json", validate_pack(pack))


def _signature_counts(root: Path, pack_id: str, trust: dict) -> tuple[int | None, int | None]:
    """Signed and unsigned requirements in the chosen working copy. None when there are none."""
    if not pack_id:
        return None, None
    chosen = next((row for row in _copy_rows(root, pack_id) if row.get("chosen")), None)
    if chosen is None:
        return None, None
    directory = select_working_copy(root, pack_id, str(chosen.get("timestamp") or ""))
    _pack, requirements = load_working_copy(directory)
    if not requirements:
        return None, None
    signed = 0
    for requirement in requirements:
        reading = read_signature(requirement, trust, what="requirement")
        if reading.get("verifiable"):
            signed += 1
    return signed, len(requirements) - signed


def _signature_mark(root: Path, pack_id: str, trust: dict) -> tuple[bool, str]:
    """Whether every requirement in the chosen working copy has a verifiable signature."""
    if not pack_id:
        return False, "No working copy yet."
    chosen = next((row for row in _copy_rows(root, pack_id) if row.get("chosen")), None)
    if chosen is None:
        return False, "No working copy yet."
    directory = select_working_copy(root, pack_id, str(chosen.get("timestamp") or ""))
    _pack, requirements = load_working_copy(directory)
    if not requirements:
        return False, "The working copy has no requirements."
    for requirement in requirements:
        reading = read_signature(requirement, trust, what="requirement")
        if not reading.get("verifiable"):
            return False, "A requirement in the selected working copy is unsigned."
    return True, "All requirements in the selected working copy are signed."


def _pack_query(params: dict) -> str:
    repo = (params.get("repo") or [""])[0].strip()
    pack = (params.get("pack") or [""])[0].strip()
    if not repo or not pack:
        return ""
    return f"repo={quote(repo, safe='')}&pack={quote(pack, safe='')}"


def _locate_repo_pack(ws: Workspace, pack_id: str, repo_id: str = "") -> tuple[str, Path, dict] | None:
    """Pack named in a registered repo's curbpack.json, with its pack.json."""
    if not pack_id:
        return None
    chosen = (repo_id or "").strip() or open_repo_id(ws.root) or ""
    if not chosen:
        return None
    row = find_repo(load_repos(ws.root), chosen)
    if row is None:
        raise ModelError("pack", "repo", f"a registered repository, not {chosen}")
    repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
    config_path = repo / "curbpack.json"
    if not config_path.is_file():
        return None
    from common.validate import validate_curbpack_config

    config = validate_curbpack_config(read_json(config_path))
    if pack_id not in config["packs"]:
        return None
    try:
        pack_dir = _pack_version_dir(packs_dir(repo, config), pack_id)
    except ModelError:
        return None
    pack_file = pack_dir / "pack.json"
    if not pack_file.is_file():
        return None
    pack = read_json(pack_file)
    if not isinstance(pack, dict):
        return None
    return chosen, pack_dir, pack


def _edit_adapter_choices() -> list[dict]:
    """Adapters a pack row can switch to. Manual Content is added by the dialog."""
    rows = []
    for item in list_adapters():
        if str(item.get("id") or "") == "manual":
            continue
        legal = item.get("source") if isinstance(item.get("source"), dict) else {}
        url = str(legal.get("url") or "")
        if not url:
            continue
        rows.append(
            {
                "id": item.get("id"),
                "instrument": str(legal.get("instrument") or item.get("id") or ""),
                "url": url,
            }
        )
    return rows


def _adapter_for_url(url: str) -> dict | None:
    wanted = (url or "").strip()
    if not wanted:
        return None
    matches = []
    for item in list_adapters():
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        if str(source.get("url") or "").strip() == wanted:
            matches.append(item)
    if not matches:
        return None
    formex = [item for item in matches if item.get("source_format") == "formex"]
    return (formex or matches)[0]


def _requirement_locators(requirement: dict) -> list[str]:
    return [
        str(ref.get("locator"))
        for ref in requirement.get("references") or []
        if isinstance(ref, dict) and ref.get("locator")
    ]


def _requirement_section(requirement: dict) -> str:
    locators = _requirement_locators(requirement)
    return locators[0] if locators else ""


def _adapter_section_ids(adapter: dict) -> list[str]:
    return [
        str(section.get("id"))
        for section in adapter.get("sections") or []
        if isinstance(section, dict) and section.get("id")
    ]


def _locator_section(locator: str, section_ids: list[str]) -> str:
    """Adapter section that contains this locator. `VII.3` belongs to `VII`."""
    best = ""
    for section_id in section_ids:
        if locator == section_id or locator.startswith(section_id + ".") or locator.startswith(section_id + "("):
            if len(section_id) > len(best):
                best = section_id
    return best


def _sections_with_requirements(requirements: list[dict], section_ids: list[str]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        for locator in _requirement_locators(requirement):
            section_id = _locator_section(locator, section_ids)
            if not section_id or section_id in seen:
                continue
            seen.add(section_id)
            found.append(section_id)
    return found


def _requirement_in_section(requirement: dict, section: str, section_ids: list[str]) -> bool:
    locators = _requirement_locators(requirement)
    if not section_ids:
        return section in locators
    return any(_locator_section(locator, section_ids) == section for locator in locators)


def _sections_named_by_locators(requirements: list[dict]) -> list[str]:
    """Section names written in locator when the pack has no adapter."""
    names = []
    seen = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        section_id = _requirement_section(requirement)
        if not section_id or section_id in seen:
            continue
        seen.add(section_id)
        names.append(section_id)
    return sorted(names)


def _pack_has_requirements(pack_dir: Path) -> bool:
    return any(path.name != "pack.json" for path in pack_dir.glob("*.json"))


def _add_pack_section(ws: Workspace, pack_id: str, repo_id: str, section_id: str) -> None:
    """Remember a section on this Pack. Does not write a Requirement."""
    section_id = (section_id or "").strip()
    if not section_id:
        raise ModelError("pack", "section_id", "a section id")
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    _repo_id, _pack_dir, pack = located
    source = pack.get("source") if isinstance(pack.get("source"), dict) else {}
    url = str(source.get("url") or "")
    adapter = _adapter_for_url(url)
    if adapter is None:
        raise ModelError("pack", "adapter", "an adapter for this pack")
    match = next(
        (
            item
            for item in adapter.get("sections") or []
            if isinstance(item, dict)
            and item.get("id") == section_id
            and item.get("ready") is True
            and item.get("in_scope") is True
        ),
        None,
    )
    if match is None:
        raise ModelError("pack", "section_id", "a section that can be extracted")
    catalog = ensure_catalog(ws.root)
    for row in catalog.get("sources") or []:
        if (
            isinstance(row, dict)
            and row.get("document_id") == pack_id
            and row.get("section_id") == section_id
        ):
            return
    catalog.setdefault("sources", []).append(
        {
            "id": make_id(str(adapter.get("id") or ""), section_id),
            "document_id": pack_id,
            "name": str(pack.get("name") or pack_id),
            "official_name": str(match.get("title") or ""),
            "url": url,
            "adapter_id": adapter.get("id"),
            "section_id": section_id,
        }
    )
    save_catalog(ws.root, catalog)


def _repo_pack_sections_model(ws: Workspace, query: dict, pack_id: str) -> dict:
    """Sections of a pack named in curbpack.json. Not a registered_sources document."""
    repo_id = (query.get("repo") or [""])[0].strip()
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("catalog", "document", f"a known document, not {pack_id}")
    found_repo, pack_dir, pack = located
    source = pack.get("source") if isinstance(pack.get("source"), dict) else {}
    url = str(source.get("url") or "")
    adapter = _adapter_for_url(url)
    if adapter is None:
        _adapter_dir, adapter = _load_adapter("manual")
    has_requirements = _pack_has_requirements(pack_dir)
    document = {
        "id": pack_id,
        "name": str(pack.get("name") or pack_id),
        "official_name": str(source.get("instrument") or ""),
        "url": url,
        "adapter_id": str(adapter.get("id") or ""),
        "repo_id": found_repo,
    }
    ready_sections = [
        section
        for section in adapter.get("sections") or []
        if isinstance(section, dict)
        and section.get("ready") is True
        and section.get("in_scope") is True
    ]
    ready_ids = {str(section.get("id") or "") for section in ready_sections}
    manual = adapter.get("id") == "manual"
    shown: set[str] = set()
    sources: list[dict] = []
    requirements: list[dict] = []
    if has_requirements:
        _loaded, requirements = load_pack_directory(pack_dir)
    if manual:
        for section_id in _sections_named_by_locators(requirements):
            if section_id in shown:
                continue
            shown.add(section_id)
            extractable = section_id in ready_ids
            sources.append(
                {
                    "adapter_id": str(adapter.get("id") or ""),
                    "source_id": make_id("section", section_id),
                    "section_id": section_id,
                    "url": url,
                    "extract_enabled": extractable,
                    "section_ready": True if extractable else None,
                    "source_format": adapter.get("source_format") or "",
                    "document_id": pack_id,
                    "pack_dir": str(pack_dir.resolve()),
                    "copies": [],
                    "repo_id": found_repo,
                    "edit_repo": found_repo,
                    "edit_pack": pack_id,
                    "edit_section": section_id,
                    "signed_count": None,
                    "unsigned_count": None,
                }
            )
    else:
        section_ids = _adapter_section_ids(adapter)
        for section_id in _sections_with_requirements(requirements, section_ids):
            if section_id in shown:
                continue
            shown.add(section_id)
            extractable = section_id in ready_ids
            sources.append(
                {
                    "adapter_id": str(adapter.get("id") or ""),
                    "source_id": f"{adapter.get('id')}-{section_id}",
                    "section_id": section_id,
                    "url": url,
                    "extract_enabled": extractable,
                    "section_ready": True if extractable else False,
                    "source_format": adapter.get("source_format") or "",
                    "document_id": pack_id,
                    "pack_dir": str(pack_dir.resolve()),
                    "copies": [],
                    "repo_id": found_repo,
                    "edit_repo": found_repo,
                    "edit_pack": pack_id,
                    "edit_section": section_id,
                    "signed_count": None,
                    "unsigned_count": None,
                }
            )
    catalog = ensure_catalog(ws.root)
    for row in catalog.get("sources") or []:
        if not isinstance(row, dict) or row.get("document_id") != pack_id:
            continue
        section_id = str(row.get("section_id") or "")
        if not section_id or section_id in shown or section_id not in ready_ids:
            continue
        shown.add(section_id)
        sources.append(
            {
                "adapter_id": str((adapter or {}).get("id") or ""),
                "source_id": str(row.get("id") or section_id),
                "section_id": section_id,
                "url": str(row.get("url") or url),
                "section_ready": True,
                "source_format": (adapter or {}).get("source_format") or "",
                "document_id": pack_id,
                "pack_dir": str(pack_dir.resolve()),
                "copies": [],
                "repo_id": found_repo,
                "signed_count": None,
                "unsigned_count": None,
            }
        )
    legal = adapter.get("source") if isinstance(adapter, dict) and isinstance(adapter.get("source"), dict) else {}
    adapters = []
    if adapter is not None:
        adapters.append(
            {
                "id": adapter.get("id"),
                "instrument": legal.get("instrument") or adapter.get("id"),
                "url": url,
                "sections": [
                    section for section in ready_sections if str(section.get("id") or "") not in shown
                ],
            }
        )
    return {
        "document": document,
        "sources": sources,
        "adapters": adapters,
        "repos": _listed_repos(ws),
        "repo_id": found_repo,
        "repo_pack": True,
        "edit_repo": "",
        "edit_pack": "",
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Section added."),
        "error": (query.get("error") or [""])[0],
        **_door_path_fields(ws, found_repo),
    }


def _catalog_model(ws: Workspace, query: dict, document_id: str) -> dict:
    repo_id = _sync_open_repo(ws, query)
    if not repo_id:
        return {
            "document": {},
            "sources": [],
            "adapters": [],
            "repos": _listed_repos(ws),
            "repo_id": "",
            "job": None,
            "message": "",
            "error": "",
        }
    if _locate_repo_pack(ws, document_id, repo_id) is not None:
        return _repo_pack_sections_model(ws, query, document_id)
    catalog = ensure_catalog(ws.root)
    document = find_document(catalog, document_id)
    if document is None:
        return _repo_pack_sections_model(ws, query, document_id)
    adapter_id = str(document.get("adapter_id") or "")
    adapters = []
    for item in list_formex_adapter_choices():
        if item.get("id") != adapter_id:
            continue
        adapters.append(
            {
                **item,
                "sections": [
                    section
                    for section in item.get("sections") or []
                    if section.get("ready") and section.get("in_scope")
                ],
            }
        )
    sources = [
        row for row in _registered_sources(ws) if row.get("document_id") == document_id
    ]
    pack_id = ""
    for item in _formex_sources():
        if item.get("id") == adapter_id:
            pack_id = str(item.get("pack_id") or "")
            break
    pack_dir = ""
    if pack_id:
        chosen = selected_copy(ws.root, pack_id)
        pack_dir = _shown_pack_dir(ws, pack_id, chosen)
    for row in sources:
        row["pack_dir"] = pack_dir
    document = dict(document)
    document["repo_id"] = repo_id
    return {
        "document": document,
        "sources": sources,
        "adapters": adapters,
        "repos": _listed_repos(ws),
        "repo_id": repo_id,
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Section added."),
        "error": (query.get("error") or [""])[0],
        **_door_path_fields(ws, repo_id),
    }


def _catalog_job(ws: Workspace, query: dict):
    job_id = (query.get("job") or [""])[0]
    if not job_id:
        return None
    return read_job(ws.root / "jobs", job_id)


def _adapter_from_query(ws: Workspace, query: dict) -> tuple[Path, dict]:
    adapter_id = (query.get("adapter") or [""])[0].strip()
    if not adapter_id:
        raise ModelError("source", "adapter", "an adapter id")
    return _load_adapter(adapter_id)


def _inspect_model(ws: Workspace, query: dict) -> dict:
    adapter_dir, adapter = _adapter_from_query(ws, query)
    listed = stage00(adapter, adapter_dir=adapter_dir)
    ready_sections = [
        item
        for item in listed["sections"]
        if item.get("ready") is True and item.get("in_scope") is True
    ]
    inspect_section = (query.get("section") or [""])[0].strip()
    provisions_preview = None
    provision_diagnostics = []
    if inspect_section and any(item["id"] == inspect_section for item in ready_sections):
        extracted = section_provisions(adapter_dir, adapter, inspect_section)
        provisions_preview = extracted["provisions"]
        provision_diagnostics = list(extracted.get("diagnostics") or [])
    sections = []
    for item in listed["sections"]:
        match = next(
            (section for section in adapter.get("sections") or [] if section.get("id") == item.get("id")),
            {},
        )
        sections.append(
            {
                "id": item.get("id"),
                "title": match.get("title") or "",
                "ready": item.get("ready"),
                "in_scope": item.get("in_scope"),
            }
        )
    return {
        "adapter_id": adapter.get("id"),
        "status": adapter.get("status"),
        "source_format": adapter.get("source_format") or "text",
        "source": adapter.get("source") or {},
        "sections": sections,
        "inventory": listed.get("inventory"),
        "inspect_section": inspect_section,
        "provisions_preview": provisions_preview,
        "provision_diagnostics": provision_diagnostics,
    }


def _requirement_rows(directory: Path, requirements: list[dict], trust: dict) -> list[dict]:
    rows = []
    for requirement in requirements:
        reading = read_signature(requirement, trust, what="requirement")
        locators = [
            ref.get("locator")
            for ref in requirement.get("references") or []
            if isinstance(ref, dict) and ref.get("locator")
        ]
        rows.append(
            {
                "id": requirement["id"],
                "locators": locators,
                "signed": isinstance(requirement.get("signed"), dict),
                "verifiable": bool(reading.get("verifiable")),
                "who": reading.get("who"),
                "when": reading.get("when"),
            }
        )
    rows.sort(key=lambda item: (_locator_sort_key(item["locators"]), str(item["id"])))
    return rows


def _locator_sort_key(locators: list) -> tuple:
    """Order VII.1(a), VII.1(b), VII.2(a)… by annex position, not by filename or reference nr."""
    text = str(locators[0]) if locators else ""
    match = re.match(
        r"^([A-Za-z]+)\.?(\d+)(?:\(([A-Za-z0-9]+)\))?(.*)$",
        text.strip(),
    )
    if not match:
        return (text, 0, "", text)
    prefix, number, clause, rest = match.groups()
    return (prefix.upper(), int(number), clause or "", rest)


def _document_for_adapter(root: Path, adapter_id: str) -> dict | None:
    """The pack source for this adapter, when the catalog names exactly one."""
    if not adapter_id:
        return None
    matches = [
        row
        for row in load_catalog(root).get("documents") or []
        if isinstance(row, dict) and str(row.get("adapter_id") or "") == adapter_id
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _copy_document(root: Path, adapter_id: str) -> dict:
    document = _document_for_adapter(root, adapter_id)
    if document is None:
        return {"document_id": "", "document_name": ""}
    return {
        "document_id": str(document.get("id") or ""),
        "document_name": str(document.get("name") or ""),
    }


def _curbpack_pack_dir(ws: Workspace, pack_id: str) -> str:
    """Versioned pack directory from the open repo's packs_dir."""
    located = _locate_repo_pack(ws, pack_id)
    if located is None:
        return ""
    return str(located[1].resolve())


def _shown_pack_dir(ws: Workspace, pack_id: str, fallback: Path | None) -> str:
    found = _curbpack_pack_dir(ws, pack_id)
    if found:
        return found
    if fallback is not None:
        return str(fallback.resolve())
    return ""


def _repo_pack_copy_model(ws: Workspace, query: dict, pack_id: str) -> dict:
    repo_id = (query.get("repo") or [""])[0].strip()
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    found_repo, pack_dir, _listed = located
    pack, requirements = load_pack_directory(pack_dir)
    section = (query.get("section") or [""])[0].strip()
    if section:
        source = pack.get("source") if isinstance(pack.get("source"), dict) else {}
        matched = _adapter_for_url(str(source.get("url") or ""))
        section_ids = _adapter_section_ids(matched) if matched else []
        requirements = [
            item
            for item in requirements
            if isinstance(item, dict) and _requirement_in_section(item, section, section_ids)
        ]
    trust = trust_store(ws.keys)
    query_string = _pack_query({"repo": [found_repo], "pack": [pack_id]})
    if section:
        query_string = f"{query_string}&section={quote(section, safe='')}"
    return {
        "adapter_id": "",
        "timestamp": pack_id,
        "pack_dir": str(pack_dir.resolve()),
        "pack_kind": "pack",
        "read_only": False,
        "requirements": _requirement_rows(pack_dir, requirements, trust),
        "coverage_detail": None,
        "message": "",
        "document_id": pack_id,
        "document_name": str(pack.get("name") or pack_id),
        "repo_id": found_repo,
        "pack_id": pack_id,
        "requirement_query": f"?{query_string}",
    }


def _copy_model(ws: Workspace, _query: dict) -> dict:
    pack_id = (_query.get("pack") or [""])[0].strip()
    if pack_id:
        return _repo_pack_copy_model(ws, _query, pack_id)
    selection = read_selection(ws.root)
    if selection and isinstance(selection.get("pack_id"), str):
        _sync_adapter_for_pack(ws, selection["pack_id"])
    adapter = _active_adapter(ws)
    adapter_id = str(adapter.get("id") or "")
    document = _copy_document(ws.root, adapter_id)
    directory = resolve_selected_pack(ws.root)
    if directory is None:
        directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return {
            "adapter_id": adapter_id,
            "timestamp": None,
            "requirements": [],
            **document,
        }
    _pack, requirements = load_working_copy(directory)
    trust = trust_store(ws.keys)
    kind = (selection or {}).get("kind") or "working"
    return {
        "adapter_id": adapter_id,
        "timestamp": directory.name,
        "pack_dir": _shown_pack_dir(ws, str(adapter.get("pack_id") or ""), directory),
        "pack_kind": kind,
        "read_only": kind == "published",
        "requirements": _requirement_rows(directory, requirements, trust),
        "coverage_detail": _coverage_detail(directory) if kind == "working" else None,
        "message": "Published Pack — read-only. Use Compare to copy into a working copy."
        if kind == "published"
        else "",
        **document,
    }


def _publication_model(ws: Workspace, query: dict) -> dict:
    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return {"timestamp": None, "blockers": [], "requirements": []}
    pack, requirements = load_working_copy(directory)
    trust = trust_store(ws.keys)
    message = ""
    if (query.get("sealed") or [""])[0]:
        message = "Pack directory sealed."
    return {
        "timestamp": directory.name,
        "pack_version": pack.get("version"),
        "requirements": _requirement_rows(directory, requirements, trust),
        "seal": read_pack_seal(directory, trust),
        "blockers": list_publication_blockers(ws.root, directory, trust),
        "coverage_detail": _coverage_detail(directory),
        "message": message,
    }


def _editor_model(ws: Workspace, requirement_id: str, query: dict) -> dict:
    directory, pack, requirement = _open_requirement(ws, requirement_id, query)
    if requirement is None or directory is None or pack is None:
        return {"requirement": None}
    trust = trust_store(ws.keys)
    try_repo = (query.get("try_repo") or [""])[0].strip()
    try_job_id = (query.get("try_job") or [""])[0].strip()
    try_open = bool((query.get("try_open") or [""])[0])
    try_job = None
    if try_job_id:
        try:
            try_job = read_try_job(ws.root / "jobs", try_job_id)
        except ModelError:
            try_job = None
        if try_job and try_job.get("status") == "done":
            try_repo = try_repo or str(try_job.get("repo_id") or "")
            try_open = True
            try_job = None
    try_document = load_try_result(ws.root / "jobs", requirement_id, try_repo) if try_repo else None
    return {
        "requirement": requirement,
        "expected_digest": version_digest(requirement),
        "reading": read_signature(requirement, trust, what="requirement"),
        "seal": read_pack_seal(directory, trust),
        "pack_version": pack.get("version"),
        "pack_id": pack.get("id"),
        "copy_timestamp": directory.name,
        "message": _editor_message(query),
        "repos": load_repos(ws.root).get("repos") or [],
        "try_repo_id": try_repo,
        "try_open": try_open or bool(try_document and not try_job),
        "try_ran": bool(try_document),
        "try_candidates": list((try_document or {}).get("candidates") or []),
        "try_assess_limit": 5,
        "try_error": (query.get("try_error") or [""])[0],
        "try_job": try_job,
        "workspace_root": str(ws.root.resolve()),
        "error": (query.get("error") or [""])[0],
        "invalid_fields": [
            name.strip()
            for name in (query.get("invalid") or [])
            if str(name).strip()
        ],
        "repo_id": (query.get("repo") or [""])[0].strip(),
        "bound_pack": (query.get("pack") or [""])[0].strip(),
        "list_href": (
            "/requirements/copy?" + _pack_query(query)
            if _pack_query(query)
            else "/requirements/copy"
        ),
    }


def _run_try_discovery(ws: Workspace, requirement_id: str, form: dict) -> str:
    directory, _pack, requirement = _open_requirement(ws, requirement_id, form)
    if requirement is None or directory is None:
        raise ModelError("try discovery", "requirement", "a requirement in the selected working copy")
    repo_id = (form.get("repo_id") or [""])[0].strip()
    data = load_repos(ws.root)
    row = find_repo(data, repo_id)
    if row is None:
        raise ModelError("try discovery", "repo_id", f"a registered repository, not {repo_id}")
    raw_limit = (form.get("assess_limit") or ["5"])[0].strip() or "5"
    if not raw_limit.isdigit():
        raise ModelError("try discovery", "assess_limit", "an integer from 0 to 20")
    assess_limit = int(raw_limit)
    if assess_limit > 20:
        raise ModelError("try discovery", "assess_limit", "an integer from 0 to 20")
    repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
    config_path = repo / "curbpack.json"
    config = read_json(config_path) if config_path.is_file() else {}
    if not isinstance(config, dict):
        config = {}
    hunt = {"search_hints": config.get("search_hints") or {}}
    job_id = f"try-{secrets.token_hex(4)}"
    start_try_job(
        ws.root / "jobs",
        job_id=job_id,
        repo=repo,
        repo_id=repo_id,
        requirement=requirement,
        hunt=hunt,
        assess_limit=assess_limit,
        complete=getattr(ws, "discover_complete", None),
    )
    return job_id


def _try_discovery_file_model(ws: Workspace, requirement_id: str, query: dict) -> dict:
    repo_id = (query.get("repo") or [""])[0].strip()
    path = (query.get("path") or [""])[0].strip()
    back = f"/requirements/requirement/{requirement_id}?try_repo={repo_id}&try_open=1"
    data = load_repos(ws.root)
    row = find_repo(data, repo_id)
    if row is None:
        return {
            "path": path,
            "error": f"Unknown repo {repo_id}",
            "back": back,
            "requirement_id": requirement_id,
        }
    repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
    document = load_try_result(ws.root / "jobs", requirement_id, repo_id)
    candidate = candidate_for_path(document, path)
    try:
        body = read_try_file(repo, path)
    except ModelError as exc:
        return {"path": path, "error": str(exc), "back": back, "requirement_id": requirement_id}
    return {
        "path": path,
        "body": body,
        "excerpt": str((candidate or {}).get("excerpt") or ""),
        "model_excerpt": str((candidate or {}).get("model_excerpt") or ""),
        "back": back,
        "requirement_id": requirement_id,
    }


def _editor_message(query: dict) -> str:
    if (query.get("saved") or [""])[0]:
        return "Saved."
    if (query.get("signed") or [""])[0]:
        return "Signed with the local Ed25519 key."
    return ""


def _check_message(query: dict) -> str:
    if (query.get("saved") or [""])[0]:
        return "Saved curbpack.json in the repo."
    return ""


def _confined_run_result_path(results_folder: str, requested: str) -> str:
    if not results_folder:
        return ""
    folder = Path(results_folder).resolve()
    wanted = (requested or "").strip()
    if wanted:
        path = Path(wanted).resolve()
        try:
            path.relative_to(folder)
        except ValueError:
            return ""
        if path.is_file() and path.name.startswith("run-result_") and path.name.endswith(".json"):
            return str(path)
        return ""
    dated = sorted(folder.glob("run-result_*.json"))
    if dated:
        return str(dated[-1].resolve())
    return ""


def _new_review_report_path(folder: Path) -> Path:
    return _new_dated_json(folder, "review-report")


def _new_dated_json(folder: Path, prefix: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = folder / f"{prefix}_{stamp}.json"
        if not path.exists():
            return path
        time.sleep(1)


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


def _check_editor_model(ws: Workspace, query: dict) -> dict:
    repos = _listed_repos(ws)
    repo_id = _sync_open_repo(ws, query)
    if repo_id and not any(row.get("id") == repo_id for row in repos):
        raise ModelError("check", "repo", f"a registered repository, not {repo_id}")
    fields = _door_path_fields(ws, repo_id) if repo_id else {}
    packs: list[dict] = []
    selection = ""
    values = {key: "" for key in ("packs_dir", "claims_dir", "results_dir", "reports_dir")}
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        config_path = repo / "curbpack.json"
        if config_path.is_file():
            from common.validate import validate_curbpack_config

            config = validate_curbpack_config(read_json(config_path))
            for key in values:
                values[key] = str(config.get(key) or "")
            packs_root = packs_dir(repo, config)
            for pack_id in config["packs"]:
                try:
                    pack_dir = _pack_version_dir(packs_root, pack_id)
                    present = True
                except ModelError:
                    pack_dir = packs_root / pack_id
                    present = False
                packs.append(
                    {
                        "id": pack_id,
                        "present": present,
                        "pack_dir": str(pack_dir.resolve()),
                    }
                )
            if "exclude_requirements" in config:
                selection = "exclude_requirements " + ", ".join(config["exclude_requirements"])
            elif "requirements" in config:
                selection = "requirements " + ", ".join(config["requirements"])
    result_path = _confined_run_result_path(fields.get("results_dir") or "", (query.get("result") or [""])[0])
    return {
        "repos": repos,
        "repo_id": repo_id,
        "ask_read": False,
        "packs": packs,
        "selection": selection,
        "curbpack_file": fields.get("curbpack_file") or "",
        "directory": fields.get("directory") or "",
        "claims_dir": fields.get("claims_dir") or "",
        "results_dir": fields.get("results_dir") or "",
        "reports_dir": fields.get("reports_dir") or "",
        "packs_dir_value": values["packs_dir"],
        "claims_dir_value": values["claims_dir"],
        "results_dir_value": values["results_dir"],
        "reports_dir_value": values["reports_dir"],
        "run_result_path": result_path,
    }


def _repo_claims(ws: Workspace, repo_id: str, packs: list[dict]) -> list[dict]:
    if not repo_id:
        return []
    requirement_pack: dict[str, str] = {}
    for pack in packs:
        directory = pack.get("directory")
        pack_id = str(pack.get("id") or "")
        if not isinstance(directory, Path) or not pack_id:
            continue
        try:
            _pack, requirements = load_pack_directory(directory)
        except ModelError:
            continue
        for requirement in requirements:
            requirement_id = requirement.get("id")
            if isinstance(requirement_id, str):
                requirement_pack.setdefault(requirement_id, pack_id)
    rows = []
    for claim in load_claims(_registered_repo_path(ws, repo_id) / "claims"):
        args = claim.get("args") if isinstance(claim.get("args"), dict) else {}
        rows.append(
            {
                "id": str(claim.get("id") or ""),
                "requirement_id": str(claim.get("requirement_id") or ""),
                "path": str(args.get("path") or ""),
                "pack_id": requirement_pack.get(str(claim.get("requirement_id") or ""), ""),
                "checks": len(claim.get("checks") or []),
            }
        )
    return rows


def _check_report(ws: Workspace, query: dict, editor: dict) -> tuple[dict | None, int | None]:
    path_text = str(editor.get("run_result_path") or "").strip()
    if not path_text:
        return None, None
    path = Path(path_text)
    if not path.is_file():
        return None, None
    result = load_run_result(path)
    if (query.get("exit") or [""])[0] != "":
        return result, int((query.get("exit") or ["1"])[0] or "1")
    from checks.run import process_exit_code

    return result, process_exit_code(result)


def _registered_repo_path(ws: Workspace, repo_id: str) -> Path:
    row = find_repo(load_repos(ws.root), repo_id)
    if row is None:
        raise ModelError("check", "repo", f"a registered repository, not {repo_id}")
    return resolve_repo_path(ws.root, str(row.get("path") or ""))


def _write_curbpack(repo: Path, pack_ids: list[str]) -> None:
    path = repo / "curbpack.json"
    current: dict = {}
    if path.is_file():
        loaded = read_json(path)
        if isinstance(loaded, dict):
            current = loaded
    document = {
        key: current[key]
        for key in (
            "search_hints",
            "exclude_requirements",
            "requirements",
            "packs_dir",
            "claims_dir",
            "results_dir",
            "reports_dir",
            "unsigned_requirements",
        )
        if key in current
    }
    document["packs"] = pack_ids
    from common.validate import validate_curbpack_config

    write_json(path, validate_curbpack_config(document))


def _pack_directory_for_check(root: Path, pack_id: str) -> Path | None:
    selection = read_selection(root)
    if isinstance(selection, dict) and selection.get("pack_id") == pack_id:
        chosen = resolve_selected_pack(root)
        if chosen is not None:
            return chosen
    stamps = [
        stamp
        for stamp in list_working_copies(root, pack_id)
        if (root / pack_id / stamp / "pack.json").is_file()
    ]
    if stamps:
        return select_working_copy(root, pack_id, stamps[-1])
    versions = list_published_versions(root, pack_id)
    if versions:
        return select_published_pack(root, pack_id, versions[-1])
    return None


def _pack_meta_for_check(directory: Path) -> dict:
    path = directory / "pack.json"
    if not path.is_file():
        return {}
    try:
        pack = load_pack(path)
    except ModelError:
        return {}
    return pack if isinstance(pack, dict) else {}


def _copy_label(directory: Path) -> str:
    if directory.parent.name == "published":
        return f"Published · {directory.name}"
    return f"Working copy · {directory.name}"


def _selected_requirement(ws: Workspace, requirement_id: str):
    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return None, None, None
    pack, requirements = load_working_copy(directory)
    match = next((item for item in requirements if item["id"] == requirement_id), None)
    return directory, pack, match


def _open_requirement(ws: Workspace, requirement_id: str, params: dict):
    """Requirement in the named repo pack, or the selected working copy."""
    pack_id = (params.get("pack") or [""])[0].strip()
    if not pack_id:
        return _selected_requirement(ws, requirement_id)
    repo_id = (params.get("repo") or [""])[0].strip()
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    _repo_id, pack_dir, _listed = located
    pack, requirements = load_pack_directory(pack_dir)
    match = next((item for item in requirements if item["id"] == requirement_id), None)
    return pack_dir, pack, match


def _save_requirement_form(ws: Workspace, requirement_id: str, form: dict) -> None:
    directory, _pack, requirement = _open_requirement(ws, requirement_id, form)
    if directory is None or requirement is None:
        raise ModelError("requirement", "id", "a requirement in the selected working copy")
    edited = apply_edits(requirement, _edits_from_form(requirement, form))
    save_working_requirement(
        directory,
        edited,
        expected_digest=(form.get("expected_digest") or [""])[0],
    )


def _edits_from_form(requirement: dict, form: dict) -> dict:
    present = set(form.get("present") or [])
    edits: dict = {}
    for field in (
        "remediation_hint",
        "note",
        "strength",
        "responsible",
        "applicability",
        "exceptions",
        "scope",
    ):
        if field in present:
            edits[field] = (form.get(field) or [""])[0].strip()
    source_fields = ("framework", "instrument", "identifier", "edition", "language", "url")
    if any(field in present for field in source_fields):
        source = dict(requirement.get("source") or {})
        for field in source_fields:
            if field not in present:
                continue
            value = (form.get(field) or [""])[0].strip()
            if value:
                source[field] = value
            else:
                source.pop(field, None)
        edits["source"] = source
    hint_names = ("concepts", "path_hints", "expected_evidence")
    if any(field in present for field in hint_names) or "sources" in present:
        hints = copy.deepcopy(requirement.get("discovery_hints") or {})
        for field in hint_names:
            if field not in present:
                continue
            values = _lines((form.get(field) or [""])[0])
            if values:
                hints[field] = values
            else:
                hints.pop(field, None)
        if "sources" in present:
            raw = (form.get("sources") or [""])[0].strip()
            if not raw:
                hints.pop("sources", None)
            else:
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ModelError("requirement", "discovery_hints.sources", "a JSON list")
                hints["sources"] = parsed
        edits["discovery_hints"] = hints
    if "references" in present:
        locators = form.get("ref_locator") or []
        texts = form.get("ref_law_text") or []
        if len(locators) != len(texts):
            raise ModelError("requirement", "references", "a locator and law text for each row")
        edits["references"] = assign_reference_numbers(
            [
                {"locator": locator.strip(), "law_text": text}
                for locator, text in zip(locators, texts)
            ]
        )
    return edits


def _sign_requirement(ws: Workspace, requirement_id: str, form: dict) -> None:
    directory, _pack, requirement = _open_requirement(ws, requirement_id, form)
    if directory is None or requirement is None:
        raise ModelError("requirement", "id", "a requirement in the selected working copy")
    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    if "origin" in requirement:
        signed = approve_working_copy(requirement, name=name, private_key=private, at=_now())
    else:
        signed = publish_requirement(requirement, name=name, private_key=private, at=_now())
    save_working_requirement(
        directory,
        signed,
        expected_digest=(form.get("expected_digest") or [""])[0],
    )


def _seal_selected(ws: Workspace, form: dict) -> None:
    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        raise ModelError("working copy", "timestamp", "a selected working copy")
    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    seal_pack_directory(directory, name=name, private_key=private, at=_now())


def _consolidate_model(ws: Workspace) -> dict:
    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return {"suggestions": [], "requirements": [], "digests": {}}
    _pack, requirements = load_working_copy(directory)
    return {
        "suggestions": suggest_consolidations(directory),
        "requirements": requirements,
        "digests": {item["id"]: version_digest(item) for item in requirements},
    }


def _apply_consolidation_form(ws: Workspace, form: dict) -> None:
    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        raise ModelError("working copy", "timestamp", "a selected working copy")
    ids = form.get("ids") or []
    digest_ids = form.get("digest_id") or []
    digest_values = form.get("digest_value") or []
    if len(digest_ids) != len(digest_values):
        raise ModelError("requirement", "version", "a digest for each selected requirement")
    locators = form.get("ref_locator") or []
    texts = form.get("ref_law_text") or []
    apply_consolidation(
        directory,
        ids,
        (form.get("retained_id") or [""])[0],
        {"note": (form.get("note") or [""])[0].strip()},
        [{"locator": locator, "law_text": text} for locator, text in zip(locators, texts)],
        digests=dict(zip(digest_ids, digest_values)),
    )


def _extract_review_model(ws: Workspace, query: dict) -> dict:
    adapter = _active_adapter(ws)
    proposal = (query.get("proposal") or [""])[0]
    destination = (query.get("destination") or [""])[0]
    review = extraction_review(
        select_working_copy(ws.root, adapter["pack_id"], destination),
        select_working_copy(ws.root, adapter["pack_id"], proposal),
    )
    review["proposal"] = proposal
    review["destination"] = destination
    if (query.get("kept") or [""])[0]:
        review["message"] = "Nothing was brought in. The working copy is unchanged."
    return review


def _apply_extraction_review(ws: Workspace, form: dict) -> str:
    adapter = _active_adapter(ws)
    pack_id = adapter["pack_id"]
    proposal_name = (form.get("proposal") or [""])[0]
    destination_name = (form.get("destination") or [""])[0]
    pairs: dict[str, tuple[str, str | None]] = {}
    for raw in form.get("pair") or []:
        requirement_id, source_digest, destination_digest = raw.split("|", 2)
        pairs[requirement_id] = (source_digest, destination_digest or None)
    grouped: dict[str, list[str]] = {}
    for raw in form.get("field") or []:
        requirement_id, field = raw.split("|", 1)
        grouped.setdefault(requirement_id, []).append(field)
    partials: dict[str, dict] = {}
    raw_parts = (form.get("parts") or [""])[0]
    if raw_parts:
        try:
            parsed = json.loads(raw_parts)
        except json.JSONDecodeError as exc:
            raise ModelError("review", "parts", "a JSON list of chosen values") from exc
        if not isinstance(parsed, list):
            raise ModelError("review", "parts", "a JSON list of chosen values")
        for item in parsed:
            if not isinstance(item, dict):
                raise ModelError("review", "parts", "one object per chosen value")
            requirement_id = str(item.get("id") or "")
            field = str(item.get("field") or "")
            partials.setdefault(requirement_id, {})[field] = item.get("value")
    choices = []
    for requirement_id in sorted(set(grouped) | set(partials)):
        fields = [name for name in grouped.get(requirement_id, []) if name not in partials.get(requirement_id, {})]
        try:
            source_digest, destination_digest = pairs[requirement_id]
        except KeyError:
            raise ModelError(
                f"requirement {requirement_id}",
                "version",
                "the digest read before this transfer",
            ) from None
        choices.append(
            {
                "id": requirement_id,
                "fields": fields,
                "partial": partials.get(requirement_id, {}),
                "source_digest": source_digest,
                "destination_digest": destination_digest,
            }
        )
    for requirement_id in form.get("add") or []:
        try:
            source_digest, _destination_digest = pairs[requirement_id]
        except KeyError:
            raise ModelError(
                f"requirement {requirement_id}",
                "version",
                "the digest read before this transfer",
            ) from None
        choices.append(
            {
                "id": requirement_id,
                "fields": [],
                "source_digest": source_digest,
                "destination_digest": None,
            }
        )
    if not choices:
        return (
            "/requirements/extract/review?proposal="
            + quote(proposal_name)
            + "&destination="
            + quote(destination_name)
            + "&kept=1"
        )
    apply_extraction_choices(
        select_working_copy(ws.root, pack_id, destination_name),
        select_working_copy(ws.root, pack_id, proposal_name),
        choices,
    )
    return "/requirements?brought=1"


def _compare_model(ws: Workspace, query: dict) -> dict:
    adapter = _active_adapter(ws)
    pack_id = adapter["pack_id"]
    options = _compare_options(ws, pack_id)
    left = (query.get("left") or [""])[0]
    right = (query.get("right") or [""])[0]
    values = {str(item.get("value") or "") for item in options}
    if left and left not in values:
        left = ""
    if right and right not in values:
        right = ""
    model = {
        "options": options,
        "copies": [item["value"] for item in options if item.get("kind") == "working"],
        "left": left,
        "right": right,
        "diff": None,
        "can_transfer": False,
    }
    if left and right:
        left_dir = _resolve_compare_ref(ws.root, pack_id, left)
        right_dir = _resolve_compare_ref(ws.root, pack_id, right)
        model["diff"] = compare_copies(left_dir, right_dir)
        model["can_transfer"] = _compare_ref_kind(right) == "working" and _compare_ref_kind(
            left
        ) in {"working", "published"}
    return model


def _compare_options(ws: Workspace, pack_id: str) -> list[dict]:
    """Working copies (selected labeled) plus published releases for Compare."""
    selection = read_selection(ws.root)
    selected_stamp = ""
    if (
        isinstance(selection, dict)
        and selection.get("pack_id") == pack_id
        and selection.get("kind") == "working"
        and isinstance(selection.get("timestamp"), str)
    ):
        selected_stamp = selection["timestamp"]
    options: list[dict] = []
    for stamp in list_working_copies(ws.root, pack_id):
        if stamp == selected_stamp:
            label = f"Working copy · {stamp}"
        else:
            label = f"Copy · {stamp}"
        options.append({"value": stamp, "label": label, "kind": "working"})
    for version in list_published_versions(ws.root, pack_id):
        options.append(
            {
                "value": f"published:{version}",
                "label": f"Published · {version}",
                "kind": "published",
            }
        )
    options.sort(
        key=lambda item: (
            0 if item.get("value") == selected_stamp else 1 if item.get("kind") == "working" else 2,
            str(item.get("value") or ""),
        )
    )
    return options


def _compare_ref_kind(ref: str) -> str:
    raw = (ref or "").strip()
    if raw.startswith("published:"):
        return "published"
    return "working" if raw else ""


def _resolve_compare_ref(root: Path, pack_id: str, ref: str) -> Path:
    raw = (ref or "").strip()
    if raw.startswith("published:"):
        return select_published_pack(root, pack_id, raw.split(":", 1)[1])
    return select_working_copy(root, pack_id, raw)


def _apply_compare_form(ws: Workspace, form: dict) -> None:
    adapter = _active_adapter(ws)
    pack_id = adapter["pack_id"]
    source_ref = (form.get("source") or [""])[0]
    destination_ref = (form.get("destination") or [""])[0]
    if _compare_ref_kind(destination_ref) != "working":
        raise ModelError("compare", "destination", "a working copy, not a published release")
    source = _resolve_compare_ref(ws.root, pack_id, source_ref)
    destination = _resolve_compare_ref(ws.root, pack_id, destination_ref)
    field = (form.get("field") or [""])[0].strip()
    destination_digest = (form.get("destination_digest") or [""])[0]
    apply_transfer(
        source,
        destination,
        (form.get("requirement_id") or [""])[0].strip(),
        {field: (form.get("value") or [""])[0]},
        source_digest=(form.get("source_digest") or [""])[0],
        destination_digest=destination_digest or None,
    )


def _publish_selected(ws: Workspace, form: dict) -> None:
    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        raise ModelError("working copy", "timestamp", "a selected working copy")
    version = (form.get("version") or [""])[0].strip()
    publish_pack(ws.root, directory, version=version, trust=trust_store(ws.keys))


def _safe_local_next(raw: str) -> str:
    """Allow only same-origin relative paths (open redirect guard)."""
    value = (raw or "").strip()
    if not value.startswith("/") or value.startswith("//"):
        return ""
    if "\\" in value or "\n" in value or "\r" in value:
        return ""
    return value


def _requirement_editor_for_error(exc: ModelError, form: dict | None = None) -> str:
    """Send publish/sign field errors back to the Requirement editor with highlights."""
    object_name = str(exc.object_name or "")
    if not object_name.startswith("requirement "):
        return ""
    rest = object_name[len("requirement ") :].strip()
    requirement_id = rest.split(".", 1)[0].strip()
    if not requirement_id or "/" in requirement_id:
        return ""
    field = str(exc.field or "").strip()
    if "." in field:
        field = field.rsplit(".", 1)[-1]
    form_fields = {
        "edition",
        "framework",
        "instrument",
        "identifier",
        "language",
        "url",
        "note",
        "remediation_hint",
        "strength",
        "responsible",
        "applicability",
        "exceptions",
        "scope",
        "concepts",
        "expected_evidence",
        "path_hints",
    }
    message = _human_requirement_field_error(field, str(exc.expected or ""))
    params = [f"error={quote(message, safe='')}"]
    if field in form_fields:
        params.append(f"invalid={quote(field, safe='')}")
    extra = _pack_query(form or {})
    if extra:
        params.append(extra)
    return f"/requirements/requirement/{quote(requirement_id, safe='')}?{'&'.join(params)}"


def _human_requirement_field_error(field: str, expected: str) -> str:
    """Short editor flash: 'Field Edition: expected non empty string'."""
    labels = {
        "edition": "Edition",
        "framework": "Framework",
        "instrument": "Instrument",
        "identifier": "Identifier",
        "language": "Language",
        "url": "URL",
        "note": "Note",
        "remediation_hint": "Remediation hint",
        "strength": "Strength",
        "responsible": "Responsible",
        "applicability": "Applicability",
        "exceptions": "Exceptions",
        "scope": "Scope",
        "concepts": "Concepts",
        "expected_evidence": "Expected evidence",
        "path_hints": "Path hints",
    }
    label = labels.get(field) or (field.replace("_", " ").strip().title() or "field")
    expected_text = (expected or "a valid value").replace("non-empty", "non empty")
    return f"Field {label}: expected {expected_text}"


def _claims_redirect(form: dict, extra: str) -> str:
    from urllib.parse import quote

    parts = [extra]
    for key in ("repo_id", "source_id", "timestamp"):
        value = _query_value(form, key)
        if value:
            parts.append(f"{key}={quote(value)}")
    return "/claims?" + "&".join(parts)


def _claims(ws: Workspace) -> list[dict]:
    directory = ws.repo / "claims"
    if not directory.is_dir():
        return []
    from common.store import load_claims

    return load_claims(directory)


def _selected_pack_requirements(ws: Workspace) -> list[dict]:
    ensure_default_selection(ws.root)
    directory = resolve_selected_pack(ws.root)
    if directory is None:
        return []
    _pack, requirements = load_working_copy(directory)
    return [item for item in requirements if isinstance(item.get("id"), str)]


def _curbpack_pack_requirements(ws: Workspace) -> list[dict]:
    """Requirements from packs named in product curbpack.json (Check path)."""
    config_path = ws.repo / "curbpack.json"
    if not config_path.is_file():
        return []
    config = read_json(config_path)
    if not isinstance(config, dict):
        return []
    rows: list[dict] = []
    seen: set[str] = set()
    for pack_id in config.get("packs") or []:
        if not isinstance(pack_id, str) or not pack_id:
            continue
        directory = ws.packs / pack_id
        if not directory.is_dir():
            continue
        try:
            _pack, requirements = load_working_copy(directory)
        except ModelError:
            continue
        for item in requirements:
            requirement_id = item.get("id")
            if isinstance(requirement_id, str) and requirement_id not in seen:
                seen.add(requirement_id)
                rows.append(item)
    return rows


def _claim_requirement_catalog(ws: Workspace) -> list[dict]:
    """Prefer the pilot-selected Pack. If none, use curbpack.json packs for direct Claims."""
    selected = _selected_pack_requirements(ws)
    if selected:
        return selected
    return _curbpack_pack_requirements(ws)


def _selected_requirement_ids(ws: Workspace) -> list[str]:
    return [item["id"] for item in _claim_requirement_catalog(ws)]


def _requirement_lookup(ws: Workspace) -> dict[str, dict]:
    return {item["id"]: item for item in _claim_requirement_catalog(ws)}


def _query_value(bag: dict, key: str) -> str:
    value = bag.get(key) or [""]
    if isinstance(value, list):
        return str(value[0] if value else "").strip()
    return str(value).strip()


def _claims_repo(ws: Workspace, bag: dict) -> Path:
    repo_id = _query_value(bag, "repo_id") or _query_value(bag, "repo") or (open_repo_id(ws.root) or "")
    if not repo_id:
        return ws.repo
    row = find_repo(load_repos(ws.root), repo_id)
    if row is None:
        raise ModelError("discover", "repo_id", f"a registered repository, not {repo_id}")
    return resolve_repo_path(ws.root, str(row.get("path") or ""))


def _claims_directory(ws: Workspace, bag: dict) -> Path:
    return repo_claims_dir(_claims_repo(ws, bag))


def _claims_lookup(ws: Workspace, bag: dict) -> dict[str, dict]:
    source_id = _query_value(bag, "source_id")
    timestamp = _query_value(bag, "timestamp")
    repo = _claims_repo(ws, bag)
    if source_id and timestamp:
        source = next((item for item in _registered_sources(ws) if item.get("source_id") == source_id), None)
        if source is None:
            raise ModelError("discover", "source_id", f"a registered source, not {source_id}")
        pack_id = source.get("pack_id")
        if not isinstance(pack_id, str) or not pack_id:
            raise ModelError("discover", "pack_id", "a pack id on the source")
        resolve_copy_ref(ws.root, pack_id, timestamp)
        return {item["id"]: item for item in repo_pack_requirements(repo, pack_id)}
    config_path = repo / "curbpack.json"
    if not config_path.is_file():
        return {}
    from common.validate import validate_curbpack_config

    config = validate_curbpack_config(read_json(config_path))
    lookup: dict[str, dict] = {}
    for pack_id in config["packs"]:
        try:
            for item in repo_pack_requirements(repo, pack_id):
                lookup[item["id"]] = item
        except ModelError:
            continue
    return lookup


def _claims_model(ws: Workspace, query: dict) -> dict:
    door = _door_chrome(ws, query)
    lookup = _claims_lookup(ws, query)
    known_ids = list(lookup)
    trust = trust_store(ws.keys)
    repo = _claims_repo(ws, query)
    rows = []
    from common.store import load_claims

    config_path = repo / "curbpack.json"
    claims_dir = repo_claims_dir(repo) if config_path.is_file() else None
    claims = load_claims(claims_dir) if claims_dir is not None and claims_dir.is_dir() else []
    from claims.ui.coverage import load_run, retire_warning

    run_result = load_run(repo)
    if claims_dir is not None:
        for claim in claims:
            requirement_id = str(claim.get("requirement_id") or "")
            requirement = lookup.get(requirement_id)
            relative = claim_file_relative(repo, claims_dir, claim["id"])
            rows.append(
                {
                    "claim": claim,
                    "passages": law_passages(requirement) if requirement else [],
                    "reading": read_claim_seal(
                        claim,
                        trust,
                        repo=repo if claims_dir.is_dir() else None,
                        relative=relative,
                    ),
                    "retire_warning": retire_warning(claim, claims, run_result),
                }
            )
    prefill_requirement_id = (query.get("requirement_id") or [""])[0].strip()
    prefill_path = (query.get("path") or [""])[0].strip()
    prefill_passages: list[str] = []
    if prefill_requirement_id:
        # Validate query context when Discovery (or the user) named a Requirement.
        # Unknown ids must not fall back to a demo Requirement.
        if prefill_requirement_id not in lookup:
            raise ModelError(
                "claim",
                "requirement_id",
                f"an id in the selected Pack, not {prefill_requirement_id}",
            )
        prefill_passages = law_passages(lookup[prefill_requirement_id])
        if prefill_path:
            exist_args_for_path(prefill_path)
    prefill_source = ""
    if prefill_requirement_id and prefill_requirement_id in lookup:
        hints = lookup[prefill_requirement_id].get("discovery_hints") or {}
        sources = hints.get("sources") if isinstance(hints, dict) else None
        ids = [
            item.get("source")
            for item in sources or []
            if isinstance(item, dict) and isinstance(item.get("source"), str)
        ]
        if len(ids) == 1:
            prefill_source = ids[0]
    return {
        "claims": rows,
        "requirement_ids": known_ids,
        "prefill_requirement_id": prefill_requirement_id,
        "prefill_path": prefill_path,
        "prefill_source": prefill_source,
        "prefill_passages": prefill_passages,
        "repos": door.get("repos") or [],
        "repo_id": str(door.get("repo_id") or ""),
        "curbpack_file": door.get("curbpack_file") or "",
        "directory": door.get("directory") or "",
        "claims_dir": door.get("claims_dir") or "",
        "results_dir": door.get("results_dir") or "",
        "reports_dir": door.get("reports_dir") or "",
        "packs_dir_value": door.get("packs_dir_value") or "",
        "claims_dir_value": door.get("claims_dir_value") or "",
        "results_dir_value": door.get("results_dir_value") or "",
        "reports_dir_value": door.get("reports_dir_value") or "",
        "source_id": _query_value(query, "source_id"),
        "timestamp": _query_value(query, "timestamp"),
    }


def _escape(text: str) -> str:
    import html

    return html.escape(text)


def serve(root: Path, host: str = "127.0.0.1", port: int = 8770) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s %(name)s: %(message)s",
        )
    httpd = ThreadingHTTPServer((host, port), make_handler(Workspace(root)))
    print(f"Curbpack Studio at http://{host}:{httpd.server_address[1]}/", flush=True)
    httpd.serve_forever()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="PoC2 demonstration UI")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args()
    serve(args.workspace, args.host, args.port)


if __name__ == "__main__":
    main()
