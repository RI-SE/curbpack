"""Researcher feedback is operational state and survives another Discover run."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.schema import validate_check_args
from common.errors import ModelError
from common.jsonio import read_json
from discovery.feedback import add_finding, feedback_path, load_feedback, save_check, save_vote
from discovery.jobs import start_discover_job


class FeedbackTest(unittest.TestCase):
    def test_vote_and_check_round_trip_and_a_bad_probe_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            repo.mkdir()
            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            known = ["REQ-A"]
            save_vote(
                root,
                repo_id="sample",
                source_id="cra-xml-vii",
                timestamp="2026-10-14T080000Z",
                requirement_id="REQ-A",
                path="README.md",
                vote="useful",
                known_ids=known,
            )
            save_check(
                root,
                repo_id="sample",
                source_id="cra-xml-vii",
                timestamp="2026-10-14T080000Z",
                requirement_id="REQ-A",
                path="README.md",
                check="exist",
                args={"paths": ["README.md"]},
                known_ids=known,
            )
            path = feedback_path(root, "sample", "cra-xml-vii", "2026-10-14T080000Z")
            before = path.read_bytes()
            with self.assertRaises(ModelError):
                validate_check_args("contents", {"path": "README.md", "probes": [{"kind": "pattern", "pattern": ""}]})
            with self.assertRaises(ModelError):
                save_check(
                    root,
                    repo_id="sample",
                    source_id="cra-xml-vii",
                    timestamp="2026-10-14T080000Z",
                    requirement_id="REQ-A",
                    path="README.md",
                    check="contents",
                    args={"path": "README.md", "probes": [{"kind": "pattern", "pattern": ""}]},
                    known_ids=known,
                )
            self.assertEqual(path.read_bytes(), before)
            loaded = load_feedback(root, "sample", "cra-xml-vii", "2026-10-14T080000Z")
            entry = loaded["requirements"]["REQ-A"]["README.md"]
            self.assertEqual(entry["vote"], "useful")
            self.assertEqual(entry["checks"], [{"check": "exist", "args": {"paths": ["README.md"]}}])

    def test_unknown_requirement_and_discover_does_not_delete_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            repo.mkdir()
            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            save_vote(
                root,
                repo_id="sample",
                source_id="cra-xml-vii",
                timestamp="2026-10-14T080000Z",
                requirement_id="REQ-A",
                path="README.md",
                vote="poor",
                known_ids=["REQ-A"],
            )
            path = feedback_path(root, "sample", "cra-xml-vii", "2026-10-14T080000Z")
            before = path.read_bytes()
            with self.assertRaises(ModelError):
                save_vote(
                    root,
                    repo_id="sample",
                    source_id="cra-xml-vii",
                    timestamp="2026-10-14T080000Z",
                    requirement_id="NO-SUCH",
                    path="README.md",
                    vote="useful",
                    known_ids=["REQ-A"],
                )
            self.assertEqual(path.read_bytes(), before)
            start_discover_job(
                root / "jobs",
                job_id="discover-keep",
                workspace=root,
                repo_id="sample",
                repo=repo,
                requirements=[{"id": "REQ-A", "references": [{"law_text": "Law."}]}],
                hunt={"search_hints": {}},
                title="Discover",
                search=lambda *_args: [],
                source_id="cra-xml-vii",
                timestamp="2026-10-14T080000Z",
                assess_limit=0,
            )
            from discovery.jobs import read_job

            for _ in range(50):
                if read_job(root / "jobs", "discover-keep").get("status") != "running":
                    break
            self.assertEqual(path.read_bytes(), before)

    def test_added_finding_needs_a_file_and_a_rationale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            repo.mkdir()
            (repo / "NOTE.md").write_text("note\n", encoding="utf-8")
            add_finding(
                root,
                repo=repo,
                repo_id="sample",
                source_id="cra-xml-vii",
                timestamp="2026-10-14T080000Z",
                requirement_id="REQ-A",
                path="NOTE.md",
                rationale="I read this file.",
                known_ids=["REQ-A"],
            )
            entry = load_feedback(root, "sample", "cra-xml-vii", "2026-10-14T080000Z")["requirements"]["REQ-A"]["NOTE.md"]
            self.assertTrue(entry["added"])
            self.assertEqual(entry["human_why"], "I read this file.")
            self.assertNotIn("checks", entry)
            with self.assertRaises(ModelError):
                add_finding(
                    root,
                    repo=repo,
                    repo_id="sample",
                    source_id="cra-xml-vii",
                    timestamp="2026-10-14T080000Z",
                    requirement_id="REQ-A",
                    path="missing.md",
                    rationale="nope",
                    known_ids=["REQ-A"],
                )


if __name__ == "__main__":
    unittest.main()
