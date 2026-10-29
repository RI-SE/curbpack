"""SYS-03: product I/O follows curbpack.json path fields (workspace.md §2)."""

from __future__ import annotations

import copy
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, _write_curbpack, make_handler
from claims.bind import build_claim, write_claim
from checks.run import claims_dir, packs_dir, reports_dir, results_dir, run_and_write, run_repository
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.store import save_pack, save_requirement
from common.validate import validate_curbpack_config
from discovery.door import created_curbpack, open_paths, open_repo_id, save_directory_fields, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack


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

ALLOWED_CURBPACK_KEYS = [
    "claims_dir",
    "exclude_requirements",
    "packs",
    "packs_dir",
    "reports_dir",
    "requirements",
    "results_dir",
    "search_hints",
    "unsigned_requirements",
]


def _config(**overrides) -> dict:
    document = {
        "packs": ["cra-baseline"],
        "search_hints": copy.deepcopy(CREATED_SEARCH_HINTS),
        "packs_dir": "curbpack/packs",
        "claims_dir": "curbpack/claims",
        "results_dir": ".curbpack",
        "reports_dir": "curbpack/reports",
        "unsigned_requirements": "reject",
    }
    document.update(overrides)
    return document


def _requirement(requirement_id: str, pack_id: str = "cra-baseline") -> dict:
    return {
        "id": requirement_id,
        "pack_id": pack_id,
        "source": {
            "framework": "EU",
            "instrument": "CRA",
            "identifier": "CELEX:32024R2847",
            "language": "en",
            "url": "https://example.invalid/cra",
        },
        "references": [{"nr": 1, "locator": "VII.1(a)", "law_text": "its intended purpose"}],
    }


def _exist_claim(claim_id: str, requirement_id: str, path: str) -> dict:
    return build_claim(
        claim_id=claim_id,
        requirement_id=requirement_id,
        source="documents",
        args={"path": path},
        checks=[{"check": "exist", "args": {"paths": [path]}}],
        description="The file is the reviewed evidence.",
    )


