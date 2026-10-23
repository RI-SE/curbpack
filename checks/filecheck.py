"""exist and contents. Invoked by curbcheck-exist and curbcheck-contents."""

from __future__ import annotations

import json
import re
from pathlib import Path

from common.errors import CheckError, ModelError

# A contents/placeholder probe fails when one of these is present.
# This is the PoC list, not a claim that it matches every curbcheck build.
_PLACEHOLDERS = (
    re.compile(r"(?i)\blorem ipsum\b"),
    re.compile(r"(?i)\bTODO\b"),
    re.compile(r"(?i)\bTBD\b"),
    re.compile(r"(?i)\bFIXME\b"),
    re.compile(r"(?i)\bplaceholder\b"),
    re.compile(r"(?i)<placeholder>"),
)


def _inside(repo: Path, relative: str) -> Path:
    root = repo.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise ModelError("check", "args.path", "a path inside the repository")
    return path


def _targets(args: dict) -> list[str]:
    if "paths" in args:
        return list(args["paths"])
    return [args["path"]]


def run_exist(repo: Path, args: dict) -> dict:
    missing = [rel for rel in _targets(args) if not _inside(repo, rel).is_file()]
    if missing:
        return {"status": "fail", "detail": "; ".join(f"{rel} is absent" for rel in missing)}
    return {"status": "pass"}


def _compare(actual: int, op: str, expected: int) -> bool:
    if op == ">":
        return actual > expected
    if op == ">=":
        return actual >= expected
    if op == "<":
        return actual < expected
    if op == "<=":
        return actual <= expected
    raise ModelError("contents", "op", "> >= < or <=")


def repo_tokens(repo: Path) -> list[str]:
    tokens = [repo.resolve().name]
    package = repo / "package.json"
    if package.is_file():
        try:
            name = json.loads(package.read_text(encoding="utf-8")).get("name")
        except json.JSONDecodeError:
            name = None
        if isinstance(name, str) and name.strip():
            tokens.append(name.strip())
    gomod = repo / "go.mod"
    if gomod.is_file():
        for line in gomod.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("module "):
                module = line.split(None, 1)[1].strip()
                if module:
                    tokens.append(module)
                break
    unique = []
    for token in tokens:
        if token not in unique:
            unique.append(token)
    return unique


def _probe_failure(repo: Path, path: Path, relative: str, probe: dict) -> str | None:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    kind = probe["kind"]
    if kind == "size":
        if not _compare(len(data), probe["op"], probe["bytes"]):
            return f"{relative} is {len(data)} bytes, not {probe['op']} {probe['bytes']}"
        return None
    if kind == "words":
        count = len(text.split())
        if not _compare(count, probe["op"], probe["n"]):
            return f"{relative} has {count} words, not {probe['op']} {probe['n']}"
        return None
    if kind == "headers":
        missing = [header for header in probe["headers"] if header not in text]
        if missing:
            return f"{relative} is missing header {missing[0]!r}"
        return None
    if kind == "token":
        tokens = repo_tokens(repo)
        if not any(token and token in text for token in tokens):
            return f"{relative} does not contain the repo token ({', '.join(tokens)})"
        return None
    if kind == "pattern":
        try:
            found = re.search(probe["pattern"], text) is not None
        except re.error as exc:
            raise ModelError("contents", "probes.pattern", f"a valid regular expression ({exc})") from exc
        if found:
            return f"{relative} matches forbidden pattern {probe['pattern']!r}"
        return None
    if kind == "placeholder":
        for compiled in _PLACEHOLDERS:
            match = compiled.search(text)
            if match:
                return f"{relative} contains placeholder text {match.group(0)!r}"
        return None
    raise CheckError(f"unknown probe kind {kind!r}")


def run_contents(repo: Path, args: dict) -> dict:
    missing = [rel for rel in _targets(args) if not _inside(repo, rel).is_file()]
    if missing:
        return {"status": "fail", "detail": "; ".join(f"{rel} is absent" for rel in missing)}
    failures = []
    for rel in _targets(args):
        path = _inside(repo, rel)
        for probe in args["probes"]:
            failure = _probe_failure(repo, path, rel, probe)
            if failure:
                failures.append(failure)
    if failures:
        return {"status": "fail", "detail": "; ".join(failures)}
    return {"status": "pass"}
