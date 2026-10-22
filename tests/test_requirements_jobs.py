"""Extract jobs record progress outside the Pack directory."""

from __future__ import annotations

import json
import re
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from common.errors import ModelError
from common.jsonio import write_json
from requirements.extract.adapter import ADAPTERS
from requirements.extract.pipeline import draft_pack
from requirements.workspace import create_extraction_copy


def _proposals() -> list[dict]:
    return [
        {
            "locus": "3",
            "id": "CRA-ANNEX-VII-RISK",
            "locator": "VII.3",
            "discovery_hints": {
                "concepts": ["risk assessment"],
                "path_hints": ["*risk*assessment*", "*THREAT*"],
                "sources": [{"source": "documents"}],
            },
        },
        # Pipeline fixture only. Not a CRA id convention.
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
    ]


def _bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _wait(read_job, jobs: Path, job_id: str) -> dict:
    deadline = time.time() + 5
    last = None
    while time.time() < deadline:
        last = read_job(jobs, job_id)
        if last["status"] in {"done", "failed", "aborted"}:
            return last
        time.sleep(0.01)
    raise AssertionError(last)


class ExtractJobTest(unittest.TestCase):
    def setUp(self):
        from requirements.jobs import read_job, request_abort, start_extract_job

        self.read_job = read_job
        self.request_abort = request_abort
        self.start_extract_job = start_extract_job
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.jobs = self.root / "jobs"
        self.older = create_extraction_copy(
            self.root, "cra-baseline", draft_pack(), at="2026-10-13T080000Z"
        )
        self.before = _bytes(self.older)

    def test_done_job_writes_a_new_copy_and_moves_progress(self):
        seen: list[float] = []
        from requirements import jobs as jobs_module

        real = jobs_module.extract_section

        def spy(*args, **kwargs):
            seen.append(self.read_job(self.jobs, "done-1")["progress"])
            return real(*args, **kwargs)

        with patch("requirements.jobs.extract_section", spy):
            self.start_extract_job(
                self.jobs,
                job_id="done-1",
                root=self.root,
                adapter_dir=ADAPTERS / "cra",
                section_id="VII",
                proposals=_proposals(),
                pack=draft_pack(),
            )
            job = _wait(self.read_job, self.jobs, "done-1")
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["progress"], 1.0)
        self.assertLess(seen[0], 1.0)
        self.assertLessEqual(len(job["log_tail"]), 200)
        names = [
            path.name
            for path in (self.root / "cra-baseline").iterdir()
            if path.is_dir() and not path.name.endswith(".work")
        ]
        self.assertIn("2026-10-13T080000Z", names)
        self.assertGreater(len(names), 1)
        self.assertEqual(_bytes(self.older), self.before)
        self.assertFalse((self.root / "published").exists())
        self.assertFalse((self.older / "done-1.json").exists())

    def test_done_job_keeps_the_selected_copy(self):
        from requirements.workspace import mark_selected, read_selection

        mark_selected(self.root, "cra-baseline", self.older.name)
        self.start_extract_job(
            self.jobs,
            job_id="review-1",
            root=self.root,
            adapter_dir=ADAPTERS / "cra",
            section_id="VII",
            proposals=_proposals(),
            pack=draft_pack(),
        )
        job = _wait(self.read_job, self.jobs, "review-1")
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["base_timestamp"], self.older.name)
        self.assertNotEqual(job["copy_timestamp"], self.older.name)
        self.assertEqual(read_selection(self.root)["timestamp"], self.older.name)
        self.assertEqual(_bytes(self.older), self.before)

    def test_stub_adapter_fails_without_publishing(self):
        self.start_extract_job(
            self.jobs,
            job_id="fail-1",
            root=self.root,
            adapter_dir=ADAPTERS / "medtech",
            section_id="VII",
            proposals=_proposals(),
            pack=draft_pack(),
        )
        job = _wait(self.read_job, self.jobs, "fail-1")
        self.assertEqual(job["status"], "failed")
        self.assertIn("error", job)
        self.assertTrue(job["error"])
        self.assertEqual(_bytes(self.older), self.before)
        self.assertFalse((self.root / "published").exists())
        names = [
            path.name
            for path in (self.root / "cra-baseline").iterdir()
            if path.is_dir() and not path.name.endswith(".work")
        ]
        self.assertEqual(names, ["2026-10-13T080000Z"])

    def test_abort_stays_aborted_and_keeps_the_older_copy(self):
        started = threading.Event()

        def hold(*_args, **_kwargs):
            started.set()
            deadline = time.time() + 2
            while time.time() < deadline:
                if self.read_job(self.jobs, "abort-1")["status"] == "aborted":
                    raise ModelError("job", "status", "aborted by user")
                time.sleep(0.01)
            raise AssertionError("abort was not requested")

        with patch("requirements.jobs.extract_section", hold):
            self.start_extract_job(
                self.jobs,
                job_id="abort-1",
                root=self.root,
                adapter_dir=ADAPTERS / "cra",
                section_id="VII",
                proposals=_proposals(),
                pack=draft_pack(),
            )
            self.assertTrue(started.wait(2))
            self.request_abort(self.jobs, "abort-1")
            job = _wait(self.read_job, self.jobs, "abort-1")
            time.sleep(0.05)
            job = self.read_job(self.jobs, "abort-1")
        self.assertEqual(job["status"], "aborted")
        self.assertEqual(job["error"], "aborted by user")
        self.assertEqual(job["log_tail"][-1], "aborted by user")
        self.assertEqual(_bytes(self.older), self.before)
        self.assertFalse((self.root / "published").exists())

    def test_abort_keeps_the_last_200_log_lines(self):
        write_json(
            self.jobs / "trim.json",
            {
                "job_id": "trim",
                "status": "running",
                "stage": "extract",
                "progress": 0.4,
                "log_tail": [f"line {index}" for index in range(200)],
            },
        )
        self.request_abort(self.jobs, "trim")
        job = self.read_job(self.jobs, "trim")
        self.assertEqual(job["status"], "aborted")
        self.assertEqual(len(job["log_tail"]), 200)
        self.assertEqual(job["log_tail"][0], "line 1")
        self.assertEqual(job["log_tail"][-1], "aborted by user")

    def test_omitted_proposals_run_producers_and_write_llm_notes(self):
        self.start_extract_job(
            self.jobs,
            job_id="model-1",
            root=self.root,
            adapter_dir=ADAPTERS / "cra",
            section_id="VII",
            pack=draft_pack(),
            complete=_fake_model_complete,
        )
        job = _wait(self.read_job, self.jobs, "model-1")
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(_bytes(self.older), self.before)
        work_dirs = [
            path
            for path in (self.root / "cra-baseline").iterdir()
            if path.is_dir() and path.name.endswith(".work")
        ]
        self.assertTrue(work_dirs)
        llm = json.loads((work_dirs[0] / "llm.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(llm["llm"]), 2)
        self.assertEqual({note["stage"] for note in llm["llm"]}, {"interpret", "discovery_hints"})


def _fake_model_complete(prompt: str, settings: dict) -> str:
    """Test double covering every locus. FIXTURE ids are not a CRA naming convention."""
    match = re.search(r"---\n(\[.*\])\n---", prompt, re.S)
    if match is None:
        raise AssertionError("prompt missing provisions JSON")
    provisions = json.loads(match.group(1))
    if settings["stage"] == "interpret":
        rows = []
        for item in provisions:
            locus = item["locus"]
            if locus == "3":
                rows.append({"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3"})
            else:
                safe = locus.replace("(", "").replace(")", "")
                rows.append(
                    {"locus": locus, "id": f"FIXTURE-VII-{safe}", "locator": f"VII.{locus}"}
                )
        return json.dumps({"provisions": rows})
    return json.dumps(
        {
            "provisions": [
                {"locus": item["locus"], "discovery_hints": {"concepts": [item["locus"]]}}
                for item in provisions
            ]
        }
    )
