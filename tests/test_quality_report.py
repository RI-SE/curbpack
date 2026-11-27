"""The quality check keeps each tool's own JSON and writes one report."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ci/checks/quality.py"
spec = importlib.util.spec_from_file_location("quality_check", SCRIPT)
quality = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = quality
spec.loader.exec_module(quality)


class QualityReportTest(unittest.TestCase):
    def test_size_records_keep_path_function_and_previous_size(self):
        findings = quality.size_findings(
            {"app/a.py": 600, "app/a.py::big": 80},
            {"app/a.py::big": 12},
            {"app/a.py": 400},
            False,
        )

        self.assertEqual(findings[0].data["path"], "app/a.py")
        self.assertEqual(findings[0].data["lines"], 600)
        self.assertEqual(findings[0].data["previous"], 400)
        self.assertNotIn("function", findings[0].data)
        self.assertEqual(findings[1].data["function"], "big")
        self.assertEqual(findings[1].data["line"], 12)
        self.assertIsNone(findings[1].data["previous"])

    def test_tool_readers_keep_the_native_json_document(self):
        ruff = quality.ruff_report("[]")
        self.assertFalse(ruff.found)
        self.assertEqual(ruff.data["report"], [])

        pylint = quality.pylint_report(json.dumps({
            "messages": [
                {"messageId": "R0801", "path": "a.py", "line": 1, "message": "Similar lines"},
                {"messageId": "C0114", "path": "a.py", "line": 1, "message": "Missing module docstring"},
            ],
            "statistics": {"score": 8.92},
        }))
        self.assertTrue(pylint.found)
        self.assertEqual(pylint.data["score"], 8.92)
        self.assertEqual(pylint.data["duplication_count"], 1)
        self.assertEqual(pylint.data["report"]["statistics"]["score"], 8.92)

        semgrep = quality.semgrep_report(json.dumps({
            "results": [{
                "check_id": "python.lang.security.use-defused-xml-parse",
                "path": "studio/pack/impl/extract/adapter.py",
                "start": {"line": 107},
                "extra": {"message": "Use defusedxml"},
            }],
        }))
        self.assertTrue(semgrep.found)
        self.assertEqual(semgrep.data["report"]["results"][0]["start"]["line"], 107)

        bandit = quality.bandit_report(json.dumps({"results": []}))
        self.assertFalse(bandit.found)
        self.assertEqual(bandit.data["report"]["results"], [])

        coverage = quality.interrogate_report(
            "RESULT: FAILED (minimum: 80.0%, actual: 34.6%)"
        )
        self.assertTrue(coverage.found)
        self.assertEqual(coverage.data["minimum"], 80.0)
        self.assertEqual(coverage.data["actual"], 34.6)

    def test_report_groups_summary_size_tools_and_architecture(self):
        results = [
            quality.Result("Python syntax", "PASS", "2 Python files compiled", {"files": 2}),
            quality.Result("Module length", "WARN", "app/server.py  10 lines", {
                "path": "app/server.py", "lines": 10, "limit": 5, "previous": None,
            }),
            quality.Result("Ruff", "PASS", "", {"format": "json", "report": []}),
        ]
        root = Path(self.id())  # absent directory: architecture targets are simply missing
        report = quality.build_report(results, root)

        self.assertEqual(report["summary"], {"PASS": 2, "WARN": 1, "FAIL": 0, "ERROR": 0})
        self.assertEqual(report["syntax"]["files"], 2)
        self.assertEqual(report["size"]["modules_over_limit"][0]["path"], "app/server.py")
        self.assertEqual(report["size"]["modules_over_limit"][0]["status"], "WARN")
        self.assertEqual(report["tools"][0]["name"], "Ruff")
        self.assertEqual(report["tools"][0]["report"], [])
        self.assertFalse(report["architecture"]["targets"][0]["present"])
        self.assertEqual(report["architecture"]["routers"], [])

    def test_written_report_is_the_same_document(self):
        path = ROOT / "tmp" / "quality-report-test.json"
        path.parent.mkdir(exist_ok=True)
        document = {"summary": {"PASS": 1, "WARN": 0, "FAIL": 0, "ERROR": 0}}
        try:
            quality.write_report(document, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), document)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
