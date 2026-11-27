"""CRA Annex I provisions from the text adapter."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from requirements.extract.adapter import ADAPTERS, load_adapter, section_provisions
from requirements.extract.atomize import atomize
from studio.pack.impl.extract.chart import Chart

_LOCI = [
    "I-1",
    *[f"I-2({letter})" for letter in "abcdefghijklm"],
    *[f"II-{number}" for number in range(1, 9)],
]


class CraAnnexITest(unittest.TestCase):
    def setUp(self):
        self.adapter = load_adapter(ADAPTERS / "cra" / "adapter.json")
        self.adapter_dir = ADAPTERS / "cra"

    def test_section_is_ready_and_cuts_both_parts(self):
        section = next(item for item in self.adapter["sections"] if item["id"] == "I")
        self.assertTrue(section["in_scope"])
        self.assertTrue(section["ready"])
        self.assertEqual(section["fixture"], "../../data/annex_i.txt")
        cut = section_provisions(self.adapter_dir, self.adapter, "I")
        self.assertEqual([item["locus"] for item in cut["provisions"]], _LOCI)
        by_locus = {item["locus"]: " ".join(item["law_text"].split()) for item in cut["provisions"]}
        self.assertIn("appropriate level of cybersecurity based on the risks", by_locus["I-1"])
        self.assertIn("without known exploitable vulnerabilities", by_locus["I-2(a)"])
        self.assertIn("On the basis of the cybersecurity risk assessment", by_locus["I-2(a)"])
        self.assertIn("secure by default configuration", by_locus["I-2(b)"])
        self.assertIn("report on corruptions", by_locus["I-2(f)"])
        self.assertIn("data minimisation", by_locus["I-2(g)"])
        self.assertIn("remove on a permanent basis", by_locus["I-2(m)"])
        self.assertIn("software bill of materials", by_locus["II-1"])
        self.assertIn("coordinated vulnerability disclosure", by_locus["II-5"])
        self.assertIn("free of charge", by_locus["II-8"])
        self.assertNotIn("Manufacturers of products with digital elements shall", by_locus["II-1"])

    def test_chart_keeps_the_part_headings_and_the_governing_sentence(self):
        text = (self.adapter_dir / "../../data/annex_i.txt").resolve().read_text(encoding="utf-8")
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        chart = Chart.create("annex-i", root=root)
        atoms = atomize(text, chart=chart)
        directory = chart.finish()
        snapshot = (directory / "snapshot.txt").read_text(encoding="utf-8")
        self.assertEqual([item["locus"] for item in atoms], _LOCI)
        self.assertIn("ANNEX I", snapshot)
        self.assertIn("Part I Cybersecurity requirements", snapshot)
        self.assertIn("Part II Vulnerability handling requirements", snapshot)
        self.assertIn("Manufacturers of products with digital elements shall:", snapshot)
        self.assertIn("without known exploitable vulnerabilities", snapshot)
        joined = "\n".join(item["law_text"] for item in atoms)
        self.assertNotIn("Manufacturers of products with digital elements shall:", joined)
