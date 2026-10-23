#!/usr/bin/env python3
"""Ensure file evidence and discovery cannot read outside the selected repository."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from checks.filecheck import run_contents, run_exist
from common.errors import ModelError
from discovery.search import iter_markdown, read_source_text
from _support import run

class PathBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        (self.repo / 'docs').mkdir()
        (self.repo / 'docs' / 'allowed.md').write_text('Approved proof\n', encoding='utf-8')
        self.secret = self.base / 'private.md'
        self.secret.write_text('OUTSIDE_SECRET\n', encoding='utf-8')

    def _reject(self, path):
        with self.assertRaises(ModelError):
            run_exist(self.repo, {'paths': [path]})
        with self.assertRaises(ModelError):
            run_contents(self.repo, {'path': path, 'probes': [{'kind': 'headers', 'headers': ['OUTSIDE_SECRET']}]})
        with self.assertRaises(ModelError):
            read_source_text(self.repo, path)

    def test_control_inside_repo_still_works(self):
        self.assertEqual(run_exist(self.repo, {'paths':['docs/allowed.md']}), {'status':'pass'})
        self.assertIn('Approved proof', read_source_text(self.repo, 'docs/allowed.md'))

    def test_traversal_and_absolute_path_cannot_escape(self):
        self._reject('../private.md')
        self._reject(str(self.secret))
        self._reject('docs/../../private.md')
        # Discovery rejects Windows-style separators even on POSIX.
        with self.assertRaises(ModelError):
            read_source_text(self.repo, 'docs\\..\\..\\private.md')

    def test_symlink_escape_is_rejected_in_checks_and_discovery(self):
        link = self.repo / 'docs' / 'link.md'
        try:
            link.symlink_to(self.secret)
        except (OSError, NotImplementedError) as exc:
            self.fail(f'symlink boundary was not exercised on this filesystem: {exc}')
        self._reject('docs/link.md')
        # The discovery walk must not surface external files either.
        self.assertNotIn(self.secret.resolve(), iter_markdown(self.repo, []))

if __name__ == '__main__':
    run()
