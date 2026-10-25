"""Start the command recorded for a Check id.

The registry command is the executable. This module does not import a Check
implementation, so a new tool is a new executable plus a registry row.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_check_tool(repo: Path, command: str, check: str, args: dict) -> dict:
    """argv: <command> <check-id> --repo <path> --args <json>. stdout is one result object."""
    argv = [command, check, "--repo", str(repo), "--args", json.dumps(args)]
    kwargs = {"capture_output": True, "text": True}
    if getattr(sys, "frozen", False):
        kwargs["executable"] = sys.executable
    else:
        root = Path(__file__).resolve().parents[1]
        bin_dir = Path(__file__).resolve().parent / "bin"
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(part for part in (str(root), env.get("PYTHONPATH", "")) if part)
        env["PATH"] = os.pathsep.join(part for part in (str(bin_dir), env.get("PATH", "")) if part)
        kwargs["env"] = env
    try:
        completed = subprocess.run(argv, **kwargs)
    except OSError:
        return {"status": "fail", "detail": f"check tool {command!r} is unavailable"}
    return _result(command, completed)


def _result(command: str, completed: subprocess.CompletedProcess) -> dict:
    text = completed.stdout.strip()
    parsed = None
    if text:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
    if isinstance(parsed, dict) and parsed.get("status") == "pass" and completed.returncode == 0:
        return {"status": "pass"}
    if isinstance(parsed, dict) and parsed.get("status") == "fail":
        detail = parsed.get("detail")
        if isinstance(detail, str) and detail.strip():
            return {"status": "fail", "detail": detail}
    return {"status": "fail", "detail": f"check tool {command!r} failed"}
