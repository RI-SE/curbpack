# Compile and final review

Status: **normative target, reviewed against PoC1 and the current PoC2 code (21 October 2026)**. Existing implementation deviates in places described under Current code. The report and signing contracts remain governed by Packs v2. The Review page opens the existing one-Requirement Discovery in a popup. The durable report path below is a design decision and is not the path the current server writes.

Normative domain model: `docs/reference/packs2.md` in this repository. The report uses the same `signed` shape as a Requirement (§2.6). Its body is the run result (§3.1) plus the reviewer's words. This file specifies how those are assembled. It is not a second run result and not a second Requirement or Claim.

Sibling documents:

- `poc2/checks/ARCHITECTURE.md` — the only writer of a run result.
- `poc2/claims/ARCHITECTURE.md` — Claim sealing (`sign_claim`). Final review reads that seal and does not write it.
- `docs/arch/ARCHITECTURE.md` — the cover page and the product scenarios.
- `poc2/tests/Review_ACCEPTANCE_SCENARIOS.md` — testable behavioral acceptance for Review/Discovery integration, not a second normative architecture.

This activity is final human Review of a Check run. Claims Review in the Claims document is a separate Claim-sealing action; the older Curbpack CLI `review` for deterministic document/reference inspection is not the final human Review UI.

## Two activities

Compile and final review share one JSON file. They are separately callable. Compile does not record a decision. Final review does not run checks.

| Activity | Function | Writes |
| --- | --- | --- |
| Compile | `compile_report(run_result, requirements, claims)` | An unsigned report with no `decision`. |
| Compile | `write_report(path, report)` / `load_report(path)` | That file, after `validate_report`. |
| Final review | `record_decision(report, text)` | The same report with `decision` set and `signed` removed. |
| Final review | `sign_report(report, *, name, private_key, at)` | The same report with `signed`. |
| Final review | `read_report_signature(report, trust, *, repo=None, relative=None)` | The five-fact reading. |

`compile_report` copies the run result. It does not call the runner and does not build a substitute result. A missing run result is `ModelError` on `run_result`. The caller loads the run result with `load_run_result`, loads each row's Claim from the product repo, and loads each of those Claims' Requirements from the pack directory. An existing report file is not an input.

The path is an argument. The durable file is `<product-repo>/docs/reports/review-report.json`. It belongs to the product repository, outside the Pack directory, so a Pack seal does not cover it. There is one current file and no report index. Earlier signed reports are that file's Git history after the user commits it. PoC2 does not commit, and it does not keep a second copy.

The current server still writes `<product-repo>/.curbpack/review-report.json`. That directory is temporary working data. The run result stays there. Moving the durable report to `docs/reports/` is this storage contract and is not yet what the server does.

The report identifies what was checked by the objects it already embeds. `run_result.commit` and `run_result.worktree` are the product revision Git reported for that run. `run_result.packs` carries each Pack id, version, and directory digest. The embedded Claims and their row digests are the Claims that ran. Committing `docs/reports/review-report.json` creates a later product-repo commit. That commit does not replace `run_result.commit`. When `worktree` is `dirty`, the recorded commit is not by itself the checked files. No new report field carries this.

## Report

One object. The embedded Requirements and Claims are the Packs v2 objects that were loaded, so a reviewer who has this file can read `references[].law_text`, Claim `args`, and those `signed` blocks. They are copies bound to this run. They are not the live files, and compile does not write the live files back.

```json
{
  "run_result": { },
  "requirements": [ ],
  "claims": [ ],
  "decision": "the reviewer's own words",
  "signed": { "at": "…", "name": "…", "signature": "…" }
}
```

`decision` is absent until `record_decision`. `signed` is absent until `sign_report`.

| Field | Why it is here |
| --- | --- |
| `run_result` | The result that was reviewed. Compile copies it. Review does not produce another. |
| `requirements` | `law_text` and the Requirement seal. One object per `requirement_id` on the embedded Claims, in the order those ids first appear. |
| `claims` | The Claim seal and the args. One object per run-result row, in row order. |
| `decision` | The reviewer's words. Inside the version digest. |
| `signed` | `review-sign`. Same shape as every other seal. |

`run_result.packs` already carries pack id, `version`, and the directory digest. The report does not embed `pack.json`. When the pack directory is available, the page calls `read_pack_seal`. The collection identity on the report is the run result's `packs` entry.

The page derives two sentences and does not store them on the report. From `worktree` `dirty`: the result is not verification of that commit's content. From `worktree` `clean`: the worktree was clean. Beside the decision field, the page states that a passing check does not mean the legal requirement is fulfilled, and that the report has no field for a conclusion that the product meets CRA.

### Validation

`validate_report` rejects an unknown key. The keys it rejects include `packs`, `git_note`, `limits`, `exit`, `compliant`, and `meets_cra`.

