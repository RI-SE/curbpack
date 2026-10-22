"""HTTP entry point. Handlers call use cases and hand the results to pages."""

from __future__ import annotations

import copy
import json
import logging
import re
import secrets
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

_LOG = logging.getLogger("poc2.app")

from app import pages
from checks.run import process_exit_code, run_and_write
from claims.bind import (
    build_claim,
    exist_args_for_path,
    law_passages,
    read_claim,
    read_claim_seal,
    rebind_from_fields,
    require_requirement_id,
    retire_claim,
    sign_claim,
    write_claim,
)
from common.canonical import version_digest
from common.errors import CheckError, ModelError, SigningUnavailable
from common.jsonio import read_json, write_json
from common.keystore import load_or_create_key, trust_store
from common.signing import read_signature
from common.store import load_pack, load_pack_directory, load_requirement, save_requirement
from claims.ui import http as claim_http
from claims.ui import pages as claim_pages
from demo_setup import prepare_demo
from discovery.jobs import read_job as read_discover_job
from discovery.jobs import reviewable_targets
from discovery.jobs import request_abort as abort_discover_job
from discovery.jobs import start_discover_job
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
    save_catalog,
)
from requirements.compare import apply_extraction_choices, apply_transfer, compare_copies, extraction_review
from requirements.consolidate import apply_consolidation, suggest_consolidations
from requirements.jobs import read_job, request_abort, start_extract_job
from requirements.ui import pages as requirement_pages
from requirements.ui import try_discovery as try_discovery_ui
from requirements.workspace import (
    ensure_default_selection,
    list_pack_options,
    list_working_copies,
    load_working_copy,
    list_publication_blockers,
    mark_published_selected,
    mark_selected,
    mark_source_adapter,
    publish_pack,
    read_selection,
    resolve_selected_pack,
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
    replace_saved_report,
    same_run,
    save_report_decision,
    save_report_signature,
    unchecked_requirement_ids,
)
from scaffold.stub import write_stub
from workflow import snapshot

ROOT = Path(__file__).resolve().parents[1]
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
DEFAULT_WORKSPACE = ROOT / "data" / "workspace"


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


def preview_report(ws: Workspace) -> dict | None:
    """Unsigned report for the current run. Does not write."""
    if not ws.run_path.is_file():
        return None
    packs, requirements = _report_sources(ws)
    if not packs:
        return None
    from common.store import load_claims, load_run_result

    claims_dir = ws.repo / "claims"
    claims = load_claims(claims_dir) if claims_dir.is_dir() else []
    return compile_report(
        run_result=load_run_result(ws.run_path),
        requirements=requirements,
        claims=claims,
        trust=trust_store(ws.keys),
        repo=ws.repo,
    )


def _review_message(query: dict) -> str:
    if (query.get("compiled") or [""])[0]:
        return "Report compiled."
    if (query.get("saved") or [""])[0]:
        return "Decision saved."
    if (query.get("signed") or [""])[0]:
        return "Report signed."
    return ""


def _review_view(ws: Workspace) -> tuple:
    report_exists = ws.report_path.is_file()
    report = None
    error = ""
    reading = None
    if report_exists:
        try:
            report = load_report(ws.report_path)
        except (ModelError, ValueError, OSError) as exc:
            error = str(exc)
    else:
        try:
            report = preview_report(ws)
        except ModelError as exc:
            error = str(exc)
    saved = report_exists and isinstance(report, dict)
    if saved:
        reading = read_report_signature(
            report,
            trust_store(ws.keys),
            repo=ws.repo,
            relative=_report_relative(ws),
        )
    run = _loaded_run(ws)
    same = same_run(report, run) if isinstance(report, dict) and isinstance(run, dict) else None
    unchecked = (
        unchecked_requirement_ids(_selected_ids_for_review(ws), report) if isinstance(report, dict) else []
    )
    return report, reading, error, saved, report_exists, same, unchecked


def _loaded_run(ws: Workspace) -> dict | None:
    if not ws.run_path.is_file():
        return None
    from common.store import load_run_result

    try:
        return load_run_result(ws.run_path)
    except (ModelError, ValueError, OSError):
        return None


def _report_relative(ws: Workspace) -> str | None:
    try:
        return str(ws.report_path.relative_to(ws.repo))
    except ValueError:
        return None


