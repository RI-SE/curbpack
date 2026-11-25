"""Render the remediation PDF from the Markdown file. The PDF is written once."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, SimpleDocTemplate

from studio.compile.impl.pdf import _ReportContent, _styles
from studio.review.impl.remedy_markdown import parse_remedy_markdown


def write_remedy_pdf(markdown: str, out: Path) -> Path:
    """Write a new PDF from Markdown text. An existing file is left unchanged."""
    out = Path(out)
    if os.path.lexists(out):
        raise FileExistsError(f"PDF output already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    content = _ReportContent(_styles())
    for kind, *rest in parse_remedy_markdown(markdown):
        if kind == "h1":
            content.paragraph(rest[0], "title")
        elif kind == "h2":
            if str(rest[0]).startswith("Appendix."):
                content.blocks.append(PageBreak())
            content.paragraph(rest[0], "heading")
        elif kind == "p":
            content.paragraph(rest[0])
        else:
            headers, rows = rest
            if not rows:
                continue
            width = 170 / max(len(headers), 1)
            content.table(headers, rows, [width] * len(headers))
    fd, temporary = tempfile.mkstemp(prefix=".remedy-pdf-", suffix=".pdf", dir=out.parent)
    os.close(fd)
    try:
        pdf = SimpleDocTemplate(
            temporary,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=19 * mm,
            bottomMargin=23 * mm,
            title="Curbpack Studio — Remediation report",
            author="Curbpack Studio",
        )
        pdf.build(content.blocks, onFirstPage=_footer, onLaterPages=_footer)
        os.link(temporary, out)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return out


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setFillColor(colors.black)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 17 * mm, A4[0] - 20 * mm, 17 * mm)
    canvas.setFont("Review", 7)
    canvas.drawString(20 * mm, 12 * mm, "Curbpack Studio · Remediation report")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()
