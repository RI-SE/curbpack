"""Load pinned Formex packages and verify their recorded identity."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json

OFFICIAL_XML = Path(__file__).resolve().parents[1] / "data" / "official_xml"

_ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")


def load_manifest(path: Path | None = None) -> dict:
    manifest_path = path or (OFFICIAL_XML / "MANIFEST.json")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), list):
        raise ModelError("official_xml", "MANIFEST.json", "an object with sources[]")
    return manifest


def verify_source_bytes(celex: str, *, root: Path | None = None) -> dict:
    """Check every recorded file hash for one CELEX. Never writes source files."""
    base = root or OFFICIAL_XML
    source = _source_entry(celex)
    mismatches = []
    checked = 0
    for entry in source.get("files") or []:
        rel = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            raise ModelError(celex, "files[]", "path and sha256 strings")
        path = base / rel
        checked += 1
        if not path.is_file():
            mismatches.append({"path": rel, "error": "missing"})
            continue
        actual = _sha256(path)
        if actual != expected:
            mismatches.append({"path": rel, "expected": expected, "actual": actual})
    return {"ok": not mismatches, "celex": celex, "checked": checked, "mismatches": mismatches}


def load_doc_package(directory: Path) -> dict:
    """Open a Formex DOC package directory and list body + annex parts in order."""
    directory = directory.resolve()
    if not directory.is_dir():
        raise ModelError("formex package", "directory", f"an existing directory ({directory})")
    doc_path = _find_doc(directory)
    root = ET.parse(doc_path).getroot()
    if _local(root.tag) != "DOC":
        raise ModelError(doc_path.name, "root", "DOC")
    fmx = root.find("FMX")
    if fmx is None:
        raise ModelError(doc_path.name, "FMX", "present")
    language = _text(fmx.find("DOC.MAIN.PUB/LG.DOC")) or ""
    legal_value = _text(fmx.find("DOC.MAIN.PUB/LEGAL.VALUE")) or ""
    title = _document_title(root)
    parts = []
    main = fmx.find("DOC.MAIN.PUB")
    if main is not None:
        parts.append(_part_from_pub(directory, main, kind="body", section_id="_body", title=title))
    annex_index = 0
    for sub in fmx.findall("DOC.SUB.PUB"):
        if (sub.get("TYPE") or "").upper() != "ANNEX":
            # Account for non-annex sub-publications explicitly.
            parts.append(
                {
                    "kind": "unsupported_sub_pub",
                    "section_id": f"_sub:{sub.get('NO.SEQ') or annex_index}",
                    "title": "",
                    "file": _resolve_ref(directory, sub),
                    "supported": False,
                    "reason": f"DOC.SUB.PUB TYPE={sub.get('TYPE')!r} is not ANNEX",
                }
            )
            continue
        section_id = _ROMAN[annex_index] if annex_index < len(_ROMAN) else str(annex_index + 1)
        annex_index += 1
        file_path = _resolve_ref(directory, sub)
        parts.append(
            {
                "kind": "annex",
                "section_id": section_id,
                "title": _annex_title(file_path),
                "file": file_path,
                "supported": True,
                "reason": None,
            }
        )
    return {
        "directory": directory,
        "doc_file": doc_path,
        "language": language,
        "legal_value": legal_value,
        "title": title,
        "parts": parts,
    }


def _source_entry(celex: str) -> dict:
    for item in load_manifest().get("sources") or []:
        if isinstance(item, dict) and item.get("celex") == celex:
            return item
    raise ModelError("official_xml", "celex", f"a recorded source, not {celex}")


def _find_doc(directory: Path) -> Path:
    candidates = sorted(directory.glob("*.doc.fmx.xml")) + sorted(directory.glob("*.doc.xml"))
    # Prefer explicit .doc. naming; avoid matching body files.
    docs = [path for path in candidates if ".doc." in path.name or path.name.endswith(".doc.xml")]
    if len(docs) != 1:
        raise ModelError(directory.name, "DOC", f"exactly one DOC entry file, found {len(docs)}")
    return docs[0]


def _part_from_pub(
    directory: Path,
    element: ET.Element,
    *,
    kind: str,
    section_id: str,
    title: str,
) -> dict:
    return {
        "kind": kind,
        "section_id": section_id,
        "title": title,
        "file": _resolve_ref(directory, element),
        "supported": True,
        "reason": None,
    }


def _resolve_ref(directory: Path, element: ET.Element) -> Path:
    ref = element.find("REF.PHYS")
    if ref is None or not ref.get("FILE"):
        raise ModelError(directory.name, "REF.PHYS/@FILE", "a file name")
    path = directory / ref.get("FILE")
    if not path.is_file():
        raise ModelError(directory.name, "REF.PHYS/@FILE", f"an existing file ({ref.get('FILE')})")
    return path


def _document_title(doc_root: ET.Element) -> str:
    for path in ("PDF/ITEM.VOLUME/TITLE/TI", "PAPER/VOLUME.PAPER/ITEM.VOLUME/TITLE/TI"):
        node = doc_root.find(path)
        if node is not None:
            return _collapse("".join(node.itertext()))
    return ""


def _annex_title(path: Path) -> str:
    root = ET.parse(path).getroot()
    chunks = []
    title = root.find("TITLE")
    if title is None:
        return path.name
    for child in title:
        if _local(child.tag) in {"TI", "STI"}:
            chunks.append(_collapse("".join(child.itertext())))
    return " — ".join(chunk for chunk in chunks if chunk) or path.name


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _collapse(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()
