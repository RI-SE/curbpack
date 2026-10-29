#!/usr/bin/env python3
"""Build and smoke-test curbpack-studio independently for the native host."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from package_common import ROOT, host_filename, host_label, package_binary, pyinstaller_args

DIST = ROOT / "dist" / "studio"
DATAS = (
    ("requirements/extract/adapters", "requirements/extract/adapters"),
    ("requirements/extract/data", "requirements/extract/data"),
    ("requirements/extract/guidance", "requirements/extract/guidance"),
    ("requirements/ui/vendor", "requirements/ui/vendor"),
    ("checks/available_checks.json", "checks"),
)


def studio_name(label: str) -> str:
    return host_filename("curbpack-studio", label)


def studio_args(name: str) -> list[str]:
    return pyinstaller_args(name, "app/__main__.py", DATAS, DIST)


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts" / "release"))
    from smoke import smoke

    filename = studio_name(host_label(platform.system(), platform.machine()))
    return package_binary(filename, studio_args(Path(filename).stem), DIST, smoke)


if __name__ == "__main__":
    raise SystemExit(main())
