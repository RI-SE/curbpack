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
    outcomes = Counter(item['status'] for item in checks)
    content.paragraph('CURBPACK STUDIO  /  REVIEW MATERIAL', 'small')
    content.paragraph('Review report', 'title')
    content.paragraph('Management summary', 'heading')
    revision = run.get('commit')
    content.paragraph(f"Run: {run['tool']} {run['tool_version']}" +
                      (f" · saved revision {revision[:8]}…" if revision else ' · saved revision not recorded'), 'small')
    if not checks:
        content.paragraph('No Checks executed. There is no successful check result to review.', 'claim')
    else:
        if outcomes['fail']:
            content.paragraph('Checks need follow-up', 'claim')
            content.paragraph(f"{outcomes['fail']} of {len(checks)} automated checks did not pass. "
                              'Review the evidence and the check configuration before relying on these results.')
        if outcomes['skipped']:
            content.paragraph('Some checks were not performed', 'claim')
            content.paragraph(f"{outcomes['skipped']} checks were skipped. Their outcomes remain unknown.")
        if not outcomes['fail'] and not outcomes['skipped']:
            content.paragraph('All recorded checks passed', 'claim')
            content.paragraph('Human review of the supporting evidence is still required.')
    content.paragraph(f"This review covers {len(report['requirements'])} source requirements and {len(rows)} recorded statements about the evidence, "
                      f"tested by {len(checks)} automated checks. It does not establish that every applicable requirement has been assessed.")
    counts = []
    for label, items in (('Evidence assertions', rows), ('Automated checks', checks)):
        total = Counter(item['status'] for item in items)
        counts.append([label, len(items), total['pass'], total['fail'], total['skipped']])
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
    references = {item['id']: f'B.{n}' for n, item in enumerate(report['requirements'], 1)}
    claim_by_id = {claim['id']: claim for claim in report['claims']}
    attention = []
    for row in rows:
        if row['status'] == 'pass':
            continue
        claim = claim_by_id[row['id']]
        assertion = claim['description']
        excerpt = assertion if len(assertion) <= 220 else assertion[:217] + '…'
        reference = references[claim['requirement_id']]
        position = [item['id'] for item in report['claims'] if item['requirement_id'] == claim['requirement_id']].index(claim['id']) + 1
        attention.append([excerpt, 'Needs follow-up' if row['status'] == 'fail' else 'Not performed',
                          f'Finding {len(attention) + 1} / {reference}, item {position}'])
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
    requirements = {item['id']: item for item in report['requirements']}
    refs = {item['id']: f'B.{n}' for n, item in enumerate(report['requirements'], 1)}
    attention = [row for row in report['run_result']['claims'] if row['status'] != 'pass']
    for number, row in enumerate(attention, 1):
        claim = claims[row['id']]
        requirement = requirements[claim['requirement_id']]
        content.paragraph(f'Finding {number} — ' + ('Check failed' if row['status'] == 'fail' else 'Check not performed'), 'claim')
        content.field('Recorded assertion', claim['description'])
        source = requirement['source']['instrument']
        locators = ', '.join(ref['locator'] for ref in requirement['references'])
        content.field('Related source', f'{source}, {locators}')
        for check in row['checks']:
            if check['status'] == 'pass':
                continue
            content.field('Recorded result', f"{check['status'].upper()} · {check['check']} · check {check['index']}")
            content.field('Reason reported by the checker', check['detail'])
        content.paragraph('Human review: does the configured check represent the intended requirement? '
                          'Is the evidence sufficient, and does this result call for a change to the evidence or to the check settings?')
        content.field('Full technical record', f"{refs[claim['requirement_id']]} / {claim['id']}", small=True)
    if not attention:
        content.paragraph('No failed or skipped checks are recorded.' if report['run_result']['claims'] else
                          'No evidence was checked. The report cannot support a successful verification.')
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
    refs = {item['id']: f'B.{n}' for n, item in enumerate(report['requirements'], 1)}
    reviewed = []
    for claim in report['claims']:
        row = rows[claim['id']]
        totals = Counter(check['status'] for check in row['checks'])
        outcomes = ' / '.join(f'{status.upper()} {totals[status]}' for status in ('pass', 'fail', 'skipped'))
        reviewed.append([claim['requirement_id'], claim['id'], f"{row['status'].upper()}; checks: {outcomes}", refs[claim['requirement_id']]])
    content.paragraph('Reviewed items — recorded outcomes', 'claim')
    content.table(['Requirement', 'Claim', 'Claim / Check outcomes', 'Details'], reviewed, [46, 50, 54, 20])
    for number, requirement in enumerate(report['requirements'], 1):
        content.heading(f"B.{number}  Requirement {requirement['id']}")
        fields = [['Pack', requirement['pack_id']], ['Source', requirement['source']['instrument']]]
        fields += [[key, value] for key, value in requirement['source'].items() if key != 'instrument']
        for key in ('strength', 'responsible', 'applicability', 'exceptions', 'scope', 'origin', 'remediation_hint', 'note'):
            if key in requirement:
                value = requirement[key]
                fields.append([key, _json(value) if isinstance(value, (dict, list)) else value])
        content.table(['Requirement field', 'Recorded value'], fields, [38, 132])
        content.table(['Passage', 'Locator', 'Source passage'],
                      [[ref['nr'], ref['locator'], ref['law_text']] for ref in requirement['references']], [20, 24, 126])
        claims = [claim for claim in report['claims'] if claim['requirement_id'] == requirement['id']]
        for item, claim in enumerate(claims, 1):
            row = rows[claim['id']]
            content.paragraph(f"Item {item}  /  {row['status'].upper()}  /  Claim {claim['id']}", 'claim')
            fields = [['Rationale', claim['description']], ['Evidence source', claim['source']],
                      ['Evidence address / args', _json(claim['args'])], ['Executed Claim digest', row['digest']]]
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
    seals.extend((f"Requirement {item['id']}", item) for item in report['requirements'])
    seals.extend((f"Claim {item['id']}", item) for item in report['claims'])
    records = []
    for what, obj in seals:
        signed = obj.get('signed') or {}
        records.append([what, f"{signed.get('name', 'Not recorded')} / {signed.get('at', 'Not recorded')}",
                        version_digest(obj), 'Recorded; not verified' if signed else 'No JSON signature recorded'])
    content.table(['Seal object', 'Who / When', 'Version digest', 'Recorded state'], records, [43, 35, 61, 31])
    content.paragraph('A signature on the JSON report does not sign the PDF bytes. Keep the original JSON report for verification.', 'small')


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
