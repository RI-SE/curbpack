# CHK-08 — Studio Check and Review talk to the new `curbcheck`

**Status:** Draft placeholder. Decided 2026-10-29 by danielfl: write after [CHK-07](CHK-07-curbcheck-workspace.md) lands. Not implemented.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**Depends on:** [CHK-07](CHK-07-curbcheck-workspace.md) (runner + defaults API + CLI contract). Door / path display: [SYS-03](SYS-03-one-repo-door.md). Contract: [workspace.md](../../../../reference/workspace.md).

**As a pilot user**, I want the Studio **Check** and **Review** pages to call the same `curbcheck` Python API CHK-07 ships (paths from the open repo’s `curbpack.json`, results under `results_dir`, reports under `reports_dir`), so the UI and the CLI cannot diverge.

### What this story is

Rewire Studio Check (run + show outcomes) and Review / Compile (read that run, write `review-report_<UTC>.json`) to the post–CHK-07 runner: import the package functions, not a second path scheme or a packs-directory override.

Preserve the approved Check / Review UX already in the app; this story changes **how** those pages talk to curbcheck, not a redesign of the pages.

### Out of this story

CHK-07 itself (CLI, `--defaults`, id-list flags, curbcheck unit/package tests). SYS-03 door chrome. Full CHK-01 editor polish beyond calling the new runner. `unsigned_requirements` behaviour.

### Requirements (to flesh out when CHK-07 is done)

Draft acceptance themes — expand to Given/When/Then when planning:

1. **Check run** — With an open repo and valid `curbpack.json`, Check invokes the shared run entry (same as `python3 -m checks` / packaged `curbcheck` for that repo). Result JSON lands under that file’s `results_dir` as `run-result_<UTC>.json` when JSON is requested by the page’s contract; the page shows the concrete path.
2. **Defaults** — Any Studio create/edit that needs a blank `curbpack.json` body calls CHK-07’s defaults function (no second Studio copy of created-file values).
3. **Review / Compile** — Compiles from the run result Check just produced for that repo; writes under `reports_dir` as `review-report_<UTC>.json`; does not read a hard-coded workspace `product/` sample as if it were that run.
4. **Tests** — Inventory and update Studio Check/Review UI tests (`tests/test_check_editor.py`, review suite, related e2e) for the new call sites and paths.

Exact GWT and plan: after CHK-07 is verified DONE.
