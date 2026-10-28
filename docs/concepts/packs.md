# Packs

A Pack identifies a set of Requirements and the publisher's version label.

```text
pack.json                         metadata only
Requirement files                 pack_id points at the Pack
        +
product curbpack.json             which Pack ids this product uses
        +
product claims/                   what this product claims, and which Checks watch it
        ↓
Run curbcheck
        ↓
pass / fail / skipped
```

A Pack can represent an organisation's own policy or provisions taken from an external instrument. It is not a legal interpretation, a conformity assessment, or a certificate. Which products an instrument covers is the Pack `description`, written once. A Requirement's own `applicability` is only the "where" clause in that Requirement's `law_text`.

`version` on `pack.json` is the publisher's hand-set label, for example `0.1.0`. It is not a Git commit, not a content hash, and not the legal edition. The legal edition is `source.edition` on the Requirement, and it is required when the Requirement is published. The pack directory seal covers the files in that directory. Changing any of them makes the earlier seal fail.

## Two copies, and they are not the same selection

Pack Editor works on a dated working copy. Extract writes unsigned Requirement candidates into that copy. A person reviews them, edits them, and signs. **Sign** is used when the Requirement has no `origin`. **Approve and sign** is used when the Requirement has `origin`, which means the copy descends from a published Pack. Approval keeps `origin`. It does not publish the publisher's release.

**Seal Pack directory** seals that directory. **Publish release** creates a new immutable `published/<pack-id>/<version>/` and refuses to overwrite an existing version. The current Publish form shows `pack.version` as a read-only field. Do not describe an interactive version picker on that form. The story that asks for an explicit version choice is still a requirement under discussion, not the control on the page.

Check does not follow the working copy you happen to have open. It reads the Pack ids in the product repository's `curbpack.json` and loads `<packs-root>/<id>/pack.json` plus the Requirement files beside it. The cover says this on the Check link: authoritative pack via `curbpack.json`.

The catalog buttons are **Add**, **Edit**, and **Publish**. Copying a published directory unchanged into a local working copy is specified in the requirements architecture. It is not a control on the current catalog.

## Selecting packs

Studio reads `curbpack.json`, without a leading dot. A file named `.curbpack.json` is not the selection file.

```json
{
  "packs": ["house-policy", "cra-baseline"],
  "exclude_requirements": ["CRA-ART14-PATH"],
  "search_hints": {
    "sources": [{ "source": "documents" }],
    "exclude_path_globs": ["**/node_modules/**", "*FUTURE_*"],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"]
  },
  "curbpack": "curbpack"
}
```

`packs` lists ids, not versions. The version in use is `version` on the local `pack.json` for that id. Nothing fetches a newer publication on its own.

`exclude_requirements` removes those ids from the selected Packs. The alternative is a `requirements` list, which includes only those ids. One file uses one of those styles, not both.

`search_hints` is the shared search scope for Discovery. It is merged with each Requirement's `discovery_hints`. Check does not read the hints. `curbpack` is the directory, relative to the repository, that holds `packs/`, `claims/`, `run-result.json`, and `reports/`. When it is absent, that directory is `curbpack`.

Putting two ids in `packs` selects both Packs. It does not merge their Requirements and it does not let one Pack override the other's fields. Studio does not apply `extends`, `overlays`, or `overlay`.

## What a reviewer receives

The compiled review report: the run result, the Requirements and Claims that ran, the reviewer's `decision`, and `signed` after review-sign. The server writes it at `<product-repo>/docs/reports/review-report.json`. See [Evidence](evidence.md) and the [reviewer guide](../user-guides/reviewers.md).

## More detail

* [Packs v2](../reference/packs2.md) — the fields
* [Pack author guide](../user-guides/pack-developers.md)
