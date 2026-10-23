"""One line of CI output. Plain text when the terminal has no color."""

from __future__ import annotations

import sys


def say(ok: bool, name: str) -> None:
    text = f"[{'PASS' if ok else 'FAIL'}] {name}"
    if sys.stdout.isatty():
        color = "32" if ok else "31"
        text = f"\033[{color}m{text}\033[0m"
    print(text, flush=True)
