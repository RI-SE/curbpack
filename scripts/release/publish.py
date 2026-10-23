#!/usr/bin/env python3
"""Publish artifacts from an existing CI run. This script does not build."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import verify_directory

ARTIFACTS = ("curbpack-studio-macos-arm64", "curbpack-studio-windows-x64")
SOURCE_NOTE = (
    "This release is source only. "
    "The requirement for standalone Windows x64 and macOS ARM64 binaries is not met. "
    "A checkout of this tag starts with `make start`."
)


def _gh(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], check=check, capture_output=True, text=True)


def _run_record(run_id: str) -> dict:
    completed = _gh(["run", "view", run_id, "--json", "conclusion,headSha,workflowName,jobs"])
    return json.loads(completed.stdout)


def _job_ok(record: dict, name: str) -> bool:
    for job in record.get("jobs") or []:
        if job.get("name") == name and job.get("conclusion") == "success":
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish a verified CI run without rebuilding.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.tag or args.tag.startswith("-") or " " in args.tag:
        print("[FAIL] publish needs an explicit tag", flush=True)
        return 1
    record = _run_record(args.run_id)
    if record.get("workflowName") != "CI":
        print("[FAIL] publish run is not the CI workflow", flush=True)
        return 1
    sha = record.get("headSha")
    if not isinstance(sha, str) or len(sha) < 7:
        print("[FAIL] publish run has no commit", flush=True)
        return 1
    if not _job_ok(record, "tests"):
        print("[FAIL] publish requires the tests job to have passed", flush=True)
        return 1
    if args.source_only:
        notes = f"{SOURCE_NOTE}\n\nCI run {args.run_id} at {sha}.\n"
        _gh(["release", "create", args.tag, "--target", sha, "--title", args.tag, "--notes", notes])
        print(f"[PASS] publish source-only {args.tag} {sha}", flush=True)
        return 0
    if record.get("conclusion") != "success":
        print("[FAIL] publish binaries requires the CI run to have passed", flush=True)
        return 1
    with tempfile.TemporaryDirectory(prefix="curbpack-release-") as tmp:
        root = Path(tmp)
        files: list[Path] = []
        lines = []
        for name in ARTIFACTS:
            destination = root / name
            destination.mkdir()
            _gh(["run", "download", args.run_id, "-n", name, "-D", str(destination)])
            if verify_directory(destination) != 0:
                print("[FAIL] publish refused a file that does not match SHA256SUMS", flush=True)
                return 1
            lines.append((destination / "SHA256SUMS").read_text(encoding="utf-8").strip())
            files.extend(
                path for path in destination.iterdir() if path.is_file() and path.name != "SHA256SUMS"
            )
        notes = (
            "These files are the binaries smoke-tested in CI run "
            f"{args.run_id} at {sha}. This release did not rebuild them.\n\n"
            + "\n".join(lines)
            + "\n"
        )
        _gh(
            ["release", "create", args.tag, "--target", sha, "--title", args.tag, "--notes", notes]
            + [str(path) for path in files]
        )
    print(f"[PASS] publish {args.tag} {sha}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
