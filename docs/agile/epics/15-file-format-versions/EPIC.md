# EP-15 — File format versions

**Status:** Draft. Not authorization to implement.

**Starts when:** Scheduled. Does not block EP-01. Does not wait for EP-11.

## Goal

`curbpack.json`, a Pack, a Requirement, and a Claim each carry a format version. A reader loads an older file up to the version the running code understands, in memory. Saving that result is a separate step.

## Why this epic exists

The contract has already moved once without a version on the file. `unsigned_requirements` was removed and `namespace_base` became required on `curbpack.json`. Packs and Requirements gained `namespace` and `status`. Claims gained `namespace`, `pack_id`, and `requirement_digest`. A file from before that move is rejected. Nothing records which shape it had, and nothing offers a chain of steps up to the current shape.

`upgrade_stored_claim` in `common/validate.py` is not this mechanism. It rewrites one retired `{check, args}` claim into a `checks` array and writes the file immediately. A claim that already has `checks` is left untouched. Packs, Requirements, and `curbpack.json` have no such function.

## Rules

- The format version is a property of the file, not the Pack release in `pack.json` `version`, and not the on-disk directory `<packs_dir>/<pack-id>/<pack-version>/`.
- The first numbered version is the contract in force when the field is added. A file with no version number is the input to the step that produces that first numbered version.
- Each later contract change has its own function. `1.0` to `1.1` is one function. `1.1` to `1.2` is the next. A step does not skip a version.
- The reader runs the chain from the file's version to the version the code can, and returns the object in memory.
- The reader does not write the file. A separate save writes the upgraded object when someone asks for that.
- The same rules apply to `curbpack.json`, Pack, Requirement, and Claim. Each kind has its own chain. A step for one kind does not rewrite the others.

## Stories

| ID | User goal | Depends on |
| --- | --- | --- |
| [FMT-01](stories/FMT-01-version-and-upgrade-chain.md) | Read an older file of each kind up to the current format version, in memory, and save only when asked. | — |

Draft stories are not permission to implement. A later contract change opens its own step story. It does not grow FMT-01.

## Epic acceptance

- Each of the four file kinds has a format version field once that kind's chain exists.
- Loading a file at an older supported version returns the current version in memory and leaves the file unchanged.
- Loading runs one function per version step, in order.
- Saving the loaded object is a separate call. Load does not save.
- An unsupported version is rejected and the file is unchanged.
- `upgrade_stored_claim` no longer writes a file as a side effect of load. Its retired-shape behavior, if still required, is one step in the Claim chain.

## Out of scope

- A database of versions. Git remains the file history.
- Rewriting the reference product inside this epic. Bringing that tree onto the contract that is current when this epic is written is a direct edit, and it is the baseline the first numbered version describes.
- Changing Check behavior, signatures, or which Pack release a repository selects.
- A screen that edits the version number by hand.

## Relation to other epics

- **EP-11** defines namespace, status, origin, and Claim binding. This epic does not change those meanings. It is how a file from an earlier contract is read after a later one.
- **EP-01** is the pilot. This epic does not gate it. The pilot keeps rejecting a file the current contract cannot read until a story here is accepted and implemented.
