"""Pack export view-model and write. The URL stays on the old server."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

from common.canonical import version_digest
from common.errors import ModelError
from common.keystore import trust_store
from common.signing import complete_pack_digest, verify_signature
from requirements.catalog import ensure_catalog, find_document
from requirements.workspace import export_pack, load_working_copy, selected_copy

if TYPE_CHECKING:
    from app.server import Workspace


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
    rows = _signature_rows(directory, pack, requirements, trust)
    signed = sum(1 for row in rows[1:] if row["status"] == "valid")
    unsigned = sum(1 for row in rows[1:] if row["status"] == "unsigned")
    model.update(
        {
            "timestamp": directory.name,
            "signed": signed,
            "unsigned": unsigned,
            "rows": rows,
            "pack_version": pack.get("version"),
        }
    )
    return model


def _export_document(ws: Workspace, document_id: str) -> tuple[dict, str, Path | None]:
    """Catalog document, its adapter pack id, and the selected working copy only."""
    from app.server import _formex_sources

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


def _git_toplevel(directory: Path) -> Path | None:
    try:
        found = subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if found.returncode != 0 or not found.stdout.strip():
        return None
    return Path(found.stdout.strip())


def _signature_rows(directory: Path, pack: dict, requirements: list, trust: dict) -> list[dict]:
    located = _paths_inside_repo(directory)
    repo = None
    paths: list[str] = []
    prefix = None
    if located is not None:
        repo, prefix, paths = located
    pack_result = verify_signature(
        complete_pack_digest(directory),
        pack.get("signed"),
        trust,
        repo=repo,
        paths=paths,
        tree_prefix=prefix,
    )
    rows = [_report_row("Pack", pack_result)]
    for requirement in requirements:
        relative = None
        if repo is not None and isinstance(requirement.get("id"), str):
            relative = (directory.resolve() / f"{requirement['id']}.json").relative_to(repo).as_posix()
        result = verify_signature(
            version_digest(requirement),
            requirement.get("signed"),
            trust,
            repo=repo,
            paths=[relative] if relative else None,
        )
        rows.append(_report_row(str(requirement.get("id") or "Requirement"), result))
    return rows


def _paths_inside_repo(directory: Path) -> tuple[Path, str, list[str]] | None:
    repo = _git_toplevel(directory)
    if repo is None:
        return None
    try:
        directory_real = directory.resolve()
        repo_real = repo.resolve()
        prefix = directory_real.relative_to(repo_real).as_posix()
        paths = sorted(
            path.resolve().relative_to(repo_real).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        )
    except ValueError:
        return None
    return repo_real, prefix, paths


def _report_row(title: str, result: dict) -> dict:
    return {
        "title": title,
        "status": result.get("status"),
        "method": result.get("method"),
        "signer": result.get("signer"),
        "version": result.get("version"),
        "reason": result.get("reason"),
    }


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
