"""Step review for one adapter run. Run from anywhere:

    python3 adapter-studio/server.py

Page one picks an adapter and a URL, the same pairing as Add Pack Source,
then calls chart_run. Each later page is one extract step, 00 through 04.
Step 04 is the pack editor's requirements page.
A click on a 01 cut hands a prompt to Cursor through its prompt deeplink.
Steps 02 and 03 call the model the first time those pages open, then cache the result.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import unicodedata
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.errors import ModelError
from discovery.search import highlight_verified
from requirements.extract.adapter import (
    ADAPTERS,
    formex_package_dir,
    is_formex_adapter,
    list_adapters,
    load_adapter,
    load_doc_package,
)
from requirements.extract.chart import chart_run
from requirements.extract.formex.text import collapse_ws, element_text, local_tag

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
INBOX = HERE / "inbox"
HOST = "127.0.0.1"
PORT = 8766
_CHART_NAME = re.compile(r"^sourcechart-[A-Za-z0-9._-]+$")
_CHART_ADAPTER = re.compile(r"^sourcechart-(.+)-(\d{4}-\d{2}-\d{2}T\d{6}Z(?:-\d+)?)$")
_MAX_NOTE = 2000
_MAX_URL = 9000
STEPS = (
    ("00", "Structure"),
    ("01", "Atomize"),
    ("02", "Interpret"),
    ("03", "Discovery hints"),
    ("04", "Assemble"),
)
_STEPS_LOCK = threading.Lock()
_STEP_THREADS: dict[str, threading.Thread] = {}


def choices() -> list[dict]:
    """Adapters that can actually cut, with the URL Add Pack Source would fill in."""
    rows = []
    for item in list_adapters():
        if item.get("status") == "stub":
            continue
        ready = [
            section
            for section in item.get("sections") or []
            if section.get("ready") is True and section.get("in_scope") is True
        ]
        if not ready:
            continue
        source = item.get("source") or {}
        rows.append(
            {
                "id": item["id"],
                "instrument": source.get("instrument") or item["id"],
                "url": source.get("url") or "",
                "source_format": item.get("source_format") or "text",
            }
        )
    return rows


def _chart_dir(name: str) -> Path:
    if not _CHART_NAME.fullmatch(name):
        raise FileNotFoundError(name)
    path = (RUNS / name).resolve()
    if not path.is_relative_to(RUNS.resolve()) or not (path / "sourcechart.json").is_file():
        raise FileNotFoundError(name)
    return path


def _load(name: str) -> tuple[dict, str]:
    directory = _chart_dir(name)
    document = json.loads((directory / "sourcechart.json").read_text(encoding="utf-8"))
    snapshot = (directory / "snapshot.txt").read_text(encoding="utf-8")
    return document, snapshot


def blocks(document: dict, snapshot: str) -> list[dict]:
    cuts = document["cuts"]
    unassigned = document.get("unassigned") or {}
    owners: dict[int, dict] = {}
    for unit in document.get("units") or []:
        for index in unit.get("blocks") or []:
            owners[index] = unit
    rows = []
    for index in range(len(cuts) - 1):
        start, end = cuts[index], cuts[index + 1]
        text = snapshot[start:end]
        dropped = unassigned.get(str(index))
        if dropped:
            rows.append(
                {
                    "index": index,
                    "start": start,
                    "end": end,
                    "text": text,
                    "status": dropped[0],
                    "reason": dropped[1] if len(dropped) > 1 else "",
                    "locus": "",
                    "parent": "",
                }
            )
            continue
        unit = owners.get(index) or {}
        rows.append(
            {
                "index": index,
                "start": start,
                "end": end,
                "text": text,
                "status": "own",
                "reason": "",
                "locus": unit.get("locator") or unit.get("id") or "",
                "parent": unit.get("parent") or "",
            }
        )
    return rows


def _clean(text: str) -> str:
    """Keep only characters the Cursor prompt deeplink accepts."""
    kept = []
    for char in unicodedata.normalize("NFC", text):
        if char in "\r\n\t" or " " <= char <= "~":
            if char != "\x7f":
                kept.append(char)
            continue
        if unicodedata.category(char)[0] in "LMNPSZ":
            kept.append(char)
    return "".join(kept).strip()


def _fit(text: str) -> str:
    text = _clean(text)
    while text and 21 + len(quote(text, safe="")) > _MAX_URL:
        text = text[: max(0, len(text) - 200)].rstrip() + "\n…"
        text = _clean(text)
    return text


def section_prompt(name: str, section_id: str, note: str) -> str:
    adapter_id = _adapter_id(name)
    adapter = load_adapter(ADAPTERS / adapter_id / "adapter.json")
    section = next((item for item in adapter["sections"] if item.get("id") == section_id), None)
    if section is None:
        raise FileNotFoundError(section_id)
    _title, text, missing = _section_reading(name, section_id)
    flags = "in scope" if section.get("in_scope") else "out of scope"
    flags += ", ready" if section.get("ready") else ", not ready"
    excerpt = text.strip()[:1500]
    body = (
        f"Adapter-studio, run {name}.\n"
        f"Adapter {adapter_id}, section {section_id} — {section.get('title') or ''}.\n"
        f"{flags}.\n\n"
        f"Add code so the adapter can process this section.\n\n"
        f"Text:\n{excerpt or missing}\n\n"
        f"{note.strip()}"
    )
    fitted = _fit(body)
    if not fitted:
        raise ValueError("The prompt has no characters Cursor accepts.")
    return fitted


def prompt_text(name: str, index: int, note: str) -> str:
    document, snapshot = _load(name)
    row = blocks(document, snapshot)[index]
    source = document.get("source") or {}
    kind = "dropped" if row["status"] != "own" else "kept"
    where = row["locus"] or "no locus"
    reason = f", reason {row['reason']}" if row["reason"] else ""
    body = (
        f"Adapter-studio, run {name}.\n"
        f"Adapter {source.get('id') or ''}, source {source.get('url') or ''}.\n"
        f"Block {index} is {kind}{reason}. Locus: {where}. "
        f"Characters {row['start']}–{row['end']} in snapshot.txt.\n\n"
        f"Text:\n{row['text']}\n\n"
        f"{note.strip()}"
    )
    fitted = _fit(body)
    if not fitted:
        raise ValueError("The prompt has no characters Cursor accepts.")
    return fitted


def deeplink(text: str) -> str:
    return (
        "cursor://anysphere.cursor-deeplink/prompt?text="
        + quote(text, safe="")
        + "&workspace=curbpack"
    )


def hand_to_cursor(text: str) -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    (INBOX / "last-prompt.txt").write_text(text + "\n", encoding="utf-8")
    subprocess.run(["open", deeplink(text)], check=False)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_CSS = """
