# Workspace config (design sketch)

**Status:** design intent — implementation follows. Pack / Requirement / Claim / run-result **shapes** stay in [Packs v2](packs2.md). This file owns **where** product and Studio config live, and which path fields Check/Compile read.

Pilot: while `curbpack-studio.json` is absent, Studio keeps today's bind/model/prompt/keys wiring. Aligning `curbcheck` itself (path fields, `-j`/`-o`, `--defaults`, id-list filters) is [CHK-07](../agile/epics/01-pack-editor/stories/CHK-07-curbcheck-workspace.md); the keys and flags are named here so created files stay stable. Created-file JSON is owned by that same defaults factory — Studio must not keep a second copy.

---

## 1. Product config and two Studio levels

`curbpack.json` sits at the product repository root. Studio settings are two files with the same field names. A project key that is present replaces the user value for that field only. There is no merged document.

| File | Read by | Job |
|------|---------|-----|
| `curbpack.json` | `curbcheck`, Studio Check / Compile / Discover | Pack selection, requirement exclude/include, `search_hints`, directory paths for packs / claims / results / reports |
| `~/.curbpack/curbpack-studio.json` | Studio | Installation values: bind, model, prompts, paths. On Windows this is `%USERPROFILE%\.curbpack\curbpack-studio.json`. |
| `<product-repo>/curbpack-studio.json` | Studio | Allowed project overrides only |

`model.api_key` is empty or a `$NAME` placeholder. The value is read from `~/.curbpack/.env`. A missing name yields an empty key. A literal key is rejected and not written. The key is sent only when the effective `model.endpoint` comes from the user file. A project endpoint and the built-in endpoint do not receive it.

Directory locations are the string fields `packs_dir`, `claims_dir`, `results_dir`, and `reports_dir`. Docs and code resolve those fields.

`curbpack.json` is not JSON-sealed. It is covered by git (optionally signed commits). Studio **import** verifies the pack/requirement seal before writing into `packs_dir`.

---

## 2. `curbpack.json`

### 2.1 Rules

- Missing file: Studio asks whether to create one; `curbcheck` stops.
- Created file lists every key in §2.2 with concrete values. Readers use the file as written.
- Missing required key → reject; stop before a run file.
- Unknown key → reject; stop before a run file.
- Selection mode is exactly one of: `exclude_requirements`, or `requirements`, or neither (all requirements in `packs`).

Accepted keys are only those in §2.2.

### 2.2 Fields

| Field | Required | Created-file value | Meaning |
|-------|----------|--------------------|---------|
| `packs` | yes | pack ids ticked in the dialog | Pack ids. On disk: `<packs_dir>/<pack-id>/<pack-version>/`. That directory's `pack.json` carries the same `id` and `version`. |
| `exclude_requirements` | no | requirement ids left unticked in the dialog | Removed from the selected packs. |
| `requirements` | no | omitted; hand/CLI only | Only these requirement ids. |
| `search_hints` | yes | see example | Shared discovery scope. |
| `packs_dir` | yes | `"curbpack/packs"` | Relative to repo. Pack tree: `<packs_dir>/<pack-id>/<pack-version>/pack.json` + requirement `*.json` in that version directory. |
| `claims_dir` | yes | `"curbpack/claims"` | Claim `*.json` directly in this directory. |
| `results_dir` | yes | `".curbpack"` | Directory for run-result JSON when JSON output is requested. |
| `reports_dir` | yes | `"curbpack/reports"` | Directory for review-report JSON from Compile / Review. |
| `namespace_base` | yes | `"RISE"` | Publisher base namespace. A new Pack namespace is this value, a slash, and the Pack `name`. |

**Dialog → file:** packs and requirements as checkboxes. Ticked packs → `packs`. Unticked requirements → `exclude_requirements`.

### 2.3 Example (created / checked-in)

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
  "namespace_base": "RISE"
}
```

With that file:

| Kind | Path |
|------|------|
| Pack | `<repo>/curbpack/packs/cra-baseline/1.0.0/pack.json` |
| Claim | `<repo>/curbpack/claims/claim-house-security-md.json` |
| Run result (JSON requested) | `<repo>/.curbpack/run-result_<YYYYMMDDTHHMMSSZ>.json` |
| Review report | `<repo>/curbpack/reports/review-report_<YYYYMMDDTHHMMSSZ>.json` |
| Studio Check | `<results_dir>/run-result_<YYYYMMDDTHHMMSSZ>/` with `run-result.json`, `review_items.json`, `review-report.json`, and `remedy-report.json` |

`"results_dir": "artifacts/check"` → run under `<repo>/artifacts/check/…`. Same contract.

Studio Check writes one directory per run. That directory is the Check's identity. Its Review and Remedy are the files inside it. A flat `run-result_<stamp>.json` from an earlier Check or from `curbcheck -j` stays where it is. Identical run content does not attach one run's Review to another run.

---

## 3. What `curbcheck` produces

Object shape: [Outputs — Run result](outputs.md#run-result). Path policy: this file.

| Channel | Behaviour (design; align `curbcheck-cli` later) |
|---------|--------------------------------------------------|
| stdout | Human-readable summary (claim/check pass\|fail\|skipped, `detail` when present). |
| `-j` / `--json` | Also write `{results_dir}/run-result_<UTC>.json`. New file per run. |
| `-o` / `--out PATH` | Also write that JSON to `PATH` (relative or absolute). Parent dirs created when permitted. |

```bash
curbcheck --repo .
# text

