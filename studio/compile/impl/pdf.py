"""Render a saved review report without reading mutable product files."""
from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle

from common.canonical import version_digest
from review.compile import NOT_A_LEGAL_CONCLUSION, load_report, worktree_sentence
from studio.compile.impl.report import assessment_identity, recorded_deviations

REVIEW_STATEMENT = 'Prepares evidence for human review — not a conformity assessment.'


def _styles():
    # ReportLab ships these fonts: no platform font discovery or network fetch.
    fonts = Path(reportlab.__file__).parent / 'fonts'
    for name, filename in (('Review', 'Vera.ttf'), ('Review-Bold', 'VeraBd.ttf')):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily('Review', normal='Review', bold='Review-Bold',
                                  italic='Review', boldItalic='Review-Bold')
    styles = getSampleStyleSheet()
    result = {}
    for name, size, leading, after in (
        ('body', 9, 14, 6), ('small', 7.5, 11, 5),
        ('title', 27, 33, 10), ('heading', 16, 21, 10), ('claim', 11, 16, 7),
    ):
        result[name] = ParagraphStyle(
            f'Review-{name}', parent=styles['Normal'], fontName='Review',
            fontSize=size, leading=leading, spaceAfter=after,
            textColor=colors.black, alignment=TA_LEFT, splitLongWords=True,
            keepWithNext=name in ('heading', 'claim'),
        )
    return result


