"""Node Checks. Invoked by curbcheck-node.

`dep_ban` (and registry aliases) inspects the repository-root package.json
dependency maps. A pin whose written version string equals an entry in
banned_versions is a fail. Later operators (>, <, ranges) can extend this
Check without a new command.
"""

from __future__ import annotations

import json
from pathlib import Path

_MAPS = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")


def run_dep_ban(repo: Path, args: dict) -> dict:
    package = args["package"]
    banned = list(args["banned_versions"])
    manifest = repo / "package.json"
    if not manifest.is_file():
        return {"status": "pass"}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"status": "fail", "detail": f"package.json is unreadable ({exc})"}
    if not isinstance(data, dict):
        return {"status": "fail", "detail": "package.json is not an object"}
    hits = []
    for map_name in _MAPS:
        section = data.get(map_name)
        if not isinstance(section, dict):
            continue
        raw = section.get(package)
        if not isinstance(raw, str):
            continue
        if raw in banned:
            hits.append(f"{map_name}.{package}={raw}")
    if hits:
        return {
            "status": "fail",
            "detail": f"banned pin {package}: " + "; ".join(hits),
        }
    return {"status": "pass"}
