"""Prepare POST. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from demo_setup import prepare_demo

if TYPE_CHECKING:
    from app.server import Workspace


def _prepare_workspace(ws: Workspace) -> str:
    prepare_demo(ws.root)
    return "/?prepared=1"
