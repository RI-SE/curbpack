"""M4: real file checks and one run result."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from checks.filecheck import run_contents, run_exist
from checks.run import build_run_result, process_exit_code
from claims.bind import build_claim
from common.store import load_run_result, save_pack, save_requirement
from common.version import TOOL_VERSION
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.editing import apply_edits
from scaffold.stub import write_stub


def _requirement():
    source = dict(extract_annex_vii_risk()["source"])
    source["edition"] = "2024-11-20"
    return apply_edits(extract_annex_vii_risk(), {"source": source})


def _exist(path: str):
    return build_claim(
        claim_id="claim-risk-exist",
        requirement_id="CRA-ANNEX-VII-RISK",
        source="documents",
        args={"path": path},
        checks=[{"check": "exist", "args": {"paths": [path]}}],
        severity="high",
        description="The file is the reviewed evidence.",
    )


def _contents(path: str, headers=None):
    return build_claim(
        claim_id="claim-risk-contents",
        requirement_id="CRA-ANNEX-VII-RISK",
        source="documents",
        args={"path": path},
        checks=[
            {
                "check": "contents",
                "args": {
                    "path": path,
                    "probes": [
                        {"kind": "size", "bytes": 200, "op": ">="},
                        {
                            "kind": "headers",
                            "headers": headers
                            or ["# Risk Assessment", "## Product Overview", "## Identified Risks"],
                        },
                        {"kind": "token"},
                    ],
                },
            }
        ],
        severity="high",
        description="The file bytes are the reviewed evidence.",
    )


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.email=poc2@example.com",
        "-c",
        "user.name=PoC2",
        "commit",
        "-m",
        message,
    )


class CheckBehaviorTest(unittest.TestCase):
    def test_missing_file_fails_exist_and_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            exist = run_exist(repo, {"paths": ["docs/annex-vii/risk_assessment.md"]})
            contents = run_contents(
                repo,
                {
                    "path": "docs/annex-vii/risk_assessment.md",
                    "probes": [{"kind": "headers", "headers": ["# Risk Assessment"]}],
                },
            )
        self.assertEqual(exist["status"], "fail")
        self.assertIn("is absent", exist["detail"])
        self.assertEqual(contents["status"], "fail")
        self.assertIn("is absent", contents["detail"])
        self.assertNotIn("header", contents["detail"])

    def test_unreadable_required_file_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            relative = "SECURITY.md"
            path = repo / relative
            path.write_text("# Security\n", encoding="utf-8")
            release = _deny_read(path)
            try:
                exist = run_exist(repo, {"path": relative})
                contents = run_contents(
                    repo,
                    {"path": relative, "probes": [{"kind": "size", "op": ">", "bytes": 0}]},
                )
            finally:
                release()
        self.assertEqual(exist["status"], "fail")
        self.assertIn("unreadable", exist["detail"])
        self.assertEqual(contents["status"], "fail")
        self.assertIn("unreadable", contents["detail"])

    def test_stub_fails_contents_and_a_real_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            relative = "docs/annex-vii/risk_assessment.md"
            write_stub(repo, relative)
            failed = run_contents(repo, _contents(relative)["checks"][0]["args"])
            self.assertEqual(failed["status"], "fail")
            self.assertIn("bytes", failed["detail"])
            self.assertIn("header", failed["detail"])
            body = _good(repo)
            (repo / relative).write_text(body, encoding="utf-8")
            passed = run_contents(repo, _contents(relative)["checks"][0]["args"])
            self.assertEqual(passed, {"status": "pass"})

    def test_empty_claim_list_is_not_success_and_dirty_is_labeled(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("readme\n", encoding="utf-8")
            _git(repo, "init", "-b", "main")
            _commit(repo, "init")
            packs = [{"id": "cra-baseline", "version": "0.1.0", "digest": "abc"}]
            empty = build_run_result(repo, [], packs)
            self.assertEqual(empty["claims"], [])
            self.assertEqual(empty["worktree"], "clean")
            self.assertEqual(process_exit_code(empty), 1)
            (repo / "README.md").write_text("readme changed\n", encoding="utf-8")
            dirty = build_run_result(repo, [_exist("README.md")], packs)
            self.assertEqual(dirty["worktree"], "dirty")
            self.assertEqual(dirty["claims"][0]["status"], "pass")
            self.assertNotIn("detail", dirty["claims"][0])
            self.assertEqual(process_exit_code(dirty), 0)
            self.assertIn("commit", dirty)

    def test_skipped_needs_a_reason_and_is_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            packs = [{"id": "cra-baseline", "version": "0.1.0", "digest": "abc"}]
            result = build_run_result(
                repo,
                [_exist("missing.md")],
                packs,
                skip={"claim-risk-exist": "operator skipped this claim"},
            )
            self.assertEqual(result["claims"][0]["status"], "skipped")
            self.assertEqual(result["claims"][0]["checks"][0]["status"], "skipped")
            self.assertEqual(result["claims"][0]["checks"][0]["detail"], "operator skipped this claim")
            self.assertNotIn("detail", result["claims"][0])
            self.assertNotIn("commit", result)
            self.assertEqual(process_exit_code(result), 1)
            self.assertEqual(result["tool_version"], TOOL_VERSION)

    def test_forbidden_pattern_fails_only_when_it_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            relative = "docs/note.md"
            (repo / "docs").mkdir()
            (repo / relative).write_text("ordinary text\n", encoding="utf-8")
            args = {"path": relative, "probes": [{"kind": "pattern", "pattern": "SECRET"}]}
            self.assertEqual(run_contents(repo, args), {"status": "pass"})
            (repo / relative).write_text("SECRET\n", encoding="utf-8")
            failed = run_contents(repo, args)
            self.assertEqual(failed["status"], "fail")
            self.assertIn("forbidden pattern", failed["detail"])

    def test_run_result_round_trip(self):
        requirement = _requirement()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_dir = root / "packs" / "cra-baseline"
            repo = root / "product"
            repo.mkdir()
            save_pack(pack_dir, draft_pack())
            save_requirement(pack_dir, requirement)
            write_stub(repo, "docs/annex-vii/risk_assessment.md")
            (repo / "curbpack.json").write_text(
                '{"packs":["cra-baseline"],"search_hints":{"exclude_path_globs":["*FUTURE_*"]}}\n',
                encoding="utf-8",
            )
            from claims.bind import write_claim
            from checks.run import run_and_write

            path = "docs/annex-vii/risk_assessment.md"
            combined = build_claim(
                claim_id="claim-risk",
                requirement_id="CRA-ANNEX-VII-RISK",
                source="documents",
                args={"path": path},
                checks=[
                    {"check": "exist", "args": {"paths": [path]}},
                    _contents(path)["checks"][0],
                ],
                severity="high",
                description="The risk assessment file is the reviewed evidence.",
            )
            write_claim(repo / "curbpack" / "claims", combined)
            out = repo / "run-result.json"
            result, code = run_and_write(repo, root / "packs", out)
            self.assertEqual(code, 1)
            loaded = load_run_result(out)
            self.assertEqual(loaded, result)
            self.assertEqual(loaded["packs"][0]["id"], "cra-baseline")
            self.assertEqual(loaded["packs"][0]["version"], "0.1.0")
            self.assertEqual(len(loaded["claims"]), 1)
            row = loaded["claims"][0]
            self.assertEqual(row["id"], "claim-risk")
            self.assertEqual(row["status"], "fail")
            self.assertEqual(row["checks"][0]["status"], "pass")
            self.assertEqual(row["checks"][1]["check"], "contents")
            self.assertEqual(row["checks"][1]["status"], "fail")


def _deny_read(path: Path):
    """Hold the file so the next open fails. chmod(0) only marks Windows read-only."""
    if os.name != "nt":
        path.chmod(0)

        def release() -> None:
            path.chmod(0o644)

        return release
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel32.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)
    # ctypes returns INVALID_HANDLE_VALUE as a signed -1 or as an unsigned all-ones pointer.
    invalid = {None, 0, -1, (1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1}
    if handle in invalid:
        raise ctypes.WinError(ctypes.get_last_error())

    def release() -> None:
        kernel32.CloseHandle(handle)

    return release


def _good(repo: Path) -> str:
    text = f"""# Risk Assessment

## Product Overview

{repo.name} is the product named in this assessment.

## Identified Risks

The assessment records the risks considered for design and maintenance of {repo.name}.
"""
    while len(text.encode("utf-8")) < 200:
        text += f"Additional notes for {repo.name}.\n"
    return text


if __name__ == "__main__":
    unittest.main()
