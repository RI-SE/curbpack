# Discovery motivation beside a saved claim

## Problem

The requirement page lists discovered evidence source candidates. A requirement can already have claims, including signed ones. A later discovery run must show the new candidate text against the saved motivation, and must leave claims that this run did not find.

## Decision

Claims and this run's visible candidates share one list. The claim field `description` is the saved motivation. The discovery field `why` is the candidate sentence. The claim file has no `why` field. Choosing the candidate copies those words into `description`.

No new claim fields. Rank, score, excerpt, and useful/poor stay off the claim.

## The shared list

The list is the union of:

- visible candidates for this requirement from the latest discovery job, including a file added by hand;
- every claim whose `requirement_id` is this requirement.

A claim is matched to a candidate by path. The claim path is `args.path` when that value is a non-empty string. Otherwise the claim has no candidate match and stays as a claim-only row.

Candidates the assessor dismissed are not visible rows. A claim for such a path is a claim-only row.

Order: candidates keep today's score order. Claim-only rows follow, ordered by path.

The page label for `description` is **Motivation**. The stored key remains `description`.

The grey "Already covered — passed in the selected Check run" note stays as it is when the page is opened from review. It does not replace the text pair below.

## When the texts differ

Compare `description` and `why` after stripping leading and trailing whitespace.

| Row | What the Motivation cell shows |
| --- | --- |
| Claim and candidate, texts equal | The motivation once. No red/green pair. |
| Claim and candidate, texts differ | Saved `description` in red with a line through it. `why` in green. |
| Claim, no visible candidate | The saved motivation only. The row stays. |
| Candidate, no claim | `why` in green. |

A blank or missing `why` is not a green alternative. The row shows the saved motivation only.

A file added by hand with no model `why` and no claim shows the typed rationale as ordinary text, not as a red/green pair.

## Writes

Keeping the red text writes nothing. A signed claim stays signed. The pair remains on the next load. There is no dismissed-change flag.

Choosing the green text on an existing claim sets `description` to that `why` string. `source`, `args`, and `checks` stay as they are. `why` is not stored on the claim.

Typing a different motivation uses the same write, with the typed string as `description`. The field starts filled with the current `description`. A save whose stripped text equals the saved `description` writes nothing.

If the claim has a `signed` block and the new text differs from the saved `description`, the page asks first: "This claim is signed. Saving replaces the motivation and removes the signature."

- **Save and remove signature.** One write stores the new `description` and removes `signed`.
- **Cancel.** The claim file is unchanged.

The server accepts that write only when the request carries an explicit unsign confirmation. A write that would change a signed claim without that confirmation does not touch the file.

An unsigned claim stores the new `description` immediately. No question.

A candidate with no claim does not create a claim file. A motivation typed on that row is stored as the finding's human rationale and is what `description` becomes when a check creates the claim. With no typed rationale, `description` becomes the green `why`.

A claim-only row is not rewritten by discovery.

After a successful choice, a later load compares the new `description` with the current `why`. Equal texts show one motivation.

## Checks

Saving a check on an existing claim updates `checks` only. It does not replace `description` with the current `why`.

If that save would change a signed claim, the page asks: "This claim is signed. Saving this check removes the signature."

- **Save and remove signature.** One write stores the new `checks` and removes `signed`. `description` is unchanged.
- **Cancel.** The claim file is unchanged, and the new check is not kept in discovery feedback.

An unchanged check list does not ask and does not rewrite the claim.

## What stays untouched

A discovery run does not create, rewrite, or delete claim files. A claim file changes only when the user saves a motivation or saves a check. A signed claim requires the matching confirmation before either save.

A signed claim whose file bytes do not change keeps its seal. `rebind` remains the way a changed payload drops `signed`.

## Errors

- Cancel, or a missing unsign confirmation, leaves the claim file bytes as they were.
- A failed validation leaves the claim file as it was.
- The motivation question and the check question are separate. One confirmation does not approve the other change.

## Tests

1. Signed claim, `why` equal to `description`: one motivation, claim file unchanged.
2. Signed claim, texts differ: red struck `description`, green `why`, claim file unchanged before a choice.
3. Choose the green text and confirm: `description` is that `why`, `signed` is absent, `source`, `args`, and `checks` are unchanged.
4. Choose the green text and cancel: claim file bytes unchanged.
5. A signed write without the unsign confirmation: claim file bytes unchanged.
6. Unsigned claim, choose the green text: `description` updated, still no `signed` block.
7. Claim path absent from visible candidates: the row is present, claim file unchanged.
8. Candidate and no claim: green `why`, no claim file until a check is saved. The saved claim's `description` is that `why`, unless the user typed a motivation, in which case the typed text is `description`.
9. Saving a check on a claim whose `description` differs from the current `why` leaves `description` as it was.
10. Saving a changed check on a signed claim asks first. Cancel leaves the claim file and the feedback checks unchanged. Confirm stores the checks and removes `signed`.

## Out of scope

Renaming the JSON key `description`. Storing rank or `why` on the claim. Remembering that the user ignored a green sentence. Changing the score column. Automatically retiring a claim that this run did not find.
