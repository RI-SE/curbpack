"""Measure source size and run the Curbpack static analysis tools."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
from tempfile import NamedTemporaryFile
import tokenize


ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    "app", "checks", "claims", "common", "compile", "curbcheck", "discovery",
    "requirements", "review", "scaffold", "studio", "scripts",
    "compile-pdf.py", "demo_setup.py", "workflow.py",
)
BASELINE = ROOT / "quality-baseline.json"
FUNCTION_LIMIT = 50
MODULE_LIMIT = 500
OUTPUT_LIMIT = 25


@dataclass(frozen=True)
class Result:
    name: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class Tool:
    name: str
    command: tuple[str, ...]
    findings: frozenset[int] = frozenset({1})
    read_report: Callable[[str], tuple[bool, str]] | None = None


def source_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *SOURCE],
        cwd=ROOT,
    )
    files = {Path(os.fsdecode(name)) for name in output.split(b"\0") if name}
    return sorted(
        path for path in files
        if path.suffix == ".py" and "vendor" not in path.parts and (ROOT / path).is_file()
    )


class FunctionSizes(ast.NodeVisitor):
    def __init__(self) -> None:
        self.scope: list[str] = []
        self.occurrences: Counter[str] = Counter()
        self.sizes: list[tuple[str, int, int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.visit_scope(node)

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        name = ".".join([*self.scope, node.name])
        self.occurrences[name] += 1
        occurrence = self.occurrences[name]
        if occurrence > 1:
            name = f"{name}#{occurrence}"
        first = min([node.lineno, *(item.lineno for item in node.decorator_list)])
        self.sizes.append((name, first, node.end_lineno - first + 1))
        self.visit_scope(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_scope(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()


def measure_sizes(files: list[Path]) -> tuple[dict[str, int], dict[str, int], list[Result]]:
    sizes = {}
    lines = {}
    for path in files:
        try:
            with tokenize.open(ROOT / path) as stream:
                source = stream.read()
            compile(source, str(path), "exec", dont_inherit=True)
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError, UnicodeError, ValueError, LookupError) as exc:
            return {}, {}, [Result("Python syntax / size", "ERROR", f"{path}: {exc}")]
        name = path.as_posix()
        sizes[name] = len(source.splitlines())
        visitor = FunctionSizes()
        visitor.visit(tree)
        for function, line, size in visitor.sizes:
            key = f"{name}::{function}"
            sizes[key] = size
            lines[key] = line
    if not files:
        return {}, {}, [Result("Python syntax / size", "ERROR", "No Python source files found")]
    return sizes, lines, [Result("Python syntax", "PASS", f"{len(files)} Python files compiled")]


def read_baseline() -> dict[str, int] | None:
    if not BASELINE.exists():
        return None
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data or any(
        type(size) is not int or size < 0 for size in data.values()
    ):
        raise ValueError(f"Invalid size baseline: {BASELINE.name}")
    return data


def write_baseline(sizes: dict[str, int]) -> None:
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=ROOT, prefix=".quality-baseline-", delete=False
    ) as stream:
        temporary = Path(stream.name)
    try:
        temporary.write_text(json.dumps(sizes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(BASELINE)
    finally:
        temporary.unlink(missing_ok=True)


def size_findings(
    sizes: dict[str, int], lines: dict[str, int], baseline: dict[str, int] | None,
    strict: bool,
) -> list[Result]:
    results = []
    for key, size in sorted(sizes.items(), key=lambda item: (-item[1], item[0])):
        function = key in lines
        label = "Function length" if function else "Module length"
        limit = FUNCTION_LIMIT if function else MODULE_LIMIT
        if size <= limit:
            continue
        old = baseline.get(key) if baseline is not None else None
        regression = baseline is not None and (old is None or size > old)
        location = key.replace("::", f":{lines[key]} ", 1) if function else key
        change = f", was {old}" if old is not None and old != size else ""
        status = "FAIL" if strict or regression else "WARN"
        results.append(Result(label, status, f"{location}  {size} lines (limit {limit}{change})"))
    if not results:
        results.append(Result("Python source size", "PASS"))
    return results


def radon_report(output: str) -> tuple[bool, str]:
    rows = []
    for path, value in json.loads(output).items():
        if isinstance(value, dict) and "error" in value:
            raise ValueError(f"{path}: {value['error']}")
        if isinstance(value, list):
            for block in value:
                rows.append(f"{path}:{block['lineno']} {block['name']} CC {block['complexity']}")
        elif value["rank"] in {"B", "C"}:
            rows.append(f"{path} MI {value['mi']:.1f} (rank {value['rank']})")
    return bool(rows), "\n".join(rows)


def pylint_report(output: str) -> tuple[bool, str]:
    data = json.loads(output)
    score = data["statistics"]["score"]
    messages = data["messages"]
    duplicates = [item for item in messages if item["messageId"] == "R0801"]
    rows = [f"Score {score:.2f}/10, {len(duplicates)} duplication findings"]
    for item in duplicates or messages:
        message = item["message"].strip().replace("\n", " ")
        rows.append(f"{item['path']}:{item['line']} {item['messageId']} {message}")
    return score < 8 or bool(duplicates), "\n".join(rows)


def secrets_report(output: str) -> tuple[bool, str]:
    files = json.loads(output)["results"]
    rows = [
        f"{path}:{finding['line_number']} {finding['type']}"
        for path, findings in files.items()
        for finding in findings
    ]
    return bool(rows), "\n".join(rows)


def audit_report(output: str) -> tuple[bool, str]:
    rows = []
    skipped = []
    for package in json.loads(output)["dependencies"]:
        if "skip_reason" in package:
            skipped.append(f"{package['name']}: {package['skip_reason']}")
        for finding in package.get("vulns", []):
            rows.append(f"{package['name']} {package['version']} {finding['id']}")
    if skipped:
        raise ValueError("Dependencies could not be audited: " + "; ".join(skipped))
    return bool(rows), "\n".join(rows)


def tools(files: list[Path]) -> tuple[Tool, ...]:
    paths = tuple(path.as_posix() for path in files)
    source = tuple(path for path in SOURCE if (ROOT / path).exists())
    pylint_findings = frozenset(code for code in range(2, 32) if code & 1 == 0)
    return (
        Tool("Ruff", ("ruff", "check", "--select", "E4,E7,E9,F,B", *paths)),
        Tool("Radon cyclomatic complexity", ("radon", "cc", "--json", "-n", "C", *paths),
             frozenset(), radon_report),
        Tool("Radon maintainability", ("radon", "mi", "--json", *paths),
             frozenset(), radon_report),
        Tool("Complexipy", ("complexipy", *paths, "--failed", "--select", "complexity",
                            "--plain", "--sort", "desc")),
        Tool("Pylint score and duplication", ("pylint", "--recursive=y", "--output-format=json2",
                                            *source), pylint_findings, pylint_report),
        Tool("Vulture", ("vulture", "--min-confidence", "60", *paths), frozenset({3})),
        Tool("Mypy", ("mypy", "--explicit-package-bases", *source)),
        Tool("Interrogate", ("interrogate", "--fail-under", "80", *paths)),
        Tool("Bandit", ("bandit", "-r", *source)),
        Tool("Semgrep", ("semgrep", "scan", "--strict", "--error", "--metrics=off",
                         "--disable-version-check", "--config", "p/python",
                         "--config", "p/javascript", "--config", "p/owasp-top-ten", *source)),
        Tool("Detect Secrets", ("detect-secrets", "scan", "--all-files", *source),
             frozenset(), secrets_report),
        Tool("pip-audit", ("pip-audit", "--strict", "-r", "requirements.txt", "-f", "json"),
             frozenset({1}), audit_report),
        Tool("Import Linter", ("lint-imports", ".importlinter")),
        Tool("TypeScript", ("node", "node_modules/typescript/bin/tsc", "--noEmit"),
             frozenset({1, 2})),
    )


def run_tool(tool: Tool, strict: bool) -> Result:
    program, *args = tool.command
    if program == "node" and not (ROOT / args[0]).is_file():
        return Result(tool.name, "ERROR", "TypeScript was not found. Run make quality-tools.")
    search_path = None if program == "node" else sysconfig.get_path("scripts")
    executable = shutil.which(program, path=search_path)
    if executable is None:
        return Result(tool.name, "ERROR", f"{program} was not found. Run make quality-tools.")
    try:
        process = subprocess.run(
            [executable, *args], cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Result(tool.name, "ERROR", str(exc))
    if process.returncode and process.returncode not in tool.findings:
        detail = process.stderr or process.stdout or f"exit code {process.returncode}"
        return Result(tool.name, "ERROR", detail.strip())
    if tool.read_report:
        try:
            found, detail = tool.read_report(process.stdout)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            return Result(tool.name, "ERROR", process.stderr.strip() or str(exc))
    else:
        found = process.returncode != 0
        detail = "\n".join(part.strip() for part in (process.stdout, process.stderr) if part.strip())
    status = ("FAIL" if strict else "WARN") if found else "PASS"
    return Result(tool.name, status, detail if found or tool.read_report else "")


def print_result(result: Result) -> None:
    print(f"{result.status:<5} {result.name}", flush=True)
    lines = result.detail.splitlines()
    for line in lines[:OUTPUT_LIMIT]:
        print(f"      {line}", flush=True)
    if len(lines) > OUTPUT_LIMIT:
        print(f"      ... {len(lines) - OUTPUT_LIMIT} more lines")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write-baseline", action="store_true", help="Record current source sizes")
    mode.add_argument("--sizes-only", action="store_true", help="Run built-in checks only")
    parser.add_argument("--strict", action="store_true", help="Fail on all findings")
    args = parser.parse_args()
    try:
        files = source_files()
        sizes, lines, results = measure_sizes(files)
        if args.write_baseline and sizes:
            write_baseline(sizes)
            print(f"Wrote {BASELINE.name} with {len(sizes)} measurements.")
            return 0
        if sizes:
            results.extend(size_findings(sizes, lines, read_baseline(), args.strict))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        results = [Result("Quality inputs", "ERROR", str(exc))]
        files = []
    for result in results:
        print_result(result)
    if files and not args.sizes_only and not args.write_baseline:
        for tool in tools(files):
            result = run_tool(tool, args.strict)
            results.append(result)
            print_result(result)
    counts = Counter(result.status for result in results)
    print("Summary: " + ", ".join(f"{counts[status]} {status}" for status in (
        "PASS", "WARN", "FAIL", "ERROR",
    )))
    return 2 if counts["ERROR"] else int(bool(counts["FAIL"]))


if __name__ == "__main__":
    sys.exit(main())
