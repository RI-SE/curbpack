#!/usr/bin/env python3
"""Run the mandatory CI checks, or exactly one when ONLY is set."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report import say

ROOT = Path(__file__).resolve().parents[2]
CHECKS = ("tests",)


def main() -> int:
    only = os.environ.get("ONLY", "").strip()
    if only and only not in CHECKS:
        print(f"[FAIL] unknown ONLY={only}", flush=True)
        print("valid: " + ", ".join(CHECKS), flush=True)
        return 1
    selected = (only,) if only else CHECKS
    failed = False
    for name in selected:
        script = ROOT / "scripts" / "ci" / "checks" / f"{name}.py"
        completed = subprocess.run([sys.executable, str(script)], cwd=ROOT)
        if completed.returncode != 0:
            failed = True
    say(not failed, "ci-tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
