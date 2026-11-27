"""Deterministic visible text extraction from Formex nodes."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# Skip footnote bodies by default; keep marker text out of law passages.
_SKIP_TAGS = frozenset({"NOTE", "BIB.INSTANCE", "QUOT.START", "QUOT.END"})

# Formex CODE values that stand for a quotation mark which is not a text node.
_QUOT_GLYPH = {
    "2018": "\u2018",
    "2019": "\u2019",
    "201C": "\u201c",
    "201D": "\u201d",
}


def local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def collapse_ws(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def element_text(node: ET.Element | None, *, skip_notes: bool = True, chart=None) -> str:
    """Depth-first visible text. Deterministic for identical element trees."""
    if node is None:
        return ""
    parts: list[str] = []
    _collect(node, parts, skip_notes=skip_notes, chart=chart)
    return collapse_ws("".join(parts))


def _collect(node: ET.Element, parts: list[str], *, skip_notes: bool, chart=None) -> None:
    tag = local_tag(node.tag)
    if skip_notes and tag in _SKIP_TAGS:
        if chart is not None:
            chart.uncovered(_skipped_visible(node, tag), reason=tag)
        return
    if node.text:
        parts.append(node.text)
    for child in list(node):
        _collect(child, parts, skip_notes=skip_notes, chart=chart)
        if child.tail:
            parts.append(child.tail)


def _skipped_visible(node: ET.Element, tag: str) -> str:
    if tag in {"QUOT.START", "QUOT.END"}:
        glyph = _QUOT_GLYPH.get(node.get("CODE") or "", "")
        inner = collapse_ws("".join(node.itertext()))
        return collapse_ws(f"{glyph}{inner}")
    return element_text(node, skip_notes=False)
