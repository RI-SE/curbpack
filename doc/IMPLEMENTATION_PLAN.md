# PoC2 Implementation Plan

This is a sequence of demonstrable increments, **not** a rewrite-all checklist. Re-plan only when actual code or tests show a reason. New work follows the target subsystem architecture in `doc/ARCHITECTURE.md`.

## Product ambition and functional baseline

PoC1 is the minimum functional baseline, not the target for PoC2.

PoC2 must preserve the useful capabilities of PoC1 while delivering a substantially more complete, more correct and more maintainable product.

In particular:

- Requirements extraction and discovery hints must be at least as useful and comprehensive as PoC1, with broader coverage, better validation and human-review support.
- Alternative LLM models, prompts and bounded agent strategies must be testable and comparable without changing the Packs v2 domain model.
- Discovery must support improved retrieval and assessment strategies, while keeping human-approved Claims authoritative.
- Requirements and Claims management must support complete workflows, including inspection, correction, editing, signing and subsequent maintenance.
- Checks, compilation and final review must produce trustworthy, traceable and actionable results.
- All subsystem functions must work independently of the graphical UI and be accessible to CLI, CI/CD and tests.
- The graphical interfaces must preserve useful PoC1 workflows and make the expanded capabilities usable.

Architecture cleanup, directory migration and data-model conversion are enabling work, not product milestones in themselves.

**Completion requires demonstrable functional improvements beyond PoC1, verified with comparable source material and realistic end-to-end scenarios.**

Milestone pass criteria below remain valid for their slices. Closing the plan as a product requires the improvements above, not only green structural migration or layout moves.

## M0 — Baseline and contracts

**Closed.** Documentation baseline only. No application code.

- `doc/END_TO_END_SCENARIO.md` holds the 12 October narrative unchanged, and the acceptance criteria that map its steps onto `packs2.md`.
- Those criteria are the end-to-end acceptance test for the later milestones.
- `docs/reference/packs2.md` in this repository stays normative. The historical narrative does not override it.
- `poc/` is unchanged.

**Pass:** the scenario and its acceptance criteria are in `poc2/doc/`, and the architecture doc points at them.

## M1 — Requirement creation and management (first app)

- Reuse steps 00-03 as extraction internals where they work.
- Make step 04 produce a draft Requirement with `references[]`, `source`, `discovery_hints` and relevant fields from Packs v2. No embedded legacy `claim`/`search` shape.
- Adapt editing to load/edit/save the **same** Requirement object. Keep notes and unrelated optional fields across edits.
- Make publication a deliberate operation. A working draft or working copy is not falsely shown as a publisher-signed release.
- Keep sign/verify behavior honest: if not implemented, label it unavailable rather than mocking a certificate.
- Leave discovery and Claim editing outside this first application's domain logic.

**Pass:** one real CRA requirement travels from extraction through human editing to a validated, persisted Requirement/Pack artifact; reload is lossless; usable without UI.

## M2 — Discovery

- Consume M1 Requirements and their `discovery_hints` plus repository hunt settings.
- Port the current working-tree file search. It does not read `source` or `args`. Do not claim Git history, DOORS, or ClearCase support. Do not add a source adapter or an error for source types that are not implemented yet.
- Show candidate relevance in the UI. Feedback there is temporary working material. A rejected candidate is not a durable object, and candidates are not Claims.

**Pass:** one Requirement produces inspectable candidates against a controlled product fixture. The search walks the working tree and does not read `source` or `args`.

## M3 — Claims

- Bind a candidate or chosen product path to one Requirement with persisted `Claim` (`check`, `args`).
- Support correcting/moving a binding without changing the publisher Requirement.

**Pass:** several distinct Claims may refer to the same Requirement and survive a save/load round trip.

## M4 — Real checks and run result

- Implement the smallest actual check set needed for a vertical slice (e.g. `exist`, `contents`), not simulated results.
- Emit the single Packs v2 Run result, including Git HEAD and clean/dirty where applicable, claim identity/digest and per-check outcome.
- A missing file is fail, multiple failures are fine; skipped needs reason; skipped is not pass.

**Pass:** real controlled failures and passes; run result reusable by CLI and UI; dirty run not mislabelled as verification of the commit.

## M5 — Compile/review and usability

- Consume the same run result; display claims and linked requirements for review.
- Capture a human conclusion without pretending it is a machine check. Signing must be verifiable or clearly marked unavailable in the PoC.
- Integrate a thin demo cover page for navigation and status only.

