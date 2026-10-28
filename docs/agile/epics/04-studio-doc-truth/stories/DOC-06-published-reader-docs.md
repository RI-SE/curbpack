# DOC-06 — Update the published documents to this repository

**Epic:** [EP-04 Studio documentation truth](../EPIC.md)

**Status:** Draft. Not authorization to edit a document until that document is the current row.

**Starts when:** DOC-01, DOC-02, and DOC-03 are accepted. They are. This story does not reopen them.

**As a reader** who opens the repository README and follows its links, I want each page to describe this repository: Curbpack Studio and curbcheck, in [RI-SE/curbpack](https://github.com/RI-SE/curbpack).

DOC-01–DOC-03 finished the SDD account under `daniel/ny_sdd/`. This story does not merge that tree into `docs/` and does not add a path under `daniel/ny_sdd/`.

## What “adapted” means

A page is adapted when every command, path, button, and file it presents as something to do now exists in this tree.

- The programs are **Curbpack Studio** (`python3 -m app`, or `curbpack-studio-<host>`) and **curbcheck** (`python3 -m checks`, or `curbcheck-<host>`).
- The first-use path is the cover: Pack Editor, Discovery & Claims, Check, Review. Install starts from the downloaded program.
- `poc2/` is not a directory to `cd` into. `curbpack scan`, `curbpack check`, `curbpack share`, and `curbpack init` are not commands this repository provides.
- A page that only remembers the old CLI says so in its first paragraph, and a user guide does not link to it.
- The page does not send the reader to a file this repository does not contain.

Describe what this tree runs today. [SYS-03](../../01-pack-editor/stories/SYS-03-one-repo-door.md) decided a `curbpack` directory layout that is not implemented. Do not write that layout into these pages. [DOC-04](../../01-pack-editor/stories/DOC-04-single-persistent-model.md) owns the Packs v2 contract. Do not edit `docs/reference/packs2.md` here.

Working-tree edits already on the front door are not acceptance. Read the file as it is, keep an edit that already meets this rule, and change the sentence that does not.

## How to walk

One row at a time, in the order below. Skip a row whose disposition is **leave**. The current row is the first **open** row.

When the maintainer asks for the next document, read that file against the rule above, propose the edit, and stop. Do not open the following row in the same turn.

## A. Front door

These are the README, the top links, and the Start here table.

| ID | Path | Disposition | What is true now |
| --- | --- | --- | --- |
| DOC6-01 | `README.md` | open, read-through | Working tree names Studio, curbcheck, and `RI-SE/curbpack`. Not accepted. |
| DOC6-02 | `docs/README.md` | open, read-through | Same. The role table and the pass sentence are already shortened in the working tree. |
| DOC6-03 | `docs/user-guides/install.md` | open, read-through | Working tree leads with the downloaded program. Source checkout is at the bottom. |
| DOC6-04 | `docs/user-guides/getting-started.md` | open, read-through | Working tree walks Pack Editor, Discovery & Claims, Check, and Review. |
| DOC6-05 | `docs/user-guides/reviewers.md` | open, read-through | Working tree says a person still decides. Confirm the rest of the page. |
| DOC6-06 | `docs/user-guides/developers.md` | open, read-through | Opening points at Getting started. The longer procedure is not yet passed. |
| DOC6-07 | `docs/user-guides/ci-cd.md` | open, read-through | Names `python3 -m checks` and the packaged `curbcheck` files. Pass the whole page. |
| DOC6-08 | `docs/user-guides/pack-developers.md` | open, mixed | Pack Editor steps match this tree. The last line still says the Getting started shape is on Glucose Log. |
| DOC6-09 | `docs/user-guides/troubleshooting.md` | open, read-through | Startup section names the downloaded program. Pass the rest. |
| DOC6-10 | `docs/user-guides/README.md` | open, mixed | Not linked from the root README. Step 2 still says to try the reference product. Make the index match Getting started. |
| DOC6-11 | `CONTRIBUTING.md` | open, read-through | First sentence names this repository, Studio, and curbcheck. Pass the rest for old commands. |

## B. Next click from the documentation index

`docs/README.md` sends a reader here after the guides. `docs/reference/packs2.md` is on that page and is **leave**: the six tool names in its table stay until DOC-04.

| ID | Path | Disposition | What is true now |
| --- | --- | --- | --- |
| DOC6-12 | `docs/concepts/README.md` | open, read-through | Names curbcheck and `curbpack.json`. Pass it. |
| DOC6-13 | `docs/concepts/packs.md` | open, read-through | Describes Pack, Requirement, and Claim as this tree stores them. `claims/` is the layout Check loads today. Do not move it to the SYS-03 directory. |
| DOC6-14 | `docs/concepts/evidence.md` | open, read-through | Names curbcheck. Pass it. |
| DOC6-15 | `docs/concepts/end-to-end-scenario.md` | leave | First lines say the scenario is historical and not normative. Do not modernize the body. |
| DOC6-16 | `docs/reference/configuration.md` | open, read-through | Describes today's `curbpack.json` and `claims/*.json`. Do not add the SYS-03 `curbpack` directory key. |
| DOC6-17 | `docs/reference/curbcheck-cli.md` | open, read-through | Says the program does not scan, init, heal, or prepare a release. Pass the flags against `python3 -m checks`. |
| DOC6-18 | `docs/reference/outputs.md` | open, read-through | Not linked from the root README. Opening names `python3 -m checks`. Pass it. |
| DOC6-19 | `docs/reference/stable-contracts.md` | open, read-through | Report shape. Do not weaken a field. Only fix a sentence that names a program this tree does not run. |
| DOC6-20 | `docs/reference/README.md` | open, read-through | Says the old repository is not required to read Packs v2. Confirm that is all a reader needs. |

## C. Contributor path

The README reaches these from the contributor row and from Development.

| ID | Path | Disposition | What is true now |
| --- | --- | --- | --- |
| DOC6-21 | `docs/development/README.md` | open, read-through | Separates `make test` from `make test-curbcheck`. Temporary notes are labeled. |
| DOC6-22 | `docs/development/ci.md` | open, read-through | Product-pipeline examples use `RI-SE/curbpack`. Pass the jobs. |
| DOC6-23 | `docs/development/xml-sources.md` | open, old | Tells the reader to `cd poc2` and reads `poc2/requirements/extract/data/official_xml/`. Those paths are not this tree. |
| DOC6-24 | `docs/development/cli.md` | leave | Temporary crosswalk of `curbpack scan`, `init`, `check`, and `share`. Keep the first paragraph. A user guide must not link here. |
| DOC6-25 | `docs/development/pack-authoring-crosswalk.md` | leave | Same kind of note for the old `pack.json` rules. Keep it. A user guide must not link here. |
| DOC6-26 | `docs/testing/README.md` | open, read-through | Tells the tester not to run `curbpack check`. Confirm the commands are `python3 -m checks` and `make test-curbcheck`. |
| DOC6-27 | `docs/testing/` below that README | leave | The carried suite. Glucose Log is the reference product. TST-01 and VER own the catalogue. |
| DOC6-28 | `AGENTS.md` | open, read-through | Agent instructions. Change only a command that is the old CLI. |

## D. Architecture, after the guides

A reader hits `docs/arch/ARCHITECTURE.md` from the bottom of the root README and from “Already in this repository”. These files are contracts. Replace a path that does not exist. Do not move code, do not invent a target tree, and do not apply SYS-03.

| ID | Path | Disposition | What is true now |
| --- | --- | --- | --- |
| DOC6-29 | `docs/arch/README.md` | open, read-through | Index. It points at the system architecture page that still says `poc2/`. |
| DOC6-30 | `docs/arch/SYSTEM.md` | open, read-through | Index only. |
| DOC6-31 | `docs/arch/ARCHITECTURE.md` | open, old | Header says each `poc2/` path means this repository. The body still draws `poc2/`. |
| DOC6-32 | `docs/arch/SYSTEM_REQUIREMENTS.md` | open, read-through | Inherited ids. Leave MUST-01 and MUST-02. Fix only a sentence that names a program this tree does not run. |
| DOC6-33 | `requirements/ARCHITECTURE.md` | open, old | Subsystem contract. Still cites `poc2/` and PoC2. |
| DOC6-34 | `claims/ARCHITECTURE.md` | open, old | Same. SYS-03 already called its path sentences stale. Do not switch them to the unimplemented directory. |
| DOC6-35 | `checks/ARCHITECTURE.md` | open, old | Same. |
| DOC6-36 | `review/ARCHITECTURE.md` | open, old | Same. |

## E. Not on the reader path

Do not open these unless the maintainer names one.

| Path | Why it stays out |
| --- | --- |
| `docs/reference/packs2.md` | Persistent contract. DOC-04. The tool table still names `curbpack-claims`, `curbpack-scaffold`, `curbpack-compile`, and `curbpack-review`. |
| `daniel/ny_sdd/` | Finished SDD account. An extra file there fails EP-04. |
| `docs/agile/` except the EP-04 row and this story | Backlog. Stories are not the product manual. |
| `docs/agile/future_architecture.md`, `docs/agile/future_cicd.md` | Drafts. Not in force. |
| `docs/req/` | Derived requirements. Do not invent one to finish a sentence. |
| `docs/ssdf/` | Evidence map, not a user guide. `harness.md` names PoC2 as a historical source. |
| `docs/test/README.md` | Pointer to keep the pilot tests. Not linked from the README. |
| `policies/` | Engineering rules for this repository. |
| `impl/`, `plan/` | Execution records. Do not resume a story from `impl/`. |
| `tests/check/`, `testdata/`, `data/reference/` | Fixtures, catalogues, and provenance. |
| `all-md.md` | Untracked dump. |

## Accept when

- Every **open** row above is either passed or explicitly left, and the pass is a sentence in this story naming what was checked.
- No user guide links to `docs/development/cli.md` or `docs/development/pack-authoring-crosswalk.md`.
- `docs/reference/packs2.md` and `daniel/ny_sdd/` are unchanged by this story.
- No page tells a reader to `cd poc2` or to run `curbpack scan`, `curbpack check`, `curbpack share`, or `curbpack init` as a command this repository provides.

## Stop if

- A true sentence would require a Packs v2 field `docs/reference/packs2.md` does not define.
- A true sentence would require the SYS-03 directory layout, which is not implemented.
- Rewriting an architecture page would choose a target tree the code does not have.
- The page is historical and already says so.

Record the conflict on the row and stop that row. Do not resolve it by writing the unimplemented layout as if it were current.
