"""Source inventory of Formex structural units (not yet provisions)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from requirements.extract.formex.package import load_doc_package
from requirements.extract.formex.text import collapse_ws, element_text, local_tag

_UNSUPPORTED_TAGS = frozenset({"TBL", "FORMULA", "MATH"})


def inventory_package(directory: Path) -> dict:
    """List structural units for a Formex DOC package directory."""
    package = load_doc_package(directory)
    units: list[dict] = []
    diagnostics: list[dict] = []
    for part in package["parts"]:
        if part.get("supported") is False:
            diagnostics.append(
                {
                    "unit_id": part["section_id"],
                    "kind": part["kind"],
                    "reason": part.get("reason") or "unsupported package part",
                }
            )
            continue
        file_path: Path = part["file"]
        root = ET.parse(file_path).getroot()
        if part["kind"] == "body":
            units.extend(_inventory_act(root, file_path))
        elif part["kind"] == "annex":
            units.extend(_inventory_annex(root, part["section_id"], file_path))
        _record_unsupported(root, part["section_id"], diagnostics)
    return {
        "language": package["language"],
        "legal_value": package["legal_value"],
        "title": package["title"],
        "doc_file": str(package["doc_file"]),
        "units": units,
        "diagnostics": diagnostics,
    }


def _inventory_act(root: ET.Element, file_path: Path) -> list[dict]:
    units: list[dict] = []
    parents = _parent_map(root)
    for node in root.iter():
        tag = local_tag(node.tag)
        if tag == "DIVISION":
            parent = parents.get(id(node))
            if parent is not None and local_tag(parent.tag) == "ARTICLE":
                continue
            heading = element_text(node.find("TITLE/TI")) or element_text(node.find("TI"))
            if not heading:
                continue
            units.append(
                {
                    "unit_id": f"DIVISION:{collapse_ws(heading)[:60]}",
                    "kind": "division",
                    "locator": collapse_ws(heading),
                    "heading": heading,
                    "subtitle": element_text(node.find("TITLE/STI")) or "",
                    "file": file_path.name,
                    "supported": True,
                }
            )
        elif tag == "ARTICLE":
            article_no = _article_number(node)
            units.append(
                {
                    "unit_id": f"Art.{article_no}",
                    "kind": "article",
                    "locator": f"Art.{article_no}",
                    "heading": element_text(node.find("TI.ART")) or f"Article {article_no}",
                    "subtitle": element_text(node.find("STI.ART")),
                    "file": file_path.name,
                    "supported": True,
                }
            )
    return units


def _inventory_annex(root: ET.Element, section_id: str, file_path: Path) -> list[dict]:
    units = [
        {
            "unit_id": f"Annex.{section_id}",
            "kind": "annex",
            "locator": f"Annex {section_id}",
            "heading": element_text(root.find("TITLE/TI")) or f"ANNEX {section_id}",
            "subtitle": element_text(root.find("TITLE/STI")),
            "file": file_path.name,
            "supported": True,
        }
    ]
    for node in root.iter():
        if local_tag(node.tag) != "GR.SEQ":
            continue
        heading = element_text(node.find("TITLE/TI")) or element_text(node.find("TI"))
        units.append(
            {
                "unit_id": f"Annex.{section_id}/Part:{collapse_ws(heading)[:40]}",
                "kind": "annex_part",
                "locator": f"Annex {section_id}",
                "heading": heading,
                "subtitle": "",
                "file": file_path.name,
                "supported": True,
            }
        )
    return units


def _record_unsupported(root: ET.Element, scope: str, diagnostics: list[dict]) -> None:
    seen: set[tuple[str, str]] = set()
    for node in root.iter():
        tag = local_tag(node.tag)
        if tag not in _UNSUPPORTED_TAGS:
            continue
        key = (scope, tag)
        if key in seen:
            continue
        seen.add(key)
        diagnostics.append(
            {
                "unit_id": f"{scope}/{tag}",
                "kind": tag.lower(),
                "reason": f"substantive Formex element <{tag}> is not extracted as provisions",
            }
        )


def _article_number(article: ET.Element) -> str:
    ti = element_text(article.find("TI.ART"))
    if ti:
        match = re.search(r"(\d+)", ti)
        if match:
            return match.group(1)
    ident = article.get("IDENTIFIER") or ""
    return ident.lstrip("0") or ident


def _parent_map(root: ET.Element) -> dict[int, ET.Element]:
    parents: dict[int, ET.Element] = {}
    for parent in root.iter():
        for child in list(parent):
            parents[id(child)] = parent
    return parents
