# Evidence

Evidence is material in a product repository that a Claim points at and that a Check inspects.

It can include documentation, manifests, dependency files, or any other path the Claim's arguments name. An SBOM is product material when a Claim names it. Studio does not build a CycloneDX or SPDX document as part of a Check run.

```text
Requirement
  ↓
Claim: this evidence, this rationale, these checks[]
  ↓
repository file at the configured path
  ↓
Run curbcheck
  ↓
pass / fail / skipped
  ↓
review report
```

## Evidence and results

Evidence is not the result of checking it.

```text
Requirement:
the product's security reporting is described

Claim checks:
exist paths ["SECURITY.md"]
contents path "SECURITY.md", probes for the heading "# Security"

evidence:
SECURITY.md

result:
pass on both Checks
```

A passing result means those arguments held for the bytes that were read.

It does not mean that every statement in the file is correct, complete, current, or sufficient for a legal, safety, security, or release decision. The Annex VII walkthrough in `docs/concepts/end-to-end-scenario.md` uses the same distinction: a file can have the required headings and still be a rewritten template. The reviewer reads `law_text` and the file. No Check decides that the assessment is an assessment.

## What each Check asks

| Question | Check |
| --- | --- |
| Is the file present? | `exist`, argument `paths` |
| Is it long enough, does it contain these headings, a token, a forbidden pattern, or placeholder text? | `contents` probes `size`, `words`, `headers`, `token`, `pattern`, `placeholder` |
| Is a dependency pin forbidden? | `dep_ban`. `npm_dep_ban` and `manifest_dep_ban` are aliases. This build does not run it; the row fails as not implemented |
| How old is the last commit that touched the file? | `git_fresh`, with `path`, `max_age_days`, and `as_of`. This build runs it |
| Did Git accept a signature on that commit? | `git_signed`. This build does not run it; the row fails as not implemented |
| Who is the recorded author? | `git_author`. This is not a signature. This build runs it |
| Who is the verified signer? | `git_signer`. This is not the author. This build does not run it; the row fails as not implemented |

`headers` are literal substrings, not regular expressions. `pattern` fails the Check when the expression matches. `placeholder` fails when the file matches this build's placeholder list in `checks/run.py`.

A missing required file is `fail` on every Check that ran against it, including `contents`. The `contents` detail says the file is absent and does not add a header miss. `skipped` is a reason the person supplied for that run. An empty reason is rejected. `skipped` is never rewritten to `pass`.

A structural pass does not answer the cited instrument. The report states that beside the decision.

## Evidence changes with the repository

A run result describes the working tree that was checked.

When Git has a HEAD, the result includes `commit` and `worktree` (`clean` or `dirty`). A dirty tree is allowed. It is not presented as verification of that commit's bytes. A directory that is not a Git checkout omits both keys. Signing a Requirement or a report does not commit. Git history is something the person maintains.

Rename `SECURITY.md` and the Check that names it fails. Restore the name and run again. Change a heading that a `headers` probe names, and `contents` fails while `exist` can still pass. Restore the file with a path-specific restore. A blanket `git restore .` can discard unrelated work.

A previous passing result does not say that a later tree still passes. A previous signed report stays the report of its own run until someone compiles again. Compile shows a checkbox, `Replace the saved report. The previous decision is not copied.`, when a report file already exists. Saving a new decision on that file does not ask a second time, and it removes the report signature. The new sentence is not the old seal.

## Review material

Compile packages the run that happened so another person can read it without re-running Check. The embedded Requirements and Claims are copies bound to that run. Compile does not write them back to the live files.

The reviewer can still run Check against the commit the team points at. Opening the report is not that run.

For a failed Claim, Review can open Discovery for that one Requirement while the failed row stays visible. The person adds one or more new Claims and, after confirming the replacement, retires the old Claim. Nothing is retargeted automatically. The record is the visible Check rows, the Claim files, and the free-text `decision`.

The report rejects keys that would turn it into a compliance verdict, including `compliant` and `meets_cra`.