curbcheck --repo . -j
# text + <results_dir>/run-result_20261029T053000Z.json

curbcheck --repo . -o /tmp/run.json
# text + /tmp/run.json
```

`-o PATH` always writes the run-result JSON object. Short flags: `-j`, `-o`. Long: `--json`, `--out`.

Compile copies the run-result object into the review report under `reports_dir` as `review-report_<UTC>.json`. Report fields: `run_result`, `requirements`, `claims`, `appendix`, and when recorded `decision` / `signed`.

---

## 4. `curbpack-studio.json`

### 4.1 Two levels

The user file holds the blocks below. While it is absent, Studio uses the created-file values (`127.0.0.1:8770`, Ollama `http://127.0.0.1:11434`, model `qwen3-coder:30b`, adapter prompts, workspace keys).

The product file may contain only `model.endpoint`, `model.name`, `model.temperature`, `prompts.interpret`, `prompts.discovery_hints`, `paths.extract_work_dir`, and `researcher_mode`. Any other field is an error that names every such field and says it belongs in the user file. Nothing is copied or ignored.

`bind` is read from the user file at process start. An omitted `--host` or `--port` does not replace it. A flag that is present does, for that process. `--workspace` still selects the Studio workspace. The product file cannot set `bind`.

`paths.temp_dir` and `paths.keys_file` stay in the user file. Review reads `paths.temp_dir`. Each Run Result and each Review Report has a directory there named after the source file's stem, and that directory holds `review_items.json`. A dirty Studio Check also writes `run-result_<stamp>.files.json` directly in `paths.temp_dir`. Signing keeps the workspace `keys/` directory. `paths.extract_work_dir` is the extract slot, confined to the open repository.

Switching repository reads that repository's product file and does not write the user file.

Studio may offer to create the file; the created values match the pilot numbers below.

### 4.2 Created-file example (today's values)

```json
{
  "bind": {
    "host": "127.0.0.1",
    "port": 8770
  },
  "model": {
    "endpoint": "http://127.0.0.1:11434",
    "api_key": "",
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
  },
  "researcher_mode": false
}
```

| Block / field | Meaning |
|---------------|---------|
| `bind` | UI listen address. |
| `model.endpoint` | Model HTTP base URL. |
| `model.api_key` | Empty, or `$NAME` from `~/.curbpack/.env`. Sent only with the user file's endpoint. |
| `model.name` | Model id sent to the endpoint. |
| `model.temperature` | Extract temperature. |
| `prompts.*` | Repo-relative path, or `null` for the installation's adapter prompt files. Key present either way. |
| `paths.temp_dir` | Scratch under the product repo. |
| `paths.extract_work_dir` | Extract work trees. |
| `paths.keys_file` | Signing keys JSON, or `null` for the pilot workspace `keys/keys.json`. |
| `researcher_mode` | Optional boolean. `true` hides the Review column on a requirement and the Useful and Poor columns on the Claims list. Omitted or `false` keeps those columns. |

`~/.curbpack/.env`:

```env
CURBPACK_MODEL_API_KEY=
```

---

## 5. Layout sketch

```text
~/.curbpack/
  curbpack-studio.json
  .env
<product-repo>/
  curbpack.json
  curbpack-studio.json
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

---

## 6. Related

| Topic | Document |
|-------|----------|
| Pack, Requirement, Claim, Check args, run-result fields | [packs2.md](packs2.md) — still needs the on-disk `<pack-id>/<pack-version>/` layout and path-field pass |
| curbcheck CLI as implemented | [curbcheck-cli.md](curbcheck-cli.md) |
| `curbpack.json` as Check reads it | [configuration.md](configuration.md) |
| Older path tables (point here on DOC pass) | [outputs.md](outputs.md) |
| Door behaviour | [SYS-03](../agile/epics/01-pack-editor/stories/SYS-03-one-repo-door.md) — align story/plan to this file |
