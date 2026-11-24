"""review_item provenance, workspaces, decisions, and remediation history."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.signing import generate_keypair, read_signature
from studio.review.impl.items import (
    append_history,
    apply_recheck,
    apply_reused_decision,
    assessments_from_decisions,
    binding_digest,
    carry_history,
    check_digest,
    decision_reusable,
    history_to_show,
    items_from_run,
    latest_signed_remedy,
    merge_items,
    open_review_items,
    project_run,
    record_dirty_files,
    record_retire,
    report_items_path,
    remedy_report_path,
    retired_absences,
    retarget_check,
    sign_items_document,
    sign_remedy_document,
    signed_decision,
    summarize_remedy,
    summarize_review,
    take_in_remedy,
    workspace_items_path,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _repo_with_file(text: str) -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name)
    _git(repo, "init")
    _git(repo, "config", "user.email", "dev@example.com")
    _git(repo, "config", "user.name", "Dev")
    (repo / "docs").mkdir()
    (repo / "docs" / "a.md").write_text(text, encoding="utf-8")
    _git(repo, "add", "docs/a.md")
    _git(repo, "commit", "-m", "first")
    return tmp, repo


def _run(commit: str, worktree: str, *, status: str = "pass", binding: str = "match") -> dict:
    return {
        "commit": commit,
        "worktree": worktree,
        "claims": [
            {
                "id": "claim-a",
                "digest": "claim-digest",
                "requirement_digest": "req-digest",
                "binding": binding,
                "status": status,
                "checks": [
                    {
                        "index": 0,
                        "check": "exist",
                        "args": {"paths": ["docs/a.md"]},
                        "status": status,
                    }
                ],
            }
        ],
    }


class FilesSidecarTest(unittest.TestCase):
    def test_a_dirty_studio_check_records_size_and_mtime_once(self):
        tmp, repo = _repo_with_file("hello\n")
        self.addCleanup(tmp.cleanup)
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        run = _run(commit, "dirty")
        run_path = repo / "runs" / "run-result_20261123T080000Z.json"
        first = record_dirty_files(repo, run_path, run)
        self.assertIsNotNone(first)
        assert first is not None
        self.assertEqual(first.name, "run-result_20261123T080000Z.files.json")
        self.assertNotIn("size", run)
        recorded = read_json(first)
        stored = recorded["checks"][0]["files"][0]
        self.assertEqual(stored["path"], "docs/a.md")
        self.assertEqual(stored["size"], (repo / "docs" / "a.md").stat().st_size)
        (repo / "docs" / "a.md").write_text("hello hello\n", encoding="utf-8")
        record_dirty_files(repo, run_path, run)
        again = read_json(first)
        self.assertEqual(again["checks"][0]["files"][0]["size"], stored["size"])


class ReuseTest(unittest.TestCase):
    def test_clean_commits_reuse_only_the_check_whose_file_is_unchanged(self):
        tmp, repo = _repo_with_file("same\n")
        self.addCleanup(tmp.cleanup)
        first = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        (repo / "docs" / "other.md").write_text("else\n", encoding="utf-8")
        _git(repo, "add", "docs/other.md")
        _git(repo, "commit", "-m", "other")
        second = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        previous = items_from_run(_run(first, "clean"))[1]
        previous["decision"] = "must_fix"
        previous["comment"] = "Add the file."
        current = items_from_run(_run(second, "clean"))[1]
        self.assertTrue(
            decision_reusable(previous, current, repo=repo, paths=["docs/a.md"])
        )
        filled = apply_reused_decision(current, previous)
        self.assertEqual(filled["decision"], "must_fix")
        self.assertNotIn("remediation_history", filled)
        (repo / "docs" / "a.md").write_text("changed\n", encoding="utf-8")
        _git(repo, "add", "docs/a.md")
        _git(repo, "commit", "-m", "edit")
        third = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        edited = items_from_run(_run(third, "clean"))[1]
        self.assertFalse(
            decision_reusable(previous, edited, repo=repo, paths=["docs/a.md"])
        )

    def test_a_missing_dirty_sidecar_keeps_the_decision_and_requires_a_new_one(self):
        previous = items_from_run(_run("a" * 40, "dirty"))[1]
        previous["decision"] = "accepted"
        previous["comment"] = "Known gap."
        previous["remediation_history"] = [{"date": "2026-11-23T09:00:00Z", "remediation": "Noted."}]
        current = items_from_run(_run("b" * 40, "clean"))[1]
        self.assertFalse(decision_reusable(previous, current, repo=Path("."), paths=["docs/a.md"]))
        self.assertEqual(previous["decision"], "accepted")
        self.assertEqual(previous["remediation_history"][0]["remediation"], "Noted.")


class WorkspaceTest(unittest.TestCase):
    def test_continue_merges_and_start_over_keeps_only_the_new_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _run("a" * 40, "clean")
            path = workspace_items_path(repo / ".curbpack" / "tmp", "run-result_20261123T080000Z.json")
            items, state = open_review_items(path, run)
            self.assertEqual(state, "ready")
            self.assertEqual(items[1]["decision"], "pass")
            self.assertNotIn("remediation_history", items[1])
            kept = items[1]
            kept["decision"] = "must_fix"
            kept["comment"] = "Not enough."
            from common.jsonio import write_json

            write_json(path, {"items": [kept]})
            asked, state = open_review_items(path, run)
            self.assertEqual(state, "ask")
            self.assertEqual(asked[0]["decision"], "must_fix")
            continued, state = open_review_items(path, run, choice="continue")
            self.assertEqual(state, "continued")
            kept_again = next(item for item in continued if item["key"]["check_digest"] == kept["key"]["check_digest"])
            self.assertEqual(kept_again["decision"], "must_fix")
            binding = [item for item in continued if item["key"]["check_digest"] == binding_digest()]
            self.assertEqual(len(binding), 1)
            restarted, state = open_review_items(path, run, choice="start")
            self.assertEqual(state, "restarted")
            self.assertTrue(all(item["decision"] in {"pass", "not_assessed"} for item in restarted))
            self.assertTrue(all("remediation_history" not in item for item in restarted))

    def test_two_runs_do_not_share_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = workspace_items_path(root, "run-result_20261123T080000Z.json")
            second = workspace_items_path(root, "run-result_20261123T090000Z.json")
            report = workspace_items_path(root, "review-report_20261123T100000Z.json")
            self.assertNotEqual(first, second)
            self.assertNotEqual(second, report)
            self.assertTrue(str(first).endswith("run-result_20261123T080000Z/review_items.json"))


class DecisionAndHistoryTest(unittest.TestCase):
    def test_must_fix_on_a_passing_check_becomes_an_assessment_and_accept_does_not(self):
        run = _run("a" * 40, "clean")
        item = items_from_run(run)[1]
        item["decision"] = "must_fix"
        item["comment"] = "The check is too weak."
        assessments = assessments_from_decisions([item], run)
        self.assertEqual(assessments[0]["disposition"], "must_fix")
        self.assertEqual(assessments[0]["text"], "The check is too weak.")
        self.assertEqual(run["claims"][0]["checks"][0]["status"], "pass")
        accepted = dict(item)
        accepted["decision"] = "pass"
        self.assertEqual(assessments_from_decisions([accepted], run), [])

    def test_a_stale_binding_decision_becomes_a_binding_assessment(self):
        from studio.compile.impl.report import _validate_assessments

        run = _run("a" * 40, "clean", status="fail", binding="stale")
        claim = run["claims"][0]
        claim["namespace"] = "RISE/house"
        claim["pack_id"] = "house"
        claim["requirement_id"] = "REQ-A"
        item = items_from_run(run)[0]
        item["decision"] = "must_fix"
        item["comment"] = "The requirement moved."
        found = assessments_from_decisions([item], run)
        self.assertEqual(
            found,
            [
                {
                    "kind": "binding",
                    "claim_id": "claim-a",
                    "claim_digest": "claim-digest",
                    "namespace": "RISE/house",
                    "pack_id": "house",
                    "requirement_id": "REQ-A",
                    "requirement_digest": "req-digest",
                    "binding": "stale",
                    "disposition": "must_fix",
                    "text": "The requirement moved.",
                }
            ],
        )
        _validate_assessments(found, run)

    def test_a_comment_is_not_retire_and_a_retire_action_is(self):
        run = _run("a" * 40, "clean")
        item = items_from_run(run)[1]
        noted = append_history(item, remediation="Talk to the owner.", date="2026-11-23T09:00:00Z")
        self.assertNotIn("action", noted["remediation_history"][0])
        empty = {"claims": []}
        self.assertEqual(retired_absences([noted], empty), [])
        retired = record_retire(noted, remediation="Remove the check.", date="2026-11-23T09:30:00Z")
        self.assertEqual(retired["remediation_history"][1]["action"], "retire")
        found = retired_absences([retired], empty)
        self.assertEqual(len(found), 1)

    def test_recheck_pass_updates_the_recommendation_and_keeps_the_item(self):
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "must_fix"
        digest = item["key"]["check_digest"]
        changed = retarget_check(
            item,
            "exist",
            {"paths": ["docs/b.md"]},
            remediation="Point the check at the right file.",
            transition="must_fix -> pass",
            date="2026-11-23T09:30:00Z",
        )
        self.assertEqual(changed["remediation_history"][0]["old_check_digest"], digest)
        self.assertNotEqual(changed["key"]["check_digest"], digest)
        checked = apply_recheck(changed, "pass", remediation="Re-check passed.", date="2026-11-23T09:40:00Z")
        self.assertEqual(checked["decision"], "pass")
        self.assertEqual(checked["key"]["claim_id"], "claim-a")

    def test_the_next_review_shows_history_without_copying_it_into_the_decision(self):
        previous = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        previous = append_history(previous, remediation="Documented the gap.", date="2026-11-23T09:00:00Z")
        current = items_from_run(_run("b" * 40, "clean"))[1]
        self.assertEqual(current["decision"], "pass")
        shown = history_to_show([previous], current)
        self.assertEqual(shown[0]["remediation"], "Documented the gap.")
        self.assertEqual(current["decision"], "pass")
        reused = apply_reused_decision(current, {**previous, "decision": "must_fix", "comment": "Still open."})
        self.assertEqual(reused["decision"], "must_fix")
        self.assertNotIn("remediation_history", reused)

    def test_signed_items_are_what_reporting_reads(self):
        private, public = generate_keypair()
        item = items_from_run(_run("a" * 40, "clean"))[1]
        item["decision"] = "must_fix"
        item["comment"] = "Insufficient."
        sealed, digest = sign_items_document([item], name="Ada Reviewer", private_key=private, at="2026-11-23T10:00:00Z")
        self.assertEqual(digest, version_digest({"items": [item]}))
        reading = read_signature(sealed, {"Ada Reviewer": public}, what="review items")
        self.assertTrue(reading["verifiable"])
        self.assertEqual(
            signed_decision(sealed, "claim-a", check_digest("exist", {"paths": ["docs/a.md"]})),
            "must_fix",
        )
        later = dict(item)
        later["decision"] = "pass"
        self.assertEqual(
            signed_decision({"items": [later]}, "claim-a", item["key"]["check_digest"]),
            None,
        )
        self.assertTrue(str(report_items_path(Path("review-report_20261123T100000Z.json"))).endswith(
            "review-report_20261123T100000Z.items.json"
        ))


class ProjectRunTest(unittest.TestCase):
    def test_a_full_check_records_must_fix_to_pass_on_the_remediation_copy(self):
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "must_fix"
        passed = _run("b" * 40, "clean", status="pass")
        projected = project_run([item], passed, remediation="Checked again.")
        check = next(row for row in projected if row["key"]["check_digest"] == item["key"]["check_digest"])
        self.assertEqual(check["decision"], "pass")
        self.assertEqual(check["remediation_history"][-1]["transition"], "must_fix -> pass")

    def test_a_failing_full_check_keeps_must_fix_and_appends_history(self):
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "must_fix"
        failed = _run("b" * 40, "clean", status="fail")
        projected = project_run([item], failed, remediation="Still missing.")
        check = next(row for row in projected if row["key"]["check_digest"] == item["key"]["check_digest"])
        self.assertEqual(check["decision"], "must_fix")
        self.assertNotIn("transition", check["remediation_history"][-1])
        self.assertEqual(check["remediation_history"][-1]["remediation"], "Still missing.")

    def test_a_changed_check_is_found_through_old_check_digest(self):
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "must_fix"
        old = item["key"]["check_digest"]
        run = _run("b" * 40, "clean", status="pass")
        run["claims"][0]["checks"][0]["args"] = {"paths": ["docs/b.md"]}
        projected = project_run([item], run, remediation="The date was wrong.")
        check = next(row for row in projected if row["key"]["claim_id"] == "claim-a" and row["key"]["check_digest"] != old)
        self.assertEqual(check["decision"], "pass")
        self.assertEqual(check["remediation_history"][0]["old_check_digest"], old)
        self.assertEqual(check["remediation_history"][-1]["transition"], "must_fix -> pass")
        binding = items_from_run(_run("a" * 40, "clean", status="fail"))[0]
        both = project_run([binding, item], run, remediation="The date was wrong.")
        self.assertEqual(both[0]["key"]["check_digest"], binding_digest())
        self.assertNotIn("remediation_history", both[0])

    def test_a_binding_that_becomes_a_match_records_must_fix_to_pass(self):
        stale = _run("a" * 40, "clean", status="fail", binding="stale")
        binding = items_from_run(stale)[0]
        binding["decision"] = "must_fix"
        check = items_from_run(stale)[1]
        check["decision"] = "must_fix"
        passed = _run("b" * 40, "clean", status="pass", binding="match")
        projected = project_run([binding, check], passed, remediation="Rebound.")
        self.assertEqual(projected[0]["key"]["check_digest"], binding_digest())
        self.assertEqual(projected[0]["decision"], "pass")
        self.assertEqual(projected[0]["remediation_history"][-1]["transition"], "must_fix -> pass")
        self.assertEqual(projected[1]["decision"], "pass")
        self.assertEqual(projected[1]["remediation_history"][-1]["transition"], "must_fix -> pass")

    def test_a_binding_that_stays_stale_keeps_must_fix(self):
        binding = items_from_run(_run("a" * 40, "clean", status="fail", binding="stale"))[0]
        binding["decision"] = "must_fix"
        again = _run("b" * 40, "clean", status="fail", binding="stale")
        projected = project_run([binding], again, remediation="Still stale.")
        kept = next(row for row in projected if row["key"]["check_digest"] == binding_digest())
        self.assertEqual(kept["decision"], "must_fix")
        self.assertNotIn("transition", kept["remediation_history"][-1])
        self.assertEqual(kept["remediation_history"][-1]["remediation"], "Still stale.")


class TakeInRemedyTest(unittest.TestCase):
    def test_unchanged_underlag_reuses_the_signed_decision(self):
        tmp, repo = _repo_with_file("same\n")
        self.addCleanup(tmp.cleanup)
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        signed = items_from_run(_run(commit, "clean", status="fail"))[1]
        signed["decision"] = "accepted"
        signed["comment"] = "Lisa will finish the document."
        signed["priority"] = 2
        signed["assessed_at"] = "2026-11-23T10:00:00Z"
        remedy = append_history(dict(signed), remediation="Waiting for Lisa.", date="2026-11-23T11:00:00Z")
        fresh = items_from_run(_run(commit, "clean", status="fail"))
        taken = take_in_remedy(repo, _run(commit, "clean", status="fail"), fresh, [remedy], [signed])
        check = next(row for row in taken if row["key"]["check_digest"] == signed["key"]["check_digest"])
        self.assertEqual(check["decision"], "accepted")
        self.assertEqual(check["remediation_history"][0]["remediation"], "Waiting for Lisa.")

    def test_changed_underlag_suggests_pass_and_records_the_transition(self):
        tmp, repo = _repo_with_file("missing\n")
        self.addCleanup(tmp.cleanup)
        first = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        signed = items_from_run(_run(first, "clean", status="fail"))[1]
        signed["decision"] = "accepted"
        signed["comment"] = "Lisa will finish the document."
        signed["priority"] = 2
        signed["assessed_at"] = "2026-11-23T10:00:00Z"
        remedy = append_history(dict(signed), remediation="Waiting for Lisa.", date="2026-11-23T11:00:00Z")
        (repo / "docs" / "a.md").write_text("done\n", encoding="utf-8")
        _git(repo, "add", "docs/a.md")
        _git(repo, "commit", "-m", "lisa")
        second = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        later = _run(second, "clean", status="pass")
        fresh = items_from_run(later)
        taken = take_in_remedy(repo, later, fresh, [remedy], [signed])
        check = next(row for row in taken if row["key"]["check_digest"] == signed["key"]["check_digest"])
        self.assertEqual(check["decision"], "pass")
        self.assertEqual(check["remediation_history"][-1]["transition"], "accepted -> pass")
        self.assertEqual(check["remediation_history"][0]["remediation"], "Waiting for Lisa.")

    def test_keeping_new_decisions_stores_the_history_on_the_items(self):
        source = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        source["decision"] = "accepted"
        source = append_history(source, remediation="The document was missing.", date="2026-11-23T09:00:00Z")
        fresh = items_from_run(_run("b" * 40, "clean"))[1]
        carried = carry_history([fresh], [source])
        self.assertEqual(carried[0]["decision"], "pass")
        self.assertEqual(carried[0]["remediation_history"][0]["remediation"], "The document was missing.")


class DirtyProvenanceTest(unittest.TestCase):
    def test_opening_a_review_copies_the_dirty_sidecar_into_provenance(self):
        tmp, repo = _repo_with_file("hello\n")
        self.addCleanup(tmp.cleanup)
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        run = _run(commit, "dirty")
        run_path = repo / "runs" / "run-result_20261123T080000Z.json"
        record_dirty_files(repo, run_path, run)
        items, state = open_review_items(
            repo / "workspace" / "review_items.json",
            run,
            repo=repo,
            run_name=run_path.name,
        )
        self.assertEqual(state, "ready")
        files = items[1]["provenance"]["files"]
        self.assertEqual(files[0]["path"], "docs/a.md")
        self.assertEqual(files[0]["size"], (repo / "docs" / "a.md").stat().st_size)

    def test_a_projected_new_check_copies_the_dirty_sidecar(self):
        tmp, repo = _repo_with_file("hello\n")
        self.addCleanup(tmp.cleanup)
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        run = _run(commit, "dirty")
        run_path = repo / "runs" / "run-result_20261123T080000Z.json"
        record_dirty_files(repo, run_path, run)
        binding = items_from_run(_run(commit, "dirty"))[0]
        projected = project_run([binding], run, remediation="Check", repo=repo, run_name=run_path.name)
        check = next(row for row in projected if row["key"]["check_digest"] != binding_digest())
        self.assertEqual(check["provenance"]["files"][0]["path"], "docs/a.md")
        self.assertIn("size", check["provenance"]["files"][0])


class DecisionBaselineTest(unittest.TestCase):
    def test_the_newest_signed_review_is_the_decision_baseline(self):
        from common.jsonio import write_json
        from common.signing import generate_keypair
        from review.compile import sign_report, write_report
        from tests.test_rev03_review import _report

        private, _public = generate_keypair()
        older = sign_report(
            _report("claim-old", "First reading."),
            name="Niklas",
            private_key=private,
            at="2026-01-01T00:00:00Z",
        )
        item = {
            "key": {"claim_id": "claim-old", "check_digest": "aa"},
            "decision": "must_fix",
            "remediation_history": [
                {"date": "2026-11-23T09:00:00Z", "remediation": "Filled the gap."}
            ],
        }
        accepted = {**item, "decision": "accepted", "comment": "Prepared.", "remediation_history": []}
        sealed_items, digest = sign_items_document(
            [accepted], name="Niklas", private_key=private, at="2026-01-02T00:00:00Z"
        )
        newer_body = _report("claim-new", "Lisa is covered.")
        newer_body["items_digest"] = digest
        newer = sign_report(
            newer_body,
            name="Niklas",
            private_key=private,
            at="2026-01-02T00:00:00Z",
        )
        current = _report("claim-now", "This run.")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_report(folder / "review-report_20260101T000000Z.json", older)
            write_report(folder / "review-report_20260102T000000Z.json", newer)
            write_json(
                folder / "review-report_20260101T000000Z.remedy.json",
                {"items": [item], "remedy": True, "signed": {"name": "Urban", "at": "2026-01-01T01:00:00Z", "signature": "seal"}},
            )
            write_json(folder / "review-report_20260101T000000Z.items.json", {"items": [item]})
            write_json(folder / "review-report_20260102T000000Z.items.json", sealed_items)
            found = latest_signed_remedy(folder, current["run_result"])
        self.assertIsNotNone(found)
        stem, remedy_items, signed_items = found
        self.assertEqual(stem, "review-report_20260101T000000Z")
        self.assertEqual(remedy_items[0]["remediation_history"][0]["remediation"], "Filled the gap.")
        self.assertEqual(signed_items[0]["decision"], "accepted")

    def test_edited_items_do_not_become_the_baseline(self):
        from common.jsonio import write_json
        from common.signing import generate_keypair
        from review.compile import sign_report, write_report
        from tests.test_rev03_review import _report

        private, _public = generate_keypair()
        item = {
            "key": {"claim_id": "claim-old", "check_digest": "aa"},
            "decision": "accepted",
            "comment": "Prepared.",
        }
        sealed_items, digest = sign_items_document(
            [item], name="Niklas", private_key=private, at="2026-01-02T00:00:00Z"
        )
        body = _report("claim-new", "Lisa is covered.")
        body["items_digest"] = digest
        signed = sign_report(body, name="Niklas", private_key=private, at="2026-01-02T00:00:00Z")
        current = _report("claim-now", "This run.")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_report(folder / "review-report_20260102T000000Z.json", signed)
            sealed_items["items"][0]["decision"] = "pass"
            write_json(folder / "review-report_20260102T000000Z.items.json", sealed_items)
            write_json(
                folder / "review-report_20260102T000000Z.remedy.json",
                {
                    "items": [{**item, "decision": "must_fix"}],
                    "remedy": True,
                    "signed": {"name": "Urban", "at": "2026-01-02T01:00:00Z", "signature": "seal"},
                },
            )
            found = latest_signed_remedy(folder, current["run_result"])
        self.assertIsNotNone(found)
        _stem, _remedy_items, signed_items = found
        self.assertEqual(signed_items[0]["decision"], "must_fix")


class KeepHistoryTest(unittest.TestCase):
    def test_keep_writes_the_history_into_the_new_review_items(self):
        import copy

        from app.server import Workspace
        from common.jsonio import write_json
        from common.signing import generate_keypair
        from review.compile import sign_report, write_report
        from studio.review.impl.items import studio_temp_dir
        from studio.review.model import _review_view
        from tests.test_rev03_review import _config, _report, _workspace

        private, _public = generate_keypair()
        older = sign_report(
            _report("flow-note", "First reading."),
            name="Niklas",
            private_key=private,
            at="2026-01-01T00:00:00Z",
        )
        new_run = copy.deepcopy(older["run_result"])
        new_run["commit"] = "b" * 40
        new_run["worktree"] = "clean"
        fresh = items_from_run(new_run)
        check = next(item for item in fresh if item["key"]["check_digest"] != binding_digest())
        remembered = append_history(
            {**check, "decision": "must_fix"},
            remediation="The document was missing.",
            date="2026-11-23T09:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _config(repo)
            reports = repo / "signed" / "reports"
            reports.mkdir(parents=True)
            write_report(reports / "review-report_20260101T000000Z.json", older)
            write_json(
                reports / "review-report_20260101T000000Z.remedy.json",
                {
                    "items": [remembered],
                    "remedy": True,
                    "signed": {"name": "Urban", "at": "2026-01-01T01:00:00Z", "signature": "seal"},
                },
            )
            write_json(reports / "review-report_20260101T000000Z.items.json", {"items": [remembered]})
            runs = repo / "runs" / "out"
            runs.mkdir(parents=True)
            run_path = runs / "run-result_20260102T000000Z.json"
            write_json(run_path, new_run)
            _review_view(
                Workspace(workspace),
                {
                    "repo": ["alpha"],
                    "result": [str(run_path)],
                    "remedy": ["review-report_20260101T000000Z"],
                },
            )
            stored = read_json(workspace_items_path(studio_temp_dir(repo), run_path.name))
            kept = next(
                row for row in stored["items"] if row["key"]["check_digest"] == check["key"]["check_digest"]
            )
            self.assertEqual(kept["decision"], "pass")
            self.assertEqual(kept["remediation_history"][0]["remediation"], "The document was missing.")


class RemedySignatureTest(unittest.TestCase):
    def test_a_remedy_report_uses_the_same_seal(self):
        private, public = generate_keypair()
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "must_fix"
        item = append_history(item, remediation="Documented the gap.", date="2026-11-23T09:00:00Z")
        sealed = sign_remedy_document([item], name="Urban", private_key=private, at="2026-11-23T12:00:00Z")
        reading = read_signature(sealed, {"Urban": public}, what="remedy report")
        self.assertTrue(reading["verifiable"])
        self.assertEqual(reading["what"], "remedy report")
        self.assertEqual(reading["who"], "Urban")
        self.assertEqual(sealed["items"][0]["decision"], "must_fix")
        self.assertTrue(str(remedy_report_path(Path("review-report_20261123T100000Z.json"))).endswith(
            "review-report_20261123T100000Z.remedy.json"
        ))
        self.assertEqual(summarize_review([item, {**item, "decision": "pass", "key": {"claim_id": "b", "check_digest": "x"}}]), "1 Passed · 1 Must fix · Signed")
        self.assertEqual(summarize_review([{**item, "decision": "pass"}]), "All Passed · Signed")
        self.assertEqual(summarize_remedy([item]), "1 action · Signed")


class MergeTest(unittest.TestCase):
    def test_merge_keeps_the_existing_item_and_adds_a_new_check(self):
        run = _run("a" * 40, "clean")
        existing = items_from_run(run)
        existing[1]["decision"] = "must_fix"
        new_run = _run("a" * 40, "clean")
        new_run["claims"][0]["checks"].append(
            {"index": 1, "check": "exist", "args": {"paths": ["docs/b.md"]}, "status": "fail"}
        )
        merged = merge_items(existing, items_from_run(new_run))
        by_digest = {item["key"]["check_digest"]: item for item in merged}
        self.assertEqual(by_digest[existing[1]["key"]["check_digest"]]["decision"], "must_fix")
        self.assertIn(check_digest("exist", {"paths": ["docs/b.md"]}), by_digest)
