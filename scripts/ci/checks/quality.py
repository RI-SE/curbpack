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
import re
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
REPORT = ROOT / "quality-report.json"
FUNCTION_LIMIT = 50
MODULE_LIMIT = 500
ARCHITECTURE_TARGETS = (
    "studio/app.py",
    "studio/pack/router.py",
    "studio/claim/router.py",
    "studio/check/router.py",
    "studio/compile/router.py",
    "studio/review/router.py",
    "curbcheck/api.py",
    "curbcheck/cli.py",
    "models/pydantic",
    "app/server.py",
)
SIZE_NAMES = {"Module length", "Function length", "Python source size"}
SYNTAX_NAMES = {"Python syntax", "Python syntax / size"}


@dataclass(frozen=True)
class Result:
    name: str
    status: str
    detail: str = ""
    data: dict | None = None


@dataclass(frozen=True)
class Reading:
    found: bool
    detail: str
    data: dict


@dataclass(frozen=True)
class Tool:
    name: str
    command: tuple[str, ...]
    findings: frozenset[int] = frozenset({1})
    read_report: Callable[[str], Reading] | None = None


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
    return sizes, lines, [Result(
        "Python syntax", "PASS", f"{len(files)} Python files compiled", {"files": len(files)},
    )]


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
        if function:
            file_path, function_name = key.split("::", 1)
            record = {
                "path": file_path, "function": function_name, "line": lines[key],
                "lines": size, "limit": limit, "previous": old,
            }
        else:
            record = {"path": key, "lines": size, "limit": limit, "previous": old}
        results.append(Result(
            label, status, f"{location}  {size} lines (limit {limit}{change})", record,
        ))
    if not results:
        results.append(Result("Python source size", "PASS"))
    return results


def radon_report(output: str) -> Reading:
    document = json.loads(output)
    rows = []
    for path, value in document.items():
        if isinstance(value, dict) and "error" in value:
            raise ValueError(f"{path}: {value['error']}")
        if isinstance(value, list):
            for block in value:
                rows.append(f"{path}:{block['lineno']} {block['name']} CC {block['complexity']}")
        elif value["rank"] in {"B", "C"}:
            rows.append(f"{path} MI {value['mi']:.1f} (rank {value['rank']})")
    return Reading(bool(rows), "\n".join(rows), {"format": "json", "report": document})


def ruff_report(output: str) -> Reading:
    document = json.loads(output)
    if not isinstance(document, list):
        raise ValueError("Ruff JSON was not a list of diagnostics")
    rows = []
    for item in document:
        location = item.get("location") or {}
        rows.append(
            f"{item.get('filename')}:{location.get('row')} {item.get('code')} {item.get('message')}"
        )
    return Reading(bool(document), "\n".join(rows), {"format": "json", "report": document})


def complexipy_report(output: str) -> Reading:
    document = json.loads(output)
    if not isinstance(document, list):
        raise ValueError("Complexipy JSON was not a list of functions")
    rows = [
        f"{item['path']}:{item['line_start']} {item['function_name']} {item['complexity']}"
        for item in document
    ]
    return Reading(bool(document), "\n".join(rows), {"format": "json", "report": document})


def pylint_report(output: str) -> Reading:
    document = json.loads(output)
    score = document["statistics"]["score"]
    messages = document["messages"]
    duplicates = [item for item in messages if item["messageId"] == "R0801"]
    rows = [f"Score {score:.2f}/10, {len(duplicates)} duplication findings"]
    for item in duplicates or messages:
        message = item["message"].strip().replace("\n", " ")
        rows.append(f"{item['path']}:{item['line']} {item['messageId']} {message}")
    return Reading(
        score < 8 or bool(duplicates),
        "\n".join(rows),
        {
            "format": "json2",
            "score": score,
            "duplication_count": len(duplicates),
            "report": document,
        },
    )


