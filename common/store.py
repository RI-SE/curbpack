"""Load and save Packs v2 JSON. Validation runs on the way in and the way out."""

from __future__ import annotations

from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.validate import (
    upgrade_stored_claim,
    validate_claim,
    validate_format_version,
    validate_pack,
    validate_requirement,
    validate_run_result,
)

CURRENT_FORMAT_VERSION = 1


def upgrade_format_0_to_1(document: dict) -> dict:
    """The only production step. It sets format_version to 1 and changes nothing else."""
    upgraded = dict(document)
    upgraded["format_version"] = CURRENT_FORMAT_VERSION
    return upgraded


PRODUCTION_FORMAT_STEPS = ((0, 1, upgrade_format_0_to_1),)


def apply_format_chain(document: dict, steps, *, floor: int = 0) -> dict:
    """Run one function per version, in order. A gap or a version below the floor is rejected.

    This does not write. Production passes PRODUCTION_FORMAT_STEPS. A test may pass
    its own steps; those steps are not registered here.
    """
    if not isinstance(document, dict):
        raise ModelError("document", "format_version", "object")
    version = document["format_version"] if "format_version" in document else 0
    if type(version) is not int:
        raise ModelError("document", "format_version", "an integer version this chain can read")
    if version < floor or version < 0:
        raise ModelError("document", "format_version", "a version at or above the floor")
    by_source: dict[int, tuple[int, object]] = {}
    for source, destination, function in steps:
        if type(source) is not int or destination != source + 1 or source in by_source:
            raise ModelError("document", "format_version", "the next step, with no gap")
        by_source[source] = (destination, function)
    if not by_source:
        return dict(document)
    highest = max(destination for destination, _function in by_source.values())
    if version > highest or version < min(by_source):
        raise ModelError("document", "format_version", "a version this chain can read")
    cursor = version
    while cursor < highest:
        found = by_source.get(cursor)
        if found is None:
            raise ModelError("document", "format_version", "the next step, with no gap")
        cursor = found[0]
    current = dict(document)
    while version < highest:
        destination, function = by_source[version]
        current = function(current)
        if not isinstance(current, dict) or current.get("format_version") != destination:
            raise ModelError("document", "format_version", "the version that step returns")
        version = destination
    return current


def stamp_saved_document(document: dict) -> dict:
    """Put format_version 1 on the validated document that save writes."""
    document["format_version"] = CURRENT_FORMAT_VERSION
    return document


def read_format_document(document: dict, object_name: str) -> tuple[dict, int, int]:
    """Return the current document, the version that was stored, and current_version.

    A missing format_version is version 0. This does not write.
    """
    validate_format_version(document, object_name)
    read_version = 0 if "format_version" not in document else document["format_version"]
    upgraded = apply_format_chain(document, PRODUCTION_FORMAT_STEPS)
    return upgraded, read_version, CURRENT_FORMAT_VERSION


def _safe_id(value: str, object_name: str) -> str:
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
    if not value or any(ch not in allowed for ch in value):
        raise ModelError(object_name, "id", "letters, digits, dot, underscore, or hyphen")
    return value


def save_requirement(directory: Path, requirement: dict, *, published: bool = False) -> Path:
    checked = validate_requirement(requirement, published=published)
    path = directory / f"{_safe_id(checked['id'], 'requirement')}.json"
    write_json(path, stamp_saved_document(checked))
    return path


def read_requirement(path: Path, *, published: bool = False) -> tuple[dict, int, int]:
    checked = validate_requirement(read_json(path), published=published)
    return read_format_document(checked, f"requirement {checked.get('id', '?')}")


def load_requirement(path: Path, *, published: bool = False) -> dict:
    document, _read_version, _current_version = read_requirement(path, published=published)
    return document


def save_pack(directory: Path, pack: dict, *, sealed: bool = False) -> Path:
    checked = validate_pack(pack, sealed=sealed)
    path = directory / "pack.json"
    write_json(path, stamp_saved_document(checked))
    return path


def read_pack(path: Path, *, sealed: bool = False) -> tuple[dict, int, int]:
    checked = validate_pack(read_json(path), sealed=sealed)
    return read_format_document(checked, f"pack {checked.get('id', '?')}")


def load_pack(path: Path, *, sealed: bool = False) -> dict:
    document, _read_version, _current_version = read_pack(path, sealed=sealed)
    return document


def save_claim(directory: Path, claim: dict) -> Path:
    checked = validate_claim(claim)
    path = directory / f"{_safe_id(checked['id'], 'claim')}.json"
    write_json(path, stamp_saved_document(checked))
    return path


def read_claim(path: Path) -> tuple[dict, int, int]:
    raw = read_json(path)
    name = f"claim {raw.get('id', '?')}" if isinstance(raw, dict) else "claim"
    if isinstance(raw, dict):
        validate_format_version(raw, name)
    upgraded = upgrade_stored_claim(raw)
    document = upgraded if upgraded is not None else validate_claim(raw)
    if isinstance(raw, dict) and "format_version" in raw and "format_version" not in document:
        document = dict(document)
        document["format_version"] = raw["format_version"]
    return read_format_document(document, name)


def load_claim(path: Path) -> dict:
    document, _read_version, _current_version = read_claim(path)
    return document


def load_claims(directory: Path) -> list[dict]:
    if not directory.is_dir():
        return []
    claims = []
    for path in sorted(directory.glob("*.json")):
        claims.append(load_claim(path))
    return claims


def save_run_result(path: Path, result: dict) -> Path:
    checked = validate_run_result(result)
    write_json(path, stamp_saved_document(checked))
    return path


def read_run_result(path: Path) -> tuple[dict, int, int]:
    checked = validate_run_result(read_json(path))
    return read_format_document(checked, "run result")


def load_run_result(path: Path) -> dict:
    document, _read_version, _current_version = read_run_result(path)
    return document


def load_pack_directory(root: Path) -> tuple[dict, list[dict]]:
    pack = load_pack(root / "pack.json")
    requirements = []
    for path in sorted(root.glob("*.json")):
        if path.name == "pack.json":
            continue
        requirements.append(load_requirement(path))
    for requirement in requirements:
        if requirement["pack_id"] != pack["id"]:
            raise ModelError(
                f"requirement {requirement['id']}",
                "pack_id",
                f"{pack['id']!r}",
            )
        if requirement.get("namespace") != pack.get("namespace"):
            raise ModelError(
                f"requirement {requirement['id']}",
                "namespace",
                f"{pack.get('namespace')!r}",
            )
    return pack, requirements
