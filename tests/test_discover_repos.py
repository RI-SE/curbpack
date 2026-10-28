"""Product repos and a discover job over one working copy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from discovery.assess import assess_candidates
from discovery.jobs import read_job, request_abort, start_discover_job
from discovery.repos import add_repo, load_repos, save_repos


class RepoRegistryTest(unittest.TestCase):
    def test_add_repo_requires_a_directory_and_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            product = root / "product"
            product.mkdir()
            data = add_repo(root, {"repos": []}, name="Sample Product", path="product")
            save_repos(root, data)
            loaded = load_repos(root)
            self.assertEqual(loaded["repos"][0]["id"], "sample-product")
            self.assertEqual(loaded["repos"][0]["path"], "product")
            with self.assertRaises(ModelError):
                add_repo(root, loaded, name="Sample Product", path="product")
            with self.assertRaises(ModelError):
                add_repo(root, {"repos": []}, name="Missing", path="no-such-dir")


class DiscoverJobTest(unittest.TestCase):
    def test_abort_stops_before_the_next_requirement_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            repo.mkdir()
            (repo / "note.md").write_text("untouched\n", encoding="utf-8")
            before = (repo / "note.md").read_bytes()
            data = add_repo(root, {"repos": []}, name="sample-product", path=str(repo))
            save_repos(root, data)
            calls = []

            def search(_repo, requirement, _hunt):
                calls.append(requirement["id"])
                request_abort(root / "jobs", "discover-abort")
                return [{"path": "docs/a.md", "matched_by": "path_hint", "excerpt": "a"}]

            start_discover_job(
                root / "jobs",
                job_id="discover-abort",
                workspace=root,
                repo_id="sample-product",
                repo=repo,
                requirements=[
                    {"id": "REQ-A", "references": [{"locator": "VII.3"}]},
                    {"id": "REQ-B", "references": [{"locator": "VII.4"}]},
                ],
                hunt={"search_hints": {}},
                title="Discover — sample-product / CRA Annex VII VII",
                search=search,
            )
            job = _wait(root / "jobs", "discover-abort")
            self.assertEqual(calls, ["REQ-A"])
            self.assertEqual(job["status"], "aborted")
            log = "\n".join(job["log_tail"])
            self.assertIn("=== REQ-A VII.3 ===", log)
            self.assertNotIn("REQ-B", log)
            self.assertEqual((repo / "note.md").read_bytes(), before)
            self.assertFalse((repo / "claims").exists())


class DiscoverAssessmentJobTest(unittest.TestCase):
    def test_scores_both_requirements_and_leaves_requirement_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, requirement_file, before = _repo(root)
            calls = []

            def complete(prompt, _settings):
                calls.append(prompt)
                return '{"score": 0.7, "rank": "Medium", "why": "Names the risk.", "excerpt": "risk"}'

            _start(root, repo, _search_two, complete=complete, assess_limit=5)
            job = _wait(root / "jobs", "discover-score")
            self.assertEqual(job["status"], "done")
            by_id = {row["requirement_id"]: row for row in job["results"]}
            self.assertEqual(by_id["REQ-A"]["candidates"][0]["score"], 0.7)
            self.assertEqual(by_id["REQ-B"]["candidates"][0]["rank"], "Medium")
            self.assertIn("REQ-A", calls[0])
            self.assertEqual(requirement_file.read_bytes(), before)
            self.assertFalse((repo / "claims").exists())

    def test_endpoint_error_keeps_paths_without_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _requirement_file, _before = _repo(root)

            def complete(_prompt, _settings):
                raise ModelError("produce", "endpoint", "a reachable model server")

            _start(root, repo, _search_two, complete=complete, job_id="discover-down")
            job = _wait(root / "jobs", "discover-down")
            self.assertEqual(job["status"], "done")
            for row in job["results"]:
                candidate = row["candidates"][0]
                self.assertEqual(candidate["matched_by"], "path_hint")
                self.assertNotIn("score", candidate)
                self.assertEqual(candidate["assessment_state"], "failed")

    def test_cap_keeps_unscored_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _requirement_file, _before = _repo(root)
            names = [f"docs/n{i}.md" for i in range(6)]
            for name in names:
                (repo / name).write_text("risk note\n", encoding="utf-8")

            def search(_repo, _requirement, _hunt):
                if _requirement["id"] != "REQ-A":
                    return []
                return [{"path": name, "matched_by": "path_hint", "excerpt": "risk"} for name in names]

            calls = []

            def complete(_prompt, _settings):
                calls.append(1)
                return '{"score": 0.2, "rank": "Low", "why": "Short.", "excerpt": ""}'

            _start(root, repo, search, complete=complete, assess_limit=2, job_id="discover-cap")
            job = _wait(root / "jobs", "discover-cap")
            candidates = job["results"][0]["candidates"]
            self.assertEqual(len(candidates), 6)
            self.assertEqual(len(calls), 2)
            self.assertEqual(candidates[2]["assessment_state"], "not_assessed")
            self.assertEqual(candidates[2]["assessment_skip"], "cap")

    def test_abort_keeps_the_score_already_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _requirement_file, _before = _repo(root)
            seen = []

            def complete(_prompt, _settings):
                seen.append(1)
                if len(seen) == 1:
                    request_abort(root / "jobs", "discover-stop")
                return '{"score": 0.9, "rank": "High", "why": "Clear.", "excerpt": "risk"}'

            _start(root, repo, _search_two, complete=complete, job_id="discover-stop")
            job = _wait(root / "jobs", "discover-stop")
            self.assertEqual(job["status"], "aborted")
            self.assertEqual(job["results"][0]["candidates"][0]["score"], 0.9)
            self.assertEqual(len(seen), 1)

    def test_second_job_reuses_an_unchanged_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _requirement_file, _before = _repo(root)
            calls = []

            def complete(_prompt, _settings):
                calls.append(1)
                return '{"score": 0.9, "rank": "High", "why": "Clear.", "excerpt": "risk"}'

            _start(root, repo, _search_one, complete=complete, job_id="discover-first")
            self.assertEqual(_wait(root / "jobs", "discover-first")["status"], "done")
            _start(root, repo, _search_one, complete=complete, job_id="discover-second")
            job = _wait(root / "jobs", "discover-second")
            self.assertEqual(job["results"][0]["candidates"][0]["assessment_state"], "reused")
            self.assertEqual(len(calls), 1)

    def test_score_zero_is_omitted_and_not_scored_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _requirement_file, _before = _repo(root)
            (repo / "docs" / "mom.md").write_text("buy milk\n", encoding="utf-8")

            def search(_repo, requirement, _hunt):
                if requirement["id"] != "REQ-A":
                    return []
                return [
                    {"path": "docs/mom.md", "matched_by": "path_hint", "excerpt": ""},
                    {"path": "docs/a.md", "matched_by": "path_hint", "excerpt": "risk"},
                ]

            calls = []

            def complete(prompt, _settings):
                calls.append(prompt)
                if "mom.md" in prompt:
                    return '{"score": 0, "rank": "None", "why": "A shopping list.", "excerpt": ""}'
                return '{"score": 0.7, "rank": "Medium", "why": "Names the risk.", "excerpt": "risk"}'

            _start(root, repo, search, complete=complete, job_id="discover-zero")
            job = _wait(root / "jobs", "discover-zero")
            self.assertEqual([item["path"] for item in job["results"][0]["candidates"]], ["docs/a.md"])
            self.assertEqual(job["results"][0]["dismissed"][0]["path"], "docs/mom.md")
            self.assertEqual(len(calls), 2)
            _start(root, repo, search, complete=complete, job_id="discover-zero-again")
            again = _wait(root / "jobs", "discover-zero-again")
            self.assertEqual(len(calls), 2)
            self.assertEqual([item["path"] for item in again["results"][0]["candidates"]], ["docs/a.md"])


def _repo(root: Path):
    repo = root / "product"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "a.md").write_text("risk alpha\n", encoding="utf-8")
    (repo / "docs" / "b.md").write_text("risk beta\n", encoding="utf-8")
    requirement_file = root / "REQ-A.json"
    requirement_file.write_text('{"id":"REQ-A"}\n', encoding="utf-8")
    before = requirement_file.read_bytes()
    add_repo(root, {"repos": []}, name="sample-product", path=str(repo))
    return repo, requirement_file, before


def _requirements():
    return [
        {"id": "REQ-A", "references": [{"locator": "VII.3", "law_text": "State the risk."}]},
        {"id": "REQ-B", "references": [{"locator": "VII.4", "law_text": "State the test."}]},
    ]


def _search_two(_repo, requirement, _hunt):
    path = "docs/a.md" if requirement["id"] == "REQ-A" else "docs/b.md"
    return [{"path": path, "matched_by": "path_hint", "excerpt": "risk"}]


def _search_one(_repo, requirement, _hunt):
    if requirement["id"] != "REQ-A":
        return []
    return [{"path": "docs/a.md", "matched_by": "path_hint", "excerpt": "risk"}]


def _start(root, repo, search, *, complete, job_id="discover-score", assess_limit=5):
    def assess(repo_path, requirement, candidates, **kwargs):
        kwargs["complete"] = complete
        return assess_candidates(repo_path, requirement, candidates, **kwargs)

    start_discover_job(
        root / "jobs",
        job_id=job_id,
        workspace=root,
        repo_id="sample-product",
        repo=repo,
        requirements=_requirements(),
        hunt={"search_hints": {}},
        title="Discover",
        search=search,
        source_id="cra-xml-vii",
        timestamp="2026-10-14T080000Z",
        assess_limit=assess_limit,
        assess=assess,
    )


def _wait(jobs: Path, job_id: str) -> dict:
    import time

    for _ in range(100):
        job = read_job(jobs, job_id)
        if job.get("status") != "running":
            return job
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish")


if __name__ == "__main__":
    unittest.main()
