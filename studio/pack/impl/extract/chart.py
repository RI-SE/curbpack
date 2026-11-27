"""Side-file chart of what a cutter kept and what it dropped.

The chart is not a Requirement and is not an input to stages 02–04.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from common.errors import ModelError
from common.jsonio import write_json

_INGESTER_FILES = (
    "formex/text.py",
    "formex/provisions.py",
    "atomize.py",
)


class Chart:
    """Blocks gathered while a cutter can still see the text it drops."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.source_id: str | None = None
        self.language: str | None = None
        self.edition: str | None = None
        self.url: str | None = None
        self.source_sha256: str | None = None
        self.ingester_name = "formex"
        self._blocks: list[dict] = []

    @classmethod
    def create(cls, adapter_id: str, *, root: Path | None = None) -> Chart:
        base = root or Path(tempfile.gettempdir())
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        directory = base / f"sourcechart-{adapter_id}-{stamp}"
        suffix = 2
        while directory.exists():
            directory = base / f"sourcechart-{adapter_id}-{stamp}-{suffix}"
            suffix += 1
        directory.mkdir(parents=True)
        return cls(directory)

    def fill_source(
        self,
        adapter: dict,
        source_bytes: bytes | None = None,
        *,
        source_sha256: str | None = None,
    ) -> None:
        source = adapter.get("source") if isinstance(adapter.get("source"), dict) else {}
        identifier = source.get("identifier") if isinstance(source, dict) else None
        language = source.get("language") if isinstance(source, dict) else None
        url = source.get("url") if isinstance(source, dict) else None
        if isinstance(identifier, str):
            self.source_id = identifier
        if isinstance(language, str):
            self.language = language
        if self.url is None and isinstance(url, str):
            self.url = url
        if source_sha256 is None:
            if source_bytes is None:
                raise ModelError("chart", "source", "bytes or a sha256")
            source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        self.source_sha256 = source_sha256

    def own(self, text: str, *, locus: str, parent: str | None = None) -> None:
        if text:
            self._blocks.append(
                {"text": text, "status": "own", "locus": locus, "parent": parent, "reason": None}
            )

    def uncovered(self, text: str, *, reason: str) -> None:
        if text:
            self._blocks.append(
                {
                    "text": text,
                    "status": "uncovered",
                    "locus": None,
                    "parent": None,
                    "reason": reason,
                }
            )

    def finish(self) -> Path:
        snapshot = "".join(block["text"] for block in self._blocks)
        cuts = [0]
        for block in self._blocks:
            cuts.append(cuts[-1] + len(block["text"]))
        units: list[dict] = []
        by_locus: dict[str, dict] = {}
        unassigned: dict[str, list[str]] = {}
        for index, block in enumerate(self._blocks):
            if block["status"] == "uncovered":
                unassigned[str(index)] = ["uncovered", block["reason"] or "uncovered"]
                continue
            locus = block["locus"] or str(index)
            unit = by_locus.get(locus)
            if unit is None:
                unit = {
                    "id": locus,
                    "locator": locus,
                    "label": "provision",
                    "parent": block["parent"],
                    "blocks": [],
                }
                by_locus[locus] = unit
                units.append(unit)
            unit["blocks"].append(index)
        document = {
            "sourcechart": "0.9",
            "source": {
                "sha256": self.source_sha256,
                "id": self.source_id,
                "edition": self.edition,
                "language": self.language,
                "url": self.url,
            },
            "snapshot": {
                "sha256": hashlib.sha256(snapshot.encode("utf-8")).hexdigest(),
                "chars": len(snapshot),
                "ingester": {
                    "name": self.ingester_name,
                    "version": "0",
                    "sha256": ingester_sha256(),
                },
            },
            "cuts": cuts,
            "units": units,
            "unassigned": unassigned,
        }
        (self.directory / "snapshot.txt").write_text(snapshot, encoding="utf-8")
        write_json(self.directory / "sourcechart.json", document)
        return self.directory


def ingester_sha256() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in _INGESTER_FILES:
        digest.update((root / name).read_bytes())
    return digest.hexdigest()


