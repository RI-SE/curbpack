#!/usr/bin/env python3
"""Shared native PyInstaller invocation and checksum writing."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
WORK = ROOT / "build" / "pyinstaller"


def host_label(system: str, machine: str) -> str:
    """Label the native build host. This script does not cross-compile."""
    machine = machine.lower()
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "macos-arm64"
    if system == "Windows" and machine in {"amd64", "x86_64"}:
        return "windows-x64"
    if system == "Linux" and machine in {"amd64", "x86_64"}:
        return "linux-x64"
    raise SystemExit(
        f"[FAIL] package builds only for the host it runs on. "
        f"{system} {machine} is not Windows x64, macOS ARM64 or Linux x64."
    )


def host_filename(prefix: str, label: str) -> str:
    name = f"{prefix}-{label}"
    if label.startswith("windows"):
        return name + ".exe"
    return name


def pyinstaller_args(name: str, entry: str, datas: tuple[tuple[str, str], ...], dist: Path) -> list[str]:
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
        str(dist),
        "--workpath",
        str(WORK / name),
        "--specpath",
        str(WORK / name),
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


def write_sums(binaries: list[Path], directory: Path | None = None) -> Path:
    lines = []
    for binary in binaries:
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        lines.append(f"{digest}  {binary.name}")
    sums = (DIST if directory is None else directory) / "SHA256SUMS"
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums


def _build(args: list[str], filename: str, dist: Path) -> Path | None:
    completed = subprocess.run(args, cwd=ROOT)
    if completed.returncode != 0:
        print("[FAIL] package", flush=True)
        return None
    binary = dist / filename
    if not binary.is_file():
        print(f"[FAIL] package did not write {binary}", flush=True)
        return None
    return binary


def package_binary(filename: str, args: list[str], dist: Path, smoke_test) -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[FAIL] package requires PyInstaller in this interpreter", flush=True)
        return 1
    dist.mkdir(parents=True, exist_ok=True)
    binary = _build(args, filename, dist)
    if binary is None:
        return 1
    if smoke_test(binary) != 0:
        print(f"[FAIL] package {filename}", flush=True)
        return 1
    sums = write_sums([binary], dist)
    print(f"[PASS] package {filename}", flush=True)
    print(f"[PASS] wrote {sums} after the smoke test", flush=True)
    return 0
