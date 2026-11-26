"""ZIP exchange of one Pack directory. The directory export is unchanged."""

from __future__ import annotations

import io
import os
import secrets
import shutil
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from common.errors import ModelError
from common.store import load_pack_directory
from requirements.workspace import _pack_id_name, mark_selected
from studio.pack.pack_export import _signature_rows


def export_pack_zip(directory: Path, trust: dict) -> tuple[bytes, list[dict]]:
    """Archive the Pack directory as it stands and report VR-00 for each object."""
    files = _regular_files(directory)
    pack, requirements = load_pack_directory(directory)
    rows = _signature_rows(directory, pack, requirements, trust)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in files:
            archive.writestr(_zip_member(path, directory), path.read_bytes())
    return buffer.getvalue(), rows


def import_pack_zip(
    payload: bytes,
    destination_root: Path,
    trust: dict,
    *,
    at: str | None = None,
) -> tuple[Path, list[dict]]:
    """Install the archive bytes as a selected working copy."""
    files = _archive_files(payload)
    stamp = at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    if not stamp or Path(stamp).name != stamp or stamp in {".", ".."}:
        raise ModelError("working copy", "timestamp", "a single directory name")
    temp = destination_root / f".import-tmp-{secrets.token_hex(8)}"
    final: Path | None = None
    try:
        temp.mkdir(parents=True, exist_ok=False)
        _write_members(temp, files)
        pack, requirements = load_pack_directory(temp)
        pack_id = _pack_id_name(str(pack.get("id") or ""))
        _refuse_same_identity(destination_root, pack)
        _confined(destination_root, pack_id, stamp)
        final = destination_root / pack_id / stamp
        if final.exists():
            raise ModelError("working copy", "timestamp", f"a new directory, not {stamp}")
        final.parent.mkdir(parents=True, exist_ok=True)
        os.rename(temp, final)
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    try:
        mark_selected(destination_root, pack_id, stamp)
    except Exception:
        shutil.rmtree(final, ignore_errors=True)
        raise
    rows = _signature_rows(final, pack, requirements, trust)
    return final, rows


def import_posted_zip(root: Path, keys: Path, payload: bytes) -> str:
    """Install an uploaded archive and open the same comparison list Extract uses."""
    from urllib.parse import quote

    from common.keystore import trust_store
    from requirements.workspace import read_selection

    selection = read_selection(root)
    installed, _rows = import_pack_zip(payload, root, trust_store(keys))
    pack_id = installed.parent.name
    previous = ""
    if (
        isinstance(selection, dict)
        and selection.get("kind") == "working"
        and selection.get("pack_id") == pack_id
        and isinstance(selection.get("timestamp"), str)
        and selection.get("timestamp") != installed.name
    ):
        previous = selection["timestamp"]
    if not previous:
        return "/requirements/copy?imported=1"
    return (
        "/requirements/copy?imported=1&proposal="
        + quote(installed.name, safe="")
        + "&destination="
        + quote(previous, safe="")
    )


def _zip_member(path: Path, directory: Path) -> zipfile.ZipInfo:
    """Record the file's own time. A later export of the same bytes stays the same archive."""
    stamp = time.localtime(path.stat().st_mtime)[:6]
    if stamp[0] < 1980:
        stamp = (1980, 1, 1, 0, 0, 0)
    info = zipfile.ZipInfo(path.relative_to(directory).as_posix(), stamp)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o600 << 16
    return info


def _regular_files(directory: Path) -> list[Path]:
    found = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ModelError("export", "path", "a regular file")
        if path.is_file():
            found.append(path)
    return found


def _archive_files(payload: bytes) -> list[tuple[str, bytes]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile:
        raise ModelError("import", "archive", "a zip archive") from None
    with archive:
        names = []
        for info in archive.infolist():
            _reject_member(info.filename)
            if info.is_dir() or info.filename.endswith("/"):
                continue
            if _symlink_member(info):
                raise ModelError("import", "path", "a regular file")
            names.append(info.filename)
        prefix = _pack_prefix(names)
        files = []
        for info in archive.infolist():
            if info.is_dir() or info.filename.endswith("/"):
                continue
            files.append((_relative(info.filename, prefix), archive.read(info)))
        return files


def _reject_member(name: str) -> None:
    bare = name[:-1] if name.endswith("/") else name
    if (
        not bare
        or bare.startswith("/")
        or bare.startswith("\\")
        or "\\" in bare
        or (len(bare) > 1 and bare[1] == ":")
    ):
        raise ModelError("import", "path", "a path inside the archive")
    if any(part in {"", ".", ".."} for part in bare.split("/")):
        raise ModelError("import", "path", "a path inside the archive")


def _symlink_member(info: zipfile.ZipInfo) -> bool:
    return (info.external_attr >> 16) & 0o170000 == 0o120000


def _pack_prefix(names: list[str]) -> str:
    pack_jsons = [name for name in names if name == "pack.json" or name.endswith("/pack.json")]
    if len(pack_jsons) != 1:
        raise ModelError("import", "pack.json", "one pack directory")
    prefix = pack_jsons[0][: -len("pack.json")].rstrip("/")
    if "/" in prefix:
        raise ModelError("import", "pack.json", "one pack directory")
    for name in names:
        if prefix and name != prefix and not name.startswith(prefix + "/"):
            raise ModelError("import", "path", "a path inside the pack directory")
    return prefix


def _relative(name: str, prefix: str) -> str:
    relative = name[len(prefix) + 1 :] if prefix else name
    if not relative or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise ModelError("import", "path", "a path inside the pack directory")
    return relative


def _write_members(temp: Path, files: list[tuple[str, bytes]]) -> None:
    root = temp.resolve()
    for relative, data in files:
        target = (temp / relative).resolve()
        if root != target and root not in target.parents:
            raise ModelError("import", "path", "a path inside the workspace")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _refuse_same_identity(root: Path, pack: dict) -> None:
    pack_id = str(pack.get("id") or "")
    for base in (root / pack_id, root / "published" / pack_id):
        if not base.is_dir():
            continue
        candidates = [base] if (base / "pack.json").is_file() else []
        for child in sorted(base.iterdir()):
            if child.is_dir() and (child / "pack.json").is_file():
                candidates.append(child)
        for directory in candidates:
            found, _requirements = load_pack_directory(directory)
            if (
                found.get("namespace") == pack.get("namespace")
                and found.get("id") == pack.get("id")
                and found.get("version") == pack.get("version")
            ):
                raise ModelError(
                    "pack",
                    "version",
                    f"no pack {pack_id} {pack.get('version')} already in {pack.get('namespace')}",
                )


def _confined(root: Path, pack_id: str, stamp: str) -> Path:
    root_resolved = root.resolve()
    final = (root_resolved / pack_id / stamp).resolve()
    if root_resolved != final and root_resolved not in final.parents:
        raise ModelError("pack", "id", "a directory inside the workspace")
    return final
