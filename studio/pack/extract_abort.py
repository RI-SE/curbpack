"""Extract job abort POST. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from requirements.jobs import request_abort

if TYPE_CHECKING:
    from app.server import Workspace


def _abort_extract(ws: Workspace, job_id: str, form: dict) -> str:
    request_abort(ws.root / "jobs", job_id)
    document_id = (form.get("document") or [""])[0].strip()
    located = f"document={document_id}&" if document_id else ""
    return f"/requirements?{located}job={job_id}"
