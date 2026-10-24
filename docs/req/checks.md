# Checks — derived system requirements

**Status:** Draft for review, **not** an approved implementation contract.
**Source:** [CHK-05](../agile/epics/01-pack-editor/stories/CHK-05-remaning-checks.md). CHK-02 is context for the existing runner only.
**External contract:** `docs/reference/packs2.md` in this repository, imported from Curbpack commit `b07b8deb9fed331b493241251087ce7ce648f5e4`. That commit records §4 and §4.1 for the four Git Checks. It, not this document, defines Claim `checks[]`, the Check registry, and the run result.

CHK-R01–CHK-R05 restate behavior already fixed by Packs v2 §2.5, §3.1, and §4, or by the current pilot tests. CHK-R06–CHK-R13 are the Git Check behavior the maintainer accepted on 2026-10-23. The plan is approved. CHK-R06’s schemas are registered. The other Git Check rows stay DRAFT until their own tests pass.

| ID | Status | Required observable behavior | Derived from |
| --- | --- | --- | --- |
| **CHK-R01** | DRAFT | `available_checks.json` may register more than one Check id on the same `command`. `validate_check_args` uses that id's own `args_schema`. An id absent from the registry is rejected when the Claim is saved. | CHK-05 acceptance 1; Packs v2 §2.5 |
| **CHK-R02** | DRAFT | A Claim holds Git Checks only as entries in the existing `checks[]` array: `{ "check", "args" }`. There is no grouping object, sub-check, or second Claim shape. One Claim may contain several entries, including repeated ids with different `args`. | CHK-05 acceptance 2; Packs v2 §2.4–§2.5 |
| **CHK-R03** | DRAFT | Each configured Check is executed on its own. The result has one Check object per entry, with `index`, `check`, `args`, and `status`. One Check's `fail` does not hide another Check's `pass`, and the reverse. Claim `status` stays the Packs v2 aggregate: `fail` if any Check fails, otherwise `skipped` if any is skipped, otherwise `pass`. | CHK-05 acceptance 3; Packs v2 §3.1 |
| **CHK-R04** | DRAFT | A Check result uses only `pass`, `fail`, or `skipped`. `detail` is absent on `pass` and required on `fail` and `skipped`. Unknown result keys are rejected. Compile copies that run result; Review does not invent a second one. A Check failure is not rewritten as a Claim-signature failure, and a Claim-signature gap is not rewritten as a Check failure. This requirement does not by itself identify the evidence path and the file's last-change commit. That is CHK-R11. | CHK-05 acceptance 7; Packs v2 §3.1; `common/validate.py` |
| **CHK-R05** | DRAFT | `exist` and `contents` keep their current Packs v2 behavior and tests. A missing file is `fail` and is not a pass. `fresh`, `owned`, and `dep_ban` stay non-passing until a later approved story implements a contract that already names them. | CHK-05 scope; `tests/test_m3_claims.py`; `tests/test_m4_checks.py` |
| **CHK-R06** | DRAFT | Packs v2 §4 changes first, in the Curbpack repository. Four Check ids replace the questions now named `fresh` and `owned`. One command, one args schema each. `owned` is not implemented. Studio does not register those ids while §4 still names `fresh` and `owned`. | CHK-05 acceptance 1–2; OPEN-1 accepted 2026-10-23 |
| **CHK-R07** | DRAFT | The relevant commit is the last commit reachable from HEAD that changes that path. Freshness, signature, author, and signer use that commit. History is not followed across a rename. A missing, untracked, or worktree-modified path is `fail` with a `detail` that names the condition. Example: `risk.md` last changed Monday, HEAD on Friday only changed another file, `max_age_days` is 2, and `as_of` is Friday: `git_fresh` is `fail`. | CHK-05 acceptance 4–5; OPEN-2 accepted 2026-10-23 |
| **CHK-R08** | DRAFT | Freshness compares the relevant commit's committer timestamp with required `args.as_of` (RFC 3339). Age in whole days is `floor((as_of - committer_time) / 86400)`. `pass` when that age is less than or equal to `max_age_days`. A committer time after `as_of` is `fail`. No wall clock. `since_ref` is out of CHK-05. | CHK-05 acceptance 5; OPEN-3 accepted 2026-10-23 |
| **CHK-R09** | DRAFT | Verification is a signature on the relevant commit that Git accepts with the product repo's existing SSH or OpenPGP trust, named in `args`. Missing signature, rejected signature, missing `git`, or missing trust input is `fail` with a `detail` that distinguishes those cases. No new trust store, no key fetch, and Claim `signed` is not a Git signature. | CHK-05 acceptance 5–6; OPEN-4 accepted 2026-10-23 |
| **CHK-R10** | DRAFT | The author Check compares author name and author email, each only when that argument is present, as exact case-sensitive strings, and does not verify a signature. The signer Check compares one identity string from a signature CHK-R09 has verified. The same author with a missing or different signer is `pass` for author and `fail` for signer. Neither Check reads the other's result. | CHK-05 acceptance 6; OPEN-5 accepted 2026-10-23 |
| **CHK-R11** | DRAFT | A passing Git Check keeps the existing result shape. The evidence path is the path in copied `args`. The checked revision is the run-level `commit` (HEAD), and CHK-R07 has required that path's blob at HEAD to match the worktree. The last-change commit id is named in `detail` only on `fail`. No new result field and no `detail` on `pass`. The part of CHK-05 acceptance 4 that asks a passing row to name the file's last-change commit is deferred. | CHK-05 acceptance 4; OPEN-6 accepted 2026-10-23 |
| **CHK-R12** | DRAFT | After `validate_check_args` succeeds, a Git Check returns `fail` with a specific `detail` for a missing path, a dirty or untracked path, absent Git metadata, a missing or rejected signature, a missing trust input, or an unavailable `git` binary. Invalid arguments are a validation `fail` and are never `pass`. `skipped` remains only the caller-supplied skip of the whole Claim. There is no fourth status. | CHK-05 acceptance 5; OPEN-7 accepted 2026-10-23 |
| **CHK-R13** | DRAFT | CHK-05 does not change `claims/ui/`. Tests call the runner with `checks[]` written in the test. The current form keeps saving `fresh` and `owned`, and those Checks stay non-passing. A user attaching the four Checks in the discovery form is a later story. | CHK-05 acceptance 2; OPEN-8 accepted 2026-10-23 |

