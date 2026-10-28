"""Run curbcheck on a product repo and write one run result.

A packaged build is one file. When that file is started with argv0 set to a
registered command, it runs that command. A source checkout still starts the
programs in checks/bin.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from checks.commands import contents_handle, exist_handle, git_handle, node_handle
from checks.run import curbpack_directory, run_and_write
from checks.schema import load_registry
from checks.toolmain import main as tool_main

_HANDLERS = {
    "curbcheck-exist": exist_handle,
    "curbcheck-contents": contents_handle,
    "curbcheck-git": git_handle,
    "curbcheck-node": node_handle,
}


def _registered_commands() -> set[str]:
    return {item["command"] for item in load_registry()["checks"] if isinstance(item.get("command"), str)}


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv if argv is None else argv
    command = Path(raw[0]).name
    if command in _registered_commands():
        return _tool(command, raw[1:])
    return _cli(raw if argv is not None else raw[1:])


def _tool(command: str, argv: list[str]) -> int:
    handle = _HANDLERS.get(command)
    if handle is None:
        sys.stdout.write(
            json.dumps({"status": "fail", "detail": f"check tool {command!r} is unavailable"}) + "\n"
        )
        return 0
    return tool_main(handle, argv)


def _cli(argv: list[str] | None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate claims and write a Packs v2 run result.")
    parser.add_argument(
        "--repo",
        type=Path,
        help="Product repository. Defaults to the current directory when it contains curbpack.json.",
    )
    parser.add_argument(
        "--packs",
        type=Path,
        help="Directory that contains <pack-id>/pack.json. Default: <repo>/<curbpack>/packs.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Run result file. Default: <repo>/<curbpack>/run-result.json.",
    )
    parser.add_argument("--skip", action="append", default=[], help="claim-id=reason")
    args = parser.parse_args(argv)
    repo = args.repo
    if repo is None:
        cwd = Path.cwd()
        if (cwd / "curbpack.json").is_file():
            repo = cwd
        else:
            parser.error("--repo is required when the current directory has no curbpack.json")
    directory = curbpack_directory(repo)
    packs = args.packs if args.packs is not None else directory / "packs"
    out = args.out if args.out is not None else directory / "run-result.json"
    skip = {}
    for item in args.skip:
        if "=" not in item:
            print(f"skip needs claim-id=reason, got {item!r}", file=sys.stderr)
            return 2
        claim_id, reason = item.split("=", 1)
        skip[claim_id] = reason
    result, code = run_and_write(repo, packs, out, skip=skip or None)
    print(f"wrote {out}")
    print(f"claims {len(result['claims'])} exit {code}")
    if result.get("worktree") == "dirty":
        print("worktree dirty: this result is not verification of that commit's exact content")
    for row in result["claims"]:
        print(f"{row['status']:7} {row['id']}")
        for item in row.get("checks") or []:
            detail = f" — {item['detail']}" if item.get("detail") else ""
            print(f"  {item['status']:7} [{item['index']}] {item['check']}{detail}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
