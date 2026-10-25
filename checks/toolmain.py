"""Shared argv for a Check executable. stdout is one JSON result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(handle, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("check")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--args", required=True)
    ns = parser.parse_args(argv)
    try:
        payload = json.loads(ns.args)
    except json.JSONDecodeError:
        payload = None
    if not isinstance(payload, dict):
        result = {"status": "fail", "detail": "check args are not an object"}
    else:
        try:
            result = handle(ns.repo, ns.check, payload)
        except Exception as exc:
            result = {"status": "fail", "detail": f"check tool failed: {exc}"}
    sys.stdout.write(json.dumps(result) + "\n")
    return 0
