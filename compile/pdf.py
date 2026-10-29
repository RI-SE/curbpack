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
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


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

    def seal(self, obj, what):
        signed = obj.get('signed') or {}
        self.field('Seal object', what, small=True)
        self.field('Who / When', f"{signed.get('name', 'Not recorded')} / {signed.get('at', 'Not recorded')}", small=True)
        self.field('Version digest', version_digest(obj), small=True)
        self.paragraph(
            'Verification not performed by this PDF export. '
            + ('A JSON signature is recorded; its presence does not establish validity.'
               if signed else 'No JSON signature is recorded; Git signature coverage is not inspected.'), 'small')


def _summary(content, report):
    run = report['run_result']
    rows = run['claims']
    checks = [item for row in rows for item in row['checks']]
    content.paragraph('CURBPACK STUDIO  /  REVIEW MATERIAL', 'small')
    content.paragraph('Review report', 'title')
    content.paragraph(REVIEW_STATEMENT)
    content.paragraph(NOT_A_LEGAL_CONCLUSION, 'small')
    content.field('Checker', f"{run['tool']} {run['tool_version']}")
    content.field('Product commit', run.get('commit', 'Not recorded'))
    content.field('Worktree', run.get('worktree', 'Not recorded'))
    if worktree_sentence(run):
        content.paragraph(worktree_sentence(run))
    if 'commit' not in run:
        content.paragraph('This run has no recorded Git revision.', 'small')
    content.field('Report version digest', version_digest(report), small=True)
    content.paragraph('Recorded outcomes', 'claim')
    counts = []
    for label, items in (('Claims', rows), ('Checks', checks)):
        total = Counter(item['status'] for item in items)
        counts.append([Paragraph(f'<b>{label}: {len(items)}</b>', content.styles['body']),
                       Paragraph('  /  '.join(f'{status.upper()} {total[status]}'
                                 for status in ('pass', 'fail', 'skipped')), content.styles['body'])])
    table = Table(counts, colWidths=[42 * mm, 128 * mm], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eeeeee')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    content.blocks.append(table)
    if not checks:
        content.paragraph('No Checks executed. This is not a successful verification.')
    content.paragraph('Counts cover the Claims and Checks in this run, not all applicable Requirements.', 'small')
    content.heading('Loaded Packs')
    for pack in run['packs']:
        content.field(pack['id'], f"version {pack['version']}")
        content.field('Directory digest', pack['digest'], small=True)
    if not run['packs']:
        content.paragraph('No Packs recorded.')


def _requirements(content, report):
    rows = {row['id']: row for row in report['run_result']['claims']}
    for requirement in report['requirements']:
        content.heading(f"Requirement {requirement['id']}")
        content.field('Pack', requirement['pack_id'])
        source = requirement['source']
        content.field('Source', source['instrument'])
        for key, value in source.items():
            if key != 'instrument':
                content.field(key, value, small=True)
        for key in ('strength', 'responsible', 'applicability', 'exceptions', 'scope', 'origin'):
            if key in requirement:
                value = requirement[key]
                content.field(key, _json(value) if isinstance(value, (dict, list)) else value)
        for reference in requirement['references']:
            content.field('Source passage', f"{reference['nr']} · {reference['locator']}")
            content.paragraph(reference['law_text'])
        for key in ('remediation_hint', 'note'):
            if key in requirement:
                content.field(key.replace('_', ' ').capitalize(), requirement[key])
        content.seal(requirement, f"Requirement {requirement['id']}")
        for claim in report['claims']:
            if claim['requirement_id'] != requirement['id']:
                continue
            row = rows[claim['id']]
            content.blocks.append(Spacer(1, 4 * mm))
            content.paragraph(f"{row['status'].upper()}  /  Claim {claim['id']}", 'claim')
            content.field('Rationale', claim['description'])
            content.field('Evidence source', claim['source'])
            content.field('Evidence address / args', _json(claim['args']))
            if 'severity' in claim:
                content.field('Product triage', claim['severity'])
            content.field('Executed Claim digest', row['digest'], small=True)
            for check in row['checks']:
                content.field(f"{check['status'].upper()}  [{check['index']}]", check['check'])
                content.field('Check arguments', _json(check['args']), small=True)
                if 'detail' in check:
                    content.field('Detail', check['detail'])
            content.seal(claim, f"Claim {claim['id']}")


def _review(content, report):
    content.heading('Signature appendix')
    content.paragraph('Recorded signature gaps are separate from Check outcomes. These reasons are copied from the report.')
    for item in report['appendix']:
        content.field(f"{item['id']} / {item['requirement_id']}", item['reason'])
    if not report['appendix']:
        content.paragraph('No entries recorded. This PDF export does not independently verify signatures.')
    content.heading('Reviewer decision')
    content.paragraph(report.get('decision', 'No reviewer decision recorded.'))
    content.heading('Report seal')
    content.seal(report, 'Review report JSON')
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