## Already fixed — do not reopen in CHK-05

- The pilot registry already shares one command across `dep_ban`, `npm_dep_ban`, and `manifest_dep_ban` (`checks/available_checks.json`). That is the existing evidence for CHK-R01. It is not an implementation of the Git Checks.
- `checks/run.py` `_execute_check` returns `fail` with detail `check '<id>' is not implemented` for a registered id other than `exist` and `contents`. `tests/test_m3_claims.py` `test_unknown_check_is_rejected_and_unimplemented_does_not_pass` locks that for `fresh`. An unknown id raises `CheckError` from `validate_check_args` before a Claim is saved.
- `common/validate.py` rejects a Check result that has `detail` when `status` is `pass`, and rejects keys other than `index`, `check`, `args`, `status`, and `detail`.
- The run result already records `commit` (HEAD) and `worktree` (`clean` or `dirty`) when Git has a HEAD. A dirty tree can still exit 0 when every Check is `pass` (`tests/test_m4_checks.py`). Packs v2 §3.1 says that dirty result must not be presented as verification of that commit's exact content. The Check page states that. A per-file Git Check must not treat that run-level HEAD as if it were the file's last-change commit.
- `checks/ARCHITECTURE.md` disagrees with the code. The responsibilities section says an unimplemented registered id is a non-passing Check result. The "Checks this build runs" section says `fresh`, `owned`, and `dep_ban` raise `CheckError` before a result file is written. The code and `tests/test_m3_claims.py` follow the first sentence. Do not "fix" that contradiction inside CHK-05.

## Open decisions

Each proposal is one way to satisfy the story. It is not a schema. Implementation stops until the maintainer marks the item approved or explicitly defers the corresponding acceptance criterion.

### OPEN-1 — Check ids conflict with the published catalog

**Conflict**

- CHK-05 proposes `git_fresh`, `git_signed`, `git_author`, and `git_signer`, and says those names are not approved Packs v2 or catalog changes (`docs/agile/epics/01-pack-editor/stories/CHK-05-remaning-checks.md`).
- Packs v2 §4 already registers `fresh` (`path` plus `max_age_days` or `since_ref`: "Age of that file's last commit") and `owned` (`path`, `bind_repo_token: true`, optional git author `name` and `email`: "Git authorship of that path").
- The same story says not to implement the old `owned` Check under that name without an explicit Packs v2 compatibility decision.
- `checks/available_checks.json` already contains those `fresh` and `owned` schemas. The discovery form hardcodes both (`claims/ui/researcher.py`, `claims/ui/http.py`).

