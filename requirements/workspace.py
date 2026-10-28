"""Dated Pack working copies. A new extraction allocates a directory; it does not replace one."""

from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.signing import read_signature
from common.store import load_pack, load_pack_directory, save_pack, save_requirement
from common.validate import validate_requirement
from requirements.extract.assemble import assemble_requirements
from requirements.editing import read_pack_seal
from requirements.extract.adapter import section_provisions


def list_working_copies(root: Path, pack_id: str) -> list[str]:
    directory = root / _pack_id_name(pack_id)
    if not directory.is_dir():
        return []
    names = []
    for child in directory.iterdir():
        if not child.is_dir():
            continue
        if child.name == "published" or child.name.endswith(".work"):
            continue
        names.append(child.name)
    return sorted(names)


def create_extraction_copy(root: Path, pack_id: str, pack: dict, *, at: str | None = None) -> Path:
    if pack.get("id") != pack_id:
        raise ModelError("pack", "id", pack_id)
    if at is not None:
        directory = _copy_directory(root, pack_id, _timestamp_name(at))
        try:
            directory.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise ModelError("working copy", "timestamp", f"a new directory, not {at}") from None
        save_pack(directory, pack)
        return directory
    moment = datetime.now(timezone.utc).replace(microsecond=0)
    for offset in range(5):
        stamp = (moment + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H%M%SZ")
        directory = _copy_directory(root, pack_id, stamp)
        try:
            directory.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        save_pack(directory, pack)
        return directory
    raise ModelError("working copy", "timestamp", "a free second within five attempts")


def select_working_copy(root: Path, pack_id: str, timestamp: str) -> Path:
    directory = _copy_directory(root, pack_id, _timestamp_name(timestamp))
    if not directory.is_dir():
        raise ModelError("working copy", "timestamp", f"an existing directory, not {timestamp}")
    pack_path = directory / "pack.json"
    if not pack_path.is_file():
        raise ModelError("working copy", "pack.json", "present")
    pack = load_pack(pack_path)
    if pack.get("id") != pack_id:
        raise ModelError("working copy", "id", pack_id)
    return directory


def load_working_copy(directory: Path) -> tuple[dict, list[dict]]:
    return load_pack_directory(directory)


_RESERVED_ROOT_NAMES = frozenset(
    {"published", "jobs", "packs", "product", "keys", "adapters"}
)


def mark_selected(root: Path, pack_id: str, timestamp: str) -> Path:
    """Remember which working copy the UI is editing. The copy itself is not written."""
    directory = select_working_copy(root, pack_id, timestamp)
    write_json(
        root / "selection.json",
        {"kind": "working", "pack_id": pack_id, "timestamp": directory.name},
    )
    return directory


def mark_published_selected(root: Path, pack_id: str, version: str) -> Path:
    """Remember a published Pack for pilot UI. Does not rewrite curbpack.json or the release."""
    directory = select_published_pack(root, pack_id, version)
    write_json(
        root / "selection.json",
        {"kind": "published", "pack_id": pack_id, "version": directory.name},
    )
    return directory


def resolve_copy_ref(root: Path, pack_id: str, ref: str) -> Path:
    """A working-copy timestamp, or ``published:<version>``."""
    if ref.startswith("published:"):
        return select_published_pack(root, pack_id, ref.split(":", 1)[1])
    return select_working_copy(root, pack_id, ref)


def select_published_pack(root: Path, pack_id: str, version: str) -> Path:
    pack_id = _pack_id_name(pack_id)
    version = _version_name(version)
    directory = root / "published" / pack_id / version
    if not directory.is_dir():
        raise ModelError("published pack", "version", f"an existing directory, not {version}")
    pack_path = directory / "pack.json"
    if not pack_path.is_file():
        raise ModelError("published pack", "pack.json", "present")
    pack = load_pack(pack_path)
    if pack.get("id") != pack_id:
        raise ModelError("published pack", "id", pack_id)
    return directory


def list_published_versions(root: Path, pack_id: str) -> list[str]:
    directory = root / "published" / _pack_id_name(pack_id)
    if not directory.is_dir():
        return []
    names = []
    for child in directory.iterdir():
        if child.is_dir() and (child / "pack.json").is_file():
            names.append(child.name)
    return sorted(names)


def list_pack_ids(root: Path) -> list[str]:
    found: set[str] = set()
    if not root.is_dir():
        return []
    for child in root.iterdir():
        if not child.is_dir() or child.name.startswith(".") or child.name in _RESERVED_ROOT_NAMES:
            continue
        if list_working_copies(root, child.name):
            found.add(child.name)
    published = root / "published"
    if published.is_dir():
        for child in published.iterdir():
            if child.is_dir() and list_published_versions(root, child.name):
                found.add(child.name)
    return sorted(found)


def list_pack_options(root: Path) -> list[dict]:
    """Filesystem Pack choices for the pilot selector. Not a Packs v2 registry."""
    options: list[dict] = []
    for pack_id in list_pack_ids(root):
        for stamp in list_working_copies(root, pack_id):
            directory = root / pack_id / stamp
            pack = _pack_meta(directory)
            options.append(
                {
                    "kind": "working",
                    "pack_id": pack_id,
                    "ref": stamp,
                    "name": pack.get("name") or pack_id,
                    "version": pack.get("version") or "",
                    "state": "working",
                    "path": directory,
                }
            )
        for version in list_published_versions(root, pack_id):
            directory = root / "published" / pack_id / version
            pack = _pack_meta(directory)
            options.append(
                {
                    "kind": "published",
                    "pack_id": pack_id,
                    "ref": version,
                    "name": pack.get("name") or pack_id,
                    "version": pack.get("version") or version,
                    "state": "published",
                    "path": directory,
                }
            )
    return options


def read_selection(root: Path) -> dict | None:
    path = root / "selection.json"
    if not path.is_file():
        return None
    document = read_json(path)
    if not isinstance(document, dict):
        return None
    pack_id = document.get("pack_id")
    if not isinstance(pack_id, str) or not pack_id:
        return None
    kind = document.get("kind")
    if kind is None and isinstance(document.get("timestamp"), str):
        kind = "working"
    if kind == "working":
        timestamp = document.get("timestamp")
        if not isinstance(timestamp, str):
            return None
        try:
            timestamp = _timestamp_name(timestamp)
        except ModelError:
            return None
        return {"kind": "working", "pack_id": pack_id, "timestamp": timestamp}
    if kind == "published":
        version = document.get("version")
        if not isinstance(version, str):
            return None
        try:
            version = _version_name(version)
        except ModelError:
            return None
        return {"kind": "published", "pack_id": pack_id, "version": version}
    return None


def resolve_selected_pack(root: Path) -> Path | None:
    selection = read_selection(root)
    if selection is None:
        return None
    try:
        if selection["kind"] == "working":
            return select_working_copy(root, selection["pack_id"], selection["timestamp"])
        return select_published_pack(root, selection["pack_id"], selection["version"])
    except ModelError:
        return None


def ensure_default_selection(root: Path) -> dict | None:
    """Initial default only. Never replaces an explicit selection that still resolves."""
    if resolve_selected_pack(root) is not None:
        return read_selection(root)
    options = list_pack_options(root)
    working = [item for item in options if item["kind"] == "working"]
    if working:
        latest = max(working, key=lambda item: item["ref"])
        mark_selected(root, latest["pack_id"], latest["ref"])
        return read_selection(root)
    published = [item for item in options if item["kind"] == "published"]
    if published:
        chosen = sorted(published, key=lambda item: (item["pack_id"], item["ref"]))[-1]
        mark_published_selected(root, chosen["pack_id"], chosen["ref"])
        return read_selection(root)
    return None


def selected_copy(root: Path, pack_id: str) -> Path | None:
    selection = read_selection(root)
    if selection is None or selection.get("pack_id") != pack_id:
        return None
    if selection.get("kind") != "working":
        return None
    timestamp = selection.get("timestamp")
    if not isinstance(timestamp, str):
        return None
    directory = _copy_directory(root, pack_id, timestamp)
    if not directory.is_dir():
        return None
    return directory


def _pack_meta(directory: Path) -> dict:
    path = directory / "pack.json"
    if not path.is_file():
        return {}
    try:
        pack = load_pack(path)
    except Exception:
        return {}
    return pack if isinstance(pack, dict) else {}


def _version_name(version: str) -> str:
    if not version or Path(version).name != version or version in {".", ".."}:
        raise ModelError("published pack", "version", "a single directory name")
    return version


def mark_source_adapter(root: Path, adapter_id: str) -> str:
    """Remember which regulation source the Requirements UI is using."""
    adapter_id = str(adapter_id or "").strip()
    if not adapter_id:
        raise ModelError("source", "adapter_id", "a non-empty adapter id")
    write_json(root / "source_adapter.json", {"adapter_id": adapter_id})
    return adapter_id


def selected_source_adapter(root: Path, *, default: str = "cra") -> str:
    path = root / "source_adapter.json"
    if not path.is_file():
        return default
    document = read_json(path)
    if not isinstance(document, dict):
        return default
    adapter_id = document.get("adapter_id")
    if not isinstance(adapter_id, str) or not adapter_id:
        return default
    return adapter_id


def list_publication_blockers(root: Path, directory: Path, trust: dict[str, bytes]) -> list[str]:
    """Reasons `publish_pack` would refuse this copy. Coverage is not one of them."""
    blockers: list[str] = []
    pack, requirements = load_working_copy(directory)
    version = pack.get("version")
    pack_id = pack.get("id")
    if isinstance(version, str) and version and isinstance(pack_id, str) and pack_id:
        try:
            destination = root / "published" / _pack_id_name(pack_id) / version
        except ModelError as exc:
            blockers.append(str(exc))
        else:
            if destination.exists():
                blockers.append(f"published version {version} already exists")
    else:
        blockers.append("pack.version is missing")
    if not requirements:
        blockers.append("the working copy has no requirements")
    for requirement in requirements:
        requirement_id = str(requirement.get("id") or "?")
        try:
            checked = validate_requirement(requirement, published=True)
        except ModelError as exc:
            blockers.append(str(exc))
            if not isinstance(requirement.get("signed"), dict):
                blockers.append(f"{requirement_id}: unsigned")
            continue
        reading = read_signature(checked, trust, what="requirement")
        if not reading["verifiable"]:
            blockers.append(f"{requirement_id}: {reading.get('reason') or 'signature does not verify'}")
    seal = read_pack_seal(directory, trust)
    if not seal["verifiable"]:
        blockers.append(str(seal.get("reason") or "pack directory seal does not verify"))
    return blockers


def publish_pack(root: Path, copy_dir: Path, *, version: str, trust: dict[str, bytes]) -> Path:
    """Copy a sealed working copy to a new immutable release directory.

    Coverage diagnostics are not consulted. A release does not certify that
    every source provision was written.
    """
    pack = _require_publishable(copy_dir, version, trust)
    destination = root / "published" / _pack_id_name(pack["id"]) / version
    if destination.exists():
        raise ModelError("published pack", "version", f"a new directory, not {version}")
    temp = root / f".publish-tmp-{secrets.token_hex(8)}"
    try:
        temp.mkdir(parents=True, exist_ok=False)
        for path in sorted(copy_dir.glob("*.json")):
            if path.is_file():
                (temp / path.name).write_bytes(path.read_bytes())
        _require_publishable(temp, version, trust)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.rename(temp, destination)
        except OSError:
            raise ModelError("published pack", "version", f"a new directory, not {version}") from None
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    return destination


def _require_publishable(directory: Path, version: str, trust: dict[str, bytes]) -> dict:
    pack, requirements = load_working_copy(directory)
    if pack.get("version") != version:
        raise ModelError("pack", "version", version)
    if not requirements:
        raise ModelError("pack", "requirements", "at least one requirement")
    for requirement in requirements:
        checked = validate_requirement(requirement, published=True)
        reading = read_signature(checked, trust, what="requirement")
        if not reading["verifiable"]:
            raise ModelError(
                f"requirement {checked['id']}",
                "signed",
                "a signature that verifies",
            )
    seal = read_pack_seal(directory, trust)
    if not seal["verifiable"]:
        raise ModelError("pack", "signed", "a directory seal that verifies")
    return pack


def extract_section(
    root: Path,
    adapter_dir: Path,
    adapter: dict,
    section_id: str,
    proposals: list[dict],
    pack: dict,
    *,
    at: str | None = None,
    llm_notes: list | None = None,
) -> dict:
    """Atomize one ready section into a new working copy. A stub raises first."""
    extracted = section_provisions(adapter_dir, adapter, section_id)
    provisions = [
        {"locus": item["locus"], "law_text": item["law_text"]}
        for item in extracted["provisions"]
    ]
    source_diagnostics = list(extracted.get("diagnostics") or [])
    requirements, exclusions = assemble_requirements(provisions, proposals, adapter=adapter)
    copy = create_extraction_copy(root, pack["id"], pack, at=at)
    work = work_directory(copy)
    try:
        for requirement in requirements:
            save_requirement(copy, requirement, published=False)
    except ModelError as exc:
        _write_extract_diagnostics(
            work,
            provisions,
            exclusions,
            status="failed",
            error=str(exc),
            source_diagnostics=source_diagnostics,
            extracted=extracted,
        )
        raise
    status = "incomplete" if exclusions or source_diagnostics else "written"
    if not provisions:
        status = "incomplete"
        source_diagnostics = source_diagnostics or [
            {"reason": "no provisions extracted from the selected section"}
        ]
    _write_extract_diagnostics(
        work,
        provisions,
        exclusions,
        status=status,
        source_diagnostics=source_diagnostics,
        extracted=extracted,
    )
    if llm_notes:
        write_json(work / "llm.json", {"llm": list(llm_notes)})
    return {
        "copy": copy,
        "work": work,
        "requirements": requirements,
        "exclusions": exclusions,
        "source_diagnostics": source_diagnostics,
    }


def work_directory(copy_dir: Path) -> Path:
    return copy_dir.parent / f"{copy_dir.name}.work"


def _pack_id_name(pack_id: str) -> str:
    if not pack_id or Path(pack_id).name != pack_id or pack_id in {".", ".."}:
        raise ModelError("pack", "id", "a single directory name")
    return pack_id


def _copy_directory(root: Path, pack_id: str, timestamp: str) -> Path:
    return root / _pack_id_name(pack_id) / timestamp


def _write_extract_diagnostics(
    work: Path,
    provisions: list[dict],
    exclusions: list[dict],
    *,
    status: str,
    error: str | None = None,
    source_diagnostics: list | None = None,
    extracted: dict | None = None,
) -> None:
    work.mkdir(parents=True, exist_ok=True)
    reasons = {item["locus"]: item["reason"] for item in exclusions}
    loci = []
    seen: set[str] = set()
    for provision in provisions:
        locus = provision["locus"]
        seen.add(locus)
        if locus in reasons:
            loci.append({"locus": locus, "status": "excluded", "reason": reasons[locus]})
        else:
            loci.append({"locus": locus, "status": "written"})
    for locus, reason in reasons.items():
        if locus not in seen:
            loci.append({"locus": locus, "status": "excluded", "reason": reason})
    coverage = {"status": status, "loci": loci}
    if error is not None:
        coverage["error"] = error
    if source_diagnostics:
        coverage["source_diagnostics"] = list(source_diagnostics)
    payload = {"provisions": provisions}
    if extracted is not None:
        payload["section_id"] = extracted.get("section_id")
        payload["source_file"] = extracted.get("file")
        payload["source_kind"] = extracted.get("kind")
        if extracted.get("diagnostics"):
            payload["diagnostics"] = list(extracted["diagnostics"])
    write_json(work / "provisions.json", payload)
    write_json(work / "coverage.json", coverage)


def _timestamp_name(timestamp: str) -> str:
    if not timestamp or Path(timestamp).name != timestamp or timestamp in {".", ".."}:
        raise ModelError("working copy", "timestamp", "a single directory name")
    return timestamp
