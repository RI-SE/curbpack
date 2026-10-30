#!/usr/bin/env python3
"""Publish artifacts from an existing CI run. This script does not build."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import verify_directory

SOURCE_NOTE = (
    "This release is source only. "
    "Standalone Windows x64, macOS ARM64 and Linux x64 binaries are not included. "
    "A checkout of this tag starts with `make start`."
)


def _parse_sums(sum_texts: list[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for text in sum_texts:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            digest, separator, name = stripped.partition("  ")
            if separator != "  " or len(digest) != 64 or not name or "/" in name or "\\" in name:
                raise ValueError(f"publish sums line is not usable: {stripped}")
            parsed.append((digest, name))
    named = {name for _digest, name in parsed}
    if len(named) != len(parsed):
        raise ValueError("publish sums name a file more than once")
    mac = [name for _digest, name in parsed if "macos" in name]
    windows = [name for _digest, name in parsed if "windows" in name]
    linux = [name for _digest, name in parsed if "linux" in name]
    installers = [name for _digest, name in parsed if name in {
        "install-studio.sh", "install-curbcheck.sh", "install-studio.ps1", "install-curbcheck.ps1",
    }]
    if len(mac) + len(windows) + len(linux) + len(installers) != len(parsed):
        raise ValueError("publish sums name a file this note cannot check")
    if not parsed:
        raise ValueError("publish sums name no binary")
    return parsed


def _mac_hash_check(entries: list[tuple[str, str]]) -> str:
    lines = "\n".join(f"{digest}  {name}" for digest, name in entries)
    return f"shasum -a 256 -c <<'EOF'\n{lines}\nEOF"


def _windows_hash_check(entries: list[tuple[str, str]]) -> str:
    quoted = ",\n".join(f"  '{digest}  {name}'" for digest, name in entries)
    return (
        "@(\n"
        f"{quoted}\n"
        ") | ForEach-Object {\n"
        "  $digest, $name = $_ -split '  ', 2\n"
        "  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $name).Hash.ToLowerInvariant()\n"
        '  if ($actual -eq $digest) { "${name}: OK" } else { "${name}: FAILED" }\n'
        "}"
    )


def binary_notes(sum_texts: list[str], repo: str, tag: str) -> str:
    """Release text: curl to run, and a hash check that prints OK."""
    if not repo or "/" not in repo or " " in repo or " " in tag or not tag:
        raise ValueError("publish needs a repository and a tag")
    parsed = _parse_sums(sum_texts)
    base = f"https://github.com/{repo}/releases/download/{quote(tag, safe='')}"
    mac = [(digest, name) for digest, name in parsed if "macos" in name]
    windows = [(digest, name) for digest, name in parsed if "windows" in name]
    linux = [(digest, name) for digest, name in parsed if "linux" in name]
    blocks = []
    if any(name == "install-studio.sh" for _digest, name in parsed):
        blocks.append(
            "Install Studio (includes curbcheck) on macOS/Linux:\n\n"
            "```sh\n"
            f"curl -fsSL {base}/install-studio.sh -o install-studio.sh "
            f"&& CURBPACK_VERSION={shlex.quote(tag)} sh install-studio.sh\n"
            "```\n\n"
            "For the checker alone, use `install-curbcheck.sh`. "
            "On Windows use `install-studio.ps1` or `install-curbcheck.ps1`.\n\n"
            "Manual installation:\n"
        )
    if mac:
        curls = "\n".join(f"curl -fsSL -O {base}/{name}" for _digest, name in mac)
        names = " ".join(name for _digest, name in mac)
        studio = next((name for _digest, name in mac if name.startswith("curbpack-studio")), None)
        command = studio or mac[0][1] + " --help"
        blocks.append(
            "macOS\n\n"
            "To download and run:\n\n"
            "```sh\n"
            f"{curls}\n"
            f"chmod +x {names}\n"
            f"./{command}\n"
            "```\n\n"
            "To check the hash:\n\n"
            "```sh\n"
            f"{_mac_hash_check(mac)}\n"
            "```\n"
        )
    if windows:
        curls = "\n".join(f"curl.exe -fsSL -O {base}/{name}" for _digest, name in windows)
        studio = next((name for _digest, name in windows if name.startswith("curbpack-studio")), None)
        command = studio or windows[0][1] + " --help"
        blocks.append(
            "Windows\n\n"
            "To download and run:\n\n"
            "```powershell\n"
            f"{curls}\n"
            f".\\{command}\n"
            "```\n\n"
            "To check the hash:\n\n"
            "```powershell\n"
            f"{_windows_hash_check(windows)}\n"
            "```\n"
        )
    if linux:
        curls = "\n".join(f"curl -fsSL -O {base}/{name}" for _digest, name in linux)
        names = " ".join(name for _digest, name in linux)
        studio = next((name for _digest, name in linux if name.startswith("curbpack-studio")), None)
        command = studio or linux[0][1] + " --help"
        sums = "\n".join(f"{digest}  {name}" for digest, name in linux)
        blocks.append(
            "Linux x64\n\n"
            "To download and run:\n\n"
            "```sh\n"
            f"{curls}\n"
            f"chmod +x {names}\n"
            f"./{command}\n"
            "```\n\n"
            "To check the hash:\n\n"
            "```sh\n"
            f"sha256sum -c <<'EOF'\n{sums}\nEOF\n"
            "```\n"
        )
    notes = "\n".join(blocks)
    if any(name.startswith("curbpack-studio") for _digest, name in parsed):
        notes += "\nThe process prints a local URL. Open it. The usual one is http://127.0.0.1:8770.\n"
    return notes


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


def _repository() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if repo:
        return repo
    viewed = _gh(["repo", "view", "--json", "nameWithOwner"])
    return json.loads(viewed.stdout)["nameWithOwner"]


def _tag_exists(tag: str) -> bool:
    completed = _gh(["api", f"repos/{_repository()}/git/ref/tags/{tag}"], check=False)
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
        listed = _gh([
            "api", f"repos/{_repository()}/actions/runs/{run_id}/artifacts",
            "--paginate", "--jq", ".artifacts[].name",
        ])
        artifacts = sorted(
            name for name in listed.stdout.splitlines()
            if name.startswith(("curbpack-studio-", "curbcheck-")) or name == "curbpack-installers"
        )
        if not artifacts:
            print("[FAIL] publish found no package artifacts", flush=True)
            return 1
        for name in artifacts:
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
        try:
            notes = binary_notes(lines, _repository(), tag)
        except ValueError as exc:
            print(f"[FAIL] {exc}", flush=True)
            return 1
        sums = root / "SHA256SUMS"
        sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _gh(
            ["release", "create", tag, "--target", sha, "--title", tag, "--notes", notes]
            + [str(path) for path in files] + [str(sums)]
        )
    print(f"[PASS] publish {tag} {sha}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
