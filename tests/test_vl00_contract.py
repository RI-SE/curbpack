"""VL-00: namespace, origin, and status contracts."""

from __future__ import annotations

import unittest

from checks.defaults import created_curbpack
from common.errors import ModelError
from common.validate import validate_curbpack_config
from studio.pack.pages import _curbpack_dialog


def _config(**overrides) -> dict:
    document = {
        "packs": ["cra-baseline"],
        "search_hints": {"sources": [{"source": "documents"}]},
        "packs_dir": "curbpack/packs",
        "claims_dir": "curbpack/claims",
        "results_dir": ".curbpack",
        "reports_dir": "curbpack/reports",
        "namespace_base": "RISE",
    }
    document.update(overrides)
    return document


class NamespaceBaseTest(unittest.TestCase):
    def test_a_valid_config_exposes_namespace_base(self):
        document = validate_curbpack_config(_config())
        self.assertEqual(document["namespace_base"], "RISE")

    def test_namespace_base_is_required(self):
        document = _config()
        del document["namespace_base"]
        with self.assertRaises(ModelError) as caught:
            validate_curbpack_config(document)
        self.assertEqual(caught.exception.field, "namespace_base")

    def test_a_blank_namespace_base_is_rejected(self):
        with self.assertRaises(ModelError) as caught:
            validate_curbpack_config(_config(namespace_base="  "))
        self.assertEqual(caught.exception.field, "namespace_base")

    def test_created_file_uses_rise(self):
        self.assertEqual(created_curbpack()["namespace_base"], "RISE")

    def test_dialog_posts_namespace_base(self):
        page = _curbpack_dialog({"curbpack_fields": created_curbpack(), "repo_id": "alpha"})
        self.assertIn('name="namespace_base"', page)
        self.assertIn('value="RISE"', page)
