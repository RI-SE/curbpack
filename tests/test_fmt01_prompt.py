"""FMT-01 upgrade-or-cancel dialog. Only screens that already save ask."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import build_claim
from common.canonical import version_digest
from common.jsonio import read_json, write_json
from common.signing import generate_keypair
from common.store import save_pack, save_requirement
from common.validate import save_curbpack, validate_pack, validate_requirement
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack
from studio.compile.impl.report import compile_report
from studio.review.impl.items import sign_remedy_document


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode()


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form).encode()
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()


def _requirement() -> dict:
    document = validate_requirement(
        {
            "id": "REQ-A",
            "pack_id": "cra-baseline",
            "namespace": "RISE/CRA baseline",
            "source": {
                "framework": "EU",
                "instrument": "CRA",
                "identifier": "CELEX:32024R2847",
                "language": "en",
                "url": "https://example.invalid/cra",
            },
            "references": [{"nr": 1, "locator": "VII.1(a)", "law_text": "its intended purpose"}],
        }
    )
    document.pop("format_version", None)
    return document


def _claim(requirement: dict) -> dict:
    claim = build_claim(
        claim_id="claim-a",
        requirement=requirement,
        source="documents",
        args={"path": "README.md"},
        checks=[{"check": "exist", "args": {"paths": ["README.md"]}}],
        description="The file is the evidence.",
    )
    claim.pop("format_version", None)
    return claim


def _pack() -> dict:
    document = validate_pack(draft_pack())
    document.pop("format_version", None)
    return document


class FormatPromptTest(unittest.TestCase):
    def _workspace(self) -> tuple[Path, Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        repo = root / "widget"
        repo.mkdir()
        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        pack_dir = repo / "tree" / "packs" / "cra-baseline" / draft_pack()["version"]
        pack_dir.mkdir(parents=True)
        write_json(repo / "curbpack.json", created_curbpack(packs=["cra-baseline"], packs_dir="tree/packs", claims_dir="kept/claims", results_dir="runs/out", reports_dir="signed/reports"))
        write_json(pack_dir / "pack.json", _pack())
        write_json(pack_dir / "REQ-A.json", _requirement())
        write_json(repo / "kept" / "claims" / "claim-a.json", _claim(_requirement()))
        save_repos(root, add_repo(root, load_repos(root), name="Widget", path=str(repo)))
        set_open_repo(root, "widget")
        return root, repo, pack_dir

    def _serve(self, root: Path):
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    def _form(self, page: str) -> str:
        start = page.index('class="format-upgrade"')
        return page[start:page.index("</form>", start)]

    def _assert_same_choice(self, page: str) -> None:
        self.assertIn('class="format-upgrade"', page)
        self.assertIn('name="format_upgrade" value="upgrade"', page)
        self.assertIn(">Convert</button>", page)
        self.assertIn('name="format_upgrade" value="cancel"', page)
        self.assertNotIn("<dialog", page[page.index('class="format-upgrade"'):page.index("</form>", page.index('class="format-upgrade"'))])
        self.assertEqual(page.count('class="format-upgrade"'), 1)

    def test_opening_an_unversioned_requirement_asks_and_does_not_write(self):
        root, _repo, pack_dir = self._workspace()
        path = pack_dir / "REQ-A.json"
        before = path.read_bytes()
        page = _get(self._serve(root) + "/requirements/requirement/REQ-A?repo=widget&pack=cra-baseline")
        self._assert_same_choice(page)
        self.assertIn("<h1>REQ-A</h1>", page)
        self.assertEqual(path.read_bytes(), before)

    def test_cancel_leaves_the_requirement_and_upgrade_writes_only_the_version(self):
        root, _repo, pack_dir = self._workspace()
        path = pack_dir / "REQ-A.json"
        original = _requirement()
        before = path.read_bytes()
        base = self._serve(root)
        fields = {
            "kind": "requirement",
            "repo": "widget",
            "pack": "cra-baseline",
            "requirement": "REQ-A",
            "next": "/requirements/requirement/REQ-A?repo=widget&pack=cra-baseline",
        }
        cancelled = _post(base + "/format-upgrade", {**fields, "format_upgrade": "cancel"})
        self.assertEqual(path.read_bytes(), before)
        self._assert_same_choice(cancelled)
        upgraded = _post(base + "/format-upgrade", {**fields, "format_upgrade": "upgrade"})
        stored = read_json(path)
        self.assertEqual(stored.pop("format_version"), 1)
        self.assertEqual(stored, original)
        self.assertNotIn('class="format-upgrade"', upgraded)
        written = path.read_bytes()
        again = _post(base + "/format-upgrade", {**fields, "format_upgrade": "upgrade"})
        self.assertEqual(path.read_bytes(), written)
        self.assertNotIn('class="format-upgrade"', again)

    def test_pack_claim_curbpack_and_review_items_use_the_same_prompt(self):
        root, repo, pack_dir = self._workspace()
        save_curbpack(repo / "curbpack.json", read_json(repo / "curbpack.json"))
        save_requirement(pack_dir, _requirement())
        base = self._serve(root)
        pack_before = (pack_dir / "pack.json").read_bytes()
        pack_page = _get(base + "/requirements?repo=widget")
        self._assert_same_choice(pack_page)
        self.assertEqual((pack_dir / "pack.json").read_bytes(), pack_before)

        claim_before = (repo / "kept" / "claims" / "claim-a.json").read_bytes()
        claim_page = _get(base + "/claims?repo=widget")
        self._assert_same_choice(claim_page)
        self.assertEqual((repo / "kept" / "claims" / "claim-a.json").read_bytes(), claim_before)

        save_pack(pack_dir, _pack())
        curbpack_path = repo / "curbpack.json"
        write_json(curbpack_path, created_curbpack(packs=["cra-baseline"], packs_dir="tree/packs", claims_dir="kept/claims", results_dir="runs/out", reports_dir="signed/reports"))
        curbpack_before = curbpack_path.read_bytes()
        curbpack_page = _get(base + "/requirements?repo=widget")
        self._assert_same_choice(curbpack_page)
        self.assertEqual(curbpack_path.read_bytes(), curbpack_before)

        run_dir = repo / "runs" / "out" / "run-result_20260101T000000Z"
        run_dir.mkdir(parents=True)
        run_path = run_dir / "run-result.json"
        write_json(
            run_path,
            {
                "tool": "curbcheck",
                "tool_version": "0.0.1a",
                "packs": [{"id": "cra-baseline", "version": "0.1.0", "digest": "abc"}],
                "claims": [],
            },
        )
        items_path = run_dir / "review_items.json"
        write_json(items_path, {"items": [], "notes": "keep"})
        items_before = items_path.read_bytes()
        review = _get(base + "/review?repo=widget&result=" + urllib.parse.quote(str(run_path.resolve())))
        self._assert_same_choice(review)
        self.assertEqual(items_path.read_bytes(), items_before)
        forced = _get(
            base
            + "/review?repo=widget&resume=1&result="
            + urllib.parse.quote(str(run_path.resolve()))
        )
        self._assert_same_choice(forced)
        resumed = read_json(items_path)
        self.assertNotIn("format_version", resumed)
        self.assertEqual(resumed.get("notes"), "keep")
        cancelled = _post(
            base + "/format-upgrade",
            {
                "kind": "review_items",
                "repo": "widget",
                "result": str(run_path.resolve()),
                "next": "/review?repo=widget&result=" + urllib.parse.quote(str(run_path.resolve())),
                "format_upgrade": "cancel",
            },
        )
        self.assertNotIn("format_version", read_json(items_path))
        self._assert_same_choice(cancelled)
        before_upgrade = read_json(items_path)
        upgraded = _post(
            base + "/format-upgrade",
            {
                "kind": "review_items",
                "repo": "widget",
                "result": str(run_path.resolve()),
                "next": "/review?repo=widget&result=" + urllib.parse.quote(str(run_path.resolve())),
                "format_upgrade": "upgrade",
            },
        )
        stored = read_json(items_path)
        self.assertEqual(stored.pop("format_version"), 1)
        self.assertEqual(stored, before_upgrade)
        self.assertNotIn('class="format-upgrade"', upgraded)

    def test_pack_sources_and_claims_ask_about_one_file_at_a_time(self):
        root, repo, pack_dir = self._workspace()
        second = build_claim(
            claim_id="claim-b",
            requirement=_requirement(),
            source="documents",
            args={"path": "README.md"},
            checks=[{"check": "exist", "args": {"paths": ["README.md"]}}],
            description="The file is the evidence.",
        )
        second.pop("format_version", None)
        write_json(repo / "kept" / "claims" / "claim-b.json", second)
        base = self._serve(root)
        curbpack_before = (repo / "curbpack.json").read_bytes()
        pack_before = (pack_dir / "pack.json").read_bytes()
        page = _get(base + "/requirements?repo=widget")
        self.assertEqual(page.count('class="format-upgrade"'), 2)
        self.assertIn("Convert curbpack.json from format version 0 to version 1?", page)
        self.assertIn("Convert cra-baseline/pack.json from format version 0 to version 1?", page)
        self.assertEqual((repo / "curbpack.json").read_bytes(), curbpack_before)
        self.assertEqual((pack_dir / "pack.json").read_bytes(), pack_before)
        _post(
            base + "/format-upgrade",
            {
                "kind": "pack",
                "repo": "widget",
                "pack": "cra-baseline",
                "next": "/requirements?repo=widget",
                "format_upgrade": "upgrade",
            },
        )
        self.assertEqual((repo / "curbpack.json").read_bytes(), curbpack_before)
        self.assertEqual(read_json(pack_dir / "pack.json")["format_version"], 1)
        remaining = _get(base + "/requirements?repo=widget")
        self._assert_same_choice(remaining)
        self.assertIn("Convert curbpack.json from format version 0 to version 1?", remaining)

        claim_a = (repo / "kept" / "claims" / "claim-a.json").read_bytes()
        claim_b = (repo / "kept" / "claims" / "claim-b.json").read_bytes()
        claims = _get(base + "/claims?repo=widget")
        self.assertEqual(claims.count('class="format-upgrade"'), 2)
        self.assertIn("Convert claim-a.json from format version 0 to version 1?", claims)
        self.assertIn("Convert claim-b.json from format version 0 to version 1?", claims)
        _post(
            base + "/format-upgrade",
            {
                "kind": "claim",
                "repo": "widget",
                "claim": "claim-b",
                "next": "/claims?repo=widget",
                "format_upgrade": "upgrade",
            },
        )
        self.assertEqual((repo / "kept" / "claims" / "claim-a.json").read_bytes(), claim_a)
        self.assertEqual(read_json(repo / "kept" / "claims" / "claim-b.json")["format_version"], 1)
        self.assertNotEqual((repo / "kept" / "claims" / "claim-b.json").read_bytes(), claim_b)
        held = _get(base + "/claims?repo=widget")
        self._assert_same_choice(held)
        self.assertIn("Convert claim-a.json from format version 0 to version 1?", held)
        self.assertNotIn("claim-b.json", self._form(held))

    def test_upgrade_writes_the_open_working_copy(self):
        from requirements.workspace import create_extraction_copy, mark_selected

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        selected = create_extraction_copy(root, "cra-baseline", _pack(), at="2026-01-01T000000Z")
        foreign = create_extraction_copy(root, "cra-baseline", _pack(), at="2026-01-01T000001Z")
        write_json(selected / "REQ-A.json", _requirement())
        write_json(foreign / "REQ-A.json", _requirement())
        mark_selected(root, "cra-baseline", "2026-01-01T000000Z")
        selected_before = (selected / "REQ-A.json").read_bytes()
        foreign_before = (foreign / "REQ-A.json").read_bytes()
        page = _get(
            self._serve(root)
            + "/requirements/requirement/REQ-A?timestamp=2026-01-01T000001Z"
        )
        self._assert_same_choice(page)
        dialog = self._form(page)
        self.assertIn('name="timestamp" value="2026-01-01T000001Z"', dialog)
        self.assertEqual((selected / "REQ-A.json").read_bytes(), selected_before)
        self.assertEqual((foreign / "REQ-A.json").read_bytes(), foreign_before)
        upgraded = _post(
            self._serve(root) + "/format-upgrade",
            {
                "kind": "requirement",
                "requirement": "REQ-A",
                "timestamp": "2026-01-01T000001Z",
                "next": "/requirements/requirement/REQ-A?timestamp=2026-01-01T000001Z",
                "format_upgrade": "upgrade",
            },
        )
        self.assertNotIn('class="format-upgrade"', upgraded)
        stored = read_json(foreign / "REQ-A.json")
        self.assertEqual(stored.pop("format_version"), 1)
        selected_stored = read_json(selected / "REQ-A.json")
        self.assertNotIn("format_version", selected_stored)

    def test_saving_an_older_requirement_keeps_its_format(self):
        from requirements.editing import save_working_requirement

        _root, _repo, pack_dir = self._workspace()
        path = pack_dir / "REQ-A.json"
        edited = _requirement()
        edited["note"] = "Kept on the old format."
        save_working_requirement(
            pack_dir,
            edited,
            expected_digest=version_digest(_requirement()),
        )
        stored = read_json(path)
        self.assertNotIn("format_version", stored)
        self.assertEqual(stored["note"], "Kept on the old format.")

    def test_check_reads_an_unversioned_pack_without_writing_or_asking(self):
        root, repo, pack_dir = self._workspace()
        pack_before = (pack_dir / "pack.json").read_bytes()
        requirement_before = (pack_dir / "REQ-A.json").read_bytes()
        claim_before = (repo / "kept" / "claims" / "claim-a.json").read_bytes()
        page = _post(self._serve(root) + "/check", {"repo_id": "widget", "action": "check"})
        self.assertNotIn('class="format-upgrade"', page)
        self.assertIn("<h1>Check</h1>", page)
        self.assertEqual((pack_dir / "pack.json").read_bytes(), pack_before)
        self.assertEqual((pack_dir / "REQ-A.json").read_bytes(), requirement_before)
        self.assertEqual((repo / "kept" / "claims" / "claim-a.json").read_bytes(), claim_before)

    def test_opening_a_sealed_file_does_not_ask_or_write(self):
        root, repo, pack_dir = self._workspace()
        save_pack(pack_dir, _pack())
        save_requirement(pack_dir, _requirement())
        requirement = _requirement()
        claim = _claim(requirement)
        run = {
            "tool": "curbcheck",
            "tool_version": "0.0.1a",
            "commit": "abc123",
            "worktree": "clean",
            "packs": [{"id": "cra-baseline", "version": "0.1.0", "digest": "abc"}],
            "claims": [
                {
                    "id": claim["id"],
                    "digest": version_digest(claim),
                    "status": "pass",
                    "checks": [
                        {
                            "index": 0,
                            "check": "exist",
                            "args": claim["checks"][0]["args"],
                            "status": "pass",
                        }
                    ],
                }
            ],
        }
        run_dir = repo / "runs" / "out" / "run-result_20260101T000000Z"
        run_dir.mkdir(parents=True)
        run_path = run_dir / "run-result.json"
        write_json(run_path, run)
        report = compile_report(run_result=run, requirements=[requirement], claims=[claim])
        report_path = repo / "signed" / "reports" / "review-report_20260101T000000Z.json"
        report_path.parent.mkdir(parents=True)
        write_json(report_path, report)
        private, _public = generate_keypair()
        remedy = sign_remedy_document([], name="Ada", private_key=private, at="2026-01-01T00:00:00Z")
        remedy_path = repo / "signed" / "reports" / "remedy-report_20260101T000000Z.json"
        write_json(remedy_path, remedy)
        sealed_items = report_path.with_name(report_path.stem + ".items.json")
        write_json(sealed_items, {"items": [], "notes": "sealed"})
        before = {
            run_path: run_path.read_bytes(),
            report_path: report_path.read_bytes(),
            remedy_path: remedy_path.read_bytes(),
            sealed_items: sealed_items.read_bytes(),
        }
        base = self._serve(root)
        run_page = _get(base + "/review?repo=widget&result=" + urllib.parse.quote(str(run_path.resolve())))
        report_page = _get(base + "/review?repo=widget&report=" + urllib.parse.quote(str(report_path.resolve())))
        self.assertNotIn('class="format-upgrade"', run_page)
        self.assertNotIn('class="format-upgrade"', report_page)
        for path, contents in before.items():
            self.assertEqual(path.read_bytes(), contents)
