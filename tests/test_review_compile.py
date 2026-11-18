"""Compile writes one report for the run that happened. It does not store a verdict."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.run import build_run_result
from claims.bind import build_claim
from common.canonical import version_digest
from common.errors import ModelError
from common.signing import generate_keypair, read_signature
from studio.review.review_page import review_page
from review.compile import (
    compile_report,
    durable_report_path,
    load_report,
    read_report_signature,
    record_decision,
    replace_saved_report,
    same_run,
    save_report_decision,
    save_report_signature,
    sign_report,
    unchecked_requirement_ids,
    validate_report,
    worktree_sentence,
    write_report,
)


class CompileReportTest(unittest.TestCase):
    def test_compile_embeds_the_run_and_omits_stored_sentences(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs").mkdir()
            (repo / "docs" / "a.md").write_text("alpha\n", encoding="utf-8")
            (repo / "docs" / "b.md").write_text("beta\n", encoding="utf-8")
            first = _claim("claim-a", "docs/a.md")
            second = _claim("claim-b", "docs/b.md")
            run = build_run_result(repo, [first, second], _packs())
            report = compile_report(
                run_result=run,
                requirements=[_requirement("REQ-A"), _requirement("REQ-UNUSED")],
                claims=[second, first],
            )
            self.assertEqual([item["id"] for item in report["claims"]], ["claim-a", "claim-b"])
            self.assertEqual([item["id"] for item in report["requirements"]], ["REQ-A"])
            self.assertEqual(report["requirements"][0]["references"][0]["law_text"], "The product documents the risk.")
            self.assertEqual(report["run_result"], run)
            for key in ("decision", "signed", "git_note", "limits", "packs", "compliant", "meets_cra"):
                self.assertNotIn(key, report)
            self.assertTrue(report["run_result"]["packs"])
            self.assertEqual(report["appendix"][0]["id"], "claim-a")
            self.assertNotIn("appendix", report["run_result"])

    def test_missing_or_changed_claim_does_not_write(self):
        claim = _claim("claim-a", "docs/a.md")
        run = _run(claim)
        report = compile_report(
            run_result=run,
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = durable_report_path(Path(tmp))
            write_report(path, report)
            before = path.read_bytes()
            changed = dict(run)
            changed["claims"] = [dict(run["claims"][0], digest="not-this-claim")]
            with self.assertRaises(ModelError):
                compile_report(
                    run_result=changed,
                    requirements=[_requirement("REQ-A")],
                    claims=[claim],
                )
            with self.assertRaises(ModelError):
                compile_report(
                    run_result=run,
                    requirements=[_requirement("REQ-A")],
                    claims=[],
                )
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(load_report(path)["claims"][0]["id"], "claim-a")

    def test_validate_rejects_a_compliance_flag(self):
        claim = _claim("claim-a", "docs/a.md")
        report = compile_report(
            run_result=_run(claim),
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        flagged = dict(report)
        flagged["compliant"] = True
        with self.assertRaises(ModelError):
            validate_report(flagged)
        flagged = dict(report)
        flagged["meets_cra"] = True
        with self.assertRaises(ModelError):
            validate_report(flagged)

    def test_decision_and_sign_stay_separate_from_the_requirement_seal(self):
        private, public = generate_keypair()
        claim = _claim("claim-a", "docs/a.md")
        report = compile_report(
            run_result=_run(claim),
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        with self.assertRaises(ModelError):
            record_decision(report, "  ")
        decided = record_decision(report, "  Currency of the assessment is a different Requirement.  ")
        self.assertEqual(
            decided["decision"],
            "Currency of the assessment is a different Requirement.",
        )
        self.assertNotIn("signed", decided)
        self.assertEqual(decided["requirements"][0]["references"][0]["law_text"], report["requirements"][0]["references"][0]["law_text"])
        with self.assertRaises(ModelError):
            sign_report(report, name="Ada Reviewer", private_key=private, at="2026-10-21T12:00:00Z")
        sealed = sign_report(decided, name="Ada Reviewer", private_key=private, at="2026-10-21T12:00:00Z")
        reading = read_report_signature(sealed, {"Ada Reviewer": public})
        requirement_reading = read_signature(sealed["requirements"][0], {"Ada Reviewer": public}, what="requirement")
        self.assertTrue(reading["verifiable"])
        self.assertEqual(reading["what"], "review report")
        self.assertEqual(reading["who"], "Ada Reviewer")
        self.assertFalse(requirement_reading["verifiable"])
        self.assertNotEqual(reading["version"], requirement_reading["version"])

    def test_dirty_run_keeps_worktree_on_the_result(self):
        claim = _claim("claim-a", "docs/a.md")
        run = _run(claim, worktree="dirty")
        report = compile_report(
            run_result=run,
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        self.assertEqual(report["run_result"]["worktree"], "dirty")
        self.assertNotIn("git_note", report)
        self.assertIn("not verification of that commit's content", worktree_sentence(report["run_result"]))
        self.assertEqual(worktree_sentence({"worktree": "clean"}), "The worktree was clean.")

    def test_same_run_and_confirmed_replace_do_not_copy_the_decision(self):
        claim = _claim("claim-a", "docs/a.md")
        run = _run(claim)
        report = compile_report(
            run_result=run,
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        self.assertTrue(same_run(report, run))
        later = _run(claim, digest_suffix="")
        later["tool_version"] = "other"
        self.assertFalse(same_run(report, later))
        with tempfile.TemporaryDirectory() as tmp:
            path = durable_report_path(Path(tmp))
            self.assertFalse(path.exists())
            with self.assertRaises(ModelError):
                save_report_decision(path, "I read the first run.")
            write_report(path, record_decision(report, "I read the first run."))
            before = path.read_bytes()
            with self.assertRaises(ModelError):
                replace_saved_report(path, report, confirm=False)
            self.assertEqual(path.read_bytes(), before)
            replace_saved_report(path, report, confirm=True)
            loaded = load_report(path)
            self.assertNotIn("decision", loaded)
            self.assertNotIn("signed", loaded)
            self.assertTrue(same_run(loaded, run))
            self.assertFalse((Path(tmp) / ".curbpack" / "review-report.json").exists())

    def test_unchecked_requirements_are_the_selected_ids_with_no_row(self):
        claim = _claim("claim-a", "docs/a.md")
        report = compile_report(
            run_result=_run(claim),
            requirements=[_requirement("REQ-A"), _requirement("REQ-B")],
            claims=[claim],
        )
        self.assertEqual(
            unchecked_requirement_ids(["REQ-A", "REQ-B", "REQ-C"], report),
            ["REQ-B", "REQ-C"],
        )

    def test_signing_requires_the_saved_file_and_does_not_write_on_failure(self):
        private, public = generate_keypair()
        claim = _claim("claim-a", "docs/a.md")
        report = compile_report(
            run_result=_run(claim),
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = durable_report_path(Path(tmp))
            write_report(path, report)
            before = path.read_bytes()
            with self.assertRaises(ModelError):
                save_report_signature(path, name="Ada Reviewer", private_key=private, at="2026-10-21T12:00:00Z")
            self.assertEqual(path.read_bytes(), before)
            save_report_decision(path, "I read this run. I am not saying the product meets CRA.")
            sealed = save_report_signature(
                path,
                name="Ada Reviewer",
                private_key=private,
                at="2026-10-21T12:00:00Z",
            )
            reading = read_report_signature(sealed, {"Ada Reviewer": public})
            self.assertTrue(reading["verifiable"])
            self.assertEqual(load_report(path)["signed"]["name"], "Ada Reviewer")

    def test_compile_keeps_pass_fail_and_explicit_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs").mkdir()
            (repo / "docs" / "present.md").write_text("present\n", encoding="utf-8")
            passed = _claim("claim-pass", "docs/present.md")
            missing = _claim("claim-miss", "docs/missing.md")
            skipped = _claim("claim-skip", "docs/present.md")
            run = build_run_result(
                repo,
                [passed, missing, skipped],
                _packs(),
                skip={"claim-skip": "the file is out of scope for this review"},
            )
            report = compile_report(
                run_result=run,
                requirements=[_requirement("REQ-A")],
                claims=[passed, missing, skipped],
            )
            by_id = {row["id"]: row for row in report["run_result"]["claims"]}
            self.assertEqual(by_id["claim-pass"]["status"], "pass")
            self.assertEqual(by_id["claim-pass"]["checks"][0]["status"], "pass")
            self.assertEqual(by_id["claim-miss"]["status"], "fail")
            self.assertIn("is absent", by_id["claim-miss"]["checks"][0]["detail"])
            self.assertEqual(by_id["claim-skip"]["status"], "skipped")
            self.assertEqual(
                by_id["claim-skip"]["checks"][0]["detail"],
                "the file is out of scope for this review",
            )
            self.assertEqual(report["run_result"]["packs"][0]["version"], "0.1.0")
            self.assertNotIn("meets_cra", report)
            page = review_page(
                report,
                None,
                saved=True,
                report_exists=True,
                same_run_value=True,
                door={"repo_id": "widget"},
            ).decode()
            self.assertIn('data-claim="claim-pass" data-status="pass"', page)
            self.assertIn('data-claim="claim-miss" data-status="fail"', page)
            self.assertIn('data-claim="claim-skip" data-status="skipped"', page)
            self.assertIn("the file is out of scope for this review", page)
            self.assertNotIn('data-claim="claim-skip" data-status="pass"', page)


class ReviewPageTest(unittest.TestCase):
    def test_page_shows_an_older_run_and_requirements_that_were_not_checked(self):
        claim = _claim("claim-a", "docs/a.md")
        report = compile_report(
            run_result=_run(claim, worktree="dirty"),
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        page = review_page(
            report,
            None,
            saved=True,
            report_exists=True,
            same_run_value=False,
            unchecked=["REQ-B"],
            door={"repo_id": "widget", "report_path": "/tmp/signed/reports/review-report_20261021T120000Z.json"},
        ).decode()
        self.assertIn("same run: no", page)
        self.assertIn("older run", page)
        self.assertIn("not verification of that commit", page)
        self.assertIn("These selected Requirements were not checked", page)
        self.assertIn("REQ-B", page)
        self.assertIn('name="report"', page)
        self.assertIn("review-report_20261021T120000Z.json", page)
        self.assertNotIn('name="confirm"', page)
        self.assertIn("no field for a conclusion that the product meets CRA", page)
        preview = review_page(
            report,
            None,
            saved=False,
            report_exists=False,
            same_run_value=True,
            door={"repo_id": "widget"},
        ).decode()
        self.assertIn("not saved", preview)
        self.assertIn('data-same-run="yes"', preview)
        self.assertNotIn('name="confirm"', preview)
        self.assertNotIn('name="decision"', preview)
        self.assertIn(">Compile</button>", preview)


def _claim(claim_id: str, path: str) -> dict:
    return build_claim(
        claim_id=claim_id,
        requirement={"id": "REQ-A", "namespace": "RISE/Example", "pack_id": "example"},
        source="documents",
        args={"path": path},
        checks=[{"check": "exist", "args": {"paths": [path]}}],
        description="The file is the evidence for this Requirement.",
    )


def _requirement(requirement_id: str) -> dict:
    return {
        "id": requirement_id,
        "pack_id": "house",
        "namespace": "RISE/house",
        "source": {
            "framework": "test",
            "instrument": "fixture",
            "identifier": "FIX-1",
            "language": "en",
            "url": "https://example.test/law",
        },
        "references": [{"nr": 1, "locator": "1", "law_text": "The product documents the risk."}],
    }


def _packs() -> list[dict]:
    return [{"id": "house", "version": "0.1.0", "digest": "abc"}]


def _run(claim: dict, *, worktree: str | None = None, digest_suffix: str | None = None) -> dict:
    row = {
        "id": claim["id"],
        "digest": version_digest(claim) if digest_suffix is None else version_digest(claim) + digest_suffix,
        "status": "pass",
        "checks": [
            {
                "index": 0,
                "check": "exist",
                "args": {"paths": [claim["args"]["path"]]},
                "status": "pass",
            }
        ],
    }
    run = {
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "packs": _packs(),
        "claims": [row],
    }
    if worktree is not None:
        run["commit"] = "a" * 40
        run["worktree"] = worktree
    return run


class CompileImplTest(unittest.TestCase):
    def test_review_compile_calls_the_compile_backend(self):
        import inspect

        from app.review_model import _compile_review
        from review.compile import compile_report as engine_compile
        from review.compile import write_report as engine_write
        from studio.compile.impl import compile_report as backend_compile
        from studio.compile.impl import write_report as backend_write

        self.assertIs(backend_compile, engine_compile)
        self.assertIs(backend_write, engine_write)
        from review.compile import load_report as kept_load
        from review.compile import replace_saved_report as kept_replace
        from studio.compile.impl import load_report as backend_load
        from studio.compile.impl import replace_saved_report as backend_replace

        self.assertIs(backend_load, kept_load)
        self.assertIs(backend_replace, kept_replace)
        for function in (backend_compile, backend_write, backend_load, backend_replace):
            self.assertIn("studio/compile/impl/", inspect.getsourcefile(function).replace("\\", "/"))
        source = inspect.getsource(_compile_review)
        self.assertIn("from studio.compile.impl import compile_report, write_report", source)
        self.assertNotIn("review.compile", source)
        kept = inspect.getsource(__import__("review.compile", fromlist=["record_decision"]))
        self.assertNotIn("def compile_report", kept)
        self.assertNotIn("def write_report", kept)
        self.assertNotIn("def validate_report", kept)
        self.assertNotIn("def load_report", kept)
        self.assertNotIn("def replace_saved_report", kept)
        self.assertNotIn("def record_decision", kept)
        self.assertNotIn("def sign_report", kept)

    def test_review_decision_lives_in_the_review_backend(self):
        import inspect

        from review.compile import read_report_signature as kept_read
        from review.compile import record_decision as kept_decision
        from review.compile import save_report_decision as kept_save_decision
        from review.compile import save_report_signature as kept_save_signature
        from review.compile import sign_report as kept_sign
        from studio.review.impl import read_report_signature as backend_read
        from studio.review.impl import record_decision as backend_decision
        from studio.review.impl import save_report_decision as backend_save_decision
        from studio.review.impl import save_report_signature as backend_save_signature
        from studio.review.impl import sign_report as backend_sign

        pairs = (
            (backend_decision, kept_decision),
            (backend_sign, kept_sign),
            (backend_save_decision, kept_save_decision),
            (backend_save_signature, kept_save_signature),
            (backend_read, kept_read),
        )
        for backend, kept in pairs:
            self.assertIs(backend, kept)
            self.assertIn("studio/review/impl/", inspect.getsourcefile(backend).replace("\\", "/"))

    def test_durable_report_path_lives_in_review(self):
        import inspect

        from review.compile import durable_report_path as kept_path
        from studio.review.impl.path import durable_report_path as review_path

        self.assertIs(review_path, kept_path)
        self.assertIn(
            "studio/review/impl/path.py",
            inspect.getsourcefile(review_path).replace("\\", "/"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                review_path(Path(tmp)),
                Path(tmp) / "docs" / "reports" / "review-report.json",
            )

    def test_compiled_report_path_lives_in_compile(self):
        import inspect

        from app.review_model import _compile_review
        from studio.compile.impl.path import _new_review_report_path

        self.assertIn(
            "studio/compile/impl/path.py",
            inspect.getsourcefile(_new_review_report_path).replace("\\", "/"),
        )
        source = inspect.getsource(_compile_review)
        self.assertIn("from studio.compile.impl.path import _new_review_report_path", source)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "reports"
            path = _new_review_report_path(folder)
            self.assertEqual(path.parent, folder)
            self.assertRegex(path.name, r"^review-report_\d{8}T\d{6}Z\.json$")
            self.assertTrue(folder.is_dir())
            self.assertFalse(path.exists())


class ReviewPresentTest(unittest.TestCase):
    def test_review_read_model_lives_in_the_review_backend(self):
        import inspect

        from review.present import PREVIOUS_UNKNOWN as kept_unknown
        from review.present import present_compiled_report as kept_compiled
        from review.present import present_raw_run as kept_raw
        from review.present import seal_label as kept_label
        from studio.review.impl.present import PREVIOUS_UNKNOWN as backend_unknown
        from studio.review.impl.present import present_compiled_report as backend_compiled
        from studio.review.impl.present import present_raw_run as backend_raw
        from studio.review.impl.present import seal_label as backend_label

        self.assertIs(backend_unknown, kept_unknown)
        pairs = (
            (backend_label, kept_label),
            (backend_raw, kept_raw),
            (backend_compiled, kept_compiled),
        )
        for backend, kept in pairs:
            self.assertIs(backend, kept)
            self.assertIn("studio/review/impl/", inspect.getsourcefile(backend).replace("\\", "/"))

    def test_report_inspection_lives_in_the_review_backend(self):
        import inspect

        from review.compile import same_run as kept_same
        from review.compile import unchecked_requirement_ids as kept_unchecked
        from studio.review.impl.present import same_run as backend_same
        from studio.review.impl.present import unchecked_requirement_ids as backend_unchecked

        self.assertIs(backend_same, kept_same)
        self.assertIs(backend_unchecked, kept_unchecked)
        for function in (backend_same, backend_unchecked):
            self.assertIn("studio/review/impl/", inspect.getsourcefile(function).replace("\\", "/"))

    def test_shared_sentences_live_outside_the_report(self):
        import inspect

        from review.compile import NO_CRA_FIELD as kept_field
        from review.compile import NOT_A_LEGAL_CONCLUSION as kept_conclusion
        from review.compile import worktree_sentence as kept_sentence
        from studio.common.presentation import NO_CRA_FIELD as shared_field
        from studio.common.presentation import NOT_A_LEGAL_CONCLUSION as shared_conclusion
        from studio.common.presentation import worktree_sentence as shared_sentence

        self.assertIs(shared_conclusion, kept_conclusion)
        self.assertIs(shared_field, kept_field)
        self.assertIs(shared_sentence, kept_sentence)
        self.assertIn(
            "studio/common/presentation.py",
            inspect.getsourcefile(shared_sentence).replace("\\", "/"),
        )
        self.assertEqual(shared_sentence({"worktree": "clean"}), "The worktree was clean.")
        self.assertIn("not verification of that commit", shared_sentence({"worktree": "dirty"}))


if __name__ == "__main__":
    unittest.main()
