# Review → Discovery → Claims — acceptance scenarios

Status: **normative behavioral test specification; not evidence of passing tests**. The target flow was agreed on 21 October 2026. The current ZIP does not implement all UI features. Use the repository's existing test conventions; these scenarios shall become automated tests rather than being declared complete because an architecture file exists.

## Fixture and authority

Use one controlled product repository, one selected Pack with Requirements R1 and R2, and Claim C-old for R1 using `exist` and `contents`, plus C-ok for R1 with passing configured Checks. Produce a real Packs v2 Check run A. Simulate a missing or moved file for C-old and run Checks again (run B), yielding C-old=`fail`, C-ok=`pass`. Prepare candidate paths (including C-ok's known evidence and new replacement evidence) in a deterministic Discovery fixture/call boundary; do not depend on a live LLM, network or external model. Ensure source paths are repo-relative and candidate/Claim matching is explicitly checkable. Separate the old signed human Review report from the current Check run.

## Required test cases

**REV-01 — Failed context and popup.** Open Review for run B. It shows C-old, the corresponding Requirement, source `args`, failing Check IDs and details. Select *Discover again*. A modal opens for **R1 only**, the old failed Claim and its Checks remain in the Review page beneath it, and a short notice requests equivalent evidence and suitable Checks. Closing/canceling changes no Claim or Check result.

**REV-02 — No Claim input into Discovery.** Calling the existing Discovery search for R1 uses its normal Requirement/repo/hunt inputs and returns the same candidates and ranking with and without the Review popup. It does not receive Claims or run Checks; any coverage annotation is computed separately for UI presentation. Stored Discover jobs, votes, hints and feedback are unchanged by the UI annotation.

**REV-03 — Grey, never hide.** The R1 candidate matching C-ok's source is shown but greyed with an accurate *passed in the selected Check run* explanation. The replacement candidate and the path associated with C-old's failing result are not greyed. Greyed candidates are still inspectable. No green/legal conclusion is derived from the grey style.

**REV-04 — Missing, stale, ambiguous or non-passing coverage.** With no applicable run, a different repo/pack, a Claim digest differing from its Check row, `skipped`/`fail` on any configured Check of the matching Claim, or multiple contradictory matches, or a path-specific Check actually evaluating different evidence, render candidates normally (not grey). A signature alone is insufficient. A Check result is described as historical run evidence, not eternal proof that file content remains unchanged.

**REV-05 — Add one or several, no overwrite.** From the popup select one or two candidates and define suitable Checks. Via ordinary Claims binding, create C-new-1 (and optionally C-new-2) for R1. C-old remains byte-for-byte unchanged, even if it was signed, and its earlier `fail` is unchanged. New Claims may have multiple `checks[]`; each distinct evidence source is a separate Claim. No new schema or automatic rebind is used.

**REV-06 — Explicit Delete only after human decision.** Cancel, close the popup, or encounter an error while adding replacements: C-old persists. After reviewing the newly added Claims, the person may explicitly retire/delete C-old via Claims Editor with confirmation; if the replacements are not yet checked, show a warning. C-ok and unrelated Claims remain untouched. No automatic deletion of old Claims is allowed.

**REV-07 — Rerun and seal boundaries.** Running Checks after Add/Delete produces a new result; it does not alter the old run or Claim files and does not delete an existing Review report. New Claims are individually reviewed/signed in Claims, and the new final Review report is separately compiled, given human decision text and signed. Neither seal converts an unexecuted or failed Check into `pass` nor asserts legal conformity.

**REV-08 — Existing report survives a new Check run.** Start with signed report A, then run B. A remains readable/verifiable and is shown as an older run; `same_run` is false. The current `/check` deletion violates this test and must be corrected. Compiling B is explicit, requires confirmation if it replaces a saved report, and produces unsigned B without silently copying A's decision. Multi-report historical retention beyond the single path is separately unresolved.

**REV-09 — Missing Check coverage and source drift.** Selected Requirements with no executed Claim/Checks are shown as not checked. If Claim bytes differ from the digest recorded in the run, Compile fails instead of embedding different evidence. Discovery greying cannot conceal that mismatch; report signing is no conformity decision.

**REV-10 — UI and CLI/domain equivalence.** The same Check/Claim/Compile/Review callable operations work without HTTP. The popup is a presentation integration and does not add a new backend evaluation engine. Returning to Review after unsuccessful Discovery preserves the unresolved failed row. Existing Requirements one-Requirement Try Discovery is a reuse source, not a requirement to put Claim business logic in Requirements.

## Deliberate exclusions

No separate Finder, Reconcile or Relocate module. No automatic Claim rebinding or retirement. No automatic compliance declaration. No new Packs v2 fields or new persistent workflow state. Durable per-Claim Keep/Re-hunt marks across runs and automatic human-review currency are outside the agreed pilot scope; do not claim them as passing tests. The original PoC1 `state.json` and artificial `scan.json` remain non-normative historical references.

## Verification and completion

Each case needs a deterministic automated assertion on the relevant domain and UI boundary, including error/cancel paths. Record observed result, test command, environment and pass/fail/not-implemented status. Do not mark an unimplemented popup/hook as passed because the documents describe it. Execute a real Check runner for run-result semantics. Live-LLM or external repo tests are not required for these assertions.
