"""List directories for the Add-repo path picker (local Studio only)."""

from __future__ import annotations

from pathlib import Path

from common.errors import ModelError


def list_directories(path: str = "", *, start: Path | None = None) -> dict:
    """Return cwd, optional parent, and child directory names for navigation.

    Does not return file contents. Paths are absolute strings the process can see.
    """
    raw = (path or "").strip()
    if raw:
        candidate = Path(raw).expanduser()
    elif start is not None:
        candidate = Path(start)
    else:
        candidate = Path.home()
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ModelError("browse", "path", f"an existing directory, not {candidate}") from exc
    except OSError as exc:
        raise ModelError("browse", "path", f"a readable directory, not {candidate}") from exc
    if not resolved.is_dir():
        raise ModelError("browse", "path", f"a directory, not {resolved}")
    entries: list[dict] = []
    try:
        children = sorted(resolved.iterdir(), key=lambda p: p.name.lower())
    except OSError as exc:
        raise ModelError("browse", "path", f"a readable directory, not {resolved}") from exc
    for child in children:
        try:
            if child.is_dir():
                entries.append({"name": child.name, "path": str(child.resolve())})
        except OSError:
            continue
    parent = resolved.parent
    parent_path = str(parent) if parent != resolved else ""
    return {
        "path": str(resolved),
        "parent": parent_path,
        "dirs": entries,
    }