**Proposal:** Change Packs v2 §4 and the published catalog in the Curbpack repository first. Replace the Check questions now named `fresh` and `owned` with four ids, one command, and one args schema each. Do not implement `owned`. Do not add the four ids only in this repository's `available_checks.json` while §4 still names `fresh` and `owned`. Record the Packs v2 commit in `plan/CHK-05.md` before any studio test for those ids.

**Justification:** The story requires the catalog alignment before coding, and policy forbids a second persistent Check contract. Implementing either the proposed ids or `owned` from this draft would publish a catalog Packs v2 does not contain, or would implement the Check the story excluded.

**Maintainer decision (2026-10-23):** accepted.

### OPEN-2 — Relevant commit and working tree

**Unspecified:** which commit is "the" commit for a path, and what happens when the file is new, deleted, renamed, or modified in the worktree.

**Proposal:** For a run at HEAD, the relevant commit is the last commit reachable from that HEAD that changes the path, without rename following. Compare the worktree file to the blob at HEAD. If the path is untracked, missing, or differs from HEAD, the Check is `fail` and `detail` names that condition. A deleted or never-committed path is `fail`, not `pass`. A rename is a different path unless the maintainer later approves rename following in Packs v2.

**Justification:** CHK-05 forbids a false pass on dirty or missing evidence. Packs v2 already separates run-level HEAD from the content that was actually verified. This proposal does not add a field.

**Maintainer decision (2026-10-23):** accepted. The relevant commit is the one where the file was last changed. `risk.md` last changed on Monday with `max_age_days` 2 is `fail` when `as_of` is more than two days later. The missing, untracked, dirty, and rename sentences above stay in this decision.

### OPEN-3 — Freshness time

**Unspecified:** `as_of` versus the wall clock, author date versus committer date, the age boundary, and how the reference time is retained. Packs v2 `fresh` names `max_age_days` or `since_ref` and does not define either comparison. `since_ref` has no definition of ref type, timezone, or what "since" includes.

**Proposal:** Do not implement `since_ref` in CHK-05. Freshness compares the relevant commit's committer timestamp to an `as_of` instant that is required in that Check's `args` and stored as RFC 3339. The comparison is retained because `args` are part of the Claim digest and are copied onto the result. Age in whole days is `floor((as_of - committer_time) / 86400)`. `pass` only when that age is less than or equal to `max_age_days`. Equal to the boundary is `pass`. A future committer timestamp relative to `as_of` is `fail`. No wall clock is read.

**Justification:** A wall clock makes the same Claim and the same commit change result later, which breaks CHK-02's reproducibility sentence. Putting `as_of` in `args` needs no new result field. The boundary "less than or equal" matches a maximum age. This proposal still requires the Packs v2 catalog change from OPEN-1, because `as_of` is not in the published `fresh` schema.

**Maintainer decision (2026-10-23):** accepted.

### OPEN-4 — Signature verification and trust

**Unspecified:** SSH versus OpenPGP, what a verified signature is, and which trust configuration is used. The pilot signs Claims with local Ed25519 keys (`impl/pilot/IMPLEMENTATION_PLAN.md`). Those keys are not Git commit signatures. The same note says an unsigned Git commit leaves the Claim unsigned and that the Git author string is not the signer.

