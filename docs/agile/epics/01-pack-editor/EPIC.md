# EP-01 — Complete Functional Pilot

**Status:** In progress. Functional scope agreed; acceptance is not yet verified.

**Goal:** A user can work through the complete Curbpack Studio pilot: author traceable regulatory Requirements, associate product evidence through Claims, run deterministic Checks, and produce a reviewable, signable report.

The pilot must work **before EP-02 (modularizing Studio)**. This epic is about functional completion and verification, not reorganizing code.

## User journey

1. Open one repository. Its `curbpack.json` names the Pack ids, and a packs root locates those Packs. Authoring uses a root inside that repository. A product repository may point the root at an exported packs directory. [SYS-03](stories/SYS-03-one-repo-door.md) is that door.
2. Edit the Pack's existing source list; extract, compare, edit and sign Requirements without losing source references. Export the selected Pack with PE-11. That export is not a published release.
3. Stay on the repository SYS-03 opened. Claims associate Requirements with evidence in that repository's `claims/`. The packs root locates the Pack files.
4. Run the configured Checks against that evidence and inspect PASS, FAIL and justified SKIP outcomes.
5. Compile the actual run results, review them and sign a report. A previous report must never be misrepresented as a report of the latest run.

Preserve existing functioning user flows. Document and verify what the imported pilot already does; implement only missing behavior. Do not infer that an interface screenshot proves a function works.

## Stories

| ID | User goal |
| --- | --- |
| SYS-03 | One repository is the door for Packs, Claims, Check, and Review. Required for the pilot. |
| SYS-04 | Rename the repository key `hunt` to `search_hints`. |
| PE-01–PE-11 | Choose Packs; extract, review, edit, sign and export Requirements |
| CHK-01 | One `curbpack.json` page: what was loaded, which Packs and Requirements, and that repo's Claims |
| CHK-02 | Run deterministic Checks on configured Claims |
| CHK-03 | Understand PASS, FAIL and SKIP outcomes |
| CHK-04 | Trace each result to the checked evidence and revision |
| CHK-06 | Ship curbcheck as its own program |
| REV-01 | Compile a report from a specific Check run |
| REV-02 | Review and sign a report without confusing different runs |
| DOC-04 | One authoritative Packs v2 model and matching JSON Schemas |
| SYS-01 | Complete and verify the full pilot workflow |
| SYS-02 | Keep every pipeline case in the one functional suite. Not a release blocker. |

Story details: [`stories/`](stories/). PE-11 is Export. SYS-03 is the door those pages share.

## Epic acceptance

- Demonstrate **Requirements → Claims → Checks → Report → Review** on a real test product repository.
- Demonstrate a valid PASS, a missing-evidence FAIL, and a SKIP with a recorded reason where skipping is permitted.
- The output identifies the Pack/version, Requirement, Claim, configured Checks, evidence and product revision, with clear limits on what was verified.
- Re-running Checks does not silently replace an already signed review report or make an old report appear current.
- Previously passing tests continue to pass, and recorded end-to-end acceptance results support the demonstrated behavior. Known pre-existing failures are reported, not hidden.
- Packs v2 is unchanged unless a separate, explicitly reviewed contract decision is made.
- `make package` builds the Studio application and a separate curbcheck program. The Studio file does not contain the check programs. From source, `python3 -m checks` still runs them.

**Not part of EP-01:** splitting up large GUI files, introducing shared Pydantic modules, central database deployment, or rewriting the Check engine for architectural neatness. Those improvements belong to later work, including EP-02. The development container is [EP-12](../12-development-environment/EPIC.md). **Multi-version Pack grip** (side-by-side releases, pack-exchange, Claim impact, SQLite index) is draft [EP-11](../11-pack-version-lifecycle/EPIC.md); the pilot may focus on the single active / latest working copy or selected release.

## Specification status

Pack Editor has draft derived requirements in [`docs/req/pack-editor.md`](../../../req/pack-editor.md). CHK-06 has approved rows CHK-R14–CHK-R17 in [`docs/req/checks.md`](../../../req/checks.md). The other CHK, REV and SYS stories **do not yet have formal derived requirements or approved acceptance tests**. Their next step is to compare these stories with the fresh pilot, identify real gaps and specify/test only those gaps before implementing changes.

Open product decisions and provenance rules: [`docs/agile/DECISIONS.md`](../../DECISIONS.md). Packs v2 in the Curbpack repository remains the authoritative persisted data contract. [DOC-04](stories/DOC-04-single-persistent-model.md) proposes one Studio model contract for that data. It is draft and is not authorization to implement.
