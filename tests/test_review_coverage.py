"""Grey-out is a presentation decision. It does not change which candidates exist."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.run import build_run_result
from claims.bind import build_claim
from claims.ui.coverage import (
    NO_REPLACEMENT,
    REPLACEMENT_UNCHECKED,
    claim_passed,
    covered_paths,
    retire_warning,
)
from common.canonical import version_digest


class CoverageHookTest(unittest.TestCase):
    def test_only_a_fully_passed_claim_on_its_own_path_is_covered(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs").mkdir()
            (repo / "docs" / "a.md").write_text("hello\n", encoding="utf-8")
            (repo / "docs" / "b.md").write_text("other\n", encoding="utf-8")
            passed = _claim("claim-a", "docs/a.md", [{"check": "exist", "args": {"paths": ["docs/a.md"]}}])
            failed = _claim(
                "claim-b",
                "docs/b.md",
                [
                    {
                        "check": "contents",
                        "args": {"path": "docs/b.md", "probes": [{"kind": "size", "bytes": 200, "op": ">="}]},
                    }
                ],
            )
            pointed_elsewhere = _claim(
                "claim-elsewhere",
                "docs/a.md",
                [{"check": "exist", "args": {"paths": ["docs/b.md"]}}],
            )
            run = build_run_result(repo, [passed, failed, pointed_elsewhere], _packs())
            self.assertEqual(covered_paths([passed], run, "REQ-A"), {"docs/a.md"})
            self.assertEqual(covered_paths([failed], run, "REQ-A"), set())
            self.assertEqual(covered_paths([pointed_elsewhere], run, "REQ-A"), set())
            self.assertEqual(covered_paths([passed, pointed_elsewhere], run, "REQ-A"), set())
            self.assertFalse(claim_passed(passed, None))
            stale = dict(run)
            stale["claims"] = [dict(run["claims"][0], digest="not-this-claim")] + run["claims"][1:]
            self.assertFalse(claim_passed(passed, stale))
            self.assertNotEqual(version_digest(passed), "not-this-claim")

    def test_absent_run_skip_and_absolute_path_are_not_covered(self):
        claim = _claim("claim-a", "docs/a.md", [{"check": "exist", "args": {"paths": ["docs/a.md"]}}])
        self.assertEqual(covered_paths([claim], None, "REQ-A"), set())
        skipped = {
            "id": "claim-a",
            "digest": version_digest(claim),
            "status": "skipped",
            "checks": [{"index": 0, "check": "exist", "args": {"paths": ["docs/a.md"]}, "status": "skipped", "detail": "later"}],
        }
        self.assertEqual(covered_paths([claim], {"claims": [skipped]}, "REQ-A"), set())
        absolute = {
            "id": "claim-abs",
            "requirement_id": "REQ-A",
            "args": {"path": "/etc/passwd"},
            "checks": [{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
        }
        self.assertEqual(covered_paths([absolute], {"claims": []}, "REQ-A"), set())

    def test_retire_warns_until_a_replacement_has_passed(self):
        old = _claim("claim-old", "docs/old.md", [{"check": "exist", "args": {"paths": ["docs/old.md"]}}])
        new = _claim("claim-new", "docs/new.md", [{"check": "exist", "args": {"paths": ["docs/new.md"]}}])
        self.assertEqual(retire_warning(old, [old], None), NO_REPLACEMENT)
        self.assertEqual(retire_warning(old, [old, new], None), REPLACEMENT_UNCHECKED)
        run = {
            "claims": [
                {
                    "id": "claim-new",
                    "digest": version_digest(new),
                    "status": "pass",
                    "checks": [{"index": 0, "check": "exist", "args": {"paths": ["docs/new.md"]}, "status": "pass"}],
                }
            ]
        }
        self.assertEqual(retire_warning(old, [old, new], run), "")


def _claim(claim_id: str, path: str, checks: list[dict]) -> dict:
    return build_claim(
        claim_id=claim_id,
        requirement_id="REQ-A",
        source="documents",
        args={"path": path},
        checks=checks,
        description="Evidence for the requirement.",
    )


def _packs() -> list[dict]:
    return [{"id": "house", "version": "0.1.0", "digest": "abc"}]


if __name__ == "__main__":
    unittest.main()
