"""Atomic JSON writes leave no temporary file behind."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common.jsonio import read_json, write_json


class WriteJsonTest(unittest.TestCase):
    def test_replace_leaves_no_temporary_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "llm.json"
            write_json(path, {"llm": [{"stage": "interpret"}]})
            self.assertEqual(read_json(path), {"llm": [{"stage": "interpret"}]})
            leftovers = list(Path(tmp).glob(".llm.json.*.tmp"))
            self.assertEqual(leftovers, [])

    def test_read_waits_out_a_windows_permission_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "discover-keep.json"
            write_json(path, {"status": "done"})
            real = Path.read_text
            calls = {"n": 0}

            def flaky(self, *args, **kwargs):
                if self == path:
                    calls["n"] += 1
                    if calls["n"] == 1:
                        raise PermissionError(13, "Permission denied", str(self))
                return real(self, *args, **kwargs)

            with patch.object(Path, "read_text", flaky):
                self.assertEqual(read_json(path), {"status": "done"})
            self.assertEqual(calls["n"], 2)
