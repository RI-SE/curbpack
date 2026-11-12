"""Copy a foreign Pack into the publisher namespace. The source directory is not opened for writing."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from common.errors import ModelError
from common.store import load_pack_directory, save_pack, save_requirement
from common.validate import pack_namespace
from requirements.editing import apply_edits


def in_target_namespace(pack: dict, namespace_base: str) -> bool:
    """True when the Pack already uses namespace_base plus its name."""
    name = pack.get("name")
    if not isinstance(name, str) or not name.strip():
        return False
    return pack.get("namespace") == pack_namespace(namespace_base, name)


def take_ownership(
    source: Path,
    destination_root: Path,
    *,
    namespace_base: str,
    requirement_id: str,
    edits: dict,
    at: str | None = None,
    also_search: tuple[Path, ...] = (),
) -> Path:
    """Write a new dated working copy. `at` is that directory name when given."""
    pack, requirements = load_pack_directory(source)
    target = pack_namespace(namespace_base, str(pack.get("name") or ""))
    if pack.get("namespace") == target:
        raise ModelError("pack", "namespace", "a namespace other than the target namespace")
    if not any(item.get("id") == requirement_id for item in requirements):
        raise ModelError(
            f"requirement {requirement_id}",
            "id",
            "a requirement in this pack",
        )
    _refuse_existing_target(pack["id"], target, source, destination_root, also_search)
    stamp = at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    if not stamp or Path(stamp).name != stamp or stamp in {".", ".."}:
        raise ModelError("working copy", "timestamp", "a single directory name")
    final = destination_root / pack["id"] / stamp
    if final.exists():
        raise ModelError("working copy", "timestamp", f"a new directory, not {stamp}")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "copy"
        shutil.copytree(source, work)
        _write_owned_copy(work, pack, requirements, target, requirement_id, edits)
        final.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(work), str(final))
    return final


def _write_owned_copy(
    directory: Path,
    pack: dict,
    requirements: list[dict],
    target: str,
    requirement_id: str,
    edits: dict,
) -> None:
    owned_pack = {
        key: value
        for key, value in pack.items()
        if key != "signed"
    }
    owned_pack["namespace"] = target
    owned_pack["status"] = "draft"
    owned_pack["origin"] = {
        "namespace": pack["namespace"],
        "pack": pack["id"],
        "version": pack["version"],
    }
    save_pack(directory, owned_pack)
    for requirement in requirements:
        owned = {
            key: value
            for key, value in requirement.items()
            if key != "signed"
        }
        owned["namespace"] = target
        owned["status"] = "draft"
        owned["origin"] = {
            "namespace": requirement["namespace"],
            "pack": pack["id"],
            "version": pack["version"],
            "requirement": requirement["id"],
        }
        if requirement["id"] == requirement_id:
            owned = apply_edits(owned, edits)
        save_requirement(directory, owned)


def _refuse_existing_target(
    pack_id: str,
    target: str,
    source: Path,
    destination_root: Path,
    also_search: tuple[Path, ...],
) -> None:
    source_resolved = source.resolve()
    roots = (destination_root, *also_search)
    for root in roots:
        for directory in _candidate_dirs(root, pack_id):
            if directory.resolve() == source_resolved:
                continue
            found, _requirements = load_pack_directory(directory)
            if found.get("namespace") == target:
                raise ModelError(
                    "pack",
                    "namespace",
                    f"no pack {pack_id} already in {target}",
                )


def _candidate_dirs(root: Path, pack_id: str):
    for base in (root / pack_id, root / "published" / pack_id):
        if not base.is_dir():
            continue
        if (base / "pack.json").is_file():
            yield base
        for child in sorted(base.iterdir()):
            if child.is_dir() and (child / "pack.json").is_file():
                yield child
