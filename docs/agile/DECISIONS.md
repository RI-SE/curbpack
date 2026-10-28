# Agreed design decisions and open questions

This short record preserves conclusions from the Pack Editor discussion. It is **not** a substitute for user stories, formal requirements, the existing pilot, or authoritative Packs v2 contracts. Do not implement the open ideas merely because they appear here.

## Agreed for the pilot and next iteration

- The app start page shows the existing tools. Pack Editor is one of them; no redesign of the launcher is requested.
- Pack Editor has **two levels**. First: one row per editable Pack, with Pack name, the regulatory document and its chosen adapter, plus **Edit** and potentially **Publish**. Second: **Edit** opens that Pack's existing list of sources. The selected document and adapter are displayed in the heading instead of repeated on each row; the source rows retain **Extract** and **Edit**. **Add Source** belongs on this second level.
- This is **one extra navigation level**, not a replacement for the existing source editor, extraction workflow, requirement editor, comparison UI or signing process. Do not create a separate Pack Publisher subsystem to achieve it. **Publish** is a Pack-level action, not an individual source-row action.
- A source records the appropriate section/range and URL used to reach the original legal text. Do not silently conflate a *source row*, the *sections that an adapter can enumerate*, and the *Requirement references* stored in Packs v2. The exact source/section selection semantics must be checked against the fresh pilot before changing them.
- An adapter is the document-specific extraction logic/configuration: for example a short program or configuration that identifies document structure and supplies regulatory sections/text to the extractor. Its implementation format is **not** a new Packs v2 field or a decision to require YAML.
- **Extract** continues to use the selected source, its document/adapter configuration and the existing extraction UI; the current view of supported/remaining sections, run progress and diagnostics must not be lost without a conscious decision.
- Re-running Extract may reflect revised legal text, a different prompt/model or an improved adapter. The new output is a **proposal**. Compare old and new and let the user explicitly apply or discard supported changes. No silent replacement or deletion; preserve unrelated Requirement fields and source references.
- All Requirements remain traceable to the original regulatory document, edition and exact supporting passages/locations, including multiple legal references when required. Editing, re-extraction and new Pack versions must not erase this provenance. Modified signed payloads need new signatures. Published versions remain immutable.
- Packs v2 is the authoritative persisted Pack/Requirement contract. Pack membership uses `requirement.pack_id`; legal provenance uses `source` and `references[]`. `origin` is reserved for descent from a published Pack, not extraction provenance. Adapter/model/prompt/run diagnostics belong outside normative Requirement fields. Confirm precise semantics against `docs/reference/packs2.md` before coding.
- Pilot-first: import implementation and tests **only from a fresh PoC2 ZIP**, establish its actual test baseline, finish the pilot and avoid premature refactoring. The starter includes no PoC2 code, keys or generated workspace.
- The license is Apache-2.0, as `LICENSE`. A later change of license is a separate ownership decision.

## Explicitly open — do not decide automatically

- How the editable workspace maps to **Git repository, working tree and branch**. The existing per-source **Working copy** column may not be the right concept. Git is considered the intended working environment, but the workflow/UI is not agreed.
- **Multi-version Pack workflow** (side-by-side releases, has-update marks, pack-exchange zip, Claim impact after taking in a new release, optional SQLite index) lives in draft epic [EP-11](epics/11-pack-version-lifecycle/EPIC.md). It is not EP-01 pilot scope.
- **Pilot simplification (agreed for EP-01 focus):** the operator may work against the **latest / single active** working copy or selected Pack release only. Immutable `published/<id>/<version>/` trees may already exist on disk; the pilot does not have to offer editing multiple versions at once. Full multi-version grip is EP-11.
- The exact meaning of a source row versus adapter-enumerated section choices; retain the working pilot behavior until agreed otherwise.
- Whether to extract multiple sections per operation; a single section at a time suffices as the initial behavior.
- How the user explicitly confirms the treatment of a Requirement that disappears on re-extraction. Its disappearance must be visible and cannot silently delete approved work.
- Whether Pack publication includes all eligible reviewed Requirements or a deliberate selected subset.
- Public repository visibility and authorization to publish code remain separate ownership decisions. The license is not one of them.

## Ideas for later epics, not Pack Editor requirements

- The development container (build and start with Make, same build in CI) is draft [EP-12](epics/12-development-environment/EPIC.md). It is not a pilot requirement.
- Aslak's old `extends` is **not automatically equivalent** to a simple dependency. Before introducing Pack inheritance or silent overrides, establish whether the real need is an explicit `requires` dependency. A narrowly configured **Check** could, for example, verify that a required Pack ID/version is present in `curbpack.json`. This is an idea, **not an approved new Packs v2 field or implemented Check**. Passing such a Check verifies only that configured condition, not overall legal compliance.
- Claims/Discovery, Checks, Compile and Review require their own user journeys, stories and derived Requirements. Existing PoC2 functions are references; these stories are not fabricated here.
- The long-term specification quality goal is that an independent developer or local-model-assisted agent can reconstruct **equivalent observable application behavior**, validated by the same acceptance and regression tests. Identical source code is neither necessary nor guaranteed. Do not treat this as a pilot feature request.
