"""Load a regulation adapter and list its sections (stage 00)."""

from __future__ import annotations

from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json
from requirements.extract.formex.inventory import inventory_package
from requirements.extract.formex.package import load_doc_package
from requirements.extract.formex.provisions import extract_section_provisions
from requirements.extract.formex.text import element_text
import xml.etree.ElementTree as ET

ADAPTERS = Path(__file__).resolve().parent / "adapters"

_SOURCE_FIELDS = ("framework", "instrument", "identifier", "language", "url")


def load_adapter(path: Path) -> dict:
    loaded = read_json(path)
    if not isinstance(loaded, dict):
        raise ModelError(path.name, "adapter", "a JSON object")
    adapter_id = _required_string(loaded, "id", path.name)
    status = loaded.get("status")
    if status not in ("partial", "stub"):
        raise ModelError(adapter_id, "status", "partial or stub")
    sections = loaded.get("sections")
    if not isinstance(sections, list):
        raise ModelError(adapter_id, "sections", "an array")
    if status != "stub":
        _required_string(loaded, "pack_id", adapter_id)
        _require_source(loaded.get("source"), adapter_id)
    if is_formex_adapter(loaded):
        _require_formex_package(loaded, path.resolve().parent)
    seen: set[str] = set()
    adapter_dir = path.resolve().parent
    for index, section in enumerate(sections):
        _check_section(section, index, adapter_id, seen, adapter_dir, loaded)
    return loaded


def is_formex_adapter(adapter: dict) -> bool:
    return adapter.get("source_format") == "formex"


def formex_package_dir(adapter_dir: Path, adapter: dict) -> Path:
    rel = adapter.get("formex_package")
    if not isinstance(rel, str) or not rel:
        raise ModelError(str(adapter.get("id") or "adapter"), "formex_package", "a path")
    path = (adapter_dir / rel).resolve()
    if not path.is_dir():
        raise ModelError(
            str(adapter.get("id") or "adapter"),
            "formex_package",
            f"an existing directory ({rel})",
        )
    return path


def stage00(adapter: dict, *, dump_text: str | None = None, adapter_dir: Path | None = None) -> dict:
    if dump_text is not None:
        raise ModelError(
            str(adapter.get("id") or "adapter"),
            "dump_text",
            "full-dump split is not implemented",
        )
    listed = []
    for section in adapter["sections"]:
        item = {
            "id": section["id"],
            "in_scope": section["in_scope"],
            "ready": section["ready"],
        }
        fixture = section.get("fixture")
        if isinstance(fixture, str) and fixture:
            item["text_file"] = fixture
        listed.append(item)
    result: dict = {"sections": listed}
    if is_formex_adapter(adapter) and adapter_dir is not None:
        package_dir = formex_package_dir(adapter_dir, adapter)
        inventory = inventory_package(package_dir)
        result["inventory"] = {
            "language": inventory["language"],
            "legal_value": inventory["legal_value"],
            "title": inventory["title"],
            "unit_count": len(inventory["units"]),
            "units": inventory["units"],
            "diagnostics": inventory["diagnostics"],
        }
        result["source_format"] = "formex"
    return result


def section_text(adapter_dir: Path, adapter: dict, section_id: str) -> str:
    adapter_id = str(adapter.get("id") or "adapter")
    match = _ready_section(adapter_dir, adapter, section_id)
    if is_formex_adapter(adapter):
        package_dir = formex_package_dir(adapter_dir, adapter)
        extracted = extract_section_provisions(package_dir, section_id)
        # Readable inspection text for engineers; provisions drive assembly.
        chunks = [f"[{item['locus']}] {item['law_text']}" for item in extracted["provisions"]]
        if not chunks:
            # Fall back to raw section XML visible text when no list provisions.
            part_file = Path(extracted["file"])
            root = ET.parse(part_file).getroot()
            return element_text(root)
        return "\n\n".join(chunks)
    fixture = match.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        raise ModelError(adapter_id, f"sections[{section_id}].fixture", "a path")
    file_path = adapter_dir / fixture
    if not file_path.is_file():
        raise ModelError(
            adapter_id,
            f"sections[{section_id}].fixture",
            f"an existing file ({fixture})",
        )
    return file_path.read_text(encoding="utf-8")


