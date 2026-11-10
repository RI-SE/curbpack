"""Demo requirement GET. The URL stays on the old server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.requirement_page import requirement_page
from common.store import load_requirement
from workflow import snapshot

if TYPE_CHECKING:
    from app.server import Workspace


def _demo_requirement(ws: Workspace) -> bytes:
    from app.server import _require_demo_requirement

    requirement = load_requirement(_require_demo_requirement(ws))
    reading = snapshot(ws.root)["requirement_reading"]
    return requirement_page(requirement, reading)
