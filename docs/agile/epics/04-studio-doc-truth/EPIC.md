# EP-04 — Studio documentation truth

**Status:** Done. `daniel/ny_sdd/` is the Studio account. Merging it into `docs/` is the next story.

**Goal:** `daniel/ny_sdd/` ends as the Studio account of the moved baseline.

1. Packs v2 is the data structure. `docs/architecture/packs2.md` is a byte copy of `docs/reference/packs2.md`.
2. The tools are `curbpack-requirements`, `curbpack-claims`, `curbpack-scaffold`, `curbcheck`, `curbpack-compile`, and `curbpack-review`. `curbpack-requirements` is the requirements tool. The packs2 table still labels that row Requirements. Discover is a mode inside `curbpack-claims`.
3. Requirement ids and their substance stay, because the test cases cite them.
4. The text describes what Studio has arrived at. The language, the structure, and the way of writing stay. The use case is the one in `docs/README.md`.
5. `docs/baseline-delta.md` is the list of what was done, simplified, or missed. One row per id. No second register.

## Paths

DOC-01 mirrors these 17 files from `curbpack/daniel/ny_struktur`:

`AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS.md`, `docs/TESTING.md`, `docs/acceptance.md`, `docs/adr/README.md`, `docs/architecture/checks.md`, `docs/architecture/evaluation.md`, `docs/architecture/packs.md`, `docs/architecture/review.md`, `docs/architecture/signatures.md`, `docs/baseline/verified-baseline.md`, `docs/governance/product-trust.md`, `docs/plans/work-packages.md`, `docs/reading-rules.md`.

DOC-03 replaces `docs/architecture/packs.md` with `docs/architecture/packs2.md` and adds `docs/baseline-delta.md`. An extra path fails the epic.

## Stories

| ID | User goal | Starts when |
| --- | --- | --- |
| [DOC-01](stories/DOC-01-ny-sdd-structure.md) | Mirror the split under `daniel/ny_sdd/` | Done |
| [DOC-02](stories/DOC-02-curbcheck-requirements.md) | Keep the requirement list, ids and substance | Done |
| [DOC-03](stories/DOC-03-align-studio-docs.md) | Align the other text with `docs/` and write the delta | Done |

## Epic acceptance

- `cmp docs/reference/packs2.md daniel/ny_sdd/docs/architecture/packs2.md` prints nothing and exits 0.
- `find daniel/ny_sdd -type f | sed 's#^daniel/ny_sdd/##' | sort` prints `docs/baseline-delta.md` and the paths above, with `packs2.md` in place of `packs.md`, and nothing else.
- Every matrix id from `docs/testing/requirements_traceability.md` is still a requirement in `docs/REQUIREMENTS.md`, with the same id. The matrix row count and that row count are equal.
- `docs/baseline-delta.md` has one row per id that was done, simplified, or missed, and no other status.

## Out of scope

`docs/testing/`, `docs/reference/test-packs/`, application code, and `cyberready-test-product`. Those are EP-06, EP-05, and EP-07. Merging `daniel/ny_sdd/` into `docs/` is the next story.