def _text(value):
    return escape(str(value)).replace('\n', '<br/>')


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class _ReportContent:
    """Small layout builder, containing only presentation of validated objects."""
    def __init__(self, styles):
        self.styles = styles
        self.blocks = []

    def paragraph(self, text, style='body'):
        self.blocks.append(Paragraph(_text(text), self.styles[style]))

    def field(self, label, value, *, small=False):
        self.blocks.append(Paragraph(
            f'<b>{_text(label)}</b>  {_text(value)}', self.styles['small' if small else 'body']))

    def heading(self, text):
        self.blocks.extend([Spacer(1, 7 * mm),
                            HRFlowable(width='100%', thickness=0.6, color=colors.black),
                            Spacer(1, 4 * mm)])
        self.paragraph(text, 'heading')

    def table(self, headers, rows, widths):
        def cell(value, *, header=False):
            text = _text(value)
            return Paragraph(f'<b>{text}</b>' if header else text, self.styles['small'])
        data = [[cell(value, header=True) for value in headers]]
        data.extend([cell(value) for value in row] for row in rows)
        table = LongTable(data, colWidths=[width * mm for width in widths],
                          repeatRows=1, splitInRow=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#777777')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        self.blocks.extend([table, Spacer(1, 3 * mm)])


def _summary(content, report):
    run = report['run_result']
    rows = run['claims']
    checks = [item for row in rows for item in row['checks']]
    retired = _retired_checks(report)
    outcomes = Counter(item['status'] for item in checks)
    outstanding_fail = 0
    retired_fail = 0
    outstanding_skip = 0
    for row in rows:
        for item in row['checks']:
            marked = (row['id'], item.get('index')) in retired
            if item['status'] == 'fail' and marked:
                retired_fail += 1
            elif item['status'] == 'fail':
                outstanding_fail += 1
            elif item['status'] == 'skipped' and not marked:
                outstanding_skip += 1
    content.paragraph('CURBPACK STUDIO  /  REVIEW MATERIAL', 'small')
    content.paragraph('Review report', 'title')
    content.paragraph('Management summary', 'heading')
    revision = run.get('commit')
    content.paragraph(f"Run: {run['tool']} {run['tool_version']}" +
                      (f" · saved revision {revision[:8]}…" if revision else ' · saved revision not recorded'), 'small')
    if not checks:
        content.paragraph('No Checks executed. There is no successful check result to review.', 'claim')
    else:
        if outstanding_fail:
            content.paragraph('Checks need follow-up', 'claim')
            content.paragraph(f"{outstanding_fail} of {len(checks)} automated checks did not pass. "
                              'Review the evidence and the check configuration before relying on these results.')
        if retired_fail:
            content.paragraph('Retired checks', 'claim')
            content.paragraph(f"{retired_fail} failed checks were retired. They are not outstanding corrections. "
                              'The recorded result remains in this report.')
        if outstanding_skip:
            content.paragraph('Some checks were not performed', 'claim')
            content.paragraph(f"{outstanding_skip} checks were skipped. Their outcomes remain unknown.")
        if not outstanding_fail and not outstanding_skip and not retired_fail:
            content.paragraph('All recorded checks passed', 'claim')
            content.paragraph('Human review of the supporting evidence is still required.')
    content.paragraph(f"This review covers {len(report['requirements'])} requirement versions and {len(rows)} recorded statements about the evidence, "
                      f"tested by {len(checks)} automated checks. It does not establish that every applicable requirement has been assessed.")
    counts = []
    for label, items in (('Evidence assertions', rows), ('Automated checks', checks)):
        total = Counter(item['status'] for item in items)
        follow_up = total['fail']
        if label == 'Automated checks':
            follow_up = outstanding_fail
        counts.append([label, len(items), total['pass'], follow_up, total['skipped']])
    content.table(['Included', 'Total', 'Passed', 'Needs follow-up', 'Not performed'], counts, [50, 18, 23, 40, 39])
    sources = list(dict.fromkeys(item['source']['instrument'] for item in report['requirements']))
    if sources:
        content.field('Sources represented', '; '.join(sources))
    content.paragraph(REVIEW_STATEMENT, 'small')
    content.paragraph(NOT_A_LEGAL_CONCLUSION, 'small')
    if run.get('worktree') == 'dirty':
        content.paragraph('The checked working files included uncommitted changes. '
                          'The saved revision alone does not identify everything that was checked.', 'small')
    elif 'commit' not in run:
        content.paragraph('No saved revision was recorded for the checked files.', 'small')
    content.blocks.append(Spacer(1, 3 * mm))
    content.paragraph('What needs attention', 'claim')
    claim_by_id = {claim['id']: claim for claim in report['claims']}
    attention = []
    for row in rows:
        if not _row_needs_attention(row, retired):
            continue
        claim = claim_by_id[row['id']]
        assertion = claim['description']
        excerpt = assertion if len(assertion) <= 220 else assertion[:217] + '…'
        reference = _ref_for_claim(report, claim)
        linked = _claims_for_requirement(report, _requirement_for_claim(report, claim) or {})
        position = [item['id'] for item in linked].index(claim['id']) + 1 if claim['id'] in [item['id'] for item in linked] else 1
        detail = f'Finding {len(attention) + 1} / {reference}, item {position}'
        identity = _binding_identity(row)
        if identity:
            detail = f'{detail}; {identity}'
        attention.append([excerpt, _attention_outcome(row), detail])
    if attention:
        content.paragraph('The statements below are recorded assertions, not conclusions drawn by this report. '
                          'Review the supporting evidence and check settings, address the cause, then run the checks again.')
        content.table(['Recorded assertion', 'Outcome', 'Details'], attention, [112, 32, 26])
    else:
        content.paragraph('No failed or skipped checks are recorded.' if checks else 'Evidence must be checked before a result can be assessed.')
    content.paragraph('Approval records', 'claim')
    gaps = len(report['appendix'])
    content.paragraph(f'The saved report lists approval or signature gaps for {gaps} evidence statements. '
                      'These are separate from automated check outcomes; see Appendix C.' if gaps else
                      'No approval or signature gaps are listed in the saved report. This export has not independently verified approvals.')
    content.paragraph('Reviewer decision', 'claim')
    content.paragraph(report.get('decision', 'No reviewer decision recorded.'))
    content.paragraph('Review findings follow. Technical records are in appendices A–C.', 'small')


def _findings(content, report):
    content.blocks.append(PageBreak())
    content.paragraph('Review findings', 'heading')
    content.paragraph('Use these points to review the material. The recorded assertions and results are not decisions by the PDF exporter.', 'small')
    claims = {claim['id']: claim for claim in report['claims']}
    saved = {}
    for item in report.get('assessments') or []:
        saved[assessment_identity(item)] = item
    outstanding = []
    accepted = []
    retired_findings = []
    for deviation in recorded_deviations(report['run_result']):
        assessment = saved.get(assessment_identity(deviation))
        if assessment and assessment.get('disposition') == 'accept':
            accepted.append((deviation, assessment))
        elif assessment and assessment.get('disposition') == 'retire':
            retired_findings.append((deviation, assessment))
        else:
            outstanding.append((deviation, assessment))
    for item in report.get('assessments') or []:
        if not isinstance(item, dict) or item.get('disposition') != 'retire' or item.get('kind') != 'check':
            continue
        if any(assessment_identity(saved_item) == assessment_identity(item) for _deviation, saved_item in retired_findings):
            continue
        retired_findings.append((_passing_retirement(report, item), item))
    content.paragraph('Outstanding deviations requiring correction', 'claim')
    if outstanding:
        for number, (deviation, assessment) in enumerate(outstanding, 1):
            _deviation_finding(content, report, claims, number, deviation, assessment)
    elif report['run_result']['claims']:
        content.paragraph('No outstanding deviations are recorded.')
    else:
        content.paragraph('No evidence was checked. The report cannot support a successful verification.')
    content.paragraph('Accepted deviations', 'claim')
    if accepted:
        for number, (deviation, assessment) in enumerate(accepted, 1):
            _deviation_finding(content, report, claims, number, deviation, assessment)
    else:
        content.paragraph('No deviations were accepted.')
    content.paragraph('Retired checks', 'claim')
    if retired_findings:
        for number, (deviation, assessment) in enumerate(retired_findings, 1):
            _retired_finding(content, report, claims, number, deviation, assessment)
    else:
        content.paragraph('No checks were retired.')
    content.paragraph('Passing checks', 'claim')
    passing = []
    for row in report['run_result']['claims']:
        claim = claims.get(row['id'])
        if claim is None:
            continue
        for check in row['checks']:
            if check['status'] == 'pass':
                passing.append((claim, row, check))
    if passing:
        for claim, row, check in passing:
            content.field(
                'Passing check',
                f"PASS · {check['check']} · check {check['index']} · {claim['id']}",
            )
    elif report['run_result']['claims']:
        content.paragraph('No passing checks are recorded.')
    content.heading('Limits to this review')
    if report['run_result'].get('worktree') == 'dirty':
        content.paragraph('The checked files included uncommitted changes. The saved revision does not capture the full checked state.')
    elif 'commit' not in report['run_result']:
        content.paragraph('No saved revision is recorded for the checked files.')
    if report['appendix']:
        content.paragraph(f"The saved report records signature gaps for {len(report['appendix'])} evidence statements. "
                          'A signature gap is separate from a failed check. See Appendix C for the recorded reasons.')
    content.paragraph('Changes since the run and unresolved current evidence are not assessed by this export. '
                      'It reads the saved historical report, without comparing current files. '
                      'Signatures are not independently verified. These are limits of the export, not zero counts or verification results.', 'small')


def _run_appendix(content, report):
    content.blocks.append(PageBreak())
    content.paragraph('Appendix A — Run and source records', 'heading')
    run = report['run_result']
    content.table(['Recorded field', 'Value'], [
        ['Checker', f"{run['tool']} {run['tool_version']}"],
        ['Product commit', run.get('commit', 'Not recorded')],
        ['Worktree', run.get('worktree', 'Not recorded')],
        ['Report version digest', version_digest(report)],
    ], [42, 128])
    if worktree_sentence(run):
        content.paragraph(worktree_sentence(run), 'small')
    counts = []
    for label, items in (('Claims', run['claims']), ('Checks', [check for row in run['claims'] for check in row['checks']])):
        totals = Counter(item['status'] for item in items)
        counts.append([f'{label}: {len(items)}', ' / '.join(f'{status.upper()} {totals[status]}' for status in ('pass', 'fail', 'skipped'))])
    content.table(['Recorded scope', 'Outcomes'], counts, [42, 128])
    content.paragraph('Loaded Packs', 'claim')
    content.table(['Pack id', 'Version', 'Directory digest'],
                  [[pack['id'], pack['version'], pack['digest']] for pack in run['packs']], [45, 23, 102])


def _requirements(content, report):
    content.blocks.append(PageBreak())
    content.paragraph('Appendix B — Requirements, evidence and checks', 'heading')
    rows = {row['id']: row for row in report['run_result']['claims']}
    reviewed = []
    for claim in report['claims']:
        row = rows[claim['id']]
        totals = Counter(check['status'] for check in row['checks'])
        outcomes = ' / '.join(f'{status.upper()} {totals[status]}' for status in ('pass', 'fail', 'skipped'))
        recorded = f"{row['status'].upper()}; checks: {outcomes}"
        label = _binding_label(row)
        if label:
            recorded = f'{recorded}; {label}'
        reviewed.append([claim['requirement_id'], claim['id'], recorded, _ref_for_claim(report, claim)])
    content.paragraph('Reviewed items — recorded outcomes', 'claim')
    content.table(['Requirement', 'Claim', 'Claim / Check outcomes', 'Details'], reviewed, [46, 50, 54, 20])
    repeated = _repeated_requirement_ids(report)
    for number, requirement in enumerate(report['requirements'], 1):
        content.heading(_requirement_heading(number, requirement, repeated))
        fields = [['Pack', requirement['pack_id']], ['Source', requirement['source']['instrument']]]
        fields += [[key, value] for key, value in requirement['source'].items() if key != 'instrument']
        for key in ('strength', 'responsible', 'applicability', 'exceptions', 'scope', 'origin', 'remediation_hint', 'note'):
            if key in requirement:
                value = requirement[key]
                fields.append([key, _json(value) if isinstance(value, (dict, list)) else value])
        content.table(['Requirement field', 'Recorded value'], fields, [38, 132])
        content.table(['Passage', 'Locator', 'Source passage'],
                      [[ref['nr'], ref['locator'], ref['law_text']] for ref in requirement['references']], [20, 24, 126])
        claims = _claims_for_requirement(report, requirement)
        for item, claim in enumerate(claims, 1):
            row = rows[claim['id']]
            label = _binding_label(row)
            heading = f"Item {item}  /  {row['status'].upper()}  /  Claim {claim['id']}"
            if label:
                heading = f"{heading}  /  {label}"
            content.paragraph(heading, 'claim')
            fields = [['Rationale', claim['description']], ['Evidence source', claim['source']],
                      ['Evidence address / args', _json(claim['args'])], ['Executed Claim digest', row['digest']]]
            if label:
                fields.append(['Requirement binding', label])
                identity = _binding_identity(row)
                if identity:
                    fields.append(['Requirement identity', identity])
            if 'severity' in claim:
                fields.append(['Product triage', claim['severity']])
            content.table(['Claim field', 'Recorded value'], fields, [38, 132])
            content.table(['Check / outcome', 'Check arguments', 'Detail'],
                          [[f"{check['status'].upper()} [{check['index']}] {check['check']}",
                            _json(check['args']), check.get('detail', '—')] for check in row['checks']], [36, 89, 45])


def _review(content, report):
    content.blocks.append(PageBreak())
    content.paragraph('Appendix C — Approval and signature records', 'heading')
    content.paragraph('Signature appendix', 'claim')
    content.paragraph('Recorded signature gaps are separate from Check outcomes. These reasons are copied from the report.', 'small')
    content.table(['Claim', 'Requirement', 'Recorded reason'],
                  [[item['id'], item['requirement_id'], item['reason']] for item in report['appendix']], [40, 40, 90])
    content.paragraph('Recorded seals', 'claim')
    content.paragraph('Verification not performed by this PDF export. JSON signatures are recorded metadata; '
                      'their presence does not establish validity. Git signature coverage is not inspected.', 'small')
    seals = [('Review report JSON', report)]
    repeated = _repeated_requirement_ids(report)
    seals.extend((_requirement_seal_label(item, repeated), item) for item in report['requirements'])
    seals.extend((f"Claim {item['id']}", item) for item in report['claims'])
    records = []
    for what, obj in seals:
        signed = obj.get('signed') or {}
        records.append([what, f"{signed.get('name', 'Not recorded')} / {signed.get('at', 'Not recorded')}",
                        version_digest(obj), 'Recorded; not verified' if signed else 'No JSON signature recorded'])
    content.table(['Seal object', 'Who / When', 'Version digest', 'Recorded state'], records, [43, 35, 61, 31])
    content.paragraph('A signature on the JSON report does not sign the PDF bytes. Keep the original JSON report for verification.', 'small')


def _deviation_finding(content, report, claims, number, deviation, assessment):
    claim = claims[deviation['claim_id']]
    row = next(item for item in report['run_result']['claims'] if item['id'] == deviation['claim_id'])
    content.paragraph(f'Finding {number} — {_deviation_title(deviation, assessment)}', 'claim')
    content.field('Recorded assertion', claim['description'])
    _binding_fields(content, row)
    requirement = _requirement_for_claim(report, claim)
    if requirement is not None:
        source = requirement['source']['instrument']
        locators = ', '.join(ref['locator'] for ref in requirement['references'])
        content.field('Related source', f'{source}, {locators}')
    if deviation['kind'] == 'check':
        content.field(
            'Recorded result',
            f"{deviation['status'].upper()} · {deviation['check']} · check {deviation['index']}",
        )
        content.field('Reason reported by the checker', deviation['detail'])
        if deviation.get('remediation_hint'):
            content.field('Check remediation', deviation['remediation_hint'])
    else:
        content.field('Requirement binding', f"binding {deviation['binding']}")
    hint = _recorded_requirement_hint(requirement, claim)
    if hint is None:
        content.field('Requirement remediation', 'Unavailable for the Requirement version recorded on this run.')
    elif hint:
        content.field('Requirement remediation', hint)
    if assessment and assessment.get('disposition') == 'must_fix':
        content.field('Required correction', assessment['text'])
    elif assessment and assessment.get('disposition') == 'accept':
        content.field('Accepted justification', assessment['text'])
    else:
        content.field('Reviewer assessment', 'Not assessed')
    content.paragraph('Human review: does the configured check represent the intended requirement? '
                      'Is the evidence sufficient, and does this result call for a change to the evidence or to the check settings?')
    content.field('Full technical record', f"{_ref_for_claim(report, claim)} / {claim['id']}", small=True)


def _recorded_requirement_hint(requirement, claim):
    if not isinstance(requirement, dict):
        return None
    recorded = claim.get('requirement_digest')
    if not isinstance(recorded, str) or not recorded:
        return None
    if version_digest(requirement) != recorded:
        return None
    hint = requirement.get('remediation_hint')
    return hint if isinstance(hint, str) else ''


def _deviation_title(deviation, assessment):
    if deviation['kind'] == 'binding':
        title = f"Requirement binding {deviation['binding']}"
    elif deviation['status'] == 'fail':
        title = 'Check failed'
    else:
        title = 'Check not performed'
    if assessment and assessment.get('disposition') == 'must_fix':
        return f'{title}; must be fixed'
    if assessment and assessment.get('disposition') == 'accept':
        return f'{title}; accepted'
    return f'{title}; not assessed'


def _retired_checks(report):
    found = set()
    for item in report.get('assessments') or []:
        if isinstance(item, dict) and item.get('kind') == 'check' and item.get('disposition') == 'retire':
            found.add((item.get('claim_id'), item.get('index')))
    return found


def _row_needs_attention(row, retired):
    if row.get('binding') in {'stale', 'missing'}:
        return True
    for item in row.get('checks') or []:
        if item.get('status') in {'fail', 'skipped'} and (row.get('id'), item.get('index')) not in retired:
            return True
    return False


def _passing_retirement(report, item):
    for row in report['run_result']['claims']:
        if row.get('id') != item.get('claim_id'):
            continue
        for check in row.get('checks') or []:
            if check.get('index') == item.get('index'):
                return {
                    'kind': 'check',
                    'claim_id': item.get('claim_id'),
                    'status': check.get('status') or 'pass',
                    'check': check.get('check') or '',
                    'index': check.get('index'),
                    'detail': check.get('detail') or '',
                }
    return {
        'kind': 'check',
        'claim_id': item.get('claim_id'),
        'status': 'pass',
        'check': '',
        'index': item.get('index'),
        'detail': '',
    }


def _retired_finding(content, report, claims, number, deviation, assessment):
    claim = claims[deviation['claim_id']]
    content.paragraph(f'Retired check {number}', 'claim')
    content.field('Recorded assertion', claim['description'])
    content.field(
        'Recorded result',
        f"{str(deviation.get('status') or 'pass').upper()} · {deviation.get('check') or ''} · check {deviation.get('index')}",
    )
    if deviation.get('detail'):
        content.field('Reason reported by the checker', deviation['detail'])
    content.field('Retirement justification', assessment['text'])
    content.paragraph("The recorded result is unchanged. Retirement is the reviewer's decision.")


def _claim_version(claim):
    return (claim.get('requirement_id'), claim.get('requirement_digest'))


def _requirement_version(requirement):
    return (requirement.get('id'), version_digest(requirement))


def _requirement_for_claim(report, claim):
    recorded = claim.get('requirement_digest')
    same_id = []
    for item in report['requirements']:
        if item.get('id') != claim.get('requirement_id'):
            continue
        same_id.append(item)
        if isinstance(recorded, str) and version_digest(item) == recorded:
            return item
    if len(same_id) == 1:
        return same_id[0]
    return None


def _ref_for_claim(report, claim):
    requirement = _requirement_for_claim(report, claim)
    if requirement is None:
        return ''
    for number, item in enumerate(report['requirements'], 1):
        if item is requirement:
            return f'B.{number}'
    return ''


def _claims_for_requirement(report, requirement):
    if not requirement:
        return []
    exact = [
        claim for claim in report['claims']
        if _claim_version(claim) == _requirement_version(requirement)
    ]
    if exact or requirement.get('id') in _repeated_requirement_ids(report):
        return exact
    return [
        claim for claim in report['claims']
        if claim.get('requirement_id') == requirement.get('id')
    ]


def _repeated_requirement_ids(report):
    counts = Counter(item.get('id') for item in report['requirements'])
    return {requirement_id for requirement_id, count in counts.items() if count > 1}


def _requirement_heading(number, requirement, repeated):
    title = f"B.{number}  Requirement {requirement['id']}"
    if requirement.get('id') in repeated:
        title = f"{title}  version {version_digest(requirement)[:12]}"
    return title


def _requirement_seal_label(requirement, repeated):
    label = f"Requirement {requirement['id']}"
    if requirement.get('id') in repeated:
        label = f"{label} {version_digest(requirement)[:12]}"
    return label


def _binding_label(row):
    binding = row.get('binding')
    if binding not in {'match', 'stale', 'missing'}:
        return ''
    return f'binding {binding}'


def _binding_identity(row):
    if row.get('binding') not in {'stale', 'missing'}:
        return ''
    parts = [str(row.get(key) or '') for key in ('namespace', 'pack_id', 'requirement_id')]
    text = ' '.join(part for part in parts if part)
    recorded = str(row.get('requirement_digest') or '')
    if recorded:
        text = f'{text} requirement {recorded}'.strip()
    if row.get('binding') == 'stale' and row.get('actual_digest'):
        text = f'{text} actual {row["actual_digest"]}'.strip()
    return text


def _attention_outcome(row):
    if row['status'] == 'fail':
        outcome = 'Needs follow-up'
    elif row['status'] == 'skipped':
        outcome = 'Not performed'
    else:
        outcome = 'Check passed'
    label = _binding_label(row)
    return f'{outcome}; {label}' if label else outcome


def _finding_title(row):
    if row['status'] == 'fail':
        title = 'Check failed'
    elif row['status'] != 'pass':
        title = 'Check not performed'
    else:
        title = 'Check passed'
    label = _binding_label(row)
    return f'{title}; {label}' if label else title


def _binding_fields(content, row):
    label = _binding_label(row)
    if not label:
        return
    content.field('Requirement binding', label)
    identity = _binding_identity(row)
    if identity:
        content.field('Requirement identity', identity)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setFillColor(colors.black)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 17 * mm, A4[0] - 20 * mm, 17 * mm)
    canvas.setFont('Review', 7)
    canvas.drawString(20 * mm, 12 * mm, 'Curbpack Studio · Review material')
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f'Page {doc.page}')
    canvas.restoreState()


def compile_pdf(report_path: Path, out: Path) -> Path:
    """Write a new PDF. Never overwrite an existing target or modify the JSON."""
    report_path, out = Path(report_path), Path(out)
    if os.path.lexists(out):
        raise FileExistsError(f'PDF output already exists: {out}')
    report = load_report(report_path)
    content = _ReportContent(_styles())
    _summary(content, report)
    _findings(content, report)
    _run_appendix(content, report)
    _requirements(content, report)
    _review(content, report)
    # Render fully before publishing. link() creates the destination exclusively,
    # protecting existing files even when another process wins the final race.
    fd, temporary = tempfile.mkstemp(prefix='.compile-pdf-', suffix='.pdf', dir=out.parent)
    os.close(fd)
    try:
        document = SimpleDocTemplate(temporary, pagesize=A4, rightMargin=20 * mm,
                                     leftMargin=20 * mm, topMargin=19 * mm, bottomMargin=23 * mm,
                                     title='Curbpack Studio — Review report', author='Curbpack Studio')
        document.build(content.blocks, onFirstPage=_footer, onLaterPages=_footer)
        os.link(temporary, out)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return out
