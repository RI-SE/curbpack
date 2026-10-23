"""One line of CI output. Plain text when the terminal has no color."""

from __future__ import annotations

import sys


def status_token(ok: bool) -> str:
    token = "[PASS]" if ok else "[FAIL]"
    if sys.stdout.isatty():
        color = "32" if ok else "31"
        return f"\033[{color}m{token}\033[0m"
    return token


def dotted(name: str, ok: bool, width: int = 24) -> str:
    dots = "." * max(3, width - len(name))
    return f"{name} {dots} {status_token(ok)}"


def summary(passed: int, failed: int) -> str:
    return f"Summary: {passed} PASS, {failed} FAIL"


def say(ok: bool, name: str) -> None:
    print(dotted(name, ok), flush=True)
