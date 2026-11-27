# EX-01 — Split a full text into the adapter's sections

**Status:** Draft. Not authorization to implement.

**Epic:** [EP-16 Text dump split](../EPIC.md)

**Starts when:** Scheduled. Does not block EP-01 or EP-14.

**As a developer**, I want stage 00 to cut one controlled full text into the sections the adapter already lists, so that a fixture is not the only way to hold a text section.

### Behavior to restore, from the text removed from the architecture

- A dump is split on lines of the form `ANNEX` plus a roman numeral.
- Text before the first annex is section `_body`. `_body` is not an `adapter.json` section, it is not in scope, and it is not atomized.
- An annex the dump contains and the adapter does not list is out of scope and not ready.
- The cut text is written under the work directory. It is not written into the adapter directory.
- Replacing an adapter fixture with a cut is a separate, deliberate change of the controlled source.

`stage00` today refuses `dump_text`. This story is that refusal becoming the split above. It does not add a new adapter field.

### Out of scope

- Formex packages.
- Choosing which sections are ready.
- Requirement ids, discovery hints, or assemble.
