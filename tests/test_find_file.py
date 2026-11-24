"""Find returns paths with the same file name and writes nothing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from studio.find_file import find_same_name


class FindSameNameTest(unittest.TestCase):
    def test_returns_matching_paths_and_skips_hidden_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "SECURITY.md").write_text("public\n", encoding="utf-8")
            (root / "notes").mkdir()
            (root / "notes" / "SECURITY.md").write_text("other\n", encoding="utf-8")
            (root / "README.md").write_text("no\n", encoding="utf-8")
            hidden = root / ".git" / "SECURITY.md"
            hidden.parent.mkdir()
            hidden.write_text("secret\n", encoding="utf-8")

            self.assertEqual(
                find_same_name(root, "docs/SECURITY.md"),
                ["docs/SECURITY.md", "notes/SECURITY.md"],
            )
            self.assertEqual(find_same_name(root, ""), [])
            self.assertEqual((root / "docs" / "SECURITY.md").read_text(encoding="utf-8"), "public\n")
