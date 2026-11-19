"""One overwriteable extract slot per pack and section."""

import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from studio.pack.section_extract import (
    begin_section_extract,
    commit_section_extract,
    drop_section_extract,
    read_section_extract,
    section_extract_directory,
)


class SectionExtractSlotTest(unittest.TestCase):
    def test_a_later_extract_replaces_the_slot_and_drop_removes_only_that_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            incoming = begin_section_extract(repo, "cra", "VII")
            (incoming / "pack.json").write_text("{}\n", encoding="utf-8")
            (incoming / "first.json").write_text("{}\n", encoding="utf-8")
            final = commit_section_extract(incoming, "2026-11-19T140000Z")
            self.assertEqual(final, section_extract_directory(repo, "cra", "VII"))
            self.assertEqual(read_section_extract(repo, "cra", "VII")[1], "2026-11-19T140000Z")
            self.assertTrue((final / "first.json").is_file())

            again = begin_section_extract(repo, "cra", "VII")
            self.assertTrue((final / "first.json").is_file())
            (again / "pack.json").write_text("{}\n", encoding="utf-8")
            (again / "second.json").write_text("{}\n", encoding="utf-8")
            replaced = commit_section_extract(again, "2026-11-19T150000Z")
            self.assertEqual(replaced, final)
            self.assertFalse((replaced / "first.json").exists())
            self.assertTrue((replaced / "second.json").is_file())
            self.assertEqual(read_section_extract(repo, "cra", "VII")[1], "2026-11-19T150000Z")

            drop_section_extract(repo, "cra", "VII")
            self.assertIsNone(read_section_extract(repo, "cra", "VII"))
            self.assertFalse(final.exists())

    def test_a_section_id_cannot_escape_the_extract_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with self.assertRaises(ModelError):
                section_extract_directory(repo, "cra", "../outside")
            with self.assertRaises(ModelError):
                section_extract_directory(repo, "..", "VII")
