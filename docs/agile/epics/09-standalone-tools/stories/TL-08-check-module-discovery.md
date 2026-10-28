# TL-08 — Discover Check families as Python modules

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)
**Depends on:** TL-04 (curbcheck alone), CHK-06 packaging baseline.

**As a curbcheck maintainer**, I want each Check family to be an ordinary Python module that curbcheck discovers and can list, so that adding `node` / `git` / a future family is one module plus its tests — not a second copy in `available_checks.json`, `_HANDLERS`, and `checks/bin/`.

## Why this is not “less safe”

Safety and predictability for Checks do not come from refusing `import`. They come from a **fixed contract**:

- A Check returns only `{status: pass|fail|skipped, detail?}` as today.
- Paths stay inside the product repo (existing boundary rules).
- A Check does not use the network, does not spawn arbitrary shells from Claim args, and does not write outside the run result.
- Discovery reads **only** modules under one declared package path in this repository (or the matching bundle inside the packaged curbcheck). It does not load Claim files, pack JSON, or paths the Claim names as code.

Subprocess-per-tool and a hand-maintained JSON registry do not by themselves make those rules true. They duplicate the allowlist. This story replaces that duplication with module discovery under a fixed root.

## Current pain (baseline)

Today:

- Check ids and commands live in `checks/available_checks.json`.
- Source runs start `checks/bin/curbcheck-*` via subprocess (`checks/dispatch.py`).
- The packaged binary re-enters through a **hard-coded** `_HANDLERS` map in `checks/__main__.py`.

Adding `dep_ban` under Node required registry rows, a bin script, a handler entry, and docs — three places for one family. That is the defect this story removes.

## Pedagogical example (normative shape)

A maintainer adds a fictional family `demo` with one Check id `demo_ping` (this id is **only** for the example in this story; it is not shipped).

```text
checks/
  families/
    __init__.py          # discovery root (empty or exports nothing required)
    demo.py              # one family module
```

```python
# checks/families/demo.py  — pedagogical only
FAMILY = "demo"
CHECKS = {
    "demo_ping": {
        "args_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["token"],
            "properties": {"token": {"type": "string", "minLength": 1}},
        }
    },
}

def run(check_id: str, repo, args: dict) -> dict:
    if check_id != "demo_ping":
        return {"status": "fail", "detail": f"unknown check {check_id!r} for family demo"}
    if args.get("token") == "ok":
        return {"status": "pass"}
    return {"status": "fail", "detail": "token was not ok"}
```

After discovery:

- `list_checks()` includes `demo_ping` with that args schema.
- A Claim with `"check": "demo_ping"` and `{"token": "ok"}` yields Check status `pass`.
- The same Claim with `{"token": "no"}` yields `fail` and a non-empty `detail`.
- No edit to `__main__._HANDLERS` and no new `checks/bin/` script is required for the source-tree runner.

Real families already in product (`exist` / `contents`, `git_*`, `dep_ban` on Node) move to this shape. Packs v2 **Check ids stay the names in `docs/reference/packs2.md`** (`exist`, `contents`, `git_fresh`, `git_author`, `dep_ban`, …). Family name (`node`, `git`, …) is an implementation grouping, not a new Packs v2 field.

## Requirements (Given / When / Then)

Acceptance tests are derived **only** from these criteria. An AI implementing this story starts by writing failing tests for each Then. Do not invent extra discovery paths, plugin directories outside the declared root, or new Packs v2 Check ids.

### R1 — Discover and list

**Given** the source tree contains the pedagogical `checks/families/demo.py` (or an equivalent test double under the declared discovery root)  
**When** curbcheck builds its Check catalogue (the same catalogue Claims validation and the runner use)  
**Then** the catalogue includes every Check id exported by every discovered family module under that root, each with its args schema  
**And** it does not include ids from Python files outside that root.

### R2 — Run through the module

**Given** a product repo and a Claim whose only Check is a discovered id with valid args  
**When** `python3 -m checks --repo … --packs … --out …` runs  
**Then** that Check’s result `status` / `detail` are exactly what the family module’s `run` returned  
**And** the runner does not require a matching entry in a hand-maintained `_HANDLERS` dict for source-tree execution.

### R3 — Unknown id still rejected

**Given** a Claim names a Check id that no discovered family exports  
**When** Claim args are validated, or a run would execute that Check  
**Then** validation fails with an unknown-check error (same class of failure as today: not a silent `pass`)  
**And** no family `run` is invoked for that id.

### R4 — Existing Packs v2 ids keep behavior

**Given** the seven carried Studio claims (or the focused unit fixtures already used for `exist`, `contents`, `git_fresh`, `git_author`, and Node `dep_ban`)  
**When** the same `--repo` / `--packs` / `--out` run executes after this refactor  
**Then** each Check id’s pass/fail/skipped outcome matches the pre-refactor baseline for those fixtures  
**And** Claim JSON still uses the Packs v2 Check id strings (`exist`, `contents`, `git_fresh`, `git_author`, `dep_ban`, …), not family-prefixed renames.

### R5 — Packaged curbcheck

**Given** `make package` has built the curbcheck binary for this host  
**When** that binary runs the same Claim fixtures as R4 (including a Node `dep_ban` fail on a banned pin, and a `git_signed` / `git_signer` “not implemented” fail if those ids remain registered that way)  
**Then** outcomes match the source-tree runner for those fixtures  
**And** the Studio package still does not embed the Check family programs as a second product.

### R6 — No silent pass on broken family

**Given** a discovered family module raises an unexpected exception from `run`  
**When** the runner executes that Check  
**Then** the Check result is `fail` with a non-empty `detail`  
**And** later Checks on the same Claim still receive a result row  
**And** the overall Claim is not `pass`.

## Out of scope

- New Packs v2 Check ids, Claim fields, or run-result fields.
- Loading Check code from the product repository, from Claim `args`, or from the network.
- A marketplace, entry-point plugin scan of the whole `PYTHONPATH`, or third-party wheel auto-install.
- Implementing unfinished Checks (`git_signed`, `git_signer`, `fresh`, `owned`) beyond keeping their current non-passing behavior.
- Renaming the `checks` package or the start command `python3 -m checks`.

## Stop if

- Discovery would need to import `app`, `pilot_app`, or another tool’s UI to list or run Checks.
- Making R4 green requires changing Packs v2 or weakening an existing Check assertion to “unavailable” when the family is present.
- The only way to list Checks is to reintroduce a second hand-edited allowlist that can drift from the modules.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| Keep `checks/bin/curbcheck-*` as thin CLI wrappers around the same modules, or drop them once the module API is the source runner | Prefer thin wrappers so PATH debugging stays; not required for R2 | OPEN |
| Whether `available_checks.json` is deleted or generated from modules at build/test time | Prefer generated or deleted; modules own schemas | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
