# Test-case automation

Encode RP, PV, FS, CL, DT, OP, NB, RL, RB, and UV as shell functions that a human can also run. EV and PK are finished written references, not work items. Archived prior plan: `.superpowers/sdd/plans/2026-09-14-remaining-test-suite-work.md`.

Resume after context loss: open this file, take the first heading that is not `FINISHED`, in the order below. Update this file as soon as a block’s state changes.

## How to execute a block

Read `.cursor/skills/ev-test-case/SKILL.md` and the named suite file. Style reference: EV-001–EV-005 (written procedure). Automation SoR is still the suite markdown: transcribe SETUP then TEST STEPS. Do not improve, generalise, or reinterpret.

Do not invent requirements, expected results, procedures, R-states, JSON, mappings, grep deny-lists, or builder/reviewer behaviour. A catalogue row marked **To be specified** becomes a SKIP stub that prints that case’s “Not specified yet. Do not run.” text. Never write SETUP/TEST STEPS for it.

Do not change Curbpack implementation. Do not add TEARDOWN. Do not construct R-state in TEST STEPS. Do not create `tmp/R*`. Do not parse suite markdown at runtime. Do not push, open PRs, or touch remotes.

**Preserve manual semantics 1:1.** Same setup, stimulus, observations, and expected results as the written case. A function that omits a written step, adds a step, merges steps, reorders steps, or PASSes after skipping a human observation is wrong.

For every automated testcase, a maintainer must be able to open the suite markdown and the function side by side and see a direct correspondence:

- manual SETUP step N → one automated command (or the case’s own stop/SKIP at that step)
- manual TEST STEP N → one automated command
- manual expected/observed result for that step → one automated assertion for that step

Label the function with the same section and step numbers as the markdown (`# SETUP 1`, `# SETUP 2`, `# TEST STEPS 1`, …). Do not merge, reorder, hide, or generalise steps in ways that break this traceability. One written step may use several shell lines only when the written Action is already several commands; they stay under that step’s label. Do not collapse SETUP 1–4 into a helper, and do not assert several steps’ expected results in one check.

**No hidden test-case abstractions.** Shared code is only dispatch + PASS/FAIL/SKIP recording + summary. Duplicate SETUP lines across functions when the written cases duplicate them. Forbidden: `prepare_r1`, `run_check_json`, `assert_fig1`, markdown parsers, and any helper that wraps `curbpack check` / `setup.sh` / `mutate_pack.sh` / Fig. JSON. Named strings already in a case (for example RP-001’s CE marking / certification / notified-body) may be checked as written; do not extend the list.

Human / assignment / builder steps: do not invent an oracle. If the case’s own stop condition is missing input, SKIP with that stop text. If a remaining step is human interpretation or builder handoff, SKIP the whole case (do not PASS the mechanical prefix). Unspecified = SKIP. Operator typo / unknown ID = runner error, not SKIP.

POSIX `sh`. Use another language only if a written step cannot be expressed in shell; state the reason in the block. `jq` is allowed only to read JSON fields the case already names.

Implementation (lower-cost model): `TODO` → `IMPL-START` → do the block → local checks → `IMPL-END`. Stop.

Review (one pass, stronger model): `IMPL-END` → `REVIEW-START` → check 1:1 step mapping (markdown step N ↔ labelled command + assertion), transcription fidelity, SKIP vs invent, helper creep, skill reject-list, runner continue/summary → write findings in the same block → `REVIEW-END`.

Fix (at most one pass, lower-cost model): if findings exist, `REVIEW-END` → `FIX-START` → fix only those findings → verify → `FINISHED`. If none, `REVIEW-END` → `FINISHED`.

Local checks: `sh -n` on touched shell files; skill reject-list; every catalogue ID has exactly one function; unspecified functions return SKIP; executable functions label SETUP/TEST STEPS with the markdown step numbers; if `tmp/verification-run.sh` exists, run the block’s selector; after doc edits, `curbpack check` (exit code authoritative). Do not invent a verification baseline.

Write set for a block: that block’s named files, this `PLAN.md`. Stage named paths only. Suite blocks do not edit `run.sh`.

Call shape (copy per function; do not source a hidden library of case steps):

```sh
# return 0 PASS, 1 FAIL, 2 SKIP
fs_001() {
	# SETUP 1  — same Action as FS.md SETUP step 1
	# assert    — same Expected result as that step; else echo FS-001 SETUP 1; return 1
	# SETUP 2  — …
	# TEST STEPS 1 — same Action as FS.md TEST STEPS step 1
	# assert       — same Expected result as that step; else echo FS-001 TEST STEPS 1; return 1
}

fs_002() {
	echo "FS-002: Not specified yet. Do not run this case."
	return 2
}
```

