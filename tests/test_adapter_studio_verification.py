"""Adapter-studio verification column. The Curbpack extract pipeline is not involved."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from common.errors import ModelError

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "adapter-studio" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verification = _load("adapter_studio_verification", "verification.py")
server = _load("adapter_studio_server", "server.py")


def _suggestion() -> dict:
    return {
        "verification_objective": "The product reports possible unauthorised access.",
        "verification_methods": [
            {
                "method": "Trigger an access attempt the product treats as unauthorised and inspect the report.",
                "verifies": "reporting of possible unauthorised access",
                "additional_assumption": None,
            }
        ],
        "evidence_hints": ["The report produced by that attempt."],
        "verification_assumptions": [],
    }


class VerificationHintsTest(unittest.TestCase):
    def test_tab_sits_between_discovery_and_assemble(self):
        self.assertEqual(
            server.STEPS,
            (
                ("00", "Structure"),
                ("01", "Atomize"),
                ("02", "Interpret"),
                ("03", "Discovery hints"),
                ("04", "Verification hints"),
                ("05", "Assemble"),
            ),
        )

    def test_rows_without_an_atomic_requirement_are_not_inputs(self):
        provisions = [
            {"locus": "I-2(d)", "law_text": "The product shall report on possible unauthorised access."},
            {"locus": "I-1", "law_text": "Part heading"},
            {"locus": "gone", "law_text": "Deleted row"},
        ]
        interpret_rows = [
            {"locus": "I-2(d)", "id": "CRA-PART-I-UNAUTHORISED-ACCESS", "locator": "I.2(d)"},
            {"locus": "I-1", "locator": "I.1"},
            {"locus": "gone", "id": "   ", "locator": "X"},
        ]
        inputs = verification.verification_inputs(provisions, interpret_rows)
        self.assertEqual([item["locus"] for item in inputs], ["I-2(d)"])

    def test_valid_model_json_is_kept(self):
        seen = []

        def complete(prompt, settings):
            seen.append((prompt, settings))
            return "```json\n" + json.dumps(_suggestion()) + "\n```"

        rows = verification.propose_verification(
            [
                {
                    "locus": "I-2(d)",
                    "source_text": "The product shall report on possible unauthorised access.",
                    "atom": "The product shall report on possible unauthorised access.",
                    "locator": "I.2(d)",
                }
            ],
            complete=complete,
        )
        self.assertEqual(rows[0]["locus"], "I-2(d)")
        self.assertEqual(rows[0]["verification_objective"], _suggestion()["verification_objective"])
        self.assertIn("Do not determine whether the product complies.", seen[0][0])
        self.assertIn("I.2(d)", seen[0][0])
        self.assertNotIn("{locator}", seen[0][0])

    def test_invalid_model_json_is_rejected(self):
        def complete(prompt, settings):
            return json.dumps({"verification_objective": "reports access"})

        with self.assertRaises(ModelError):
            verification.propose_verification(
                [{"locus": "I-2(d)", "source_text": "text", "atom": "text", "locator": "I.2(d)"}],
                complete=complete,
            )

    def test_prompt_keeps_the_traceability_rules(self):
        text = (ROOT / "adapter-studio" / "prompts" / "verification_hints.txt").read_text(encoding="utf-8")
        for phrase in (
            "Do not silently introduce cybersecurity best practices as legal requirements.",
            "including but not limited to",
            "Do not determine whether the product complies.",
        ):
            self.assertIn(phrase, text)
