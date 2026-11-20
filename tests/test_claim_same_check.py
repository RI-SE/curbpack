"""Saving a Claim warns when another Claim already names one of its files."""

from __future__ import annotations

import unittest

from studio.claim.impl.bind import claims_sharing_a_source, source_overlap


def _claim(claim_id: str, paths: list[str], checks: list[dict]) -> dict:
    args = {"path": paths[0]} if len(paths) == 1 else {"paths": paths}
    return {
        "id": claim_id,
        "requirement_id": "REQ-A",
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
        self.assertEqual(rows[0]["sources"], ["SECURITY.md"])
        self.assertEqual(rows[0]["checks"], ["File has the expected content — SECURITY.md"])

    def test_the_claim_itself_is_left_out_even_as_another_object(self):
        claim = _claim("one", ["SECURITY.md"], [{"check": "exist", "args": {"paths": ["SECURITY.md"]}}])
        copy = _claim("one", ["SECURITY.md"], [{"check": "exist", "args": {"paths": ["SECURITY.md"]}}])
        self.assertEqual(claims_sharing_a_source(claim, [copy]), [])
        self.assertEqual(source_overlap(claim, [copy]), [])