Runner selectors from the Curbpack root, after a verification run exists:

```sh
sh docs/testing/automation/run.sh FS-001   # one case
sh docs/testing/automation/run.sh FS       # one suite
sh docs/testing/automation/run.sh all      # RP PV FS CL DT OP NB RL RB UV
```

A human equivalent: `make start-verification-run` once, then `sh docs/testing/automation/run.sh FS-001`, or `source` the suite file and call `fs_001`. Manual markdown steps and the function must remain the same procedure.

Continue after FAIL/SKIP. Print a final count of PASS / FAIL / SKIP. Non-zero runner exit if any FAIL or if the selector is unknown / suite file missing. SKIP-only is exit 0.

---

## [FINISHED] Matching verification run — executable cases through assertions

**Objective.** Encoding exists, but a matching verification run has not yet taken those cases through their assertions. Start a run at the committed HEAD with the published reference-product pin. Run every executable automated case. Report SETUP failures separately from TEST STEPS / product failures. Preserve evidence. One review plus one remedy round.

**Files.** This `PLAN.md`. Do not hand-edit `tmp/verification-run.sh`. Do not bypass `make start-verification-run` checks. Do not change Curbpack implementation.

**Procedure.**

1. Commit the intended automation and suite-markdown gap fixes on a clean tree (preserve unrelated work).
2. `make start-verification-run` with defaults: this HEAD, `tests/cyberready-test-product.pin`, today's as-of date.
3. `sh docs/testing/automation/run.sh all` from the Curbpack root. Continue after FAIL/SKIP.
4. Classify each FAIL as SETUP (stopped before stimulus) or TEST STEPS (oracle). Keep SKIP as coverage gaps, not completed coverage.
5. Review once. One remedy round with targeted reruns. Record remaining findings here.

**Verify.** Executable cases reach TEST STEPS unless a written SETUP stop applies. Human-facilitated cases remain SKIP. Unspecified cases remain SKIP.

**Revisions (not one freeze).** Product under test: Curbpack `c64ec44e9f102717f529ef5426ee6d6a4199aa71` (binary from `tmp/verification-run.sh`). Reference product: `2b0c3f30bda411917ca0cd5b5f545e04de11cd25`. As-of: `2026-09-16`. Test scripts actually executed in the final `all` run: `c64ec44` suite files plus uncommitted `run.sh` / `rp.sh` later committed as `4c0eed6`. Do not treat `CURBPACK_COMMIT` and those scripts as the same frozen revision.

Logs: `tmp/automation-evidence/all-round1.log`, `all-round2.log`. RP-002 underlag: `tmp/automation-evidence/rp-002/`.

Round 1 (`all`): SETUP failures 0 for cases that started. Runner aborted after PV-007 (`fs.sh` cwd-relative).

Remedy: `automation_dir` from `$0`; RP-001 “selected checks passed” case-insensitive. One remedy round; stop.

Round 2 (`all`): runner printed `PASS 13 / FAIL 2 / SKIP 39`. SETUP failures: 0.

**Classification (not the runner labels)**

- 13 reported PASS, with coverage limits (DT-001 does not close MUST-30; DT-004 R1 `failures` is `null` so empty finding lists are not proven by digest identity).
- RP-001: **test assessment error**, not product-FAIL. `grep` on `certification` matches the disclaimer “not certification”. Claim check stays manual until it works.
- RP-002: **product observation to investigate**. `share` wrote `SECURITY.md` then exported a different result than the preceding check. Exact requirement violation not established; share contract is split (README/comment: check-first; `help.go`/implementation: draft inputs then check). Evidence from the log; working-tree after-files were not retained after later restores.
- 39 SKIP: not completed coverage. Human-facilitated: CL-001, CL-002, UV-001–UV-003. Assignment stop: RL-004. Unspecified: RP-006/007, PV-004, FS-002–007, CL-003/004, DT-002, OP-001–006, NB-001/002, RL-001–003, RL-005, RB-001–004, UV-004–008.

Automation pass ended after the agreed remedy round. Full verification is not complete.

---

## [FINISHED] Harness — dispatch, status, summary

**Objective.** Add a POSIX runner with no test-case bodies. Later suite files plug in by filename.

