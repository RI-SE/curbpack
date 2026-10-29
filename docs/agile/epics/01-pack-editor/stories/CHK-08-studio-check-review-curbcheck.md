# CHK-08 — Studio Check and Review talk to the new `curbcheck`

**Status:** Decided 2026-10-29 by danielfl. GWT below. Implementation: `plan/CHK-08.md`.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**Depends on:** [CHK-07](CHK-07-curbcheck-workspace.md) (runner + defaults API + CLI contract). Door / path display: [SYS-03](SYS-03-one-repo-door.md). Contract: [workspace.md](../../../../reference/workspace.md).

**As a pilot user**, I want the Studio **Check** and **Review** pages to call the same `curbcheck` Python API CHK-07 ships (paths from the open repo’s `curbpack.json`, results under `results_dir`, reports under `reports_dir`), so the UI and the CLI cannot diverge.

### What this story is

Rewire Studio Check (run + show outcomes) and Review / Compile (read that run, write `review-report_<UTC>.json`) to the post–CHK-07 runner: import the package functions, not a second path scheme or a packs-directory override.

Preserve the approved Check / Review UX already in the app; this story changes **how** those pages talk to curbcheck, not a redesign of the pages.

### Out of this story

CHK-07 itself (CLI, `--defaults`, id-list flags, curbcheck unit/package tests). SYS-03 door chrome. SYS-03 Task 8 (extract stays temporary until accept). Full CHK-01 editor polish beyond calling the new runner. `unsigned_requirements` behaviour. Cover-page `workflow.py` sample-product paths. Packs v2 field invention. New Check/Review page UX.

The ids CHK-R01–CHK-R04 in this file are this story’s requirements. They are not `docs/req/checks.md` CHK-R01–CHK-R17 (CHK-05/CHK-06) and not CHK-07’s story-local CHK-R01–CHK-R06.

---

### CHK-R01 — Check run uses the shared runner

With an open repo and a valid `curbpack.json`, Check invokes the same Python run entry as `python3 -m checks` / packaged `curbcheck` for that repo (`run_repository` / `run_and_write` with `packs_root=None`, so packs, claims, and results come from that file). The Check page’s existing contract requests JSON (the Run action writes a run-result file). CLI stdout-only (`-j` omitted) is not the page contract.

- **Given** an open product repository with a valid `curbpack.json` per workspace.md §2
- **When** the person chooses Check on the Check page
- **Then** Studio calls `run_and_write` for that repository with `packs_root=None`
- **And** packs load from that file’s `packs_dir` and claims from `claims_dir`
- **And** a new `{results_dir}/run-result_<YYYYMMDDTHHMMSSZ>.json` is written
- **And** the page shows that concrete path
- **And** a second Check writes a second dated file and leaves the first byte-for-byte

- **Given** that same repository
- **When** Check runs
- **Then** it does not pass a packs **directory** as `packs_root`
- **And** it does not write an undated `run-result.json` as the page’s JSON file

---

### CHK-R02 — Create/edit blank `curbpack.json` uses CHK-07 defaults

Any Studio create/edit that needs a blank `curbpack.json` body calls CHK-07’s defaults function. There is no second Studio copy of created-file values.

- **Given** Studio needs a blank `curbpack.json` body (create dialog, or edit when seeding missing created-file values)
- **When** it builds that object
- **Then** it calls `checks.defaults.created_curbpack` (the same function `discovery.door.created_curbpack` already is)
- **And** the path fields and `unsigned_requirements` match workspace.md §2.2 created-file values
- **And** Studio does not keep a second literal of those created-file values

CHK-07 Task 4 already made door a call-through. This requirement only fails remaining copies.

---

### CHK-R03 — Review / Compile reads that run

Compile reads the run result Check just produced for the open repo and writes under that file’s `reports_dir`. It does not treat a hard-coded workspace `product/` sample as that run.

- **Given** Check has written `{results_dir}/run-result_<UTC>.json` for the open repository
- **When** the person compiles on Review
- **Then** the report is compiled from that run result (the latest dated file under that repo’s `results_dir`, or the confined `?result=` path)
- **And** Claims load from that repo’s `claims_dir`
- **And** a new `{reports_dir}/review-report_<YYYYMMDDTHHMMSSZ>.json` is written
- **And** the page shows that concrete path
- **And** a second compile writes a second dated file and leaves the first byte-for-byte

- **Given** `<workspace>/product/` has a different run-result and a different Claim
- **When** Review compiles the open repository
- **Then** the report does not contain that workspace Claim
- **And** nothing is read or written under `product/docs/reports/` or `product/.curbpack/` as if it were this run

---

### CHK-R04 — Studio Check/Review tests match the new call sites

- **Given** the Studio Check/Review test inventory recorded in this story’s plan
- **When** this story is verified done
- **Then** those tests construct `curbpack.json` with the required workspace.md §2.2 fields
- **And** they assert Check/Review paths per CHK-R01 and CHK-R03
- **And** a packs-directory `packs_root` override is not required for a green Studio Check/Review (or related e2e) suite listed in that inventory

---

## Out of scope (restated)

- CHK-07 CLI, `--defaults`, id-list flags, `tests/test_chk07_curbcheck.py`, `tests/test_curbcheck_package.py`, `make test-curbcheck`.
- SYS-03 door chrome and SYS-03 Task 8.
- Redesigning Check/Review pages; gutting Discover/Check/Review UX.
- `unsigned_requirements` enforcement.
- Cover `workflow.py` / `Workspace.run_path` sample-product paths (not the Check/Review pages).
- Inventing Packs v2 fields or a new page UX.
