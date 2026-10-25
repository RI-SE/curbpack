#!/usr/bin/env python3
"""Start a built binary and read its local cover page. Does not rebuild."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=2) as response:
        return response.read().decode("utf-8", errors="replace")


def smoke(binary: Path) -> int:
    if not binary.is_file():
        print(f"[FAIL] smoke missing binary {binary}", flush=True)
        return 1
    port = _free_port()
    with tempfile.TemporaryDirectory(prefix="curbpack-smoke-") as tmp:
        workspace = Path(tmp)
        process = subprocess.Popen(
            [
                str(binary),
                "--workspace",
                str(workspace),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        url = f"http://127.0.0.1:{port}/"
        body = ""
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    output = process.stdout.read() if process.stdout else ""
                    print(output, flush=True)
                    print("[FAIL] smoke binary exited before the cover page", flush=True)
                    return 1
                try:
                    with urllib.request.urlopen(url, timeout=2) as response:
                        body = response.read().decode("utf-8", errors="replace")
                    break
                except Exception:
                    time.sleep(0.2)
            else:
                print("[FAIL] smoke cover page did not respond", flush=True)
                return 1
            if "Curbpack" not in body or "Review" not in body:
                print("[FAIL] smoke cover page is not the pilot", flush=True)
                return 1
            vendor = _get(f"http://127.0.0.1:{port}/vendor/jsondiffpatch.js")
            if "jsondiffpatch" not in vendor:
                print("[FAIL] smoke did not read the bundled UI resource", flush=True)
                return 1
            requirements = _get(f"http://127.0.0.1:{port}/requirements")
            if "cra-xml" not in requirements:
                print("[FAIL] smoke did not read the bundled adapters", flush=True)
                return 1
            if not workspace.is_dir():
                print("[FAIL] smoke workspace was not the directory passed to the binary", flush=True)
                return 1
            print(f"[PASS] smoke {binary.name}", flush=True)
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _git(repo: Path, *args: str, when: str | None = None) -> None:
    env = os.environ.copy()
    if when is not None:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env, capture_output=True, text=True)


def _curbcheck_repo(root: Path) -> tuple[Path, Path]:
    """A temp product whose exist, contents, git_fresh, and git_author claims can pass."""
    sys.path.insert(0, str(root))
    repo = Path(tempfile.mkdtemp(prefix="curbcheck-smoke-"))
    packs = repo.parent / f"{repo.name}-packs"
    try:
        return _fill_curbcheck_repo(repo, packs)
    except Exception:
        shutil.rmtree(repo, ignore_errors=True)
        shutil.rmtree(packs, ignore_errors=True)
        raise


def _fill_curbcheck_repo(repo: Path, packs: Path) -> tuple[Path, Path]:
    from claims.bind import build_claim, write_claim
    from common.store import save_pack, save_requirement
    from requirements.editing import apply_edits
    from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk

    docs = repo / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("hello\n", encoding="utf-8")
    when = "2026-10-23T12:00:00Z"
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "poc2@example.com")
    _git(repo, "config", "user.name", "PoC2")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "add", "docs/a.md")
    _git(repo, "commit", "-m", "add doc", when=when)
    pack_dir = packs / "cra-baseline"
    source = dict(extract_annex_vii_risk()["source"])
    source["edition"] = "2024-11-20"
    requirement = apply_edits(extract_annex_vii_risk(), {"source": source})
    save_pack(pack_dir, draft_pack())
    save_requirement(pack_dir, requirement)
    (repo / "curbpack.json").write_text('{"packs":["cra-baseline"]}\n', encoding="utf-8")
    claims = [
        ("claim-exist", [{"check": "exist", "args": {"paths": ["docs/a.md"]}}]),
        (
            "claim-contents",
            [{"check": "contents", "args": {"path": "docs/a.md", "probes": [{"kind": "pattern", "pattern": "SECRET"}]}}],
        ),
        (
            "claim-fresh",
            [{"check": "git_fresh", "args": {"path": "docs/a.md", "max_age_days": 0, "as_of": when}}],
        ),
        (
            "claim-author",
            [{"check": "git_author", "args": {"path": "docs/a.md", "name": "PoC2", "email": "poc2@example.com"}}],
        ),
        (
            "claim-signed",
            [{"check": "git_signed", "args": {"path": "docs/a.md", "allowed_signers": ".git-allowed-signers"}}],
        ),
        (
            "claim-signer",
            [
                {
                    "check": "git_signer",
                    "args": {"path": "docs/a.md", "signer": "PoC2", "allowed_signers": ".git-allowed-signers"},
                }
            ],
        ),
        (
            "claim-dep",
            [{"check": "dep_ban", "args": {"package": "axios", "banned_versions": ["1.0.0"]}}],
        ),
    ]
    for claim_id, checks in claims:
        write_claim(
            repo / "claims",
            build_claim(
                claim_id=claim_id,
                requirement_id="CRA-ANNEX-VII-RISK",
                source="documents",
                args={"path": "docs/a.md"},
                checks=checks,
                severity="high",
                description="The file is the reviewed evidence.",
            ),
        )
    return repo, packs


def _run_curbcheck(binary: Path, repo: Path, packs: Path, out: Path, skip: str | None = None) -> subprocess.CompletedProcess:
    argv = [str(binary), "--repo", str(repo), "--packs", str(packs), "--out", str(out)]
    if skip is not None:
        argv.extend(["--skip", skip])
    return subprocess.run(argv, capture_output=True, text=True, timeout=120)


def smoke_curbcheck(binary: Path) -> int:
    if not binary.is_file():
        print(f"[FAIL] smoke missing binary {binary}", flush=True)
        return 1
    root = Path(__file__).resolve().parents[2]
    repo = None
    packs = None
    try:
        repo, packs = _curbcheck_repo(root)
        out = repo / "run-result.json"
        completed = _run_curbcheck(binary, repo, packs, out)
        if not out.is_file():
            print(completed.stdout, flush=True)
            print(completed.stderr, flush=True)
            print("[FAIL] smoke curbcheck wrote no run result", flush=True)
            return 1
        result = json.loads(out.read_text(encoding="utf-8"))
        by_id = {row["id"]: row for row in result["claims"]}
        expected = {
            "claim-exist": "pass",
            "claim-contents": "pass",
            "claim-fresh": "pass",
            "claim-author": "pass",
            "claim-signed": "fail",
            "claim-signer": "fail",
            "claim-dep": "fail",
        }
        for claim_id, status in expected.items():
            row = by_id.get(claim_id)
            if row is None or row["status"] != status:
                print(completed.stdout, flush=True)
                print(completed.stderr, flush=True)
                print(f"[FAIL] smoke curbcheck {claim_id} is not {status}", flush=True)
                return 1
        signed = by_id["claim-signed"]["checks"][0].get("detail", "")
        signer = by_id["claim-signer"]["checks"][0].get("detail", "")
        dep = by_id["claim-dep"]["checks"][0].get("detail", "")
        if "not implemented" not in signed or "not implemented" not in signer:
            print("[FAIL] smoke curbcheck git signature checks were not left unimplemented", flush=True)
            return 1
        if "unavailable" not in dep:
            print(f"[FAIL] smoke curbcheck dep_ban detail was {dep!r}", flush=True)
            return 1
        skipped = _run_curbcheck(binary, repo, packs, out, skip="claim-exist=not this build")
        if skipped.returncode != 1:
            print(skipped.stdout, flush=True)
            print("[FAIL] smoke curbcheck skip did not exit 1", flush=True)
            return 1
        again = json.loads(out.read_text(encoding="utf-8"))
        exist = next(row for row in again["claims"] if row["id"] == "claim-exist")
        if exist["status"] != "skipped" or exist["checks"][0].get("detail") != "not this build":
            print("[FAIL] smoke curbcheck did not store the skip reason", flush=True)
            return 1
        print(f"[PASS] smoke {binary.name}", flush=True)
        return 0
    finally:
        if repo is not None:
            shutil.rmtree(repo, ignore_errors=True)
        if packs is not None:
            shutil.rmtree(packs, ignore_errors=True)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: smoke.py <binary>", flush=True)
        return 2
    return smoke(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())
