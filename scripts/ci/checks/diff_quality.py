"""Compare Python health in the working tree with the committed versions.

Print a table for functions whose size, complexity, or nesting changed, and a
second table for module size and cloned lines. Write nothing to disk.
"""

from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
CC_LIMIT = 11
NEST_LIMIT = 4
CLONE_LINES = 6


def _quality():
    spec = importlib.util.spec_from_file_location(
        "quality_check", Path(__file__).with_name("quality.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


quality = _quality()


class FunctionMeasure:
    def __init__(self, lines: int, cc: int, nest: int) -> None:
        self.lines = lines
        self.cc = cc
        self.nest = nest

    def same(self, other: FunctionMeasure) -> bool:
        return (self.lines, self.cc, self.nest) == (other.lines, other.cc, other.nest)


ZERO = FunctionMeasure(0, 0, 0)


class _Health(quality.FunctionSizes):
    def __init__(self) -> None:
        super().__init__()
        self.health: dict[str, tuple[int, int]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        bare = ".".join([*self.scope, node.name])
        occurrence = self.occurrences[bare] + 1
        qualified = bare if occurrence == 1 else f"{bare}#{occurrence}"
        self.health[qualified] = _body_metrics(node.body)
        super().visit_FunctionDef(node)

    visit_AsyncFunctionDef = visit_FunctionDef


def _decision(node: ast.AST) -> int:
    if isinstance(node, ast.Try):
        return len(node.handlers) + bool(node.orelse)
    if isinstance(node, ast.BoolOp):
        return len(node.values) - 1
    if isinstance(node, (ast.If, ast.IfExp)):
        return 1
    if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
        return 1 + bool(node.orelse)
    if isinstance(node, ast.comprehension):
        return len(node.ifs) + 1
    if isinstance(node, ast.Assert):
        return 1
    match = getattr(ast, "Match", None)
    if match is not None and isinstance(node, match):
        wildcard = 0
        for case in node.cases:
            pattern = getattr(case.pattern, "pattern", False)
            if pattern is None:
                wildcard = 1
                break
        return max(0, len(node.cases) - wildcard)
    return 0


def _body_metrics(statements: list[ast.stmt]) -> tuple[int, int]:
    complexity = 1
    nesting = 0

    def walk(node: ast.AST, depth: int) -> None:
        nonlocal complexity, nesting
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        complexity += _decision(node)
        deeper = depth
        if isinstance(node, (
            ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith,
        )):
            deeper = depth + 1
            nesting = max(nesting, deeper)
        for child in ast.iter_child_nodes(node):
            walk(child, deeper)

    for statement in statements:
        walk(statement, 0)
    return complexity, nesting


def measure(source: str) -> tuple[int, dict[str, FunctionMeasure]]:
    """Module line count and per-function health. A syntax error has no functions."""
    lines = len(source.splitlines())
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return lines, {}
    visitor = _Health()
    visitor.visit(tree)
    functions = {}
    for name, _line, size in visitor.sizes:
        complexity, nesting = visitor.health[name]
        functions[name] = FunctionMeasure(size, complexity, nesting)
    return lines, functions


def cloned_lines(sources: dict[str, str]) -> dict[str, int]:
    """Lines in each text that sit inside a repeated block of at least six lines."""
    files = {path: text.splitlines() for path, text in sources.items()}
    windows: dict[tuple[str, ...], list[tuple[str, int]]] = {}
    for path, lines in files.items():
        for start in range(len(lines) - CLONE_LINES + 1):
            key = tuple(lines[start:start + CLONE_LINES])
            windows.setdefault(key, []).append((path, start))
    marked = {path: set() for path in files}
    for positions in windows.values():
        if len(positions) < 2:
            continue
        for path, start in positions:
            marked[path].update(range(start, start + CLONE_LINES))
    return {path: len(lines) for path, lines in marked.items()}


def _over_limit(measure: FunctionMeasure) -> bool:
    return (
        measure.lines > quality.FUNCTION_LIMIT
        or measure.cc >= CC_LIMIT
        or measure.nest >= NEST_LIMIT
    )


def _cell(before: int, after: int, bang: bool) -> str:
    return f"{before}→{after}{'!' if bang else ''}"


def compare(
    before: dict[str, str | None], after: dict[str, str | None],
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    """Return function rows and file rows. Unchanged measures are left out."""
    before_text = {path: text for path, text in before.items() if text is not None}
    after_text = {path: text for path, text in after.items() if text is not None}
    before_clones = cloned_lines(before_text)
    after_clones = cloned_lines(after_text)
    functions = []
    files = []
    for path in sorted(set(before) | set(after)):
        old_lines, old_functions = measure(before.get(path) or "")
        new_lines, new_functions = measure(after.get(path) or "")
        if before.get(path) is None:
            old_lines = 0
        if after.get(path) is None:
            new_lines = 0
        for name in sorted(set(old_functions) | set(new_functions)):
            old = old_functions.get(name, ZERO)
            new = new_functions.get(name, ZERO)
            if old.same(new) or not (_over_limit(old) or _over_limit(new)):
                continue
            functions.append((
                path,
                name,
                _cell(old.lines, new.lines, new.lines > quality.FUNCTION_LIMIT),
                _cell(old.cc, new.cc, new.cc >= CC_LIMIT),
                _cell(old.nest, new.nest, new.nest >= NEST_LIMIT),
            ))
        old_dup = before_clones.get(path, 0)
        new_dup = after_clones.get(path, 0)
        if (
            old_lines > quality.MODULE_LIMIT or new_lines > quality.MODULE_LIMIT
            or new_dup > old_dup
        ):
            files.append((
                path,
                _cell(old_lines, new_lines, new_lines > quality.MODULE_LIMIT),
                _cell(old_dup, new_dup, new_dup > old_dup),
            ))
    return functions, files


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    widths = [
        max([len(header), *(len(row[index]) for row in rows)])
        for index, header in enumerate(headers)
    ]
    def render(values: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(values)).rstrip()
    return "\n".join([render(headers), *(render(row) for row in rows)])


def format_report(
    functions: list[tuple[str, ...]], files: list[tuple[str, ...]],
) -> str:
    parts = ["limits: function lines > 50, cc >= 11, nest >= 4; module lines > 500; dup increased"]
    if functions:
        parts.append(_table(("file", "function", "lines", "cc", "nest"), functions))
    if files:
        parts.append(_table(("file", "lines", "dup"), files))
    if len(parts) == 1:
        return "No health limits crossed."
    return "\n\n".join(parts)


def python_paths(names: list[str]) -> list[str]:
    chosen = []
    for name in names:
        path = Path(name)
        if path.suffix == ".py" and "vendor" not in path.parts:
            chosen.append(name)
    return sorted(set(chosen))


def _git_names(root: Path) -> list[str]:
    diff = subprocess.run(
        ["git", "diff", "HEAD", "--name-only", "-z"],
        cwd=root, capture_output=True, check=False,
    )
    if diff.returncode != 0:
        sys.stderr.write(diff.stderr.decode("utf-8", errors="replace"))
        return []
    others = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, check=False,
    )
    names = []
    for blob in diff.stdout.split(b"\0") + others.stdout.split(b"\0"):
        if blob:
            names.append(os.fsdecode(blob))
    return python_paths(names)


def _head_text(root: Path, path: str) -> str | None:
    shown = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=root, capture_output=True, check=False,
    )
    if shown.returncode != 0:
        return None
    return shown.stdout.decode("utf-8", errors="replace")


def sources(root: Path, paths: list[str]) -> tuple[dict[str, str | None], dict[str, str | None]]:
    before = {}
    after = {}
    for path in paths:
        before[path] = _head_text(root, path)
        file = root / path
        after[path] = file.read_text(encoding="utf-8", errors="replace") if file.is_file() else None
    return before, after


def main() -> int:
    paths = _git_names(ROOT)
    before, after = sources(ROOT, paths)
    print(format_report(*compare(before, after)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
