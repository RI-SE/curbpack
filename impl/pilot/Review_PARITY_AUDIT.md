# Review functional parity and source audit

Status: evidence-based design audit, 21 October 2026. This is a comparison, **not** a claim that the target is implemented.

## Evidence and authority

- `poc(3).zip`: `poc/components/review/README.md`, `ui.py`, `check_dialog.py`, `findings_ui.py`, `scan.json`. Direct evidence of PoC1 behavior; `scan.json` was simulated, not the product checker.
- `poc2(3).zip` (earlier) and `poc2 2.zip` (current): `poc2/review/ARCHITECTURE.md`, `review/compile.py`, `checks/ARCHITECTURE.md`. Evidence of target assertions and current code; source documents acknowledge implementation gaps.
- `aslaks-first-vision.zip`: `docs/shared-frame.md`, `docs/intent-vs-scope.md`, `docs/method/review-method-1.3.0.md`. Evidence of earlier intent and legacy method, **not a new Packs v2 contract**.
- `PoC2_ARCHITECTURE_revised.md`: cross-subsystem target, including ownership split requirements / claims / checks / compile / review.
- Normative Packs v2 is identified by the above documents as `docs/reference/packs2.md`; its **complete authoritative source was not independently available in the uploaded extracts**. Schema-sensitive proposals remain conservative and subject to direct contract validation.

## Parity matrix

| Capability / invariant | PoC1 actual | Earlier vision | PoC2 target / code | Judgment / action |
|---|---|---|---|---|
| Review starts after check | README uses simulated `scan.json`; UI queue | Deterministic observations feed human decision | Run Result feeds Compile, then Review | **Preserved concept**; real run preferred over simulation |
| Previously accepted Claims that turn red | Explicit Review purpose; work queue | Nothing dies silently | Shows failed run rows, but little historical comparison | **Partial**; specify baseline and changed-since-last-reviewed behavior |
| Keep | Explicit action stored in `state.json`, row remains | Human acceptance not equivalent to machine fact | Existing architecture drops mark; doing nothing leaves Claim | **Gap**; retain-with-rationale action distinct from pass |
| Re-hunt | Explicit start/done; can repoint demo `_new` path | Deterministic candidate search, human gate | Link to Claims Discovery | **Partial**; preserve action-oriented navigation and unresolved state, not demo path mutation |
| Check editing from review | UI has inline edit/demo overlays | Deterministic checks | Claims Editor owns Check configuration | **Intent preserved by relocation**, must test round-trip |
| Row remains visible | README explicitly says rows stay until Sign off | Nothing dies silently | Current Review renders Check rows; no unresolved queue contract | **Partial**; test navigational return and no silent disappearance |
| Per-item decision persistence | `state.json` stores keep/rehunt | Human-approved edges and review states, legacy schema | Report has one `decision` string, no structured dispositions | **Open contract gap**, do not invent hidden second schema |
| Signed final review | Demo signoff flag and `/remedy` | Human decision is not compliance | `decision` + signed review report | **Strengthened**, signing report is not Claim or Requirement seal |
| Previous report after new run | No demonstrated immutable history contract | Re-review freshness and provenance matter | Architecture mandates old report remains; code noted as deleting on Check | **Implementation gap**; regression test |
| Artifact state vs review currency | Not shown as full two-axis model in PoC1 | Explicit in shared-frame | Current Review only uses `same_run`, worktree, seals | **Design gap**; do not infer review current from Git-clean or Check-pass |
| Legal/compliance conclusion | Not evidenced as formal assessment | Explicitly forbids conformity assertion | Report has no `compliant` or `meets_cra` field | **Preserve** |
| Legacy Curbpack review method | Not PoC1 QA queue | Structural offline document-reference checking | Final human review | **Different operations**; do not unify them by naming |
| Checks authority | Simulated status in PoC1 | Deterministic checking | `checks/` owns result, Review read-only | **Correct** |
| Signing ownership | PoC1 demo flag | Human-gated accepted linkage | Requirement, Claim, report separate seals | **Correct**, never imply one seal signs the others |

