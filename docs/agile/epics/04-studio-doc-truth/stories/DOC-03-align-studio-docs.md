# DOC-03 — Align the other text

**Epic:** [EP-04 Studio documentation truth](../EPIC.md)

**Status:** Done.

**Starts when:** DOC-02 is accepted.

**As a developer**, I want every file under `daniel/ny_sdd/` to keep its language and structure, with the content adapted to Studio as `docs/` describes it, and one delta for what was removed, simplified, or missed.

## Read

`docs/`, starting at `docs/README.md` and `docs/reference/packs2.md`. `docs/concepts/end-to-end-scenario.md` is a historical scenario and is not normative. `docs/development/`, `docs/agile/`, and `docs/testing/` are not sources. Read `daniel/ny_sdd/` as the text to align. The requirement list is DOC-02's file. Do not rewrite it.

## Write only

Paths under `daniel/ny_sdd/`, except `docs/REQUIREMENTS.md`. The merge into `docs/` is the next story.

## Rules

Keep the language, the structure, and the way each file is written. That prose was cleaned by hand. Do not write it again in new sentences.

Change the content so the facts match Studio as `docs/` describes it. A file should read as complete: a link resolves, and nothing in the file tells the reader that the body is some other document. Where an existing sentence can carry the Studio fact, change that fact and keep the sentence. Where it cannot, take the sentence out and record the id in the delta. The delta is the list. It is not a hole in the page.

`daniel/ny_sdd/docs/architecture/packs2.md` is a byte copy of `docs/reference/packs2.md`.

The tools are `curbpack-requirements`, `curbpack-claims`, `curbpack-scaffold`, `curbcheck`, `curbpack-compile`, and `curbpack-review`. `curbpack-requirements` is the tool that processes requirements. The packs2 table still labels that row Requirements. Discover is a mode inside `curbpack-claims`. A Studio document that still uses another name is a delta row.

The use case is the one in `docs/README.md`.

Do not rename `MUST-*`, `INV-*`, `FG-*`, `REG-*`, `INT-*`, `ACC-*`, `W0`–`W8`, or a metric key in `docs/TESTING.md`. Do not restore a label from `docs/reading-rules.md`.

`docs/baseline-delta.md` has columns `id`, `change`, `baseline`, and `studio source`. `change` is `done`, `simplified`, or `missed`. One row per id that is not already the same fact as `docs/`. `done` means Studio has arrived at it and the text now says that. `simplified` means the text states only the narrower fact. `missed` means it is not done. A `missed` id is not left as if Studio did it. It stays in the delta so a test can cite it.

## Accept when

- `cmp docs/reference/packs2.md daniel/ny_sdd/docs/architecture/packs2.md` prints nothing and exits 0.
- `find daniel/ny_sdd -type f | sed 's#^daniel/ny_sdd/##' | sort` prints `docs/baseline-delta.md` and the epic paths, with `packs2.md` in place of `packs.md`, and nothing else.
- `docs/REQUIREMENTS.md` still has every matrix id, and the sentence for that id. A disposition cell says where that sentence is.
- Every delta id appears once, and its `change` is `done`, `simplified`, or `missed`.
- `README.md` links to `docs/baseline-delta.md`.
- No file under `daniel/ny_sdd/` except `docs/baseline-delta.md` contains the phrase `moved Curbpack baseline`.

## Stop if

A match needs a Packs v2 field `docs/reference/packs2.md` does not define. Mark the id `missed`, name the field in `studio source`, and do not add the field.
