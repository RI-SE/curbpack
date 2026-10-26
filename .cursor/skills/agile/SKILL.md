---
name: agile
description: Print a one-line board of Curbpack Studio epics and stories. Use when the user runs /agile or asks which epics and stories are done, in progress, waiting, or ready.
disable-model-invocation: true
---

# Agile board

Print the board and stop. Read the files yourself. Write nothing. Do not edit stories, plans, or git.

## Read

- `docs/agile/epics/*/EPIC.md` and each `stories/*.md`
- `plan/<STORY-ID>.md`, else `docs/plan/<STORY-ID>.md`
- The code and tests named by a story's accept-when, before calling it STARTKLAR

## Epics

An epic is KLAR when every one of its stories is KLAR. Print one line and no stories:

`EP-02 — Modularize Studio — KLAR`

Any other epic gets a heading and one line per story, in the epic table's order. Add a story file the table omits. Omit a row the epic says is not part of that epic.

## Status

Use the first match.

1. **KLAR** — the plan's `Plan status` is DONE, or the story and the epic table both say Done.
2. **STOPPAD** — the plan is BLOCKED, checkpoint Blockers is not None, or a task is BLOCKED.
3. **RUNNING** — the plan is APPROVED and a task is unfinished.
4. **UTKAST** — the plan is DRAFT.
5. **FINNS** — the accept-when already happens in the current code and a test covers that behavior. A library function does not count when the control the story names does nothing.
6. **VÄNTAR** — no plan, and a story or epic named under Starts when is not KLAR or FINNS.
7. **STARTKLAR** — no plan, dependencies are met, and the behavior is not already present.
8. **OSÄKER** — a dependency sentence cannot be applied. Do not call that story STARTKLAR.

`Status: Draft` on a story is not an implementation result. A missing plan does not mean the behavior is missing. `Starts when: now` is no dependency. An epic-level wait applies to every story in that epic.

## Shape

The board is the whole reply. No sentence before it and none after.

The first line counts only the rows printed:

`Läget: 0 epic klara · 2 running · 1 utkast · 0 stoppade · 16 finns · 3 startklara · 18 väntar · 2 osäkra`

A blank line, then the epics in numeric order. A blank line between epics.

Do not pad with dashes or spaces, and do not wrap the board in a code fence. Status is its own table column so the rows stay aligned.

A KLAR epic is one plain line and nothing under it:

`EP-04 — Studio documentation truth — KLAR`

Any other epic is a heading, then one markdown table. Columns are `ID`, `Namn`, and `Status`. One story is one row. The short name is a few words from the title. The status cell is the status word only. No sentence in any cell.

```markdown
EP-01 — Complete Functional Pilot

| ID | Namn | Status |
| --- | --- | --- |
| PE-02 | List Packs | FINNS |
| CHK-05 | Git provenance | RUNNING |
| | Task 5 · git_signed, git_signer | inte gjord |
| | nästa | Task 5 |
```

RUNNING, UTKAST, and STOPPAD add one row per task under the story. The ID cell is empty. The name cell is `Task N ·` plus a few words. The status cell is `gjord`, `inte gjord`, or `stoppad`. RUNNING adds one more row: name `nästa`, status the checkpoint's current task (`Task 5`). FINNS, KLAR, and STARTKLAR get no extra rows.

VÄNTAR, OSÄKER, and STOPPAD may put a few words in the status cell: `VÄNTAR · EP-01`.
