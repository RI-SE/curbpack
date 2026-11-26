"""Technical details renders recorded Check facts without a raw dump."""

from __future__ import annotations

import html
import json
import unittest

from studio.review.review_page import review_page


def _page(result: dict, door: dict | None = None, **kwargs) -> str:
    report = {"run_result": result, "claims": kwargs.pop("claims", []), "requirements": kwargs.pop("requirements", []), "appendix": []}
    opened = {
        "repo_id": "alpha",
        "selected_result": "/tmp/runs/run-result_20260101T153045Z.json",
        "presentation": {"groups": []},
    }
    if door:
        opened.update(door)
    return review_page(report, None, door=opened, **kwargs).decode()


def _result(**overrides) -> dict:
    result = {
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "commit": "abc123def",
        "worktree": "clean",
        "packs": [{"id": "house-policy", "version": "1.2.3", "digest": "packdigest"}],
        "claims": [
            {
                "id": "HOUSE-1",
                "digest": "claimdigest",
                "namespace": "RISE/House",
                "pack_id": "house-policy",
                "requirement_id": "REQ-1",
                "requirement_digest": "reqdigest",
                "actual_digest": "actualdigest",
                "binding": "match",
                "status": "pass",
                "checks": [
                    {
                        "index": 0,
                        "check": "exist",
                        "args": {"paths": ["SECURITY.md"]},
                        "status": "pass",
                    }
                ],
            }
        ],
    }
    result.update(overrides)
    return result


def _section(page: str, marker: str) -> str:
    start = page.index(marker)
    end = page.index("</section>", start)
    return page[start:end]


class TechnicalDetailsRenderTest(unittest.TestCase):
    def test_normal_metadata_is_structured_and_collapsed(self):
        page = _page(_result())
        execution = _section(page, "data-run-header")
        packs = _section(page, "data-packs")
        recorded = _section(page, "data-secondary")
        raw = _section(page, "data-raw-result")

        self.assertIn("Execution", execution)
        self.assertIn("2026-01-01 15:30:45 UTC", execution)
        self.assertIn("curbcheck", execution)
        self.assertIn("0.0.1a", execution)
        self.assertIn("abc123def", execution)
        self.assertIn('data-worktree="clean"', execution)
        self.assertIn("The worktree was clean.", execution)
        self.assertIn("run-result_20260101T153045Z.json", execution)

        self.assertIn("Loaded Packs", packs)
        self.assertIn("house-policy", packs)
        self.assertIn("1.2.3", packs)
        self.assertIn("<details>", packs)
        self.assertNotIn("<details open", packs)
        self.assertIn("packdigest", packs)
        self.assertIn("No recorded signature.", packs)

        self.assertIn("Recorded object details", recorded)
        self.assertIn("HOUSE-1", recorded)
        self.assertIn("<dt>Claim</dt>", recorded)
        self.assertIn("claimdigest", recorded)
        self.assertIn("<dt>Requirement</dt>", recorded)
        self.assertIn("reqdigest", recorded)
        self.assertIn("<dt>Resolved requirement</dt>", recorded)
        self.assertIn("actualdigest", recorded)
        self.assertNotIn("claimdigest reqdigest", recorded)
        self.assertNotIn("<details open", recorded)
        self.assertIn("Arguments", recorded)
        self.assertIn("&quot;paths&quot;", recorded)
        self.assertNotIn(">Technical details</summary>", recorded)

        self.assertIn("Raw result", raw)
        self.assertIn("Recorded JSON", raw)
        self.assertNotIn("<details open", raw)
        self.assertIn(html.escape(json.dumps(_result(), indent=2, ensure_ascii=False)[:40]), raw)
        self.assertEqual(page.count(">Technical details<"), 1)

    def test_dirty_worktree_does_not_invent_changed_files(self):
        page = _page(
            _result(worktree="dirty"),
            door={"changed_files": ["secret-uncommitted.md"], "presentation": {"groups": []}},
        )
        execution = _section(page, "data-run-header")
        self.assertIn('data-worktree="dirty"', execution)
        self.assertIn(
            "This result is not verification of that commit&#x27;s content.",
            execution,
        )
        self.assertIn("The commit alone cannot reproduce the checked content.", execution)
        self.assertNotIn("secret-uncommitted.md", page)
        self.assertNotIn("changed files", page.lower())

    def test_unavailable_git_metadata_is_labeled_unavailable(self):
        result = _result()
        result.pop("commit")
        result.pop("worktree")
        page = _page(result, door={"selected_result": "/tmp/custom-result.json", "presentation": {"groups": []}})
        execution = _section(page, "data-run-header")
        self.assertIn('data-worktree="unavailable"', execution)
        self.assertIn('data-commit="unavailable"', execution)
        self.assertIn("unavailable", execution)
        self.assertNotIn("The worktree was clean.", page)
        self.assertNotIn("not verification of that commit", page)
        self.assertNotIn("abc123def", execution)

    def test_legacy_claim_and_repository_text_stay_safe(self):
        legacy = {
            "tool": "curbcheck",
            "tool_version": "0.0.1a",
            "packs": [{"id": "pack<script>", "version": "1", "digest": "d"}],
            "claims": [
                {
                    "id": "legacy<id>",
                    "digest": "olddigest",
                    "status": "fail",
                    "checks": [
                        {
                            "index": 0,
                            "check": "exist",
                            "args": {"paths": ["a<b>.md"]},
                            "status": "fail",
                            "detail": "a<b>.md is absent",
                        }
                    ],
                }
            ],
        }
        page = _page(legacy, door={"selected_result": "", "source_result": "", "presentation": {"groups": []}})
        recorded = _section(page, "data-secondary")
        self.assertIn("legacy&lt;id&gt;", recorded)
        self.assertIn("olddigest", recorded)
        self.assertIn("not recorded", recorded)
        self.assertNotIn("legacy<id>", page)
        self.assertNotIn("pack<script>", page)
        self.assertIn("pack&lt;script&gt;", page)
        self.assertNotIn("a<b>.md", page)
        self.assertIn("a&lt;b&gt;.md", page)
        self.assertIn('data-worktree="unavailable"', page)
        self.assertIn("Check time", page)
        self.assertIn("unavailable", _section(page, "data-run-header"))
