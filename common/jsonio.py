"""Pretty JSON on disk. Digests use `canonical.canonical_json`, not these bytes."""

from __future__ import annotations

import json
from pathlib import Path


def dump_text(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_text(obj), encoding="utf-8")


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
