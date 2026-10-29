"""CHK-08 — Studio Check and Review call the CHK-07 Python API."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import build_claim, write_claim
from common.jsonio import write_json
from common.store import load_run_result, save_pack, save_requirement
from discovery.door import created_curbpack
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack
from review.compile import load_report


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode()


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form, doseq=True).encode()
    request = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()


def _requirement(requirement_id: str, pack_id: str = "cra-baseline") -> dict:
    return {
        "id": requirement_id,
        "pack_id": pack_id,
        "source": {
            "framework": "EU",
            "instrument": "CRA",
            "identifier": "CELEX:32024R2847",
            "language": "en",
            "url": "https://example.invalid/cra",
        },
        "references": [{"nr": 1, "locator": "VII.1(a)", "law_text": "its intended purpose"}],
    }


def _exist_claim(claim_id: str, requirement_id: str, path: str) -> dict:
    return build_claim(
        claim_id=claim_id,
        requirement_id=requirement_id,
        source="documents",
        args={"path": path},
        checks=[{"check": "exist", "args": {"paths": [path]}}],
        description="The file is the reviewed evidence.",
    )


def _register(workspace: Path, name: str, repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    save_repos(workspace, add_repo(workspace, load_repos(workspace), name=name, path=str(repo)))


class CheckRunTest(unittest.TestCase):
    def test_check_writes_dated_results_dir_json_from_the_open_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            product = workspace / "product"
            repo = workspace / "widget"
            product.mkdir()
            write_json(product / "curbpack.json", created_curbpack(packs=["hidden-pack"]))
            write_json(
                product / "curbpack" / "packs" / "hidden-pack" / draft_pack()["version"] / "pack.json",
                {"id": "hidden-pack", "name": "Hidden Pack", "version": draft_pack()["version"]},
            )
            write_claim(
                product / "curbpack" / "claims",
                _exist_claim("sneak-claim", "CRA-PURPOSE", "README.md"),
            )
            _register(workspace, "Widget", repo)
            pack_dir = repo / "tree" / "packs" / "cra-baseline" / draft_pack()["version"]
            save_pack(pack_dir, draft_pack())
            save_requirement(pack_dir, _requirement("CRA-PURPOSE"))
            (repo / "README.md").write_text("hello from widget\n", encoding="utf-8")
            write_claim(
                repo / "kept" / "claims",
                _exist_claim("claim-readme", "CRA-PURPOSE", "README.md"),
            )
            write_json(
                repo / "curbpack.json",
                created_curbpack(
                    packs=["cra-baseline"],
                    packs_dir="tree/packs",
                    claims_dir="kept/claims",
                    results_dir="runs/out",
                    reports_dir="signed/reports",
                ),
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(workspace)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                ran = _post(base + "/check", {"repo_id": "widget", "action": "check"})
                results = sorted((repo / "runs" / "out").glob("run-result_*.json"))
                self.assertEqual(len(results), 1)
                self.assertRegex(results[0].name, r"^run-result_\d{8}T\d{6}Z\.json$")
                self.assertIn(str(results[0].resolve()), ran)
                self.assertFalse((repo / "runs" / "out" / "run-result.json").exists())
                first = results[0].read_bytes()
                result = load_run_result(results[0])
                self.assertEqual([row["id"] for row in result["claims"]], ["claim-readme"])
                self.assertNotIn("sneak-claim", json.dumps(result))
                self.assertNotIn("hidden-pack", ran)
                ran_again = _post(base + "/check", {"repo_id": "widget", "action": "check"})
                results = sorted((repo / "runs" / "out").glob("run-result_*.json"))
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0].read_bytes(), first)
                self.assertIn(str(results[1].resolve()), ran_again)
            finally:
                httpd.shutdown()
                httpd.server_close()


class ReviewCompileTest(unittest.TestCase):
    def test_compile_reads_the_open_repo_run_and_writes_dated_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            product = workspace / "product"
            repo = workspace / "widget"
            product.mkdir()
            write_json(product / "curbpack.json", created_curbpack(packs=["hidden-pack"]))
            write_json(
                product / ".curbpack" / "run-result.json",
                {
                    "tool": "curbcheck",
                    "tool_version": "0.0.1a",
                    "packs": [{"id": "hidden-pack", "version": "0.1.0", "digest": "aaa"}],
                    "claims": [
                        {
                            "id": "sneak-claim",
                            "digest": "bbb",
                            "status": "pass",
                            "checks": [
                                {
                                    "index": 0,
                                    "check": "exist",
                                    "args": {"paths": ["README.md"]},
                                    "status": "pass",
                                }
                            ],
                        }
                    ],
                },
            )
            write_claim(
                product / "curbpack" / "claims",
                _exist_claim("sneak-claim", "CRA-PURPOSE", "README.md"),
            )
            _register(workspace, "Widget", repo)
            pack_dir = repo / "tree" / "packs" / "cra-baseline" / draft_pack()["version"]
            save_pack(pack_dir, draft_pack())
            save_requirement(pack_dir, _requirement("CRA-PURPOSE"))
            (repo / "README.md").write_text("hello from widget\n", encoding="utf-8")
            write_claim(
                repo / "kept" / "claims",
                _exist_claim("claim-readme", "CRA-PURPOSE", "README.md"),
            )
            write_json(
                repo / "curbpack.json",
                created_curbpack(
                    packs=["cra-baseline"],
                    packs_dir="tree/packs",
                    claims_dir="kept/claims",
                    results_dir="runs/out",
                    reports_dir="signed/reports",
                ),
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(workspace)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                _post(base + "/check", {"repo_id": "widget", "action": "check"})
                runs = sorted((repo / "runs" / "out").glob("run-result_*.json"))
                self.assertEqual(len(runs), 1)
                compiled = _post(
                    base + "/review/compile",
                    {"repo_id": "widget", "result": str(runs[0].resolve())},
                )
                reports = sorted((repo / "signed" / "reports").glob("review-report_*.json"))
                self.assertEqual(len(reports), 1)
                self.assertRegex(reports[0].name, r"^review-report_\d{8}T\d{6}Z\.json$")
                self.assertIn(str(reports[0].resolve()), compiled)
                first = reports[0].read_bytes()
                report = load_report(reports[0])
                self.assertEqual(report["run_result"], load_run_result(runs[0]))
                self.assertEqual([row["id"] for row in report["claims"]], ["claim-readme"])
                self.assertNotIn("sneak-claim", json.dumps(report))
                self.assertFalse((product / "docs" / "reports").exists())
                self.assertFalse((product / ".curbpack" / "review-report.json").exists())
                compiled_again = _post(
                    base + "/review/compile",
                    {"repo_id": "widget", "result": str(runs[0].resolve())},
                )
                reports = sorted((repo / "signed" / "reports").glob("review-report_*.json"))
                self.assertEqual(len(reports), 2)
                self.assertEqual(reports[0].read_bytes(), first)
                self.assertIn(str(reports[1].resolve()), compiled_again)
            finally:
                httpd.shutdown()
                httpd.server_close()


class InventoryTest(unittest.TestCase):
    def test_listed_studio_tests_do_not_pass_a_packs_directory_packs_root(self):
        root = Path(__file__).resolve().parents[1]
        listed = (
            "tests/test_check_editor.py",
            "tests/test_sys03_door.py",
            "tests/test_review_report_kept.py",
            "tests/test_review_replace_flow.py",
            "tests/test_review_discover_again.py",
            "tests/test_review_coverage_ui.py",
            "tests/test_review_compile.py",
            "tests/test_review_coverage.py",
            "tests/test_ui_smoke.py",
            "tests/test_e2e_annex_vii.py",
            "tests/test_chk08_studio.py",
        )
        leftovers = []
        for rel in listed:
            text = (root / rel).read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), 1):
                if "run_and_write(" in line and ", None" not in line:
                    leftovers.append(f"{rel}:{line_no}:{line.strip()}")
        self.assertEqual(leftovers, [])


class DefaultsTest(unittest.TestCase):
    def test_blank_curbpack_body_is_the_checks_defaults_function(self):
        from checks.defaults import created_curbpack as factory
        from discovery.door import created_curbpack as door_created

        self.assertIs(door_created, factory)
        self.assertIs(created_curbpack, factory)
        fields = factory()
        self.assertEqual(fields["packs_dir"], "curbpack/packs")
        self.assertEqual(fields["claims_dir"], "curbpack/claims")
        self.assertEqual(fields["results_dir"], ".curbpack")
        self.assertEqual(fields["reports_dir"], "curbpack/reports")
        self.assertEqual(fields["unsigned_requirements"], "reject")

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo = workspace / "widget"
            _register(workspace, "Widget", repo)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(workspace)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                page = _get(base + "/requirements?repo=widget")
                self.assertIn('name="packs_dir"', page)
                self.assertIn(f'value="{fields["packs_dir"]}"', page)
                self.assertIn(f'value="{fields["claims_dir"]}"', page)
                self.assertIn(f'value="{fields["results_dir"]}"', page)
                self.assertIn(f'value="{fields["reports_dir"]}"', page)
                self.assertIn(f'value="{fields["unsigned_requirements"]}" selected', page)
                self.assertFalse((repo / "curbpack.json").exists())
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
