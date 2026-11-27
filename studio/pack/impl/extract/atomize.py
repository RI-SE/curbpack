"""Step 01 — split annex prose into locus + law_text.

The splitting rules are the ones in poc/components/transform/steps/01_atomize.py.
They are copied here so PoC2 does not import poc at runtime. Temporary atoms
are not Requirements.
"""

from __future__ import annotations

import re
import textwrap

PART_RE = re.compile(r"(?m)^(Part\s+([IVXLCDM]+|[0-9]+))\b[^\n]*$")
INT_POINT_RE = re.compile(r"(?m)^(\d+)\.\s*$")
SUB_POINT_RE = re.compile(r"(?m)^(\d+\.\d+)\.\s*$")
PAREN_POINT_RE = re.compile(r"(?m)^\((\d+)\)\s*$")
LETTER_RE = re.compile(r"(?m)^\(([a-z])\)\s*$")
FOOTNOTE_LINE_RE = re.compile(r"(?is)^(OJ\s+L\b|ELI:\s*http|^\(\d+\)\s*OJ\b)")


class ExtractError(ValueError):
    pass


def wrap_law(text: str, width: int = 78) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return textwrap.fill(text, width=width, break_long_words=False, break_on_hyphens=False)


def normalize_annex(raw: str, chart=None) -> str:
    """Flatten EUR-Lex HTML dumps and keep a single annex body."""
    raw = raw.replace("\t", " ").replace("\xa0", " ")
    heads = list(re.finditer(r"(?m)^ANNEX\s+[IVXLCDM]+\s*$", raw))
    if len(heads) >= 2:
        if chart is not None:
            chart.uncovered(raw[heads[1].start() :], reason="text after next ANNEX")
        raw = raw[: heads[1].start()]
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.splitlines()]
    merged: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if i + 1 < len(lines) and re.fullmatch(r"Annex\s+[IVXLCDM]+", lines[i + 1], flags=re.I):
            nxt = lines[i + 1]
            fol = lines[i + 2] if i + 2 < len(lines) else ""
            if fol in {";", ".", ",", "and", "or"}:
                ln = f"{ln} {nxt}{fol}".replace("  ", " ")
                i += 3
            else:
                ln = f"{ln} {nxt}".rstrip()
                i += 2
            merged.append(ln)
            continue
        merged.append(ln)
        i += 1
    raw = "\n".join(merged)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip() + "\n"


def strip_trailing_footnotes(text: str, chart=None) -> str:
    """Drop EUR-Lex footnote tails like '(1)\\nOJ L, …'."""
    lines = text.splitlines()
    cut = len(lines)
    for i, ln in enumerate(lines):
        if re.fullmatch(r"\(\d+\)", ln.strip()) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if FOOTNOTE_LINE_RE.match(nxt) or nxt.startswith("OJ L"):
                cut = i
                break
        if ln.strip().startswith("OJ L,") and "ELI:" in ln:
            if i > 0 and re.fullmatch(r"\(\d+\)", lines[i - 1].strip()):
                cut = i - 1
                break
    if chart is not None and cut < len(lines):
        dropped = "\n".join(lines[cut:]).strip()
        if dropped:
            chart.uncovered(dropped, reason="footnote tail")
    return "\n".join(lines[:cut]).strip()


def split_parts(text: str) -> list[tuple[str | None, str]]:
    _leading, parts = _part_spans(text)
    return [(part_id, body) for part_id, _heading, body in parts]


def _part_spans(text: str) -> tuple[str, list[tuple[str | None, str, str]]]:
    """Return title text before the first Part, then ``(part id, heading, body)``."""
    matches = list(PART_RE.finditer(text))
    if not matches:
        return "", [(None, "", text)]
    out: list[tuple[str | None, str, str]] = []
    preamble = text[: matches[0].start()].strip()
    leading = ""
    if preamble and (INT_POINT_RE.search(preamble) or PAREN_POINT_RE.search(preamble)):
        out.append((None, "", preamble))
    else:
        leading = preamble
    for i, match in enumerate(matches):
        part_id = match.group(2).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((part_id, match.group(0).strip(), text[start:end].strip()))
    return leading, out


def split_marker_blocks(body: str, pattern: re.Pattern[str]) -> list[tuple[str, str]]:
    parts = pattern.split(body)
    out: list[tuple[str, str]] = []
    i = 1
    while i + 1 < len(parts):
        out.append((parts[i].strip(), parts[i + 1].strip()))
        i += 2
    return out


def looks_like_footnote_annex(body: str) -> bool:
    if INT_POINT_RE.search(body):
        return False
    if not PAREN_POINT_RE.findall(body):
        return False
    blocks = split_marker_blocks(body, PAREN_POINT_RE)
    if not blocks:
        return False
    substantive = 0
    for _, text in blocks:
        stripped = text.strip()
        if not stripped or stripped.startswith("OJ L") or stripped.startswith("ELI:"):
            continue
        if len(stripped) >= 40:
            substantive += 1
    return substantive == 0


_HEADING_LINE = re.compile(
    r"ANNEX\s+[IVXLCDM]+|SIMPLIFIED EU DECLARATION OF CONFORMITY|"
    r"EU DECLARATION OF CONFORMITY|ESSENTIAL CYBERSECURITY REQUIREMENTS",
    re.I,
)


