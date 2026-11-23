# Studio-internal structures

**Status:** Approved.

This document defines Curbpack Studio's internal data structures. This page defines `review_item`. Claim, Check, and signature are added to this document in a later step.

## review_item

`review_item` is the decision for one Check. `decision`, `priority`, and `comment` are written once and remain the next time the same deviation is found.

### Key and provenance

`key` names the Check within the product repository:

- `claim_id`, unique in that repository's Claim collection
- `check_digest`

`check_digest` is the SHA-256 hex of the canonical JSON of `{ "check": <id>, "args": <object> }`. The canonical JSON is the same one used for the version digest in Packs v2 §2.6: sorted keys, no insignificant whitespace, UTF-8.

A Claim has one Check per Check id and arguments.

Binding is an obligatory implicit Check on every Claim:

```json
{ "check": "requirement_binding", "args": {} }
```

Its `check_digest` is the SHA-256 hex of that canonical JSON. `key` is `claim_id` and that digest. The Requirement digest is in `provenance`.

`provenance` comes from the Run Result and is the circumstances at Check time.

- `requirement_digest` is the run's recorded `requirement_digest`.
- `git_commit` is the run's recorded `commit`.
- `dirty_git` is `true` when the run's `worktree` is `dirty`, and `false` when it is `clean`.
- `files` are the relevant files at Check time. Each entry has a path relative to the product repository. `size` is the file size in bytes at that run. `mtime` is the file's modification time at that run, UTC `YYYY-MM-DDTHH:MM:SSZ`.

The Run Result records `commit` and `worktree`. File `size` and `mtime` at Check time are not among the Run Result fields in [Outputs](outputs.md). When `dirty_git` is true and `files` is therefore absent, the decision is not reused.

### The same deviation

A judgment is reused automatically when `key` matches and the relevant provenance can be verified as unchanged. A value the comparison needs, and which is missing on either side, yields `False`.

`provenance` is compared when `key` matches. `files` are compared when `dirty_git` is `true` on either side.

```text
if previous.key != current.key:
    return False
a = previous.provenance
b = current.provenance
if a.requirement_digest is missing or b.requirement_digest is missing:
    return False
if a.requirement_digest != b.requirement_digest:
    return False
if a.git_commit is missing or b.git_commit is missing:
    return False
if a.git_commit != b.git_commit:
    return False
if a.dirty_git is missing or b.dirty_git is missing:
    return False
if a.dirty_git or b.dirty_git:
    if a.files is missing or b.files is missing:
        return False
    return same_file_metadata(a.files, b.files)
return True
```

`same_file_metadata` is true when both lists are present and contain the same set of `path`, and each path has the same `size` and the same `mtime`. Order does not matter.

A stored `decision`, `priority`, `comment`, and `remediation_history` remain when the predicate is false.

### Object

A missing key is omitted. Unknown keys are invalid.

```json
{
  "key": {
    "claim_id": "HOUSE-SECURITY-MD",
    "check_digest": "<sha256 of canonical {check, args}>"
  },
  "provenance": {
    "requirement_digest": "<run result requirement_digest>",
    "git_commit": "<run result commit>",
    "dirty_git": true,
    "files": [
      { "path": "docs/a.md", "size": 1204, "mtime": "2026-11-22T18:04:11Z" }
    ]
  },
  "decision": "must_fix",
  "priority": 1,
  "comment": "Add docs/a.md.",
  "assessed_at": "2026-11-23T05:20:00Z",
  "remediation_history": [
    {
      "at": "2026-11-23T08:15:00Z",
      "comment": "Added security documentation."
    }
  ]
}
```

`decision` is `pass`, `accepted`, `not_assessed`, or `must_fix`.

`remediation_history` is the sequence of remediations recorded for this decision, earliest first. Each entry has `at`, UTC `YYYY-MM-DDTHH:MM:SSZ`, and `comment`, the non-empty text of what was done. The key is omitted when the sequence is empty.

`priority` is an integer from 1 to 10. 1 is the most urgent.

- `pass` is the recorded Check outcome. `priority`, `comment`, and `assessed_at` are omitted.
- `accepted` means the reviewer has accepted the deficiencies the Check found. `priority` is set. `comment` is non-empty text and `assessed_at` is UTC `YYYY-MM-DDTHH:MM:SSZ`, the same form as `signed.at`.
- `not_assessed` is a deviation that has not been judged. `priority`, `comment`, and `assessed_at` are omitted.
- `must_fix` is the decision that the deficiencies are to be corrected. `priority`, `comment`, and `assessed_at` have the same form as for `accepted`.

A provenance key the run does not have is omitted. `decision`, `priority`, `comment`, and `remediation_history` are kept.