**Pass:** the path in `doc/END_TO_END_SCENARIO.md` meets that file's acceptance criteria, with identifiable inputs, outputs and explicit limitations.

## Progress

### M1 — Requirement creation and management

Implemented and tested (`tests/test_m1_requirement.py`).

- Steps 01–03 run on the Annex VII fixture. Temporary rows keep the old claim slug and are not Requirements.
- Step 04 emits one unsigned draft, `CRA-ANNEX-VII-RISK`, with `references[]`, `source`, and `discovery_hints`.
- Edits round-trip through JSON. A change drops `signed`. `note` is kept.
- Publisher seal is an Ed25519 signature over the version digest, name, and time. A missing local public key is reported as not available. It is not an X.509 certificate and nothing is fetched.
- A working copy sets `origin` and is unsigned. The publisher signature does not cover it.
- The pack directory seal covers the directory digest. Changing a file makes that seal fail.

### M2 — Discovery

Implemented and tested (`tests/test_m2_discovery.py`).

- Walks markdown files in the working tree using `path_hints`, `concepts`, and repo hunt exclude/prefer globs.
- Does not read `source` or `args`, and does not match on `expected_evidence`.
- Returns candidates and does not write them. A rejected path is just absent.

### M3 — Claims

Implemented and tested (`tests/test_m3_claims.py`).

- `exist` and `contents` claims persist as Packs v2 objects and round-trip.
- Rebinding `args` drops `signed` and does not change the requirement digest.
- `fresh`, `owned`, and `dep_ban` raise "not implemented". Unknown check ids raise as well.

### M4 — Checks and run result

Implemented and tested (`tests/test_m4_checks.py`).

- `exist` and `contents` read the files. A missing file is `fail` for both, and `contents` does not also report a header miss.
- A short stub fails `contents`. A long enough file with the headers and the repo token passes, and a pass row has no `detail`.
- One run result records pack id, `version`, directory digest, tool version, and Git HEAD plus clean/dirty when the repo has a commit.
- Exit 0 only when at least one row ran and every row is `pass`. An empty claim list exits 1. `skipped` requires a reason and is not `pass`.
- A dirty worktree is recorded as `dirty`. The exit code does not turn that into a clean verification.

### M5 — Scaffold, compile, review, demo UI

Implemented and tested (`tests/test_e2e_annex_vii.py`, `tests/test_ui_smoke.py`).

- Scaffold writes a short stub marked incomplete and will not overwrite an existing file.
- The end-to-end test runs the Annex VII.3 path: extract, edit, publish, discover, stub, bind, fail, fill the file, pass, move the file, rebind, rename a header, rebind, compile the actual run result, record a decision, and sign the report with a different key from the requirement.
- A passing check does not sign the review. A dirty run's report says it is not verification of that commit's content.
- `python -m app.server` is a cover page and forms. Domain calls stay outside the HTML.
- `python -m checks` writes the same run result.

Limitations that remain:

- Only Annex VII point 3 is published. Other loci stay in temporary extraction files.
- Discovery reads markdown in the working tree only. No Git history, DOORS, or ClearCase.
- Seals are local Ed25519 keys created on sign. They are not X.509 certificates and are not fetched. A missing key is reported as not available.
- The requirement form edits source ids, not source `args`.
- The placeholder probe list is this PoC's list.
- The demo does not create a signed Git commit. An unsigned commit leaves the claim unsigned, and the Git author string is not treated as the signer.
- Editing a file inside a sealed pack directory invalidates that directory seal until it is sealed again.
- `python -m checks` does not delete an older review report. The demo's Check button does, so a signature is not left on a different run.

Next: none for 0.0.1a. Further checks (`fresh`, `owned`, `dep_ban`) and other annex points are out of this slice.

The checks, compile, final-review, and cover-page contracts are in `checks/ARCHITECTURE.md`, `review/ARCHITECTURE.md`, and `doc/ARCHITECTURE.md`. Where this slice is narrower than those contracts, those files say so.

## Execution discipline

Do one milestone at a time. The end-to-end acceptance test is the criteria section of `doc/END_TO_END_SCENARIO.md`, read against `packs2.md`. Before each milestone, name the smallest working slice; after it, demonstrate the output, tests and changed files. Refactor only when concrete duplication or coupling appears. Avoid parallel app rewrites, temporary adapters that become permanent, or changing Packs v2 merely to accommodate existing PoC code. If Packs v2 is ambiguous, record the exact blocker and continue independent work rather than silently deciding a new schema.
