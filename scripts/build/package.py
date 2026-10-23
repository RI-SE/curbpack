#!/usr/bin/env python3
"""Build one PyInstaller binary for the OS that is running this script, then smoke-test it."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
WORK = ROOT / "build" / "pyinstaller"

DATAS = (
    ("requirements/extract/adapters", "requirements/extract/adapters"),
    ("requirements/extract/data", "requirements/extract/data"),
    ("requirements/extract/guidance", "requirements/extract/guidance"),
    ("requirements/ui/vendor", "requirements/ui/vendor"),
    ("checks/available_checks.json", "checks"),
)


def host_label(system: str, machine: str) -> str:
    """The pilot ships two host builds. This script does not cross-compile."""
    machine = machine.lower()
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "macos-arm64"
    if system == "Windows" and machine in {"amd64", "x86_64"}:
        return "windows-x64"
    raise SystemExit(
        f"[FAIL] package builds only for the host it runs on. "
        f"{system} {machine} is not Windows x64 or macOS ARM64."
    )


def binary_name(label: str) -> str:
    name = f"curbpack-studio-{label}"
    if label.startswith("windows"):
        return name + ".exe"
    return name


def _pyinstaller_args(name: str) -> list[str]:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--name",
        name,
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK),
        "--specpath",
        str(WORK),
        "--paths",
        str(ROOT),
        "--additional-hooks-dir",
        str(ROOT / "scripts" / "build" / "hooks"),
    ]
    separator = os.pathsep
    for source, dest in DATAS:
        args.extend(["--add-data", f"{ROOT / source}{separator}{dest}"])
    args.append(str(ROOT / "app" / "__main__.py"))
    return args


def write_sums(binary: Path) -> Path:
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    sums = DIST / "SHA256SUMS"
    sums.write_text(f"{digest}  {binary.name}\n", encoding="utf-8")
    return sums


def main() -> int:
    import platform

    label = host_label(platform.system(), platform.machine())
    name = binary_name(label)
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[FAIL] package requires PyInstaller in this interpreter", flush=True)
        return 1
    DIST.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(_pyinstaller_args(Path(name).stem), cwd=ROOT)
    if completed.returncode != 0:
        print("[FAIL] package", flush=True)
        return completed.returncode
    binary = DIST / name
    if not binary.is_file():
        print(f"[FAIL] package did not write {binary}", flush=True)
        return 1
    sys.path.insert(0, str(ROOT / "scripts" / "release"))
    from smoke import smoke

    if smoke(binary) != 0:
        print("[FAIL] package", flush=True)
        return 1
    sums = write_sums(binary)
    print(f"[PASS] package {binary.name}", flush=True)
    print(f"[PASS] wrote {sums.name} after the smoke test", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
