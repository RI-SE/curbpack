# Review — Studio component architecture

**Status:** Target functional contract, updated 2026-11-06 for EP-02, VR-00 and revised EP-11. The existing implementation and previous legacy PoC2 assertions below are migration/test evidence, not overriding architecture. Persisted contracts are governed by `docs/reference/packs2.md`, output contracts and current `docs/reference/workspace.md`. `review_item` is defined in `docs/reference/studio-internal.md`. Review and remediation are two configurations of the same queue. Review edits the decision. Remediation edits the Check, rebind, and Discover, and records Retire as `action` `retire` on `remediation_history`.

## Responsibility and boundaries

`studio/review/` owns human inspection of existing Run Results and compiled reports, review decisions, verification readings, Review report signatures, and read-only historical traceability (VL-05). It **does not** execute Checks, create Run Results, assemble reports, render PDFs, edit Claims, or change Requirements.

| Component | Responsibility |
|---|---|
| `curbcheck/` | Executes Checks and records Run Results |
| `studio/compile/` | Builds unsigned validated review reports and renders JSON/PDF |
| `studio/review/impl/` | Loads/inspects reports, records decisions, verifies/signs reports, resolves history |
| `studio/review/router.py` | Thin REST endpoint adapter to Review backend operations |
| `studio/review/pages/` | Thin TypeScript UI for inspecting evidence and taking explicit actions |
| `studio/claim/` | Claim editing/signing and Discovery; callable by Review UI navigation, never reimplemented in Review |

Review uses `studio/app.py` only for router registration. No Review domain logic lives in a central server or page template. Optional Review CLI calls the **same backend operations** as REST. The user may open Claim Discovery from a failed Check; it is the existing Claims-owned Discovery flow, not a Review search engine.

## Review operations

| Operation | Behavior |
|---|---|
| Open Run Result / report | Read exact selected persisted records; do not assume newest means same run |
| Inspect Claim and Requirement | Display what the run actually evaluated, including Check arguments and recorded outcomes |
| Record decision | Explicit human text on an unsigned draft. A report that already has `signed` is unchanged; the operation is rejected. A later decision is a newly compiled report. |
| Verify signatures | Reuse VR-00's independent embedded/Git reading, never imply approval from a seal |
| Sign report | Sign an unsigned draft that already has a decision. A second signature on that file is rejected. Signing does not sign Requirements or Claims. |
| Resolve historical chain (VL-05) | Backend-only read-only exact identity/digest lookup, local Git fallback, report every missing/stale link and verification method |

Compile and Review are **separate components**. `compile_report`, `write_report` and PDF rendering move to Compile. `record_decision`, `sign_report` and signature inspection remain Review operations. Review may call Compile's public backend operation at the user's explicit request to create an unsigned report; it does not own that implementation.

## Historical chain resolution (VL-05)

Review's backend resolver starts from a selected Run Result, resolves the recorded Claim and its bound Requirement using **both qualified identity and exact digest**, searches local Git history when current objects differ, and reports the verified recovered commit where available. It compares recorded Check configuration and outcomes without recomputing the historical run. Missing or changed objects are independently reported and do not suppress other links. A Git match proves recovered bytes, not that those bytes were signed; perform separate VR-00 verification. Read-only resolution never mutates Packs, Claims, results, reports or Git. The UI only displays the backend findings and invokes existing comparison for historical vs current Requirements.

## Report

One object. The embedded Requirements and Claims are the Packs v2 objects that were loaded, so a reviewer who has this file can read `references[].law_text`, Claim `args`, and those `signed` blocks. They are copies bound to this run. They are not the live files, and compile does not write the live files back.

```json
{
  "run_result": { },
  "requirements": [ ],
  "claims": [ ],
  "assessments": [],
  "remove_retired_checks": false,
  "decision": "the reviewer's own words",
  "signed": { "at": "…", "name": "…", "signature": "…" }
}
```

`decision` is absent until `record_decision`. `signed` is absent until `sign_report`. `remove_retired_checks` is absent unless an assessment is `retire`; the example includes it because that assessment is present.

| Field | Why it is here |
| --- | --- |
| `run_result` | The result that was reviewed. Compile copies it. Review does not produce another. |
| `requirements` | `law_text` and the Requirement seal. One object per Requirement version recorded on the embedded Claims, in the order those versions first appear. The same `requirement_id` may occur more than once. A Claim links to the object whose digest equals its `requirement_digest`. |
| `claims` | The Claim seal and the args. One object per run-result row, in row order. |
| `assessments` | Optional. `accept` or `must_fix` for a recorded deviation, or `retire` for any Check on this run. Accept on a failing Check includes the reviewer's text. A binding cannot be retired. Absent means Not assessed. Inside the version digest. Not copied to another run. |
| `remove_retired_checks` | Present only when an assessment is `retire`. `true` or `false`. Inside the version digest. `true` is applied to live Claim files after the report signature is written. `false` is the record only. |
| `decision` | The reviewer's words for the whole report. Inside the version digest. |
| `signed` | `review-sign`. Same shape as every other seal. |