body { font: 16px/1.45 ui-sans-serif, system-ui, sans-serif; margin: 2rem auto; max-width: 76rem;
       color: #1c1c1c; background: #f7f6f3; }
a { color: #143d66; }
form, .chart, dialog { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 1rem 1.2rem; }
label { display: block; margin-top: 0.8rem; font-weight: 600; }
select, input, textarea { width: 100%; box-sizing: border-box; font: inherit; padding: 0.4rem; }
button { margin-top: 1rem; font: inherit; padding: 0.4rem 0.9rem; }
.error { color: #8a1f11; }
.chart { max-height: 70vh; overflow: auto; padding: 0; background: #fff; }
.atoms { width: 100%; border-collapse: separate; border-spacing: 0; }
.atoms th, .atoms td { text-align: left; vertical-align: top; padding: .45rem .6rem; border-right: 1px solid #7d766c; border-bottom: 1px solid #7d766c; }
.atoms th:first-child, .atoms td:first-child { border-left: 1px solid #7d766c; }
.atoms thead th { border-top: 1px solid #7d766c; }
.atoms th { position: sticky; top: 0; background: #fff; z-index: 1; }
.atoms td.point, .atoms td.letter { width: 2.2rem; white-space: nowrap; }
.atoms td.prior, .atoms th.prior { background: #eeeae4; }
.atoms tr.drop td { background: #ffe08a; text-decoration: line-through; }
.atoms tr.cut { cursor: pointer; }
.section { display: block; margin: 0; padding: .45rem .7rem; cursor: pointer; }
.sections { list-style: none; margin: 0; padding: 0; background: #fff; border: 1px solid #ddd; border-radius: 8px; overflow: auto; max-height: 50vh; }
.sections .section:nth-child(odd) { background: #d9e8f6; }
.sections .section:nth-child(even) { background: #e4d4f5; }
.band0 { background: #d9e8f6; }
.band1 { background: #e4d4f5; }
.drop { background: #ffe08a; color: #3d3208; text-decoration: line-through; }
.legend .swatch { padding: 0 .3rem; }
dialog { width: min(52rem, calc(100vw - 2rem)); max-width: none; }
dialog pre.doc { white-space: pre-wrap; max-height: 50vh; overflow: auto; background: #fff; border: 1px solid #ddd; padding: .6rem; }
dialog pre.doc mark { background: #ffe08a; color: inherit; }
.watching { margin-top: 0; }
nav.steps { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0 0 1rem; }
nav.steps a, nav.steps .here { padding: .2rem .55rem; border-radius: 999px; border: 1px solid #ddd; text-decoration: none; }
nav.steps .here { background: #143d66; color: #fff; }
.atom { border-top: 1px solid #e4e0d8; padding: .8rem 0; }
.atom h2 { font-size: 1rem; margin: 0 0 .35rem; }
.atom pre { white-space: pre-wrap; margin: 0; font: inherit; }
.muted { color: #5c5852; }
"""


def _page(title: str, body: str) -> bytes:
    html = (
        "<!doctype html><meta charset=utf-8>"
        f"<title>{_escape(title)}</title><style>{_CSS}</style>"
        f"<h1>{_escape(title)}</h1>{body}"
    )
    return html.encode("utf-8")


def _form(error: str = "") -> bytes:
    rows = choices()
    options = []
    urls = {}
    for row in rows:
        options.append(
            f'<option value="{_escape(row["id"])}">'
            f'{_escape(row["id"])} — {_escape(row["instrument"])}'
            f'</option>'
        )
        urls[row["id"]] = row["url"]
    previous = []
    if RUNS.is_dir():
        found = [
            path.name
            for path in sorted(RUNS.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
            if path.is_dir() and (path / "sourcechart.json").is_file()
        ]
        previous = [
            f'<li><a href="/chart/{_escape(name)}/00">{_escape(name)}</a></li>' for name in found[:12]
        ]
    error_html = f'<p class="error">{_escape(error)}</p>' if error else ""
    past = "<h2>Earlier runs</h2><ul>" + "".join(previous) + "</ul>" if previous else ""
    body = f"""
<p>Choose an adapter. The URL is filled in from the adapter, the same pair as Add Pack Source.
An empty URL uses the saved package. A Formex URL is fetched again.
After the run there is one page per step, 00 Structure through 04 Assemble.</p>
{error_html}
<form method="post" action="/run">
  <label for="adapter">Adapter</label>
  <select id="adapter" name="adapter">{''.join(options)}</select>
  <label for="url">URL</label>
  <input id="url" name="url" value="{_escape(urls.get(rows[0]["id"], "") if rows else "")}">
  <button type="submit">Run chart</button>
</form>
{past}
<script>
const urls = {json.dumps(urls)};
const adapter = document.querySelector("#adapter");
const url = document.querySelector("#url");
adapter.addEventListener("change", () => {{ url.value = urls[adapter.value] || ""; }});
</script>
"""
    return _page("Adapter-studio", body)


def _adapter_id(name: str) -> str:
    match = _CHART_ADAPTER.fullmatch(name)
    if match is None:
        raise FileNotFoundError(name)
    return match.group(1)


_FORMEX_SKIP = frozenset({"BIB.INSTANCE", "NOTE", "QUOT.START", "QUOT.END"})


def _lists_under_item(item: ET.Element) -> list[ET.Element]:
    """Lists that belong to this item, not to an item nested inside it."""
    found: list[ET.Element] = []

    def walk(node: ET.Element, under_list: bool) -> None:
        for child in list(node):
            tag = local_tag(child.tag)
            if tag == "ITEM":
                continue
            if tag == "LIST" and not under_list:
                found.append(child)
            walk(child, under_list or tag == "LIST")

    walk(item, False)
    return found


def _item_lead(item: ET.Element) -> str:
    """This item's own marker and text, without the nested list."""
    numbered = next((child for child in list(item) if local_tag(child.tag) == "NP"), None)
    if numbered is None:
        return element_text(item)
    parts: list[str] = []
    for child in list(numbered):
        tag = local_tag(child.tag)
        if tag == "LIST":
            continue
        if tag == "P":
            if child.text and child.text.strip():
                parts.append(child.text)
            for inner in list(child):
                if local_tag(inner.tag) != "LIST":
                    parts.append(element_text(inner))
            continue
        parts.append(element_text(child))
    return " ".join(parts)


def _readable_formex(xml_text: str) -> str:
    """The text the Formex cutter reads: tags gone, whitespace collapsed, one line per paragraph or item."""
    root = ET.fromstring(xml_text)
    lines: list[str] = []

    def add(text: str, depth: int) -> None:
        cleaned = collapse_ws(text)
        if cleaned:
            lines.append(f"{'  ' * depth}{cleaned}")

    def walk(node: ET.Element, depth: int) -> None:
        tag = local_tag(node.tag)
        if tag in _FORMEX_SKIP:
            return
        if tag == "ITEM":
            add(_item_lead(node), depth)
            for listing in _lists_under_item(node):
                for child in list(listing):
                    if local_tag(child.tag) == "ITEM":
                        walk(child, depth + 1)
            return
        if tag == "P":
            add(element_text(node), depth)
            return
        for child in list(node):
            walk(child, depth)

    walk(root, 0)
    return "\n".join(lines)


def _original(adapter_id: str) -> tuple[str, str]:
    """The source the cutter read. Formex is shown as that reading, not the tags."""
    adapter_dir = ADAPTERS / adapter_id
    adapter = load_adapter(adapter_dir / "adapter.json")
    ready = [
        section
        for section in adapter["sections"]
        if section.get("ready") is True and section.get("in_scope") is True
    ]
    if is_formex_adapter(adapter):
        package = load_doc_package(formex_package_dir(adapter_dir, adapter))
        wanted = {section["id"] for section in ready}
        files: list[Path] = []
        for part in package["parts"]:
            section_id = str(part.get("section_id") or "")
            file_path = Path(part["file"])
            if section_id in wanted or (section_id == "" and any(item.startswith("Art.") for item in wanted)):
                files.append(file_path)
            elif part.get("kind") == "body" and any(item.startswith("Art.") for item in wanted):
                files.append(file_path)
        seen: list[Path] = []
        for file_path in files:
            if file_path not in seen:
                seen.append(file_path)
        texts = [_readable_formex(path.read_text(encoding="utf-8", errors="replace")) for path in seen]
        return ", ".join(path.name for path in seen) + " · reading text", "\n\n".join(texts)
    names = []
    texts = []
    for section in ready:
        file_path = adapter_dir / str(section.get("fixture") or "")
        names.append(file_path.name)
        texts.append(file_path.read_text(encoding="utf-8"))
    return ", ".join(names), "\n\n".join(texts)


_LOCUS = re.compile(r"^(.+?)\(([a-z]+)\)$")


def _point_letter(locus: str) -> tuple[str, str]:
    match = _LOCUS.fullmatch(locus)
    if match is None:
        return locus, ""
    return match.group(1), match.group(2)


def _atoms_table(rows: list[dict], columns: list[tuple[str, bool]] | None = None) -> str:
    """columns are (header, already done). Done columns stay grey; new ones stay white."""
    columns = list(columns or [])
    carried = bool(columns)
    spec = [("point", carried), ("letter", carried), ("atom", carried), *columns]
    head = "".join(
        f'<th class="{"prior" if done else "added"}">{_escape(header)}</th>'
        for header, done in spec
    )
    body = []
    for row in rows:
        point, letter = _point_letter(row["locus"])
        kind = "drop" if row["status"] != "own" else ""
        click = "" if carried else "cut"
        values = [point, letter, row["text"], *(row.get("added") or [])]
        cells = []
        for index, ((header, done), value) in enumerate(zip(spec, values)):
            role = "prior" if done else "added"
            extra = " point" if index == 0 else " letter" if index == 1 else ""
            cells.append(f'<td class="{role}{extra}">{_escape(str(value))}</td>')
        body.append(
            f'<tr class="{click} {kind}" data-index="{row["index"]}" '
            f'data-start="{row["start"]}" data-end="{row["end"]}" '
            f'data-status="{_escape(row["status"])}" data-reason="{_escape(row["reason"])}" '
            f'data-locus="{_escape(row["locus"])}">{"".join(cells)}</tr>'
        )
    return (
        f'<table class="atoms"><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def _step_label(code: str) -> str:
    return dict(STEPS)[code]


def _run_context(name: str) -> tuple[str, str]:
    document, _snapshot = _load(name)
    source = document.get("source") or {}
    return _adapter_id(name), str(source.get("url") or "")


def _steps_nav(name: str, current: str) -> str:
    links = []
    for code, label in STEPS:
        text = f"{code} {label}"
        if code == current:
            links.append(f'<span class="here">{text}</span>')
            continue
        links.append(f'<a href="/chart/{_escape(name)}/{code}">{text}</a>')
    return '<nav class="steps">' + "".join(links) + "</nav>"


def _watching(adapter: str, url: str) -> str:
    shown = f'<a href="{_escape(url)}">{_escape(url)}</a>' if url else "no URL"
    return (
        f'<p class="watching"><a href="/">New run</a> · '
        f"<code>{_escape(adapter)}</code> · {shown}</p>"
    )


def _frame(name: str, code: str, inner: str) -> bytes:
    adapter, url = _run_context(name)
    body = _watching(adapter, url) + _steps_nav(name, code) + inner
    return _page(f"{code} {_step_label(code)}", body)


def _provisions(name: str) -> list[dict]:
    """The same provisions stage 01 would hand on. Reads the run package when the chart fetched one."""
    adapter_id = _adapter_id(name)
    adapter_dir = ADAPTERS / adapter_id
    adapter = load_adapter(adapter_dir / "adapter.json")
    ready = [
        section["id"]
        for section in adapter["sections"]
        if section.get("ready") is True and section.get("in_scope") is True
    ]
    provisions: list[dict] = []
    if is_formex_adapter(adapter):
        from requirements.extract.formex.provisions import extract_section_provisions

        package = _chart_dir(name) / "package"
        if not package.is_dir():
            package = formex_package_dir(adapter_dir, adapter)
        for section_id in ready:
            extracted = extract_section_provisions(package, section_id)
            provisions.extend(extracted["provisions"])
        return provisions
    from requirements.extract.adapter import section_provisions

    for section_id in ready:
        extracted = section_provisions(adapter_dir, adapter, section_id)
        provisions.extend(extracted["provisions"])
    return provisions


def _formex_package(name: str, adapter: dict, adapter_dir: Path) -> Path | None:
    """The Formex package for this run, or a sibling adapter for the same instrument."""
    fetched = _chart_dir(name) / "package"
    if is_formex_adapter(adapter) and fetched.is_dir():
        return fetched
    if is_formex_adapter(adapter):
        return formex_package_dir(adapter_dir, adapter)
    identifier = (adapter.get("source") or {}).get("identifier")
    for item in list_adapters():
        source = item.get("source") or {}
        if item.get("source_format") != "formex" or source.get("identifier") != identifier:
            continue
        other_dir = Path(item["adapter_dir"])
        other = load_adapter(other_dir / "adapter.json")
        return formex_package_dir(other_dir, other)
    return None


def _section_reading(name: str, section_id: str) -> tuple[str, str, str]:
    """File name, readable text, and a note when the annex text is missing."""
    adapter_id = _adapter_id(name)
    adapter_dir = ADAPTERS / adapter_id
    adapter = load_adapter(adapter_dir / "adapter.json")
    section = next((item for item in adapter["sections"] if item.get("id") == section_id), None)
    if section is None:
        raise FileNotFoundError(section_id)
    fixture = section.get("fixture")
    if isinstance(fixture, str) and fixture:
        path = adapter_dir / fixture
        return path.name, path.read_text(encoding="utf-8"), ""
    package = _formex_package(name, adapter, adapter_dir)
    if package is None:
        return section_id, "", "The adapter has no text file for this section."
    loaded = load_doc_package(package)
    part = next((item for item in loaded["parts"] if item.get("section_id") == section_id), None)
    if part is None:
        return section_id, "", "The section is not in the Formex package."
    raw = Path(part["file"]).read_text(encoding="utf-8", errors="replace")
    if raw.lstrip().startswith("<"):
        try:
            text = _readable_formex(raw)
        except ET.ParseError:
            text = raw
    else:
        text = raw
    return Path(part["file"]).name + " · reading text", text, ""


def _sections_inner(name: str) -> str:
    """Step 00 lists the adapter sections. A click shows the annex and can ask Cursor for code."""
    adapter_id = _adapter_id(name)
    adapter = load_adapter(ADAPTERS / adapter_id / "adapter.json")
    items = []
    for section in adapter["sections"]:
        used = section.get("ready") is True and section.get("in_scope") is True
        flags = "in scope" if section.get("in_scope") else "out of scope"
        flags += ", ready" if section.get("ready") else ", not ready"
        mark = " · cut in this run" if used else ""
        title = str(section.get("title") or "")
        title_html = f" — {_escape(title)}" if title else ""
        section_id = str(section.get("id") or "")
        items.append(
            f'<li class="section" data-id="{_escape(section_id)}">'
            f"<code>{_escape(section_id)}</code>{title_html} · {_escape(flags)}{_escape(mark)}</li>"
        )
    return f"""
<p>Click a section to see the text under it and ask Cursor to add code that processes it.</p>
<ul class="sections">{''.join(items)}</ul>
<dialog id="ask">
  <form method="dialog">
    <p id="meta"></p>
    <p id="doc-title"></p>
    <p id="doc-note" class="error"></p>
    <pre id="doc" class="doc"></pre>
    <label for="note">Prompt till Cursor</label>
    <textarea id="note" rows="4" placeholder="Add code that processes this section."></textarea>
    <p><button type="button" id="send">Put in the Cursor chat</button>
       <button value="cancel">Close</button></p>
    <p id="sent"></p>
  </form>
</dialog>
<script>
const chart = {json.dumps(name)};
const dialog = document.querySelector("#ask");
document.querySelector(".sections").addEventListener("click", async (event) => {{
  const row = event.target.closest(".section");
  if (!row) return;
  dialog.dataset.id = row.dataset.id;
  document.querySelector("#meta").textContent = row.textContent;
  document.querySelector("#doc-title").textContent = "Loading the section…";
  document.querySelector("#doc-note").textContent = "";
  document.querySelector("#doc").textContent = "";
  document.querySelector("#sent").textContent = "";
  dialog.showModal();
  const response = await fetch("/chart/" + encodeURIComponent(chart) + "/section?id=" + encodeURIComponent(row.dataset.id));
  const payload = await response.json();
  document.querySelector("#doc-title").textContent = payload.title || "";
  document.querySelector("#doc-note").textContent = payload.note || "";
  document.querySelector("#doc").innerHTML = payload.html || "";
}});
document.querySelector("#send").addEventListener("click", async () => {{
  const note = document.querySelector("#note").value.trim();
  const sent = document.querySelector("#sent");
  sent.textContent = "Sending…";
  const response = await fetch("/prompt", {{
    method: "POST",
    headers: {{ "Content-Type": "application/json" }},
    body: JSON.stringify({{ chart, section: dialog.dataset.id, note }})
  }});
  const payload = await response.json();
  sent.textContent = payload.message || payload.error || "";
}});
</script>
"""


def _steps_file(name: str) -> Path:
    return _chart_dir(name) / "steps.json"


def _read_steps(name: str) -> dict | None:
    path = _steps_file(name)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_steps(name: str, payload: dict) -> None:
    path = _steps_file(name)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _run_steps(name: str) -> None:
    """Stages 02 and 03 call the model. Stage 04 assembles their proposals."""
    from requirements.extract.assemble import assemble_requirements
    from requirements.extract.produce import proposals_from_producers

    try:
        adapter_id = _adapter_id(name)
        adapter_dir = ADAPTERS / adapter_id
        adapter = load_adapter(adapter_dir / "adapter.json")
        provisions = [
            {"locus": item["locus"], "law_text": item["law_text"]} for item in _provisions(name)
        ]
        proposals, _notes = proposals_from_producers(provisions, adapter_dir=adapter_dir)
        requirements, exclusions = assemble_requirements(provisions, proposals, adapter=adapter)
        _write_steps(
            name,
            {
                "status": "done",
                "error": "",
                "interpret": [row for row in proposals if "discovery_hints" not in row],
                "hints": [row for row in proposals if "discovery_hints" in row],
                "requirements": requirements,
                "exclusions": exclusions,
            },
        )
    except Exception as exc:
        _write_steps(name, {"status": "failed", "error": str(exc) or exc.__class__.__name__})


def _ensure_steps(name: str, *, again: bool = False) -> dict:
    with _STEPS_LOCK:
        current = _read_steps(name)
        running = _STEP_THREADS.get(name)
        alive = running is not None and running.is_alive()
        if again and not alive:
            path = _steps_file(name)
            if path.is_file():
                path.unlink()
            current = None
        if current and current.get("status") in ("done", "failed") and not (again and not alive):
            return current
        if current and current.get("status") == "running" and alive:
            return current
        _write_steps(name, {"status": "running", "error": ""})
        thread = threading.Thread(target=_run_steps, args=(name,), daemon=True)
        _STEP_THREADS[name] = thread
        thread.start()
        return {"status": "running", "error": ""}


def _waiting(name: str, state: dict) -> str:
    if state.get("status") == "failed":
        return (
            f'<p class="error">{_escape(str(state.get("error") or "The step failed."))}</p>'
            f'<p><a href="/chart/{_escape(name)}/02?again=1">Run 02 and 03 again</a></p>'
        )
    return (
        '<meta http-equiv="refresh" content="3">'
        "<p>Steps 02 and 03 call the model. The page reloads when the answer is ready.</p>"
    )


_INTERPRET_FIELDS = ("id", "locator", "strength", "responsible", "applicability", "note")


def _interpret_headers(proposals: list[dict]) -> list[str]:
    present = {"id", "locator"}
    for row in proposals:
        for key in _INTERPRET_FIELDS:
            if row.get(key):
                present.add(key)
    return [key for key in _INTERPRET_FIELDS if key in present]


def _interpret_inner(name: str, state: dict) -> str:
    proposals = [row for row in (state.get("interpret") or []) if isinstance(row, dict)]
    by_locus = {str(row.get("locus") or ""): row for row in proposals}
    headers = _interpret_headers(proposals)
    document, snapshot = _load(name)
    rows = blocks(document, snapshot)
    for row in rows:
        proposal = by_locus.get(row["locus"]) or {}
        row["added"] = [str(proposal.get(key) or "") for key in headers]
    table = _atoms_table(rows, [(header, False) for header in headers]) if rows else "<p>No atoms.</p>"
    return (
        "<p>Same rows as 01. Grey columns are already done. "
        "White columns are what 02 added.</p>"
        f'<article class="chart">{table}</article>'
    )


_HINT_FIELDS = ("concepts", "path_hints", "sources", "expected_evidence")


def _hint_headers(proposals: list[dict]) -> list[str]:
    present = {"concepts", "path_hints", "sources"}
    for row in proposals:
        hints = row.get("discovery_hints") if isinstance(row.get("discovery_hints"), dict) else {}
        for key in _HINT_FIELDS:
            if hints.get(key):
                present.add(key)
    return [key for key in _HINT_FIELDS if key in present]


def _hint_cell(hints: dict, key: str) -> str:
    if key == "sources":
        items = hints.get("sources") or []
        return ", ".join(
            str(item.get("source") or item) if isinstance(item, dict) else str(item) for item in items
        )
    values = hints.get(key) or []
    if isinstance(values, list):
        return ", ".join(str(item) for item in values)
    return str(values or "")


def _hints_inner(name: str, state: dict) -> str:
    proposals = [row for row in (state.get("interpret") or []) if isinstance(row, dict)]
    hint_rows = [row for row in (state.get("hints") or []) if isinstance(row, dict)]
    earlier = _interpret_headers(proposals)
    headers = _hint_headers(hint_rows)
    by_locus = {str(row.get("locus") or ""): row for row in proposals}
    by_hint = {str(row.get("locus") or ""): row for row in hint_rows}
    document, snapshot = _load(name)
    rows = blocks(document, snapshot)
    for row in rows:
        proposal = by_locus.get(row["locus"]) or {}
        hints = by_hint.get(row["locus"]) or {}
        detail = hints.get("discovery_hints") if isinstance(hints.get("discovery_hints"), dict) else {}
        row["added"] = [str(proposal.get(key) or "") for key in earlier]
        row["added"] += [_hint_cell(detail, key) for key in headers]
    columns = [(header, True) for header in earlier] + [(header, False) for header in headers]
    table = _atoms_table(rows, columns) if rows else "<p>No atoms.</p>"
    return (
        "<p>Same rows as 02. Grey columns are already done. "
        "White columns are what 03 added.</p>"
        f'<article class="chart">{table}</article>'
    )


def _pack_banner(name: str, code: str, lead: str) -> str:
    adapter, url = _run_context(name)
    return (
        "<style>nav.steps{display:flex;flex-wrap:wrap;gap:.4rem;margin:0 0 1rem}"
        "nav.steps a,nav.steps .here{padding:.2rem .55rem;border-radius:999px;border:1px solid #ddd;text-decoration:none}"
        "nav.steps .here{background:#143d66;color:#fff}</style>"
        f"<h1>{_escape(code)} {_escape(_step_label(code))}</h1>"
        + _watching(adapter, url)
        + _steps_nav(name, code)
        + lead
    )


def _assemble_page(name: str, state: dict) -> bytes:
    """Step 04 is the pack editor requirements page, fed by this run's requirements."""
    from studio.pack.pages import copy_page

    adapter, _url = _run_context(name)
    requirements = state.get("requirements") or []
    rows = []
    for requirement in requirements:
        locators = [
            str(ref.get("locator") or "")
            for ref in (requirement.get("references") or [])
            if isinstance(ref, dict)
        ]
        rows.append({"id": requirement.get("id"), "locators": locators})
    loci = []
    for requirement in requirements:
        references = [ref for ref in (requirement.get("references") or []) if isinstance(ref, dict)]
        locus = references[0].get("locator") if references else requirement.get("id")
        loci.append({"locus": locus, "status": "written"})
    for item in state.get("exclusions") or []:
        loci.append(
            {
                "locus": item.get("locus"),
                "status": "excluded",
                "reason": item.get("reason") or "excluded",
            }
        )
    document = copy_page(
        {
            "timestamp": name,
            "adapter_id": adapter,
            "read_only": False,
            "requirements": rows,
            "requirement_query": "?chart=" + quote(name, safe=""),
            "message": "",
            "coverage_detail": {
                "status": "written" if requirements else "none",
                "loci": loci,
            },
        }
    )
    banner = _pack_banner(name, "04", "<p>The list below is the pack editor's requirements view.</p>")
    html = document.decode("utf-8").replace("<body><main>\n", "<body><main>\n" + banner, 1)
    return html.encode("utf-8")


def _requirement_page(chart: str, requirement_id: str) -> bytes:
    from studio.pack.pages import editor_page

    state = _read_steps(chart)
    if state is None or state.get("status") != "done":
        raise FileNotFoundError(requirement_id)
    requirement = next(
        (item for item in state.get("requirements") or [] if item.get("id") == requirement_id),
        None,
    )
    if requirement is None:
        raise FileNotFoundError(requirement_id)
    document = editor_page(
        {
            "requirement": requirement,
            "list_href": f"/chart/{chart}/04",
            "pack_id": requirement.get("pack_id") or "",
        }
    )
    banner = _pack_banner(chart, "04", "")
    html = document.decode("utf-8").replace("<body><main>\n", "<body><main>\n" + banner, 1)
    return html.encode("utf-8")


def _step_page(name: str, code: str, *, again: bool = False) -> bytes:
    _chart_dir(name)
    if code == "00":
        return _frame(name, code, _sections_inner(name))
    if code == "01":
        return _frame(name, code, _structure_inner(name))
    state = _ensure_steps(name, again=again)
    if state.get("status") != "done":
        return _frame(name, code, _waiting(name, state))
    if code == "02":
        return _frame(name, code, _interpret_inner(name, state))
    if code == "03":
        return _frame(name, code, _hints_inner(name, state))
    return _assemble_page(name, state)


def _structure_inner(name: str) -> str:
    document, snapshot = _load(name)
    rows = blocks(document, snapshot)
    return f"""
<p>One row per atom. An empty letter means the point has no subpoint.</p>
<article class="chart">{_atoms_table(rows)}</article>
<dialog id="ask">
  <form method="dialog">
    <p id="meta"></p>
    <p id="doc-title"></p>
    <p id="doc-note" class="error"></p>
    <pre id="doc" class="doc"></pre>
    <label for="note">Prompt till Cursor</label>
    <textarea id="note" rows="4" placeholder="What is wrong, or what should the cutter do?"></textarea>
    <p><button type="button" id="send">Put in the Cursor chat</button>
       <button value="cancel">Close</button></p>
    <p id="sent"></p>
  </form>
</dialog>
<script>
const chart = {json.dumps(name)};
const dialog = document.querySelector("#ask");
document.querySelector(".chart").addEventListener("click", async (event) => {{
  const span = event.target.closest(".cut");
  if (!span) return;
  dialog.dataset.index = span.dataset.index;
  const where = span.dataset.locus || "no locus";
  const reason = span.dataset.reason ? ", " + span.dataset.reason : "";
  document.querySelector("#meta").textContent =
    span.dataset.status + reason + " · " + where
    + " · characters " + span.dataset.start + "–" + span.dataset.end;
  document.querySelector("#doc-title").textContent = "Loading the original…";
  document.querySelector("#doc-note").textContent = "";
  document.querySelector("#doc").textContent = "";
  document.querySelector("#sent").textContent = "";
  dialog.showModal();
  const response = await fetch("/chart/" + encodeURIComponent(chart) + "/original?index=" + span.dataset.index);
  const payload = await response.json();
  document.querySelector("#doc-title").textContent = payload.title || "";
  document.querySelector("#doc-note").textContent = payload.note || "";
  document.querySelector("#doc").innerHTML = payload.html || "";
  const mark = document.querySelector("#doc mark");
  if (mark) mark.scrollIntoView({{block: "center"}});
}});
document.querySelector("#send").addEventListener("click", async () => {{
  const note = document.querySelector("#note").value.trim();
  const sent = document.querySelector("#sent");
  if (!note) {{ sent.textContent = "Write a prompt first."; return; }}
  sent.textContent = "Sending…";
  const response = await fetch("/prompt", {{
    method: "POST",
    headers: {{ "Content-Type": "application/json" }},
    body: JSON.stringify({{ chart, index: Number(dialog.dataset.index), note }})
  }});
  const payload = await response.json();
  sent.textContent = payload.message || payload.error || "";
}});
</script>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, _form(), "text/html; charset=utf-8")
            return
        if path.startswith("/requirements/requirement/"):
            requirement_id = path.removeprefix("/requirements/requirement/")
            query = parse_qs(urlparse(self.path).query)
            chart = (query.get("chart") or [""])[0]
            try:
                self._send(200, _requirement_page(chart, requirement_id), "text/html; charset=utf-8")
            except (FileNotFoundError, KeyError, json.JSONDecodeError):
                self._send(404, _page("Missing", "<p>That requirement is not in the run.</p>"), "text/html; charset=utf-8")
            return
        if path.startswith("/chart/") and path.endswith("/section"):
            name = path.removeprefix("/chart/").removesuffix("/section").strip("/")
            query = parse_qs(urlparse(self.path).query)
            section_id = (query.get("id") or [""])[0]
            try:
                title, text, missing = _section_reading(name, section_id)
                self._json(
                    200,
                    {
                        "title": title,
                        "html": _escape(text),
                        "note": missing,
                    },
                )
            except (FileNotFoundError, KeyError, OSError, ModelError, ET.ParseError) as exc:
                self._json(400, {"title": "", "html": "", "note": str(exc) or "The section could not be read."})
            return
        if path.startswith("/chart/") and path.endswith("/original"):
            name = path.removeprefix("/chart/").removesuffix("/original")
            query = parse_qs(urlparse(self.path).query)
            try:
                index = int((query.get("index") or ["0"])[0])
                document, snapshot = _load(name)
                row = blocks(document, snapshot)[index]
                title, body = _original(_adapter_id(name))
                html_text, found = highlight_verified(body, row["text"])
                self._json(
                    200,
                    {
                        "title": title,
                        "html": html_text,
                        "note": "" if found else "The excerpt is not an exact substring of the original file.",
                    },
                )
            except (FileNotFoundError, KeyError, IndexError, ValueError, json.JSONDecodeError, ModelError) as exc:
                self._json(400, {"title": "", "html": "", "note": str(exc) or "The original could not be read."})
            return
        if path.startswith("/chart/"):
            rest = path.removeprefix("/chart/").strip("/")
            parts = rest.split("/")
            if len(parts) == 1 and parts[0]:
                self.send_response(303)
                self.send_header("Location", f"/chart/{parts[0]}/00")
                self.end_headers()
                return
            if len(parts) == 2 and parts[1] in dict(STEPS):
                query = parse_qs(urlparse(self.path).query)
                again = (query.get("again") or [""])[0] == "1"
                try:
                    self._send(200, _step_page(parts[0], parts[1], again=again), "text/html; charset=utf-8")
                except (FileNotFoundError, KeyError, json.JSONDecodeError):
                    self._send(404, _page("Missing", "<p>That run does not exist.</p>"), "text/html; charset=utf-8")
                return
            self._send(404, _page("Missing", "<p>That step does not exist.</p>"), "text/html; charset=utf-8")
            return
        self._send(404, _page("Missing", "<p>The page does not exist.</p>"), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length)
        if path == "/run":
            form = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
            adapter = (form.get("adapter") or [""])[0]
            url = (form.get("url") or [""])[0].strip()
            allowed = {row["id"] for row in choices()}
            if adapter not in allowed:
                self._send(400, _form("That adapter cannot cut."), "text/html; charset=utf-8")
                return
            try:
                RUNS.mkdir(parents=True, exist_ok=True)
                directory = chart_run(adapter, url or None, root=RUNS)
            except (ModelError, OSError) as exc:
                self._send(400, _form(str(exc)), "text/html; charset=utf-8")
                return
            self.send_response(303)
            self.send_header("Location", f"/chart/{directory.name}/00")
            self.end_headers()
            return
        if path == "/prompt":
            try:
                payload = json.loads(raw.decode("utf-8"))
                note = str(payload.get("note") or "")[:_MAX_NOTE]
                if payload.get("section"):
                    text = section_prompt(str(payload["chart"]), str(payload["section"]), note)
                else:
                    text = prompt_text(str(payload["chart"]), int(payload["index"]), note)
            except (KeyError, TypeError, ValueError, IndexError, FileNotFoundError, json.JSONDecodeError) as exc:
                self._json(400, {"ok": False, "error": str(exc) or "The prompt could not be built."})
                return
            hand_to_cursor(text)
            self._json(
                200,
                {
                    "ok": True,
                    "message": "Cursor shows the prompt and asks whether to open the chat. Confirm there.",
                },
            )
            return
        self._send(404, b"", "text/plain; charset=utf-8")

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
