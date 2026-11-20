"""A Check tool may attach optional remediation guidance to a failure.

The hint is a non-empty string on a fail result. The runner copies it and does
not invent, trim, or apply it. Pass, skip, Claim, and Requirement stay unchanged.
"""

from __future__ import annotations

import copy
import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from checks.dispatch import run_check_tool
from checks.run import build_run_result
from checks.schema import registry_entry
from claims.bind import build_claim
from common.canonical import version_digest
from common.errors import ModelError
from common.signing import generate_keypair
from common.store import load_run_result, save_run_result
from common.validate import validate_claim, validate_run_result
from review.compile import compile_report, read_report_signature, record_decision, sign_report

_PACKS = [{"id": "example", "version": "0.1.0", "digest": "abc"}]
_HINT = "Add the missing file."


def _claim(checks: list[dict] | None = None) -> dict:
    return build_claim(
        claim_id="claim-hint",
        requirement={"id": "REQ-A", "namespace": "RISE/Example", "pack_id": "example"},
        source="documents",
        args={"path": "docs/a.md"},
        checks=checks or [{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
        description="The reviewed file is the evidence for this Requirement.",
        severity="high",
    )


def _requirement() -> dict:
    return {
        "id": "REQ-A",
        "pack_id": "example",
        "namespace": "RISE/Example",
        "remediation_hint": "Publisher advice that the runner must leave on the Requirement.",
        "source": {
            "framework": "test",
            "instrument": "test",
            "identifier": "FIX-1",
            "language": "en",
            "url": "https://example.test",
        },
        "references": [{"nr": 1, "locator": "1", "law_text": "The product documents the risk."}],
    }


def _script(root: Path, payload: dict) -> Path:
    script = root / "curbcheck-probe"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.stdout.write({json.dumps(json.dumps(payload))})\n"
        "sys.stdout.write('\\n')\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _run_with_tool(root: Path, payload: dict, claim: dict | None = None) -> dict:
    script = _script(root, payload)
    claim = claim or _claim()

    def entry(check: str):
        found = registry_entry(check)
        if check == "exist" and isinstance(found, dict):
            return {**found, "command": str(script)}
        return found

    with patch("checks.run.registry_entry", side_effect=entry):
        return build_run_result(root, [claim], _PACKS, requirements=[])


def _stored(status: str, **extra: object) -> dict:
    row = {
        "index": 0,
        "check": "exist",
        "args": {"paths": ["docs/a.md"]},
        "status": status,
    }
    if status != "pass":
        row["detail"] = "docs/a.md is absent"
    row.update(extra)
    claim_status = status if status != "pass" else "pass"
    return {
        "packs": _PACKS,
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "claims": [
            {
                "id": "claim-hint",
                "digest": "d" * 64,
                "status": claim_status,
                "checks": [row],
            }
        ],
    }


class RemediationHintTest(unittest.TestCase):
    def test_a_failing_tool_keeps_its_hint_on_the_saved_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_with_tool(
                root,
                {
                    "status": "fail",
                    "detail": "docs/a.md is absent",
                    "remediation_hint": f"  {_HINT}  ",
                    "advice": "drop this",
                },
            )
            path = root / "run-result.json"
            save_run_result(path, result)
            check = load_run_result(path)["claims"][0]["checks"][0]
        self.assertEqual(check["status"], "fail")
        self.assertEqual(check["detail"], "docs/a.md is absent")
        self.assertEqual(check["remediation_hint"], f"  {_HINT}  ")
        self.assertNotIn("advice", check)

    def test_a_blank_or_non_string_hint_is_omitted_and_the_failure_stays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for hint in ("   ", 3, None):
                result = _run_with_tool(
                    root,
                    {"status": "fail", "detail": "docs/a.md is absent", "remediation_hint": hint},
                )
                check = result["claims"][0]["checks"][0]
                self.assertEqual(check["status"], "fail")
                self.assertEqual(check["detail"], "docs/a.md is absent")
                self.assertNotIn("remediation_hint", check)

    def test_a_passing_tool_hint_is_not_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_with_tool(
                root,
                {"status": "pass", "remediation_hint": _HINT},
            )
        check = result["claims"][0]["checks"][0]
        self.assertEqual(
            check,
            {"index": 0, "check": "exist", "args": {"paths": ["docs/a.md"]}, "status": "pass"},
        )

    def test_skip_and_a_missing_tool_do_not_invent_a_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("inside\n", encoding="utf-8")
            claim = _claim(
                [
                    {"check": "fresh", "args": {"path": "docs/a.md", "max_age_days": 2}},
                    {"check": "exist", "args": {"paths": ["docs/a.md"]}},
                ]
            )
            skipped = build_run_result(root, [claim], _PACKS, requirements=[], skip={"claim-hint": "not this build"})
            self.assertEqual(skipped["claims"][0]["status"], "skipped")
            for check in skipped["claims"][0]["checks"]:
                self.assertEqual(check["detail"], "not this build")
                self.assertNotIn("remediation_hint", check)
            failed = build_run_result(
                root,
                [_claim([{"check": "fresh", "args": {"path": "docs/a.md", "max_age_days": 2}}])],
                _PACKS,
                requirements=[],
            )
        check = failed["claims"][0]["checks"][0]
        self.assertEqual(check["status"], "fail")
        self.assertIn("unavailable", check["detail"])
        self.assertNotIn("remediation_hint", check)

    def test_the_requirement_hint_is_not_copied_onto_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claim = _claim()
            result = build_run_result(
                root,
                [claim],
                _PACKS,
                requirements=[({"id": "example", "namespace": "RISE/Example"}, [_requirement()])],
            )
        check = result["claims"][0]["checks"][0]
        self.assertEqual(check["status"], "fail")
        self.assertIn("is absent", check["detail"])
        self.assertNotIn("remediation_hint", check)
        self.assertNotIn("remediation_hint", claim["checks"][0])

    def test_a_claim_cannot_store_a_check_hint(self):
        claim = _claim()
        claim["checks"][0]["remediation_hint"] = _HINT
        with self.assertRaises(ModelError) as caught:
            validate_claim(claim)
        self.assertIn("checks[0]", caught.exception.object_name)
        self.assertEqual(caught.exception.field, "remediation_hint")
        sealed = _claim()
        sealed["remediation"] = _HINT
        with self.assertRaises(ModelError) as forbidden:
            validate_claim(sealed)
        self.assertEqual(forbidden.exception.field, "remediation")

    def test_validation_accepts_only_a_non_empty_hint_on_fail(self):
        accepted = validate_run_result(_stored("fail", remediation_hint=_HINT))
        self.assertEqual(accepted["claims"][0]["checks"][0]["remediation_hint"], _HINT)
        historical = validate_run_result(_stored("fail"))
        self.assertNotIn("remediation_hint", historical["claims"][0]["checks"][0])
        for status in ("pass", "skipped"):
            with self.assertRaises(ModelError) as caught:
                validate_run_result(_stored(status, remediation_hint=_HINT))
            self.assertTrue(caught.exception.field.endswith("remediation_hint"))
            self.assertIn("absent", caught.exception.expected)
        for hint in ("  ", 3):
            with self.assertRaises(ModelError) as caught:
                validate_run_result(_stored("fail", remediation_hint=hint))
            self.assertEqual(caught.exception.field, "remediation_hint")
            self.assertIn("non-empty string", caught.exception.expected)

    def test_compile_preserves_a_hint_and_still_accepts_a_result_without_one(self):
        claim = _claim()
        requirement = _requirement()
        hinted = _stored("fail", remediation_hint=_HINT)
        hinted["claims"][0]["id"] = claim["id"]
        hinted["claims"][0]["digest"] = version_digest(claim)
        report = compile_report(run_result=hinted, requirements=[requirement], claims=[claim])
        self.assertEqual(
            report["run_result"]["claims"][0]["checks"][0]["remediation_hint"],
            _HINT,
        )
        plain = _stored("fail")
        plain["claims"][0]["id"] = claim["id"]
        plain["claims"][0]["digest"] = version_digest(claim)
        compiled = compile_report(run_result=plain, requirements=[requirement], claims=[claim])
        self.assertNotIn("remediation_hint", compiled["run_result"]["claims"][0]["checks"][0])

    def test_a_persisted_check_rejects_an_unknown_key(self):
        stored = _stored("fail", remediation_hint=_HINT, advice="not a result field")
        with self.assertRaises(ModelError) as caught:
            validate_run_result(stored)
        self.assertEqual(caught.exception.field, "advice")
        self.assertIn("one of", caught.exception.expected)
        self.assertNotIn("advice", caught.exception.expected)

    def test_an_empty_hint_is_left_off_the_tool_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = _script(
                root,
                {"status": "fail", "detail": "probe says no", "remediation_hint": ""},
            )
            result = run_check_tool(root, str(script), "demo", {"path": "notes.md"})
        self.assertEqual(result, {"status": "fail", "detail": "probe says no"})

    def test_an_unusable_detail_does_not_keep_the_hint(self):
        payloads = [
            {"status": "fail", "detail": "", "remediation_hint": _HINT},
            {"status": "fail", "detail": "   ", "remediation_hint": _HINT},
            {"status": "fail", "detail": 3, "remediation_hint": _HINT},
            {"status": "fail", "remediation_hint": _HINT},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for payload in payloads:
                script = _script(root, payload)
                result = run_check_tool(root, str(script), "demo", {"path": "notes.md"})
                self.assertEqual(result["status"], "fail")
                self.assertNotIn("remediation_hint", result)
                self.assertNotIn(_HINT, result["detail"])
                self.assertIn("failed", result["detail"])

    def test_a_signed_report_keeps_the_hint_under_the_signature(self):
        private, public = generate_keypair()
        claim = _claim()
        requirement = _requirement()
        hinted = _stored("fail", remediation_hint=_HINT)
        hinted["claims"][0]["id"] = claim["id"]
        hinted["claims"][0]["digest"] = version_digest(claim)
        report = compile_report(run_result=hinted, requirements=[requirement], claims=[claim])
        decided = record_decision(report, "I read the recorded check failure.")
        sealed = sign_report(
            decided,
            name="Ada Reviewer",
            private_key=private,
            at="2026-10-21T12:00:00Z",
        )
        trust = {"Ada Reviewer": public}
        reading = read_report_signature(sealed, trust)
        self.assertTrue(reading["verifiable"])
        self.assertEqual(reading["what"], "review report")
        self.assertEqual(reading["who"], "Ada Reviewer")
        self.assertEqual(
            sealed["run_result"]["claims"][0]["checks"][0]["remediation_hint"],
            _HINT,
        )
        self.assertEqual(
            sealed["requirements"][0]["remediation_hint"],
            requirement["remediation_hint"],
        )
        changed = copy.deepcopy(sealed)
        changed["run_result"]["claims"][0]["checks"][0]["remediation_hint"] = "A different hint."
        broken = read_report_signature(changed, trust)
        self.assertFalse(broken["verifiable"])
        self.assertIn("not the digest that was signed", broken["reason"])
        self.assertTrue(read_report_signature(sealed, trust)["verifiable"])

    def test_the_tool_response_returns_the_hint_without_running_a_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = _script(
                root,
                {"status": "fail", "detail": "probe says no", "remediation_hint": _HINT},
            )
            result = run_check_tool(root, str(script), "demo", {"path": "notes.md"})
        self.assertEqual(
            result,
            {"status": "fail", "detail": "probe says no", "remediation_hint": _HINT},
        )
