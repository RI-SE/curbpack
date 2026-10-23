#!/usr/bin/env python3
"""Unverified Git author fields and dirty snapshots must not imply a verified seal."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from checks.run import build_run_result
from claims.bind import build_claim
from review.compile import worktree_sentence
from review.gitseal import read_claim_signature
from common.store import save_claim
from _support import run

PACKS = [{'id':'house','version':'0.1.0','digest':'abc'}]

def git(repo, *args):
    return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()

class GitProvenance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        git(self.repo, 'init', '-q')
        (self.repo / 'docs').mkdir()
        (self.repo / 'docs' / 'evidence.md').write_text('first version\n', encoding='utf-8')
        self.claim = build_claim(claim_id='C-EVIDENCE', requirement_id='REQ-A', source='documents',
          args={'path':'docs/evidence.md'},checks=[{'check':'exist','args':{'paths':['docs/evidence.md']}}],
          description='The document is evidence.')
        save_claim(self.repo / 'claims', self.claim)
        git(self.repo, 'add', '-A')
        # Force an unsigned commit, independent of the developer's global signing settings.
        git(self.repo, '-c', 'commit.gpgsign=false', '-c', f'core.hooksPath={os.devnull}', '-c', 'user.name=Trusted Authority',
            '-c', 'user.email=authority@example.test', 'commit', '-q', '-m', 'unsigned test commit')

    def test_git_author_is_not_a_verified_signer(self):
        result = read_claim_signature(self.claim, {}, repo=self.repo, relative='claims/C-EVIDENCE.json')
        self.assertFalse(result['verifiable'])

    def test_dirty_worktree_is_labeled_not_commit_verified(self):
        (self.repo / 'docs' / 'evidence.md').write_text('changed after commit\n', encoding='utf-8')
        result = build_run_result(self.repo,[self.claim],PACKS)
        self.assertEqual(result['worktree'], 'dirty')
        self.assertIn('not verification of that commit',worktree_sentence(result))

if __name__ == '__main__':
    run()
