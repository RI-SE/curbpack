"""Pilot home Pack selection and thin Discover wiring."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.jsonio import read_json, write_json
from common.store import save_requirement
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import (
    create_extraction_copy,
    ensure_default_selection,
    list_pack_options,
    list_published_versions,
    list_working_copies,
    mark_published_selected,
    mark_selected,
    read_selection,
    resolve_selected_pack,
    selected_copy,
)


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(directory.glob("*.json"))}


def _requirement(requirement_id: str, concept: str) -> dict:
    requirement = extract_annex_vii_risk()
    requirement["id"] = requirement_id
    requirement["discovery_hints"] = {
        "concepts": [concept],
        "path_hints": ["*risk*"],
        "expected_evidence": ["assessment"],
        "sources": [{"source": "documents", "args": {"path": "docs"}}],
    }
    return requirement


def _product_with_hunt(root: Path) -> Path:
    repo = root / "product"
    repo.mkdir(parents=True)
    write_json(
        repo / "curbpack.json",
        {
            "packs": ["other-authoritative"],
            "search_hints": {
                "exclude_path_globs": ["**/node_modules/**"],
                "prefer_path_globs": ["**/docs/**"],
            },
        },
    )
    (repo / "docs").mkdir()
    (repo / "docs" / "risk-assessment.md").write_text(
        "product risk assessment notes\n", encoding="utf-8"
    )
    (repo / "readme.md").write_text("other text\n", encoding="utf-8")
    return repo


class PackOptionListingTest(unittest.TestCase):
    def test_lists_working_and_published_from_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = draft_pack()
            create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
            later = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T143000Z")
            save_requirement(later, _requirement("CRA-ANNEX-VII-RISK", "risk assessment"), published=False)
            published = root / "published" / "cra-baseline" / "0.1.0"
            published.mkdir(parents=True)
            (published / "pack.json").write_text(
                json.dumps({"id": "cra-baseline", "name": "CRA", "version": "0.1.0"}) + "\n",
                encoding="utf-8",
            )
            options = list_pack_options(root)
            kinds = {(item["kind"], item["pack_id"], item["ref"]) for item in options}
            self.assertIn(("working", "cra-baseline", "2026-10-13T090000Z"), kinds)
            self.assertIn(("working", "cra-baseline", "2026-10-13T143000Z"), kinds)
            self.assertIn(("published", "cra-baseline", "0.1.0"), kinds)
            self.assertEqual(list_published_versions(root, "cra-baseline"), ["0.1.0"])
            self.assertEqual(
                list_working_copies(root, "cra-baseline"),
                ["2026-10-13T090000Z", "2026-10-13T143000Z"],
            )


class SelectionStabilityTest(unittest.TestCase):
    def test_default_is_latest_working_and_explicit_selection_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = draft_pack()
            first = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
            second = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T143000Z")
            self.assertIsNone(read_selection(root))
            ensured = ensure_default_selection(root)
            self.assertEqual(ensured["kind"], "working")
            self.assertEqual(ensured["timestamp"], "2026-10-13T143000Z")
            self.assertEqual(resolve_selected_pack(root), second)
            mark_selected(root, "cra-baseline", "2026-10-13T090000Z")
            selection = read_selection(root)
            self.assertEqual(selection["kind"], "working")
            self.assertEqual(selection["timestamp"], "2026-10-13T090000Z")
            create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T180000Z")
            ensure_default_selection(root)
            self.assertEqual(read_selection(root)["timestamp"], "2026-10-13T090000Z")
            self.assertEqual(resolve_selected_pack(root), first)
            self.assertEqual(selected_copy(root, "cra-baseline"), first)

    def test_published_selection_does_not_mutate_release_or_curbpack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = draft_pack()
            copy = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
            save_requirement(copy, _requirement("CRA-ANNEX-VII-RISK", "risk"), published=False)
            published = root / "published" / "cra-baseline" / "0.1.0"
            published.mkdir(parents=True)
            for path in copy.glob("*.json"):
                (published / path.name).write_bytes(path.read_bytes())
            repo = _product_with_hunt(root)
            before_curb = (repo / "curbpack.json").read_bytes()
            before_pub = _file_bytes(published)
            mark_published_selected(root, "cra-baseline", "0.1.0")
            selection = read_selection(root)
            self.assertEqual(selection["kind"], "published")
            self.assertEqual(selection["version"], "0.1.0")
            self.assertEqual(resolve_selected_pack(root), published)
            self.assertIsNone(selected_copy(root, "cra-baseline"))
            ensure_default_selection(root)
            self.assertEqual(read_selection(root)["kind"], "published")
            self.assertEqual((repo / "curbpack.json").read_bytes(), before_curb)
            self.assertEqual(_file_bytes(published), before_pub)


class HomeAndDiscoverNavigationTest(unittest.TestCase):
    def test_home_selector_and_discover_require_explicit_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = draft_pack()
            first = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
            second = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T143000Z")
            save_requirement(first, _requirement("REQ-A", "alpha"), published=False)
            save_requirement(second, _requirement("REQ-A", "alpha"), published=False)
            save_requirement(second, _requirement("REQ-B", "risk assessment"), published=False)
            _product_with_hunt(root)
            published = root / "published" / "cra-baseline" / "0.1.0"
            published.mkdir(parents=True)
            (published / "pack.json").write_text(
                (second / "pack.json").read_text(encoding="utf-8"), encoding="utf-8"
            )
            (published / "REQ-A.json").write_bytes((second / "REQ-A.json").read_bytes())
            before_curb = (root / "product" / "curbpack.json").read_bytes()
            before_pub = _file_bytes(published)

            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                home = _get(base + "/")
                self.assertIn(">Home</a>", home)
                self.assertIn("Turn law into checkable packs", home)
                self.assertIn("author packs from law text", home)
                self.assertNotIn(">PoC2</a>", home)
                self.assertNotIn("Active Pack", home)
                self.assertNotIn("/select-pack", home)
                self.assertIn('href="/requirements"', home)
                self.assertIn('href="/discover"', home)
                self.assertIn('href="/check"', home)
                self.assertIn('href="/review"', home)
                self.assertNotIn("Developer", home)
                self.assertNotIn('href="/claims"', home)
                self.assertNotIn('href="/scaffold"', home)
                self.assertNotIn("No review report.", home)
                self.assertNotIn("signature verifies", home)

                _post(base + "/select-pack", {"kind": "working", "pack_id": "cra-baseline", "ref": "2026-10-13T090000Z"})

                requirements = _get(base + "/requirements/copy")
                self.assertIn("2026-10-13T090000Z", requirements)
                self.assertIn("REQ-A", requirements)

                discover = _get(base + "/discover")
                self.assertIn(">Pack</th>", discover)
                self.assertIn("Section", discover)
                self.assertIn(">Copy</th>", discover)
                self.assertIn("Add repo", discover)
                self.assertIn("Choose a repo", discover)
                self.assertNotIn("CRA Annex VII", discover)
                self.assertNotIn("matched_by", discover)
                self.assertNotIn("docs/risk-assessment.md", discover)

                _post(
                    base + "/select-pack",
                    {"kind": "published", "pack_id": "cra-baseline", "ref": "0.1.0"},
                )
                published_discover = _get(base + "/discover")
                self.assertIn(">Pack</th>", published_discover)
                self.assertIn(">Copy</th>", published_discover)
                self.assertNotIn("REQ-A", published_discover)
                self.assertEqual((root / "product" / "curbpack.json").read_bytes(), before_curb)
                self.assertEqual(_file_bytes(published), before_pub)
                curb = read_json(root / "product" / "curbpack.json")
                self.assertEqual(curb["packs"], ["other-authoritative"])
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_empty_workspace_home_has_clear_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                home = _get(base + "/")
                self.assertIn("Curbpack Studio", home)
                self.assertIn("author packs from law text", home)
                self.assertIn('href="/requirements"', home)
                self.assertNotIn("Developer", home)
                self.assertNotIn("No review report.", home)
                for href in ("/discover", "/check", "/review"):
                    self.assertIn(f'href="{href}"', home)
                for href in ("/claims", "/scaffold"):
                    self.assertNotIn(f'href="{href}"', home)
            finally:
                httpd.shutdown()
                httpd.server_close()


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, fields: dict[str, str]) -> str:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code in {302, 303}:
            return ""
        raise


if __name__ == "__main__":
    unittest.main()
