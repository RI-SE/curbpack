# DOC-01 — Mirror the split

**Epic:** [EP-04 Studio documentation truth](../EPIC.md)

**Status:** Done. The move is commit `8a712b9`.

**Starts when:** now. DOC-02 does not start until this story is accepted.

**As a developer**, I want `curbpack/daniel/ny_struktur` mirrored as `daniel/ny_sdd/`, so the split that already exists is the structure Studio continues from.

The split is good enough. This story does not rewrite it toward Studio, does not replace `docs/architecture/packs.md`, and does not add a gap register. Those belong to DOC-03. The requirement list belongs to DOC-02.

## Write only

Paths under `daniel/ny_sdd/`. Same relative paths as the source. After the move, `curbpack/daniel/ny_struktur` is gone.

## Accept when

- `find daniel/ny_sdd -type f | sed 's#^daniel/ny_sdd/##' | sort` prints the 17 epic paths and nothing else.
- A sentence in those files is the sentence from the source. The language pass dated 2026-10-24 stays as it was.
- `curbpack/daniel/ny_struktur` does not exist.

## Definition of done

The find command is the file check. The Studio commit contains only paths under `daniel/ny_sdd/`. The Curbpack commit only removes `daniel/ny_struktur`.
