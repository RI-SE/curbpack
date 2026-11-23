"""Review, remediation, Remedy Report, Check, and the next review, through the page."""

from __future__ import annotations

import re
import tempfile
import unittest
import urllib.parse
from pathlib import Path

from claims.bind import build_claim, write_claim
from common.jsonio import read_json
from common.store import load_requirement
from requirements.extract.pipeline import draft_pack
from tests.test_rev03_review import _get, _pack, _post, _post_redirect, _serve, _workspace


def _href(page: str, label: str) -> str:
    match = re.search(rf'<a class="btn[^"]*" href="([^"]+)">{label}</a>', page)
    if not match:
        raise AssertionError(f"{label} is not on the page")
    return match.group(1).replace("&amp;", "&")


class ReviewRemediationFlowTest(unittest.TestCase):
    def test_the_page_carries_a_review_through_remediation_and_into_the_next_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _pack(repo, "REQ-SHARED")
            pack_dir = repo / "tree" / "packs" / "cra-baseline" / draft_pack()["version"]
            requirement = load_requirement(pack_dir / "REQ-SHARED.json")
            claim = build_claim(
                claim_id="flow-note",
                requirement=requirement,
                source="documents",
                args={"path": "docs/a.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
                description="The file is the evidence.",
            )
            write_claim(repo / "kept" / "claims", claim)
            (repo / "docs").mkdir()
            (repo / "docs" / "a.md").write_text("a\n", encoding="utf-8")
            with _serve(workspace) as base:
                opened = _post_redirect(
                    base + "/check",
                    {"repo_id": "alpha", "action": "check", "return_to": "/review"},
                )
                review = _get(base + opened)
                self.assertIn(">Must be fixed</option>", review)
                self.assertNotIn('data-action="retire"', review)
                self.assertNotIn(">Re-Discover</button>", review)
                result = re.search(r"result=([^&]+)", opened)
                self.assertIsNotNone(result)
                compiled = _post(
                    base + "/review/compile",
                    {"repo_id": "alpha", "result": urllib.parse.unquote(result.group(1))},
                )
                report = re.search(r'name="report" value="([^"]+)"', compiled)
                self.assertIsNotNone(report)
                report_path = report.group(1)
                _post(
                    base + "/review",
                    {
                        "repo_id": "alpha",
                        "report": report_path,
                        "decision": "I read this run.",
                    },
                )
                signed = _post(
                    base + "/review/sign",
                    {"repo_id": "alpha", "report": report_path, "name": "Ada Reviewer"},
                )
                self.assertIn(">Remediate</a>", signed)
                remediation = _get(base + _href(signed, "Remediate"))
                self.assertIn('data-action="retire"', remediation)
                self.assertIn(">Sign Remedy Report</button>", remediation)
                form = re.search(
                    r'action="/review/remediate"(.*?)</form>',
                    remediation,
                    re.S,
                )
                self.assertIsNotNone(form)
                fields = dict(re.findall(r'name="([^"]+)" value="([^"]*)"', form.group(1)))
                fields["remediation"] = "Recorded from the remediation page."
                saved = _post(base + "/review/remediate", fields)
                self.assertIn("Recorded from the remediation page.", saved)
                remedy = _post(
                    base + "/review/remedy",
                    {"repo_id": "alpha", "report": report_path, "name": "Urban"},
                )
                self.assertIn(">Run Check</button>", remedy)
                nxt = _post_redirect(
                    base + "/check",
                    {"repo_id": "alpha", "action": "check", "return_to": "/review"},
                )
                again = _get(base + nxt)
                self.assertIn("Recorded from the remediation page.", again)
                self.assertIn("Take in the remediation report?", again)
                self.assertIn(">Take in the report</a>", again)
                self.assertIn(">Keep the new decisions</a>", again)
                self.assertNotIn('data-action="retire"', again)
                reused = _get(base + _href(again, "Take in the report"))
                self.assertIn("Recorded from the remediation page.", reused)
                self.assertNotIn("Take in the remediation report?", reused)
                kept = _get(base + _href(again, "Keep the new decisions"))
                self.assertIn("Recorded from the remediation page.", kept)
                self.assertNotIn("Take in the remediation report?", kept)
                table = _get(base + "/check?repo=alpha")
                self.assertIn("<th>Check Result</th>", table)
                self.assertIn("<th>Review</th>", table)
                self.assertIn("<th>Remedy</th>", table)
                self.assertIn("All Passed · Signed", table)
                self.assertIn("1 action · Signed", table)
            stored = read_json(repo / "signed" / "reports" / Path(report_path).name)
            self.assertIn("signed", stored)
