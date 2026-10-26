#!/usr/bin/env python3
"""Run the functional tests. make test prints each case. A quiet CI check prints one line when it passes, and the full failure report when it does not."""

from __future__ import annotations

import os
import sys
import traceback
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from report import dotted, summary

ROOT = Path(__file__).resolve().parents[3]


def case_name(test: unittest.TestCase) -> str:
    parts = test.id().split(".")
    if len(parts) >= 2:
        return f"{parts[-3]}.{parts[-1]}" if len(parts) >= 3 else parts[-1]
    return test.id()


def short_reason(err: tuple) -> str:
    lines = [line.strip() for line in traceback.format_exception(*err) if line.strip()]
    text = lines[-1] if lines else err[0].__name__
    line = " ".join(text.split())
    if len(line) > 160:
        return line[:157] + "..."
    return line


class _Result(unittest.TextTestResult):
    def __init__(self) -> None:
        super().__init__(sys.stderr, descriptions=False, verbosity=0)
        self.buffer = True
        self.rows: list[tuple[str, bool, str]] = []

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        self.rows.append((case_name(test), True, ""))

    def addFailure(self, test: unittest.TestCase, err: tuple) -> None:
        reason = short_reason(err)
        super().addFailure(test, err)
        self.rows.append((case_name(test), False, reason))

    def addError(self, test: unittest.TestCase, err: tuple) -> None:
        reason = short_reason(err)
        super().addError(test, err)
        self.rows.append((case_name(test), False, reason))

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        self.rows.append((case_name(test), False, f"skipped: {reason}"))

    def addSubTest(self, test: unittest.TestCase, subtest: unittest.TestCase, err) -> None:
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.rows.append((case_name(subtest), False, short_reason(err)))


def _print_details(result: _Result) -> None:
    """Tracebacks, captured output, skips, and unexpected successes."""
    for label, entries in (("ERROR", result.errors), ("FAIL", result.failures)):
        for test, err in entries:
            print(flush=True)
            print("=" * 70, flush=True)
            print(f"{label}: {test.id()}", flush=True)
            print("-" * 70, flush=True)
            print(str(err).rstrip("\n"), flush=True)
    for test, reason in result.skipped:
        print(flush=True)
        print(f"SKIP: {test.id()}", flush=True)
        print(reason, flush=True)
    for test in result.unexpectedSuccesses:
        print(flush=True)
        print(f"UNEXPECTED SUCCESS: {test.id()}", flush=True)


def report(result: _Result, *, quiet: bool) -> int:
    failed = [row for row in result.rows if not row[1]]
    bad = bool(failed or result.failures or result.errors or result.unexpectedSuccesses)
    passed = len(result.rows) - len(failed)
    if quiet:
        print(dotted("tests", not bad), flush=True)
        if bad:
            _print_details(result)
            print(flush=True)
            print(summary(passed, len(failed)), flush=True)
        return 1 if bad else 0
    width = max((len(name) for name, _, _ in result.rows), default=21) + 3
    for name, ok, reason in result.rows:
        print(dotted(name, ok, width), flush=True)
        if reason:
            print(f"  {reason}", flush=True)
    print(flush=True)
    print(summary(passed, len(failed)), flush=True)
    return 1 if bad else 0


def main() -> int:
    os.chdir(ROOT)
    # The runner file is named tests.py. Its directory is on sys.path, and a
    # later tests.py hides the tests package because that directory has no
    # __init__.py. Drop the script directory before discovery.
    script_dir = str(Path(__file__).resolve().parent)
    sys.path[:] = [entry for entry in sys.path if os.path.abspath(entry) != script_dir]
    sys.modules.pop("tests", None)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover("tests")
    result = _Result()
    suite.run(result)
    quiet = os.environ.get("CURBPACK_CHECK_QUIET", "").strip() == "1"
    return report(result, quiet=quiet)


if __name__ == "__main__":
    raise SystemExit(main())
