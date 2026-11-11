"""VR-00: unsigned_requirements is not a configuration policy."""

from __future__ import annotations

import unittest

from checks.defaults import CREATED_SEARCH_HINTS, created_curbpack
from common.errors import ModelError
from common.validate import validate_curbpack_config
from studio.pack.pages import _curbpack_dialog


def _config(**overrides) -> dict:
    document = {
        "packs": ["cra-baseline"],
        "search_hints": {
            "sources": [{"source": "documents"}, {"source": "git"}],
            "exclude_path_globs": list(CREATED_SEARCH_HINTS["exclude_path_globs"]),
            "prefer_path_globs": list(CREATED_SEARCH_HINTS["prefer_path_globs"]),
        },
        "packs_dir": "curbpack/packs",
        "claims_dir": "curbpack/claims",
        "results_dir": ".curbpack",
        "reports_dir": "curbpack/reports",
    }
    document.update(overrides)
    return document


class UnsignedRequirementsRemovedTest(unittest.TestCase):
    def test_the_key_is_an_unknown_field(self):
        with self.assertRaises(ModelError) as caught:
            validate_curbpack_config(_config(unsigned_requirements="reject"))
        self.assertEqual(caught.exception.field, "unsigned_requirements")

    def test_a_file_without_the_key_validates(self):
        document = validate_curbpack_config(_config())
        self.assertNotIn("unsigned_requirements", document)

    def test_created_file_omits_the_key(self):
        document = created_curbpack()
        self.assertNotIn("unsigned_requirements", document)
        self.assertNotIn("reject", document.values())

    def test_dialog_has_no_policy_control(self):
        page = _curbpack_dialog({"curbpack_fields": created_curbpack(), "repo_id": "alpha"})
        self.assertNotIn("unsigned_requirements", page)
        self.assertNotIn("signed_commit", page)
        self.assertNotIn(">reject<", page)
