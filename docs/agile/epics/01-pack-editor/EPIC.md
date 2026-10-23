# EP-01 — Complete Functional Pilot

**Status:** In progress. Functional scope agreed; acceptance is not yet verified.

**Goal:** A user can work through the complete Curbpack Studio pilot: author traceable regulatory Requirements, associate product evidence through Claims, run deterministic Checks, and produce a reviewable, signable report.

The pilot must work **before EP-02 (modularizing Studio)**. This epic is about functional completion and verification, not reorganizing code.

## User journey

1. Open Pack Editor and choose or add a Pack. Each editable Pack has a regulatory document and a configured adapter.
2. Edit the Pack's existing source list; extract, compare, edit and sign Requirements without losing source references. Publish the selected Pack under a version.
3. Select a product repository and the applicable published Packs, then use Claims to associate Requirements with specific product evidence.
4. Run the configured Checks against that evidence and inspect PASS, FAIL and justified SKIP outcomes.
5. Compile the actual run results, review them and sign a report. A previous report must never be misrepresented as a report of the latest run.

Preserve existing functioning user flows. Document and verify what the imported pilot already does; implement only missing behavior. Do not infer that an interface screenshot proves a function works.

## Stories

| ID | User goal |
| --- | --- |
| PE-01–PE-11 | Choose Packs; extract, review, edit, sign and publish Requirements |
| CHK-01 | Select a product repository and applicable Packs |
| CHK-02 | Run deterministic Checks on configured Claims |
| CHK-03 | Understand PASS, FAIL and SKIP outcomes |
| CHK-04 | Trace each result to the checked evidence and revision |
| REV-01 | Compile a report from a specific Check run |
| REV-02 | Review and sign a report without confusing different runs |
| SYS-01 | Complete and verify the full pilot workflow |
| SYS-02 | Keep every pipeline case in the one functional suite. Not a release blocker. |

Story details: [`stories/`](stories/). The original Pack Editor stories remain unchanged.

## Epic acceptance

- Demonstrate **Requirements → Claims → Checks → Report → Review** on a real test product repository.
- Demonstrate a valid PASS, a missing-evidence FAIL, and a SKIP with a recorded reason where skipping is permitted.
- The output identifies the Pack/version, Requirement, Claim, configured Checks, evidence and product revision, with clear limits on what was verified.
- Re-running Checks does not silently replace an already signed review report or make an old report appear current.
- Previously passing tests continue to pass, and recorded end-to-end acceptance results support the demonstrated behavior. Known pre-existing failures are reported, not hidden.
- Packs v2 is unchanged unless a separate, explicitly reviewed contract decision is made.

**Not part of EP-01:** splitting up large GUI files, introducing shared Pydantic modules, central Docker/database deployment, or rewriting the Check engine for architectural neatness. Those improvements belong to later work, including EP-02.

## Specification status

Pack Editor has draft derived requirements in [`docs/req/pack-editor.md`](../../../req/pack-editor.md). CHK, REV and SYS stories **do not yet have formal derived requirements or approved acceptance tests**. Their next step is to compare these stories with the fresh pilot, identify real gaps and specify/test only those gaps before implementing changes.

Open product decisions and provenance rules: [`docs/agile/DECISIONS.md`](../../DECISIONS.md). Packs v2 in the Curbpack repository remains the authoritative persisted data contract.
