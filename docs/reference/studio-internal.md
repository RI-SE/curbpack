# Studio-internal structures

**Status:** Approved.

This document defines Curbpack Studio's internal data structures. This page defines `review_item`. Claim, Check, and signature are added to this document in a later step.

## review_item

`review_item` is the decision for one Check. On the signed items, `decision`, `priority`, and `comment` remain as signed. On the remediation copy, `decision` is the recommendation and may change, and `remediation_history` is appended.

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

The Run Result records `commit` and `worktree`. File `size` and `mtime` are not Run Result fields. When Studio Check writes a Run Result and `worktree` is `dirty`, the same operation writes `paths.temp_dir/run-result_<stamp>.files.json` with each Check's relevant paths, `size`, and `mtime`. Those values are copied to `provenance.files` when the `review_item` is created. A later edit of the worktree does not change that file. `curbcheck` without Studio writes no such file. When `dirty_git` is true and `files` is absent, the stored decision and history remain and a new decision is required.

### The same deviation

Reusing a decision fills `decision` only. `remediation_history` is shown from the remediation file and does not set `decision`.

A decision is reusable when `key` matches, `requirement_digest` matches, and the underlag below is unchanged. A value the comparison needs, and which is missing on either side, yields false. The stored decision and history remain.

- Clean to clean compares the Check's relevant file content between the two Git commits. Paths are `provenance.files` when that list exists, otherwise the paths in the Check arguments. A Check with no such paths depends on the commit. The same content reuses the decision. A path added, removed, or changed opens only that item.
- When either side is `dirty_git`, compare `path`, `size`, and `mtime` with `same_file_metadata`. The worktree is not read again.

`same_file_metadata` is true when both lists are present and contain the same set of `path`, and each path has the same `size` and the same `mtime`. Order does not matter.

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
      "date": "2026-11-23T08:15:00Z",
      "remediation": "Added security documentation."
    }
  ]
}
```

`decision` is `pass`, `accepted`, `not_assessed`, or `must_fix`.

`comment` is the note on this item. It is not a history entry. On the remediation copy it is the current note and may be replaced or cleared.

`remediation_history` is the sequence of actions recorded for this item, earliest first. Each entry has `date`, UTC `YYYY-MM-DDTHH:MM:SSZ`, and `remediation`, the non-empty text of what was done. An action has `action` (`retire` or `rebind`) or `transition`. `old_check_digest` is optional. The key is omitted when the sequence is empty.

`priority` is an integer from 1 to 10. 1 is the most urgent.

- `pass` is the recorded Check outcome. `priority`, `comment`, and `assessed_at` are omitted.
- `accepted` means the reviewer has accepted the deficiencies the Check found. `priority` is set. `comment` is non-empty text and `assessed_at` is UTC `YYYY-MM-DDTHH:MM:SSZ`, the same form as `signed.at`.
- `not_assessed` is a deviation that has not been judged. `priority`, `comment`, and `assessed_at` are omitted.
- `must_fix` is the decision that the deficiencies are to be corrected. `priority` and `assessed_at` have the same form as for `accepted`. `comment` may be omitted.

A provenance key the run does not have is omitted. `decision`, `priority`, `comment`, and `remediation_history` are kept.
