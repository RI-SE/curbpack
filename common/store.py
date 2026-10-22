"""Load and save Packs v2 JSON. Validation runs on the way in and the way out."""

from __future__ import annotations

from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.validate import (
    upgrade_stored_claim,
    validate_claim,
    validate_pack,
    validate_requirement,
    validate_run_result,
)


def _safe_id(value: str, object_name: str) -> str:
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
    if not value or any(ch not in allowed for ch in value):
        raise ModelError(object_name, "id", "letters, digits, dot, underscore, or hyphen")
    return value


def save_requirement(directory: Path, requirement: dict, *, published: bool = False) -> Path:
    checked = validate_requirement(requirement, published=published)
    path = directory / f"{_safe_id(checked['id'], 'requirement')}.json"
    write_json(path, checked)
    return path


def load_requirement(path: Path, *, published: bool = False) -> dict:
    return validate_requirement(read_json(path), published=published)


def save_pack(directory: Path, pack: dict, *, sealed: bool = False) -> Path:
    checked = validate_pack(pack, sealed=sealed)
    path = directory / "pack.json"
    write_json(path, checked)
    return path


def load_pack(path: Path, *, sealed: bool = False) -> dict:
    return validate_pack(read_json(path), sealed=sealed)


def save_claim(directory: Path, claim: dict) -> Path:
    checked = validate_claim(claim)
    path = directory / f"{_safe_id(checked['id'], 'claim')}.json"
    write_json(path, checked)
    return path


def load_claim(path: Path) -> dict:
    raw = read_json(path)
    upgraded = upgrade_stored_claim(raw)
    if upgraded is not None:
        write_json(path, upgraded)
        return upgraded
    return validate_claim(raw)


def load_claims(directory: Path) -> list[dict]:
    if not directory.is_dir():
        return []
    claims = []
    for path in sorted(directory.glob("*.json")):
        claims.append(load_claim(path))
    return claims


def save_run_result(path: Path, result: dict) -> Path:
    checked = validate_run_result(result)
    write_json(path, checked)
    return path


def load_run_result(path: Path) -> dict:
    return validate_run_result(read_json(path))


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
    return pack, requirements
