# EP-16 — Text dump split

**Status:** Draft. Not authorization to implement.

**Starts when:** Scheduled. Does not block EP-01 or EP-14.

## Goal

Stage 00 can split one controlled full text into the sections the adapter already names. The adapter file stays the contract for which sections exist. The split does not invent sections, and it does not write over a fixture.

## Why this epic exists

`requirements/ARCHITECTURE.md` used to describe that splitter as current behavior: cut a dump on `ANNEX` headings, add an out-of-scope `_body` for the text before the first annex, and write the cuts under the work directory. `stage00` does none of that. It refuses `dump_text` and returns the `sections` array from `adapter.json`.

The architecture now describes the loader. This epic keeps the splitter as work that is not built.

## Stories

| ID | User goal | Depends on |
| --- | --- | --- |
| [EX-01](stories/EX-01-split-a-full-text.md) | Split one full text into the adapter's sections without touching the fixture | — |

Draft stories are not permission to implement.

## Out of scope

- A new `adapter.json` field, a plugin registry, or a general parser for PDF, HTML, or Markdown.
- Formex. A Formex package is already the whole act.
- Marking more sections ready. That is EP-14 where a cut already exists.
- Changing Packs v2.
