# Workspace config (design sketch)

**Status:** design intent — implementation follows. Pack / Requirement / Claim / run-result **shapes** stay in [Packs v2](packs2.md). This file owns **where** product and Studio config live, and which path fields Check/Compile read.

Pilot: while `curbpack-studio.json` is absent, Studio keeps today's bind/model/prompt/keys wiring. `unsigned_requirements` behaviour ships in a later epic. Aligning `curbcheck` itself (path fields, `-j`/`-o`, `--defaults`, id-list filters) is [CHK-07](../agile/epics/01-pack-editor/stories/CHK-07-curbcheck-workspace.md); the keys and flags are named here so created files stay stable. Created-file JSON is owned by that same defaults factory — Studio must not keep a second copy.

---

## 1. Two files in the product repo

Both sit at the **product repository root**.

| File | Read by | Job |
|------|---------|-----|
| `curbpack.json` | `curbcheck`, Studio Check / Compile / Discover | Pack selection, requirement exclude/include, `search_hints`, directory paths for packs / claims / results / reports |
| `curbpack-studio.json` | Studio | Bind address, model endpoint/name, `$ENV` secrets, prompt paths, temp/extract/keys |

`.env` (gitignored) supplies values for `$NAME` placeholders in `curbpack-studio.json` at load time. Unknown `$NAME` → error.

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
| `unsigned_requirements` | yes | `"reject"` | `"report"`, `"reject"`, or `"signed_commit"`. Behaviour: §2.4, later epic. |

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
  "unsigned_requirements": "report"
}
```

With that file:

| Kind | Path |
|------|------|
| Pack | `<repo>/curbpack/packs/cra-baseline/1.0.0/pack.json` |
| Claim | `<repo>/curbpack/claims/claim-house-security-md.json` |
| Run result (JSON requested) | `<repo>/.curbpack/run-result_<YYYYMMDDTHHMMSSZ>.json` |
| Review report | `<repo>/curbpack/reports/review-report_<YYYYMMDDTHHMMSSZ>.json` |

`"results_dir": "artifacts/check"` → run under `<repo>/artifacts/check/…`. Same contract.

### 2.4 `unsigned_requirements` (later epic)

Accepted values are `report`, `reject`, and `signed_commit`. A created file uses `reject`. Intended curbcheck behaviour where it is already written:

| Value | Intended curbcheck behaviour |
|-------|------------------------------|
| `reject` | Requirement whose JSON `signed` does not verify → reported unsigned. |
| `signed_commit` | Same report, unless that requirement file is covered by a signed commit (allowed-signers). |

Studio import still verifies seals when bringing a published pack into `packs_dir`.

---

## 3. What `curbcheck` produces

Object shape: [Packs v2](packs2.md) §3.1. Path policy: this file.

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

### 4.1 Pilot compatibility

| State | Behaviour |
|-------|-----------|
| File absent | Today's Studio wiring (`127.0.0.1:8770`, Ollama `http://127.0.0.1:11434`, model `qwen3-coder:30b`, adapter prompts, workspace keys). |
| File present | Studio loads it after `$ENV` substitution from `.env`. |
| CLI `--host` / `--port` / `--workspace` | Override for that process. |

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

`.env` (gitignored):

```env
CURBPACK_MODEL_API_KEY=
```

---

## 5. Layout sketch

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

---

## 6. Related

| Topic | Document |
|-------|----------|
| Pack, Requirement, Claim, Check args, run-result fields | [packs2.md](packs2.md) — still needs the on-disk `<pack-id>/<pack-version>/` layout and path-field pass |
| curbcheck CLI as implemented | [curbcheck-cli.md](curbcheck-cli.md) |
| `curbpack.json` as Check reads it | [configuration.md](configuration.md) |
| Older path tables (point here on DOC pass) | [outputs.md](outputs.md) |
| Door behaviour | [SYS-03](../agile/epics/01-pack-editor/stories/SYS-03-one-repo-door.md) — align story/plan to this file |
