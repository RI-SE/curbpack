"""Canonical JSON and the pack directory digest.

`packs2.md` §2.6 says "canonical JSON" and "each file's bytes hashed, then
combine" without naming the serializer. PoC2 uses one rule, here, so every
digest in this process is the same bytes:

- objects: UTF-8 JSON, keys sorted, no insignificant whitespace
- version digest: SHA-256 hex of that JSON with the whole `signed` block removed
- pack directory digest: SHA-256 hex of sorted relative paths, each followed by
  the SHA-256 hex of that file's bytes. `pack.json` is included with
  `signed.signature` cleared to an empty string and then re-encoded with the
  same canonical JSON. Dotfiles are ignored.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def without_signed(obj: dict) -> dict:
    return {key: value for key, value in obj.items() if key != "signed"}


def version_digest(obj: dict) -> str:
    payload = canonical_json(without_signed(obj)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack_json_bytes_for_digest(doc: dict) -> bytes:
    signed = doc.get("signed")
    if isinstance(signed, dict):
        cleared = dict(doc)
        cleared_signed = dict(signed)
        cleared_signed["signature"] = ""
        cleared["signed"] = cleared_signed
        doc = cleared
    return canonical_json(doc).encode("utf-8")


def pack_directory_digest(root: Path) -> str:
    rows: list[str] = []
    files = [path for path in root.rglob("*") if path.is_file() and not any(part.startswith(".") for part in path.relative_to(root).parts)]
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if rel == "pack.json":
            doc = json.loads(path.read_text(encoding="utf-8"))
            data = pack_json_bytes_for_digest(doc)
        else:
            data = path.read_bytes()
        rows.append(f"{rel}\n{_sha256(data)}\n")
    return _sha256("".join(rows).encode("utf-8"))
