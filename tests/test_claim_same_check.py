"""Saving a Claim warns when another Claim already names one of its files."""

from __future__ import annotations

import unittest

from studio.claim.impl.bind import claims_sharing_a_source, source_overlap


def _claim(
    claim_id: str,
    paths: list[str],
    checks: list[dict],
    requirement_id: str = "REQ-A",
) -> dict:
    args = {"path": paths[0]} if len(paths) == 1 else {"paths": paths}
    return {
        "id": claim_id,
        "requirement_id": requirement_id,
        "source": "documents",
        "args": args,
        "checks": checks,
    }


class SharedSourceTest(unittest.TestCase):
    def test_a_shared_file_returns_the_other_claim_and_its_checks(self):
        claim = _claim(
            "several",
            ["README.md", "SECURITY.md"],
            [{"check": "exist", "args": {"paths": ["README.md", "SECURITY.md"]}}],
        )
        other = _claim(
            "headers",
            ["SECURITY.md"],
            [
                {
                    "check": "contents",
                    "args": {
                        "path": "SECURITY.md",
                        "probes": [{"kind": "headers", "headers": ["# Security"]}],
                    },
                }
            ],
        )
        unrelated = _claim(
            "elsewhere",
            ["docs/other.md"],
            [{"check": "exist", "args": {"paths": ["docs/other.md"]}}],
        )
        found = claims_sharing_a_source(claim, [claim, unrelated, other])
        self.assertEqual([item["id"] for item in found], ["headers"])
        rows = source_overlap(claim, [claim, unrelated, other])
        self.assertEqual(
            rows,
            [
                {
                    "file": "SECURITY.md",
                    "requirement_id": "REQ-A",
                    "checks": [
                        {
                            "caption": "File has the expected content",
                            "fields": [{"label": "Require headers", "value": "# Security"}],
                        }
                    ],
                }
            ],
        )

    def test_rows_are_one_file_each_sorted_by_file_then_requirement(self):
        claim = _claim("several", ["README.md", "SECURITY.md"], [])
        later = _claim(
            "b",
            ["README.md"],
            [{"check": "exist", "args": {"paths": ["README.md"]}}],
            requirement_id="REQ-B",
        )
        earlier = _claim(
            "a",
            ["SECURITY.md", "README.md"],
            [
                {"check": "exist", "args": {"paths": ["README.md", "SECURITY.md"]}},
                {
                    "check": "contents",
                    "args": {"paths": ["SECURITY.md"], "probes": [{"kind": "placeholder"}]},
                },
            ],
            requirement_id="REQ-A",
        )
        rows = source_overlap(claim, [later, earlier])
        self.assertEqual(
            [(row["file"], row["requirement_id"], [item["caption"] for item in row["checks"]]) for row in rows],
            [
                ("README.md", "REQ-A", ["File is present"]),
                ("README.md", "REQ-B", ["File is present"]),
                ("SECURITY.md", "REQ-A", ["File is present", "File is not a placeholder"]),
            ],
        )
        security = rows[2]["checks"]
        self.assertEqual(security[0]["fields"], [])
        self.assertEqual(security[1]["fields"], [])

    def test_the_claim_itself_is_left_out_even_as_another_object(self):
        claim = _claim("one", ["SECURITY.md"], [{"check": "exist", "args": {"paths": ["SECURITY.md"]}}])
        copy = _claim("one", ["SECURITY.md"], [{"check": "exist", "args": {"paths": ["SECURITY.md"]}}])
        self.assertEqual(claims_sharing_a_source(claim, [copy]), [])
        self.assertEqual(source_overlap(claim, [copy]), [])