def vulture_report(output: str) -> Reading:
    findings = []
    for line in output.splitlines():
        match = re.match(r"^(.*?):(\d+): (.*)$", line.strip())
        if match:
            findings.append({
                "path": match.group(1),
                "line": int(match.group(2)),
                "message": match.group(3),
            })
    return Reading(bool(findings), output.strip(), {"format": "text", "findings": findings})


def mypy_report(output: str) -> Reading:
    findings = []
    for line in output.splitlines():
        match = re.match(r"^(.*?):(\d+): (error|note|warning): (.*)$", line.strip())
        if match:
            findings.append({
                "path": match.group(1),
                "line": int(match.group(2)),
                "severity": match.group(3),
                "message": match.group(4),
            })
    found = any(item["severity"] == "error" for item in findings)
    return Reading(found, output.strip(), {"format": "text", "findings": findings})


def interrogate_report(output: str) -> Reading:
    match = re.search(r"minimum:\s*([0-9.]+)%.*actual:\s*([0-9.]+)%", output)
    data = {"format": "text", "output": output.strip()}
    if match:
        data["minimum"] = float(match.group(1))
        data["actual"] = float(match.group(2))
    return Reading("RESULT: FAILED" in output, output.strip(), data)


def bandit_report(output: str) -> Reading:
    document = json.loads(output)
    results = document.get("results") or []
    rows = [
        f"{item['filename']}:{item['line_number']} {item['test_id']} "
        f"{item['issue_severity']} {item['issue_text']}"
        for item in results
    ]
    return Reading(bool(results), "\n".join(rows), {"format": "json", "report": document})


def semgrep_report(output: str) -> Reading:
    document = json.loads(output)
    results = document.get("results") or []
    rows = []
    for item in results:
        start = item.get("start") or {}
        extra = item.get("extra") or {}
        message = str(extra.get("message") or "").strip().replace("\n", " ")
        rows.append(f"{item.get('path')}:{start.get('line')} {item.get('check_id')} {message}")
    return Reading(bool(results), "\n".join(rows), {"format": "json", "report": document})


def secrets_report(output: str) -> Reading:
    document = json.loads(output)
    files = document["results"]
    rows = [
        f"{path}:{finding['line_number']} {finding['type']}"
        for path, findings in files.items()
        for finding in findings
    ]
    return Reading(bool(rows), "\n".join(rows), {"format": "json", "report": document})


def audit_report(output: str) -> Reading:
    document = json.loads(output)
    rows = []
    skipped = []
    for package in document["dependencies"]:
        if "skip_reason" in package:
            skipped.append(f"{package['name']}: {package['skip_reason']}")
        for finding in package.get("vulns", []):
            rows.append(f"{package['name']} {package['version']} {finding['id']}")
    if skipped:
        raise ValueError("Dependencies could not be audited: " + "; ".join(skipped))
    return Reading(bool(rows), "\n".join(rows), {"format": "json", "report": document})