**Files.** Create: `docs/testing/automation/run.sh`. Do not create suite files here. Do not edit suite markdown.

**Behaviour.**

- Map `RP-001` → `rp_001`, `RP` → all `rp_[0-9][0-9][0-9]` in `rp.sh`, `all` → suite files in this order: `rp.sh pv.sh fs.sh cl.sh dt.sh op.sh nb.sh rl.sh rb.sh uv.sh`.
- `source` the suite file (not execute) so functions share the runner shell; each function still `source tmp/verification-run.sh` itself when the written SETUP says so. The runner must not restore the product or `cd` for the case.
- Wrap each call: capture 0/1/2; record `PASS id` / `FAIL id` / `SKIP id`; continue. Do not unwrap, merge, or run case steps in the runner.
- Unknown selector or missing selected suite file: error, no SKIP.
- `all` with missing suite files: error (incremental work uses a suite selector until those files exist).
- Header comment: how to run one case / one suite / all; requires an already-filled `tmp/verification-run.sh`; EV/PK not in this runner.

**Verify.** `sh -n docs/testing/automation/run.sh`; `sh docs/testing/automation/run.sh` with no args and with `NO-SUCH` both error; `sh docs/testing/automation/run.sh RP` errors on missing `rp.sh`.

---

## [FINISHED] RP — Review Pack cases

**Objective.** One function per RP catalogue row. Transcribe RP-001–RP-005. SKIP RP-006 and RP-007.

**Files.** Create: `docs/testing/automation/rp.sh`. Read: `docs/testing/test_suites/RP.md`. Do not rewrite RP.md.

**Functions.** `rp_001` … `rp_007`.

**Traps.** RP-003–RP-005 do not verify a specified requirement; keep that. For human-read steps, check only results the case already names (files present, named JSON fields, named forbidden phrases). If a remaining sentence is un-named “unsupported assurance”, SKIP the case rather than inventing a deny-list. Do not invent a digest fixture for RP-004.

**Verify.** `sh -n`; `sh docs/testing/automation/run.sh RP` (SKIP-only is OK if no verification run); with a verification run, `RP-006` SKIP and `RP-001` PASS/FAIL against the written oracle.

---

## [FINISHED] PV — provenance cases

**Objective.** Transcribe PV-001–PV-003 and PV-005–PV-007. SKIP PV-004 (EC-04/EC-05 not specified).

**Files.** Create: `docs/testing/automation/pv.sh`. Read: `docs/testing/test_suites/PV.md`. Do not invent PF-02.

**Functions.** `pv_001` … `pv_007`.

**Traps.** Each executable case already says it does not close MUST-31. Observe stdout/cache omissions as the case writes them; do not “fix” them in the function. PV-006 SETUP 5 runs a PF-01 control and records `comparison_key`; TEST STEPS 3 must differ from that control.

**Verify.** `sh -n`; `run.sh PV-004` SKIP; with a matching verification run, `run.sh PV-001` and `run.sh PV-006` reach TEST STEPS.

**Findings**

- Important (fixed in files, pending matching run): PV-006 now records a PF-01 `comparison_key` before PF-06 mutation and compares the mutated key to that control.
- Minor: `pv_005` SETUP 5 does not assert that `SOURCE.txt` lacks pack IDs/versions.

---

## [FINISHED] FS — path-boundary cases

**Objective.** Transcribe FS-001. SKIP FS-002–FS-007.

**Files.** Create: `docs/testing/automation/fs.sh`. Read: `docs/testing/test_suites/FS.md`.

**Functions.** `fs_001` … `fs_007`.

**Traps.** FS-001 pass criteria are non-zero exit and actual traversal rejection (`ADV-TRAVERSAL` and `path traversal refused`). The exact stderr line on the verification baseline is also required. An exact stderr line alone is not sufficient.

**Verify.** `sh -n`; `run.sh FS-002` SKIP; with a matching verification run, `run.sh FS-001` reaches TEST STEPS.

---

## [FINISHED] CL — claim-review cases

**Objective.** Encode CL-001–CL-004 without inventing claim oracles. SKIP CL-003 and CL-004 as unspecified.

**Files.** Create: `docs/testing/automation/cl.sh`. Read: `docs/testing/test_suites/CL.md`.

**Functions.** `cl_001` … `cl_004`.

**Traps.** CL-001 TEST STEPS are human search for implied overclaim language — SKIP citing that; do not invent grep patterns. CL-002 steps 1–4 are mechanical; step 5 (“no derivative weakens the structural-only boundary”) is human — SKIP the case, do not PASS after step 4, do not invent a third R-id (R1 or R2 as written; if the function must pick one, use R1 and record it).