For a report that compile returns:

- `run_result` passes `validate_run_result`.
- For each run-result row whose Claim is embedded, `version_digest` of that Claim equals the row's `digest`, and each nested Check `index`, `check`, and `args` equal the configured Check.
- Each Claim's `requirement_id` is the `id` of exactly one embedded Requirement, and every embedded Requirement is referenced.
- Each embedded Requirement passes `validate_requirement`. Each embedded Claim passes `validate_claim`.
- `appendix` lists executed Claims that are unsigned or whose signature does not verify, with Claim id, Requirement id, and the reading's reason. It is not part of `run_result`. A Claim with no Checks is outside the appendix.
- `decision` and `signed` are absent.

A row whose Claim file is missing, or whose digest does not match, fails compile. The previous report file is left in place. The person runs checks again after changing a Claim. Compile does not embed a Claim that did not run.

`record_decision` requires non-empty words, strips them, and removes the report's `signed` only. Embedded `signed` blocks stay. `sign_report` requires `decision` and `run_result`, then calls `sign_object`. An empty signer name fails before a write, the same way the other seals do.

`load_report` runs `validate_report` and, when `decision` or `signed` is present, requires a non-empty `decision`. A `signed` block is the usual seal check.

### Signature

The five facts are `packs2.md` §2.6 with `what` set to `review report`. The version is `version_digest` of the report. That digest covers `run_result`, the embedded objects, and `decision`. It is not the Requirement digest and not the Claim digest.

When `signed` is present, `read_report_signature` reads that block. When it is absent and the caller passes the repo and the report's relative path, a signed Git commit of that file is the seal, through the same reading as `read_claim_signature`. The Git author string is not the signer. When neither exists, the report is unsigned.

The page reads an embedded Requirement with `read_signature` and an embedded Claim with `read_claim_signature`. A Claim whose only seal is a Git commit shows that commit when the product repo is available. A reviewer who has only the report file sees the `signed` block that was copied, and an unsigned reading when the Claim had none.

Signing the report does not sign the Requirement, the Claim, or the pack. The organisation chooses who holds the key. The report has no role field.

### A later run

`same_run(report, run_result)` is true when the report's `run_result` and the loaded run result compare equal. The cover and the review page both use it. Nothing stores the flag.

A check run **must not write or delete** the saved report. After a different result is written, Review must distinguish the earlier signed report from the new run; `same_run` is a relationship between snapshots, not a review-currency or compliance verdict. **Compile** can replace the single durable file with a new unsigned report and no `decision` only after explicit confirmation. The previous bytes remain available when the user has committed that file; PoC2 does not create that commit, and an uncommitted overwrite is not retained. Compiling the same run also requires confirmation; prior decisions are not copied forward.

Opening the review page when no report file exists shows a preview from `compile_report` and does not write. **Compile** is the write. **Save decision** and **review-sign** require the file.

## UI

Review owns this rendering, including the compile action on this page. Target path: `poc2/review/ui/`. Until migration the page still renders from `poc2/app/pages.py` `review_page`. The route stays in `app/`. Compile keeps the report functions in this file until that split; this page is not a second architecture document.

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
| Compile | `compile_report`, then `write_report`. | The new file. No decision, unsigned. |
| Save decision | `record_decision`, then `write_report`. | Flash that the decision was saved. A previous report signature is gone. |
| review-sign | `sign_report`, then `write_report`. | The report reading. Requirement and Claim readings are unchanged. |
| Open the Claim | Navigation. | Claims Editor for this Claim; Return preserves the Review context. |
| Discover again | UI opens the existing one-Requirement Discovery as a popup. | The failed Claim and its original Check statuses remain visible in the underlying Review context. No mutation on open/close. |
| Run checks | Navigation. | The check page; a new result must be rendered before claiming a replacement passes. |

`ModelError` and `SigningUnavailable` are the red error. A failed sign leaves the file unchanged. Unsaved decision text is the textarea. The file changes only after `write_report` returns.

The inputs for `check` and `args` are not on this page. A verified report is shown with the decision as text until the person compiles again or saves a new decision.

### Review a failed Claim by discovering replacement evidence

This is the required **PoC1-style follow-up**, implemented using the existing Claims Discovery and Claims Editor rather than a new Reconcile/Finder/Relocate subsystem:

