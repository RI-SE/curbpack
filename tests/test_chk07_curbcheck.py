"""CHK-07 — curbcheck reads curbpack.json, owns defaults, stdout / -j / -o."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from checks.__main__ import main
from claims.bind import build_claim, write_claim
from common.store import save_pack, save_requirement
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk


CREATED_SEARCH_HINTS = {
    "sources": [{"source": "documents"}, {"source": "git"}],
    "exclude_path_globs": [
        "**/node_modules/**",
        "**/.git/**",
        "**/dist/**",
        "**/build/**",
    ],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"],
}


class DefaultsFactoryTest(unittest.TestCase):
    def test_defaults_function_returns_created_file_values(self):
        from checks.defaults import created_curbpack

        document = created_curbpack()
        self.assertEqual(document["packs"], [])
        self.assertEqual(document["search_hints"], CREATED_SEARCH_HINTS)
        self.assertEqual(document["packs_dir"], "curbpack/packs")
        self.assertEqual(document["claims_dir"], "curbpack/claims")
        self.assertEqual(document["results_dir"], ".curbpack")
        self.assertEqual(document["reports_dir"], "curbpack/reports")
        self.assertEqual(document["unsigned_requirements"], "reject")
        self.assertNotIn("exclude_requirements", document)
        self.assertNotIn("requirements", document)

    def test_defaults_cli_prints_that_json_without_a_repository(self):
        from checks.defaults import created_curbpack

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        previous = Path.cwd()
        os.chdir(tmp.name)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--defaults"])
        finally:
            os.chdir(previous)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue()), created_curbpack())
        self.assertEqual(list(Path(tmp.name).iterdir()), [])

    def test_studio_calls_the_same_defaults_function(self):
        from checks.defaults import created_curbpack
        from discovery.door import created_curbpack as door_created

        self.assertIs(door_created, created_curbpack)
        self.assertEqual(door_created(), created_curbpack())


def _requirement():
    source = dict(extract_annex_vii_risk()["source"])
    source["edition"] = "2024-11-20"
    return apply_edits(extract_annex_vii_risk(), {"source": source})


def _passing_repo() -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name)
    (repo / "docs").mkdir()
    (repo / "docs" / "a.md").write_text("hello\n", encoding="utf-8")
    pack_dir = repo / "curbpack" / "packs" / "cra-baseline" / "0.1.0"
    save_pack(pack_dir, draft_pack())
    save_requirement(pack_dir, _requirement())
    from checks.defaults import created_curbpack

    (repo / "curbpack.json").write_text(
        json.dumps(created_curbpack(packs=["cra-baseline"])) + "\n", encoding="utf-8"
    )
    write_claim(
        repo / "curbpack" / "claims",
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
    return tmp, repo


def _run_results(repo: Path) -> list[Path]:
    return sorted(repo.rglob("run-result*.json"))


class OutputChannelsTest(unittest.TestCase):
    def test_stdout_only_writes_no_run_result_file(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--repo", str(repo)])
        text = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("claims 1 exit 0", text)
        self.assertIn("pass    claim-risk", text)
        self.assertNotIn("wrote ", text)
        self.assertEqual(_run_results(repo), [])

    def test_json_flag_writes_a_dated_file_under_results_dir(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--repo", str(repo), "-j"])
        dated = _run_results(repo)
        self.assertEqual(code, 0)
        self.assertEqual(len(dated), 1)
        self.assertEqual(dated[0].parent, repo / ".curbpack")
        self.assertRegex(dated[0].name, r"^run-result_\d{8}T\d{6}Z\.json$")
        loaded = json.loads(dated[0].read_text(encoding="utf-8"))
        self.assertEqual(loaded["claims"][0]["status"], "pass")
        self.assertIn("claims 1 exit 0", buf.getvalue())
        self.assertIn(f"wrote {dated[0]}", buf.getvalue())

    def test_second_json_run_leaves_the_first_file(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["--repo", str(repo), "--json"])
        first = _run_results(repo)
        self.assertEqual(len(first), 1)
        before = first[0].read_bytes()
        import time

        time.sleep(1)
        with redirect_stdout(buf):
            main(["--repo", str(repo), "--json"])
        dated = _run_results(repo)
        self.assertEqual(len(dated), 2)
        self.assertEqual(first[0].read_bytes(), before)
        self.assertIn("claims 1 exit 0", buf.getvalue())
        self.assertIn("pass    claim-risk", buf.getvalue())

    def test_out_writes_the_run_result_to_path(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "chosen" / "result.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--repo", str(repo), "-o", str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(_run_results(repo), [])
        loaded = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(loaded["claims"][0]["id"], "claim-risk")
        self.assertIn(f"wrote {out}", buf.getvalue())
        self.assertIn("claims 1 exit 0", buf.getvalue())

    def test_json_and_out_write_both_files(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "also.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["--repo", str(repo), "-j", "--out", str(out)])
        dated = [path for path in _run_results(repo) if path != out]
        self.assertEqual(len(dated), 1)
        self.assertTrue(out.is_file())
        self.assertEqual(
            json.loads(dated[0].read_text(encoding="utf-8"))["claims"][0]["id"],
            json.loads(out.read_text(encoding="utf-8"))["claims"][0]["id"],
        )
        text = buf.getvalue()
        self.assertIn(f"wrote {dated[0]}", text)
        self.assertIn(f"wrote {out}", text)
        self.assertIn("claims 1 exit 0", text)

    def test_missing_curbpack_json_writes_nothing(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        with self.assertRaises(FileNotFoundError):
            main(["--repo", str(repo), "-j", "-o", str(repo / "out.json")])
        self.assertEqual(_run_results(repo), [])
        self.assertFalse((repo / "out.json").exists())

    def test_invalid_curbpack_json_writes_nothing(self):
        from common.errors import ModelError

        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        (repo / "curbpack.json").write_text("{}\n", encoding="utf-8")
        out = repo / "out.json"
        with self.assertRaises(ModelError):
            main(["--repo", str(repo), "-o", str(out)])
        self.assertEqual(_run_results(repo), [])
        self.assertFalse(out.exists())


class IdListFlagsTest(unittest.TestCase):
    def test_packs_flag_checks_those_ids_from_packs_dir(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        extra = dict(draft_pack())
        extra["id"] = "house-policy"
        extra_dir = repo / "curbpack" / "packs" / "house-policy" / "0.1.0"
        save_pack(extra_dir, extra)
        house_req = dict(_requirement())
        house_req["id"] = "HOUSE-REQ"
        house_req["pack_id"] = "house-policy"
        save_requirement(extra_dir, house_req)
        config_path = repo / "curbpack.json"
        before = config_path.read_bytes()
        out = repo / "out.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(
                ["--repo", str(repo), "--packs", "cra-baseline,house-policy", "-o", str(out)]
            )
        self.assertEqual(code, 0)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual([row["id"] for row in loaded["packs"]], ["cra-baseline", "house-policy"])
        self.assertEqual([row["id"] for row in loaded["claims"]], ["claim-risk"])
        self.assertEqual(config_path.read_bytes(), before)

    def test_requirements_flag_checks_those_ids_from_claims_dir(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        other = dict(_requirement())
        other["id"] = "OTHER-REQ"
        save_requirement(repo / "curbpack" / "packs" / "cra-baseline" / "0.1.0", other)
        write_claim(
            repo / "curbpack" / "claims",
            build_claim(
                claim_id="claim-other",
                requirement_id="OTHER-REQ",
                source="documents",
                args={"path": "docs/a.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
                severity="high",
                description="The other requirement.",
            ),
        )
        out = repo / "out.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(
                [
                    "--repo",
                    str(repo),
                    "--requirements",
                    "CRA-ANNEX-VII-RISK,OTHER-REQ",
                    "-o",
                    str(out),
                ]
            )
        self.assertEqual(code, 0)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual([row["id"] for row in loaded["claims"]], ["claim-other", "claim-risk"])
        self.assertTrue((repo / "curbpack" / "claims" / "claim-other.json").is_file())
        self.assertTrue((repo / "curbpack" / "claims" / "claim-risk.json").is_file())

    def test_packs_path_exits_2_and_writes_nothing(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        out = repo / "out.json"
        with redirect_stderr(io.StringIO()):
            code = main(["--repo", str(repo), "--packs", str(repo / "curbpack" / "packs"), "-o", str(out)])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())
        self.assertEqual(_run_results(repo), [])

    def test_requirements_backslash_exits_2_and_writes_nothing(self):
        tmp, repo = _passing_repo()
        self.addCleanup(tmp.cleanup)
        out = repo / "out.json"
        with redirect_stderr(io.StringIO()):
            code = main(["--repo", str(repo), "--requirements", r"CRA\ANNEX", "-o", str(out)])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())
