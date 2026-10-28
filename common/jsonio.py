"""Pretty JSON on disk. Digests use `canonical.canonical_json`, not these bytes."""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path


def dump_text(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def write_json(path: Path, obj: object) -> None:
    """Replace the file in one step so a reader never sees a half-written document.

    The temporary file is created with the directory's own permissions. mkstemp's
    owner-only mode stays unreadable on the Windows CI runner after the replace.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(dump_text(obj))
        _replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _replace(temporary: Path, path: Path) -> None:
    """Retry when Windows still has the destination open for a poll."""
    denied: PermissionError | None = None
    for _ in range(8):
        try:
            os.replace(temporary, path)
            return
        except PermissionError as exc:
            denied = exc
            time.sleep(0.01)
    assert denied is not None
    raise denied


def read_json(path: Path) -> object:
    denied: PermissionError | None = None
    for _ in range(8):
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise
        except PermissionError as exc:
            # A replace in progress on Windows denies the reader for a moment.
            denied = exc
            time.sleep(0.01)
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    assert denied is not None
    raise denied
