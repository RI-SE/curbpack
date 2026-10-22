"""Formex package load and pinned official XML identity."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from requirements.extract.formex.package import (
    OFFICIAL_XML,
    load_doc_package,
    load_manifest,
    verify_source_bytes,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ManifestIdentityTest(unittest.TestCase):
    def test_manifest_lists_cra_and_nis2_with_matching_zip_hashes(self):
        manifest = load_manifest()
        by_celex = {item["celex"]: item for item in manifest["sources"]}
        self.assertEqual(
            by_celex["32024R2847"]["zip"]["sha256"],
            "93a1084b14383c0828b060ca933e9e83f9e8477fb2f9fbf81ee47750565f3155",
        )
        self.assertEqual(
            by_celex["32022L2555"]["zip"]["sha256"],
            "260e9b24760def5bb3ac7cf8681065572dd8bd537b5ce4ebaaac420259878985",
        )
        self.assertEqual(by_celex["32024R2847"]["edition"]["kind"], "original_oj")
        self.assertEqual(by_celex["32022L2555"]["edition"]["kind"], "original_oj")

    def test_verify_source_bytes_accepts_pinned_files_and_does_not_mutate(self):
        before = {
            path: _sha256(path)
            for path in sorted((OFFICIAL_XML / "cra").glob("*.xml"))
        }
        report = verify_source_bytes("32024R2847")
        self.assertTrue(report["ok"])
        self.assertEqual(report["checked"], len(before) + 1)  # xml files + zip
        after = {
            path: _sha256(path)
            for path in sorted((OFFICIAL_XML / "cra").glob("*.xml"))
        }
        self.assertEqual(before, after)


class DocPackageTest(unittest.TestCase):
    def test_cra_doc_resolves_annex_vii_file(self):
        package = load_doc_package(OFFICIAL_XML / "cra")
        self.assertEqual(package["language"], "EN")
        self.assertEqual(package["legal_value"], "REG")
        vii = next(part for part in package["parts"] if part["section_id"] == "VII")
        self.assertEqual(vii["kind"], "annex")
        self.assertEqual(vii["file"].name, "L_202402847EN.007501.fmx.xml")
        self.assertTrue(vii["file"].is_file())
        self.assertIn("CONTENT OF THE TECHNICAL DOCUMENTATION", vii["title"])

    def test_nis2_doc_lists_body_and_three_annexes(self):
        package = load_doc_package(OFFICIAL_XML / "nis2")
        self.assertEqual(package["legal_value"], "DIR")
        kinds = [part["kind"] for part in package["parts"]]
        self.assertEqual(kinds[0], "body")
        self.assertEqual(kinds[1:], ["annex", "annex", "annex"])
        self.assertEqual(
            [part["section_id"] for part in package["parts"] if part["kind"] == "annex"],
            ["I", "II", "III"],
        )


if __name__ == "__main__":
    unittest.main()
