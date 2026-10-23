#!/usr/bin/env python3
"""Start a built binary and read its local cover page. Does not rebuild."""

from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=2) as response:
        return response.read().decode("utf-8", errors="replace")


def smoke(binary: Path) -> int:
    if not binary.is_file():
        print(f"[FAIL] smoke missing binary {binary}", flush=True)
        return 1
    port = _free_port()
    with tempfile.TemporaryDirectory(prefix="curbpack-smoke-") as tmp:
        workspace = Path(tmp)
        process = subprocess.Popen(
            [
                str(binary),
                "--workspace",
                str(workspace),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        url = f"http://127.0.0.1:{port}/"
        body = ""
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    output = process.stdout.read() if process.stdout else ""
                    print(output, flush=True)
                    print("[FAIL] smoke binary exited before the cover page", flush=True)
                    return 1
                try:
                    with urllib.request.urlopen(url, timeout=2) as response:
                        body = response.read().decode("utf-8", errors="replace")
                    break
                except Exception:
                    time.sleep(0.2)
            else:
                print("[FAIL] smoke cover page did not respond", flush=True)
                return 1
            if "Curbpack" not in body or "Review" not in body:
                print("[FAIL] smoke cover page is not the pilot", flush=True)
                return 1
            vendor = _get(f"http://127.0.0.1:{port}/vendor/jsondiffpatch.js")
            if "jsondiffpatch" not in vendor:
                print("[FAIL] smoke did not read the bundled UI resource", flush=True)
                return 1
            requirements = _get(f"http://127.0.0.1:{port}/requirements")
            if "cra-xml" not in requirements:
                print("[FAIL] smoke did not read the bundled adapters", flush=True)
                return 1
            if not workspace.is_dir():
                print("[FAIL] smoke workspace was not the directory passed to the binary", flush=True)
                return 1
            print(f"[PASS] smoke {binary.name}", flush=True)
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: smoke.py <binary>", flush=True)
        return 2
    return smoke(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())
