#!/usr/bin/env python3
"""Run the functional tests. make test and the CI tests check both call this."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from report import say

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
    )
    say(completed.returncode == 0, "tests")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
