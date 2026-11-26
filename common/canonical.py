"""Canonical JSON and the pack directory digest.

`packs2.md` §2.6 says "canonical JSON" and "each file's bytes hashed, then
combine" without naming the serializer. PoC2 uses one rule, here, so every
digest in this process is the same bytes:

- objects: UTF-8 JSON, keys sorted, no insignificant whitespace
- version digest: SHA-256 hex of that JSON with `signed` and `format_version` removed
- pack directory digest: SHA-256 hex of sorted relative paths, each followed by
  the SHA-256 hex of that file's bytes. `pack.json` is included with
  `signed.signature` cleared to an empty string, `format_version` removed, and
  then re-encoded with the same canonical JSON. Every other file keeps its raw
  bytes when `format_version` is absent. A file that has the key is hashed as
  `dump_text` of the same object with that key removed, using the newline
  sequence already in that file, which matches the bytes written before the
  key was added. Every file is included, including dotfiles.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from common.jsonio import dump_text


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def without_signed(obj: dict) -> dict:
    return {key: value for key, value in obj.items() if key != "signed"}


def without_format_version(obj: dict) -> dict:
    if "format_version" not in obj:
        return obj
    return {key: value for key, value in obj.items() if key != "format_version"}


def version_digest(obj: dict) -> str:
    payload = canonical_json(without_signed(without_format_version(obj))).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack_json_bytes_for_digest(doc: dict) -> bytes:
    doc = without_format_version(doc)
    signed = doc.get("signed")
    if isinstance(signed, dict):
        cleared = dict(doc)
        cleared_signed = dict(signed)
        cleared_signed["signature"] = ""
        cleared["signed"] = cleared_signed
        doc = cleared
    return canonical_json(doc).encode("utf-8")


def _bytes_ignoring_format_version(path: Path) -> bytes:
    """Raw bytes, unless the file is a JSON object that carries `format_version`.

    A file without the key keeps today's hash. A file with the key is hashed as
    `dump_text` of the same object with the key removed. Text-mode writers on
    Windows store that pretty JSON with CRLF, so the hash uses the newline
    sequence already in the file.
    """
    data = path.read_bytes()
    try:
        parsed = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return data
    if not isinstance(parsed, dict) or "format_version" not in parsed:
        return data
    text = dump_text(without_format_version(parsed))
    if b"\r\n" in data:
        text = text.replace("\n", "\r\n")
    return text.encode("utf-8")


def pack_directory_digest(root: Path) -> str:
    rows: list[str] = []
    files = [path for path in root.rglob("*") if path.is_file()]
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if rel == "pack.json":
            doc = json.loads(path.read_text(encoding="utf-8"))
            data = pack_json_bytes_for_digest(doc)
        else:
            data = _bytes_ignoring_format_version(path)
        rows.append(f"{rel}\n{_sha256(data)}\n")
    return _sha256("".join(rows).encode("utf-8"))
