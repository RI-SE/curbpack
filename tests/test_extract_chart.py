"""A chart records kept passages and text the cutter drops."""

from __future__ import annotations

import io
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from common.errors import ModelError
from common.jsonio import read_json
from requirements.extract.chart import chart_run, main
from requirements.extract.formex.provisions import _provisions_from_article
from studio.pack.impl.extract.atomize import atomize
from studio.pack.impl.extract.chart import Chart


_ARTICLE = """
<ARTICLE IDENTIFIER="021">
  <TI.ART>Article 21</TI.ART>
  <PARAG IDENTIFIER="021.002">
    <NO.PARAG>2.</NO.PARAG>
    <ALINEA>The manufacturer shall: <QUOT.START CODE="2018"/>keep logs<QUOT.END CODE="2019"/>
      <LIST TYPE="ALPHA">
        <ITEM><NP><NO.P>(a)</NO.P><TXT>retain audit logs;</TXT></NP></ITEM>
        <ITEM><NP><NO.P>(b)</NO.P><TXT>document incidents;</TXT></NP></ITEM>
      </LIST>
      unless specifically exempted.
    </ALINEA>
  </PARAG>
</ARTICLE>
"""

_FOOTNOTE = """1.

keep this sentence about the product.

(1)
OJ L 333, 27.12.2022, p. 80, ELI: http://data.europa.eu/eli/dir/2022/2555/oj
"""

_HEADING = """ANNEX VII

ESSENTIAL CYBERSECURITY REQUIREMENTS

the product keeps a record.
"""


def _partition(directory: Path) -> tuple[str, dict]:
    snapshot = (directory / "snapshot.txt").read_text(encoding="utf-8")
    document = read_json(directory / "sourcechart.json")
    cuts = document["cuts"]
    if cuts[0] != 0 or cuts[-1] != len(snapshot) or document["snapshot"]["chars"] != len(snapshot):
        raise AssertionError(f"cuts {cuts} do not cover {len(snapshot)} characters")
    if any(left >= right for left, right in zip(cuts, cuts[1:])):
        raise AssertionError(f"cuts are not strictly rising: {cuts}")
    count = len(cuts) - 1
    owners = [0] * count
    for unit in document["units"]:
        for block in unit["blocks"]:
            owners[block] += 1
    for key in document["unassigned"]:
        owners[int(key)] += 1
    if owners != [1] * count:
        raise AssertionError(f"block owners {owners}")
    return snapshot, document


def _slices(snapshot: str, document: dict, reason: str) -> list[str]:
    cuts = document["cuts"]
    found = []
    for key, (status, why) in document["unassigned"].items():
        if status == "uncovered" and why == reason:
            index = int(key)
            found.append(snapshot[cuts[index] : cuts[index + 1]])
    return found


class FormexChartTest(unittest.TestCase):
    def test_list_tail_and_quotes_are_uncovered_and_the_snapshot_is_partitioned(self):
        article = ET.fromstring(_ARTICLE)
        without = _provisions_from_article(article, "21")
        chart = Chart.create("sample", root=Path(self._tmp()))
        with_chart = _provisions_from_article(article, "21", chart=chart)
        self.assertEqual(without, with_chart)
        directory = chart.finish()
        snapshot, document = _partition(directory)
        self.assertIn("The manufacturer shall:", snapshot)
        self.assertIn("retain audit logs;", snapshot)
        self.assertEqual(_slices(snapshot, document, "text after list"), ["unless specifically exempted."])
        self.assertEqual(_slices(snapshot, document, "QUOT.START"), ["\u2018"])
        self.assertEqual(_slices(snapshot, document, "QUOT.END"), ["\u2019"])
        joined = " ".join(item["law_text"] for item in with_chart)
        self.assertNotIn("unless specifically exempted.", joined)
        self.assertNotIn("\u2018", joined)

    def _tmp(self) -> str:
        import tempfile

        path = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path


class TextChartTest(unittest.TestCase):
    def test_footnote_tail_is_uncovered_and_the_sentence_is_kept(self):
        chart = Chart.create("text", root=Path(self._tmp()))
        chart.ingester_name = "text"
        atoms = atomize(_FOOTNOTE, chart=chart)
        directory = chart.finish()
        snapshot, document = _partition(directory)
        self.assertTrue(any("keep this sentence" in item["law_text"] for item in atoms))
        self.assertIn("keep this sentence", snapshot)
        tails = _slices(snapshot, document, "footnote tail")
        self.assertEqual(len(tails), 1)
        self.assertIn("OJ L 333", tails[0])
        self.assertNotIn("OJ L 333", atoms[0]["law_text"])

    def test_heading_lines_are_uncovered(self):
        chart = Chart.create("text", root=Path(self._tmp()))
        atomize(_HEADING, chart=chart)
        directory = chart.finish()
        snapshot, document = _partition(directory)
        headings = _slices(snapshot, document, "heading")
        self.assertIn("ANNEX VII", headings)
        self.assertIn("ESSENTIAL CYBERSECURITY REQUIREMENTS", headings)
        self.assertIn("the product keeps a record.", snapshot)

    def _tmp(self) -> str:
        import tempfile

        path = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path


class ChartRunTest(unittest.TestCase):
    def test_text_adapter_writes_a_chart_without_fetching(self):
        root = Path(self._tmp())
        with patch("studio.pack.impl.extract.chart.urllib.request.urlopen") as opened:
            first = chart_run("cra", "https://example.test/cra", root=root)
            second = chart_run("cra", root=root)
        opened.assert_not_called()
        self.assertNotEqual(first, second)
        snapshot, document = _partition(first)
        self.assertTrue(snapshot)
        self.assertIsNone(document["source"]["edition"])
        self.assertEqual(document["source"]["id"], "CELEX:32024R2847")
        self.assertEqual(document["source"]["url"], "https://example.test/cra")
        self.assertEqual(document["snapshot"]["ingester"]["name"], "text")
        pinned = read_json(second / "sourcechart.json")
        self.assertIn("eur-lex.europa.eu", pinned["source"]["url"])

    def test_stub_writes_nothing(self):
        root = Path(self._tmp())
        with self.assertRaises(ModelError):
            chart_run("medtech", root=root)
        self.assertEqual(list(root.iterdir()), [])

    def test_cli_prints_the_chart_directory(self):
        root = Path(self._tmp())
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code = main(["--adapter", "cra", "--out", str(root)])
        self.assertEqual(code, 0)
        printed = Path(stdout.getvalue().strip())
        self.assertTrue((printed / "sourcechart.json").is_file())

    def test_formex_url_is_fetched_and_a_failure_removes_the_directory(self):
        root = Path(self._tmp())
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as archive:
            archive.writestr("readme.txt", "not a formex package")

        class Response:
            def read(self):
                return payload.getvalue()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        with patch(
            "studio.pack.impl.extract.chart.urllib.request.urlopen",
            return_value=Response(),
        ) as opened:
            with self.assertRaises(ModelError):
                chart_run("nis", "https://example.test/nis2.fmx4.zip", root=root)
        opened.assert_called_once()
        self.assertEqual(list(root.iterdir()), [])

    def _tmp(self) -> str:
        import tempfile

        path = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path


if __name__ == "__main__":
    unittest.main()
