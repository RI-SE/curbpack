"""Find files that share a name.

Returns repo-relative paths. It does not write a Claim or sign anything.
"""

from __future__ import annotations

from pathlib import Path

_SKIP = {"node_modules", "__pycache__", "venv", ".venv"}


def find_same_name(repo: Path, filename: str) -> list[str]:
    """Paths inside `repo` whose file name equals the last part of `filename`."""
    name = Path(str(filename or "")).name.strip()
    if not name or name in {".", ".."}:
        return []
    root = Path(repo).resolve()
    if not root.is_dir():
        return []
    found: list[str] = []

    def walk(directory: Path) -> None:
        try:
            children = list(directory.iterdir())
        except OSError:
            return
        for child in children:
            if child.name.startswith(".") or child.name in _SKIP:
                continue
            if child.is_dir():
                walk(child)
            elif child.is_file() and child.name == name:
                found.append(child.resolve().relative_to(root).as_posix())

    walk(root)
    return sorted(found)
