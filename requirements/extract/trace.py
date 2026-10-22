"""Append-only diagnostic trace for propose/critique/revise.

The directory is not a Pack and not a Requirement. Events are appended and
flushed. Numbered call artifacts are written once. The manifest is rewritten
after each event so a crash still leaves a readable index.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from common.errors import ModelError


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Trace:
    def __init__(self, directory: Path | None, handle, run_id: str, enabled: bool):
        self.directory = directory
        self.run_id = run_id
        self.enabled = enabled
        self.status = "ok"
        self.outputs: list[dict] = []
        self.calls: list[dict] = []
        self._handle = handle
        self._started = False
        self._closed = False
        self._call_number = 0
        self._extra: dict = {}

    @classmethod
    def open(cls, directory: Path) -> Trace:
        if directory.exists():
            raise ModelError("produce", "trace_dir", f"a new directory, not {directory}")
        try:
            directory.mkdir(parents=True)
        except OSError as exc:
            raise ModelError("produce", "trace_dir", f"a directory that can be created ({exc})") from exc
        handle = (directory / "events.jsonl").open("a", encoding="utf-8")
        return cls(directory, handle, uuid.uuid4().hex, True)

    @classmethod
    def disabled(cls) -> Trace:
        return cls(None, None, "", False)

    def add_meta(self, meta: dict) -> None:
        self._extra.update(meta)

    def start(self, meta: dict) -> None:
        if self._started:
            return
        self._started = True
        payload = {"event": "run_start", "run_id": self.run_id, "started_at": now_utc()}
        payload.update(self._extra)
        payload.update(meta)
        self.event(payload)

    def next_call(self) -> int:
        self._call_number += 1
        return self._call_number

    def event(self, payload: dict) -> None:
        if not self.enabled:
            return
        if self._closed:
            raise ModelError("produce", "trace", "an open events file")
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        self._handle.write(line + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._write_manifest()

    def artifact(self, relative: str, text: str) -> str:
        if not self.enabled:
            return ""
        path = self.directory / relative
        if path.exists():
            raise ModelError("produce", "trace", f"an unused path, not {relative}")
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, text.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        return relative

    def add_call(self, record: dict) -> None:
        self.calls.append(record)

    def add_output(self, record: dict) -> None:
        self.outputs.append(record)

    def finish(self) -> None:
        if not self.enabled or self._closed:
            return
        pending = sys.exc_info()[1]
        if pending is not None and self.status == "ok":
            self.status = "failed"
        self._closed = True
        self._handle.write(
            json.dumps(
                {"ended_at": now_utc(), "event": "run_end", "status": self.status},
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()
        self._write_manifest()

    def _write_manifest(self) -> None:
        events = (self.directory / "events.jsonl").read_bytes()
        manifest = {
            "calls": self.calls,
            "events_sha256": hashlib.sha256(events).hexdigest(),
            "outputs": self.outputs,
            "run_id": self.run_id,
        }
        target = self.directory / "manifest.json"
        temporary = self.directory / "manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, target)
