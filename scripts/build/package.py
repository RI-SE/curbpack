#!/usr/bin/env python3
"""Build the Studio application and curbcheck for the OS running this script, then smoke-test both."""

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
CURBCHECK_DATAS = (("checks/available_checks.json", "checks"),)


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


def _host_filename(prefix: str, label: str) -> str:
    name = f"{prefix}-{label}"
    if label.startswith("windows"):
        return name + ".exe"
    return name


def studio_name(label: str) -> str:
    return _host_filename("curbpack-studio", label)


def binary_name(label: str) -> str:
    return studio_name(label)


def curbcheck_name(label: str) -> str:
    return _host_filename("curbcheck", label)


def _pyinstaller_args(name: str, entry: str, datas: tuple[tuple[str, str], ...]) -> list[str]:
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
    for source, dest in datas:
        args.extend(["--add-data", f"{ROOT / source}{separator}{dest}"])
    args.append(str(ROOT / entry))
    return args


def studio_args(name: str) -> list[str]:
    return _pyinstaller_args(name, "app/__main__.py", DATAS)


def curbcheck_args(name: str) -> list[str]:
    return _pyinstaller_args(name, "checks/__main__.py", CURBCHECK_DATAS)


def write_sums(binaries: list[Path]) -> Path:
    lines = []
    for binary in binaries:
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        lines.append(f"{digest}  {binary.name}")
    sums = DIST / "SHA256SUMS"
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums


def _build(args: list[str], filename: str) -> Path | None:
    completed = subprocess.run(args, cwd=ROOT)
    if completed.returncode != 0:
        print("[FAIL] package", flush=True)
        return None
    binary = DIST / filename
    if not binary.is_file():
        print(f"[FAIL] package did not write {binary}", flush=True)
        return None
    return binary


def main() -> int:
    import platform

    label = host_label(platform.system(), platform.machine())
    studio = studio_name(label)
    checker = curbcheck_name(label)
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[FAIL] package requires PyInstaller in this interpreter", flush=True)
        return 1
    DIST.mkdir(parents=True, exist_ok=True)
    studio_binary = _build(studio_args(Path(studio).stem), studio)
    if studio_binary is None:
        return 1
    sys.path.insert(0, str(ROOT / "scripts" / "release"))
    from smoke import smoke, smoke_curbcheck

    if smoke(studio_binary) != 0:
        print("[FAIL] package", flush=True)
        return 1
    print(f"[PASS] package {studio_binary.name}", flush=True)
    checker_binary = _build(curbcheck_args(Path(checker).stem), checker)
    if checker_binary is None:
        return 1
    if smoke_curbcheck(checker_binary) != 0:
        print("[FAIL] package", flush=True)
        return 1
    if not studio_binary.is_file():
        print(f"[FAIL] package removed {studio_binary.name} while building curbcheck", flush=True)
        return 1
    sums = write_sums([studio_binary, checker_binary])
    print(f"[PASS] package {checker_binary.name}", flush=True)
    print(f"[PASS] wrote {sums.name} after the smoke test", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
