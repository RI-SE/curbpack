"""Scaffold POST. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scaffold.stub import write_stub

if TYPE_CHECKING:
    from app.server import Workspace


def _write_scaffold(ws: Workspace, form: dict) -> str:
    write_stub(ws.repo, (form.get("path") or [""])[0].strip())
    return "/scaffold?wrote=1"
