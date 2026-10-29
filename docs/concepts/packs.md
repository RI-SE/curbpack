# Packs

A Pack is a versioned collection of Requirements. `pack.json` is metadata only. Membership is `requirement.pack_id` pointing at `pack.id`. Requirement files sit in the same version directory; that grouping is packaging.

```text
<packs_dir>/<pack-id>/<pack-version>/
  pack.json                         metadata only
  <requirement>.json                pack_id points at the Pack
        +
curbpack.json                       which Pack ids this product uses
        +
<claims_dir>/<claim-id>.json        evidence, rationale, and Checks
        ↓
Run curbcheck
        ↓
pass / fail / skipped
```

A Pack can represent an organisation's own policy or provisions taken from an external instrument. Which products an instrument covers is the Pack `description`, written once. A Requirement's own `applicability` is only the "where" clause in that Requirement's `law_text`.

`version` on `pack.json` is the publisher's hand-set label, for example `0.1.0`. It is not a Git commit, not a content hash, and not the legal edition. The legal edition is `source.edition` on the Requirement, and it is part of that Requirement's seal. The pack `signed.signature` seals the entire pack directory. Add, remove, or rewrite any file and the pack check fails.

Field lists are [Packs v2](../reference/packs2.md). Where the product files live is [Workspace](../reference/workspace.md).

## The published Requirement and the working copy

A published Requirement has `signed` and no `origin`. Creating a local working copy sets `origin` to that published pack id and `version`, and leaves the fetched Pack unchanged. The copy is an unsigned draft. Adding `origin` changes the payload, so the publisher's signature does not cover the draft. Copying does not approve it.

Approving the draft seals that local version. A later edit, including `discovery_hints`, is another draft until it is approved and sealed. `origin.version` stays until a newer published version is taken in and accepted.

`pack.version`, `origin.version`, and the version digest are three different facts. A newer publication is visible only once its `pack.json` has reached the environment. Nothing fetches it on its own.

Check reads the Pack ids in the product repository's `curbpack.json` and loads `<packs_dir>/<pack-id>/<pack-version>/pack.json` plus the other Requirement `*.json` files in that version directory. The version in use is `version` on that local `pack.json`.

## Selecting packs

The selection file is `curbpack.json` at the repository root. Accepted keys are `packs`, `exclude_requirements`, `requirements`, `search_hints`, `packs_dir`, `claims_dir`, `results_dir`, `reports_dir`, and `unsigned_requirements`. A missing required key or an unknown key is rejected before a run file is written.

```json
{
  "packs": ["house-policy", "cra-baseline"],
  "exclude_requirements": ["CRA-ART14-PATH"],
  "search_hints": {
    "sources": [{ "source": "documents" }],
    "exclude_path_globs": ["**/node_modules/**", "*FUTURE_*"],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"]
  },
  "packs_dir": "curbpack/packs",
  "claims_dir": "curbpack/claims",
  "results_dir": ".curbpack",
  "reports_dir": "curbpack/reports",
  "unsigned_requirements": "reject"
}
```

`packs` lists ids, not versions. On disk a selected Pack is `<packs_dir>/<pack-id>/<pack-version>/`, and that directory's `pack.json` carries the same `id` and `version`. With the created-file defaults that is `<repo>/curbpack/packs/<pack-id>/<pack-version>/pack.json`.

Selection is one mode. `exclude_requirements` removes those ids from the selected Packs. `requirements` includes only those ids, and each id belongs to a selected Pack. With neither key, Check evaluates every Requirement whose `pack_id` is in `packs`.

`search_hints` is the shared discovery scope. Search uses that object, then the Requirement's `discovery_hints`. The key `hunt` is not accepted. Check does not read the hints.

The four directory fields are each required. Created-file values are `curbpack/packs`, `curbpack/claims`, `.curbpack`, and `curbpack/reports`. A Claim file is `<claims_dir>/<claim-id>.json`. A run-result JSON, when one is requested, is `<results_dir>/run-result_<UTC>.json`. `unsigned_requirements` is required. Accepted values and intended behaviour are Workspace §2.4.

Putting two ids in `packs` selects both Packs. Each Requirement stays in its own Pack through `pack_id`.

## What a reviewer receives

Compile copies the run result into one review report at `<reports_dir>/review-report_<UTC>.json`. With the created-file default that is `<repo>/curbpack/reports/review-report_<UTC>.json`.

The report carries `run_result`, `requirements`, `claims`, and `appendix`. When a person has recorded them, it also carries `decision` and `signed`. The review-report signature is the reviewer's decision on that report. It is not the Requirement seal and not the Claim seal.

See [Evidence](evidence.md) and the [reviewer guide](../user-guides/reviewers.md).

## More detail

* [Packs v2](../reference/packs2.md) — Pack, Requirement, Claim, Check, signing, and run-result fields
* [Workspace](../reference/workspace.md) — `curbpack.json` keys, created-file values, and on-disk paths
* [Pack author guide](../user-guides/pack-developers.md)
