#!/usr/bin/env python3
"""Check SHA-256 of files named in SHA256SUMS. Does not build or publish."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def verify_directory(directory: Path) -> int:
    sums = directory / "SHA256SUMS"
    if not sums.is_file():
        print(f"[FAIL] verify missing {sums}", flush=True)
        return 1
    lines = [line for line in sums.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        print("[FAIL] verify SHA256SUMS is empty", flush=True)
        return 1
    for line in lines:
        digest, separator, name = line.partition("  ")
        if separator != "  " or len(digest) != 64 or not name or "/" in name or "\\" in name:
            print(f"[FAIL] verify bad sums line: {line}", flush=True)
            return 1
        target = directory / name
        if not target.is_file():
            print(f"[FAIL] verify missing {name}", flush=True)
            return 1
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            print(f"[FAIL] verify {name} sha256 {actual} != {digest}", flush=True)
            return 1
        print(f"[PASS] verify {name} {digest}", flush=True)
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify.py <directory>", flush=True)
        return 2
    return verify_directory(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())