def tools(files: list[Path]) -> tuple[Tool, ...]:
    paths = tuple(path.as_posix() for path in files)
    source = tuple(path for path in SOURCE if (ROOT / path).exists())
    pylint_findings = frozenset(code for code in range(2, 32) if code & 1 == 0)
    return (
        Tool("Ruff", ("ruff", "check", "--select", "E4,E7,E9,F,B", "--output-format", "json",
                      *paths), frozenset({1}), ruff_report),
        Tool("Radon cyclomatic complexity", ("radon", "cc", "--json", "-n", "C", *paths),
             frozenset(), radon_report),
        Tool("Radon maintainability", ("radon", "mi", "--json", *paths),
             frozenset(), radon_report),
        Tool("Complexipy", ("complexipy", *paths, "--failed", "--select", "complexity",
                            "--sort", "desc", "--quiet", "--color", "no",
                            "--output-format", "json", "--output", "-"),
             frozenset({1}), complexipy_report),
        Tool("Pylint score and duplication", ("pylint", "--recursive=y", "--output-format=json2",
                                            *source), pylint_findings, pylint_report),
        Tool("Vulture", ("vulture", "--min-confidence", "60", *paths), frozenset({3}),
             vulture_report),
        Tool("Mypy", ("mypy", "--explicit-package-bases", *source), frozenset({1}), mypy_report),
        Tool("Interrogate", ("interrogate", "--fail-under", "80", "--no-color", *paths),
             frozenset({1}), interrogate_report),
        Tool("Bandit", ("bandit", "-q", "-f", "json", "-r", *source), frozenset({1}),
             bandit_report),
        Tool("Semgrep", ("semgrep", "scan", "--strict", "--error", "--metrics=off",
                         "--disable-version-check", "--json", "--config", "p/python",
                         "--config", "p/javascript", "--config", "p/owasp-top-ten", *source),
             frozenset({1}), semgrep_report),
        Tool("Detect Secrets", ("detect-secrets", "scan", "--all-files", *source),
             frozenset(), secrets_report),
        Tool("pip-audit", ("pip-audit", "--strict", "-r", "requirements.txt", "-f", "json"),
             frozenset({1}), audit_report),
        Tool("Import Linter", ("lint-imports", ".importlinter")),
        Tool("TypeScript", ("node", "node_modules/typescript/bin/tsc", "--noEmit"),
             frozenset({1, 2})),
    )


def text_data(detail: str) -> dict:
    return {"format": "text", "output": detail}


def run_tool(tool: Tool, strict: bool) -> Result:
    program, *args = tool.command
    if program == "node" and not (ROOT / args[0]).is_file():
        detail = "TypeScript was not found. Run make quality-tools."
        return Result(tool.name, "ERROR", detail, text_data(detail))
    search_path = None if program == "node" else sysconfig.get_path("scripts")
    executable = shutil.which(program, path=search_path)
    if executable is None:
        detail = f"{program} was not found. Run make quality-tools."
        return Result(tool.name, "ERROR", detail, text_data(detail))
    try:
        process = subprocess.run(
            [executable, *args], cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        detail = str(exc)
        return Result(tool.name, "ERROR", detail, text_data(detail))
    if process.returncode and process.returncode not in tool.findings:
        detail = (process.stderr or process.stdout or f"exit code {process.returncode}").strip()
        return Result(tool.name, "ERROR", detail, text_data(detail))
    if tool.read_report:
        try:
            reading = tool.read_report(process.stdout)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            detail = process.stderr.strip() or str(exc)
            return Result(tool.name, "ERROR", detail, text_data(detail))
        found = reading.found
        detail = reading.detail
        data = reading.data
    else:
        found = process.returncode != 0
        detail = "\n".join(part.strip() for part in (process.stdout, process.stderr) if part.strip())
        data = text_data(detail)
    status = ("FAIL" if strict else "WARN") if found else "PASS"
    kept = detail if found or tool.read_report else ""
    return Result(tool.name, status, kept, data)


def architecture_inventory(root: Path = ROOT) -> dict:
    studio = root / "studio"
    routers = []
    typescript = []
    if studio.is_dir():
        routers = sorted(path.relative_to(root).as_posix() for path in studio.rglob("router.py"))
        typescript = sorted(
            path.relative_to(root).as_posix()
            for path in studio.rglob("*")
            if path.suffix in {".ts", ".tsx"}
        )
    return {
        "targets": [
            {"path": path, "present": (root / path).exists()}
            for path in ARCHITECTURE_TARGETS
        ],
        "routers": routers,
        "typescript_files": typescript,
    }


def build_report(results: list[Result], root: Path = ROOT) -> dict:
    counts = Counter(result.status for result in results)
    syntax = next((result for result in results if result.name in SYNTAX_NAMES), None)
    inputs = next((result for result in results if result.name == "Quality inputs"), None)
    tools = []
    for result in results:
        if result.name in SIZE_NAMES or result.name in SYNTAX_NAMES or result.name == "Quality inputs":
            continue
        entry = {"name": result.name, "status": result.status}
        entry.update(result.data or text_data(result.detail))
        tools.append(entry)
    report = {
        "summary": {status: counts[status] for status in ("PASS", "WARN", "FAIL", "ERROR")},
        "syntax": None if syntax is None else {
            "status": syntax.status,
            "files": (syntax.data or {}).get("files"),
            "detail": syntax.detail,
        },
        "size": {
            "module_limit": MODULE_LIMIT,
            "function_limit": FUNCTION_LIMIT,
            "modules_over_limit": [
                {"status": result.status, **result.data}
                for result in results if result.name == "Module length" and result.data
            ],
            "functions_over_limit": [
                {"status": result.status, **result.data}
                for result in results if result.name == "Function length" and result.data
            ],
        },
        "tools": tools,
        "architecture": architecture_inventory(root),
    }
    if inputs is not None:
        report["inputs"] = {"status": inputs.status, "detail": inputs.detail}
    return report


def write_report(report: dict, path: Path = REPORT) -> None:
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".quality-report-", delete=False
    ) as stream:
        temporary = Path(stream.name)
    try:
        temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def brief(result: Result) -> str:
    data = result.data or {}
    if "score" in data:
        return f"{data['score']:.2f}/10, {data['duplication_count']} duplications"
    if "actual" in data:
        return f"{data['actual']}% of docstrings, minimum {data['minimum']}%"
    report = data.get("report")
    if isinstance(report, list):
        return f"{len(report)} findings"
    if isinstance(report, dict):
        findings = report.get("results")
        if isinstance(findings, list):
            return f"{len(findings)} findings"
        if isinstance(findings, dict):
            return f"{sum(len(items) for items in findings.values())} findings"
    listed = data.get("findings")
    if isinstance(listed, list):
        return f"{len(listed)} findings"
    if result.detail:
        return result.detail.splitlines()[0][:120]
    return ""


