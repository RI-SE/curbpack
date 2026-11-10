"""HTTP entry point. Handlers call use cases and hand the results to pages."""

from __future__ import annotations

import json
import logging
import re
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

_LOG = logging.getLogger("poc2.app")

from app import pages
from app import project_selector
from app.catalog_model import _add_catalog_section, _catalog_model
from app.check_model import _check_editor_model, _check_report, _run_check
from app.check_page import check_page
from app.claims_model import _claims_model, _create_claim, _retire_claim, _sign_claim, _update_claim
from app.claims_page import claims_page
from app.copy_model import _copy_model, _select_working_copy
from app.cover import cover
from app.discover_model import _add_discover_repo, _discover_model, _start_discover
from app.documents_model import _documents_model, _save_curbpack, _save_pack_document
from app.empty_folder import _start_empty_folder
from app.extract_review import _apply_extraction_review, _extract_review_model
from app.extract_start import _start_extract
from app.home_model import _home_model, _select_pack
from app.inspect_model import _inspect_model, _select_source
from app.pack_compare import _apply_compare_form, _compare_model
from app.pack_consolidate import _apply_consolidation_form, _consolidate_model
from app.pack_export import _export_model, _export_selected
from app.prepare_post import _prepare_workspace
from app.publication_model import _publication_model, _publish_selected, _seal_selected
from app.requirement_demo import _demo_requirement
from app.requirement_editor import (
    _editor_model,
    _run_try_discovery,
    _save_requirement_form,
    _sign_requirement,
)
from app.review_model import _compile_review, _review_view, _save_review_decision, _sign_review
from app.review_page import review_page
from app.scaffold_page import scaffold_page
from app.scaffold_write import _write_scaffold
from app.studio_model import _save_studio, _studio_model
from app.studio_page import studio_page
from app.try_discovery_file import _try_discovery_file_model
from checks.run import (
    _pack_version_dir,
    claims_dir,
    packs_dir,
)
from claims.bind import (
    read_claims,
)
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
    save_requirement,
)
from claims.ui import http as claim_http
from claims.ui import pages as claim_pages
from discovery.jobs import read_job as read_discover_job
from discovery.jobs import request_abort as abort_discover_job
from discovery.browse import list_directories
from discovery.door import (
    open_paths,
    open_repo_id,
    pack_display_name,
    repo_claims_dir,
    repo_pack_requirements,
    save_directory_fields,
    set_open_repo,
)
from discovery.repos import add_repo, find_repo, load_repos, resolve_repo_path, save_repos
from discovery.try_run import read_try_job
from requirements.editing import (
    apply_edits,
    publish_requirement,
    seal_pack_directory,
)
from requirements.extract.adapter import (
    ADAPTERS,
    list_adapters,
    load_adapter,
)
from requirements.catalog import (
    add_document,
    ensure_catalog,
)
from requirements.jobs import read_job, request_abort
from requirements.ui import pages as requirement_pages
from requirements.ui import try_discovery as try_discovery_ui
from requirements.workspace import (
    ensure_default_selection,
    list_pack_ids,
    list_published_versions,
    list_working_copies,
    load_working_copy,
    mark_source_adapter,
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
    durable_report_path,
)

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
    "/icons/curbpack-icon.svg": (
        ROOT / "app" / "icons" / "curbpack-icon.svg",
        "image/svg+xml",
    ),
}
_PROJECT_ALLOWED = frozenset({"/project"})
DEFAULT_WORKSPACE = default_workspace()


