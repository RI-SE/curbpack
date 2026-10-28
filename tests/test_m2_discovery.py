"""M2: discovery walks the working tree and does not store candidates."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from discovery.search import discover_candidates, highlight_verified, read_source_text, verify_excerpt
from requirements.extract.pipeline import extract_annex_vii_risk


def _tree(root: Path) -> None:
    files = {
        "README.md": "Project readme.\n",
        "docs/threat-model-draft.md": "A draft threat note.\n",
        "docs/annex-vii/risk_assessment.md": "placeholder path only\n",
        "docs/security-note.md": "The note mentions cybersecurity risk.\n",
        "notes/THREAT-log.md": "outside the preferred docs tree\n",
        "marketing/brochure.md": "The brochure mentions cybersecurity risk.\n",
        "FUTURE_plan.md": "risk assessment planned later\n",
        "node_modules/pkg/README.md": "cybersecurity risk inside dependencies\n",
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


HUNT = {
    "packs": ["cra-baseline"],
    "search_hints": {
        "sources": [{"source": "documents"}],
        "exclude_path_globs": ["**/node_modules/**", "*FUTURE_*"],
        "prefer_path_globs": ["**/README*", "**/docs/**"],
    },
}


class DiscoveryTest(unittest.TestCase):
    def test_candidates_follow_hints_and_hunt_and_are_not_stored(self):
        requirement = extract_annex_vii_risk()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _tree(repo)
            before = sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*") if path.is_file())
            found = discover_candidates(repo, requirement, HUNT)
            after = sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*") if path.is_file())
            self.assertEqual(before, after)
            self.assertEqual(
                [(item["path"], item["matched_by"]) for item in found],
                [
                    ("docs/annex-vii/risk_assessment.md", "path_hint"),
                    ("docs/threat-model-draft.md", "path_hint"),
                    ("notes/THREAT-log.md", "path_hint"),
                    ("docs/security-note.md", "concept"),
                    ("marketing/brochure.md", "concept"),
                ],
            )
            for item in found:
                self.assertEqual(set(item), {"path", "matched_by", "matched_hints", "excerpt"})
                self.assertTrue(item["matched_hints"])
            self.assertEqual(found, discover_candidates(repo, requirement, HUNT, limit=40))
            self.assertEqual(
                [item["path"] for item in discover_candidates(repo, requirement, HUNT, limit=2)],
                [
                    "docs/annex-vii/risk_assessment.md",
                    "docs/threat-model-draft.md",
                ],
            )

    def test_sources_and_expected_evidence_do_not_change_the_walk(self):
        requirement = extract_annex_vii_risk()
        altered = copy.deepcopy(requirement)
        altered["discovery_hints"]["sources"] = [{"source": "doors", "args": {"project": "secret"}}]
        altered["discovery_hints"]["expected_evidence"] = ["not-a-real-kind"]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _tree(repo)
            self.assertEqual(
                discover_candidates(repo, requirement, HUNT),
                discover_candidates(repo, altered, HUNT),
            )


class ReadSourceTextTest(unittest.TestCase):
    def test_reads_a_candidate_and_rejects_escape_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _tree(repo)
            text = read_source_text(repo, "docs/security-note.md")
            self.assertIn("cybersecurity risk", text)
            with self.assertRaises(ModelError):
                read_source_text(repo, "../outside.md")
            with self.assertRaises(ModelError):
                read_source_text(repo, "/etc/passwd")
            with self.assertRaises(ModelError):
                read_source_text(repo, "docs/missing.md")

    def test_verify_excerpt_is_exact_and_highlight_marks_only_a_hit(self):
        body = "The note mentions cybersecurity risk.\n"
        start, end = verify_excerpt(body, "  cybersecurity risk  ")
        self.assertEqual(body[start:end], "cybersecurity risk")
        self.assertIsNone(verify_excerpt(body, "cyber security risk"))
        self.assertIsNone(verify_excerpt(body, "cybersecurity\nrisk"))
        html_text, found = highlight_verified(body, "cybersecurity risk")
        self.assertTrue(found)
        self.assertIn("<mark>cybersecurity risk</mark>", html_text)
        html_text, found = highlight_verified(body, "not in the file")
        self.assertFalse(found)
        self.assertNotIn("<mark>", html_text)


if __name__ == "__main__":
    unittest.main()
