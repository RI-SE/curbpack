"""Copy a foreign Pack into the publisher namespace. The source directory is not opened for writing."""

from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common.errors import ModelError
from common.store import load_pack_directory, save_pack, save_requirement
from common.validate import pack_namespace
from requirements.editing import apply_edits
from requirements.workspace import _pack_id_name


def in_target_namespace(pack: dict, namespace_base: str) -> bool:
    """True when the Pack already uses namespace_base plus its name."""
    name = pack.get("name")
    if not isinstance(name, str) or not name.strip():
        return False
    return pack.get("namespace") == pack_namespace(namespace_base, name)


def _free_stamp(root: Path, pack_id: str, at: str | None) -> str:
    """Use `at` when the caller named the directory. Otherwise take a free second."""
    if at is not None:
        if not at or Path(at).name != at or at in {".", ".."}:
            raise ModelError("working copy", "timestamp", "a single directory name")
        return at
    moment = datetime.now(timezone.utc).replace(microsecond=0)
    for offset in range(5):
        stamp = (moment + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H%M%SZ")
        if not (root / pack_id / stamp).exists():
            return stamp
    raise ModelError("working copy", "timestamp", "a free second within five attempts")


def _confined_directory(root: Path, pack_id: str, stamp: str) -> Path:
    """A new working-copy path that stays inside root."""
    pack_id = _pack_id_name(pack_id)
    root_resolved = root.resolve()
    final = (root_resolved / pack_id / stamp).resolve()
    if root_resolved != final and root_resolved not in final.parents:
        raise ModelError("pack", "id", "a directory inside the workspace")
    return final


def take_ownership(
    source: Path,
    destination_root: Path,
    *,
    namespace_base: str,
    requirement_id: str,
    edits: dict,
    at: str | None = None,
    also_search: tuple[Path, ...] = (),
    addition: dict | None = None,
    addition_pack: dict | None = None,
) -> Path:
    """Write a new dated working copy. `at` is that directory name when given."""
    pack, requirements = load_pack_directory(source)
    target = pack_namespace(namespace_base, str(pack.get("name") or ""))
    if pack.get("namespace") == target:
        raise ModelError("pack", "namespace", "a namespace other than the target namespace")
    present = any(item.get("id") == requirement_id for item in requirements)
    if not present and addition is None:
        raise ModelError(
            f"requirement {requirement_id}",
            "id",
            "a requirement in this pack",
        )
    pack_id = _pack_id_name(str(pack.get("id") or ""))
    _refuse_existing_target(pack_id, target, source, destination_root, also_search)
    stamp = _free_stamp(destination_root, pack_id, at)
    final = _confined_directory(destination_root, pack_id, stamp)
    if final.exists():
        raise ModelError("working copy", "timestamp", f"a new directory, not {stamp}")
    temp = destination_root / f".own-tmp-{secrets.token_hex(8)}"
    try:
        shutil.copytree(source, temp)
        _write_owned_copy(
            temp,
            pack,
            requirements,
            target,
            requirement_id,
            edits,
            addition=addition,
            addition_pack=addition_pack,
        )
        final.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.rename(temp, final)
        except OSError:
            raise ModelError("working copy", "timestamp", f"a new directory, not {stamp}") from None
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    return final


def _write_owned_copy(
    directory: Path,
    pack: dict,
    requirements: list[dict],
    target: str,
    requirement_id: str,
    edits: dict,
    addition: dict | None = None,
    addition_pack: dict | None = None,
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
    items = list(requirements)
    if addition is not None and not any(item.get("id") == requirement_id for item in items):
        items.append(addition)
    for requirement in items:
        owned = {
            key: value
            for key, value in requirement.items()
            if key != "signed"
        }
        source_pack = addition_pack if addition is not None and requirement.get("id") == requirement_id and addition_pack else pack
        owned["namespace"] = target
        owned["status"] = "draft"
        owned["origin"] = {
            "namespace": requirement["namespace"],
            "pack": source_pack["id"],
            "version": source_pack["version"],
            "requirement": requirement["id"],
        }
        if requirement["id"] == requirement_id and edits:
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
