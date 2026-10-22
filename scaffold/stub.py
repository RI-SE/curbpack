"""Write a short, obviously unfinished document. Never marks it approved."""

from __future__ import annotations

from pathlib import Path

from common.errors import ModelError

MARKER = "curbpack-scaffold: incomplete stub. Not approved evidence."

STUB_BODY = f"""<!-- {MARKER} -->
# Incomplete stub

Not approved evidence. Generated because a file was missing.
"""


def write_stub(repo: Path, relative: str) -> Path:
    if relative.startswith("/") or ".." in relative.split("/"):
        raise ModelError("scaffold", "path", "a relative path inside the repository")
    path = (repo / relative).resolve()
    root = repo.resolve()
    if path != root and root not in path.parents:
        raise ModelError("scaffold", "path", "a relative path inside the repository")
    if path.exists():
        raise ModelError("scaffold", "path", "a path that does not already exist")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(STUB_BODY, encoding="utf-8")
    return path


def is_stub(path: Path) -> bool:
    if not path.is_file():
        return False
    return MARKER in path.read_text(encoding="utf-8", errors="replace")
