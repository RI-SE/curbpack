"""Human edits and the draft / working-copy / publisher split.

Editing returns a new object. A changed payload loses `signed`, because the
old signature covered the previous bytes. The caller decides where to save it.
"""

from __future__ import annotations

import copy

from pathlib import Path

from common.canonical import pack_directory_digest, version_digest
from common.errors import ModelError
from common.jsonio import write_json
from common.signing import read_digest, sign_object, signed_block
from common.store import load_pack, load_requirement, save_pack, save_requirement
from common.validate import validate_pack, validate_requirement

EDITABLE = {
    "remediation_hint",
    "note",
    "discovery_hints",
    "source",
    "references",
    "strength",
    "responsible",
    "applicability",
    "exceptions",
    "scope",
}


def apply_edits(requirement: dict, edits: dict) -> dict:
    unknown = sorted(set(edits) - EDITABLE)
    if unknown:
        raise ModelError(f"requirement {requirement.get('id', '?')}", unknown[0], "an editable field")
    out = copy.deepcopy(requirement)
    for key, value in edits.items():
        if value is None or value == "" or value == [] or value == {}:
            out.pop(key, None)
        else:
            out[key] = copy.deepcopy(value)
    if version_digest(out) == version_digest(requirement):
        return copy.deepcopy(requirement)
    out.pop("signed", None)
    return validate_requirement(out, published=False)


def assign_reference_numbers(references: list[dict]) -> list[dict]:
    numbered = []
    for index, ref in enumerate(references, start=1):
        numbered.append(
            {
                "nr": index,
                "locator": ref["locator"],
                "law_text": ref["law_text"],
            }
        )
    return numbered


def save_working_requirement(directory: Path, requirement: dict, *, expected_digest: str) -> Path:
    _refuse_published_directory(directory)
    path = directory / f"{requirement['id']}.json"
    if path.is_file():
        existing = load_requirement(path)
        if version_digest(existing) != expected_digest:
            raise ModelError(
                f"requirement {requirement.get('id', '?')}",
                "version",
                "the digest read before this save",
            )
    return save_requirement(directory, requirement)


def _refuse_published_directory(directory: Path) -> None:
    if "published" in Path(directory).parts:
        raise ModelError(
            "working copy",
            "path",
            "a dated working copy, not a published release",
        )


def working_copy(requirement: dict, pack: dict) -> dict:
    """Copy a published requirement into the product repo. Unsigned, with origin set."""
    validate_pack(pack)
    if "origin" in requirement:
        raise ModelError(
            f"requirement {requirement.get('id', '?')}",
            "origin",
            "absent on the requirement being copied",
        )
    out = copy.deepcopy(requirement)
    out.pop("signed", None)
    out["origin"] = {"pack": pack["id"], "version": pack["version"]}
    return validate_requirement(out, published=False)


def accept_published_version(published: dict, pack: dict) -> dict:
    """Take a publisher requirement into the local working copy. The result is an unsigned draft."""
    validate_pack(pack)
    if "origin" in published:
        raise ModelError(
            f"requirement {published.get('id', '?')}",
            "origin",
            "absent on the publisher requirement",
        )
    out = copy.deepcopy(published)
    out.pop("signed", None)
    out["origin"] = {"pack": pack["id"], "version": pack["version"]}
    return validate_requirement(out, published=False)


def publish_requirement(requirement: dict, *, name: str, private_key: bytes, at: str) -> dict:
    if "origin" in requirement:
        raise ModelError(
            f"requirement {requirement.get('id', '?')}",
            "origin",
            "absent when publishing; this is a local working copy",
        )
    signed = sign_object(requirement, name=name, private_key=private_key, at=at)
    return validate_requirement(signed, published=True)


def seal_pack_directory(root: Path, *, name: str, private_key: bytes, at: str) -> dict:
    """Sign the pack directory digest and return the sealed pack.json object."""
    pack = load_pack(root / "pack.json")
    unsigned = copy.deepcopy(pack)
    unsigned.pop("signed", None)
    # Name and time sit in the directory digest. The signature field is cleared
    # while that digest is computed, then written back.
    pending = copy.deepcopy(unsigned)
    pending["signed"] = {"at": at, "name": name, "signature": ""}
    write_json(root / "pack.json", pending)
    digest = pack_directory_digest(root)
    sealed = copy.deepcopy(pending)
    sealed["signed"] = signed_block(digest, name=name, private_key=private_key, at=at)
    save_pack(root, sealed, sealed=True)
    return sealed


def read_pack_seal(root: Path, trust: dict[str, bytes]) -> dict:
    pack = load_pack(root / "pack.json")
    return read_digest(
        pack_directory_digest(root),
        pack.get("signed"),
        trust,
        what="pack directory",
    )


def approve_working_copy(requirement: dict, *, name: str, private_key: bytes, at: str) -> dict:
    if "origin" not in requirement:
        raise ModelError(
            f"requirement {requirement.get('id', '?')}",
            "origin",
            "present on a local working copy before approval",
        )
    signed = sign_object(requirement, name=name, private_key=private_key, at=at)
    return validate_requirement(signed, published=False)