def section_provisions(adapter_dir: Path, adapter: dict, section_id: str) -> dict:
    """Deterministic provisions for one ready section."""
    _ready_section(adapter_dir, adapter, section_id)
    if is_formex_adapter(adapter):
        package_dir = formex_package_dir(adapter_dir, adapter)
        return extract_section_provisions(package_dir, section_id)
    from requirements.extract.atomize import atomize

    text = section_text(adapter_dir, adapter, section_id)
    provisions = [{"locus": item["locus"], "law_text": item["law_text"]} for item in atomize(text)]
    return {
        "section_id": section_id,
        "kind": "text_fixture",
        "file": str((_section(adapter, section_id) or {}).get("fixture") or ""),
        "provisions": provisions,
        "diagnostics": [],
    }


def list_adapters() -> list[dict]:
    """Catalog adapters for UI/CLI source selection."""
    listed = []
    for path in sorted(ADAPTERS.glob("*/adapter.json")):
        adapter = load_adapter(path)
        listed.append(
            {
                "id": adapter["id"],
                "status": adapter["status"],
                "pack_id": adapter.get("pack_id"),
                "source_format": adapter.get("source_format") or "text",
                "source": adapter.get("source"),
                "sections": [
                    {
                        "id": section["id"],
                        "title": section.get("title") or "",
                        "ready": section["ready"],
                        "in_scope": section["in_scope"],
                    }
                    for section in adapter["sections"]
                ],
                "path": str(path),
                "adapter_dir": str(path.parent),
            }
        )
    return listed


def _ready_section(adapter_dir: Path, adapter: dict, section_id: str) -> dict:
    adapter_id = str(adapter.get("id") or "adapter")
    if adapter.get("status") == "stub":
        raise ModelError(adapter_id, "status", "partial, not stub")
    match = _section(adapter, section_id)
    if match is None:
        raise ModelError(adapter_id, "sections[].id", f"a section named {section_id}")
    if match.get("ready") is not True:
        raise ModelError(adapter_id, f"sections[{section_id}].ready", "true")
    if match.get("in_scope") is not True:
        raise ModelError(adapter_id, f"sections[{section_id}].in_scope", "true")
    return match


def _required_string(obj: dict, field: str, object_name: str) -> str:
    value = obj.get(field)
    if not isinstance(value, str) or not value:
        raise ModelError(object_name, field, "a non-empty string")
    return value


def _require_source(source: object, adapter_id: str) -> None:
    if not isinstance(source, dict):
        raise ModelError(adapter_id, "source", "an object")
    if "edition" in source:
        raise ModelError(adapter_id, "source.edition", "absent")
    for field in _SOURCE_FIELDS:
        value = source.get(field)
        if not isinstance(value, str) or not value:
            raise ModelError(adapter_id, f"source.{field}", "a non-empty string")


def _require_formex_package(adapter: dict, adapter_dir: Path) -> None:
    adapter_id = str(adapter.get("id") or "adapter")
    package_dir = formex_package_dir(adapter_dir, adapter)
    # Ensure the DOC package opens; do not mutate files.
    load_doc_package(package_dir)
    if adapter.get("source_format") != "formex":
        raise ModelError(adapter_id, "source_format", "formex")


def _check_section(
    section: object,
    index: int,
    adapter_id: str,
    seen: set[str],
    adapter_dir: Path,
    adapter: dict,
) -> None:
    if not isinstance(section, dict):
        raise ModelError(adapter_id, f"sections[{index}]", "an object")
    section_id = section.get("id")
    if not isinstance(section_id, str) or not section_id:
        raise ModelError(adapter_id, f"sections[{index}].id", "a non-empty string")
    if section_id in seen:
        raise ModelError(adapter_id, "sections[].id", f"a unique id, not a duplicate {section_id}")
    seen.add(section_id)
    for flag in ("in_scope", "ready"):
        if not isinstance(section.get(flag), bool):
            raise ModelError(adapter_id, f"sections[{section_id}].{flag}", "a boolean")
    if section["ready"] is not True:
        return
    if is_formex_adapter(adapter):
        # Ready Formex sections are resolved through formex_package, not fixture files.
        return
    fixture = section.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        raise ModelError(adapter_id, f"sections[{section_id}].fixture", "a path when ready is true")
    if not (adapter_dir / fixture).is_file():
        raise ModelError(
            adapter_id,
            f"sections[{section_id}].fixture",
            f"an existing file, not {fixture}",
        )


def _section(adapter: dict, section_id: str) -> dict | None:
    for section in adapter.get("sections") or []:
        if isinstance(section, dict) and section.get("id") == section_id:
            return section
    return None