def _uncover_preamble(preamble: str, chart) -> None:
    """Record a title or a governing sentence that is not itself a point."""
    if chart is None:
        return
    headings: list[str] = []
    rest: list[str] = []
    for line in preamble.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _HEADING_LINE.fullmatch(stripped):
            headings.append(stripped)
        else:
            rest.append(stripped)
    for line in headings:
        chart.uncovered(line, reason="heading")
    prose = "\n".join(rest).strip()
    if prose:
        chart.uncovered(prose, reason="text before points")


def _mark_preamble(body: str, pattern: re.Pattern[str], chart) -> None:
    if chart is None:
        return
    match = pattern.search(body)
    if match is None or match.start() == 0:
        return
    _uncover_preamble(body[: match.start()], chart)


def split_top_points(body: str, chart=None) -> list[tuple[str, str]]:
    body = strip_trailing_footnotes(body, chart=chart)
    if INT_POINT_RE.search(body):
        blocks = split_marker_blocks(body, INT_POINT_RE)
        if blocks:
            _mark_preamble(body, INT_POINT_RE, chart)
            return blocks
    if PAREN_POINT_RE.search(body) and not looks_like_footnote_annex(body):
        blocks = split_marker_blocks(body, PAREN_POINT_RE)
        if blocks:
            _mark_preamble(body, PAREN_POINT_RE, chart)
            return [(num, strip_trailing_footnotes(text, chart=chart)) for num, text in blocks]
    cleaned = strip_trailing_footnotes(body, chart=chart)
    lines = []
    for ln in cleaned.splitlines():
        stripped = ln.strip()
        if not stripped:
            continue
        if _HEADING_LINE.fullmatch(stripped):
            if chart is not None:
                chart.uncovered(stripped, reason="heading")
            continue
        lines.append(ln)
    prose = "\n".join(lines).strip()
    if prose:
        return [("1", prose)]
    raise ExtractError("could not find operable text to atomize")


def expand_subpoints(num: str, text: str) -> list[tuple[str, str]]:
    if not SUB_POINT_RE.search(text):
        return [(num, text)]
    parent = num.split(".")[0]
    parts = SUB_POINT_RE.split(text)
    preamble = parts[0].strip()
    out: list[tuple[str, str]] = []
    if preamble:
        out.append((num, preamble))
    i = 1
    while i + 1 < len(parts):
        sub, body = parts[i].strip(), parts[i + 1].strip()
        out.append((sub, body))
        i += 2
    return out or [(num, text)]


def split_lettered(text: str) -> tuple[str, list[tuple[str, str]]]:
    parts = LETTER_RE.split(text)
    if len(parts) < 3:
        return text.strip(), []
    preamble = parts[0].strip()
    children: list[tuple[str, str]] = []
    i = 1
    while i + 1 < len(parts):
        children.append((parts[i].strip(), parts[i + 1].strip()))
        i += 2
    return preamble, children


def build_law_text(preamble: str, letter: str | None, clause: str) -> str:
    if letter is None:
        return wrap_law(clause if not preamble else f"{preamble} {clause}".strip())
    head = wrap_law(preamble.rstrip()) if preamble else ""
    letter_block = wrap_law(f"({letter}) {clause}")
    if head:
        return f"{head}\n{letter_block}"
    return letter_block


def locus_for(part: str | None, num: str, letter: str | None = None) -> str:
    base = f"{part}-{num}" if part else num
    if letter:
        return f"{base}({letter})"
    return base


def atomize(raw: str, chart=None) -> list[dict]:
    text = normalize_annex(raw, chart=chart)
    atoms: list[dict] = []
    seen: set[str] = set()
    leading, parts = _part_spans(text)
    if leading.strip():
        _uncover_preamble(leading, chart)
    for part, heading, part_body in parts:
        if chart is not None and heading.strip():
            chart.uncovered(heading.strip(), reason="heading")
        for num, body in split_top_points(part_body, chart=chart):
            for sub_num, sub_body in expand_subpoints(num, body):
                preamble, children = split_lettered(sub_body)
                parent = locus_for(part, sub_num)
                if children:
                    if chart is not None and preamble:
                        chart.own(preamble, locus=parent, parent=part)
                    for letter, clause in children:
                        loc = locus_for(part, sub_num, letter)
                        if loc in seen:
                            loc = f"{loc}~{len(seen)}"
                        seen.add(loc)
                        atoms.append(
                            {
                                "locus": loc,
                                "part": part,
                                "parent_point": sub_num,
                                "law_text": build_law_text(preamble, letter, clause),
                            }
                        )
                        if chart is not None and clause:
                            chart.own(clause, locus=loc, parent=parent)
                else:
                    loc = locus_for(part, sub_num)
                    if loc in seen:
                        loc = f"{loc}~{len(seen)}"
                    seen.add(loc)
                    kept = preamble
                    atoms.append(
                        {
                            "locus": loc,
                            "part": part,
                            "parent_point": sub_num,
                            "law_text": build_law_text("", None, kept),
                        }
                    )
                    if chart is not None and kept:
                        chart.own(kept, locus=loc, parent=part)
    return atoms
