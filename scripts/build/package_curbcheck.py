#!/usr/bin/env python3
"""Build and smoke-test curbcheck independently for the native host."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from package_common import ROOT, host_filename, host_label, package_binary, pyinstaller_args

DIST = ROOT / "dist" / "curbcheck"
DATAS = (("checks/available_checks.json", "checks"),)


def curbcheck_name(label: str) -> str:
    return host_filename("curbcheck", label)


def curbcheck_args(name: str) -> list[str]:
    return pyinstaller_args(name, "checks/__main__.py", DATAS, DIST)


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts" / "release"))
    from smoke import smoke_curbcheck

    filename = curbcheck_name(host_label(platform.system(), platform.machine()))
    return package_binary(filename, curbcheck_args(Path(filename).stem), DIST, smoke_curbcheck)


if __name__ == "__main__":
    raise SystemExit(main())