**Proposal:** Verify only a signature on the relevant commit that Git itself accepts for that repository's configured SSH or OpenPGP trust. The Check's `args` name the trust input that was already present in the product repo (allowed signers file or the repo's Git configuration). A missing signature, a signature Git does not accept, a missing Git binary, or a missing trust input is `fail` with a `detail` that distinguishes those cases. Do not embed a new trust store, do not fetch keys, and do not treat Claim `signed` as a Git signature.

**Justification:** CHK-05 separates signer trust from author identity. Inventing a trust store would be a new policy. Reusing Git's verification keeps the trust decision in the product repository.

**Maintainer decision (2026-10-23):** accepted.

### OPEN-5 — Author versus signer

**Unspecified:** the exact identity strings.

**Proposal:** The author Check compares the relevant commit's author name and author email, each only when that argument is present, as exact case-sensitive strings. It does not verify a signature. The signer Check compares one identity string taken from a signature that OPEN-4 has already verified. A matching author with a missing or different signer is `pass` for the author Check and `fail` for the signer Check. Neither Check reads the other Check's result.

**Justification:** This is the distinction CHK-05 acceptance 6 states. The exact signer string Git reports is still part of OPEN-4 and must be copied into Packs v2 before coding, not chosen while writing the test.

**Maintainer decision (2026-10-23):** accepted.

### OPEN-6 — Path and commit on a passing result

**Conflict:** CHK-05 acceptance 4 says the result identifies the evidence path and the relevant Git commit. Packs v2 §3.1 and `common/validate.py` omit `detail` on `pass` and allow no other Check-result keys. The run-level `commit` is HEAD, which is not the file's last-change commit when the path was last changed by an ancestor. Copied `args` can identify a path the user typed. They cannot record the commit the checker observed unless that commit was an input argument.

**Proposal:** Keep the result schema. Require the evidence path in `args`. On `pass`, the run-level `commit` is the revision that was checked, and OPEN-2 has already required the path's blob at HEAD to match the worktree. The last-change commit id is included in `detail` only on `fail`. Do not add an evidence object, and do not allow `detail` on `pass`, unless the maintainer first changes Packs v2 and `validate_run_result`.

If this proposal is approved, acceptance 4 is only partly met: the result identifies the path through copied `args` and the checked revision through run-level HEAD. It does not identify the file's last-change commit on `pass`. That part of acceptance 4 is deferred unless Packs v2 and `validate_run_result` change. The maintainer records that deferral with the same explicitness as OPEN-8.

**Justification:** A new field or a `detail` on `pass` is a published contract change. HEAD plus a clean blob for that path is the revision Packs v2 already records. If the maintainer needs the ancestor commit on a pass, that is a Packs v2 change and CHK-05 stops.

**Maintainer decision (2026-10-23):** accepted. A green row shows the path and HEAD. The last-change commit id is in `detail` only when the Check is `fail`. The passing-row half of acceptance 4 is deferred.

### OPEN-7 — Fail, skip, and execution error

**Unspecified:** the story says the precise handling follows the approved Check contract. Packs v2 has no status other than `pass`, `fail`, and `skipped`. `skipped` is already the caller-supplied skip map in `build_run_result`: every Check on that Claim is `skipped` with the typed reason, and the Check function is not called.

**Proposal:** Git Checks do not raise once the Claim has passed `validate_check_args`. Invalid arguments stay a save-time or validation `fail`, as `_execute_check` does today, and are never `pass`. Missing evidence, a dirty path, absent Git metadata, an unverifiable signature, and an unavailable `git` binary are `fail` with a specific `detail`. `skipped` remains only the existing caller skip. There is no fourth status.

**Justification:** This matches Packs v2 ("unavailable/unsupported execution must be explicit and non-passing") and the tested runner. Using `skipped` for a broken Git setup would look like the human skip action.

**Maintainer decision (2026-10-23):** accepted. A stale file, a missing file, an unsaved edit, missing Git, and an unverifiable signature are `fail` with a reason. `skipped` stays the deliberate Claim skip.

### OPEN-8 — Who configures the Checks

**Conflict:** Acceptance 2 says a user can attach and configure several Git Checks on one Claim. The out-of-scope section says no GUI redesign. Packs v2 §2.5 says Check configuration UIs read the registry rather than hardcoding argument fields. The pilot form hardcodes `fresh` and `owned` and tells the user those Checks are not evaluated yet.

**Proposal:** CHK-05 does not change `claims/ui/`. Configuration of the four Checks is a later story after OPEN-1 names the schemas. This story's tests call `run_claim` / `build_run_result` with `checks[]` written in the test. The existing form must keep saving `fresh` and `owned` exactly as it does now, and those saved Checks must remain non-passing.

**Justification:** A new form is a GUI change the story excluded, and the form cannot be drawn until OPEN-1 fixes the fields. Runner tests still cover the mechanical Checks. Acceptance 2's user-facing attach stays a later story.

**Maintainer decision (2026-10-23):** accepted. Acceptance 2 for the discovery form is deferred.

## Not in this document

- `dep_ban`, CVE, SBOM, and Trivy.
- Implementing `owned` under that name.
- A new Check framework, Claim schema, or EP-02 split.
