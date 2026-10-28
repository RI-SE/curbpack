"""The release tag and the refusal to publish a CI run that has not passed."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release" / "publish.py"
spec = importlib.util.spec_from_file_location("release_publish", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleasePublishTest(unittest.TestCase):
    def test_blank_tag_uses_the_run_date(self):
        self.assertEqual(
            module.choose_tag("", "2026-10-28T12:09:00Z", lambda _name: False),
            "v2026.10.28",
        )

    def test_blank_tag_steps_past_a_tag_that_exists(self):
        taken = {"v2026.10.28", "v2026.10.28.2"}
        self.assertEqual(
            module.choose_tag("", "2026-10-28T12:09:00Z", taken.__contains__),
            "v2026.10.28.3",
        )

    def test_typed_tag_is_kept(self):
        self.assertEqual(
            module.choose_tag("test-1", "2026-10-28T12:09:00Z", lambda _name: True),
            "test-1",
        )

    def test_typed_tag_rejects_spaces(self):
        with self.assertRaises(ValueError):
            module.choose_tag("test 1", "2026-10-28T12:09:00Z", lambda _name: False)

    def test_a_green_run_is_publishable(self):
        self.assertIsNone(module.latest_run_refusal({"conclusion": "success", "databaseId": 7}))

    def test_a_run_that_has_not_passed_is_refused(self):
        message = module.latest_run_refusal(
            {
                "databaseId": 7,
                "status": "in_progress",
                "conclusion": None,
                "url": "https://example.test/run/7",
            }
        )
        self.assertIn("7", message)
        self.assertIn("in_progress", message)
        self.assertIn("https://example.test/run/7", message)
