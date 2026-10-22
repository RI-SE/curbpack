"""Assessment returns model fields only when a call succeeds, and verifies excerpts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from discovery.assess import assess_candidates

LAW = "The product shall state its intended purpose."
REQUIREMENT = {
    "id": "CRA-ANNEX-VII-DESCRIPTION-PURPOSE",
    "references": [{"law_text": LAW, "locator": "VII.1(a)"}],
}


def _candidate(path: str, excerpt: str = "intended purpose") -> dict:
    return {"path": path, "matched_by": "concept", "excerpt": excerpt}


class AssessCandidatesTest(unittest.TestCase):
    def test_exact_excerpt_is_verified_and_prompt_contains_law_and_path(self):
        seen = []

        def complete(prompt, _settings):
            seen.append(prompt)
            return (
                '{"score": 0.9, "rank": "High", "why": "Names the intended purpose.", '
                '"excerpt": "intended purpose"}'
            )

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("The intended purpose is a demo.\n", encoding="utf-8")
            rows = assess_candidates(
                repo,
                REQUIREMENT,
                [_candidate("README.md")],
                complete=complete,
                assess_limit=5,
            )
        self.assertEqual(len(seen), 1)
        self.assertIn(LAW, seen[0])
        self.assertIn("README.md", seen[0])
        row = rows[0]
        self.assertEqual(row["assessment_state"], "assessed")
        self.assertEqual(row["score"], 0.9)
        self.assertEqual(row["rank"], "High")
        self.assertEqual(row["why"], "Names the intended purpose.")
        self.assertTrue(row["model_excerpt_verified"])
        self.assertEqual(row["excerpt"], "intended purpose")

    def test_mismatched_model_excerpt_keeps_score_and_is_not_verified(self):
        def complete(_prompt, _settings):
            return (
                '{"score": 0.4, "rank": "Low", "why": "Only a heading.", '
                '"excerpt": "this sentence is not in the file"}'
            )

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("The intended purpose is a demo.\n", encoding="utf-8")
            row = assess_candidates(
                repo,
                REQUIREMENT,
                [_candidate("README.md", excerpt="intended purpose")],
                complete=complete,
                assess_limit=5,
            )[0]
        self.assertEqual(row["score"], 0.4)
        self.assertEqual(row["why"], "Only a heading.")
        self.assertFalse(row["model_excerpt_verified"])
        self.assertEqual(row["excerpt"], "intended purpose")

    def test_unparseable_reply_fails_without_a_score(self):
        def complete(_prompt, _settings):
            return "not json"

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            row = assess_candidates(
                repo,
                REQUIREMENT,
                [_candidate("README.md", excerpt="")],
                complete=complete,
                assess_limit=5,
            )[0]
        self.assertEqual(row["assessment_state"], "failed")
        self.assertEqual(row["matched_by"], "concept")
        self.assertNotIn("score", row)

    def test_endpoint_error_writes_no_score(self):
        def complete(_prompt, _settings):
            raise ModelError("produce", "endpoint", "a reachable model server")

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            row = assess_candidates(
                repo,
                REQUIREMENT,
                [_candidate("README.md", excerpt="")],
                complete=complete,
                assess_limit=5,
            )[0]
        self.assertEqual(row["assessment_state"], "failed")
        self.assertNotIn("score", row)

    def test_cap_keeps_unscored_candidates(self):
        calls = []

        def complete(prompt, _settings):
            calls.append(prompt)
            return '{"score": 0.2, "rank": "Low", "why": "Short.", "excerpt": ""}'

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            candidates = []
            for index in range(6):
                name = f"note-{index}.md"
                (repo / name).write_text(f"file {index}\n", encoding="utf-8")
                candidates.append(_candidate(name, excerpt=""))
            rows = assess_candidates(repo, REQUIREMENT, candidates, complete=complete, assess_limit=2)
        self.assertEqual(len(calls), 2)
        self.assertEqual([row["assessment_state"] for row in rows[:2]], ["assessed", "assessed"])
        self.assertEqual([row["assessment_state"] for row in rows[2:]], ["not_assessed"] * 4)
        self.assertTrue(all(row.get("assessment_skip") == "cap" for row in rows[2:]))
        self.assertEqual(len(rows), 6)

    def test_unchanged_inputs_are_reused_and_a_changed_file_is_scored_again(self):
        calls = []

        def complete(_prompt, _settings):
            calls.append(1)
            return '{"score": 0.8, "rank": "High", "why": "Matches.", "excerpt": "alpha"}'

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "README.md"
            path.write_text("alpha line\n", encoding="utf-8")
            first = assess_candidates(
                repo, REQUIREMENT, [_candidate("README.md", excerpt="alpha")], complete=complete, assess_limit=5
            )
            second = assess_candidates(
                repo,
                REQUIREMENT,
                [_candidate("README.md", excerpt="alpha")],
                complete=complete,
                assess_limit=5,
                prior=first,
            )
            path.write_text("alpha line changed\n", encoding="utf-8")
            third = assess_candidates(
                repo,
                REQUIREMENT,
                [_candidate("README.md", excerpt="alpha")],
                complete=complete,
                assess_limit=5,
                prior=first,
            )
        self.assertEqual(len(calls), 2)
        self.assertEqual(second[0]["assessment_state"], "reused")
        self.assertEqual(second[0]["score"], 0.8)
        self.assertEqual(third[0]["assessment_state"], "assessed")


if __name__ == "__main__":
    unittest.main()
