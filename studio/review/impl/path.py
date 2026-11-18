"""The fixed Review report path. Not Compile's configured output."""

from __future__ import annotations

from pathlib import Path


def durable_report_path(repo: Path) -> Path:
    """Conventional product-repo report. Not a configuration setting."""
    return Path(repo) / "docs" / "reports" / "review-report.json"
