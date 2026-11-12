"""Extract POST. The URL stays on the old server."""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

from common.errors import ModelError
from common.validate import pack_namespace
from requirements.extract.pipeline import draft_pack
from requirements.jobs import start_extract_job
from requirements.workspace import mark_source_adapter, selected_source_adapter

if TYPE_CHECKING:
    from app.server import Workspace


def _namespace_base_at(repo: Path | None) -> str:
    """RISE when there is no repository file. Otherwise the file's namespace_base."""
    if repo is None:
        return "RISE"
    path = repo / "curbpack.json"
    if not path.is_file():
        return "RISE"
    from common.jsonio import read_json
    from common.validate import validate_curbpack_config

    return str(validate_curbpack_config(read_json(path))["namespace_base"])


def _pack_for_adapter(adapter: dict, namespace_base: str) -> dict:
    if adapter.get("id") == "cra":
        pack = draft_pack()
        pack["namespace"] = pack_namespace(namespace_base, str(pack["name"]))
        return pack
    name = f"{adapter['id']} extract"
    return {
        "id": adapter["pack_id"],
        "name": name,
        "version": "0.1.0",
        "namespace": pack_namespace(namespace_base, name),
        "status": "draft",
    }


def _start_extract(ws: Workspace, form: dict) -> str:
    from app.server import _load_adapter, _locate_repo_pack

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
    document_id = (form.get("document_id") or [""])[0].strip()
    repo_id = (form.get("repo") or [""])[0].strip()
    dest_repo = ""
    dest_pack = ""
    repo_path = None
    if repo_id:
        from app.server import _registered_repo_path

        repo_path = _registered_repo_path(ws, repo_id)
    if document_id:
        found = _locate_repo_pack(ws, document_id, repo_id)
        if found is not None:
            dest_repo = found[0]
            dest_pack = document_id
    job_id = f"extract-{secrets.token_hex(4)}"
    start_extract_job(
        ws.root / "jobs",
        job_id=job_id,
        root=ws.root,
        adapter_dir=adapter_dir,
        section_id=section_id,
        pack=_pack_for_adapter(adapter, _namespace_base_at(repo_path)),
        dest_repo=dest_repo,
        dest_pack=dest_pack,
    )
    located = f"document={document_id}&" if document_id else ""
    repo_id = (form.get("repo") or [""])[0].strip()
    if repo_id:
        located += f"repo={quote(repo_id, safe='')}&"
    return f"/requirements?{located}job={job_id}&adapter={adapter_id}"
