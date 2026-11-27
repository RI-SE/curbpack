"""Delta table for Python health against the committed text."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ci/checks/diff_quality.py"
spec = importlib.util.spec_from_file_location("diff_quality", SCRIPT)
diff = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = diff
spec.loader.exec_module(diff)


NESTED = """\
def nested():
    if True:
        for item in items:
            while item:
                with item:
                    return item
"""

KEEP = """\
def keep():
    return 1
"""


class DiffQualityTest(unittest.TestCase):
    def test_length_comes_from_the_shared_function_counter(self):
        source = "@decorator\ndef named():\n    return 1\n"
        _lines, functions = diff.measure(source)
        self.assertEqual(functions["named"].lines, 3)

    def test_nesting_and_complexity_of_one_function(self):
        _lines, functions = diff.measure(NESTED)
        self.assertEqual(functions["nested"].nest, 4)
        self.assertEqual(functions["nested"].cc, 4)
        self.assertEqual(functions["nested"].lines, 6)

    def test_changed_function_is_marked_and_unchanged_function_is_omitted(self):
        before = KEEP + "\n" + "def grow():\n    return 1\n"
        after = KEEP + "\n" + NESTED.replace("def nested():", "def grow():")
        functions, files = diff.compare({"mod.py": before}, {"mod.py": after})
        self.assertEqual([row[1] for row in functions], ["grow"])
        self.assertTrue(functions[0][4].endswith("!"))
        self.assertIn("0→4!", functions[0][4])
        self.assertEqual(files, [])

    def test_limits_mark_long_functions_and_complex_ones(self):
        body = "\n".join(f"    x = {number}" for number in range(50))
        long_function = f"def long():\n{body}\n"
        branches = "\n".join("    if True:\n        pass" for _ in range(10))
        complex_function = f"def branch():\n{branches}\n"
        functions, _files = diff.compare(
            {"mod.py": "def long():\n    return 1\ndef branch():\n    return 1\n"},
            {"mod.py": long_function + complex_function},
        )
        by_name = {row[1]: row for row in functions}
        self.assertTrue(by_name["long"][2].endswith("!"))
        self.assertTrue(by_name["branch"][3].endswith("!"))
        self.assertGreaterEqual(diff.measure(complex_function)[1]["branch"].cc, 11)

    def test_six_line_clone_counts_once_per_line_and_marks_growth(self):
        block = [f"    x = {number}" for number in range(6)]
        once = "def copy():\n" + "\n".join(block) + "\n"
        twice = once + "\n" + "\n".join(block) + "\n"
        self.assertEqual(diff.cloned_lines({"mod.py": once})["mod.py"], 0)
        self.assertEqual(diff.cloned_lines({"mod.py": twice})["mod.py"], 12)
        _functions, files = diff.compare({"mod.py": once}, {"mod.py": twice})
        self.assertEqual(files[0][2], "0→12!")

    def test_syntax_error_keeps_the_line_count_and_drops_functions(self):
        lines, functions = diff.measure("def broken(:\n    return 1\n")
        self.assertEqual(lines, 2)
        self.assertEqual(functions, {})

    def test_healthy_edit_is_omitted(self):
        before = "def small():\n    return 1\n"
        after = "def small():\n    return 1\n    return 2\n"
        functions, files = diff.compare({"mod.py": before}, {"mod.py": after})
        self.assertEqual(functions, [])
        self.assertEqual(files, [])
        self.assertEqual(diff.format_report(functions, files), "No health limits crossed.")

    def test_empty_diff_says_nothing_changed(self):
        self.assertEqual(diff.format_report([], []), "No health limits crossed.")

    def test_python_paths_skip_other_files_and_vendored_copies(self):
        self.assertEqual(
            diff.python_paths(["app/server.py", "readme.md", "pkg/vendor/lib.py", "app/server.py"]),
            ["app/server.py"],
        )


if __name__ == "__main__":
    unittest.main()
