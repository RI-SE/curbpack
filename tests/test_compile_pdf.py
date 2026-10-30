"""REV-04 / REV-05: a saved historical report becomes a readable monochrome PDF."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from common.canonical import version_digest
from review.compile import validate_report

ROOT = Path(__file__).resolve().parents[1]


def report_fixture(*, long=False):
    passage = 'Åtgärder för säkerhet: läs och granska <källa> & underlag.'
    requirement = {
        'id': 'REQ-A', 'pack_id': 'house',
        'source': {'framework': 'test', 'instrument': 'Security policy',
                   'identifier': 'POL-1', 'language': 'sv', 'url': 'https://example.test/policy'},
        'references': [{'nr': 1, 'locator': '2.1', 'law_text': (passage + ' ') * (230 if long else 1)}],
        'strength': 'MUST', 'remediation_hint': 'Document the security process.',
    }
    claims, rows = [], []
    for index, status in enumerate(('pass', 'fail', 'skipped')):
        paths = [f'docs/{"long-path-" * (18 if long else 1)}{n}-säkerhet.md' for n in range(9 if long else 2)]
        claim = {
            'id': f'claim-{index}', 'requirement_id': 'REQ-A',
            'source': 'documents', 'args': {'path': paths[0]},
            'description': f'Reviewed evidence {index}: <b>literal text</b> & rationale.',
            'checks': [{'check': 'exist', 'args': {'paths': paths}}],
        }
        check = dict(claim['checks'][0], index=0, status=status)
        if status != 'pass':
            check['detail'] = 'Evidence missing' if status == 'fail' else 'Deferred by reviewer'
        claims.append(claim)
        rows.append({'id': claim['id'], 'digest': version_digest(claim), 'status': status, 'checks': [check]})
    return {
        'run_result': {'commit': 'a' * 40, 'worktree': 'dirty', 'tool': 'curbcheck',
                       'tool_version': '0.0.1a', 'packs': [{'id': 'house', 'version': '1.0', 'digest': 'b' * 64}],
                       'claims': rows},
        'requirements': [requirement], 'claims': claims,
        'appendix': [{'id': claim['id'], 'requirement_id': 'REQ-A', 'reason': 'No trusted certificate available.'} for claim in claims],
    }


class CompilePdfTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder / 'report.json'
        self.target = self.folder / 'review.pdf'

    def save(self, report):
        validate_report(report)
        self.source.write_text(json.dumps(report, ensure_ascii=False), encoding='utf-8')

    def run_cli(self, *extra):
        return subprocess.run([sys.executable, str(ROOT / 'compile-pdf.py'), '--report', str(self.source),
                               '--out', str(self.target), *extra], capture_output=True, text=True)

    def text(self):
        return '\n'.join(page.extract_text() for page in PdfReader(self.target).pages)

    def test_management_summary_precedes_technical_appendix(self):
        report = report_fixture()
        self.save(report)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = self.text()
        self.assertIn('Appendix A — Run and source records', text)
        main, technical = text.split('Appendix A — Run and source records', 1)
        for expected in ('Management summary', 'Evidence assertions', 'Automated checks',
                         'What needs attention', 'Checks need follow-up',
                         'Some checks were not performed', 'No reviewer decision recorded',
                         'uncommitted changes', 'B.1', 'Recorded assertion'):
            self.assertIn(expected, main)
        for technical_value in ('Product commit', 'worktree',
                                'digest', 'Check arguments', 'https://', 'REQ-A',
                                'claim-0', 'No trusted certificate available.',
                                report['run_result']['commit'], version_digest(report)):
            self.assertNotIn(technical_value, main)
        self.assertIn('Reason reported by the checker', main)
        self.assertIn('Evidence missing', main)
        self.assertIn('Changes since the run', main)
        self.assertIn('Signatures are not independently verified', main)
        self.assertIn('Appendix B', technical)
        self.assertIn('Appendix C', technical)
        self.assertIn('No trusted certificate available.', technical)
        reader = PdfReader(self.target)
        appendix_page = next(page for page in reader.pages if 'Appendix A — Run and source records' in page.extract_text())
        self.assertTrue(appendix_page.extract_text().startswith('Curbpack Studio'))
        self.assertNotIn('Management summary', appendix_page.extract_text())

    def test_all_pass_summary_still_requires_human_review(self):
        report = report_fixture()
        for row in report['run_result']['claims']:
            row['status'] = 'pass'
            for check in row['checks']:
                check['status'] = 'pass'
                check.pop('detail', None)
        report['decision'] = 'A named owner must review the underlying evidence.'
        self.save(report)
        self.assertEqual(self.run_cli().returncode, 0)
        main = self.text().split('Appendix A — Run and source records', 1)[0]
        self.assertIn('All recorded checks passed', main)
        self.assertIn('Human review', main)
        self.assertIn(report['decision'], main)
        self.assertNotIn('Checks need follow-up', main)

    def test_cli_creates_readable_pdf_without_changing_report(self):
        self.save(report_fixture())
        before = self.source.read_bytes()
        result = self.run_cli()
        self.assertTrue(self.target.is_file(), result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.source.read_bytes(), before)
        text = self.text()
        for expected in ('Review report', 'curbcheck', '0.0.1a', 'dirty', 'house', '1.0',
                         'Claims: 3', 'Checks: 3', 'PASS 1', 'FAIL 1', 'SKIPPED 1',
                         'Prepares evidence for human review — not a conformity assessment.',
                         "not verification of that commit", 'REQ-A', 'Security policy', '2.1',
                         'Åtgärder', '<b>literal text</b>', 'claim-0', 'claim-1', 'claim-2',
                         'exist', 'Evidence missing', 'Deferred by reviewer',
                         'No trusted certificate available.', 'No reviewer decision recorded'):
            self.assertIn(expected, text)
        # Rendering may wrap, but the full recorded arguments and digests remain readable.
        self.assertIn('docs/long-path-0-säkerhet.md', text)
        for claim in report_fixture()['claims']:
            self.assertIn(version_digest(claim), text.replace('\n', ''))
        self.assertFalse(any('/Annots' in page for page in PdfReader(self.target).pages))

    def test_long_unicode_report_wraps_across_numbered_pages(self):
        self.save(report_fixture(long=True))
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        reader = PdfReader(self.target)
        self.assertGreater(len(reader.pages), 2)
        text = self.text()
        for n, page in enumerate(reader.pages, 1):
            self.assertIn(f'Page {n}', page.extract_text())
        self.assertIn('säkerhet', text)
        self.assertIn('claim-2', text)
        self.assertIn('Deferred by reviewer', text)

    def test_decision_and_recorded_signatures_are_not_claimed_verified(self):
        report = report_fixture()
        report['decision'] = 'Request more evidence before acceptance.'
        report['signed'] = {'name': 'Åsa Reviewer', 'at': '2026-10-29T15:00:00Z', 'signature': 'AA=='}
        self.save(report)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = self.text()
        for expected in ('Åsa Reviewer', report['decision'], '2026-10-29T15:00:00Z',
                         'Verification not performed', 'does not sign the PDF bytes', version_digest(report)):
            self.assertIn(expected, text.replace('\n', '') if expected == version_digest(report) else text)

    def test_existing_pdf_and_source_alias_are_preserved(self):
        self.save(report_fixture())
        self.target.write_bytes(b'previous signed or shared output')
        before = self.source.read_bytes()
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertEqual(self.target.read_bytes(), b'previous signed or shared output')
        self.target = self.source
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertEqual(self.source.read_bytes(), before)

    def test_invalid_or_missing_source_and_missing_parent_write_nothing(self):
        for value in (None, 'not JSON', '{}'):
            with self.subTest(value=value):
                if value is None:
                    self.source.unlink(missing_ok=True)
                else:
                    self.source.write_text(value)
                result = self.run_cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.target.exists())
                self.assertIn(str(self.source), result.stderr)
        self.save(report_fixture())
        self.target = self.folder / 'missing' / 'report.pdf'
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertFalse(self.target.parent.exists())

    def test_changed_claim_is_rejected_without_a_pdf(self):
        self.save(report_fixture())
        report = json.loads(self.source.read_text())
        report['claims'][0]['description'] = 'Changed after the run'
        self.source.write_text(json.dumps(report))
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertFalse(self.target.exists())

    def test_interleaved_claims_group_by_embedded_requirement_and_keep_check_indices(self):
        report = report_fixture()
        second_requirement = copy.deepcopy(report['requirements'][0])
        second_requirement['id'] = 'REQ-B'
        report['requirements'].append(second_requirement)
        second_claim = copy.deepcopy(report['claims'][0])
        second_claim.update(id='claim-b', requirement_id='REQ-B')
        second_claim['checks'].append({'check': 'exist', 'args': {'paths': ['second.md']}})
        report['claims'].insert(1, second_claim)
        report['run_result']['claims'].insert(1, {
            'id': 'claim-b', 'digest': version_digest(second_claim), 'status': 'pass',
            'checks': [dict(check, index=n, status='pass') for n, check in enumerate(second_claim['checks'])],
        })
        self.save(report)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = self.text()
        self.assertLess(text.index('Requirement REQ-A'), text.index('Claim claim-2'))
        self.assertLess(text.index('Claim claim-2'), text.index('Requirement REQ-B'))
        self.assertLess(text.index('Requirement REQ-B'), text.index('Claim claim-b'))
        second_group = text[text.index('Requirement REQ-B'):]
        self.assertIn('PASS [0]', second_group)
        self.assertIn('PASS [1]', second_group)
        self.assertIn('second.md', second_group)

    def test_empty_run_is_not_described_as_success(self):
        report = report_fixture()
        for key in ('claims', 'requirements', 'appendix'):
            report[key] = []
        report['run_result']['claims'] = []
        self.save(report)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No Checks executed', self.text())


if __name__ == '__main__':
    unittest.main()