def _selected_ids_for_review(ws: Workspace) -> list[str]:
    from checks.run import selected_requirement_ids
    from common.validate import validate_curbpack_config

    config_path = ws.repo / "curbpack.json"
    if not config_path.is_file():
        return []
    try:
        config = validate_curbpack_config(read_json(config_path))
    except (ModelError, ValueError):
        return []
    loaded = []
    for pack_id in config.get("packs") or []:
        if not isinstance(pack_id, str) or not pack_id:
            continue
        directory = ws.packs / pack_id
        if not (directory / "pack.json").is_file():
            continue
        try:
            pack, requirements = load_pack_directory(directory)
        except ModelError:
            continue
        loaded.append((pack, requirements))
    if not loaded:
        return []
    try:
        return sorted(selected_requirement_ids(loaded, config))
    except ModelError:
        return []


def _report_sources(ws: Workspace) -> tuple[list[dict], list[dict]]:
    """Packs named by the product, otherwise the demo pack when that file is present."""
    config_path = ws.repo / "curbpack.json"
    if config_path.is_file():
        config = read_json(config_path)
        pack_ids = config.get("packs") if isinstance(config, dict) else None
        packs: list[dict] = []
        requirements: list[dict] = []
        if isinstance(pack_ids, list):
            for pack_id in pack_ids:
                if not isinstance(pack_id, str):
                    continue
                directory = ws.packs / pack_id
                if not (directory / "pack.json").is_file():
                    continue
                pack, rows = load_pack_directory(directory)
                packs.append(pack)
                requirements.extend(rows)
        if packs:
            return packs, requirements
    if ws.requirement_path().is_file() and (ws.pack / "pack.json").is_file():
        return [load_pack(ws.pack / "pack.json")], [load_requirement(ws.requirement_path())]
    return [], []


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
            _LOG.error(
                "request failed method=%s path=%s: %s\n%s",
                self.command,
                self.path,
                exc,
                traceback.format_exc(),
            )
            if isinstance(exc, (ModelError, CheckError, SigningUnavailable)):
                message = str(exc)
            else:
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
            try:
                self._post(parsed.path, self._form())
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
                info = snapshot(ws.root)
                return pages.check_page(info["run_result"], info["run_exit"])
            if path == "/review":
                report, reading, error, saved, report_exists, same, unchecked = _review_view(ws)
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
                )
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
            if path == "/requirements/documents":
                catalog = ensure_catalog(ws.root)
                add_document(
                    catalog,
                    name=(form.get("name") or [""])[0],
                    official_name=(form.get("official_name") or [""])[0],
                    url=(form.get("url") or [""])[0],
                    adapter_id=(form.get("adapter_id") or [""])[0],
                )
                save_catalog(ws.root, catalog)
                self._redirect("/requirements?added=1")
                return
            if path == "/requirements/catalog":
                catalog = ensure_catalog(ws.root)
                document_id = (form.get("document_id") or [""])[0].strip()
                add_section(
                    catalog,
                    document_id=document_id,
                    section_id=(form.get("section_id") or [""])[0],
                )
                save_catalog(ws.root, catalog)
                self._redirect(f"/requirements?document={document_id}&added=1")
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
                self._redirect(f"/requirements/requirement/{requirement_id}?signed=1")
                return
            if path.startswith("/requirements/requirement/") and path.endswith("/try-discovery"):
                requirement_id = path[
                    len("/requirements/requirement/") : -len("/try-discovery")
                ]
                job_id = _run_try_discovery(ws, requirement_id, form)
                self._redirect(
                    f"/requirements/requirement/{requirement_id}?try_job={job_id}"
                )
                return
            if path.startswith("/requirements/requirement/"):
                requirement_id = path[len("/requirements/requirement/") :]
                _save_requirement_form(ws, requirement_id, form)
                self._redirect(f"/requirements/requirement/{requirement_id}?saved=1")
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
                known = _selected_requirement_ids(ws)
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
                claims_dir = _claims_repo(ws, form) / "claims"
                destination = claims_dir / f"{claim['id']}.json"
                if destination.is_file():
                    raise ModelError("claim", "id", "a new id; an existing Claim is edited explicitly")
                write_claim(claims_dir, claim)
                self._redirect(_claims_redirect(form, f"saved=1&requirement_id={requirement_id}"))
                return
            if path.startswith("/claims/") and path.endswith("/retire"):
                claim_id = path[len("/claims/") : -len("/retire")]
                retire_claim(_claims_repo(ws, form) / "claims", claim_id)
                self._redirect(_claims_redirect(form, "retired=1"))
                return
            if path.startswith("/claims/") and path.endswith("/sign"):
                claim_id = path[len("/claims/") : -len("/sign")]
                claim = read_claim(_claims_repo(ws, form) / "claims" / f"{claim_id}.json")
                name = (form.get("name") or [""])[0].strip()
                private, _public = load_or_create_key(ws.keys, name)
                sealed = sign_claim(claim, name=name, private_key=private, at=_now())
                write_claim(_claims_repo(ws, form) / "claims", sealed)
                self._redirect(
                    _claims_redirect(form, f"signed=1&requirement_id={claim.get('requirement_id', '')}")
                )
                return
            if path.startswith("/claims/"):
                claim_id = path[len("/claims/") :]
                claim = read_claim(_claims_repo(ws, form) / "claims" / f"{claim_id}.json")
                had_signed = isinstance(claim.get("signed"), dict)
                updated = rebind_from_fields(
                    claim,
                    source=(form.get("source") or [""])[0],
                    args_json=(form.get("args") or ["{}"])[0],
                    checks_json=(form.get("checks") or ["[]"])[0],
                    severity=(form.get("severity") or [""])[0],
                    description=(form.get("description") or [""])[0],
                )
                write_claim(_claims_repo(ws, form) / "claims", updated)
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
                result, code = run_and_write(ws.repo, ws.packs, ws.run_path)
                self._redirect(f"/check?exit={code}&rows={len(result['claims'])}")
                return
            if path == "/review/compile":
                preview = preview_report(ws)
                if preview is None:
                    raise ModelError("review report", "run_result", "a run result to compile")
                replace_saved_report(
                    ws.report_path,
                    preview,
                    confirm=(form.get("confirm") or [""])[0] == "yes",
                )
                self._redirect("/review?compiled=1")
                return
            if path == "/review":
                save_report_decision(ws.report_path, (form.get("decision") or [""])[0])
                self._redirect("/review?saved=1")
                return
            if path == "/review/sign":
                name = (form.get("name") or [""])[0].strip()
                private, _public = load_or_create_key(ws.keys, name)
                save_report_signature(
                    ws.report_path,
                    name=name,
                    private_key=private,
                    at=_now(),
                )
                self._redirect("/review?signed=1")
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


