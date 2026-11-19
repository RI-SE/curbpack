# EP-15 — Update Pack with minimal Claim rework

**Status:** Draft. Product feature after Pilot 2; no implementation authorization from this epic alone.

## Goal

When the publisher of an adopted Pack releases a newer version (for example RISE CRA 1.0 → 1.1), let a product team inspect and selectively adopt only the changes it wants, retain its local adaptations and existing evidence, and obtain the **smallest defensible set of Requirements and Claims requiring human attention**. Never equate a changed digest with an automatic obligation to rewrite or re-sign every Claim.

This is an **Update Pack** workflow inside Studio's Pack component, not a parallel lifecycle, independent service, update database or automatic legal compliance engine.

## User journey

```text
Existing product workspace: RISE/CRA 1.0 -> local A/CRA working copy -> Claims
                                                        |
User supplies newer RISE/CRA 1.1 ZIP or existing local directory
  -> identify/inspect publisher, source version, trust reading [UP-01, UP-06]
  -> three-way read-only comparison [UP-02]
       BASE  = RISE/CRA version adopted by local copy
       LOCAL = current A/CRA working copy (including local edits)
       NEW   = RISE/CRA 1.1
  -> classify exact changes and potential semantic impacts [UP-03]
  -> review conflicts; explicitly select updates per Requirement/field [UP-04]
  -> preview affected Claims, with distinct technical and human-action statuses [UP-05]
  -> apply to new local working copy, with preserved originals and audit context [UP-04]
  -> only impacted Claims: review/rebind/discover/later as needed [UP-05]
  -> run Checks, inspect Run Results / Review using existing machinery [UP-07]
```

## Principles and exact semantics

- **Authority:** `docs/reference/packs2.md` specifies Pack/Requirement/Claim and signatures; `docs/reference/workspace.md` owns workspace selection. Neither this epic nor a backend implementation may silently change persistent contracts. `docs/arch/ARCHITECTURE.md` and EP-02 define component ownership.
- **Snapshot provenance, not release automation:** The user explicitly supplies an upstream candidate; there is no background fetch, mandatory Publish, or remote registry. Preserve source bytes, local copy and historical Run Results.
- **Correct identity:** Compare by qualified `(namespace, pack_id, requirement_id)` where appropriate and resolve source identity via explicit `origin`. An unqualified id collision is not a match. Until existing workspace selection supports multiple same-`pack_id` namespaces, detect ambiguity and stop rather than silently choose.
- **Three-way, not two-way:** Only BASE→NEW shows publisher change. BASE→LOCAL shows local edits. NEW→LOCAL alone is not enough to know whose change is whose. Missing BASE means no safe automatic three-way update.
- **Read-only until confirmed:** Import, compare, preview and impact analysis may not rewrite source, local Claims, signatures or previous results. Apply creates a separate new local working copy; user explicitly confirms selected changes.
- **No semantic oracle:** Full-payload digest detects any change, including `discovery_hints`, `status`, `origin` or administrative fields. A narrower deterministic *normative-field delta* may select items for human review, but must not assert legal equivalence or that a Claim is certainly still valid. When in doubt, classify as potentially affected. An exact unchanged Requirement payload retains its existing binding; a different payload cannot be reported as an exact `match` without an explicit rebind.
- **Minimize rework, not traceability:** Keep independent categories: source delta, locally adopted delta, exact Claim-binding state (`match`, `stale`, `missing`), suggested review scope, Check outcomes and signature state. Never silently update `requirement_digest` or reuse a signature on changed bytes.
- **Provenance is a claim:** `origin` records an assertion. A nominated source Pack plus a verified signature supports authentic source identification and an auditable comparison, not proof that the derivative author used that source or was authorized. Missing/untrusted material is shown explicitly; no automatic trust laundering.
- **Reuse:** Existing VL-01 Take Ownership, VL-02 ZIP Import/Export, VL-03 field-level Compare/Apply, VL-04 binding and Curbcheck status, VL-05 historical resolver and VL-06 affected-Claim actions remain authoritative and are reused. No duplicate comparison or Claim editor.

## Stories

| ID | User goal | Depends on |
|---|---|---|
| [UP-01](stories/UP-01-select-and-identify-versions.md) | Select BASE, LOCAL and NEW safely and unambiguously | EP-11 VL-00–VL-02 |
| [UP-02](stories/UP-02-three-way-delta.md) | Explain publisher changes, local changes and conflicts | UP-01, VL-03 |
| [UP-03](stories/UP-03-minimal-change-impact.md) | Compute precise structural change sets and conservative review scope | UP-02, VL-04 |
| [UP-04](stories/UP-04-preview-and-selective-apply.md) | Apply chosen changes to a new working copy, preserving local work | UP-02, UP-03, VL-01, VL-03 |
| [UP-05](stories/UP-05-affected-claims-worklist.md) | Show only potentially affected Claims and existing actions | UP-03, UP-04, VL-05–VL-06 |
| [UP-06](stories/UP-06-check-declared-origin.md) | Verify presented predecessor and display provenance limits | UP-01, VR-00 |
| [UP-07](stories/UP-07-update-view-and-e2e.md) | Complete one Update view and prove low-rework behavior in end-to-end use | UP-01–UP-06 |