**Verify.** `sh -n`; `run.sh CL` shows SKIP for 001/003/004; CL-002 SKIP until step 5 has a written machine oracle (it does not).

---

## [FINISHED] DT — determinism cases

**Objective.** Transcribe DT-001, DT-003, DT-004. SKIP DT-002 (EC-07 not specified).

**Files.** Create: `docs/testing/automation/dt.sh`. Read: `docs/testing/test_suites/DT.md`.

**Functions.** `dt_001` … `dt_004`.

**Traps.** DT-001 is 20 runs into `$CURBPACK_ROOT/tmp/dt-001` (evidence dir, not an R-id). Compare only the named semantic fields. Capture receipt `evaluation_digest` (stdout evaluation JSON has no `digest` field). A missing digest fails; a digest-only difference does not. Finding identity is `failures[].gate_id`. Do not invent locale/timezone commands.

**Verify.** `sh -n`; `run.sh DT-002` SKIP; with a matching verification run, `run.sh DT-001` (long; must still continue the suite afterward).

**Findings**

- Important (fixed): DT-004 must always run SETUP 6–10; copy-and-skip on file existence was removed.
- Important (fixed in files, pending matching run): DT-001 records `evaluation_digest` from the receipt. An empty/`null` digest fails. Difference in `evaluation_digest` alone still does not fail.

---

## [FINISHED] OP — operational-failure cases

**Objective.** SKIP OP-001–OP-006. Do not write executable OP procedures.

**Files.** Create: `docs/testing/automation/op.sh`. Read: `docs/testing/test_suites/OP.md`.

**Functions.** `op_001` … `op_006`. Each prints that case’s “Not specified yet. Do not run this case.” and returns 2.

**Traps.** Do not invent EC-09, unwritable-destination, storage-exhaustion, kill-window, or cache-failure injection.

**Verify.** `sh -n`; `run.sh OP` → six SKIP, exit 0.

---

## [FINISHED] NB — network/data-boundary cases

**Objective.** SKIP NB-001 and NB-002. Do not invent EC-06 or observation methods.

**Files.** Create: `docs/testing/automation/nb.sh`. Read: `docs/testing/test_suites/NB.md`.

**Functions.** `nb_001` `nb_002`. SKIP stubs only.

**Verify.** `sh -n`; `run.sh NB` → two SKIP, exit 0.

---

## [FINISHED] RL — release-artefact cases

**Objective.** SKIP RL-001–RL-003 and RL-005. Encode RL-004’s stop/skip without inventing tag, commit, artefact, or checksum.

**Files.** Create: `docs/testing/automation/rl.sh`. Read: `docs/testing/test_suites/RL.md`.

**Functions.** `rl_001` … `rl_005`.

**Traps.** RL-004 SETUP step 3: if the assignment does not name tag, source commit, and shipped artefact, SKIP with that stop text. Do not read GitHub or compute a checksum to fill gaps. Do not auto-PASS an observed gap.

**Verify.** `sh -n`; `run.sh RL` → SKIP all five when assignment values are absent.

---

## [FINISHED] RB — resource/concurrency cases

**Objective.** SKIP RB-001–RB-004. Do not invent large-tree R-states, numeric limits, or EC-08.

**Files.** Create: `docs/testing/automation/rb.sh`. Read: `docs/testing/test_suites/RB.md`.

**Functions.** `rb_001` … `rb_004`. SKIP stubs only.

**Verify.** `sh -n`; `run.sh RB` → four SKIP, exit 0.

---

## [FINISHED] UV — user-handoff cases

**Objective.** SKIP UV-004–UV-008 as unspecified. SKIP UV-001–UV-003 as builder-facilitated; do not simulate a builder.

**Files.** Create: `docs/testing/automation/uv.sh`. Read: `docs/testing/test_suites/UV.md`. After this file exists, `run.sh all` must run.

**Functions.** `uv_001` … `uv_008`.

**Traps.** UV-001–UV-003 are Executable for a human builder. Automation must not PASS them. SKIP citing builder handoff / interpretation. Do not run `setup.sh` for UV-001. Do not map UV-002 to MUST-60. Do not invent UV-004–UV-008 procedures.

**Verify.** `sh -n`; `run.sh UV` → eight SKIP; `run.sh all` sources all ten suite files, continues after FAIL, prints PASS/FAIL/SKIP counts.
