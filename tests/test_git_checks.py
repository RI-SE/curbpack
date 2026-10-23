"""CHK-05 Git Check schemas. Behavior tests come in later tasks."""

from __future__ import annotations

import unittest

from checks.schema import load_registry, validate_check_args
from common.errors import ModelError

_GIT_IDS = ("git_fresh", "git_signed", "git_author", "git_signer")
_AS_OF = "2026-10-23T06:00:00Z"


def _commands() -> dict[str, str]:
    found = {}
    for item in load_registry()["checks"]:
        if item.get("id") in _GIT_IDS:
            found[item["id"]] = item.get("command")
    return found


class GitCheckSchemaTest(unittest.TestCase):
    def test_four_ids_share_one_command_and_old_ids_remain(self):
        commands = _commands()
        self.assertEqual(set(commands), set(_GIT_IDS))
        self.assertEqual(set(commands.values()), {"curbcheck-git"})
        registered = {item["id"] for item in load_registry()["checks"]}
        self.assertIn("fresh", registered)
        self.assertIn("owned", registered)

    def test_git_fresh_requires_as_of_and_a_non_negative_age(self):
        validate_check_args(
            "git_fresh",
            {"path": "docs/a.md", "max_age_days": 0, "as_of": _AS_OF},
        )
        with self.assertRaises(ModelError):
            validate_check_args("git_fresh", {"path": "docs/a.md", "max_age_days": 2})
        with self.assertRaises(ModelError):
            validate_check_args(
                "git_fresh",
                {"path": "docs/a.md", "max_age_days": -1, "as_of": _AS_OF},
            )
        with self.assertRaises(ModelError):
            validate_check_args(
                "git_fresh",
                {"path": "docs/a.md", "max_age_days": 2, "as_of": "Friday"},
            )
        validate_check_args(
            "git_fresh",
            {"path": "docs/a.md", "max_age_days": 2, "as_of": "2026-10-23T06:00:00+02:00"},
        )
        validate_check_args(
            "git_fresh",
            {"path": "docs/a.md", "max_age_days": 2, "as_of": "2026-10-23T06:00:00.1234567Z"},
        )
        for bad in (
            "2026-10-23T06:00:00",
            "2026-10-23T06:00Z",
            "2026-10-23T06:00:00.Z",
            "2026-10-23T06:00:00+00:00:30",
        ):
            with self.assertRaises(ModelError):
                validate_check_args(
                    "git_fresh",
                    {"path": "docs/a.md", "max_age_days": 2, "as_of": bad},
                )

    def test_git_signed_takes_exactly_one_trust_input(self):
        validate_check_args(
            "git_signed",
            {"path": "docs/a.md", "allowed_signers": ".git-allowed-signers"},
        )
        validate_check_args("git_signed", {"path": "docs/a.md", "openpgp": "repo"})
        with self.assertRaises(ModelError):
            validate_check_args(
                "git_signed",
                {
                    "path": "docs/a.md",
                    "allowed_signers": ".git-allowed-signers",
                    "openpgp": "repo",
                },
            )
        with self.assertRaises(ModelError):
            validate_check_args("git_signed", {"path": "docs/a.md"})
        with self.assertRaises(ModelError):
            validate_check_args(
                "git_signed",
                {"path": "docs/a.md", "allowed_signers": "../keys"},
            )

    def test_git_author_needs_a_name_or_an_email(self):
        validate_check_args("git_author", {"path": "docs/a.md", "name": "Anna"})
        validate_check_args("git_author", {"path": "docs/a.md", "email": "anna@example.com"})
        validate_check_args(
            "git_author",
            {"path": "docs/a.md", "name": "Anna", "email": "anna@example.com"},
        )
        with self.assertRaises(ModelError):
            validate_check_args("git_author", {"path": "docs/a.md"})

    def test_git_signer_names_a_signer_and_one_trust_input(self):
        validate_check_args(
            "git_signer",
            {"path": "docs/a.md", "signer": "Anna", "allowed_signers": ".git-allowed-signers"},
        )
        validate_check_args(
            "git_signer",
            {"path": "docs/a.md", "signer": "Anna", "openpgp": "repo"},
        )
        with self.assertRaises(ModelError):
            validate_check_args("git_signer", {"path": "docs/a.md", "signer": "Anna"})