## Explicit end-to-end scenario and expected work savings

**Example only (counts must be derived at runtime):** RISE/CRA 1.0 contains 30 Requirements. A has a derivative with 24 unchanged and 6 locally modified Requirements; A maintains 40 Claims. RISE/CRA 1.1 adds 2 Requirements, removes 1, edits 4, and changes only discovery hints on 3.

The user must see which upstream edits collide with A's local changes. Only accepted changes are written. Claims bound to byte-identical Requirements stay untouched. Claims bound to Requirements whose resulting digest changed must be shown as `stale` until explicitly rebound; the UI may mark administrative/hints-only changes as *review potentially unnecessary*, but cannot turn `stale` into `match` or assert that claims are valid. New Requirements are shown as uncovered; removed Requirements with Claims require a disposition, never silent Claim deletion. Claims for unrelated Requirements are not shown as requiring rework.

The dashboard must report actual counts: `unchanged`, `publisher changed`, `local-only`, `conflict`, `added`, `removed`; plus affected Requirements, affected Claims, `match/stale/missing`, and **review decisions needed**. It must not present fictional confidence or a mathematically guaranteed minimum of human decisions.

## Component placement

- `studio/pack/impl/`: snapshot selection, qualified identity matching, three-way diff, update preview, applying selected choices. Reuse `studio/pack/impl/compare.py`, `workspace.py` and existing safety/confinement checks; no new persistent update queue.
- `studio/claim/impl/`: Claim lookup/binding impact and action targets. Pack invokes this API; never implements Claim rules or mutates Claims itself.
- `studio/pack/pages/`: one thin TypeScript Update page, invoking backend via the component-owned REST route when supported. During unfinished EP-02, any temporary HTTP adapter remains thin and must not duplicate domain logic. Do not silently start EP-02 stages 4–7 as part of this epic.
- Curbcheck and Review are reused unchanged except a narrowly evidenced integration issue.

## Product and contract decisions requiring explicit approval before implementation

1. **Qualified workspace selection:** Existing `curbpack.json` selects by unqualified pack ID, and historical on-disk paths may collide when different namespaces share a `pack_id`. UP-01 must detect this immediately. If supporting both is required, first approve a minimal `workspace.md` contract change and compatibility migration. Do not invent a new storage layout in a story implementation.
2. **Exact predecessor pinning:** Current `origin` names namespace/pack/version (and requirement) but does not universally carry a predecessor content digest. UP-06 can verify a user-supplied candidate and report its fingerprint, but robust provenance pinning across transfers requires a separately approved `packs2.md` decision; do not silently add `origin.digest`.
3. **What counts as normative:** UP-03 lists conservative candidate field groups for review; classifying legal changes as semantically non-impacting remains a human decision. No claim of semantic equivalence from a hash.

## Acceptance at epic level

- A real three-way update of source 1.0, locally adapted copy and source 1.1 is read-only until confirm; conflicts are surfaced rather than overwritten; no source or prior artifact is modified.
- The user can preview and selectively adopt additions, edits and removals, preserve local-only changes, and cancel safely. Apply is atomic and rejects changed inputs with explicit errors.
- Exactly unchanged Claims and Requirements are preserved byte-for-byte; only structurally affected Claims are shown for action. No Claims, seals, Run Results or signed Review Reports are rewritten by Update.
- Every apparent `match`, provenance-verification outcome, signature and Check outcome is justified by the correct exact identity/version/digest, not by display name or unqualified ID.
- The UI makes an intelligible case that only a subset of the Claims requires human attention, and a test measures the selected subset against a known fixture (including hints-only change and local conflicts).
- Existing Import/Compare/Take Ownership/Claims/Check/Review and entire pilot regression suite remain passing. User-level installed-package smoke test is part of pilot acceptance, not a reason to widen this epic.

## Excluded

Automatic legal interpretation, automatic Claim approval or silent rebinding, auto-downloading updates, central namespace authority, PKI/trust marketplace, blockchain, history database, mandatory Publish, update notifications, full EP-02 migration, new Check engine, generalized diff/merge framework, and rewriting original upstream artifacts.

## Delivery and pause point

This epic is **proposed work after the next pilot release**. Do not implement it while finalizing EP-02 stage 3 or Pilot 2. Any normative contract or trust policy decision must return to the human/PO before coding. Each story is a bounded independently verifiable unit with tests, not license to implement the entire epic at once.
