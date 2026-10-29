# CHK-07 — `curbcheck` uses `curbpack.json` paths, owns defaults, updates CLI docs

**Status:** Draft. Decided in walkthrough 2026-10-29 by danielfl: separate from SYS-03; owns CLI contract and created-file defaults. Not implemented.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**Contract:** [workspace.md](../../../../reference/workspace.md) (spec). Runtime input: product-repo `curbpack.json`. Connection to [SYS-03](SYS-03-one-repo-door.md): Studio create dialog uses the same defaults API.

**As a maintainer or CI user**, I want `curbcheck` to resolve packs, claims, and results from the product repository’s `curbpack.json` path fields, and to emit that file’s created-file shape from one shared function, so Studio and the CLI never invent different defaults.

### What this story is

Make the `curbcheck` program and its Python entry (`python3 -m checks`) honour the product `curbpack.json` contract in [workspace.md](../../../../reference/workspace.md): required path fields, versioned pack directories, stdout / `-j` / `-o` output channels, and a single defaults factory.

**In scope:**
- rewrite [curbcheck-cli.md](../../../../reference/curbcheck-cli.md) so it is the CLI description of that contract (not a follow-up doc chore);
- **inventory and update** existing curbcheck / `python3 -m checks` / packaged-binary tests and fixtures that still assume a packs **directory** `--packs`, a single `curbpack` key, or hard-coded `<curbpack>/…` result paths (at least `tests/test_curbcheck_package.py`, `tests/test_curbcheck_catalogue.py`, and any suite argv under `docs/testing/` that this story’s plan lists).

### Out of this story

`unsigned_requirements` behaviour (workspace §2.4). Studio door UI (SYS-03). Studio Check/Review pages calling the new runner — that is [CHK-08](CHK-08-studio-check-review-curbcheck.md) after this story.

---

### CHK-R01 — Always read `curbpack.json`

A repository run always loads `<repo>/curbpack.json` and uses its fields. Path locations are the string fields in that file.

**Given** a product repository with a valid `curbpack.json` per workspace.md §2  
**When** `curbcheck --repo <repo>` (or `curbcheck` with cwd that repository) runs  
**Then** packs load from `<packs_dir>/<pack-id>/<pack-version>/pack.json`  
**And** claims load from `<claims_dir>/*.json`  

**Given** `<repo>/curbpack.json` is missing or fails workspace §2 validation  
**When** the run starts  
**Then** the process stops before writing a run-result file  

---

### CHK-R02 — Output channels

Stdout is always the human summary. JSON is opt-in.

**Given** a successful or finished evaluation run  
**When** neither `-j`/`--json` nor `-o`/`--out` is set  
**Then** stdout is the text summary  
**And** no run-result JSON file is written  

**Given** the same run with `-j` or `--json`  
**When** the run finishes writing  
**Then** stdout still has the text summary  
**And** a new file `{results_dir}/run-result_<YYYYMMDDTHHMMSSZ>.json` is written  

**Given** the same run with `-o PATH` or `--out PATH`  
**When** the run finishes writing  
**Then** stdout still has the text summary  
**And** the run-result JSON object is written to `PATH`  

---

### CHK-R03 — Defaults factory (`--defaults` and Python API)

Created-file values for `curbpack.json` come from curbcheck. Studio calls the same function.

**Given** the checks package is importable  
**When** the defaults function is called with no repository-specific packs or excludes  
**Then** it returns a JSON object that contains every required key in workspace.md §2.2  
**And** the path and `unsigned_requirements` values match the created-file column in §2.2 / the example in §2.3  
**And** `search_hints` matches that same created-file shape  

**Given** the CLI  
**When** `curbcheck --defaults` runs  
**Then** that same JSON object is printed on stdout  
**And** no repository is required  
**And** no run-result file is written  
**And** the process exits 0  

**Given** Studio (or another caller) needs a create-dialog starting document  
**When** it imports and calls that same defaults function  
**Then** it receives the same object the CLI would print  

---

### CHK-R04 — `--packs` / `--requirements` select what to check

Without these flags, the run uses the selection in `curbpack.json`. With a flag, the value is a comma-separated list of ids: those are the packs or requirements this run checks. Paths still come from `curbpack.json` (`packs_dir`, `claims_dir`, `results_dir`).

**Given** a valid `curbpack.json`  
**When** `curbcheck --repo <repo> --packs id-a,id-b` runs  
**Then** this run checks packs `id-a` and `id-b`  
**And** pack files still load under that file’s `packs_dir`  

**Given** a valid `curbpack.json`  
**When** `curbcheck --repo <repo> --requirements req-a,req-b` runs  
**Then** this run checks requirements `req-a` and `req-b`  
**And** claim files still load under that file’s `claims_dir`  

**Given** either flag whose value contains `/` or `\`  
**When** arguments are parsed  
**Then** the process exits 2 and writes no run-result file  

---

### CHK-R05 — `curbcheck-cli.md` is updated in this story

The reference page is acceptance evidence for CHK-R01–CHK-R04.

**Given** the program behaviour in CHK-R01–CHK-R04  
**When** this story is verified done  
**Then** [curbcheck-cli.md](../../../../reference/curbcheck-cli.md) describes that behaviour: `curbpack.json` path fields, `-j`/`--json`, `-o`/`--out`, `--defaults`, and `--packs` / `--requirements` as comma-separated id lists of what to check  
**And** the pending-update banner added during drafting is removed  

---

### CHK-R06 — Existing curbcheck tests match the new contract

**Given** the curbcheck / checks test inventory recorded in this story’s plan  
**When** this story is verified done  
**Then** those tests construct `curbpack.json` with the required workspace.md §2.2 fields  
**And** they treat `--packs` / `--requirements` as id lists where the story’s CLI is under test  
**And** they assert run-result paths per CHK-R02  
**And** a packs-directory `--packs` path is not required for a green suite  

---

## Out of scope

- `unsigned_requirements` enforcement (later epic).
- Studio door UI, empty views, and Save/Cancel dialogs (SYS-03).
- Studio Check and Review pages rewired to the new runner API ([CHK-08](CHK-08-studio-check-review-curbcheck.md)).
- Changing Packs v2 Claim / run-result object shapes.
- Implementing unavailable Check ids (`fresh`, `owned`, …).
