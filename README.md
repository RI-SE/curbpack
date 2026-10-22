# Curbpack Studio

Curbpack Studio is a graphical environment for authoring regulatory Requirements, finding and reviewing product evidence, running Checks, and reviewing results.

## Repository contents

This starter archive contains **backlog and repository structure only**. Application code and existing tests will be imported separately from a **fresh PoC2 archive**. No PoC2 implementation is bundled here.

- `docs/agile/epics/` — epics and **user stories grouped by epic**, starting with EP-01 Pack Editor (PE-01–PE-11).
- `docs/agile/DECISIONS.md` — concise record of decisions, boundaries and still-open questions from the Pack Editor discussion.
- `docs/req/` — formal, testable **system requirements derived from stories**; drafts are clearly marked. They are not synonymous with stories.
- `docs/arch/` — architecture documents, to be reconciled against the fresh pilot.
- `docs/test/` — test strategy, procedures, traceability and acceptance evidence.
- `docs/ssdf/` — actual security practices mapped to NIST SSDF and evidence; no unsupported compliance claims.
- `docs/plan/` and `docs/impl/` — active work and verified implementation records.
- `policies/` and `AGENTS.md` — small set of working rules.
- `tests/` — proposed future organization; preserve existing imported tests as-is first.

Traceability: **Epic → Story → REQ → Test → Implementation.** Packs v2 governs the app's persisted Pack/Requirement data; this documentation governs our software development.

## Import the pilot

1. Unzip the **contents of the fresh `poc2/` folder into this repository root** (no extra `poc2/` directory).
2. **Do not overwrite this scaffold's `AGENTS.md`, `README.md` or `.gitignore`** with the PoC2 versions. Compare and migrate any still-needed rules separately.
3. Keep the fresh pilot's code, tests, plans and architecture files at first. Reconcile conflicting documentation in reviewed changes; do not bulk rewrite the pilot during import.
4. Do **not** import `data/workspace/`, signing keys, `.venv/`, caches, job traces or local generated output.
5. Record and run the fresh pilot's test baseline before behavior changes or reorganizing modules.
6. Obtain authoritative `docs/reference/packs2.md` from the **separate Curbpack repository** before changing persistent formats, signing or publishing.

No license is chosen by this scaffold. Repository visibility and release licensing are separate decisions.
