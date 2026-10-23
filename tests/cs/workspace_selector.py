#!/usr/bin/env python3
"""A pack id has to be one directory name, so selection stays inside the workspace."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.errors import ModelError
from common.store import save_pack
from requirements.workspace import select_working_copy, select_published_pack
from _support import run

class WorkspaceSelector(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.workspace = self.base / 'workspace'
        self.workspace.mkdir()

    def test_normal_working_copy_selection_still_works(self):
        path = self.workspace / 'house' / '2026-10-23T120000Z'
        save_pack(path, {'id':'house', 'version':'0.1.0'})
        self.assertEqual(select_working_copy(self.workspace, 'house', path.name), path)

    def test_pack_id_cannot_select_working_copy_outside_workspace(self):
        stamp = '2026-10-23T120000Z'
        # Outside tree is a controlled temp fixture, never real user data.
        save_pack(self.base / 'outside' / stamp, {'id':'../outside', 'version':'0.1.0'})
        with self.assertRaises(ModelError):
            select_working_copy(self.workspace, '../outside', stamp)

    def test_pack_id_cannot_select_published_pack_outside_published_root(self):
        # Traversal from workspace/published to sibling temp directory.
        (self.workspace / 'published').mkdir()
        save_pack(self.workspace / 'external' / '1.0.0', {'id':'../external', 'version':'1.0.0'})
        with self.assertRaises(ModelError):
            select_published_pack(self.workspace, '../external', '1.0.0')

if __name__ == '__main__':
    run()
