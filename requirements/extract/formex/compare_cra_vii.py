"""Compare CRA Annex VII text-fixture atomize output with Formex provisions."""

from __future__ import annotations

import json
import re
from pathlib import Path

from common.paths import install_root
from requirements.extract.atomize import atomize
from requirements.extract.formex.package import OFFICIAL_XML
from requirements.extract.formex.provisions import extract_section_provisions
from requirements.extract.formex.text import collapse_ws

DATA = install_root() / "requirements" / "extract" / "data"
ANNEX_VII_TXT = DATA / "annex_vii.txt"
COMPARE_DIR = OFFICIAL_XML / "compare"


def _display_path(path: Path | str) -> str:
    candidate = Path(path)
    root = install_root()
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def compare_annex_vii() -> dict:
    text_provisions = [
        {"locus": item["locus"], "law_text": item["law_text"]}
        for item in atomize(ANNEX_VII_TXT.read_text(encoding="utf-8"))
    ]
    xml_result = extract_section_provisions(OFFICIAL_XML / "cra", "VII")
    xml_provisions = xml_result["provisions"]
    text_by = {item["locus"]: item["law_text"] for item in text_provisions}
    xml_by = {item["locus"]: item["law_text"] for item in xml_provisions}
    all_loci = sorted(set(text_by) | set(xml_by), key=_locus_sort)
    structural = {
        "text_only_loci": [locus for locus in all_loci if locus not in xml_by],
        "xml_only_loci": [locus for locus in all_loci if locus not in text_by],
        "shared_loci": [locus for locus in all_loci if locus in text_by and locus in xml_by],
    }
    exact = []
    normalized = []
    for locus in structural["shared_loci"]:
        left = text_by[locus]
        right = xml_by[locus]
        exact_match = left == right
        norm_match = _norm(left) == _norm(right)
        entry = {
            "locus": locus,
            "exact_match": exact_match,
            "normalized_match": norm_match,
            "text_law_text": left,
            "xml_law_text": right,
        }
        if not exact_match:
            exact.append(entry)
        if not norm_match:
            normalized.append(entry)
        elif exact_match:
            pass
    report = {
        "section": "VII",
        "text_source": _display_path(ANNEX_VII_TXT),
        "xml_source": _display_path(xml_result["file"]),
        "text_count": len(text_provisions),
        "xml_count": len(xml_provisions),
        "structural": structural,
        "exact_text_differences": exact,
        "normalization_differences": normalized,
        "exact_matches": [
            locus
            for locus in structural["shared_loci"]
            if text_by[locus] == xml_by[locus]
        ],
        "normalized_only_matches": [
            locus
            for locus in structural["shared_loci"]
            if text_by[locus] != xml_by[locus] and _norm(text_by[locus]) == _norm(xml_by[locus])
        ],
        "genuine_wording_differences": [
            locus
            for locus in structural["shared_loci"]
            if _norm(text_by[locus]) != _norm(xml_by[locus])
        ],
        "counts": {
            "shared_loci": len(structural["shared_loci"]),
            "exact_matches": sum(
                1 for locus in structural["shared_loci"] if text_by[locus] == xml_by[locus]
            ),
            "normalization_only_matches": sum(
                1
                for locus in structural["shared_loci"]
                if text_by[locus] != xml_by[locus]
                and _norm(text_by[locus]) == _norm(xml_by[locus])
            ),
            "genuine_wording_differences": sum(
                1
                for locus in structural["shared_loci"]
                if _norm(text_by[locus]) != _norm(xml_by[locus])
            ),
        },
        "unresolved_questions": [
            "Locus 1(d) differs in wording (fixture 'the information…' vs Formex TXT 'user information…'). The controlled text fixture is left unchanged until independently verified against the official OJ/PDF; Formex is not treated as automatic ground truth.",
            "Normalized equality is not semantic equivalence.",
            "Text atomizer wraps at 78 columns; Formex extraction collapses whitespace then rewraps — exact-byte mismatches can be formatting-only.",
            "EUR-Lex HTML notice retrieval was WAF-blocked; XML identity is CELLAR Formex ZIP checksums in MANIFEST.json.",
        ],
    }
    return report


def write_compare_artifacts() -> dict:
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    report = compare_annex_vii()
    machine = COMPARE_DIR / "cra_annex_vii_text_vs_xml.json"
    human = COMPARE_DIR / "cra_annex_vii_text_vs_xml.md"
    machine.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    human.write_text(_summary_markdown(report), encoding="utf-8")
    return {"report": report, "json": machine, "markdown": human}


def _summary_markdown(report: dict) -> str:
    structural = report["structural"]
    counts = report["counts"]
    lines = [
        "# CRA Annex VII — text fixture vs Formex XML",
        "",
        f"- Text provisions: {report['text_count']}",
        f"- XML provisions: {report['xml_count']}",
        f"- Shared loci: {counts['shared_loci']}",
        f"- Exact matches: {counts['exact_matches']}",
        f"- Normalization-only matches: {counts['normalization_only_matches']}",
        f"- Genuine wording differences: {counts['genuine_wording_differences']}",
        f"- Exact-text differences (includes wrap-only): {len(report['exact_text_differences'])}",
        "",
        "## Structural",
        "",
        f"- Text-only loci: {', '.join(structural['text_only_loci']) or 'none'}",
        f"- XML-only loci: {', '.join(structural['xml_only_loci']) or 'none'}",
        f"- Shared loci: {', '.join(structural['shared_loci'])}",
        "",
        "## Classification",
        "",
        "Normalized string equality is **not** a claim of semantic equivalence.",
        "The text fixture is unchanged pending independent verification of locus `1(d)`.",
        "",
        f"- Exact: {', '.join(report['exact_matches']) or 'none'}",
        f"- Normalization only: {', '.join(report['normalized_only_matches']) or 'none'}",
        f"- Genuine wording: {', '.join(report['genuine_wording_differences']) or 'none'}",
        "",
        "## Unresolved parsing questions",
        "",
    ]
    for item in report["unresolved_questions"]:
        lines.append(f"- {item}")
    lines.append("")
    if report["exact_text_differences"]:
        lines.extend(["## Exact-text differences (sample)", ""])
        for entry in report["exact_text_differences"][:5]:
            lines.append(f"### Locus `{entry['locus']}`")
            lines.append("")
            lines.append(f"- normalized_match: {entry['normalized_match']}")
            lines.append(f"- text: `{entry['text_law_text'][:200]}`")
            lines.append(f"- xml: `{entry['xml_law_text'][:200]}`")
            lines.append("")
    return "\n".join(lines)


def _norm(text: str) -> str:
    text = collapse_ws(text)
    text = text.replace("(a)", "").replace("(b)", "").replace("(c)", "").replace("(d)", "")
    return re.sub(r"[^\w]+", "", text.lower())


def _locus_sort(locus: str) -> tuple:
    match = re.match(r"^(\d+)(?:\(([a-z])\))?$", locus)
    if not match:
        return (999, locus)
    return (int(match.group(1)), match.group(2) or "")
