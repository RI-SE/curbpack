#!/usr/bin/env python3
"""Fail when CI workflow job display names drift from branch-protection required contexts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ROOT / ".github" / "required-checks.json"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def parse_jobs(text: str) -> dict[str, dict[str, object]]:
    jobs: dict[str, dict[str, object]] = {}
    m = re.search(r"^jobs:\s*$", text, re.MULTILINE)
    if not m:
        return jobs
    block = text[m.end() :]
    for jm in re.finditer(r"^  ([a-zA-Z0-9_-]+):\s*$", block, re.MULTILINE):
        job_id = jm.group(1)
        start = jm.end()
        nxt = re.search(r"^  [a-zA-Z0-9_-]+:\s*$", block[start:], re.MULTILINE)
        job_block = block[start : start + nxt.start()] if nxt else block[start:]
        jobs[job_id] = {"block": job_block}
    return jobs


def job_display_name(job_id: str, job_block: str) -> str | None:
    nm = re.search(r"^\s+name:\s*(.+?)\s*$", job_block, re.MULTILINE)
    if nm:
        return nm.group(1).strip().strip("'\"")
    return job_id


def matrix_os_values(job_block: str) -> list[str]:
    mm = re.search(r"matrix:\s*\n\s+os:\s*\[(.*?)\]", job_block, re.DOTALL)
    if not mm:
        return []
    inner = mm.group(1)
    return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]


def expand_contexts(job_id: str, job_block: str) -> list[str]:
    name = job_display_name(job_id, job_block)
    if name is None:
        return []
    os_vals = matrix_os_values(job_block)
    if "${{ matrix.os }}" in name and os_vals:
        return [name.replace("${{ matrix.os }}", os_val) for os_val in os_vals]
    return [name]


def main() -> int:
    required = json.loads(REQUIRED.read_text())
    expected = set(required.get("contexts", []))
    if not expected:
        print("required-checks.json: empty contexts", file=sys.stderr)
        return 2

    ci_text = CI.read_text()
    jobs = parse_jobs(ci_text)
    actual: set[str] = set()
    for job_id, meta in jobs.items():
        block = str(meta["block"])
        actual.update(expand_contexts(job_id, block))

    missing = sorted(expected - actual)
    extra = sorted(actual - expected - {"windows-smoke", "required-check-drift", "pin-guard", "dogfood"})
    if missing or extra:
        print("required-check context drift detected", file=sys.stderr)
        if missing:
            print("  missing from ci.yml:", ", ".join(missing), file=sys.stderr)
        if extra:
            print("  in ci.yml but not required-checks.json:", ", ".join(extra), file=sys.stderr)
        print("  ci contexts:", ", ".join(sorted(actual)), file=sys.stderr)
        print("  expected:", ", ".join(sorted(expected)), file=sys.stderr)
        return 1

    print("required-check contexts OK:", ", ".join(sorted(expected)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
