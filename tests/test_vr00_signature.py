"""VR-00 signature result. Object signatures, then Git."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.canonical import pack_directory_digest, version_digest
from common.jsonio import write_json
from common.signing import complete_pack_digest, generate_keypair, signed_block, verify_object


class ObjectSignatureTest(unittest.TestCase):
    def test_valid_object_signature_reports_signer_and_digest(self):
        private, public = generate_keypair()
        payload = {"id": "REQ-1", "pack_id": "pack"}
        digest = version_digest(payload)
        block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        result = verify_object(digest, block, {"Ada": public})
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["method"], "object")
        self.assertEqual(result["signer"], "Ada")
        self.assertEqual(result["version"], digest)

    def test_bad_object_signature_stays_invalid(self):
        private, public = generate_keypair()
        payload = {"id": "REQ-1", "pack_id": "pack"}
        digest = version_digest(payload)
        block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        result = verify_object(digest + "ff", block, {"Ada": public})
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["method"], "object")
        self.assertIn("does not verify", result["reason"])

    def test_missing_certificate_is_invalid_without_fetching(self):
        private, _public = generate_keypair()
        payload = {"id": "REQ-1"}
        digest = version_digest(payload)
        block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        result = verify_object(digest, block, {})
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["method"], "object")
        self.assertIn("not available", result["reason"])
        self.assertIn("does not fetch", result["reason"])

    def test_version_digest_ignores_format_version(self):
        private, public = generate_keypair()
        requirement = {"id": "REQ-1", "pack_id": "pack", "note": "keep"}
        digest = version_digest(requirement)
        block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        changed = {**requirement, "format_version": 1}
        self.assertEqual(version_digest(changed), digest)
        result = verify_object(version_digest(changed), block, {"Ada": public})
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["version"], digest)

    def test_dotfile_changes_the_pack_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "pack.json", {"id": "pack", "version": "1"})
            hidden = root / ".note"
            hidden.write_text("a", encoding="utf-8")
            before = complete_pack_digest(root)
            self.assertEqual(before, pack_directory_digest(root))
            hidden.write_text("b", encoding="utf-8")
            after = complete_pack_digest(root)
            self.assertNotEqual(before, after)
            self.assertEqual(after, pack_directory_digest(root))


def _git(repo: Path, *args: str, env: dict | None = None) -> str:
    import os
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env=env,
    )
    return result.stdout.decode("utf-8")


def _unsigned_commit(repo: Path, relative: str) -> None:
    if not (repo / ".git").is_dir():
        _git(repo, "init")
    _git(repo, "config", "user.name", "Author Name")
    _git(repo, "config", "user.email", "author@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "add", "--", relative)
    _git(repo, "commit", "-m", "unsigned")


def _signed_commit(repo: Path, *relative_paths: str) -> str:
    import os
    import subprocess

    signer = "CLAIM-KEY"
    key_dir = repo / ".ssh-fixture"
    key_dir.mkdir(parents=True, exist_ok=True)
    key = key_dir / "signing_key"
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-f", str(key), "-N", "", "-C", signer],
        check=True,
        capture_output=True,
    )
    allowed = key_dir / "allowed_signers"
    allowed.write_text(
        f'{signer} namespaces="git" {key.with_suffix(".pub").read_text(encoding="utf-8")}',
        encoding="utf-8",
    )
    if not (repo / ".git").is_dir():
        _git(repo, "init")
    for name, value in {
        "user.name": "Author Name",
        "user.email": "author@example.com",
        "gpg.format": "ssh",
        "user.signingkey": str(key.resolve()),
        "commit.gpgsign": "true",
        "gpg.ssh.allowedSignersFile": str(allowed.resolve()),
    }.items():
        _git(repo, "config", name, value)
    for relative in relative_paths:
        _git(repo, "add", "--", relative)
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Author Name"
    env["GIT_COMMITTER_NAME"] = "Author Name"
    env["GIT_AUTHOR_EMAIL"] = "author@example.com"
    env["GIT_COMMITTER_EMAIL"] = "author@example.com"
    _git(repo, "commit", "-S", "-m", "signed seal", env=env)
    return _git(repo, "rev-parse", "HEAD").strip()


class GitSignatureTest(unittest.TestCase):
    def _verify(self, *args, **kwargs):
        from common.signing import verify_signature

        return verify_signature(*args, **kwargs)

    def test_valid_git_signature_reports_the_signing_key_and_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            payload = {"id": "REQ-1"}
            write_json(repo / "req.json", payload)
            commit = _signed_commit(repo, "req.json")
            result = self._verify(
                version_digest(payload),
                None,
                {},
                repo=repo,
                paths=["req.json"],
            )
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["method"], "git")
        self.assertEqual(result["signer"], "CLAIM-KEY")
        self.assertNotEqual(result["signer"], "Author Name")
        self.assertEqual(result["version"], commit)

    def test_dirty_file_is_not_a_valid_git_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_json(repo / "req.json", {"id": "REQ-1"})
            _signed_commit(repo, "req.json")
            (repo / "req.json").write_text('{"id":"REQ-1","note":"changed"}\n', encoding="utf-8")
            result = self._verify(version_digest({"id": "REQ-1"}), None, {}, repo=repo, paths=["req.json"])
        self.assertNotEqual(result["status"], "valid")
        self.assertEqual(result["method"], "git")
        self.assertIn("differs", result["reason"])

    def test_invalid_object_signature_is_not_replaced_by_git(self):
        private, public = generate_keypair()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            payload = {"id": "REQ-1"}
            digest = version_digest(payload)
            block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
            block["signature"] = "not-a-valid-signature"
            write_json(repo / "req.json", {**payload, "signed": block})
            _signed_commit(repo, "req.json")
            result = self._verify(digest, block, {"Ada": public}, repo=repo, paths=["req.json"])
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["method"], "object")
        self.assertNotEqual(result["signer"], "CLAIM-KEY")

    def test_unsigned_without_object_or_git_signature(self):
        missing = self._verify("abc", None, {}, repo=None, paths=["req.json"])
        self.assertEqual(missing["status"], "unsigned")
        self.assertEqual(missing["method"], "none")
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_json(repo / "req.json", {"id": "REQ-1"})
            _unsigned_commit(repo, "req.json")
            result = self._verify(
                version_digest({"id": "REQ-1"}),
                None,
                {},
                repo=repo,
                paths=["req.json"],
            )
        self.assertEqual(result["status"], "unsigned")
        self.assertEqual(result["method"], "none")

    def test_pack_dotfile_change_is_a_git_content_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pack = repo / "pack"
            pack.mkdir()
            write_json(pack / "pack.json", {"id": "pack", "version": "1"})
            (pack / ".note").write_text("a", encoding="utf-8")
            _signed_commit(repo, "pack/pack.json", "pack/.note")
            digest = complete_pack_digest(pack)
            (pack / ".note").write_text("b", encoding="utf-8")
            result = self._verify(
                digest,
                None,
                {},
                repo=repo,
                paths=["pack/pack.json", "pack/.note"],
                tree_prefix="pack",
            )
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["method"], "git")
        self.assertIn("differs", result["reason"])
