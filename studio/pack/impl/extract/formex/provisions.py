"""Provision extraction from selected Formex structural units."""

from __future__ import annotations

import re
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

from common.errors import ModelError
from requirements.extract.formex.package import load_doc_package
from requirements.extract.formex.text import collapse_ws, element_text, local_tag


def wrap_law(text: str, width: int = 78) -> str:
    return textwrap.fill(
        collapse_ws(text),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def extract_section_provisions(directory: Path, section_id: str, chart=None) -> dict:
    """Return provisions + diagnostics for one package section id.

    Annex sections use roman ids (``VII``). Article sections use ``Art.13``.
    Body ``_body`` is refused for provision extraction until article selection
    is explicit.
    """
    package = load_doc_package(directory)
    if section_id.startswith("Art."):
        body = next((part for part in package["parts"] if part["kind"] == "body"), None)
        if body is None:
            raise ModelError(directory.name, "body", "present for article extraction")
        article_no = section_id.split(".", 1)[1]
        root = ET.parse(body["file"]).getroot()
        article = _find_article(root, article_no)
        if article is None:
            raise ModelError(directory.name, "ARTICLE", f"Art.{article_no}")
        provisions = _provisions_from_article(article, article_no, chart=chart)
        return {
            "section_id": section_id,
            "kind": "article",
            "file": str(body["file"]),
            "provisions": provisions,
            "diagnostics": [],
        }

    part = next(
        (
            item
            for item in package["parts"]
            if item.get("section_id") == section_id and item.get("kind") == "annex"
        ),
        None,
    )
    if part is None:
        raise ModelError(directory.name, "sections[].id", f"a ready annex named {section_id}")
    if part.get("supported") is False:
        raise ModelError(directory.name, section_id, part.get("reason") or "unsupported")
    root = ET.parse(part["file"]).getroot()
    diagnostics = []
    tables = [node for node in root.iter() if local_tag(node.tag) == "TBL"]
    if tables:
        diagnostics.append(
            {
                "unit_id": f"Annex.{section_id}/TBL",
                "reason": "annex contains <TBL>; table cells are not emitted as provisions",
            }
        )
        if chart is not None:
            for table in tables:
                chart.uncovered(element_text(table, chart=chart), reason="TBL")
    provisions = _provisions_from_annex(root, chart=chart)
    return {
        "section_id": section_id,
        "kind": "annex",
        "file": str(part["file"]),
        "provisions": provisions,
        "diagnostics": diagnostics,
    }


def _find_article(root: ET.Element, article_no: str) -> ET.Element | None:
    for article in root.iter():
        if local_tag(article.tag) != "ARTICLE":
            continue
        ti = element_text(article.find("TI.ART"))
        match = re.search(r"(\d+)", ti or "")
        number = match.group(1) if match else (article.get("IDENTIFIER") or "").lstrip("0")
        if number == article_no:
            return article
    return None


def _provisions_from_article(article: ET.Element, article_no: str, chart=None) -> list[dict]:
    provisions: list[dict] = []
    paragraphs = [child for child in list(article) if local_tag(child.tag) == "PARAG"]
    if not paragraphs:
        text = element_text(article, chart=chart)
        if text:
            provisions.append({"locus": article_no, "law_text": wrap_law(text)})
            if chart is not None:
                chart.own(text, locus=article_no, parent=None)
        return provisions
    for parag in paragraphs:
        para_no = _para_number(parag)
        locus = f"{article_no}({para_no})" if para_no else article_no
        # Prefer leaf list items under the paragraph when present.
        items = _top_list_items(parag)
        if items:
            preamble = _preamble_before_list(parag, chart=chart)
            if chart is not None and preamble:
                chart.own(preamble, locus=locus, parent=article_no)
            for item in items:
                letter = _normalize_letter(_marker(item))
                item_text = _item_body(item, chart=chart)
                if letter:
                    item_locus = (
                        f"{article_no}({para_no})({letter})"
                        if para_no
                        else f"{article_no}({letter})"
                    )
                    law = (
                        f"{preamble}\n({letter}) {item_text}"
                        if preamble
                        else f"({letter}) {item_text}"
                    )
                    provisions.append({"locus": item_locus, "law_text": wrap_law(law)})
                else:
                    point = _normalize_point(_marker(item))
                    item_locus = (
                        f"{article_no}({para_no})({point})"
                        if para_no and point
                        else locus
                    )
                    provisions.append({"locus": item_locus, "law_text": wrap_law(item_text)})
                if chart is not None and item_text:
                    chart.own(item_text, locus=item_locus, parent=locus)
            if chart is not None:
                rest = _after_list_in(parag, chart=chart)
                if rest:
                    chart.uncovered(rest, reason="text after list")
            continue
        body = _paragraph_body(parag, chart=chart)
        provisions.append({"locus": locus, "law_text": wrap_law(body)})
        if chart is not None and body:
            chart.own(body, locus=locus, parent=article_no)
    return _unique_loci(provisions)


def _provisions_from_annex(root: ET.Element, chart=None) -> list[dict]:
    """Emit one provision per lettered clause, or per numbered point without letters.

    Matches the CRA text atomizer's Annex VII grain: parents with children are
    not separate provisions.
    """
    contents = root.find("CONTENTS")
    scope = contents if contents is not None else root
    top_lists = [child for child in list(scope) if local_tag(child.tag) == "LIST"]
    if not top_lists:
        # Some annexes wrap lists deeper under P.
        top_lists = [node for node in scope.iter() if local_tag(node.tag) == "LIST"]
        # Prefer shallowest lists only: those whose parent is CONTENTS or P under CONTENTS.
        filtered = []
        parents = _parent_map(scope)
        for node in top_lists:
            parent = parents.get(id(node))
            if parent is None:
                continue
            ptag = local_tag(parent.tag)
            if ptag in {"CONTENTS", "ANNEX"}:
                filtered.append(node)
            elif ptag == "P":
                gp = parents.get(id(parent))
                if gp is not None and local_tag(gp.tag) in {"CONTENTS", "ANNEX"}:
                    filtered.append(node)
        top_lists = filtered
    provisions: list[dict] = []
    for lst in top_lists:
        for item in [child for child in list(lst) if local_tag(child.tag) == "ITEM"]:
            provisions.extend(_provisions_from_annex_item(item, chart=chart))
    return _unique_loci(provisions)


def _provisions_from_annex_item(item: ET.Element, chart=None) -> list[dict]:
    marker = _marker(item)
    point = _normalize_point(marker)
    preamble = _item_intro(item, chart=chart)
    child_items = _nested_alpha_items(item)
    if child_items:
        if chart is not None and preamble:
            chart.own(preamble, locus=point or marker, parent=None)
        out = []
        for child in child_items:
            letter = _normalize_letter(_marker(child))
            body = _item_body(child, chart=chart)
            law = f"{preamble}\n({letter}) {body}" if preamble else f"({letter}) {body}"
            locus = f"{point}({letter})"
            out.append({"locus": locus, "law_text": wrap_law(law)})
            if chart is not None and body:
                chart.own(body, locus=locus, parent=point or None)
        if chart is not None:
            rest = _after_list_in(item, chart=chart)
            if rest:
                chart.uncovered(rest, reason="text after list")
        return out
    if not point:
        return []
    if chart is not None and preamble:
        chart.own(preamble, locus=point, parent=None)
    return [{"locus": point, "law_text": wrap_law(preamble)}]


def _nested_alpha_items(item: ET.Element) -> list[ET.Element]:
    nested: list[ET.Element] = []
    for node in item.iter():
        if local_tag(node.tag) != "LIST":
            continue
        # Only the first nested list under this item (direct descendant lists).
        parents = _parent_map(item)
        parent = parents.get(id(node))
        # LIST may sit under P under NP/ITEM
        depth_ok = False
        cur = parent
        for _ in range(4):
            if cur is None:
                break
            if cur is item:
                depth_ok = True
                break
            cur = parents.get(id(cur))
        if not depth_ok:
            continue
        for child in list(node):
            if local_tag(child.tag) == "ITEM":
                letter = _normalize_letter(_marker(child))
                if letter:
                    nested.append(child)
        if nested:
            return nested
    return nested


def _item_intro(item: ET.Element, chart=None) -> str:
    """Point body text without copying ``NO.P`` numbering into ``law_text``.

    Locators keep the point number (``3``, ``1(a)``). The Formex ``NO.P``
    marker must not be duplicated inside the passage.
    """
    return _item_body(item, chart=chart)


def _item_body(item: ET.Element, chart=None) -> str:
    np = item.find("NP")
    if np is None:
        return element_text(item, chart=chart)
    txt = np.find("TXT")
    if txt is not None:
        return element_text(txt, chart=chart)
    # Fall back without NO.P marker.
    parts = []
    for child in list(np):
        if local_tag(child.tag) == "NO.P":
            continue
        parts.append(element_text(child, chart=chart))
    return collapse_ws(" ".join(parts)) or element_text(np, chart=chart)


def _marker(item: ET.Element) -> str:
    no = item.find("NP/NO.P")
    return element_text(no)


def _normalize_point(marker: str) -> str:
    marker = collapse_ws(marker)
    match = re.match(r"^(\d+)\.?$", marker)
    return match.group(1) if match else ""


def _normalize_letter(marker: str) -> str:
    marker = collapse_ws(marker)
    match = re.match(r"^\(?([a-z])\)?\.?$", marker)
    return match.group(1) if match else ""


def _para_number(parag: ET.Element) -> str:
    no = element_text(parag.find("NO.PARAG"))
    match = re.match(r"^(\d+)\.?$", collapse_ws(no))
    if match:
        return match.group(1)
    ident = parag.get("IDENTIFIER") or ""
    if "." in ident:
        return ident.split(".")[-1].lstrip("0") or ident.split(".")[-1]
    return ""


def _top_list_items(parag: ET.Element) -> list[ET.Element]:
    for child in parag.iter():
        if local_tag(child.tag) != "LIST":
            continue
        return [item for item in list(child) if local_tag(item.tag) == "ITEM"]
    return []


def _preamble_before_list(parag: ET.Element, chart=None) -> str:
    chunks = []
    for child in list(parag):
        if local_tag(child.tag) == "LIST":
            break
        if local_tag(child.tag) == "NO.PARAG":
            continue
        if local_tag(child.tag) == "ALINEA":
            chunks.append(_alinea_preamble(child, chart=chart))
            if any(local_tag(node.tag) == "LIST" for node in child.iter()):
                break
    return collapse_ws(" ".join(chunk for chunk in chunks if chunk))


def _alinea_preamble(alinea: ET.Element, chart=None) -> str:
    parts: list[str] = []
    if alinea.text:
        parts.append(alinea.text)
    for child in list(alinea):
        if local_tag(child.tag) == "LIST":
            break
        parts.append(element_text(child, chart=chart))
        if child.tail:
            parts.append(child.tail)
    return collapse_ws("".join(parts))


def _paragraph_body(parag: ET.Element, chart=None) -> str:
    chunks = []
    for child in list(parag):
        if local_tag(child.tag) == "NO.PARAG":
            continue
        chunks.append(element_text(child, chart=chart))
    return collapse_ws(" ".join(chunks)) or element_text(parag, chart=chart)


def _after_list_in(node: ET.Element, chart=None) -> str:
    """Visible text that follows the first list under ``node``."""
    chunks: list[str] = []

    def walk(current: ET.Element) -> None:
        seen = False
        for child in list(current):
            if local_tag(child.tag) == "LIST":
                seen = True
                if child.tail:
                    chunks.append(child.tail)
                continue
            if seen:
                chunks.append(element_text(child, chart=chart))
                if child.tail:
                    chunks.append(child.tail)
                continue
            walk(child)

    walk(node)
    return collapse_ws("".join(chunks))


def _parent_map(root: ET.Element) -> dict[int, ET.Element]:
    parents: dict[int, ET.Element] = {}
    for parent in root.iter():
        for child in list(parent):
            parents[id(child)] = parent
    return parents


def _unique_loci(provisions: list[dict]) -> list[dict]:
    seen: dict[str, int] = {}
    out = []
    for item in provisions:
        locus = item["locus"]
        if locus in seen:
            seen[locus] += 1
            locus = f"{locus}~{seen[locus]}"
            item = {"locus": locus, "law_text": item["law_text"]}
        else:
            seen[locus] = 1
        out.append(item)
    return out
