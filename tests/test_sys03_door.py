"""SYS-03: product I/O follows curbpack.json path fields (workspace.md §2)."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from app.server import _write_curbpack
from claims.bind import build_claim, write_claim
from checks.run import claims_dir, packs_dir, reports_dir, results_dir, run_and_write, run_repository
from common.errors import ModelError
from common.jsonio import write_json
from common.store import save_pack, save_requirement
from common.validate import validate_curbpack_config
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


if __name__ == "__main__":
    unittest.main()
