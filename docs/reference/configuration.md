# Configuration

[Workspace](workspace.md) decides where product and Studio config live, which keys exist, and the on-disk paths. [Packs v2](packs2.md) §2.3 decides how `curbpack.json` selects packs and requirements, and how `search_hints` merges. This page repeats that contract. It does not add a key or a path.

Two files sit at the product repository root.

| File | Read by | Job |
|------|---------|-----|
| `curbpack.json` | `curbcheck`, Studio Check / Compile / Discover | Pack selection, requirement exclude/include, `search_hints`, directory paths for packs / claims / results / reports |
| `curbpack-studio.json` | Studio | Bind address, model endpoint/name, `$ENV` secrets, prompt paths, temp/extract/keys |

`.env` (gitignored) supplies values for `$NAME` placeholders in `curbpack-studio.json` at load time. An unknown `$NAME` is an error.

`curbpack.json` is not JSON-sealed. It is covered by git (optionally signed commits). Studio import verifies the pack/requirement seal before writing into `packs_dir`. `.curbpack.json` is not `curbpack.json`.

## `curbpack.json`

Missing file: Studio asks whether to create one; `curbcheck` stops.

A created file lists every key below with concrete values. Readers use the file as written. A missing required key is rejected, and so is an unknown key, before a run file is written. The key `hunt` is not accepted. Accepted keys are only the fields in the table.

Selection mode is exactly one of: `exclude_requirements`, or `requirements`, or neither (all requirements in `packs`). A file that sets both `requirements` and `exclude_requirements` is rejected.

### Fields

| Field | Required | Created-file value | Meaning |
|-------|----------|--------------------|---------|
| `packs` | yes | pack ids ticked in the dialog | Pack ids. On disk: `<packs_dir>/<pack-id>/<pack-version>/`. That directory's `pack.json` carries the same `id` and `version`. |
| `exclude_requirements` | no | requirement ids left unticked in the dialog | Removed from the selected packs. |
| `requirements` | no | omitted; hand/CLI only | Only these requirement ids. Each id belongs to a selected pack. |
| `search_hints` | yes | see example | Shared discovery scope. |
| `packs_dir` | yes | `"curbpack/packs"` | Relative to the repo. Pack tree: `<packs_dir>/<pack-id>/<pack-version>/pack.json` plus requirement `*.json` in that version directory. |
| `claims_dir` | yes | `"curbpack/claims"` | Claim `*.json` directly in this directory: `<claims_dir>/<claim-id>.json`. |
| `results_dir` | yes | `".curbpack"` | Directory for run-result JSON when JSON output is requested. |
| `reports_dir` | yes | `"curbpack/reports"` | Directory for review-report JSON from Compile / Review. |
| `unsigned_requirements` | yes | `"report"` | Accepted values and intended behaviour: [Workspace](workspace.md) §2.4. |

`packs` lists pack ids. It does not list versions. The version in use is `version` on the local `pack.json` for that id. Keeping that file is what makes the choice reproducible. A newer publication is visible when its `pack.json` has reached `packs_dir`. Nothing fetches one.

Each of `packs_dir`, `claims_dir`, `results_dir`, and `reports_dir` is its own required field. Docs and code resolve those strings. There is no single `curbpack` directory key, and temp is not a field of this file.

**Dialog → file:** packs and requirements as checkboxes. Ticked packs → `packs`. Unticked requirements → `exclude_requirements`.

### `search_hints`

The object is the one [Packs v2](packs2.md) §2.3 uses: `sources`, `exclude_path_globs`, and `prefer_path_globs`.

Search merge: the repository `search_hints`, then that requirement's `discovery_hints` ([Packs v2](packs2.md) §2.7). A requirement that sets `sources` uses that list. Otherwise the repository `search_hints` list is used.

### Example (created / checked-in)

```json
{
  "packs": ["house-policy", "cra-baseline"],
  "exclude_requirements": [
    "CRA-ART14-PATH"
  ],
  "search_hints": {
    "sources": [
      { "source": "documents" },
      { "source": "git" }
    ],
    "exclude_path_globs": [
      "**/node_modules/**",
      "**/.git/**",
      "**/dist/**",
      "**/build/**"
    ],
    "prefer_path_globs": [
      "**/docs/**",
      "**/SECURITY*",
      "**/README*"
    ]
  },
  "packs_dir": "curbpack/packs",
  "claims_dir": "curbpack/claims",
  "results_dir": ".curbpack",
  "reports_dir": "curbpack/reports",
  "unsigned_requirements": "reject"
}
```

Semantics: evaluate all requirements whose pack is in `packs`, minus `exclude_requirements`.

Explicit include, hand/CLI only. A real file still carries every required key:

