# Curbcheck — Check execution architecture

**Status:** Target functional contract aligned with EP-02 and revised EP-11 (2026-11-06). Old `checks/` paths and `app/server.py` integrations are migration sources, not the target architecture.

## System owner and boundaries

**Curbcheck is an independent system**, not a Studio component. Its Python API can run without Studio, its GUI, FastAPI, a browser or an interactive terminal. The thin `curbcheck/cli.py` parses arguments and calls the **same Python backend operations** as `curbcheck/api.py`; it never reimplements execution or result interpretation. CI calls this CLI headlessly.

```text
curbcheck/
  api.py                # Public Python operations used by CLI and Studio
  cli.py                # Thin CLI to shared operations
  impl/                 # Registry, argument validation, execution, Run Result writing
  checks/               # Registered Check programs and supporting implementations
  tests/
studio/check/
  router.py             # Studio REST adapter calling curbcheck/api.py
  pages/                # Thin TypeScript GUI calling router.py
```

`studio/check/` is the **deliberate exception**: it owns Studio interaction with Check execution, not a second engine. Its router invokes Curbcheck Python APIs and is registered by the thin `studio/app.py`. Neither `studio/check/` nor `studio/app.py` owns Check selection, registry interpretation, validation rules, execution or Run Result construction.

## Inputs and execution

Curbcheck consumes the selected product repository and current `docs/reference/workspace.md` configuration (`curbpack.json`, Pack/Claim/Results locations), validated Packs v2 objects, and the check registry `available_checks.json`. It must not guess paths from unrelated Claim fields or inline arbitrary code.

- Every configured Check is identified by registered `check` id and `args` validated using that id's schema. A Claim may contain multiple Checks on one evidence binding.
- Execution uses the registered Check command/implementation, without implementing the same Check in Studio. A missing or unavailable command is an explicit failure, never an invented PASS.
- Check outcomes are recorded individually as **pass**, **fail**, or **skipped** with explicit reasons. Failures do not suppress unrelated configured Checks. A permitted SKIP is not PASS.
- Preserve the Check programs and established subprocess execution architecture; the migration is about ownership and API boundaries, not replacing it with in-process Python or an agent framework.
- Record product Git revision / dirty state as actual observations, not as proof that uncommitted bytes correspond to a signed commit.
- Run Results are persisted under configured results location and validated using the authoritative Packs v2/output contracts. Re-running Checks must **never overwrite, alter or delete an existing signed Review report**.

## Exact Requirement binding (VL-04)

A Claim's accepted binding will carry fully qualified Requirement identity (`namespace`, `pack_id`, `requirement_id`) and the `requirement_digest`. **Curbcheck compares it to the selected Requirement and independently reports `match`, `stale` or `missing`, plus expected/actual digest as available.** The Run Result also preserves the Claim digest, binding identity and configured Check results. Exact schema is defined by the human-approved Packs v2 revision, not invented here.

**Always run all configured Checks even when the binding is stale or missing.** A binding finding is independent of Check execution outcomes and signature verification. A future separately approved release-policy evaluator may act on these facts; Curbcheck does not silently impose a release gate or claim legal compliance.

## Interfaces

- `curbcheck/api.py`: public entry points for loading configuration, checking arguments, running configured Checks, writing/reading Run Results, and the workspace defaults factory where implemented.
- `curbcheck/cli.py`: thin command-line adapter to those functions. Use conventional noninteractive exit codes and structured human/machine output. Do not invent separate CLI-specific business rules.
- `studio/check/router.py`: thin REST adapter to the **same** Curbcheck API. Studio pages display status, configured Checks, and Run Results; they do not evaluate outcomes or recompute binding status.
- `studio/compile/`: assembles reports from saved Run Results; does not run Checks.
- `studio/review/`: inspects result and report history; does not run Checks or change the past.

## Architecture invariants and tests

1. Import and run `curbcheck/api.py` without importing Studio or launching HTTP/UI.
2. CLI and Studio REST paths produce equivalent results on the same fixture and settings, using one backend implementation.
3. Every registered Check executes (or reports its own explicit failure/SKIP); one failure does not skip unrelated Checks.
4. Missing Check commands, invalid args and missing evidence do not become PASS.
5. Binding statuses match/stale/missing are independently observed and preserved alongside Check outcomes after VL-04.
6. A stale/missing Requirement never prevents execution of the configured Checks.
7. Running again creates or updates only the intended Run Result; an earlier signed Review report remains untouched.
8. The existing supported Checks, CLI flags, result shape, Git snapshots and tests remain behaviorally equivalent through EP-02 except separately approved changes.

## Current-to-target migration

Legacy `checks/`, `checks/bin/`, old `python3 -m checks` and `app/server.py` are implementation and test inputs. Preserve supported CLI compatibility where required by existing acceptance. EP-02's `MIGRATION_COVERAGE.md` records each program, call path, Check id and test. The published user-facing commands must be maintained or explicitly changed through an accepted story. The historical PoC1 Scan and old HTML Check page are not architecture authorities.