def chart_run(adapter_id: str, url: str | None = None, *, root: Path | None = None) -> Path:
    """Write a chart for one adapter. A text adapter never fetches ``url``."""
    from requirements.extract.adapter import (
        ADAPTERS,
        _ready_section,
        formex_package_dir,
        is_formex_adapter,
        load_adapter,
        section_provisions,
    )
    from requirements.extract.formex.package import load_doc_package
    from requirements.extract.formex.provisions import extract_section_provisions

    adapter_dir = ADAPTERS / adapter_id
    if not (adapter_dir / "adapter.json").is_file():
        raise ModelError("source", "adapter_id", f"a known adapter, not {adapter_id}")
    adapter = load_adapter(adapter_dir / "adapter.json")
    if adapter.get("status") == "stub":
        raise ModelError(adapter_id, "status", "partial, not stub")
    ready = [
        section["id"]
        for section in adapter["sections"]
        if section.get("ready") is True and section.get("in_scope") is True
    ]
    if not ready:
        raise ModelError(adapter_id, "sections[].ready", "one ready section")

    chart = Chart.create(adapter_id, root=root)
    if isinstance(url, str) and url:
        chart.url = url
    try:
        if is_formex_adapter(adapter):
            chart.ingester_name = "formex"
            if isinstance(url, str) and url:
                package_dir, source_bytes = _fetch_formex_zip(url, chart.directory)
                chart.fill_source(adapter, source_bytes)
            else:
                package_dir = formex_package_dir(adapter_dir, adapter)
                chart.fill_source(adapter, source_sha256=_directory_sha256(package_dir))
            package = load_doc_package(package_dir)
            for part in package["parts"]:
                if part.get("supported") is False:
                    chart.uncovered(
                        str(part.get("reason") or part.get("section_id") or "unsupported"),
                        reason="unsupported package part",
                    )
            for section_id in ready:
                _ready_section(adapter_dir, adapter, section_id)
                extract_section_provisions(package_dir, section_id, chart=chart)
        else:
            chart.ingester_name = "text"
            chart.fill_source(adapter, _fixture_bytes(adapter_dir, adapter, ready))
            for section_id in ready:
                section_provisions(adapter_dir, adapter, section_id, chart)
    except Exception:
        _discard(chart.directory)
        raise
    return chart.finish()


def _discard(directory: Path) -> None:
    if not directory.is_dir():
        return
    for path in sorted(directory.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            path.rmdir()
    directory.rmdir()


def _directory_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        digest.update(path.relative_to(directory).as_posix().encode("utf-8"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _fixture_bytes(adapter_dir: Path, adapter: dict, section_ids: list[str]) -> bytes:
    sections = {section["id"]: section for section in adapter["sections"]}
    payload = bytearray()
    for section_id in section_ids:
        fixture = sections[section_id].get("fixture")
        if not isinstance(fixture, str) or not fixture:
            raise ModelError(adapter.get("id") or "adapter", f"sections[{section_id}].fixture", "a path")
        payload.extend((adapter_dir / fixture).read_bytes())
    return bytes(payload)


def _fetch_formex_zip(url: str, directory: Path) -> tuple[Path, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/zip;mtype=fmx4",
            "Accept-Language": "eng",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    zip_path = directory / "source.fmx4.zip"
    zip_path.write_bytes(payload)
    package_dir = directory / "package"
    package_dir.mkdir()
    _extract_zip(zip_path, package_dir)
    return package_dir, payload


def _extract_zip(zip_path: Path, package_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            target = (package_dir / info.filename).resolve()
            if not target.is_relative_to(package_dir.resolve()):
                raise ModelError(zip_path.name, "member", f"a path inside the package, not {info.filename}")
        archive.extractall(package_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a source chart for one adapter.")
    parser.add_argument("--adapter", required=True, help="Adapter id, for example nis or cra.")
    parser.add_argument(
        "--url",
        default=None,
        help="Formex CELLAR zip to fetch. Omitted, the pinned package is used. Text adapters never fetch.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Parent directory for the chart. Default is the system temp directory.",
    )
    args = parser.parse_args(argv)
    try:
        path = chart_run(args.adapter, args.url, root=args.out)
    except (ModelError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(path)
    return 0
