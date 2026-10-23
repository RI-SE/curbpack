#!/usr/bin/env python3
"""Real Ed25519 report: nested tampering and signer substitution must not verify."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.signing import generate_keypair
from checks.run import build_run_result
from claims.bind import build_claim
from review.compile import compile_report, record_decision, read_report_signature, sign_report
import tempfile
from _support import run

# Construct a real, schema-valid report from a Check run, not arbitrary JSON.
def specimen(private: bytes) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / 'evidence.md').write_text('Evidence\n', encoding='utf-8')
        claim = build_claim(
            claim_id='C-1', requirement_id='REQ-1', source='documents',
            args={'path':'evidence.md'},
            checks=[{'check':'exist', 'args':{'paths':['evidence.md']}}],
            description='This document is the checked evidence.')
        requirement = {
            'id':'REQ-1', 'pack_id':'house',
            'source':{'framework':'test','instrument':'test','identifier':'FIX-1',
                      'language':'en','url':'https://example.test'},
            'references':[{'nr':1,'locator':'1','law_text':'The documentation exists.'}],
        }
        run = build_run_result(repo, [claim], [{'id':'house','version':'0.1.0','digest':'abc'}])
        report = compile_report(run_result=run, requirements=[requirement], claims=[claim])
        report = record_decision(report, 'Evidence reviewed, not a compliance conclusion.')
        return sign_report(report, name='Reviewer A', private_key=private,
                           at='2026-10-23T10:00:00Z')

class ReviewSignature(unittest.TestCase):
    def setUp(self):
        self.private, self.public = generate_keypair()
        _, self.attacker_public = generate_keypair()
        self.report = specimen(self.private)
        self.trust = {'Reviewer A': self.public}
        self.assertTrue(read_report_signature(self.report, self.trust)['verifiable'])

    def test_mutated_check_result_is_unverifiable(self):
        forged = copy.deepcopy(self.report)
        forged['run_result']['claims'][0]['status'] = 'fail'
        forged['run_result']['claims'][0]['checks'][0]['status'] = 'fail'
        self.assertFalse(read_report_signature(forged, self.trust)['verifiable'])

    def test_mutated_human_decision_is_unverifiable(self):
        forged = copy.deepcopy(self.report)
        forged['decision'] = 'Fully compliant'
        self.assertFalse(read_report_signature(forged, self.trust)['verifiable'])

    def test_signer_and_trust_substitution_are_unverifiable(self):
        renamed = copy.deepcopy(self.report)
        renamed['signed']['name'] = 'Reviewer B'
        self.assertFalse(read_report_signature(renamed, {'Reviewer B': self.public})['verifiable'])
        self.assertFalse(read_report_signature(self.report, {'Reviewer A': self.attacker_public})['verifiable'])
        self.assertFalse(read_report_signature(self.report, {})['verifiable'])

    def test_corrupt_signature_is_unverifiable(self):
        forged = copy.deepcopy(self.report)
        forged['signed']['signature'] = 'not-base64!'
        self.assertFalse(read_report_signature(forged, self.trust)['verifiable'])

if __name__ == '__main__':
    run()