```json
{
  "packs": ["house-policy"],
  "requirements": [
    "HOUSE-SECURITY-REPORTING",
    "HOUSE-SECURITY-TXT"
  ],
  "search_hints": {
    "sources": [
      { "source": "documents" },
      { "source": "git" }
    ],
    "exclude_path_globs": ["**/node_modules/**"]
  },
  "packs_dir": "curbpack/packs",
  "claims_dir": "curbpack/claims",
  "results_dir": ".curbpack",
  "reports_dir": "curbpack/reports",
  "unsigned_requirements": "reject"
}
```

Semantics: only these requirement ids. Each belongs to a selected pack.

With the created file:

| Kind | Path |
|------|------|
| Pack | `<repo>/curbpack/packs/cra-baseline/1.0.0/pack.json` |
| Claim | `<repo>/curbpack/claims/claim-house-security-md.json` |
| Run result (JSON requested) | `<repo>/.curbpack/run-result_<YYYYMMDDTHHMMSSZ>.json` |
| Review report | `<repo>/curbpack/reports/review-report_<YYYYMMDDTHHMMSSZ>.json` |

`"results_dir": "artifacts/check"` writes the run under `<repo>/artifacts/check/…`. Same contract.

### `unsigned_requirements` (later epic)

Accepted values, the created-file value, and the intended behaviour are [Workspace](workspace.md) §2.4.

### What the run reads

For each id in `packs`, load `<packs_dir>/<pack-id>/<pack-version>/pack.json` and the other `*.json` files in that version directory. Those files are the Requirements. The shape of `pack.json` is [Packs v2](packs2.md). The version the run records is `version` on that `pack.json`.

Claims are `<claims_dir>/<claim-id>.json`. Run-result and review-report paths are the table above. Object shape of the run result: [Outputs — Run result](outputs.md#run-result). Output channels: [Workspace](workspace.md) §3. The command as shipped: [curbcheck](curbcheck-cli.md).

| Channel | Behaviour (design; align `curbcheck-cli` later) |
|---------|--------------------------------------------------|
| stdout | Human-readable summary (claim/check pass\|fail\|skipped, `detail` when present). |
| `-j` / `--json` | Also write `{results_dir}/run-result_<UTC>.json`. New file per run. |
| `-o` / `--out PATH` | Also write that JSON to `PATH` (relative or absolute). Parent dirs created when permitted. |

`-o PATH` always writes the run-result JSON object. Compile copies the run-result object into the review report under `reports_dir` as `review-report_<UTC>.json`. Report fields: `run_result`, `requirements`, `claims`, `appendix`, and when recorded `decision` / `signed`.

## `curbpack-studio.json`

While this file is absent, Studio keeps today's wiring (`127.0.0.1:8770`, Ollama `http://127.0.0.1:11434`, model `qwen3-coder:30b`, adapter prompts, workspace keys). When the file is present, Studio loads it after `$ENV` substitution from `.env`. CLI `--host`, `--port`, and `--workspace` override for that process.

Studio may offer to create the file. The created values match today's:

```json
{
  "bind": {
    "host": "127.0.0.1",
    "port": 8770
  },
  "model": {
    "endpoint": "http://127.0.0.1:11434",
    "api_key": "$CURBPACK_MODEL_API_KEY",
    "name": "qwen3-coder:30b",
    "temperature": 0.2
  },
  "prompts": {
    "interpret": null,
    "discovery_hints": null
  },
  "paths": {
    "temp_dir": ".curbpack/tmp",
    "extract_work_dir": ".curbpack/extract",
    "keys_file": null
  }
}
```

| Block / field | Meaning |
|---------------|---------|
| `bind` | UI listen address. |
| `model.endpoint` | Model HTTP base URL. |
| `model.api_key` | `$NAME` from `.env`. |
| `model.name` | Model id sent to the endpoint. |
| `model.temperature` | Extract temperature. |
| `prompts.*` | Repo-relative path, or `null` for the installation's adapter prompt files. Key present either way. |
| `paths.temp_dir` | Scratch under the product repo. |
| `paths.extract_work_dir` | Extract work trees. |
| `paths.keys_file` | Signing keys JSON, or `null` for the pilot workspace `keys/keys.json`. |

```env
CURBPACK_MODEL_API_KEY=
```

Packs, claims, the run result, and the review report are the path fields in `curbpack.json`. Confirmation is a signature on a Requirement, a Claim, or a review report. `git_signed` and `git_signer` take their trust input in that Check's arguments (`allowed_signers` or `openpgp`), as [Packs v2](packs2.md) §4.1 describes.

## Layout

```text
<product-repo>/
  curbpack.json
  curbpack-studio.json
  .env
  curbpack/
    packs/<pack-id>/<pack-version>/pack.json
    claims/<claim-id>.json
    reports/review-report_<UTC>.json
  .curbpack/
    run-result_<UTC>.json
    tmp/
    extract/
```

Authoritative paths are the strings in `curbpack.json` and `curbpack-studio.json`. The sketch matches the created-file defaults.
