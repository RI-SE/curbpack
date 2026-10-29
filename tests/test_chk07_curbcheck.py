"""CHK-07 — curbcheck reads curbpack.json, owns defaults, stdout / -j / -o."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from checks.__main__ import main


CREATED_SEARCH_HINTS = {
    "sources": [{"source": "documents"}, {"source": "git"}],
    "exclude_path_globs": [
        "**/node_modules/**",
        "**/.git/**",
        "**/dist/**",
        "**/build/**",
    ],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"],
}


class DefaultsFactoryTest(unittest.TestCase):
    def test_defaults_function_returns_created_file_values(self):
        from checks.defaults import created_curbpack

        document = created_curbpack()
        self.assertEqual(document["packs"], [])
        self.assertEqual(document["search_hints"], CREATED_SEARCH_HINTS)
        self.assertEqual(document["packs_dir"], "curbpack/packs")
        self.assertEqual(document["claims_dir"], "curbpack/claims")
        self.assertEqual(document["results_dir"], ".curbpack")
        self.assertEqual(document["reports_dir"], "curbpack/reports")
        self.assertEqual(document["unsigned_requirements"], "reject")
        self.assertNotIn("exclude_requirements", document)
        self.assertNotIn("requirements", document)

    def test_defaults_cli_prints_that_json_without_a_repository(self):
        from checks.defaults import created_curbpack

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        previous = Path.cwd()
        os.chdir(tmp.name)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--defaults"])
        finally:
            os.chdir(previous)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue()), created_curbpack())
        self.assertEqual(list(Path(tmp.name).iterdir()), [])

    def test_studio_calls_the_same_defaults_function(self):
        from checks.defaults import created_curbpack
        from discovery.door import created_curbpack as door_created

        self.assertIs(door_created, created_curbpack)
        self.assertEqual(door_created(), created_curbpack())
