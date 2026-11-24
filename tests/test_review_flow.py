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
                result_path = urllib.parse.unquote(result.group(1))
                fields = {
                    name: value
                    for name, value in re.findall(
                        r'name="(assess_[^"]+)"[^>]*value="([^"]*)"', review
                    )
                }
                fields.update(
                    {
                        "repo_id": "alpha",
                        "result": result_path,
                        "decision": "I read this run.",
                        "assess_disposition": "must_fix",
                        "assess_text": "The file is missing.",
                    }
                )
                saved = _post(base + "/review/compile", fields)
                self.assertIn("<h1>Check</h1>", saved)
                self.assertNotIn(">Start</a>", saved)
                self.assertFalse((Path(result_path).parent / "review-report.json").is_file())
                fields["name"] = "Ada Reviewer"
                signed = _post(base + "/review/compile", fields)
                self.assertIn("<h1>Check</h1>", signed)
                start = re.search(r'<a href="([^"]*mode=remediation[^"]*)">Start</a>', signed)
                self.assertIsNotNone(start)
                remediation = _get(base + start.group(1).replace("&amp;", "&"))
                self.assertIn('data-action="retire"', remediation)
                self.assertIn(">Re-check</button>", remediation)
                self.assertIn(">Save</button>", remediation)
                self.assertIn(">Sign Off</button>", remediation)
                self.assertIn(">Cancel</a>", remediation)
                self.assertNotIn(">Sign Remediation</button>", remediation)
                self.assertNotIn(">Re-run Checks</button>", remediation)
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
                    {"repo_id": "alpha", "result": result_path, "name": "Urban"},
                )
                self.assertIn("This signed remediation is read-only.", remedy)
                self.assertNotIn(">Sign Off</button>", remedy)
                nxt = _post_redirect(
                    base + "/check",
                    {"repo_id": "alpha", "action": "check", "return_to": "/review"},
                )
                again = _get(base + nxt)
                self.assertNotIn("Recorded from the remediation page.", again)
                self.assertIn("Take in the remediation report?", again)
                self.assertIn(">Take in the report</a>", again)
                self.assertIn(">Keep the new decisions</a>", again)
                self.assertNotIn('data-action="retire"', again)
                reused = _get(base + _href(again, "Take in the report"))
                self.assertNotIn("Recorded from the remediation page.", reused)
                self.assertNotIn("Take in the remediation report?", reused)
                kept = _get(base + _href(again, "Keep the new decisions"))
                self.assertNotIn("Recorded from the remediation page.", kept)
                self.assertNotIn("Take in the remediation report?", kept)
                table = _get(base + "/check?repo=alpha")
                self.assertIn("<th>Check Result</th>", table)
                self.assertIn("<th>Review</th>", table)
                self.assertIn("<th>Remedy</th>", table)
                self.assertIn(">View</a>", table)
                self.assertIn(">View report</a>", table)
            stored = read_json(next(Path(result_path).parent.glob("remedy-report_*.json")))
            self.assertIn("signed", stored)
            work = read_json(Path(result_path).parent / "review_items.json")
            self.assertNotIn("signed", work)
