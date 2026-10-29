"""Registered source catalog for the Requirements UI."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.errors import ModelError
from common.jsonio import read_json, write_json
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack
from requirements.catalog import (
    add_document,
    add_section,
    add_source,
    ensure_catalog,
    load_catalog,
    make_document_id,
    make_id,
    save_catalog,
)


class RequirementsCatalogTest(unittest.TestCase):
    def test_defaults_and_add_keep_adapter_fixed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = ensure_catalog(root)
            ids = {row["id"] for row in catalog["sources"]}
            self.assertIn(make_id("cra-xml", "VII"), ids)
            self.assertIn(make_id("nis", "Art.21"), ids)
            cra = next(row for row in catalog["sources"] if row["adapter_id"] == "cra-xml")
            self.assertEqual(cra["official_name"], "Content of the technical documentation")
            self.assertEqual(cra["section_id"], "VII")
            self.assertEqual(cra["document_id"], make_document_id("CRA Annex VII"))
            self.assertEqual(
                {row["id"] for row in catalog["documents"]},
                {make_document_id("CRA Annex VII"), make_document_id("NIS2 Article 21")},
            )
            before = len(catalog["sources"])
            add_document(
                catalog,
                name="Extra instrument",
                official_name="An extra document",
                url="https://example.test/extra",
                adapter_id="nis",
            )
            self.assertEqual(len(catalog["sources"]), before)
            with self.assertRaises(ModelError):
                add_section(
                    catalog,
                    document_id=make_document_id("CRA Annex VII"),
                    section_id="V",
                )
            add_section(
                catalog,
                document_id=make_document_id("NIS2 Article 21"),
                section_id="Art.1",
            )

            add_source(
                catalog,
                name="CRA Annex II",
                official_name="Information and instructions to the user",
                url="https://example.test/cra",
                adapter_id="cra-xml",
                section_id="II",
            )
            save_catalog(root, catalog)
            reloaded = load_catalog(root)
            self.assertEqual(len(reloaded["sources"]), 4)
            with self.assertRaises(ModelError):
                add_source(
                    reloaded,
                    name="Dup",
                    url="https://example.test/cra",
                    adapter_id="cra-xml",
                    section_id="VII",
                )

    def test_add_via_http(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            repo.mkdir()
            catalog_path = root / "registered_sources.json"
            write_json(repo / "curbpack.json", created_curbpack(packs=[]))
            save_repos(root, add_repo(root, load_repos(root), name="Product", path=str(repo)))
            set_open_repo(root, "product")
            before_catalog = catalog_path.read_bytes() if catalog_path.is_file() else None
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                before = _get(base + "/requirements")
                self.assertIn("Pack Sources", before)
                self.assertIn('id="add-open"', before)
                self.assertIn("Official name", before)
                self.assertNotIn("Section<select", before)
                data = urllib.parse.urlencode(
                    {
                        "repo": "product",
                        "adapter_id": "cra-xml",
                        "name": "CRA Annex V",
                        "official_name": "EU declaration of conformity",
                        "url": "https://publications.europa.eu/resource/celex/32024R2847",
                    }
                ).encode("utf-8")
                request = urllib.request.Request(
                    base + "/requirements/documents", data=data, method="POST"
                )
                with urllib.request.urlopen(request) as response:
                    page = response.read().decode("utf-8")
                self.assertIn("Pack added", page)
                self.assertIn("CRA Annex V", page)
                self.assertIn("EU declaration of conformity", page)
                self.assertIn('data-document="cra-annex-v"', page)
                pack_file = (
                    repo / "curbpack" / "packs" / "cra-annex-v" / draft_pack()["version"] / "pack.json"
                )
                self.assertTrue(pack_file.is_file())
                self.assertEqual(read_json(repo / "curbpack.json")["packs"], ["cra-annex-v"])
                catalog = read_json(catalog_path) if catalog_path.is_file() else {"documents": []}
                self.assertNotIn(
                    "cra-annex-v",
                    [row.get("id") for row in catalog.get("documents") or []],
                )
                if before_catalog is not None:
                    self.assertEqual(catalog_path.read_bytes(), before_catalog)
                editor = _get(base + "/requirements?document=cra-annex-vii")
                self.assertIn("Pack Editor", editor)
                self.assertIn("Add section", editor)
                self.assertIn('"id": "VII"', editor)
                self.assertNotIn('"id": "V"', editor)
                self.assertNotIn("Cannot be extracted", editor)
                self.assertNotIn('data-adapter="nis"', editor)
                added_editor = _get(base + "/requirements?document=cra-annex-v")
                self.assertIn("Pack Editor", added_editor)
                self.assertIn("CRA Annex V", added_editor)
                blocked = urllib.parse.urlencode(
                    {
                        "document_id": "cra-annex-v",
                        "section_id": "V",
                        "repo": "product",
                    }
                ).encode("utf-8")
                refused = urllib.request.Request(
                    base + "/requirements/catalog", data=blocked, method="POST"
                )
                with self.assertRaises(urllib.error.HTTPError) as rejected:
                    urllib.request.urlopen(refused)
                self.assertEqual(rejected.exception.code, 400)
                self.assertIn("can be extracted", rejected.exception.read().decode("utf-8"))
            finally:
                httpd.shutdown()
                httpd.server_close()


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
