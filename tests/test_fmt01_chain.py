"""FMT-01 chain. Production is 0 to 1. A second step exists only in this test."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from common.jsonio import write_json
from common.store import PRODUCTION_FORMAT_STEPS, apply_format_chain, upgrade_format_0_to_1


def _step(source: int, destination: int, calls: list[int]):
    def upgrade(document: dict) -> dict:
        calls.append(document["format_version"])
        upgraded = dict(document)
        upgraded["format_version"] = destination
        upgraded["steps"] = list(document.get("steps") or []) + [f"{source}->{destination}"]
        return upgraded

    return upgrade


class FormatChainTest(unittest.TestCase):
    def test_a_document_at_3_runs_both_steps_and_returns_version_5(self):
        calls: list[int] = []
        steps = (
            (3, 4, _step(3, 4, calls)),
            (4, 5, _step(4, 5, calls)),
        )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "document.json"
        document = {"format_version": 3, "name": "kept"}
        write_json(path, document)
        before = path.read_bytes()
        upgraded = apply_format_chain(document, steps)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(document, {"format_version": 3, "name": "kept"})
        self.assertEqual(calls, [3, 4])
        self.assertEqual(upgraded["format_version"], 5)
        self.assertEqual(upgraded["steps"], ["3->4", "4->5"])
        self.assertEqual(upgraded["name"], "kept")

    def test_a_document_below_the_chain_start_is_rejected_and_the_file_stays(self):
        calls: list[int] = []
        steps = (
            (3, 4, _step(3, 4, calls)),
            (4, 5, _step(4, 5, calls)),
        )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "document.json"
        document = {"format_version": 1, "name": "kept"}
        write_json(path, document)
        before = path.read_bytes()
        with self.assertRaises(ModelError) as caught:
            apply_format_chain(document, steps)
        self.assertEqual(caught.exception.field, "format_version")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(document["format_version"], 1)
        self.assertEqual(calls, [])

    def test_a_missing_step_is_rejected_and_not_jumped(self):
        calls: list[int] = []
        steps = (
            (3, 4, _step(3, 4, calls)),
            (5, 6, _step(5, 6, calls)),
        )
        document = {"format_version": 3, "name": "kept"}
        with self.assertRaises(ModelError) as caught:
            apply_format_chain(document, steps)
        self.assertEqual(caught.exception.field, "format_version")
        self.assertEqual(document, {"format_version": 3, "name": "kept"})
        self.assertEqual(calls, [])

    def test_a_version_above_the_chain_is_rejected_and_the_file_stays(self):
        calls: list[int] = []
        steps = (
            (3, 4, _step(3, 4, calls)),
            (4, 5, _step(4, 5, calls)),
        )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "document.json"
        document = {"format_version": 6, "name": "kept"}
        write_json(path, document)
        before = path.read_bytes()
        with self.assertRaises(ModelError) as caught:
            apply_format_chain(document, steps)
        self.assertEqual(caught.exception.field, "format_version")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(document, {"format_version": 6, "name": "kept"})
        self.assertEqual(calls, [])

    def test_a_document_below_the_floor_is_rejected(self):
        document = {"name": "old"}
        with self.assertRaises(ModelError) as caught:
            apply_format_chain(document, ((0, 1, upgrade_format_0_to_1),), floor=1)
        self.assertEqual(caught.exception.field, "format_version")
        self.assertNotIn("format_version", document)

    def test_production_registers_only_the_step_from_0_to_1(self):
        self.assertEqual(PRODUCTION_FORMAT_STEPS, ((0, 1, upgrade_format_0_to_1),))
