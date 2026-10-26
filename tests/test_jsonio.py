"""Atomic JSON writes leave no temporary file behind."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.jsonio import read_json, write_json


class WriteJsonTest(unittest.TestCase):
    def test_replace_leaves_no_temporary_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "llm.json"
            write_json(path, {"llm": [{"stage": "interpret"}]})
            self.assertEqual(read_json(path), {"llm": [{"stage": "interpret"}]})
            leftovers = list(Path(tmp).glob(".llm.json.*.tmp"))
            self.assertEqual(leftovers, [])