`run_result.packs` contains recorded Pack identity and version/digest data defined by the currently approved output contract (extended by VL-00/VL-04 where specified). The report does not embed `pack.json`. When the pack directory is available, the page calls `read_pack_seal`. The collection identity on the report is the run result's `packs` entry.

The presentation derives explanatory observations from recorded result facts without changing them. From `worktree` `dirty`: the result is not verification of that commit's content. From `worktree` `clean`: the worktree was clean. Beside the decision field, the page states that a passing check does not mean the legal requirement is fulfilled, and that the report has no field for a conclusion that the product meets CRA.

### Validation

`validate_report` follows the current human-approved report contract; it rejects unknown/unapproved keys. The keys it rejects include `packs`, `git_note`, `limits`, `exit`, `compliant`, and `meets_cra`.

For a report that compile returns:

- `run_result` passes `validate_run_result`.
- For each run-result row whose Claim is embedded, `version_digest` of that Claim equals the row's `digest`, and each nested Check `index`, `check`, and `args` equal the configured Check.
- Claims resolve to exact qualified Requirement identity and digest after VL-04; historical objects use VL-05 resolution. Before that implementation, retain existing output validation without silently substituting different current objects.
- Each embedded Requirement passes `validate_requirement`. Each embedded Claim passes `validate_claim`.
- `appendix` lists executed Claims that are unsigned or whose signature does not verify, with Claim id, Requirement id, and the reading's reason. It is not part of `run_result`. A Claim with no Checks is outside the appendix.
- `decision` and `signed` are absent.

Compile must not silently embed a Claim different from the one recorded in the run. Historical resolution under VL-05 can recover the exact earlier object and report an unresolved link when history is absent. A previous report file is never silently destroyed. This is a Compile input rule, not Review-owned compilation logic.

`record_decision` requires non-empty words and strips them. It rejects a report that already has `signed` and does not write. On an unsigned draft it sets `decision`. Embedded Requirement and Claim `signed` blocks stay. `sign_report` requires `decision` and `run_result`, rejects a report that already has `signed`, then calls `sign_object`. An empty signer name fails before a write, the same way the other seals do.

`load_report` runs `validate_report` and, when `decision` or `signed` is present, requires a non-empty `decision`. A `signed` block is the usual seal check.

### Signature

The five facts are `packs2.md` §2.6 with `what` set to `review report`. The version is `version_digest` of the report. That digest covers `run_result`, the embedded objects, `assessments`, `remove_retired_checks`, and `decision`. It is not the Requirement digest and not the Claim digest.

VR-00's shared verifier reads embedded object signatures and eligible trusted signed Git-commit evidence independently, reporting valid, invalid or unsigned and the method/reason. An invalid embedded block is never masked by a valid Git signature. The Git author string is not the signer. When neither exists, the report is unsigned.

The Review backend verifies an embedded Requirement or Claim using the available embedded signature and eligible signed-Git evidence according to VR-00. A standalone report may not provide the repository context required to verify a Git-based seal; explicitly report verification unavailable rather than silently declaring unsigned or valid.

Signing the report does not sign the Requirement or the pack. It does not sign a Claim unless `remove_retired_checks` is true. In that case the report is signed first. The same signer then removes the retired Checks from the live Claims, signs a Claim that still has a Check, and deletes a Claim that has none. The embedded Claim and the Check result stay as compiled. A live Claim that does not match the run is a conflict: nothing is signed and no Claim file is changed. A Claim write that fails after the report signature leaves that report signed and names every Claim that was not updated. The same review-sign action retries only those Claims. The organisation chooses who holds the key. The report has no role field.

### A later run

`same_run(report, run_result)` is true when the report's `run_result` and the loaded run result compare equal. The cover and the review page both use it. Nothing stores the flag.

A check run **must not write or delete** the saved report. After a different result is written, Review must distinguish the earlier signed report from the new run; `same_run` is a relationship between snapshots, not a review-currency or compliance verdict. **Compile** can replace the single durable file with a new unsigned report and no `decision` only after explicit confirmation. Preserving prior bytes requires the configured retention behavior or committed Git history; do not infer that an uncommitted overwritten file can be recovered. Compiling the same run also requires confirmation; prior decisions are not copied forward.

Opening Review without a report does not write anything. A preview may be requested from the Compile backend; explicit Compile creates the unsigned report. **Save decision** and **review-sign** operate on a selected saved report.

## UI

