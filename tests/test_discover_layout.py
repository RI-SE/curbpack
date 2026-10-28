"""Discover pilot table and the selected-repo view."""

from __future__ import annotations

import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile

from app.server import Workspace, make_handler
from claims.bind import build_claim, write_claim
from common.jsonio import write_json
from common.store import save_requirement
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy, mark_selected


def _get(url: str) -> str:
    import urllib.request

    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _pack(pack_id: str) -> dict:
    pack = draft_pack()
    pack["id"] = pack_id
    pack["name"] = pack_id
    return pack


def _requirement(requirement_id: str, pack_id: str) -> dict:
    requirement = extract_annex_vii_risk()
    requirement["id"] = requirement_id
    requirement["pack_id"] = pack_id
    return requirement


class DiscoverLayoutTest(unittest.TestCase):
    def test_pilot_lists_sections_and_product_view_hides_choices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cra = create_extraction_copy(root, "cra-xml-baseline", _pack("cra-xml-baseline"), at="2026-10-13T090000Z")
            create_extraction_copy(root, "cra-xml-baseline", _pack("cra-xml-baseline"), at="2026-10-13T143000Z")
            save_requirement(cra, _requirement("REQ-A", "cra-xml-baseline"), published=False)
            save_requirement(cra, _requirement("REQ-B", "cra-xml-baseline"), published=False)
            mark_selected(root, "cra-xml-baseline", "2026-10-13T090000Z")
            published = root / "published" / "cra-xml-baseline" / "0.1.0"
            published.mkdir(parents=True)
            for path in cra.glob("*.json"):
                (published / path.name).write_bytes(path.read_bytes())
            nis = create_extraction_copy(root, "nis2-baseline", _pack("nis2-baseline"), at="2026-10-13T100000Z")
            save_requirement(nis, _requirement("REQ-N", "nis2-baseline"), published=False)

            repo = root / "product"
            repo.mkdir()
            write_json(repo / "curbpack.json", {"packs": ["cra-xml-baseline", "nis2-baseline"], "search_hints": {}})
            write_claim(
                repo / "claims",
                build_claim(
                    claim_id="claim-a",
                    requirement_id="REQ-A",
                    source="documents",
                    args={"path": "docs/a.md"},
                    checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
                    description="Evidence for A.",
                ),
            )
            from discovery.repos import add_repo, load_repos, save_repos

            data = load_repos(root)
            add_repo(root, data, name="sample-product", path=str(repo))
            save_repos(root, data)

            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                discover = _get(base + "/discover?repo=sample-product")
                self.assertIn("This page is the pilot", discover)
                self.assertIn('class="repo-picker" action="/discover"', discover)
                self.assertEqual(discover.count('name="repo"'), 1)
                self.assertLess(discover.index('name="repo"'), discover.index("<table>"))
                self.assertLess(discover.index("<table>"), discover.index("CRA Annex VII"))
                self.assertLess(discover.index("CRA Annex VII"), discover.index(">Add repo<"))
                self.assertIn("NIS2 Article 21", discover)
                self.assertIn("># Req</th>", discover)
                self.assertIn("># Claims</th>", discover)
                self.assertIn("># Req without<br>claims</th>", discover)
                self.assertLess(
                    discover.index("># Req without<br>claims</th>"),
                    discover.index(">Limit</th>"),
                )
                self.assertLess(discover.index(">Limit</th>"), discover.index(">Actions</th>"))
                self.assertIn("Working copy · 2026-10-13T090000Z", discover)
                self.assertNotIn("2026-10-13T143000Z", discover)
                self.assertIn("Published · 0.1.0", discover)
                self.assertNotIn("· written", discover)
                self.assertRegex(discover, r'class="req-link"[^>]*>2</a>')
                self.assertRegex(discover, r'class="claims-link"[^>]*>1</a>')
                self.assertRegex(discover, r'class="unclaimed-link"[^>]*>1</a>')
                self.assertIn('href="/discover/repo?repo=sample-product"', discover)
                self.assertIn(">Discover<", discover)
                self.assertIn("aria-label=\"Limit\"", discover)

                product = _get(base + "/discover/repo")
                self.assertIn('class="repo-picker" action="/discover/repo"', product)
                self.assertEqual(product.count('name="repo"'), 1)
                self.assertLess(product.index('name="repo"'), product.index("<table>"))
                self.assertIn('value="sample-product" selected', product)
                self.assertNotIn(">Add repo<", product)
                self.assertNotIn('class="copy-select"', product)
                self.assertIn("CRA Annex VII", product)
                self.assertIn("NIS2 Article 21", product)
                self.assertIn("Working copy · 2026-10-13T090000Z", product)
                self.assertIn("Working copy · 2026-10-13T100000Z", product)
                self.assertNotIn("Published · 0.1.0", product)
                self.assertNotIn("2026-10-13T143000Z", product)
                self.assertRegex(product, r'class="req-link"[^>]*>2</a>')
                self.assertRegex(product, r'class="claims-link"[^>]*>1</a>')
                self.assertRegex(product, r'class="unclaimed-link"[^>]*>1</a>')
                self.assertLess(product.index(">Limit</th>"), product.index(">Actions</th>"))
                self.assertIn(">Limit</th>", product)
                self.assertIn(">Discover<", product)
            finally:
                httpd.shutdown()
                httpd.server_close()