1. Render each failed/skipped Claim with its Requirement, original source path, Check IDs, arguments, statuses and failure details. Keep the failed Claim visible. Passing Claims may be collapsed/filtered from the **Review working view** for focus, but remain in the underlying Check result and report. A `fail` is never converted to `pass` merely because the reviewer retained it or opened Discovery.
2. **Discover again** opens Discovery for that **one Requirement** as a popup. The old Claim and its Checks remain available behind the popup. No copying of Claims into the Discovery core; closing/canceling makes no changes. Show a short instruction to find equivalent evidence and configure suitable Checks.
3. The **Claims-owned UI presentation hook** (see [`../claims/ARCHITECTURE.md`](../claims/ARCHITECTURE.md)) greys, but never suppresses, candidates already matched to Claims whose configured Checks pass in the relevant run. Unchecked, stale, failed, skipped and ambiguous candidates are not greyed. This is not a green light for legal compliance, and not a new retrieval strategy.
4. The human inspects candidates, chooses appropriate Checks, and **adds one or more new Claims** via Claims. The failed original is **not** automatically edited or deleted; adding candidates without suitable Checks is not verification.
5. The human may **explicitly delete/retire** the replaced old Claim in Claims Editor after confirming replacement. Any not-yet-verified replacement is identified as such. Canceling, an empty search, or an Add failure leaves the old Claim intact. A prior signed report remains evidence of its original run and is never rewritten.
6. Run Checks again and inspect the new result. Review and sign the new Claim(s) separately in Claims; then Compile/Review can record and sign the **new human decision** for that new run. Neither operation silently copies the old report decision or turns a Check outcome into a claim of conformity.

**No automatic Keep/Re-hunt history is required for this pilot workflow.** The visible Check failures and ordinary persisted Claims supply the actionable state, while the review report retains only its existing free-text human `decision`. This explicitly does **not** reproduce PoC1's historical per-item action marks across sessions. The product owner chose the simpler, operationally sufficient workflow; do not resurrect `state.json` or extend Packs v2 to simulate parity. Do not infer human-review currency solely from pass, worktree cleanliness or signatures.

## PoC1

PoC1 review is `poc/components/review/ui.py` on port 8767, fed by `scan.json`. The SCAN panel on the requirement catalog starts that demo and does not run a checker. `state.json` stores keep, re-hunt, a signed flag, and check edits. `/remedy` is a closing page. PoC2's review page shows one report for `CRA-ANNEX-VII-RISK` and can sign it.

| Capability | Decision | Why |
| --- | --- | --- |
| See which evaluated rows failed, and keep them on screen | Retain | The rows are the run result. A `fail` stays a `fail`. |
| Read the passage and the path the check used | Adapt | `law_text` and Claim `args` on the report. PoC1 also showed a claim slug and a locus column. |
| Record a human conclusion and sign it | Adapt | `decision` and `review-sign`. PoC1's Sign off opens `/remedy` and stores `signed_off` in `state.json`. |
| Leave a binding as it is | Retain | No action. The Claim file stays. |
| Look for evidence again after a red check | **Retain and simplify** | Open the existing one-Requirement Discovery in a popup, grey already-checked evidence through a presentation hook, add one or more replacement Claims, explicitly retire the old Claim, rerun Checks, then sign. No new finder. |
| Change `check` or `args` from the review card | Drop | Claims Editor writes the Claim. This page links there. |
| Rewrite a path to a `_new` suffix as a re-point | Drop | `rehunt_repoint_path` only renames a demo string. The person edits `args` in the Claims editor. |
| Persist individual Keep/Re-hunt marks across runs | **Deferred by explicit product decision** | The pilot uses visible Check results, unchanged failing Claims until explicit deletion, and the normal signed report decision. It does not promise per-item history. Do not recreate `state.json`. |
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

## Current code

`compile_report` copies `packs`, sets `git_note` from `worktree`, sets `limits` to the two standing sentences, checks an embedded Claim's digest and nested Checks against its row, and writes `appendix` for unsigned or unverifiable executed Claims. `current_report` in `poc2/app/server.py` loads the Packs named by the product `curbpack.json` when those directories exist. `read_report_signature` does not take a repo. Check leaves the report file in place. The review page shows the failed Claim, its Checks, and a Discovery popup for that Requirement. It still writes `.curbpack/review-report.json`. It does not show `same_run`, and it does not ask before a new decision replaces the saved report.

## Unresolved and verified implementation gaps

- **Implemented in the current UI, still short of this contract:** the one-Requirement Discovery popup, the Check-result grey-out on that presentation, and Add → explicit Retire → Check → Claim sign → report sign. The page still has no separate Compile action. Saving a decision writes the preview. `same_run` is not shown, and replacing a saved report does not ask for confirmation.
- **Durable path not yet written:** the server still uses `.curbpack/review-report.json`. The approved file is `docs/reports/review-report.json` in the product repository. Check must keep whichever file is the saved report. Git history of the durable file, after the user commits it, is the retention. PoC2 does not commit and does not store another copy.
- **Intentionally deferred:** durable per-item Keep/Re-hunt marks and automatic review-currency inference. Do not mark those features implemented or invent persistence solely for them.

The reviewer's authority is the organisation's choice of key. The report does not record it.
