"""Run curbcheck on a product repo and print a text summary.

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
from checks.defaults import created_curbpack
from checks.run import new_run_result_path, packs_dir, results_dir, run_repository
from checks.schema import load_registry
from checks.toolmain import main as tool_main
from common.jsonio import dump_text
from common.store import save_run_result

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
    parser = argparse.ArgumentParser(
        description="Evaluate claims and print a text summary. Write JSON only with -j/--json or -o/--out."
    )
    parser.add_argument(
        "--defaults",
        action="store_true",
        help="Print the created-file curbpack.json object and exit. No repository is required.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        help="Product repository. Defaults to the current directory when it contains curbpack.json.",
    )
    parser.add_argument(
        "--packs",
        type=Path,
        help="Directory that contains <pack-id>/<pack-version>/pack.json. Default: packs_dir from curbpack.json.",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="write_json",
        help="Also write {results_dir}/run-result_<UTC>.json.",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        help="Also write the run-result JSON object to PATH.",
    )
    parser.add_argument("--skip", action="append", default=[], help="claim-id=reason")
    args = parser.parse_args(argv)
    if args.defaults:
        sys.stdout.write(dump_text(created_curbpack()))
        return 0
    repo = args.repo
    if repo is None:
        cwd = Path.cwd()
        if (cwd / "curbpack.json").is_file():
            repo = cwd
        else:
            parser.error("--repo is required when the current directory has no curbpack.json")
    packs = args.packs if args.packs is not None else packs_dir(repo)
    skip = {}
    for item in args.skip:
        if "=" not in item:
            print(f"skip needs claim-id=reason, got {item!r}", file=sys.stderr)
            return 2
        claim_id, reason = item.split("=", 1)
        skip[claim_id] = reason
    result, code = run_repository(repo, packs, skip=skip or None)
    if args.write_json:
        dated = new_run_result_path(results_dir(repo))
        save_run_result(dated, result)
        print(f"wrote {dated}")
    if args.out is not None:
        save_run_result(args.out, result)
        print(f"wrote {args.out}")
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
