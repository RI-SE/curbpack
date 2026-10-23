"""Read-only install root, separate from mutable workspace data."""

from __future__ import annotations

import sys
from pathlib import Path


def install_root() -> Path:
    """Repository root, or the frozen bundle directory when packaged."""
    bundled = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and bundled:
        return Path(bundled)
    return Path(__file__).resolve().parents[1]


def default_workspace() -> Path:
    """Mutable pilot data. A frozen app must not write inside its extract directory."""
    if getattr(sys, "frozen", False):
        return Path.home() / "curbpack-studio" / "workspace"
    return install_root() / "data" / "workspace"