def _requires_open_project(path: str) -> bool:
    """Product doors and the cover need an open project.

    Pack-editor routes under /requirements/... (export, extract, try-discovery)
    stay reachable without one. Exact /requirements is Pack Sources and does not.
    """
    if path in {
        "/",
        "/requirements",
        "/studio",
        "/discover",
        "/discover/repo",
        "/check",
        "/review",
        "/requirement",
        "/scaffold",
    }:
        return True
    if path == "/discover/run" or path.startswith("/discover/jobs/"):
        return True
    if path.startswith("/discover/claims") or path.startswith("/discover/feedback"):
        return True
    if path.startswith("/review/") or path.startswith("/studio/"):
        return True
    return False


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
        return "Report sealed."
    if (query.get("claim_changed") or [""])[0]:
        return (
            "The current Claim has changed. "
            "A new curbcheck run is required for a new run result, and then a new review report."
        )
    return ""


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
            try:
                query = parse_qs(parsed.query, keep_blank_values=(parsed.path == "/review"))
                try:
                    _sync_open_repo(ws, query)
                except ModelError:
                    pass
                if parsed.path == "/discover/browse":
                    self._send_browse(query)
                    return
                if _requires_open_project(parsed.path) and not open_repo_id(ws.root):
                    self._redirect("/project")
                    return
                body = self._get(parsed.path, query)
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
                try:
                    _sync_open_repo(ws, form)
                except ModelError:
                    pass
                if _requires_open_project(parsed.path) and not open_repo_id(ws.root):
                    self._redirect("/project")
                    return
                self._post(parsed.path, form)
            except ModelError as exc:
                if parsed.path == "/project":
                    self._send(
                        200,
                        project_selector.project_page(
                            project_selector.project_model(
                                ws.root,
                                error=_escape(str(exc)),
                            )
                        ),
                    )
                    return
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
            if path == "/project":
                message = ""
                if (query.get("added") or [""])[0]:
                    message = "Project added."
                if (query.get("saved") or [""])[0]:
                    message = "Saved curbpack.json in the repo."
                return project_selector.project_page(
                    project_selector.project_model(ws.root, message=message)
                )
            if path == "/":
                return cover(_home_model(ws), message=_home_message(query))
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
                return _demo_requirement(ws)
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
                return claims_page(_claims_model(ws, query), message=message)
            if path == "/scaffold":
                return scaffold_page()
            if path == "/check":
                editor = _check_editor_model(ws, query)
                result, exit_code = _check_report(ws, query, editor)
                return check_page(
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
            if path == "/studio":
                return studio_page(_studio_model(ws, query), message=_studio_message(query))
            return pages.page("Not found", "<p>Unknown page.</p>")

        def _post(self, path: str, form: dict) -> None:
            if path == "/project":
                self._redirect(project_selector.handle_project_post(ws.root, form))
                return
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
                self._redirect(_prepare_workspace(ws))
                return
            if path == "/select-pack":
                self._redirect(_select_pack(ws, form))
                return
            if path == "/requirements/source":
                self._redirect(_select_source(ws, form))
                return
            if path == "/requirements/start-empty":
                self._redirect(_start_empty_folder(ws, (form.get("folder") or [""])[0]))
                return
            if path == "/requirements/curbpack":
                self._redirect(_save_curbpack(ws, form))
                return
            if path == "/requirements/documents":
                self._redirect(_save_pack_document(ws, form))
                return
            if path == "/requirements/catalog":
                self._redirect(_add_catalog_section(ws, form))
                return
            if path == "/requirements/select":
                self._redirect(_select_working_copy(ws, form))
                return
            if path == "/requirements/extract":
                self._redirect(_start_extract(ws, form))
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
                self._redirect(_sign_requirement(ws, requirement_id, form))
                return
            if path.startswith("/requirements/requirement/") and path.endswith("/try-discovery"):
                requirement_id = path[
                    len("/requirements/requirement/") : -len("/try-discovery")
                ]
                self._redirect(_run_try_discovery(ws, requirement_id, form))
                return
            if path.startswith("/requirements/requirement/"):
                requirement_id = path[len("/requirements/requirement/") :]
                self._redirect(_save_requirement_form(ws, requirement_id, form))
                return
            if path == "/requirements/seal":
                self._redirect(_seal_selected(ws, form))
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
                self._redirect(_publish_selected(ws, form))
                return
            if path == "/discover/repos":
                self._redirect(_add_discover_repo(ws, form))
                return
            if path == "/discover/run":
                self._redirect(_start_discover(ws, form))
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
                self._redirect(_create_claim(ws, form))
                return
            if path.startswith("/claims/") and path.endswith("/retire"):
                claim_id = path[len("/claims/") : -len("/retire")]
                self._redirect(_retire_claim(ws, claim_id, form))
                return
            if path.startswith("/claims/") and path.endswith("/sign"):
                claim_id = path[len("/claims/") : -len("/sign")]
                self._redirect(_sign_claim(ws, claim_id, form))
                return
            if path.startswith("/claims/"):
                claim_id = path[len("/claims/") :]
                self._redirect(_update_claim(ws, claim_id, form))
                return
            if path == "/scaffold":
                self._redirect(_write_scaffold(ws, form))
                return
            if path == "/check":
                self._redirect(_run_check(ws, form))
                return
            if path == "/review/compile":
                self._redirect(_compile_review(ws, form))
                return
            if path == "/review":
                self._redirect(_save_review_decision(ws, form))
                return
            if path == "/review/sign":
                self._redirect(_sign_review(ws, form))
                return
            if path == "/studio":
                self._redirect(_save_studio(ws, form))
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


def _sync_adapter_for_pack(ws: Workspace, pack_id: str) -> None:
    for item in list_adapters():
        if item.get("pack_id") == pack_id:
            mark_source_adapter(ws.root, item["id"])
            return


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


def _catalog_job(ws: Workspace, query: dict):
    job_id = (query.get("job") or [""])[0]
    if not job_id:
        return None
    return read_job(ws.root / "jobs", job_id)


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


def _check_message(query: dict) -> str:
    if (query.get("saved") or [""])[0]:
        return "Saved curbpack.json in the repo."
    return ""


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


def _claims_redirect(form: dict, extra: str, *, claim_changed: bool = False) -> str:
    from urllib.parse import quote

    return_to = _safe_local_next(_query_value(form, "return_to"))
    if return_to.startswith("/review?") or return_to == "/review":
        if claim_changed:
            join = "&" if "?" in return_to else "?"
            return f"{return_to}{join}claim_changed=1"
        return return_to
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
