# SYS-02 — Keep the pilot on one test suite

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)
**Status:** Draft. Not a pilot release blocker. Do not implement before this plan is approved, and do not start it ahead of a runnable pilot.

**As a maintainer**, I want every case the pipeline runs to live in the functional suite, and the CI scripts only to summarize that suite, so the next change cannot grow a second test world beside the pilot.

**Accept when:**

- `make test` and the `tests` check inside `make ci-tests` run the same `tests/test_*.py` files through `scripts/ci/checks/tests.py`.
- `make ci-tests` prints one line for that check and a summary. `ONLY=tests` prints each case. An unknown `ONLY` fails and names the valid checks. No new Make target.
- `tests/cs/` is gone, including its runner. There is no `tests/ci/` and no `run_cs_checks` script.
- `select_working_copy` and `select_published_pack` still reject a `pack_id` that is not one directory name, and a normal id still selects. That assertion is inside the suite above.
- Cases already covered by the named tests below are deleted, not copied. The gaps listed in the plan move into the existing module for that behavior.
- `make test` is green after the move. Previously passing tests stay passing.

**Already covered, do not copy:**

- `read_source_text` rejects `../` and an absolute path: `tests/test_m2_discovery.py`
- A skip with a reason is not a green run: `tests/test_m4_checks.py`
- Compile rejects a changed claim digest: `tests/test_review_compile.py`
- A dirty worktree is not verification of that commit: `tests/test_review_compile.py` and `tests/test_e2e_annex_vii.py`
- An unsigned claim is not a verified signature: `tests/test_e2e_annex_vii.py`

**Out of scope:** Moving the flat suite into subsystem folders. Scanners (`sast`, `secrets`, `vuln`). Docker. Packs v2. EP-02. The pilot release itself. A new test runner.

**Conflict:** EP-03's unpublished SEC-03 line says to preserve separate executable checks for the five scripts. Proposed resolution, not normative until this plan is approved: those functional cases fold into this story. A separate script is only a future scanner check under EP-03 SEC-04. See `docs/agile/epics/03-ssdf-security/EPIC.md`.
