"""REV-03 Review lists run results and review reports as different documents.

REV-R01 is scenarios 1, 2, and 38. REV-R02 is scenarios 3, 4, 5, 37a, 39, 40, 41, and 42.
"""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import build_claim, write_claim
from common.canonical import version_digest
from common.jsonio import write_json
from common.store import save_pack, save_requirement
from discovery.door import created_curbpack
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack
from review.compile import compile_report, record_decision, write_report


class ReviewDocumentListsTest(unittest.TestCase):
    def test_review_lists_the_two_document_kinds_and_opens_only_the_one_asked_for(self):
        """REV-03 scenarios 1, 3, and 5. REV-R01 and REV-R02."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _config(repo, packs_dir="packs/here", claims_dir="claims/here", results_dir="runs/out", reports_dir="signed/reports")
            one = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            two = repo / "runs" / "out" / "run-result_20260101T000001Z.json"
            failed = _run("claim-one")
            failed["claims"][0]["status"] = "fail"
            failed["claims"][0]["checks"][0]["status"] = "fail"
            failed["claims"][0]["checks"][0]["detail"] = "missing file"
            write_json(one, failed)
            write_json(two, _run("claim-two"))
            first = repo / "signed" / "reports" / "review-report_20260101T000000Z.json"
            second = repo / "signed" / "reports" / "review-report_20260101T000001Z.json"
            write_report(first, _report("claim-one", "Decision for claim-one."))
            write_report(second, _report("claim-two", "Decision for claim-two."))
            before = _files(repo)
            with _serve(workspace) as base:
                page = _get(base + "/review?repo=alpha")
                self.assertIn("Current Configuration", page)
                self.assertIn('value="packs/here"', page)
                self.assertIn('value="claims/here"', page)
                self.assertIn('value="runs/out"', page)
                self.assertIn('value="signed/reports"', page)
                runs = _section(page, "run-results")
                reports = _section(page, "review-reports")
                self.assertIn("Run result", runs)
                self.assertIn(one.name, runs)
                self.assertIn(two.name, runs)
                self.assertNotIn(first.name, runs)
                self.assertNotIn(second.name, runs)
                self.assertIn("Review report", reports)
                self.assertIn(first.name, reports)
                self.assertIn(second.name, reports)
                self.assertNotIn(one.name, reports)
                self.assertNotIn(two.name, reports)
                self.assertNotIn("claim-one", page)
                self.assertNotIn("claim-two", page)
                self.assertEqual(_files(repo), before)
                opened = _get(base + "/review?repo=alpha&result=" + urllib.parse.quote(str(one.resolve())))
                self.assertIn("claim-one", opened)
                self.assertIn("missing file", opened)
                self.assertNotIn("claim-two", opened)
                self.assertNotIn("No unsigned or unverifiable Claims in this run.", opened)
                self.assertNotIn("Requirement <code></code>", opened)
                self.assertNotIn("Source args", opened)
                self.assertEqual(_files(repo), before)
                report_page = _get(base + "/review?repo=alpha&report=" + urllib.parse.quote(str(first.resolve())))
                self.assertIn("Decision for claim-one.", report_page)
                self.assertNotIn("Decision for claim-two.", report_page)

    def test_another_repository_drops_a_selection_that_is_not_its_document(self):
        """REV-03 scenario 2. REV-R01."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace, alpha = _workspace("Alpha", root / "alpha")
            _config(alpha, results_dir="runs/out", reports_dir="signed/reports")
            run = alpha / "runs" / "out" / "run-result_20260101T000000Z.json"
            write_json(run, _run("claim-alpha"))
            report = alpha / "signed" / "reports" / "review-report_20260101T000000Z.json"
            write_report(report, _report("claim-alpha", "Decision for claim-alpha."))
            _register(workspace, "Beta", root / "beta")
            _config(root / "beta", results_dir="runs/out", reports_dir="signed/reports")
            (root / "beta" / "runs" / "out").mkdir(parents=True)
            (root / "beta" / "signed" / "reports").mkdir(parents=True)
            with _serve(workspace) as base:
                dropped_run = _get(base + "/review?repo=beta&result=" + urllib.parse.quote(str(run.resolve())))
                self.assertIn(str(run.resolve()), dropped_run)
                self.assertIn("run result", dropped_run)
                self.assertNotIn("claim-alpha", dropped_run)
                dropped_report = _get(base + "/review?repo=beta&report=" + urllib.parse.quote(str(report.resolve())))
                self.assertIn(str(report.resolve()), dropped_report)
                self.assertIn("review report", dropped_report)
                self.assertNotIn("claim-alpha", dropped_report)

    def test_a_missing_or_outside_document_is_named_and_not_replaced(self):
        """REV-03 scenario 37a. REV-R02."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _config(repo, results_dir="runs/out", reports_dir="signed/reports")
            kept = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            write_json(kept, _run("claim-kept"))
            missing = repo / "runs" / "out" / "run-result_20260101T000002Z.json"
            outsider = Path(tmp) / "run-result_20260101T000003Z.json"
            write_json(outsider, _run("claim-outside"))
            with _serve(workspace) as base:
                absent = _get(base + "/review?repo=alpha&result=" + urllib.parse.quote(str(missing.resolve())))
                self.assertIn(str(missing.resolve()), absent)
                self.assertIn("run result", absent)
                self.assertNotIn("claim-kept", absent)
                outside = _get(base + "/review?repo=alpha&result=" + urllib.parse.quote(str(outsider.resolve())))
                self.assertIn(str(outsider.resolve()), outside)
                self.assertIn("run result", outside)
                self.assertNotIn("claim-kept", outside)
                self.assertNotIn("claim-outside", outside)

    def test_missing_or_invalid_curbpack_json_is_named_and_directories_are_not_invented(self):
        """REV-03 scenario 38. REV-R01."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace, missing_repo = _workspace("Missing", root / "missing")
            _register(workspace, "Broken", root / "broken")
            (root / "broken" / "curbpack.json").write_text("{", encoding="utf-8")
            with _serve(workspace) as base:
                missing = _get(base + "/review?repo=missing")
                self.assertIn("curbpack.json", missing)
                self.assertNotIn("curbpack/packs", missing)
                self.assertNotIn("curbpack/claims", missing)
                self.assertNotIn("curbpack/reports", missing)
                broken = _get(base + "/review?repo=broken")
                self.assertIn("curbpack.json", broken)
                self.assertNotIn("curbpack/packs", broken)
                self.assertNotIn("runs/out", broken)

    def test_an_unusable_results_directory_is_named_and_reports_are_not_its_fallback(self):
        """REV-03 scenario 39. REV-R02."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _config(repo, results_dir="blocked-results", reports_dir="signed/reports")
            (repo / "blocked-results").write_text("not a directory\n", encoding="utf-8")
            report = repo / "signed" / "reports" / "review-report_20260101T000000Z.json"
            report.parent.mkdir(parents=True)
            report.write_text("{}\n", encoding="utf-8")
            with _serve(workspace) as base:
                page = _get(base + "/review?repo=alpha")
                self.assertIn("blocked-results", page)
                runs = _section(page, "run-results")
                self.assertNotIn(report.name, runs)

    def test_an_unusable_reports_directory_is_named_and_results_are_not_its_fallback(self):
        """REV-03 scenario 40. REV-R02."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _config(repo, results_dir="runs/out", reports_dir="blocked-reports")
            run = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            write_json(run, _run("claim-kept"))
            (repo / "blocked-reports").write_text("not a directory\n", encoding="utf-8")
            before = _files(repo)
            with _serve(workspace) as base:
                page = _get(base + "/review?repo=alpha")
                self.assertIn("blocked-reports", page)
                reports = _section(page, "review-reports")
                self.assertNotIn(run.name, reports)
                self.assertEqual(_files(repo), before)

    def test_no_run_result_is_an_empty_state_and_not_a_passing_review(self):
        """REV-03 scenario 41. REV-R02."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _config(repo, results_dir="runs/out", reports_dir="signed/reports")
            (repo / "runs" / "out").mkdir(parents=True)
            (repo / "signed" / "reports").mkdir(parents=True)
            with _serve(workspace) as base:
                page = _get(base + "/review?repo=alpha")
                self.assertIn("There is no run result.", page)
                self.assertNotIn("the review passed", page)

    def test_a_listed_file_that_is_not_json_names_that_document_and_type(self):
        """REV-03 scenario 42. REV-R02."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _config(repo, results_dir="runs/out", reports_dir="signed/reports")
            bad = repo / "runs" / "out" / "run-result_20260101T000009Z.json"
            bad.parent.mkdir(parents=True)
            bad.write_text("not json\n", encoding="utf-8")
            kept = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            write_json(kept, _run("claim-kept"))
            with _serve(workspace) as base:
                page = _get(base + "/review?repo=alpha&result=" + urllib.parse.quote(str(bad.resolve())))
                self.assertIn(bad.name, page)
                self.assertIn("run result", page)
                self.assertNotIn("claim-kept", page)

    def test_check_links_review_to_that_run_result(self):
        """REV-03 scenario 4. REV-R02."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Widget", Path(tmp) / "widget")
            _config(
                repo,
                packs=["cra-baseline"],
                packs_dir="tree/packs",
                claims_dir="kept/claims",
                results_dir="runs/out",
                reports_dir="signed/reports",
            )
            pack_dir = repo / "tree" / "packs" / "cra-baseline" / draft_pack()["version"]
            save_pack(pack_dir, draft_pack())
            save_requirement(pack_dir, _requirement("CRA-PURPOSE"))
            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            write_claim(repo / "kept" / "claims", _exist_claim("claim-readme", "CRA-PURPOSE", "README.md"))
            with _serve(workspace) as base:
                check = _post(base + "/check", {"repo_id": "widget", "action": "check"})
                run = next((repo / "runs" / "out").glob("run-result_*.json"))
                self.assertIn("/review?", check)
                self.assertIn("repo=widget", check)
                self.assertIn(urllib.parse.quote(str(run.resolve()), safe=""), check)

    def test_compile_without_a_selected_run_result_writes_nothing(self):
        """REV-03 scenario 5. REV-R02.

        The repository has a run result Compile can read. Omitting the selected
        result must not write a review report.
        """
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Widget", Path(tmp) / "widget")
            _config(
                repo,
                packs=["cra-baseline"],
                packs_dir="tree/packs",
                claims_dir="kept/claims",
                results_dir="runs/out",
                reports_dir="signed/reports",
            )
            pack_dir = repo / "tree" / "packs" / "cra-baseline" / draft_pack()["version"]
            save_pack(pack_dir, draft_pack())
            save_requirement(pack_dir, _requirement("CRA-PURPOSE"))
            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            write_claim(repo / "kept" / "claims", _exist_claim("claim-readme", "CRA-PURPOSE", "README.md"))
            with _serve(workspace) as base:
                _post(base + "/check", {"repo_id": "widget", "action": "check"})
                before = _files(repo)
                try:
                    _post(base + "/review/compile", {"repo_id": "widget"})
                except urllib.error.HTTPError:
                    pass
                self.assertEqual(_files(repo), before)


def _workspace(name: str, repo: Path) -> tuple[Path, Path]:
    workspace = repo.parent
    _register(workspace, name, repo)
    return workspace, repo


def _register(workspace: Path, name: str, repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    save_repos(workspace, add_repo(workspace, load_repos(workspace), name=name, path=str(repo)))


def _config(repo: Path, **paths: str) -> None:
    fields = {
        "packs_dir": "packs/here",
        "claims_dir": "claims/here",
        "results_dir": "runs/out",
        "reports_dir": "signed/reports",
    }
    fields.update(paths)
    write_json(repo / "curbpack.json", created_curbpack(**fields))


def _run(claim_id: str) -> dict:
    return {
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "packs": [{"id": "house", "version": "0.1.0", "digest": "abc"}],
        "claims": [
            {
                "id": claim_id,
                "digest": "digest",
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
    }


def _report(claim_id: str, decision: str) -> dict:
    claim = build_claim(
        claim_id=claim_id,
        requirement_id="CRA-PURPOSE",
        source="documents",
        args={"path": "README.md"},
        checks=[{"check": "exist", "args": {"paths": ["README.md"]}}],
        description="The file is the reviewed evidence.",
    )
    args = claim["checks"][0]["args"]
    report = compile_report(
        run_result={
            "tool": "curbcheck",
            "tool_version": "0.0.1a",
            "packs": [{"id": "cra-baseline", "version": draft_pack()["version"], "digest": "abc"}],
            "claims": [
                {
                    "id": claim_id,
                    "digest": version_digest(claim),
                    "status": "pass",
                    "checks": [{"index": 0, "check": "exist", "args": args, "status": "pass"}],
                }
            ],
        },
        requirements=[_requirement("CRA-PURPOSE")],
        claims=[claim],
    )
    return record_decision(report, decision)


def _requirement(requirement_id: str) -> dict:
    return {
        "id": requirement_id,
        "pack_id": "cra-baseline",
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


def _files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _section(page: str, kind: str) -> str:
    marker = f'data-list="{kind}"'
    start = page.index(marker)
    end = page.index("</ul>", start)
    return page[start:end]


class _serve:
    def __init__(self, workspace: Path):
        self.workspace = workspace

    def __enter__(self) -> str:
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(self.workspace)))
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def __exit__(self, *args) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def _get(url: str) -> str:
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.read().decode("utf-8")


def _post(url: str, fields: dict) -> str:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")
