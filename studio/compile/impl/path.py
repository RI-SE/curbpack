"""Where Compile writes the next review report.

This is the dated file under the configured reports directory. It is not
Review's fixed ``docs/reports/review-report.json`` path.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path


def _new_dated_json(folder: Path, prefix: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = folder / f"{prefix}_{stamp}.json"
        if not path.exists():
            return path
        time.sleep(1)


def _new_review_report_path(folder: Path) -> Path:
    return _new_dated_json(folder, "review-report")