def print_brief(result: Result) -> None:
    text = brief(result)
    suffix = f"  {text}" if text else ""
    print(f"{result.status:<5} {result.name}{suffix}", flush=True)


def print_size_summary(results: list[Result]) -> None:
    for label, limit in (("Module length", MODULE_LIMIT), ("Function length", FUNCTION_LIMIT)):
        group = [result for result in results if result.name == label]
        if not group:
            continue
        counts = Counter(result.status for result in group)
        status = "FAIL" if counts["FAIL"] else "WARN"
        detail = ", ".join(
            f"{counts[item]} {item}" for item in ("FAIL", "WARN", "ERROR") if counts[item]
        )
        print(f"{status:<5} {label:<28} {detail}, limit {limit}", flush=True)
    if any(result.name in {"Module length", "Function length"} for result in results):
        return
    passed = next((result for result in results if result.name == "Python source size"), None)
    if passed is not None:
        print_brief(passed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write-baseline", action="store_true", help="Record current source sizes")
    mode.add_argument("--sizes-only", action="store_true", help="Run built-in checks only")
    parser.add_argument("--strict", action="store_true", help="Fail on all findings")
    parser.add_argument("--report", default=REPORT.name, help="Write the JSON report to this path")
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
    print_size_summary(results)
    for result in results:
        if result.name not in SIZE_NAMES:
            print_brief(result)
    if files and not args.sizes_only and not args.write_baseline:
        for tool in tools(files):
            result = run_tool(tool, args.strict)
            results.append(result)
            print_brief(result)
    counts = Counter(result.status for result in results)
    print("Summary: " + ", ".join(f"{counts[status]} {status}" for status in (
        "PASS", "WARN", "FAIL", "ERROR",
    )))
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    write_report(build_report(results), report_path)
    print(f"Wrote {report_path.relative_to(ROOT) if report_path.is_relative_to(ROOT) else report_path}")
    return 2 if counts["ERROR"] else int(bool(counts["FAIL"]))


if __name__ == "__main__":
    sys.exit(main())