class CurbpackPathFieldsTest(unittest.TestCase):
    def test_four_directory_fields_resolve_independently(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            config = validate_curbpack_config(
                _config(
                    packs_dir="tree/packs",
                    claims_dir="kept/claims",
                    results_dir="runs/out",
                    reports_dir="signed/reports",
                )
            )
            self.assertEqual(packs_dir(repo, config), repo / "tree/packs")
            self.assertEqual(claims_dir(repo, config), repo / "kept/claims")
            self.assertEqual(results_dir(repo, config), repo / "runs/out")
            self.assertEqual(reports_dir(repo, config), repo / "signed/reports")

    def test_old_curbpack_key_is_rejected(self):
        document = _config()
        document["curbpack"] = "curbpack"
        with self.assertRaises(ModelError) as caught:
            validate_curbpack_config(document)
        self.assertEqual(
            str(caught.exception),
            "curbpack.json: field curbpack: expected one of " + str(ALLOWED_CURBPACK_KEYS),
        )

    def test_missing_required_keys_are_rejected(self):
        cases = {
            "packs_dir": "a relative directory",
            "claims_dir": "a relative directory",
            "results_dir": "a relative directory",
            "reports_dir": "a relative directory",
            "search_hints": "object",
            "unsigned_requirements": '"reject" or "signed_commit"',
            "packs": "non-empty list of strings",
        }
        for field, expected in cases.items():
            with self.subTest(field=field):
                document = _config()
                del document[field]
                with self.assertRaises(ModelError) as caught:
                    validate_curbpack_config(document)
                self.assertEqual(
                    str(caught.exception),
                    f"curbpack.json: field {field}: expected {expected}",
                )

    def test_both_selection_lists_are_rejected(self):
        document = _config(requirements=["CRA-PURPOSE"], exclude_requirements=["OTHER-REQ"])
        with self.assertRaises(ModelError) as caught:
            validate_curbpack_config(document)
        self.assertEqual(
            str(caught.exception),
            "curbpack.json: field requirements: expected absent when exclude_requirements is set",
        )

    def test_absolute_or_parent_directory_fields_are_rejected(self):
        for field, value in (
            ("packs_dir", "/tmp/packs"),
            ("claims_dir", "claims/../outside"),
        ):
            with self.subTest(field=field, value=value):
                document = _config(**{field: value})
                with self.assertRaises(ModelError) as caught:
                    validate_curbpack_config(document)
                self.assertEqual(
                    str(caught.exception),
                    f"curbpack.json: field {field}: expected a relative directory",
                )

    def test_run_repository_loads_versioned_pack_and_claims_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pack_dir = repo / "tree" / "packs" / "cra-baseline" / "0.1.0"
            save_pack(pack_dir, draft_pack())
            save_requirement(pack_dir, _requirement("CRA-PURPOSE"))
            save_requirement(pack_dir, _requirement("OTHER-REQ"))
            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            claims = repo / "kept" / "claims"
            write_claim(claims, _exist_claim("claim-readme", "CRA-PURPOSE", "README.md"))
            write_claim(claims, _exist_claim("claim-other", "OTHER-REQ", "README.md"))
            (repo / "runs" / "out").mkdir(parents=True)
            sentinel = repo / "runs" / "out" / "untouched.json"
            sentinel.write_text("{}\n", encoding="utf-8")
            write_json(
                repo / "curbpack.json",
                _config(
                    packs_dir="tree/packs",
                    claims_dir="kept/claims",
                    results_dir="runs/out",
                    reports_dir="signed/reports",
                    exclude_requirements=["OTHER-REQ"],
                ),
            )
            # Old layout must not be consulted.
            old_pack = repo / "curbpack" / "packs" / "cra-baseline"
            save_pack(old_pack, {"id": "cra-baseline", "name": "old", "version": "9.9.9"})
            write_claim(
                repo / "curbpack" / "claims",
                _exist_claim("claim-old-root", "CRA-PURPOSE", "README.md"),
            )

            result, code = run_repository(repo)

            self.assertEqual(code, 0)
            self.assertEqual(result["packs"][0]["id"], "cra-baseline")
            self.assertEqual(result["packs"][0]["version"], "0.1.0")
            self.assertEqual([row["id"] for row in result["claims"]], ["claim-readme"])
            self.assertEqual(result["claims"][0]["status"], "pass")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "{}\n")
            self.assertFalse((repo / "curbpack" / "run-result.json").exists())
            self.assertEqual(
                json.loads((repo / "curbpack.json").read_text(encoding="utf-8"))["claims_dir"],
                "kept/claims",
            )

    def test_invalid_config_stops_before_a_run_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_json(repo / "curbpack.json", {"packs": ["cra-baseline"], "curbpack": "curbpack"})
            results = repo / "runs" / "out" / "run-result.json"
            results.parent.mkdir(parents=True)
            results.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(ModelError) as caught:
                run_and_write(repo, None, results)
            self.assertEqual(
                str(caught.exception),
                "curbpack.json: field curbpack: expected one of " + str(ALLOWED_CURBPACK_KEYS),
            )
            self.assertEqual(results.read_text(encoding="utf-8"), "{}\n")

    def test_write_curbpack_keeps_path_fields_and_drops_curbpack(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            original = _config(
                packs_dir="tree/packs",
                claims_dir="kept/claims",
                results_dir="runs/out",
                reports_dir="signed/reports",
                exclude_requirements=["OTHER-REQ"],
            )
            original["curbpack"] = "curbpack"
            (repo / "curbpack.json").write_text(json.dumps(original) + "\n", encoding="utf-8")
            _write_curbpack(repo, ["cra-baseline", "house-policy"])
            written = json.loads((repo / "curbpack.json").read_text(encoding="utf-8"))
            self.assertEqual(written["packs"], ["cra-baseline", "house-policy"])
            self.assertEqual(written["packs_dir"], "tree/packs")
            self.assertEqual(written["claims_dir"], "kept/claims")
            self.assertEqual(written["results_dir"], "runs/out")
            self.assertEqual(written["reports_dir"], "signed/reports")
            self.assertEqual(written["unsigned_requirements"], "reject")
            self.assertEqual(written["exclude_requirements"], ["OTHER-REQ"])
            self.assertNotIn("curbpack", written)
            validate_curbpack_config(written)


class OpenRepoMemoryTest(unittest.TestCase):
    def test_open_repo_json_stores_only_a_known_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo_a = workspace / "alpha"
            repo_b = workspace / "beta"
            repo_a.mkdir()
            repo_b.mkdir()
            write_json(repo_a / "curbpack.json", _config(packs_dir="a-packs", claims_dir="a-claims"))
            write_json(repo_b / "curbpack.json", _config(packs_dir="b-packs", claims_dir="b-claims"))
            before_a = (repo_a / "curbpack.json").read_bytes()
            before_b = (repo_b / "curbpack.json").read_bytes()
            save_repos(
                workspace,
                add_repo(
                    workspace,
                    add_repo(workspace, load_repos(workspace), name="Alpha", path=str(repo_a)),
                    name="Beta",
                    path=str(repo_b),
                ),
            )

            self.assertIsNone(open_paths(workspace))
            self.assertIsNone(open_repo_id(workspace))
            with self.assertRaises(ModelError) as caught:
                set_open_repo(workspace, "")
            self.assertEqual(
                str(caught.exception),
                "open-repo.json: field id: expected an id already in product_repos.json",
            )
            self.assertFalse((workspace / "open-repo.json").exists())
            with self.assertRaises(ModelError) as caught:
                set_open_repo(workspace, "nope")
            self.assertEqual(
                str(caught.exception),
                "open-repo.json: field id: expected an id already in product_repos.json",
            )
            self.assertFalse((workspace / "open-repo.json").exists())
            set_open_repo(workspace, "alpha")
            set_open_repo(workspace, "beta")

            stored = read_json(workspace / "open-repo.json")
            self.assertEqual(stored, {"id": "beta"})
            self.assertEqual(open_repo_id(workspace), "beta")
            self.assertFalse((repo_a / "open-repo.json").exists())
            self.assertFalse((repo_b / "open-repo.json").exists())
            self.assertFalse((workspace / "selection.json").exists())
            self.assertFalse((repo_a / "selection.json").exists())
            self.assertEqual((repo_a / "curbpack.json").read_bytes(), before_a)
            self.assertEqual((repo_b / "curbpack.json").read_bytes(), before_b)

            resolved = open_paths(workspace)
            opened = repo_b.resolve()
            self.assertEqual(resolved["id"], "beta")
            self.assertEqual(resolved["path"], opened)
            self.assertEqual(resolved["packs_dir"], opened / "b-packs")
            self.assertEqual(resolved["claims_dir"], opened / "b-claims")
            self.assertEqual(resolved["results_dir"], opened / ".curbpack")
            self.assertEqual(resolved["reports_dir"], opened / "curbpack/reports")

            (workspace / "open-repo.json").write_text("{}\n", encoding="utf-8")
            self.assertIsNone(open_paths(workspace))
            write_json(workspace / "open-repo.json", {"id": ""})
            self.assertIsNone(open_paths(workspace))
            write_json(workspace / "open-repo.json", {"id": "nope"})
            self.assertIsNone(open_paths(workspace))
            write_json(workspace / "open-repo.json", {"id": "beta", "packs_dir": "sneak"})
            self.assertIsNone(open_paths(workspace))

            empty = workspace / "gamma"
            empty.mkdir()
            save_repos(
                workspace,
                add_repo(workspace, load_repos(workspace), name="Gamma", path=str(empty)),
            )
            set_open_repo(workspace, "gamma")
            self.assertEqual(open_repo_id(workspace), "gamma")
            bare = open_paths(workspace)
            self.assertEqual(bare["id"], "gamma")
            self.assertEqual(bare["path"], empty.resolve())
            self.assertIsNone(bare["packs_dir"])
            self.assertIsNone(bare["claims_dir"])
            self.assertIsNone(bare["results_dir"])
            self.assertIsNone(bare["reports_dir"])

    def test_saving_one_repo_path_field_leaves_the_other_file_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo_a = workspace / "alpha"
            repo_b = workspace / "beta"
            repo_a.mkdir()
            repo_b.mkdir()
            write_json(repo_a / "curbpack.json", _config(packs_dir="a-packs"))
            write_json(repo_b / "curbpack.json", _config(packs_dir="b-packs"))
            before_b = (repo_b / "curbpack.json").read_bytes()
            save_repos(
                workspace,
                add_repo(
                    workspace,
                    add_repo(workspace, load_repos(workspace), name="Alpha", path=str(repo_a)),
                    name="Beta",
                    path=str(repo_b),
                ),
            )
            set_open_repo(workspace, "alpha")
            save_directory_fields(repo_a, packs_dir="other/packs")
            self.assertEqual(read_json(repo_a / "curbpack.json")["packs_dir"], "other/packs")
            self.assertEqual((repo_b / "curbpack.json").read_bytes(), before_b)
            after_ok = (repo_a / "curbpack.json").read_bytes()
            with self.assertRaises(ModelError):
                save_directory_fields(repo_a, packs_dir="/tmp/packs")
            with self.assertRaises(ModelError):
                save_directory_fields(repo_a, claims_dir="claims/../out")
            self.assertEqual((repo_a / "curbpack.json").read_bytes(), after_ok)


def _register(workspace: Path, name: str, repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    save_repos(workspace, add_repo(workspace, load_repos(workspace), name=name, path=str(repo)))
    return name.strip().lower().replace(" ", "-")


def _pack_json(pack_id: str, name: str, **source) -> dict:
    pack = {"id": pack_id, "name": name, "version": draft_pack()["version"]}
    if source:
        pack["source"] = source
    return pack


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, fields: dict) -> str:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


class DoorUiTest(unittest.TestCase):
    def test_product_views_are_empty_until_a_repository_is_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            product = workspace / "product"
            product.mkdir()
            write_json(product / "curbpack.json", created_curbpack(packs=["hidden-pack"]))
            write_json(
                product / "curbpack" / "packs" / "hidden-pack" / "0.1.0" / "pack.json",
                _pack_json("hidden-pack", "Hidden Pack"),
            )
            write_json(
                product / ".curbpack" / "run-result.json",
                {"claims": [{"id": "hidden-claim", "status": "pass"}]},
            )
            write_json(
                workspace / "registered_sources.json",
                {
                    "documents": [
                        {
                            "id": "catalog-only",
                            "name": "Catalog Only",
                            "official_name": "Not a door pack",
                            "url": "https://example.test/catalog",
                            "adapter_id": "cra-xml",
                        }
                    ],
                    "sources": [],
                },
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(workspace)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                sources = _get(base + "/requirements")
                self.assertIn("Choose a repo", sources)
                self.assertNotIn("Hidden Pack", sources)
                self.assertNotIn("Catalog Only", sources)
                self.assertNotIn('id="add-open"', sources)
                editor = _get(base + "/requirements?document=hidden-pack")
                self.assertIn("Choose a repo", editor)
                self.assertNotIn("Hidden Pack", editor)
                discover = _get(base + "/discover")
                self.assertIn("Choose a repo", discover)
                self.assertNotIn("Catalog Only", discover)
                self.assertNotIn("Hidden Pack", discover)
                check = _get(base + "/check")
                self.assertIn("Choose a repo", check)
                self.assertNotIn("hidden-claim", check)
                self.assertNotIn("Hidden Pack", check)
                review = _get(base + "/review")
                self.assertIn("Choose a repo", review)
                self.assertIn("No repository is chosen", review)
                self.assertNotIn("hidden-claim", review)
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_curbpack_dialog_save_and_cancel_and_versioned_add(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo_a = workspace / "alpha"
            repo_b = workspace / "beta"
            _register(workspace, "Alpha", repo_a)
            _register(workspace, "Beta", repo_b)
            write_json(repo_b / "curbpack.json", created_curbpack(packs_dir="b-packs"))
            before_b = (repo_b / "curbpack.json").read_bytes()
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(workspace)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                empty = _get(base + "/requirements?repo=alpha")
                self.assertIn("curbpack.json", empty)
                self.assertIn('id="curbpack-dialog"', empty)
                self.assertIn('name="packs_dir"', empty)
                self.assertIn('name="claims_dir"', empty)
                self.assertIn('name="results_dir"', empty)
                self.assertIn('name="reports_dir"', empty)
                self.assertIn('name="unsigned_requirements"', empty)
                self.assertIn('name="search_hints"', empty)
                self.assertIn("Save", empty)
                self.assertIn("Cancel", empty)
                self.assertIn('<div class="head">', empty)
                self.assertIn('<div class="body">', empty)
                self.assertNotIn('id="add-open"', empty)
                self.assertFalse((repo_a / "curbpack.json").exists())
                fields = created_curbpack()
                saved = _post(
                    base + "/requirements/curbpack",
                    {
                        "repo": "alpha",
                        "action": "save",
                        "packs": "",
                        "packs_dir": fields["packs_dir"],
                        "claims_dir": fields["claims_dir"],
                        "results_dir": fields["results_dir"],
                        "reports_dir": fields["reports_dir"],
                        "unsigned_requirements": fields["unsigned_requirements"],
                        "search_hints": json.dumps(fields["search_hints"]),
                    },
                )
                written = read_json(repo_a / "curbpack.json")
                validate_curbpack_config(written)
                self.assertEqual(written["packs"], [])
                self.assertEqual(written["packs_dir"], "curbpack/packs")
                self.assertEqual(written["claims_dir"], "curbpack/claims")
                self.assertEqual(written["results_dir"], ".curbpack")
                self.assertEqual(written["reports_dir"], "curbpack/reports")
                self.assertEqual(written["unsigned_requirements"], "reject")
                self.assertIn("No Claims", saved)
                self.assertIn("No packs yet", saved)
                self.assertIn("Packs directory", saved)
                self.assertIn("Claims directory", saved)
                listed_missing = _post(
                    base + "/requirements/curbpack",
                    {
                        "repo": "alpha",
                        "action": "save",
                        "packs": "present-pack,ghost-pack",
                        "packs_dir": "tree/packs",
                        "claims_dir": "kept/claims",
                        "results_dir": fields["results_dir"],
                        "reports_dir": fields["reports_dir"],
                        "unsigned_requirements": fields["unsigned_requirements"],
                        "search_hints": json.dumps(fields["search_hints"]),
                    },
                )
                self.assertEqual((repo_b / "curbpack.json").read_bytes(), before_b)
                self.assertIn("ghost-pack", listed_missing)
                self.assertIn("missing", listed_missing)
                self.assertIn("present-pack", listed_missing)
                with self.assertRaises(urllib.error.HTTPError) as rejected:
                    _post(
                        base + "/requirements/documents",
                        {
                            "repo": "alpha",
                            "adapter_id": "cra-xml",
                            "name": "Bad Adapter",
                            "official_name": "House",
                            "url": "https://example.test/present",
                        },
                    )
                self.assertEqual(rejected.exception.code, 400)
                self.assertIn("matches this URL", rejected.exception.read().decode("utf-8"))
                added = _post(
                    base + "/requirements/documents",
                    {
                        "repo": "alpha",
                        "name": "Present Pack",
                        "official_name": "House",
                        "url": "https://example.test/present",
                    },
                )
                pack_file = repo_a / "tree" / "packs" / "present-pack" / draft_pack()["version"] / "pack.json"
                self.assertTrue(pack_file.is_file())
                pack = read_json(pack_file)
                self.assertEqual(pack["id"], "present-pack")
                self.assertEqual(pack["version"], draft_pack()["version"])
                self.assertNotEqual(pack["id"], draft_pack()["id"])
                self.assertEqual(read_json(repo_a / "curbpack.json")["packs"], ["present-pack", "ghost-pack"])
                self.assertIn("Present Pack", added)
                self.assertIn("House", added)
                self.assertIn('data-document="present-pack"', added)
                self.assertIn("ghost-pack", added)
                edit = _get(base + "/requirements?curbpack=edit")
                self.assertIn('value="tree/packs"', edit)
                self.assertIn('value="kept/claims"', edit)
                before_edit = (repo_a / "curbpack.json").read_bytes()
                _get(base + "/requirements?curbpack=edit")
                self.assertEqual((repo_a / "curbpack.json").read_bytes(), before_edit)
                self.assertEqual((repo_b / "curbpack.json").read_bytes(), before_b)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
