"""The packaged curbcheck program re-enters its own tools."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "build"))

from checks.dispatch import run_check_tool
from checks.__main__ import main
from claims.bind import build_claim, write_claim
from common.store import save_pack, save_requirement
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk


def _requirement():
    source = dict(extract_annex_vii_risk()["source"])
    source["edition"] = "2024-11-20"
    return apply_edits(extract_annex_vii_risk(), {"source": source})


def _invoke(argv: list[str]) -> tuple[int, dict]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    return code, json.loads(buf.getvalue())


def _git(repo: Path, *args: str, when: str | None = None) -> None:
    env = os.environ.copy()
    if when is not None:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env, capture_output=True, text=True)


def _repo_with_file() -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name)
    docs = repo / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("hello\n", encoding="utf-8")
    return tmp, repo


class ToolReentryTest(unittest.TestCase):
    def test_a_frozen_parent_keeps_the_registered_argv_and_reenters_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch.object(sys, "frozen", True, create=True), patch("checks.dispatch.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"status":"pass"}\n', stderr=""
                )
                result = run_check_tool(repo, "curbcheck-exist", "exist", {"paths": ["docs/a.md"]})
            self.assertEqual(result, {"status": "pass"})
            argv = run.call_args.args[0]
            self.assertEqual(
                argv[:4],
                ["curbcheck-exist", "exist", "--repo", str(repo)],
            )
            self.assertEqual(argv[4], "--args")
            self.assertEqual(json.loads(argv[5]), {"paths": ["docs/a.md"]})
            self.assertEqual(run.call_args.kwargs["executable"], sys.executable)

    def test_exist_and_contents_pass_through_the_tool_entry(self):
        tmp, repo = _repo_with_file()
        self.addCleanup(tmp.cleanup)
        code, exist = _invoke(
            ["curbcheck-exist", "exist", "--repo", str(repo), "--args", json.dumps({"paths": ["docs/a.md"]})]
        )
        self.assertEqual(code, 0)
        self.assertEqual(exist, {"status": "pass"})
        code, contents = _invoke(
            [
                "curbcheck-contents",
                "contents",
                "--repo",
                str(repo),
                "--args",
                json.dumps({"path": "docs/a.md", "probes": [{"kind": "pattern", "pattern": "SECRET"}]}),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(contents, {"status": "pass"})

    def test_git_fresh_and_git_author_pass_and_signed_checks_are_not_implemented(self):
        tmp, repo = _repo_with_file()
        self.addCleanup(tmp.cleanup)
        when = "2026-10-23T12:00:00Z"
        _git(repo, "init", "-b", "main")
        _git(repo, "config", "user.email", "poc2@example.com")
        _git(repo, "config", "user.name", "PoC2")
        _git(repo, "config", "commit.gpgsign", "false")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "add doc", when=when)
        fresh_args = {"path": "docs/a.md", "max_age_days": 0, "as_of": when}
        code, fresh = _invoke(
            ["curbcheck-git", "git_fresh", "--repo", str(repo), "--args", json.dumps(fresh_args)]
        )
        self.assertEqual((code, fresh), (0, {"status": "pass"}))
        author_args = {"path": "docs/a.md", "name": "PoC2", "email": "poc2@example.com"}
        code, author = _invoke(
            ["curbcheck-git", "git_author", "--repo", str(repo), "--args", json.dumps(author_args)]
        )
        self.assertEqual((code, author), (0, {"status": "pass"}))
        for check in ("git_signed", "git_signer"):
            code, result = _invoke(
                [
                    "curbcheck-git",
                    check,
                    "--repo",
                    str(repo),
                    "--args",
                    json.dumps({"path": "docs/a.md", "allowed_signers": ".git-allowed-signers"}),
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "fail")
            self.assertIn("not implemented", result["detail"])

    def test_dep_ban_is_unavailable(self):
        tmp, repo = _repo_with_file()
        self.addCleanup(tmp.cleanup)
        code, result = _invoke(
            [
                "curbcheck-dep-ban",
                "dep_ban",
                "--repo",
                str(repo),
                "--args",
                json.dumps({"package": "axios", "banned_versions": ["1.0.0"]}),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(result, {"status": "fail", "detail": "check tool 'curbcheck-dep-ban' is unavailable"})

    def test_skip_stores_the_reason(self):
        tmp, repo = _repo_with_file()
        self.addCleanup(tmp.cleanup)
        pack_dir = Path(tmp.name) / "packs" / "cra-baseline"
        save_pack(pack_dir, draft_pack())
        save_requirement(pack_dir, _requirement())
        (repo / "curbpack.json").write_text('{"packs":["cra-baseline"]}\n', encoding="utf-8")
        write_claim(
            repo / "claims",
            build_claim(
                claim_id="claim-risk",
                requirement_id="CRA-ANNEX-VII-RISK",
                source="documents",
                args={"path": "docs/a.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
                severity="high",
                description="The file is the reviewed evidence.",
            ),
        )
        out = repo / "run-result.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(
                ["--repo", str(repo), "--packs", str(Path(tmp.name) / "packs"), "--out", str(out), "--skip", "claim-risk=not this build"]
            )
        self.assertEqual(code, 1)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(loaded["claims"][0]["status"], "skipped")
        self.assertEqual(loaded["claims"][0]["checks"][0]["detail"], "not this build")
        self.assertIn("skipped", buf.getvalue())


class PackageArgsTest(unittest.TestCase):
    def test_names_and_argv_keep_studio_and_curbcheck_apart(self):
        from package import curbcheck_args, curbcheck_name, studio_args, studio_name
        self.assertEqual(studio_name("macos-arm64"), "curbpack-studio-macos-arm64")
        self.assertEqual(curbcheck_name("macos-arm64"), "curbcheck-macos-arm64")
        self.assertEqual(studio_name("windows-x64"), "curbpack-studio-windows-x64.exe")
        self.assertEqual(curbcheck_name("windows-x64"), "curbcheck-windows-x64.exe")
        studio = studio_args("curbpack-studio-macos-arm64")
        checker = curbcheck_args("curbcheck-macos-arm64")
        self.assertTrue(studio[-1].endswith("app/__main__.py"))
        self.assertNotIn("checks/bin", " ".join(studio))
        self.assertTrue(checker[-1].endswith("checks/__main__.py"))
        self.assertTrue(any("available_checks.json" in part for part in checker))
        self.assertFalse(any("requirements/ui" in part for part in checker))
        self.assertNotIn("checks/bin", " ".join(checker))

    def test_sums_name_every_packaged_file(self):
        from package import write_sums

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            studio = directory / "curbpack-studio-macos-arm64"
            checker = directory / "curbcheck-macos-arm64"
            studio.write_bytes(b"studio")
            checker.write_bytes(b"curbcheck")
            with patch("package.DIST", directory):
                sums = write_sums([studio, checker])
            text = sums.read_text(encoding="utf-8")
            expected = []
            for path in (studio, checker):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                expected.append(f"{digest}  {path.name}")
            self.assertEqual(text.splitlines(), expected)

    def test_importing_the_checker_does_not_import_the_application(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import checks.__main__\n"
                "import sys\n"
                "banned = ('app', 'requirements.ui', 'claims.ui', 'review', 'scaffold')\n"
                "loaded = [name for name in banned if name in sys.modules or any(key == name or key.startswith(name + '.') for key in sys.modules)]\n"
                "raise SystemExit(0 if not loaded else 'loaded ' + ','.join(loaded))\n",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
