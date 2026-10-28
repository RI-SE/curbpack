#!/usr/bin/env python3
"""Publish artifacts from an existing CI run. This script does not build."""

from __future__ import annotations

import argparse
import json
import os
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
    completed = _gh(
        ["run", "view", run_id, "--json", "conclusion,headSha,workflowName,jobs,createdAt,url"]
    )
    return json.loads(completed.stdout)


def latest_run_refusal(run: dict) -> str | None:
    """Refuse every run except the latest CI run on main once it has passed."""
    if run.get("conclusion") == "success":
        return None
    run_id = run.get("databaseId")
    status = run.get("status") or "unknown"
    conclusion = run.get("conclusion") or "none"
    url = run.get("url") or ""
    return (
        f"[FAIL] the latest CI run on main ({run_id}) has not passed ({status}, {conclusion}). "
        f"Release publishes that run only after it passes. {url}"
    ).rstrip()


def choose_tag(requested: str, created_at: str, taken) -> str:
    """Use the typed tag, or vYYYY.MM.DD from the CI run, with .2 .3 when that tag exists."""
    explicit = requested.strip()
    if explicit:
        if explicit.startswith("-") or " " in explicit:
            raise ValueError("publish needs a tag without spaces")
        return explicit
    day = created_at[:10]
    if len(day) != 10 or day[4] != "-" or day[7] != "-":
        raise ValueError("publish run has no date")
    base = "v" + day.replace("-", ".")
    if not taken(base):
        return base
    number = 2
    while taken(f"{base}.{number}"):
        number += 1
        if number > 20:
            raise ValueError(f"publish could not find a free tag after {base}")
    return f"{base}.{number}"


def _tag_exists(tag: str) -> bool:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        viewed = _gh(["repo", "view", "--json", "nameWithOwner"])
        repo = json.loads(viewed.stdout)["nameWithOwner"]
    completed = _gh(["api", f"repos/{repo}/git/ref/tags/{tag}"], check=False)
    return completed.returncode == 0


def _job_ok(record: dict, name: str) -> bool:
    for job in record.get("jobs") or []:
        if job.get("name") == name and job.get("conclusion") == "success":
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish a verified CI run without rebuilding.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--tag", default="")
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args(argv)
    run_id = args.run_id.strip()
    if not run_id:
        listed = _gh(
            [
                "run",
                "list",
                "--workflow",
                "ci.yml",
                "--branch",
                "main",
                "--limit",
                "1",
                "--json",
                "databaseId,status,conclusion,url",
            ]
        )
        runs = json.loads(listed.stdout)
        if not runs:
            print("[FAIL] publish found no CI run on main", flush=True)
            return 1
        refusal = latest_run_refusal(runs[0])
        if refusal:
            print(refusal, flush=True)
            return 1
        run_id = str(runs[0]["databaseId"])
    record = _run_record(run_id)
    if record.get("workflowName") != "CI":
        print("[FAIL] publish run is not the CI workflow", flush=True)
        return 1
    sha = record.get("headSha")
    if not isinstance(sha, str) or len(sha) < 7:
        print("[FAIL] publish run has no commit", flush=True)
        return 1
    try:
        tag = choose_tag(args.tag, str(record.get("createdAt") or ""), _tag_exists)
    except ValueError as exc:
        print(f"[FAIL] {exc}", flush=True)
        return 1
    if args.tag.strip() and _tag_exists(tag):
        print(f"[FAIL] publish tag {tag} already exists", flush=True)
        return 1
    if not _job_ok(record, "tests"):
        print("[FAIL] publish requires the tests job to have passed", flush=True)
        return 1
    if args.source_only:
        notes = f"{SOURCE_NOTE}\n\nCI run {run_id} at {sha}.\n"
        _gh(["release", "create", tag, "--target", sha, "--title", tag, "--notes", notes])
        print(f"[PASS] publish source-only {tag} {sha}", flush=True)
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
            _gh(["run", "download", run_id, "-n", name, "-D", str(destination)])
            if verify_directory(destination) != 0:
                print("[FAIL] publish refused a file that does not match SHA256SUMS", flush=True)
                return 1
            lines.append((destination / "SHA256SUMS").read_text(encoding="utf-8").strip())
            files.extend(
                path for path in destination.iterdir() if path.is_file() and path.name != "SHA256SUMS"
            )
        notes = (
            "These files are the binaries smoke-tested in CI run "
            f"{run_id} at {sha}. This release did not rebuild them.\n\n"
            + "\n".join(lines)
            + "\n"
        )
        _gh(
            ["release", "create", tag, "--target", sha, "--title", tag, "--notes", notes]
            + [str(path) for path in files]
        )
    print(f"[PASS] publish {tag} {sha}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