## Findings by severity

**F1 / high:** Architecture currently labels persistent Keep/Re-hunt marks as Drop without identifying equivalent auditable per-item decisions. Relocating the screen interaction is acceptable; deleting its semantic purpose is not.

**F2 / high:** Prior-review freshness is not the same as live Check status, file changes, Claim digest, or dirty/clean repository. The vision's two independent axes need an explicit data basis or a clearly labeled unknown state.

**F3 / high:** Source architecture says the existing Check action deletes the report after a new run, contradicting intended preservation of signed historical review. This is a testable behavior defect pending verification in the current repository.

**F4 / medium:** Current `decision` string can express a human assessment but does not provide machine-addressable per-Claim dispositions for a queue across runs. This is a *schema/retention decision*, not an excuse to create `state.json` again.

**F5 / medium:** Legacy Curbpack `review` tests document references; it is not PoC2 final human Review. The shared noun must not cause import of legacy report/edge fields.

**F6 / medium:** The source architecture still co-locates Compile functions and Review UI. Planned split must preserve data validation, callability, and user workflow, not merely move files.

## Non-goals and hard boundaries

No new Packs v2 fields without explicit approval; no `BuyerQuestion`, `edges`, or `Finding.ID` migration by implication. No automatic compliance assertion. No auto-pass on Keep/Re-hunt. No re-running Checks inside Review. No automatic Claim changes during Re-hunt. No moving files merely for architectural neatness. No assumption that historical Git commit identifies dirty bytes.

## Decision required from product owner

Is durable, item-level Keep/Re-hunt and automatic cross-run re-review **essential pilot functionality**? If yes, identify an authorised persistence contract before implementation and specify the historical record retention guarantee. If consciously postponed, record it as an explicit parity exception, not as “review complete.”

## Reviewer verdict

**Conditional architecture approval only.** The report/signing core is sound as a separation of responsibility, but the Review UX and historical disposition/currency semantics cannot be signed off as complete. The revised architecture specifies desired behaviors and exposes rather than hides the contract gap.


## Product decision and update — 21 October 2026

The product owner's later explicit decision supersedes the earlier proposal for a separate Reconcile/Finder and the assumption that a new persistent Keep/Re-hunt history is required for the pilot. **It does not change the recorded historical PoC1 behavior or Aslak's earlier intent**; it chooses a simpler implementation of the useful user action.

- Review shows the failing Claim and its Checks. The user opens the **existing one-Requirement Discovery** in a popup. Discovery core still knows no Claims and returns its normal candidates.
- A thin Claims/UI-only hook uses a relevant Check run and existing Claims to **grey, not hide**, already-covered candidates whose matching Claim's configured Checks all passed. Unknown/stale/failed/skipped/ambiguous coverage stays normal. This does not change Discovery candidates or persisted jobs.
- A person explicitly adds one or several new Claims and associated Checks, then may explicitly delete the old Claim. No automatic rebind, deletion, Find/Relocate component or new domain object. The person reruns Checks and separately signs Claims and the human review report.
- The pilot does **not** require durable per-item Keep/Re-hunt marks or automatic cross-run review-currency reconciliation. Those remain unimplemented and are not to be declared achieved. The current report retains free-text decisions; it is not a structured per-Claim decision log.
- **Independent defect remains:** actual `/check` code deletes saved Review reports; this violates the normative non-destructive Checks contract and requires a separate code fix/test. Compile's single report filename still lacks reliable multi-report retention without an external mechanism.

The authoritative operational contracts are `docs/arch/ARCHITECTURE.md`, `poc2/claims/ARCHITECTURE.md` and `poc2/review/ARCHITECTURE.md`. This audit records why; it is not a fourth specification.
