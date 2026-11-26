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
    load_items,
    latest_signed_remedy,
    merge_items,
    open_review_items,
    accept_pending,
    affected,
    failing_checks,
    outside,
    project_run,
    record_dirty_files,
    remember_studio_edit,
    record_rebind,
    rollback_pending,
    settle_regression,
    turned_green,
    write_items,
    is_retired,
    mark_retired,
    record_retire,
    remediation_comment,
    set_remediation_comment,
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
        retired = record_retire(noted, remediation="Remove the check.", name="Ada", date="2026-11-23T09:30:00Z")
        self.assertEqual(retired["remediation_history"][1]["action"], "retire")
        self.assertEqual(retired["remediation_history"][1]["name"], "Ada")
        self.assertNotIn("name", noted["remediation_history"][0])
        blank = append_history(item, remediation="Talk to the owner.", name="  ", date="2026-11-23T09:05:00Z")
        self.assertNotIn("name", blank["remediation_history"][0])
        found = retired_absences([retired], empty)
        self.assertEqual(len(found), 1)

    def test_a_comment_replaces_the_previous_note_and_can_be_cleared(self):
        item = items_from_run(_run("a" * 40, "clean"))[1]
        noted = set_remediation_comment(item, "snopp", date="2026-11-23T09:00:00Z")
        self.assertEqual(noted["comment"], "snopp")
        self.assertNotIn("remediation_history", noted)
        replaced = set_remediation_comment(noted, "Talk to the owner.", date="2026-11-23T09:10:00Z")
        self.assertEqual(replaced["comment"], "Talk to the owner.")
        self.assertNotIn("remediation_history", replaced)
        parked = append_history(item, remediation="snopp", date="2026-11-23T09:00:00Z")
        parked = record_retire(parked, remediation="Remove the check.", date="2026-11-23T09:30:00Z")
        moved = set_remediation_comment(parked, "Talk to the owner.")
        self.assertEqual(moved["comment"], "Talk to the owner.")
        self.assertEqual([entry["action"] for entry in moved["remediation_history"]], ["retire"])
        cleared = set_remediation_comment(moved, "  ")
        self.assertNotIn("comment", cleared)
        self.assertEqual(remediation_comment(cleared), "")

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

    def test_a_later_failure_clears_a_pass(self):
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "pass"
        failed = _run("b" * 40, "clean", status="fail")
        projected = project_run([item], failed, remediation="Check")
        check = next(row for row in projected if row["key"]["check_digest"] == item["key"]["check_digest"])
        self.assertEqual(check["decision"], "must_fix")
        self.assertEqual(check["remediation_history"][-1]["transition"], "pass -> fail")

    def test_a_failing_full_check_keeps_must_fix_and_writes_no_history(self):
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "must_fix"
        failed = _run("b" * 40, "clean", status="fail")
        projected = project_run([item], failed, remediation="Check")
        check = next(row for row in projected if row["key"]["check_digest"] == item["key"]["check_digest"])
        self.assertEqual(check["decision"], "must_fix")
        self.assertNotIn("remediation_history", check)

    def test_a_background_check_records_the_change_and_not_the_run(self):
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        item["decision"] = "must_fix"
        passed = _run("b" * 40, "clean", status="pass")
        projected = project_run([item], passed, remediation="Check")
        check = next(row for row in projected if row["key"]["check_digest"] == item["key"]["check_digest"])
        self.assertEqual(check["decision"], "pass")
        entry = check["remediation_history"][-1]
        self.assertEqual(entry["transition"], "must_fix -> pass")
        self.assertEqual(entry["remediation"], "must_fix -> pass")
        self.assertNotEqual(entry["remediation"], "Check")

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
        self.assertNotIn("remediation_history", kept)


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
        self.assertNotIn("outside", sealed)
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
        noted = sign_remedy_document(
            [item],
            name="Urban",
            private_key=private,
            at="2026-11-23T12:00:00Z",
            notes="Y and P still fail outside this round. A full Check is recommended.",
        )
        self.assertEqual(
            noted["notes"],
            "Y and P still fail outside this round. A full Check is recommended.",
        )
        self.assertTrue(read_signature(noted, {"Urban": public}, what="remedy report")["verifiable"])
        self.assertNotIn("notes", sealed)

    def test_a_later_save_keeps_the_round_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review_items.json"
            write_items(path, [], marker={"notes": "Review decision.", "remedy_notes": "Run a full Check."})
            write_items(path, [], marker={"work_saved": True})
            stored = read_json(path)
        self.assertEqual(stored["notes"], "Review decision.")
        self.assertEqual(stored["remedy_notes"], "Run a full Check.")

    def test_the_newest_seal_locks_the_round_until_that_file_is_revoked(self):
        from app.review_model import _require_open_remediation, _revoke_remedy
        from common.jsonio import write_json
        from studio.review.impl.items import active_remedy_report, remediation_is_sealed

        private, public = generate_keypair()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "run-result_20261125T110000Z"
            folder.mkdir()
            items = folder / "review_items.json"
            write_items(items, [], marker={"review_locked": True, "remedy": True, "remedy_locked": True})
            first = sign_remedy_document([], name="Ada", private_key=private, at="2026-11-25T11:00:00Z")
            second = sign_remedy_document([], name="Ada", private_key=private, at="2026-11-25T11:05:00Z")
            write_json(folder / "remedy-report_20261125T110000Z.json", first)
            write_json(folder / "remedy-report_20261125T110500Z.json", second)
            self.assertTrue(remediation_is_sealed(items))
            self.assertEqual(
                active_remedy_report(folder, read_json(items)).name,
                "remedy-report_20261125T110500Z.json",
            )
            with self.assertRaises(ModelError):
                _require_open_remediation(items)
            _revoke_remedy(
                "alpha",
                str(folder / "run-result.json"),
                items,
                {"name": ["Ada"], "result": [str(folder / "run-result.json")]},
            )
            stored = read_json(items)
            self.assertEqual(stored["remedy_revoked"][0]["report"], "remedy-report_20261125T110500Z.json")
            self.assertEqual(stored["remedy_revoked"][0]["name"], "Ada")
            self.assertNotIn("remedy_locked", stored)
            self.assertFalse(remediation_is_sealed(items))
            self.assertIsNone(active_remedy_report(folder, stored))
            self.assertTrue((folder / "remedy-report_20261125T110500Z.json").is_file())
            self.assertTrue(read_signature(second, {"Ada": public}, what="remedy report")["verifiable"])
            _require_open_remediation(items)
            write_items(items, [], marker={"work_saved": True})
            self.assertEqual(read_json(items)["remedy_revoked"][0]["name"], "Ada")

    def test_an_acknowledged_outside_check_is_inside_the_signed_remedy(self):
        private, public = generate_keypair()
        item = items_from_run(_run("a" * 40, "clean", status="fail"))[1]
        event = {
            "run": "run-result_20261125T070000Z",
            "checks": [{"claim_id": "claim-a", "check": "contents", "digest": "abc"}],
            "choice": "ok",
            "studio": {"claim_id": "claim-a", "check": "exist"},
        }
        sealed = sign_remedy_document(
            [item],
            name="Urban",
            private_key=private,
            at="2026-11-23T12:00:00Z",
            outside=[event],
        )
        reading = read_signature(sealed, {"Urban": public}, what="remedy report")
        self.assertTrue(reading["verifiable"])
        self.assertEqual(sealed["outside"][0]["choice"], "ok")
        self.assertEqual(sealed["outside"][0]["checks"][0]["check"], "contents")
        review_items = sign_items_document([item], name="Urban", private_key=private, at="2026-11-23T12:00:00Z")
        self.assertEqual(review_items[1], version_digest({"items": [item]}))
        self.assertNotIn("outside", review_items[0])


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

    def test_merge_does_not_restore_a_check_a_retarget_replaced(self):
        run = _run("a" * 40, "clean", status="fail")
        old = items_from_run(run)[1]
        moved = retarget_check(
            old,
            "exist",
            {"paths": ["docs/b.md"]},
            remediation="SECURITY.md -> docs/SECURITY.md",
            action="retarget",
            date="2026-11-23T09:30:00Z",
        )
        merged = merge_items([moved], items_from_run(run))
        digests = [item["key"]["check_digest"] for item in merged]
        self.assertIn(moved["key"]["check_digest"], digests)
        self.assertNotIn(old["key"]["check_digest"], digests)