Review owns its thin TypeScript presentation under `studio/review/pages/` and REST endpoints under `studio/review/router.py`. A Compile action exposed on the Review page invokes **Compile-owned** backend operations via the appropriate REST/API interface. The legacy `poc2/review/ui/`, `poc2/app/pages.py` and central routing are migration sources, not targets.

The page renders the report and posts the decision and the signer name. It does not evaluate checks, edit Claim `args`, or edit a Requirement.

**Shown.**

- The five-fact reading of the report file, or "not saved" for a preview.
- When a current run result is loaded, whether `same_run` is true.
- Each row: Claim status, and each Check's index, id, status, and detail, plus the matching Claim's source `args`, severity, and seal reading. A `fail` and an unsigned Claim stay separate. The signature appendix is that second list.
- Each embedded Requirement: id, locators, `law_text`, and seal reading.
- `run_result.packs`: id, `version`, digest. The pack-seal line when the directory is available.
- `commit` and `worktree`, plus the dirty or clean sentence.
- The two standing sentences about what a passing check does not mean.
- Selected Requirement ids that have no row, computed from `curbpack.json` and the embedded Claims. The line says they were not checked. The words about them belong in `decision` if the reviewer wants them recorded.

**Actions.**

| Action | Function | Result on the page |
| --- | --- | --- |
| Compile | Call the `studio/compile/` operation explicitly. | A new unsigned report, without a decision. A Retire confirmation can cancel that write. The removal choice is stored on the report and is not applied yet. |
| Save decision | Review-owned decision operation and shared persisted report IO. | The decision is saved on an unsigned draft. A signed report is rejected and left unchanged. |
| review-sign | Review-owned signing operation and shared report IO. | Signs the report. Requirement signatures stay. Claim files change only when `remove_retired_checks` is true, and only after that signature. A finished signed report is not signed again. An unfinished removal keeps review-sign for the remaining Claims. |
| Open the Claim | Navigation. | Claims Editor for this Claim; Return preserves the Review context. |
| Discover again | When the page has a Discovery source and timestamp, the UI opens the existing one-Requirement Discovery as a popup. Otherwise it links to Discover. | The failed Claim and its original Check statuses remain visible. No mutation on open or on following the link. |
| Run checks | Navigation. | The check page; a new result must be rendered before claiming a replacement passes. |

`ModelError` and `SigningUnavailable` are the red error. A refusal before the report signature leaves the report and the Claim files unchanged. A Claim write that fails after the signature leaves the signed report in place. Unsaved decision text is the textarea. The report file changes only after `write_report` returns.

The inputs for `check` and `args` are not on this page. A signed report shows the decision as text. Compile writes a new unsigned file and leaves the signed report unchanged.

### Review a failed Claim by discovering replacement evidence

This is the required **PoC1-style follow-up**, implemented using the existing Claims Discovery and Claims Editor rather than a new Reconcile/Finder/Relocate subsystem:

1. Render each Claim in the review queue with its Requirement, original source path, Check IDs, arguments, statuses and failure details. A failed or skipped Check keeps Accept and Must be fixed. A passing Check stays in the same table with Passed and Retire. The Check result and the report keep the recorded status. A `fail` is never converted to `pass` merely because the reviewer retained it or opened Discovery.
2. **Discover again** opens Discovery for that **one Requirement** as a popup. The old Claim and its Checks remain available behind the popup. No copying of Claims into the Discovery core; closing/canceling makes no changes. Show a short instruction to find equivalent evidence and configure suitable Checks.
3. The **Claims-owned UI presentation hook** (see [`../claims/ARCHITECTURE.md`](../claims/ARCHITECTURE.md)) greys, but never suppresses, candidates already matched to Claims whose configured Checks pass in the relevant run. Unchecked, stale, failed, skipped and ambiguous candidates are not greyed. This is not a green light for legal compliance, and not a new retrieval strategy.
4. The human inspects candidates, chooses appropriate Checks, and **adds one or more new Claims** via Claims. The failed original is **not** automatically edited or deleted; adding candidates without suitable Checks is not verification.
5. The human may **explicitly delete/retire** the replaced old Claim in Claims Editor after confirming replacement. Any not-yet-verified replacement is identified as such. Canceling, an empty search, or an Add failure leaves the old Claim intact. A prior signed report remains evidence of its original run and is never rewritten.
6. Run Checks again and inspect the new result. Review and sign the new Claim(s) separately in Claims; then Compile/Review can record and sign the **new human decision** for that new run. Neither operation silently copies the old report decision or turns a Check outcome into a claim of conformity.

The visible Check failures and ordinary persisted Claims supply the actionable state. The review report retains the free-text `decision` and may retain `assessments` for the Checks of that run, including a passing Check marked Retire. Those assessments are not a second queue and are not stored in `state.json`. Do not infer human-review currency solely from pass, worktree cleanliness or signatures.

## PoC1

