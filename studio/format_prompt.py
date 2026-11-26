"""Convert one older saved JSON file to the current format.

Opening a file does not ask and does not write. A normal save keeps the
format that was already on disk. Convert asks about that one file: Convert
writes format_version 1, and Cancel leaves the bytes alone.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from common.errors import ModelError

_READERS = {
    "requirement": "read_requirement",
    "pack": "read_pack",
    "claim": "read_claim",
    "curbpack": "read_curbpack",
    "review_items": "read_review_items",
}


def _reader(kind: str):
    if kind == "curbpack":
        from common.validate import read_curbpack

        return read_curbpack
    if kind == "review_items":
        from studio.review.impl.items import read_review_items

        return read_review_items
    from common import store

    name = _READERS.get(kind)
    if name is None:
        return None
    return getattr(store, name)


def file_key(kind: str, fields: dict[str, str]) -> str:
    """Stable identity for one file on the page that asked."""
    if kind == "pack":
        return "pack:" + fields.get("pack", "")
    if kind == "claim":
        return "claim:" + fields.get("claim", "")
    if kind == "requirement":
        stamp = fields.get("timestamp") or fields.get("pack") or ""
        return "requirement:" + fields.get("requirement", "") + ":" + stamp
    return kind


def _stored_behind(path: Path, kind: str) -> tuple[int, int] | None:
    reader = _reader(kind)
    if reader is None or not path.is_file():
        return None
    try:
        _document, read_version, current_version = reader(path)
    except (ModelError, OSError, ValueError):
        return None
    if read_version >= current_version:
        return None
    return read_version, current_version


def compatibility_form(
    path: Path,
    kind: str,
    *,
    next_path: str,
    fields: dict[str, str],
    label: str | None = None,
) -> str:
    """One convert-or-cancel form when this file's stored version is older."""
    versions = _stored_behind(path, kind)
    if versions is None:
        return ""
    read_version, current_version = versions
    name = label or path.name
    form_id = "format-upgrade-" + re.sub(r"[^A-Za-z0-9._-]+", "-", file_key(kind, fields))
    hidden = [
        f'<input type="hidden" name="kind" value="{html.escape(kind)}">',
        f'<input type="hidden" name="next" value="{html.escape(next_path)}">',
    ]
    for key, value in fields.items():
        if value:
            hidden.append(
                f'<input type="hidden" name="{html.escape(key)}" value="{html.escape(value)}">'
            )
    return (
        f'<form method="post" action="/format-upgrade" class="format-upgrade" id="{html.escape(form_id)}">'
        f"<p>Convert {html.escape(name)} from format version {read_version} "
        f"to version {current_version}?</p>"
        + "".join(hidden)
        + '<p class="actions">'
        '<button type="submit" name="format_upgrade" value="upgrade">Convert</button>'
        '<button type="submit" name="format_upgrade" value="cancel">Cancel</button>'
        "</p></form>"
    )


def compatibility_forms(candidates: list[dict], *, next_path: str) -> str:
    """One form per older file. Each form converts only that file."""
    parts = []
    for item in candidates:
        parts.append(
            compatibility_form(
                item["path"],
                item["kind"],
                next_path=next_path,
                fields=item["fields"],
                label=item.get("label") or item["path"].name,
            )
        )
    return "".join(parts)


def _document_to_save(path: Path, kind: str):
    reader = _reader(kind)
    if reader is None or not path.is_file():
        return None
    document, read_version, current_version = reader(path)
    if read_version >= current_version:
        return None
    return document


def apply_format_upgrade(ws, form: dict) -> str:
    """Convert writes version 1. Cancel returns without writing."""
    from app.server import _open_requirement, _registered_repo_path, _safe_local_next

    next_path = _safe_local_next((form.get("next") or ["/"])[0]) or "/"
    if (form.get("format_upgrade") or [""])[0] != "upgrade":
        return next_path
    kind = (form.get("kind") or [""])[0].strip()
    repo_id = (form.get("repo") or [""])[0].strip()
    try:
        if kind == "requirement":
            requirement_id = (form.get("requirement") or [""])[0].strip()
            directory, _pack, requirement = _open_requirement(ws, requirement_id, form)
            if directory is None or requirement is None:
                return next_path
            from common.store import save_requirement

            document = _document_to_save(directory / f"{requirement_id}.json", "requirement")
            if document is None:
                return next_path
            save_requirement(directory, document)
            return next_path
        if not repo_id:
            return next_path
        repo = _registered_repo_path(ws, repo_id)
        if kind == "pack":
            from app.server import _locate_repo_pack
            from common.store import save_pack

            located = _locate_repo_pack(ws, (form.get("pack") or [""])[0].strip(), repo_id)
            if located is None:
                return next_path
            _repo_id, pack_dir, _listed = located
            document = _document_to_save(pack_dir / "pack.json", "pack")
            if document is None:
                return next_path
            save_pack(pack_dir, document)
            return next_path
        if kind == "claim":
            from common.store import _safe_id, save_claim
            from discovery.door import repo_claims_dir

            claim_id = _safe_id((form.get("claim") or [""])[0].strip(), "claim")
            folder = repo_claims_dir(repo)
            path = (folder / f"{claim_id}.json").resolve()
            path.relative_to(folder.resolve())
            document = _document_to_save(path, "claim")
            if document is None:
                return next_path
            save_claim(folder, document)
            return next_path
        if kind == "curbpack":
            from common.validate import save_curbpack

            path = repo / "curbpack.json"
            document = _document_to_save(path, "curbpack")
            if document is None:
                return next_path
            save_curbpack(path, document)
            return next_path
        if kind == "review_items":
            from studio.review.impl.items import items_home, save_review_items

            raw = (form.get("result") or [""])[0].strip()
            if not raw:
                return next_path
            result = Path(raw).resolve()
            result.relative_to(repo.resolve())
            path = items_home(repo, result)
            path.resolve().relative_to(repo.resolve())
            document = _document_to_save(path, "review_items")
            if document is None:
                return next_path
            save_review_items(path, document)
            return next_path
    except (ModelError, OSError, ValueError):
        return next_path
    return next_path
