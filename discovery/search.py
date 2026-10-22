"""Working-tree file search.

Reads `discovery_hints` concepts and path hints, plus the repo hunt
exclude/prefer globs. Prefer globs only order paths that already match a
path hint or a concept. It does not read `source` or `args`. Candidates are
returned to the caller and are not stored.
"""

from __future__ import annotations

import fnmatch
import html
from pathlib import Path

from common.errors import ModelError


def glob_hit(rel: str, pattern: str) -> bool:
    """Case-insensitive glob. `**` is a directory wildcard, not a regexp."""
    rel = rel.replace("\\", "/").lower()
    pattern = pattern.replace("\\", "/").lower()
    name = rel.rsplit("/", 1)[-1]
    if fnmatch.fnmatchcase(rel, pattern) or fnmatch.fnmatchcase(name, pattern):
        return True
    if pattern.startswith("**/"):
        return glob_hit(rel, pattern[3:])
    if pattern.endswith("/**"):
        prefix = pattern[:-3].lstrip("/")
        return bool(prefix) and (rel == prefix or rel.startswith(prefix + "/"))
    return False


def excluded(rel: str, patterns: list[str]) -> bool:
    return any(glob_hit(rel, pattern) for pattern in patterns)


def iter_markdown(repo: Path, exclude: list[str]) -> list[Path]:
    root = repo.resolve()
    found = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        try:
            rel_path = path.resolve().relative_to(root)
        except ValueError:
            continue
        if any(part.startswith(".") for part in rel_path.parts):
            continue
        rel = rel_path.as_posix()
        if excluded(rel, exclude):
            continue
        found.append(path.resolve())
    return sorted(found, key=lambda item: item.as_posix())


def _excerpt(body: str, concepts: list[str]) -> str:
    lines = body.splitlines()
    needles = [concept.lower() for concept in concepts if concept.strip()]
    for index, line in enumerate(lines):
        low = line.lower()
        if any(needle in low for needle in needles):
            start = max(0, index - 1)
            end = min(len(lines), index + 2)
            return "\n".join(lines[start:end]).strip()
    return ""


def read_source_text(repo: Path, locator: str) -> str:
    """Return the text of one repo-relative locator. Does not search or write."""
    if not isinstance(locator, str) or not locator.strip():
        raise ModelError("source", "path", "a repo-relative path")
    if locator.startswith("/") or locator.startswith("\\"):
        raise ModelError("source", "path", "a repo-relative path")
    parts = locator.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        raise ModelError("source", "path", "a path inside the repository")
    root = repo.resolve()
    path = (root / locator).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ModelError("source", "path", "a path inside the repository") from exc
    if not path.is_file():
        raise ModelError("source", "path", f"an existing file, not {locator}")
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ModelError("source", "path", f"a readable file ({exc})") from exc


def verify_excerpt(body: str, excerpt: str) -> tuple[int, int] | None:
    """Exact substring after strip. Whitespace folding is not a match."""
    if not isinstance(excerpt, str):
        return None
    needle = excerpt.strip()
    if not needle or not isinstance(body, str):
        return None
    index = body.find(needle)
    if index < 0:
        return None
    return index, index + len(needle)


def highlight_verified(body: str, excerpt: str) -> tuple[str, bool]:
    """Escape the file text and mark an exact excerpt. A miss is unmarked."""
    span = verify_excerpt(body, excerpt)
    if span is None:
        return html.escape(body), False
    start, end = span
    return (
        html.escape(body[:start]) + "<mark>" + html.escape(body[start:end]) + "</mark>" + html.escape(body[end:]),
        True,
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def discover_candidates(
    repo: Path,
    requirement: dict,
    config: dict,
    *,
    limit: int = 40,
) -> list[dict]:
    """Return candidate dicts. Does not write a file and does not create a Claim."""
    hints = requirement.get("discovery_hints") or {}
    hunt = (config or {}).get("hunt") or {}
    # `sources` and `args` are intentionally unused. expected_evidence is stored
    # on the requirement and is not a match key.
    concepts = [item for item in (hints.get("concepts") or []) if isinstance(item, str)]
    path_hints = [item for item in (hints.get("path_hints") or []) if isinstance(item, str)]
    exclude = [item for item in (hunt.get("exclude_path_globs") or []) if isinstance(item, str)]
    prefer = [item for item in (hunt.get("prefer_path_globs") or []) if isinstance(item, str)]

    identified: list[tuple[int, int, str, dict]] = []
    for path in iter_markdown(repo, exclude):
        rel = path.relative_to(repo.resolve()).as_posix()
        path_hits = [hint for hint in path_hints if glob_hit(rel, hint)]
        body = _read_text(path) if path_hits or concepts else ""
        concept_hits: list[str] = []
        if concepts and body:
            low = body.lower()
            concept_hits = [concept for concept in concepts if concept.lower() in low]
        if path_hits:
            matched_by = "path_hint"
        elif concept_hits:
            matched_by = "concept"
        else:
            continue
        prefer_hit = bool(prefer) and any(glob_hit(rel, pattern) for pattern in prefer)
        identified.append(
            (
                0 if matched_by == "path_hint" else 1,
                0 if prefer_hit else 1,
                rel,
                {
                    "path": rel,
                    "matched_by": matched_by,
                    "matched_hints": path_hits + concept_hits,
                    "excerpt": _excerpt(body, concepts),
                },
            )
        )
    identified.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in identified[:limit]]