PoC1 review is `poc/components/review/ui.py` on port 8767, fed by `scan.json`. The SCAN panel on the requirement catalog starts that demo and does not run a checker. `state.json` stores keep, re-hunt, a signed flag, and check edits. `/remedy` is a closing page. legacy PoC2's review page shows one report for `CRA-ANNEX-VII-RISK` and can sign it.

| Capability | Decision | Why |
| --- | --- | --- |
| See which evaluated rows failed, and keep them on screen | Retain | The rows are the run result. A `fail` stays a `fail`. |
| Read the passage and the path the check used | Adapt | `law_text` and Claim `args` on the report. PoC1 also showed a claim slug and a locus column. |
| Record a human conclusion and sign it | Adapt | `decision` and `review-sign`. PoC1's Sign off opens `/remedy` and stores `signed_off` in `state.json`. |
| Leave a binding as it is | Retain | No action. The Claim file stays. |
| Look for evidence again after a red check | **Retain and simplify** | Open the existing one-Requirement Discovery in a popup, grey already-checked evidence through a presentation hook, add one or more replacement Claims, delete the old Claim in Claims Editor, rerun Checks, then sign. No new finder. |
| Change `check` or `args` from the review card | Drop | Claims Editor writes the Claim. This page links there. |
| Rewrite a path to a `_new` suffix as a re-point | Drop | `rehunt_repoint_path` only renames a demo string. The person edits `args` in the Claims editor. |
| Persist individual Keep/Re-hunt marks across runs | Recorded on the review report as `assessments` | Accept, Must be fixed, and Not assessed apply to deviations of the selected run. There is no `state.json`, no review queue, and no copy of those assessments onto another run. |
| Toggle a signed flag on the Requirement | Drop | The Requirement seal and the Claim seal are the other activities. |
| Prepared `scan.json` and the SCAN theatre | Drop | The check runner writes the run result. |
| Remedy page | Drop | The signed report is what the reviewer can hand on. |

## Acceptance tests

1. `compile_report` on a two-Claim run embeds those Claims in row order, embeds the one Requirement they name, copies `run_result`, and omits `decision`, `signed`, `git_note`, `limits`, and `packs`.
2. A Claim file whose `version_digest` differs from the row fails compile. The previous report file is unchanged.
3. A report that contains `compliant` or `meets_cra` fails `validate_report`.
4. `record_decision` with blank text raises. With text, it sets `decision`, removes the report `signed`, and leaves the embedded Requirement `signed` in place.
5. `sign_report` without `decision` raises. With `decision`, `read_report_signature` is verifiable for that name and key, `what` is `review report`, and the version digest differs from the embedded Requirement's version digest.
6. A dirty run's report has `worktree` `dirty` and no `git_note` key. The review page's HTML contains the sentence that this is not verification of that commit's content.
7. After a new run result is written, `same_run` is false and the report file is still present. Compile then writes an unsigned report whose `run_result` equals the new result.
8. A handler test posts a decision and asserts `record_decision` received that text and that the handler did not call `run_and_write`.
9. UI integration tests demonstrate failed Claim context retained behind the Discovery popup; candidates are greyed only on verified matching passing Check rows for the same Requirement/repo; Add creates one or more new Claims; original Claim requires explicit retire; cancellation changes nothing; later Check/Claim-sign and final Review-sign remain separate. See `poc2/tests/Review_ACCEPTANCE_SCENARIOS.md`.

## Historical code notes (not a target contract)

`compile_report` copies `packs`, sets `git_note` from `worktree`, sets `limits` to the two standing sentences, checks an embedded Claim's digest and nested Checks against its row, and writes `appendix` for unsigned or unverifiable executed Claims. `current_report` in `poc2/app/server.py` loads the Packs named by the product `curbpack.json` when those directories exist. `read_report_signature` does not take a repo. Check leaves the report file in place. The review page shows the failed Claim, its Checks, and a Discovery popup for that Requirement. It still writes `.curbpack/review-report.json`. It does not show `same_run`, and it does not ask before a new decision replaces the saved report.

## Historical gaps (verify against current code before scheduling)

- **Implemented in the current UI, still short of this contract:** the one-Requirement Discovery popup, the Check-result grey-out on that presentation, and Add → explicit Retire → Check → Claim sign → report sign. The page still has no separate Compile action. Saving a decision writes the preview. `same_run` is not shown, and replacing a saved report does not ask for confirmation.
- **Durable path not yet written:** the server still uses `.curbpack/review-report.json`. The approved file is `docs/reports/review-report.json` in the product repository. Check must keep whichever file is the saved report. Git history of the durable file, after the user commits it, is the retention. legacy PoC2 does not commit and does not store another copy.
- **Intentionally deferred:** durable per-item Keep/Re-hunt marks and automatic review-currency inference. Do not mark those features implemented or invent persistence solely for them.

The reviewer's authority is the organisation's choice of key. The report does not record it.
