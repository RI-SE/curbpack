"""Deterministic visible text extraction from Formex nodes."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# Skip footnote bodies by default; keep marker text out of law passages.
_SKIP_TAGS = frozenset({"NOTE", "BIB.INSTANCE", "QUOT.START", "QUOT.END"})


def local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def collapse_ws(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def element_text(node: ET.Element | None, *, skip_notes: bool = True) -> str:
    """Depth-first visible text. Deterministic for identical element trees."""
    if node is None:
        return ""
    parts: list[str] = []
    _collect(node, parts, skip_notes=skip_notes)
    return collapse_ws("".join(parts))


def _collect(node: ET.Element, parts: list[str], *, skip_notes: bool) -> None:
    tag = local_tag(node.tag)
    if skip_notes and tag in _SKIP_TAGS:
        return
    if node.text:
        parts.append(node.text)
    for child in list(node):
        _collect(child, parts, skip_notes=skip_notes)
        if child.tail:
            parts.append(child.tail)
