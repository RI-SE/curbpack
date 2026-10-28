# VL-07 — Claims after a Pack update is taken in

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** VL-06; Claims / product selection stories under EP-01.

**As a Claim author**, I want a visible impact list when the product starts using a newer Pack release, so that Claims are not silently assumed to still match changed Requirement payloads.

## Pedagogical example (normative shape)

A product team has bought `cra-baseline` `1.0.0`, run Discovery, and signed Claims in the product repository. The statute is then revised. Release `1.1.0` arrives. The impact list runs when the team switches the loaded tree. The scene below uses Packs v2 and VL-06. It adds no Claim field.

**Scene, still on `1.0.0`.**

`published/cra-baseline/1.0.0/` is the loaded release. Product `curbpack.json` lists `cra-baseline`. The product repository holds three signed Claims:

| Claim | `requirement_id` | Evidence the human saved |
| --- | --- | --- |
| `claim-risk` | `CRA-ANNEX-VII-RISK` | `docs/annex-vii/risk_assessment.md` |
| `claim-gone` | `CRA-OLD` | `docs/legacy/old-control.md` |
| `claim-same` | `CRA-STABLE` | `docs/stable/control.md` |

Discovery suggested candidates from the repo `hunt` and that Requirement's `discovery_hints`. Each saved Claim was an explicit human save, with `source`, `args`, `description`, and `checks[]`. The signature covers that Claim payload. The Claim records `requirement_id` only. A Check pass monitors those arguments.

**`1.1.0` is imported, then loaded.**

`published/cra-baseline/1.1.0/` is imported beside `1.0.0` (VL-06). The `1.0.0` directory stays byte-identical. Import leaves `curbpack.json`, the loaded tree, and the Claim files as they are. The impact list stays off while `1.0.0` remains loaded.

The new release, produced earlier by VL-02–VL-04, differs as follows. `claim-risk` is a change of legal text. A release whose only Requirement difference is `discovery_hints` is the OPEN hint row, and is not this example.

| Requirement | In `1.0.0` | In `1.1.0` |
| --- | --- | --- |
| `CRA-ANNEX-VII-RISK` | digest D0, `source.edition` `2024-11-20`, passage at its locator | same id, digest D1 ≠ D0, `source.edition` `2026-12-01`, replacement `law_text` at that locator |
| `CRA-OLD` | present | absent |
| `CRA-STABLE` | digest D | digest D |

The team switches the loaded tree from `1.0.0` to `1.1.0`. The list compares those two releases:

| Claim | `requirement_id` | In 1.0.0 | In 1.1.0 | List, before confirmation |
| --- | --- | --- | --- | --- |
| `claim-risk` | `CRA-ANNEX-VII-RISK` | present, digest D0, edition `2024-11-20` | present, digest D1 ≠ D0, edition `2026-12-01` | needs review |
| `claim-gone` | `CRA-OLD` | present | absent | unbound |
| `claim-same` | `CRA-STABLE` | digest D | digest D | ok |

The list shows Requirement id, both digests, and edition or locator, so the old and new passages can be told apart. Check results stay the runner's results. A passing Check leaves "needs review" and "unbound" on the list.

**Confirmation.** The list writes nothing by itself. These are the human actions already named for a listed Claim:

| Confirmation | Who acts | Result |
| --- | --- | --- |
| keep | the human, on a "needs review" or "unbound" row | The Claim file stays, including `requirement_id`, evidence `args`, and `signed`. An unbound Claim stays unbound. |
| rebind | the human, in the Claims editor | An explicit edit of evidence `args` and/or `requirement_id`. The editor writes the Claim after that confirmation. The changed payload is outside the previous signature. Signing again is a separate action. |
| retire | the human, in the Claims editor | An explicit delete of that Claim after its own confirmation. The list does not delete the file. |

`claim-same` needs no confirmation. Its file stays.

On `claim-risk` the human may open Discovery for `CRA-ANNEX-VII-RISK` and save a further Claim. That suggestion becomes a Claim only when saved. Retiring `claim-risk` remains the separate delete above. Cancelling Discovery leaves the Claim files unchanged.

The list is this comparison of `1.0.0` with `1.1.0`. Keep does not alter the Claim or the Requirement, so a later comparison of the same two trees still shows D0 against D1. This story adds no stored mark that a later visit can read as "accepted against `1.1.0`".

Today Packs v2 Claims carry `requirement_id` only (no Requirement digest field). This story’s **minimum** is the impact list and forced human action before pretending nothing changed. Pinning a Requirement digest on the Claim is OPEN and must not be implemented as if already in Packs v2.

## Requirements (Given / When / Then)

### R1 — Unbound when Requirement id missing

**Given** a Claim whose `requirement_id` is absent from the newly selected Pack tree  
**When** the post-update Claims impact view runs  
**Then** that Claim is listed as unbound  
**And** curbcheck still must not treat a missing Requirement as a silent pass for that Claim’s meaning (existing runner rules apply; this story does not invent a pass).

### R2 — Payload change is visible

**Given** a Claim whose `requirement_id` exists in both old and new trees but the Requirement version digest differs  
**When** the impact view runs  
**Then** the Claim is listed as needs review (or equivalent)  
**And** the view shows enough identity to tell old vs new apart (ids + digests or edition/locator summary).

### R3 — No silent rewrite

**Given** any Claim in the impact list  
**When** the operator has not confirmed a rebind/retire/keep action  
**Then** Studio does not rewrite that Claim’s `requirement_id`, evidence `args`, or `signed` block automatically.

## Out of scope

- Adding a normative `requirement_digest` field to Packs v2 without a separate contract decision.  
- Auto-merging legal text into Claims.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| Claim pins Requirement digest | Defer; file a Packs v2 contract change if pilot proves id-only insufficient | OPEN |
| Whether “keep” without re-sign is allowed when only hints changed | Prefer require human confirm; re-sign if Claim payload changes | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
