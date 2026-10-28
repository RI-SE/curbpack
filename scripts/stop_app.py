"""Stop the local Studio process that is listening on its port."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import time


def pids_from_lsof(text: str) -> list[int]:
    return [int(line) for line in text.split() if line.isdigit()]


def pids_from_ss(text: str) -> list[int]:
    return [int(match) for match in re.findall(r"pid=(\d+)", text)]


def pids_from_netstat(text: str, port: int) -> list[int]:
    suffix = f":{port}"
    found = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0].upper() != "TCP":
            continue
        if parts[3].upper() != "LISTENING":
            continue
        if not parts[1].endswith(suffix):
            continue
        if parts[-1].isdigit():
            found.append(int(parts[-1]))
    return found


def listening_pids(port: int) -> list[int]:
    if os.name == "nt":
        result = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            check=False,
        )
        found = pids_from_netstat(result.stdout, port)
    else:
        found = _posix_pids(port)
    me = os.getpid()
    return sorted({pid for pid in found if pid > 0 and pid != me})


def _posix_pids(port: int) -> list[int]:
    if shutil.which("lsof"):
        result = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode in (0, 1):
            return pids_from_lsof(result.stdout)
    if shutil.which("ss"):
        result = subprocess.run(
            ["ss", "-H", "-ltnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            check=False,
        )
        return pids_from_ss(result.stdout)
    raise SystemExit("Could not find lsof or ss, so the listener on this port cannot be identified.")


def stop_listener(port: int) -> None:
    pids = listening_pids(port)
    if not pids:
        print(f"Nothing is listening on port {port}.")
        return
    for pid in pids:
        _signal(pid, signal.SIGTERM)
    if _wait_until_quiet(port):
        print(f"Stopped the server on port {port}.")
        return
    for pid in listening_pids(port):
        _signal(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
    if _wait_until_quiet(port):
        print(f"Stopped the server on port {port}.")
        return
    raise SystemExit(f"A process is still listening on port {port}.")


def _signal(pid: int, sig: int) -> None:
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        return
    except PermissionError as exc:
        raise SystemExit(f"Could not stop process {pid}: {exc}") from exc


def _wait_until_quiet(port: int) -> bool:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if not listening_pids(port):
            return True
        time.sleep(0.1)
    return not listening_pids(port)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stop the local Studio server.")
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args(argv)
    stop_listener(args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
