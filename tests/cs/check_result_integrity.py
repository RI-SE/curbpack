#!/usr/bin/env python3
"""Claim/check consistency and fail-closed behavior at the Check -> Review seam."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from checks.run import build_run_result, process_exit_code
from claims.bind import build_claim
from common.errors import ModelError
from review.compile import compile_report
from _support import run

REQ = {'id':'REQ-A', 'pack_id':'house',
       'source':{'framework':'test','instrument':'test','identifier':'FIX-1','language':'en','url':'https://example.test'},
       'references':[{'nr':1,'locator':'1','law_text':'The product documents the risk.'}]}
PACKS = [{'id':'house','version':'0.1.0','digest':'abc'}]

def claim(cid, path):
    return build_claim(claim_id=cid, requirement_id='REQ-A', source='documents', args={'path':path},
        checks=[{'check':'exist','args':{'paths':[path]}}],
        description='Evidence is present at the identified path.')

class CheckResultIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        (self.repo / 'exists.md').write_text('real evidence\n', encoding='utf-8')
        self.good = claim('C-GOOD','exists.md')
        self.missing = claim('C-MISSING','missing.md')

    def test_missing_evidence_overrides_other_passing_checks(self):
        result = build_run_result(self.repo, [self.good, self.missing], PACKS)
        self.assertEqual([row['status'] for row in result['claims']], ['pass','fail'])
        self.assertNotEqual(process_exit_code(result), 0)

    def test_skip_has_reason_and_cannot_make_run_green(self):
        result = build_run_result(self.repo, [self.good, self.missing], PACKS,
                                  skip={'C-MISSING':'reviewer must verify external document'})
        self.assertEqual(result['claims'][1]['status'], 'skipped')
        self.assertEqual(result['claims'][1]['checks'][0]['detail'], 'reviewer must verify external document')
        self.assertNotEqual(process_exit_code(result), 0)
        with self.assertRaises(ModelError):
            build_run_result(self.repo, [self.missing], PACKS, skip={'C-MISSING':'  '})

    def test_changed_claim_digest_is_rejected_by_compile(self):
        result = build_run_result(self.repo, [self.good], PACKS)
        forged = copy.deepcopy(result)
        forged['claims'][0]['digest'] = '0' * 64
        with self.assertRaises(ModelError):
            compile_report(run_result=forged, requirements=[REQ], claims=[self.good])

    def test_changed_check_arguments_are_rejected_by_compile(self):
        result = build_run_result(self.repo, [self.good], PACKS)
        forged = copy.deepcopy(result)
        forged['claims'][0]['checks'][0]['args']['paths'] = ['another.md']
        with self.assertRaises(ModelError):
            compile_report(run_result=forged, requirements=[REQ], claims=[self.good])

if __name__ == '__main__':
    run()
