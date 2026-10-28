# Configuration reference

Curbpack configuration is stored in `curbpack.json` at the root of the product repository.

This page describes the current configuration file, how pack ids and requirement ids are selected, where pack definitions are loaded from, and the repository paths a run uses. The field contract is [Packs v2](packs2.md) §2.3. How a run is started and how its result is read is [curbcheck](curbcheck-cli.md).

## `curbpack.json`

The file is a JSON object. Check accepts `packs`, `requirements`, `exclude_requirements`, `search_hints`, and `curbpack`. Any other key is rejected, and no result is written. The key `hunt` is rejected. Write the file at the repository root. `.curbpack.json` is not this file.

### Fields

| Field | JSON type | Optional | Behavior |
| --- | --- | --- | --- |
| `packs` | `array<string>` | No | Pack ids selected for the repository. A non-empty list of non-empty strings. The version is `version` on the local `pack.json`. |
| `requirements` | `array<string>` | Yes | Only these requirement ids. Each id belongs to a selected pack. A non-empty list of non-empty strings. |
| `exclude_requirements` | `array<string>` | Yes | Requirement ids removed from the selected packs. A non-empty list of non-empty strings. |
| `search_hints` | `object` | Yes | Shared discovery scope, the same for every selected pack. See [`search_hints`](#search_hints). |
| `curbpack` | `string` | Yes | Path relative to the repository. Packs, Claims, the run result, and the review report live under it. When the key is absent, the directory is `curbpack`. |

Use either `requirements` or `exclude_requirements`. A file that sets both is rejected, and check writes no result.

`packs` does not list versions. The version in use is `version` on the local `pack.json` for that id. Keeping that file is what makes the choice reproducible. A newer publication is visible when its `pack.json` has reached the packs directory. Check does not fetch one.

### `search_hints`

| Field | JSON type | Optional | Behavior |
| --- | --- | --- | --- |
| `sources` | `array<object>` | Yes | Each item is an object with `source` (non-empty string) and an optional `args` object. |
| `exclude_path_globs` | `array<string>` | Yes | Path globs Discovery's file search skips. |
| `prefer_path_globs` | `array<string>` | Yes | Path globs that order a match ahead of other matches. |

Check validates `search_hints` and leaves it in the file. The run does not walk its globs or its `sources`. Discovery's file search applies `exclude_path_globs` and `prefer_path_globs`. A prefer glob only orders a path that already matched a requirement path hint or concept. That search does not read `source` or `args`.

### Example

```json
{
  "packs": [
    "house-policy",
    "medtech-iec62304"
  ]
}
```

The `packs` entry identifies the packs that check evaluates.

To evaluate every requirement in those packs except named ids, add `exclude_requirements`. To evaluate only named ids, add `requirements` and leave `exclude_requirements` out:

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

## Pack selection

For the check path, active pack ids are the `packs` array in `curbpack.json`.

`curbcheck` loads each id from `<repo>/<curbpack>/packs/<pack-id>/pack.json`. `curbpack` is the relative directory in the file. When the key is absent, that directory is `curbpack`.

`--packs` is an optional override. It is the directory that directly contains `<pack-id>/pack.json`, so an explicit path does not gain another `packs/` segment. `--out` is an optional override of the dated run file under `<repo>/<curbpack>/reports/`. Neither flag is a second configuration.

### Requirement selection

Requirement ids in scope are resolved from the same file:

1. when `requirements` is set, only those ids, and each id must be present in the loaded packs;
2. otherwise every requirement loaded from the selected packs, minus `exclude_requirements` when that key is set.

An id in `requirements` that is not in the loaded packs stops the run before a result is written. An id in `exclude_requirements` that is absent from the loaded packs leaves the selection unchanged. Check and the Studio Check page use this selection.

## Pack sources

For pack id `<pack-id>`, Curbpack looks for:

```text
<repo>/<curbpack>/packs/<pack-id>/pack.json
```

and every other `*.json` file in that directory. Those files are the Requirements. The result records that pack's `id`, the `version` string from `pack.json`, and a digest of the pack directory.

A missing `pack.json`, or a pack or requirement file that does not validate, stops the run before a result is written.

The structure of `pack.json` is documented in [Packs v2](packs2.md).

## Runtime configuration

### Pack loading and updates

Pack bytes come from the directory in [Pack selection](#pack-selection). Check loads the `pack.json` and Requirement files already in that directory. A newer publication is the copy whose `pack.json` is already there.

`python3 -m app` accepts `--workspace`, `--host`, and `--port`. A source checkout defaults to `data/workspace` inside this repository, `127.0.0.1`, and `8770`. A frozen build defaults the workspace to `~/curbpack-studio/workspace`. The Check page reads `<workspace>/product` and `<workspace>/packs`.

### Human confirmation

Confirmation is a signature on a Requirement, a Claim, or a review report. The key is the local key for the name that signs, stored at `<workspace>/keys/keys.json`.

### Attestation verification

`git_signed` and `git_signer` take their trust input in that Check's arguments (`allowed_signers` or `openpgp`), as Packs v2 §4.1 describes.

Git snapshot and the Git Checks take `git` from `PATH`. The child environment drops `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`, `GIT_NAMESPACE`, `GIT_GLOB_PATHSPECS`, and `GIT_NOGLOB_PATHSPECS`, and sets `GIT_LITERAL_PATHSPECS=1`.

### Names that are unused

`CURBPACK_PACKS_DIR`, `CURBPACK_PACKS_URL`, `CURBPACK_PACKS_SHA256`, `CURBPACK_ALLOW_CONFIRM`, `CURBPACK_EXPLAIN_ALLOW_CLOUD`, `CURBPACK_ALLOWED_SIGNERS`, `CURBPACK_SIGNER_ID`, `CURBPACK_AGENT_ID`, `CURBPACK_MODEL_HASH`, `CURBPACK_MANDATE_ID`, and `CURBPACK_SOCK` are unused. Pack selection, signing, and Check trust input are the settings in the sections above.

## Repository paths

Paths in the product repository:

| Purpose | Path |
| --- | --- |
| Configuration | `curbpack.json` |
| Packs | `<curbpack>/packs/<pack-id>/pack.json` |
| Claims | `<curbpack>/claims/*.json` |
| Check run | `<curbpack>/reports/run-<YYYYMMDDTHHMMSSZ>.json` |
| Review report | `<curbpack>/reports/review-<YYYYMMDDTHHMMSSZ>.json` |

Claims are the `*.json` files directly inside `<curbpack>/claims/`, in filename order. Files in subdirectories are not loaded. The pilot rule is one new file per Check run under `<curbpack>/reports/`. The current `curbcheck` command still writes `<curbpack>/run-result.json` unless `--out` names another file. Studio does not do this yet. SYS-03 is the change.

Paths in the Studio workspace:

| Purpose | Path |
| --- | --- |
| Packs the Check page loads | `packs/<pack-id>/` |
| Product repository the Check page reads | `product/` |
| Signing keys | `keys/keys.json` |

Individual commands may write the run result somewhere else. See [curbcheck](curbcheck-cli.md) for that file, and [Packs v2](packs2.md) §3.1 for its fields.