def _discover_model(ws: Workspace, query: dict) -> dict:
    job = None
    job_id = (query.get("job") or [""])[0]
    if job_id:
        job = read_discover_job(ws.root / "jobs", job_id)
    return {
        "sources": _registered_sources(ws),
        "repos": load_repos(ws.root).get("repos") or [],
        "reviewable": reviewable_targets(ws.root),
        "job": job,
        "error": (query.get("error") or [""])[0],
    }


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
        raise ModelError("discover", "timestamp", "a dated working copy")
    directory = select_working_copy(ws.root, pack_id, timestamp)
    _pack, requirements = load_working_copy(directory)
    repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
    config_path = repo / "curbpack.json"
    config = read_json(config_path) if config_path.is_file() else {}
    if not isinstance(config, dict):
        config = {}
    hunt = {"hunt": config.get("hunt") or {}}
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


def _documents_model(ws: Workspace, query: dict) -> dict:
    catalog = ensure_catalog(ws.root)
    adapters = {item["id"]: item for item in _formex_sources()}
    trust = trust_store(ws.keys)
    documents = []
    for document in catalog.get("documents") or []:
        adapter = adapters.get(str(document.get("adapter_id") or ""))
        pack_id = adapter.get("pack_id") if isinstance(adapter, dict) else None
        signed, title = _signature_mark(ws.root, pack_id if isinstance(pack_id, str) else "", trust)
        documents.append({**document, "all_signed": signed, "signature_title": title})
    return {
        "documents": documents,
        "adapters": list_formex_adapter_choices(),
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Document added."),
        "error": (query.get("error") or [""])[0],
    }


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