class RegressionTest(unittest.TestCase):
    def _pair(self, exist_status: str, contents_status: str) -> dict:
        return {
            "claims": [
                {
                    "id": "claim-a",
                    "checks": [
                        {
                            "index": 0,
                            "check": "exist",
                            "args": {"paths": ["docs/a.md"]},
                            "status": exist_status,
                        },
                        {
                            "index": 1,
                            "check": "contents",
                            "args": {"path": "docs/b.md"},
                            "status": contents_status,
                        },
                    ],
                }
            ]
        }

    def _items(self) -> tuple[list[dict], str, str]:
        exist = check_digest("exist", {"paths": ["docs/a.md"]})
        contents = check_digest("contents", {"path": "docs/b.md"})
        return [
            {"key": {"claim_id": "claim-a", "check_digest": exist}, "decision": "must_fix"},
            {"key": {"claim_id": "claim-a", "check_digest": contents}, "decision": "pass"},
        ], exist, contents

    def test_the_same_failures_are_inside_and_a_different_pair_is_outside(self):
        items, _exist, _contents = self._items()
        source = self._pair("fail", "fail")
        self.assertEqual(outside(failing_checks(source), failing_checks(source), items), [])
        swapped = self._pair("fail", "pass")
        swapped["claims"][0]["checks"].append(
            {"index": 2, "check": "exist", "args": {"paths": ["docs/c.md"]}, "status": "fail"}
        )
        extra = outside(failing_checks(swapped), failing_checks(source), items)
        self.assertEqual(
            [row["digest"] for row in extra],
            [check_digest("exist", {"paths": ["docs/c.md"]})],
        )

    def test_a_previous_pass_that_fails_is_outside_and_a_fail_that_passes_is_green(self):
        items, exist, contents = self._items()
        source = self._pair("fail", "pass")
        new = self._pair("pass", "fail")
        extra = outside(failing_checks(new), failing_checks(source), items)
        self.assertEqual([row["digest"] for row in extra], [contents])
        self.assertEqual(turned_green([items[0]], new)[0]["key"]["check_digest"], exist)
        self.assertEqual(
            affected([items[1]], failing_checks(self._pair("fail", "fail")))[0]["key"]["check_digest"],
            contents,
        )

    def test_a_retargeted_check_remains_the_original_deviation(self):
        source = self._pair("fail", "pass")
        old = check_digest("exist", {"paths": ["docs/a.md"]})
        moved = retarget_check(
            {"key": {"claim_id": "claim-a", "check_digest": old}, "decision": "must_fix"},
            "exist",
            {"paths": ["docs/b.md"]},
            remediation="docs/a.md -> docs/b.md",
            action="retarget",
        )
        new = self._pair("fail", "pass")
        new["claims"][0]["checks"][0]["args"] = {"paths": ["docs/b.md"]}
        self.assertEqual(outside(failing_checks(new), failing_checks(source), [moved]), [])

    def test_a_remediated_check_that_fails_again_comes_back(self):
        items, exist, _contents = self._items()
        items[0]["decision"] = "pass"
        source = self._pair("fail", "pass")
        again = self._pair("fail", "pass")
        projected = project_run(items, again, remediation="Check", source=source)
        check = next(item for item in projected if item["key"]["check_digest"] == exist)
        self.assertEqual(check["decision"], "must_fix")
        self.assertEqual(check["remediation_history"][-1]["transition"], "pass -> fail")

    def test_ok_updates_the_original_deviation_and_leaves_the_new_failure_out(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "review_items.json"
        items, exist, contents = self._items()
        write_items(path, items, marker={"review_locked": True})
        source = self._pair("fail", "pass")
        new = self._pair("pass", "fail")
        self.assertEqual(
            settle_regression(path, source, new, run_name="run-result_1", run_path=str(path)),
            "outside",
        )
        self.assertEqual([item["decision"] for item in load_items(path)], ["must_fix", "pass"])
        accept_pending(path, source, new)
        updated = {item["key"]["check_digest"]: item for item in load_items(path)}
        self.assertEqual(updated[exist]["decision"], "pass")
        self.assertEqual(updated[exist]["remediation_history"][-1]["transition"], "must_fix -> pass")
        self.assertEqual(updated[contents]["decision"], "pass")
        document = read_json(path)
        self.assertEqual(document["outside"][0]["choice"], "ok")
        self.assertEqual(document["outside"][0]["checks"][0]["digest"], contents)

    def test_rollback_restores_the_claim_and_records_the_event(self):
        from common.jsonio import write_json

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / "repo"
        (repo / "claims").mkdir(parents=True)
        claim_path = repo / "claims" / "claim-a.json"
        original = {"id": "claim-a", "args": {"path": "docs/a.md"}}
        write_json(claim_path, original)
        items, _exist, _contents = self._items()
        items_path = repo / "review_items.json"
        write_items(items_path, items, marker={"review_locked": True})
        remember_studio_edit(
            items_path,
            original,
            "claims/claim-a.json",
            {"claim_id": "claim-a", "check": "exist"},
        )
        write_json(claim_path, {"id": "claim-a", "args": {"path": "docs/c.md"}})
        source = self._pair("fail", "pass")
        new = self._pair("pass", "fail")
        self.assertEqual(
            settle_regression(items_path, source, new, run_name="run-result_1", run_path=str(items_path)),
            "outside",
        )
        rollback_pending(items_path, repo)
        self.assertEqual(read_json(claim_path)["args"]["path"], "docs/a.md")
        self.assertEqual(load_items(items_path)[0]["decision"], "must_fix")
        self.assertEqual(read_json(items_path)["outside"][0]["choice"], "rolled_back")
        self.assertFalse((repo / "docs" / "c.md").exists())

    def test_the_warning_names_the_changed_check_and_the_check_that_failed(self):
        from studio.review.review_page import _outside_panel

        warning = _outside_panel(
            {
                "repo_id": "alpha",
                "selected_result": "/tmp/run.json",
                "outside_can_rollback": True,
                "pending_outside": {
                    "checks": [{"claim_id": "claim-b", "check": "contents", "digest": "x"}],
                    "studio": {"claim_id": "claim-a", "check": "exist"},
                },
            }
        )
        self.assertIn("claim-b", warning)
        self.assertIn("contents", warning)
        self.assertIn("claim-a", warning)
        self.assertIn("exist", warning)
        self.assertIn("Rollback restores only that Studio change", warning)
        self.assertIn('value="rollback"', warning)
        no_studio = _outside_panel(
            {
                "repo_id": "alpha",
                "selected_result": "/tmp/run.json",
                "pending_outside": {"checks": [{"claim_id": "claim-b", "check": "contents"}]},
            }
        )
        self.assertIn("no Studio change to restore", no_studio)
        self.assertNotIn('value="rollback"', no_studio)
        account = _outside_panel(
            {
                "outside": [
                    {
                        "run": "run-result_1",
                        "choice": "ok",
                        "checks": [{"claim_id": "claim-b", "check": "contents"}],
                        "studio": {"claim_id": "claim-a", "check": "exist"},
                    }
                ]
            }
        )
        self.assertIn("data-outside-account", account)
        self.assertIn("Acknowledged", account)

    def test_a_retired_check_is_not_retargeted_or_passed(self):
        exist = check_digest("exist", {"paths": ["docs/a.md"]})
        item = record_retire(
            {"key": {"claim_id": "claim-a", "check_digest": exist}, "decision": "must_fix"},
            remediation="Retired.",
        )
        source = self._pair("fail", "pass")
        new = {
            "claims": [
                {
                    "id": "claim-a",
                    "checks": [
                        {
                            "index": 0,
                            "check": "contents",
                            "args": {"path": "docs/b.md"},
                            "status": "fail",
                        }
                    ],
                }
            ]
        }
        projected = project_run([item], new, remediation="Check", source=source)
        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0]["key"]["check_digest"], exist)
        self.assertEqual(projected[0]["decision"], "must_fix")
        self.assertTrue(is_retired(projected[0]))
        self.assertEqual(
            [entry.get("action") for entry in projected[0]["remediation_history"]],
            ["retire"],
        )
        again = apply_recheck(projected[0], "pass", remediation="Check")
        self.assertEqual(again["decision"], "must_fix")
        self.assertEqual(again["remediation_history"], projected[0]["remediation_history"])

    def test_retiring_the_claim_retires_every_row_and_one_check_does_not(self):
        items, exist, contents = self._items()
        one = mark_retired(items, "claim-a", exist, "Retired.", claim_gone=False)
        self.assertTrue(is_retired(one[0]))
        self.assertFalse(is_retired(one[1]))
        self.assertEqual(one[0]["decision"], "must_fix")
        self.assertEqual(one[1]["decision"], "pass")
        both = mark_retired(items, "claim-a", exist, "Retired.", claim_gone=True)
        self.assertTrue(all(is_retired(item) for item in both))
        self.assertEqual(both[0]["decision"], "must_fix")
        self.assertEqual(both[1]["decision"], "pass")
        self.assertEqual(both[0]["key"]["check_digest"], exist)
        self.assertEqual(both[1]["key"]["check_digest"], contents)

    def test_rebind_history_is_written_next_to_the_run(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / "repo"
        run = repo / "runs" / "run-result_20261125T100000Z"
        run.mkdir(parents=True)
        source = run / "run-result.json"
        source.write_text("{}", encoding="utf-8")
        items_path = run / "review_items.json"
        write_items(items_path, [], marker={"review_locked": True})
        record_rebind(
            repo,
            f"/review?repo=alpha&mode=remediation&result={source}",
            "claim-a",
            signed=True,
            matched=True,
            name="Ada",
        )
        stored = load_items(items_path)
        self.assertEqual(stored[0]["key"]["check_digest"], binding_digest())
        self.assertEqual(stored[0]["decision"], "pass")
        self.assertEqual(stored[0]["remediation_history"][0]["action"], "rebind")
        self.assertEqual(stored[0]["remediation_history"][0]["name"], "Ada")
