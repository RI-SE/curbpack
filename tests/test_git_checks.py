"""CHK-05 Git Check schemas and git_fresh behavior."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from checks import gitcheck
from checks.run import git_snapshot, run_claim
from checks.schema import load_registry, validate_check_args
from claims.bind import build_claim
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


def _git(repo: Path, *args: str, when: str | None = None) -> str:
    env = os.environ.copy()
    if when is not None:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def _init(repo: Path) -> None:
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "poc2@example.com")
    _git(repo, "config", "user.name", "PoC2")
    _git(repo, "config", "commit.gpgsign", "false")


def _commit(repo: Path, message: str, when: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message, when=when)
    return _git(repo, "rev-parse", "HEAD")


def _two_fresh(repo: Path, first: str, second: str, as_of: str) -> dict:
    return run_claim(
        repo,
        build_claim(
            claim_id="claim-fresh",
            requirement_id="CRA-ANNEX-VII-RISK",
            source="documents",
            args={"path": first},
            checks=[
                {
                    "check": "git_fresh",
                    "args": {"path": first, "max_age_days": 0, "as_of": as_of},
                },
                {
                    "check": "git_fresh",
                    "args": {"path": second, "max_age_days": 0, "as_of": as_of},
                },
            ],
            description="The evidence file changed recently enough.",
            severity="high",
        ),
    )


def _fresh(repo: Path, path: str, max_age_days: int, as_of: str) -> dict:
    result = run_claim(repo, _fresh_claim(path, max_age_days, as_of))
    return result["checks"][0]


def _fresh_claim(path: str, max_age_days: int, as_of: str) -> dict:
    return build_claim(
        claim_id="claim-fresh",
        requirement_id="CRA-ANNEX-VII-RISK",
        source="documents",
        args={"path": path},
        checks=[
            {
                "check": "git_fresh",
                "args": {"path": path, "max_age_days": max_age_days, "as_of": as_of},
            }
        ],
        description="The evidence file changed recently enough.",
        severity="high",
    )


class GitFreshTest(unittest.TestCase):
    def test_a_recent_file_passes_without_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            relative = "docs/risk.md"
            (repo / "docs").mkdir()
            (repo / relative).write_text("risk\n", encoding="utf-8")
            when = "2026-10-23T12:00:00Z"
            _commit(repo, "add risk", when)
            row = _fresh(repo, relative, 0, when)
        self.assertEqual(row["status"], "pass")
        self.assertNotIn("detail", row)

    def test_monday_change_fails_when_friday_head_touched_another_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            relative = "docs/risk.md"
            (repo / "docs").mkdir()
            (repo / relative).write_text("monday\n", encoding="utf-8")
            monday = _commit(repo, "risk on monday", "2026-10-19T12:00:00Z")
            (repo / "README.md").write_text("friday\n", encoding="utf-8")
            friday = _commit(repo, "readme on friday", "2026-10-23T12:00:00Z")
            result = _fresh(repo, relative, 2, "2026-10-23T12:00:00Z")
        self.assertEqual(result["status"], "fail")
        self.assertIn(monday, result["detail"])
        self.assertNotIn(friday, result["detail"])

    def test_age_equal_to_the_maximum_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            relative = "docs/risk.md"
            (repo / "docs").mkdir()
            (repo / relative).write_text("monday\n", encoding="utf-8")
            _commit(repo, "risk", "2026-10-19T12:00:00Z")
            result = _fresh(repo, relative, 2, "2026-10-21T12:00:00Z")
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("detail", result)

    def test_a_future_commit_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            relative = "docs/risk.md"
            (repo / "docs").mkdir()
            (repo / relative).write_text("later\n", encoding="utf-8")
            commit = _commit(repo, "later", "2026-10-23T12:00:00Z")
            result = _fresh(repo, relative, 90, "2026-10-19T12:00:00Z")
        self.assertEqual(result["status"], "fail")
        self.assertIn(commit, result["detail"])

    def test_missing_dirty_and_untracked_paths_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "docs").mkdir()
            missing = _fresh(repo, "docs/risk.md", 2, "2026-10-23T12:00:00Z")
            self.assertEqual(missing["status"], "fail")
            self.assertIn("absent", missing["detail"])
            (repo / "docs" / "risk.md").write_text("tracked\n", encoding="utf-8")
            commit = _commit(repo, "track", "2026-10-23T12:00:00Z")
            (repo / "docs" / "risk.md").write_text("dirty\n", encoding="utf-8")
            dirty = _fresh(repo, "docs/risk.md", 2, "2026-10-23T12:00:00Z")
            self.assertEqual(dirty["status"], "fail")
            self.assertIn("differs", dirty["detail"])
            self.assertIn(commit, dirty["detail"])
            (repo / "docs" / "new.md").write_text("new\n", encoding="utf-8")
            untracked = _fresh(repo, "docs/new.md", 2, "2026-10-23T12:00:00Z")
        self.assertEqual(untracked["status"], "fail")
        self.assertIn("untracked", untracked["detail"])

    def test_a_bracket_path_is_not_a_glob(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "notes1.md").write_text("fresh sibling\n", encoding="utf-8")
            sibling = _commit(repo, "sibling", "2026-10-23T12:00:00Z")
            (repo / "notes[1].md").write_text("untracked\n", encoding="utf-8")
            untracked = _fresh(repo, "notes[1].md", 2, "2026-10-23T12:00:00Z")
            self.assertEqual(untracked["status"], "fail")
            self.assertIn("untracked", untracked["detail"])
            self.assertNotIn(sibling, untracked["detail"])
            (repo / "notes[1].md").write_text("stale\n", encoding="utf-8")
            stale = _commit(repo, "bracket file", "2026-10-01T12:00:00Z")
            (repo / "notes1.md").write_text("still fresh\n", encoding="utf-8")
            fresh_sibling = _commit(repo, "sibling again", "2026-10-23T12:00:00Z")
            result = _fresh(repo, "notes[1].md", 2, "2026-10-23T12:00:00Z")
        self.assertEqual(result["status"], "fail")
        self.assertIn(stale, result["detail"])
        self.assertNotIn(fresh_sibling, result["detail"])

    def test_skip_worktree_and_assume_unchanged_do_not_hide_a_dirty_file(self):
        for flag in ("--skip-worktree", "--assume-unchanged"):
            with self.subTest(flag=flag):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    _init(repo)
                    relative = "docs/risk.md"
                    (repo / "docs").mkdir()
                    (repo / relative).write_text("tracked\n", encoding="utf-8")
                    _commit(repo, "track", "2026-10-23T12:00:00Z")
                    _git(repo, "update-index", flag, relative)
                    (repo / relative).write_text("dirty\n", encoding="utf-8")
                    result = _fresh(repo, relative, 30, "2026-10-23T12:00:00Z")
                self.assertEqual(result["status"], "fail")
                self.assertIn("differs", result["detail"])

    def test_a_rename_does_not_keep_the_old_path_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "old.md").write_text("old\n", encoding="utf-8")
            _commit(repo, "old name", "2026-10-19T12:00:00Z")
            _git(repo, "mv", "old.md", "new.md")
            _commit(repo, "rename", "2026-10-23T12:00:00Z")
            result = _fresh(repo, "new.md", 0, "2026-10-23T12:00:00Z")
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("detail", result)

    def test_a_symlink_with_the_same_bytes_differs_from_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "risk.md").write_text("same\n", encoding="utf-8")
            _commit(repo, "file", "2026-10-23T12:00:00Z")
            (repo / "other.md").write_text("same\n", encoding="utf-8")
            (repo / "risk.md").unlink()
            (repo / "risk.md").symlink_to("other.md")
            result = _fresh(repo, "risk.md", 0, "2026-10-23T12:00:00Z")
        self.assertEqual(result["status"], "fail")
        self.assertIn("differs", result["detail"])

    def test_a_clean_symlink_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "target.md").write_text("body\n", encoding="utf-8")
            _commit(repo, "target", "2026-10-01T12:00:00Z")
            (repo / "link.md").symlink_to("target.md")
            _commit(repo, "link", "2026-10-23T12:00:00Z")
            result = _fresh(repo, "link.md", 0, "2026-10-23T12:00:00Z")
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("detail", result)

    def test_an_inherited_git_dir_stays_on_the_requested_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale = root / "stale"
            newer = root / "newer"
            stale.mkdir()
            newer.mkdir()
            _init(stale)
            _init(newer)
            (stale / "risk.md").write_text("same\n", encoding="utf-8")
            old = _commit(stale, "old", "2026-10-01T12:00:00Z")
            (newer / "risk.md").write_text("same\n", encoding="utf-8")
            fresh = _commit(newer, "new", "2026-10-23T12:00:00Z")
            previous = os.environ.get("GIT_DIR")
            os.environ["GIT_DIR"] = str(newer / ".git")
            try:
                result = _fresh(stale, "risk.md", 0, "2026-10-23T12:00:00Z")
                snapshot = git_snapshot(stale)
            finally:
                if previous is None:
                    os.environ.pop("GIT_DIR", None)
                else:
                    os.environ["GIT_DIR"] = previous
        self.assertEqual(result["status"], "fail")
        self.assertIn(old, result["detail"])
        self.assertNotIn(fresh, result["detail"])
        self.assertEqual(snapshot["commit"], old)

    def test_a_crlf_worktree_matches_the_lf_blob(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            _git(repo, "config", "core.autocrlf", "false")
            (repo / ".gitattributes").write_text("*.md text eol=lf\n", encoding="utf-8")
            (repo / "risk.md").write_bytes(b"line\n")
            _commit(repo, "lf", "2026-10-23T12:00:00Z")
            (repo / "risk.md").write_bytes(b"line\r\n")
            result = _fresh(repo, "risk.md", 0, "2026-10-23T12:00:00Z")
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("detail", result)

    def test_windows_symlink_text_matches_the_blob_git_stores(self):
        original = gitcheck.os.name
        gitcheck.os.name = "nt"
        try:
            self.assertEqual(gitcheck._symlink_target_text(r"C:\repo\ext.txt"), "C:/repo/ext.txt")
            self.assertEqual(
                gitcheck._symlink_target_text("\\\\?\\C:\\repo\\ext.txt"),
                "C:/repo/ext.txt",
            )
            self.assertEqual(
                gitcheck._symlink_target_text(r"..\outside\ext.txt"),
                "../outside/ext.txt",
            )
        finally:
            gitcheck.os.name = original

    def test_a_file_parent_is_not_a_directory_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "notdir").write_text("file\n", encoding="utf-8")
            self.assertTrue(gitcheck._not_a_directory_path(repo, "notdir/child.md"))
            self.assertFalse(gitcheck._not_a_directory_path(repo, "missing.md"))

    def test_a_clean_symlink_passes_for_every_target_kind(self):
        when = "2026-10-23T12:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            outside = root / "outside"
            repo.mkdir()
            outside.mkdir()
            (outside / "ext.txt").write_text("x\n", encoding="utf-8")
            _init(repo)
            cases = {
                "abs.md": outside / "ext.txt",
                "up.md": Path("..") / "outside" / "ext.txt",
                "dang.md": Path("missing-target"),
                "dirlink": Path("subdir"),
            }
            (repo / "subdir").mkdir()
            for name, target in cases.items():
                (repo / name).symlink_to(target)
            _commit(repo, "links", when)
            for name in cases:
                with self.subTest(name=name):
                    result = _fresh(repo, name, 0, when)
                    self.assertEqual(result["status"], "pass")
                    self.assertNotIn("detail", result)

    def test_a_path_that_leaves_the_repo_fails_without_aborting_the_claim(self):
        when = "2026-10-23T12:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            outside = root / "outside"
            repo.mkdir()
            outside.mkdir()
            _init(repo)
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _commit(repo, "risk", when)
            (repo / "out").symlink_to(outside, target_is_directory=True)
            claim = build_claim(
                claim_id="claim-fresh",
                requirement_id="CRA-ANNEX-VII-RISK",
                source="documents",
                args={"path": "out/file.md"},
                checks=[
                    {
                        "check": "git_fresh",
                        "args": {"path": "out/file.md", "max_age_days": 0, "as_of": when},
                    },
                    {
                        "check": "git_fresh",
                        "args": {"path": "risk.md", "max_age_days": 0, "as_of": when},
                    },
                ],
                description="The evidence file changed recently enough.",
                severity="high",
            )
            result = run_claim(repo, claim)
        self.assertEqual(result["checks"][0]["status"], "fail")
        self.assertEqual(result["checks"][1]["status"], "pass")
        self.assertNotIn("detail", result["checks"][1])

    def test_an_executable_bit_fails_only_when_git_tracks_filemode(self):
        when = "2026-10-23T12:00:00Z"
        for tracked in ("true", "false"):
            with self.subTest(filemode=tracked):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    _init(repo)
                    _git(repo, "config", "core.filemode", tracked)
                    (repo / "exec.md").write_text("body\n", encoding="utf-8")
                    _commit(repo, "exec", when)
                    (repo / "exec.md").chmod(0o755)
                    executable = bool((repo / "exec.md").stat().st_mode & 0o111)
                    result = _fresh(repo, "exec.md", 0, when)
                expected = "fail" if tracked == "true" and executable else "pass"
                self.assertEqual(result["status"], expected)
                if expected == "fail":
                    self.assertIn("differs", result["detail"])
                else:
                    self.assertNotIn("detail", result)

    def test_a_symlink_loop_fails_and_the_next_check_still_runs(self):
        when = "2026-10-23T12:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _commit(repo, "risk", when)
            (repo / "loop").symlink_to("loop")
            result = _two_fresh(repo, "loop/child.md", "risk.md", when)
        self.assertEqual(result["checks"][0]["status"], "fail")
        self.assertIn("symlink loop", result["checks"][0]["detail"])
        self.assertEqual(result["checks"][1]["status"], "pass")

    def test_a_path_through_a_file_fails_and_the_next_check_still_runs(self):
        when = "2026-10-23T12:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "notdir").write_text("file\n", encoding="utf-8")
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _commit(repo, "files", when)
            result = _two_fresh(repo, "notdir/child.md", "risk.md", when)
        self.assertEqual(result["checks"][0]["status"], "fail")
        self.assertIn("not a directory path", result["checks"][0]["detail"])
        self.assertEqual(result["checks"][1]["status"], "pass")


def _author(repo: Path, path: str, *, name: str | None = None, email: str | None = None) -> dict:
    args = {"path": path}
    if name is not None:
        args["name"] = name
    if email is not None:
        args["email"] = email
    result = run_claim(
        repo,
        build_claim(
            claim_id="claim-author",
            requirement_id="CRA-ANNEX-VII-RISK",
            source="documents",
            args={"path": path},
            checks=[{"check": "git_author", "args": args}],
            description="The evidence file has the named author.",
            severity="high",
        ),
    )
    return result["checks"][0]


class GitAuthorTest(unittest.TestCase):
    def test_matching_name_and_email_pass_without_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _commit(repo, "risk", "2026-10-23T12:00:00Z")
            row = _author(repo, "risk.md", name="PoC2", email="poc2@example.com")
        self.assertEqual(row["status"], "pass")
        self.assertNotIn("detail", row)

    def test_a_different_author_fails_and_names_the_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            commit = _commit(repo, "risk", "2026-10-19T12:00:00Z")
            (repo / "README.md").write_text("other\n", encoding="utf-8")
            _git(repo, "config", "user.name", "Anna")
            _git(repo, "config", "user.email", "anna@example.com")
            other = _commit(repo, "readme", "2026-10-23T12:00:00Z")
            wrong = _author(repo, "risk.md", name="Anna", email="anna@example.com")
            case = _author(repo, "risk.md", name="poc2")
            email_only = _author(repo, "risk.md", email="poc2@example.com")
        self.assertEqual(wrong["status"], "fail")
        self.assertIn(commit, wrong["detail"])
        self.assertNotIn(other, wrong["detail"])
        self.assertEqual(case["status"], "fail")
        self.assertEqual(email_only["status"], "pass")
        self.assertNotIn("detail", email_only)

    def test_an_unsigned_commit_still_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _commit(repo, "risk", "2026-10-23T12:00:00Z")
            signature = _git(repo, "log", "-1", "--format=%G?")
            row = _author(repo, "risk.md", name="PoC2", email="poc2@example.com")
        self.assertEqual(signature, "N")
        self.assertEqual(row["status"], "pass")
        self.assertNotIn("detail", row)

    def test_a_missing_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            _git(repo, "commit", "--allow-empty", "-m", "empty", when="2026-10-23T12:00:00Z")
            row = _author(repo, "risk.md", name="PoC2")
        self.assertEqual(row["status"], "fail")
        self.assertIn("absent", row["detail"])

    def test_a_non_utf8_author_fails_and_the_next_check_still_runs(self):
        when = "2026-10-23T12:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _git(repo, "add", "risk.md")
            tree = _git(repo, "write-tree")
            raw = (
                f"tree {tree}\n".encode("ascii")
                + b"author \xc5se <ase@example.com> 1792756800 +0000\n"
                + b"committer PoC2 <poc2@example.com> 1792756800 +0000\n"
                + b"\nlatin1 author\n"
            )
            stored = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "-t", "commit", "-w", "--stdin"],
                input=raw,
                capture_output=True,
                check=True,
            )
            _git(repo, "update-ref", "HEAD", stored.stdout.decode().strip())
            result = run_claim(
                repo,
                build_claim(
                    claim_id="claim-author",
                    requirement_id="CRA-ANNEX-VII-RISK",
                    source="documents",
                    args={"path": "risk.md"},
                    checks=[
                        {"check": "git_author", "args": {"path": "risk.md", "name": "PoC2"}},
                        {
                            "check": "git_fresh",
                            "args": {"path": "risk.md", "max_age_days": 0, "as_of": when},
                        },
                    ],
                    description="The evidence file has the named author.",
                    severity="high",
                ),
            )
        self.assertEqual(result["checks"][0]["status"], "fail")
        self.assertIn("not UTF-8", result["checks"][0]["detail"])
        self.assertEqual(result["checks"][1]["status"], "pass")
        self.assertNotIn("detail", result["checks"][1])

    def test_a_utf8_author_passes_when_the_repo_prints_latin1(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            _git(repo, "config", "i18n.logOutputEncoding", "ISO-8859-1")
            _git(repo, "config", "user.name", "Åse")
            _git(repo, "config", "user.email", "ase@example.com")
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _commit(repo, "risk", "2026-10-23T12:00:00Z")
            row = _author(repo, "risk.md", name="Åse", email="ase@example.com")
        self.assertEqual(row["status"], "pass")
        self.assertNotIn("detail", row)

    def test_a_unit_separator_in_the_name_is_not_the_email(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init(repo)
            (repo / "risk.md").write_text("risk\n", encoding="utf-8")
            _git(repo, "add", "risk.md")
            tree = _git(repo, "write-tree")
            raw = (
                f"tree {tree}\n".encode("ascii")
                + b"author PoC2\x1fpoc2@example.com <evil@example.com> 1792756800 +0000\n"
                + b"committer PoC2 <poc2@example.com> 1792756800 +0000\n"
                + b"\nseparator in the name\n"
            )
            stored = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "-t", "commit", "-w", "--stdin"],
                input=raw,
                capture_output=True,
                check=True,
            )
            _git(repo, "update-ref", "HEAD", stored.stdout.decode().strip())
            injected = _author(repo, "risk.md", name="PoC2", email="poc2@example.com")
            recorded = _author(
                repo,
                "risk.md",
                name="PoC2\x1fpoc2@example.com",
                email="evil@example.com",
            )
        self.assertEqual(injected["status"], "fail")
        self.assertIn("evil@example.com", injected["detail"])
        self.assertEqual(recorded["status"], "pass")
        self.assertNotIn("detail", recorded)