def _catalog_model(ws: Workspace, query: dict, document_id: str) -> dict:
    catalog = ensure_catalog(ws.root)
    document = find_document(catalog, document_id)
    if document is None:
        raise ModelError("catalog", "document", f"a known document, not {document_id}")
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
    return {
        "document": document,
        "sources": sources,
        "adapters": adapters,
        "job": _catalog_job(ws, query),
        "message": _catalog_message(query, added="Section added."),
        "error": (query.get("error") or [""])[0],
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


def _copy_model(ws: Workspace, _query: dict) -> dict:
    selection = read_selection(ws.root)
    if selection and isinstance(selection.get("pack_id"), str):
        _sync_adapter_for_pack(ws, selection["pack_id"])
    adapter = _active_adapter(ws)
    directory = resolve_selected_pack(ws.root)
    if directory is None:
        directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return {"adapter_id": adapter.get("id"), "timestamp": None, "requirements": []}
    _pack, requirements = load_working_copy(directory)
    trust = trust_store(ws.keys)
    kind = (selection or {}).get("kind") or "working"
    return {
        "adapter_id": adapter.get("id"),
        "timestamp": directory.name,
        "pack_kind": kind,
        "read_only": kind == "published",
        "requirements": _requirement_rows(directory, requirements, trust),
        "coverage_detail": _coverage_detail(directory) if kind == "working" else None,
        "message": "Published Pack — read-only. Use Compare to copy into a working copy."
        if kind == "published"
        else "",
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
    directory, pack, requirement = _selected_requirement(ws, requirement_id)
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
        "message": _editor_message(query),
        "repos": load_repos(ws.root).get("repos") or [],
        "try_repo_id": try_repo,
        "try_open": try_open or bool(try_document and not try_job),
        "try_ran": bool(try_document),
        "try_candidates": list((try_document or {}).get("candidates") or []),
        "try_assess_limit": 5,
        "try_error": (query.get("try_error") or [""])[0],
        "try_job": try_job,
    }


def _run_try_discovery(ws: Workspace, requirement_id: str, form: dict) -> str:
    directory, _pack, requirement = _selected_requirement(ws, requirement_id)
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
    hunt = {"hunt": config.get("hunt") or {}}
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


def _selected_requirement(ws: Workspace, requirement_id: str):
    adapter = _active_adapter(ws)
    directory = selected_copy(ws.root, adapter["pack_id"])
    if directory is None:
        return None, None, None
    pack, requirements = load_working_copy(directory)
    match = next((item for item in requirements if item["id"] == requirement_id), None)
    return directory, pack, match


def _save_requirement_form(ws: Workspace, requirement_id: str, form: dict) -> None:
    directory, _pack, requirement = _selected_requirement(ws, requirement_id)
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
    directory, _pack, requirement = _selected_requirement(ws, requirement_id)
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
    copies = list_working_copies(ws.root, adapter["pack_id"])
    left = (query.get("left") or [""])[0]
    right = (query.get("right") or [""])[0]
    model = {"copies": copies, "left": left, "right": right, "diff": None}
    if left and right:
        model["diff"] = compare_copies(
            select_working_copy(ws.root, adapter["pack_id"], left),
            select_working_copy(ws.root, adapter["pack_id"], right),
        )
    return model


def _apply_compare_form(ws: Workspace, form: dict) -> None:
    adapter = _active_adapter(ws)
    source = select_working_copy(ws.root, adapter["pack_id"], (form.get("source") or [""])[0])
    destination = select_working_copy(
        ws.root, adapter["pack_id"], (form.get("destination") or [""])[0]
    )
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
    repo_id = _query_value(bag, "repo_id")
    if not repo_id:
        return ws.repo
    row = find_repo(load_repos(ws.root), repo_id)
    if row is None:
        raise ModelError("discover", "repo_id", f"a registered repository, not {repo_id}")
    return resolve_repo_path(ws.root, str(row.get("path") or ""))


def _claims_lookup(ws: Workspace, bag: dict) -> dict[str, dict]:
    source_id = _query_value(bag, "source_id")
    timestamp = _query_value(bag, "timestamp")
    if source_id and timestamp:
        source = next((item for item in _registered_sources(ws) if item.get("source_id") == source_id), None)
        if source is None:
            raise ModelError("discover", "source_id", f"a registered source, not {source_id}")
        directory = select_working_copy(ws.root, source["pack_id"], timestamp)
        _pack, requirements = load_working_copy(directory)
        return {
            item["id"]: item
            for item in requirements
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
    return _requirement_lookup(ws)


def _claims_model(ws: Workspace, query: dict) -> dict:
    lookup = _claims_lookup(ws, query)
    known_ids = list(lookup)
    trust = trust_store(ws.keys)
    repo = _claims_repo(ws, query)
    claims_dir = repo / "claims"
    rows = []
    from common.store import load_claims

    claims = load_claims(claims_dir) if claims_dir.is_dir() else []
    from claims.ui.coverage import load_run, retire_warning

    run_result = load_run(repo)
    for claim in claims:
        requirement_id = str(claim.get("requirement_id") or "")
        requirement = lookup.get(requirement_id)
        relative = f"claims/{claim['id']}.json"
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
        "repo_id": _query_value(query, "repo_id"),
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
    print(f"PoC2 demo at http://{host}:{httpd.server_address[1]}/", flush=True)
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
