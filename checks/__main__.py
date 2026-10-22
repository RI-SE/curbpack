"""Run curbcheck on a product repo and write one run result."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from checks.run import run_and_write


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate claims and write a Packs v2 run result.")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--packs", type=Path, required=True, help="Directory that contains <pack-id>/pack.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip", action="append", default=[], help="claim-id=reason")
    args = parser.parse_args(argv)
    skip = {}
    for item in args.skip:
        if "=" not in item:
            print(f"skip needs claim-id=reason, got {item!r}", file=sys.stderr)
            return 2
        claim_id, reason = item.split("=", 1)
        skip[claim_id] = reason
    result, code = run_and_write(args.repo, args.packs, args.out, skip=skip or None)
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
