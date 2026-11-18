"""Saved reports Review can open. Compile still names the next file."""

from __future__ import annotations

from pathlib import Path


def _dated_entries(folder: Path, prefix: str) -> list[dict]:
    rows = []
    for path in sorted(folder.glob(f"{prefix}_*.json")):
        if path.is_file():
            rows.append({"name": path.name, "path": str(path.resolve())})
    return rows


def _confined_review_report_path(reports_folder: str, requested: str) -> str:
    if not reports_folder:
        return ""
    folder = Path(reports_folder).resolve()
    wanted = (requested or "").strip()
    if wanted:
        path = Path(wanted).resolve()
        try:
            path.relative_to(folder)
        except ValueError:
            path = None
        if path is not None and path.is_file() and path.name.startswith("review-report_") and path.name.endswith(".json"):
            return str(path)
    dated = sorted(folder.glob("review-report_*.json"))
    if dated:
        return str(dated[-1].resolve())
    return ""
