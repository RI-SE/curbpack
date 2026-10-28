# SYS-04 — Rename repo hunt to search_hints

**Status:** Decided 2026-10-28 by danielfl. The key rename is in `docs/reference/packs2.md` and the validator. A file that still has `hunt` is rejected.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a pilot user**, I want the repository search scope in `curbpack.json` to be called `search_hints`, so that the file says what it is.

The object stays the one Packs v2 already defines: `sources`, `exclude_path_globs`, and `prefer_path_globs`. Merge stays the same: the repository object, then that Requirement's `discovery_hints`. `discovery_hints` is not renamed. Review wording such as re-hunt, and hunt YAML in other epics, are not this card.

### HINT-R01 — The key is search_hints

**Given** a repository `curbpack.json`  
**When** it sets the shared search scope  
**Then** the key is `search_hints`  
**And** a file that still has `hunt` is rejected  
**And** Studio and curbcheck read `search_hints` for the scope they used to read from `hunt`.

### HINT-R02 — The contract text uses the new key

**Given** `docs/reference/packs2.md` §2.3  
**When** this story is done  
**Then** the repository example and the merge sentence say `search_hints`  
**And** they do not tell a reader to write `hunt`.
