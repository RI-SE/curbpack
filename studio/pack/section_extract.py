"""One latest extraction per product pack and section.

The slot lives under the product repository's ``paths.extract_work_dir``
(default ``.curbpack/extract``). Extract overwrites that slot. Apply writes
the pack. Drop deletes only the slot.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import urlencode

from common.errors import ModelError

_SECTION_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def extract_work_root(repo: Path) -> Path:
    """The configured extract directory, confined to the repository."""
    from discovery.studio import created_studio_config, load_studio_config

    loaded = load_studio_config(repo)
    config = loaded if loaded is not None else created_studio_config()
    relative = str(config["paths"]["extract_work_dir"]).strip()
    root = (repo / relative).resolve()
    repo_root = repo.resolve()
    if repo_root not in root.parents:
        raise ModelError("extract", "path", "a directory inside the repository")
    return root


def section_extract_directory(repo: Path, pack_id: str, section_id: str) -> Path:
    """The committed slot for this pack and section. It may not exist yet."""
    base = extract_work_root(repo)
    directory = (base / _pack_name(pack_id) / _section_name(section_id)).resolve()
    _inside(base, directory)
    return directory


def begin_section_extract(repo: Path, pack_id: str, section_id: str) -> Path:
    """An empty incoming directory. The committed slot is left in place until commit."""
    directory = section_extract_directory(repo, pack_id, section_id)
    incoming = directory.with_name(directory.name + ".incoming")
    incoming_work = directory.with_name(directory.name + ".incoming.work")
    base = extract_work_root(repo)
    for path in (incoming, incoming_work):
        _inside(base, path)
        if path.exists():
            _remove_directory(path)
    incoming.mkdir(parents=True)
    return incoming


def commit_section_extract(incoming: Path, when: str) -> Path:
    """Replace the committed slot with ``incoming`` and record ``when``."""
    stamp = when.strip()
    if not stamp or any(char in stamp for char in "\n\r/\\"):
        raise ModelError("extract", "extracted_at", "a timestamp")
    name = incoming.name
    if not name.endswith(".incoming"):
        raise ModelError("extract", "slot", "an incoming extract directory")
    final = incoming.with_name(name[: -len(".incoming")])
    incoming_work = incoming.with_name(name + ".work")
    final_work = final.with_name(final.name + ".work")
    if final.exists():
        _remove_directory(final)
    if final_work.exists():
        _remove_directory(final_work)
    incoming.rename(final)
    if incoming_work.is_dir():
        incoming_work.rename(final_work)
    (final / "extracted-at.txt").write_text(stamp + "\n", encoding="utf-8")
    return final


def read_section_extract(repo: Path, pack_id: str, section_id: str) -> tuple[Path, str] | None:
    """The committed slot and its timestamp, or None when this section has no extract."""
    directory = section_extract_directory(repo, pack_id, section_id)
    stamp_path = directory / "extracted-at.txt"
    if not (directory / "pack.json").is_file() or not stamp_path.is_file():
        return None
    stamp = stamp_path.read_text(encoding="utf-8").strip()
    if not stamp:
        return None
    return directory, stamp


def drop_section_extract(repo: Path, pack_id: str, section_id: str) -> None:
    """Delete the slot and its incoming or diagnostic siblings. The pack is not touched."""
    directory = section_extract_directory(repo, pack_id, section_id)
    base = extract_work_root(repo)
    for path in (
        directory,
        directory.with_name(directory.name + ".work"),
        directory.with_name(directory.name + ".incoming"),
        directory.with_name(directory.name + ".incoming.work"),
    ):
        _inside(base, path)
        if path.exists():
            _remove_directory(path)


def open_incoming_section_extract(root: Path, dest_repo: str, dest_pack: str, section_id: str) -> Path:
    """Resolve a registered product repo and start its section slot."""
    from discovery.repos import find_repo, load_repos, resolve_repo_path

    row = find_repo(load_repos(root), dest_repo)
    if row is None:
        raise ModelError("pack", "repo", f"a registered repository, not {dest_repo}")
    repo = resolve_repo_path(root, str(row.get("path") or ""))
    return begin_section_extract(repo, dest_pack, section_id)


def _drop_section_extract(ws, form: dict) -> str:
    """POST target: delete the slot and return to the section Requirements page."""
    from app.server import _locate_repo_pack, _registered_repo_path

    pack_id = (form.get("pack") or [""])[0].strip()
    repo_id = (form.get("repo") or [""])[0].strip()
    section_id = (form.get("section") or [""])[0].strip()
    if not section_id:
        raise ModelError("section", "id", "the section this extract belongs to")
    located = _locate_repo_pack(ws, pack_id, repo_id)
    if located is None:
        raise ModelError("pack", "id", f"a pack named in curbpack.json, not {pack_id}")
    found_repo, _pack_dir, _pack = located
    drop_section_extract(_registered_repo_path(ws, found_repo), pack_id, section_id)
    return "/requirements/copy?" + urlencode(
        [("pack", pack_id), ("repo", found_repo), ("section", section_id)]
    )


def _pack_name(pack_id: str) -> str:
    if not pack_id or Path(pack_id).name != pack_id or pack_id in {".", ".."}:
        raise ModelError("pack", "id", "a single directory name")
    return pack_id


def _section_name(section_id: str) -> str:
    name = (section_id or "").strip()
    if (
        not _SECTION_NAME.fullmatch(name)
        or name.endswith(".incoming")
        or name.endswith(".work")
    ):
        raise ModelError("section", "id", "a single directory name")
    return name


def _inside(root: Path, path: Path) -> None:
    base = root.resolve()
    resolved = path.resolve()
    if resolved != base and base not in resolved.parents:
        raise ModelError("extract", "path", "a directory inside the repository")


def _remove_directory(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ModelError("extract", "path", "a real directory inside the repository")
    shutil.rmtree(path)
