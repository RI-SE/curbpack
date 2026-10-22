# Claims binding correctness (pilot Step 1)

Status: COMPLETE — move to `poc2/doc/IMPL/` after commit.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan state | COMPLETE |
| Current step | done |
| Last verified | 2026-10-14 — unit + HTTP walkthrough |
| Local commit | `befe2f2` |
| Active blocker | none |
| Exact next action | none — Step 1 complete |

## Goal

A pilot user can create a Claim from Discovery without attaching it to the wrong Requirement, and can tell an unsigned draft from a signed Claim.

## Steps

1. [x] Plan + confirm defects.
2. [x] `sign_claim` / `read_claim_seal`, `exist_args_for_path`, `require_requirement_id`, `law_passages` in `claims/bind.py`. `rebind` keeps seal when payload digest unchanged.
3. [x] Discover Use path carries `requirement_id` + `path`. Claims UI validates Requirement against selected Pack (or curbpack packs when none selected), shows law_text, unsigned/signed/verifiable, sign form, seal-clear flash. No hardcoded `CRA-ANNEX-VII-RISK`.
4. [x] Tests: `tests/test_claims_binding_ui.py` plus `test_m3_claims`, `test_ui_smoke`, `test_pilot_pack_selection`, `test_cover_navigation`.
5. [x] HTTP walkthrough: Discover REQ-A → Use path → create → reopen unsigned → sign → edit clears seal; REQ-B separate. `WALKTHROUGH_OK`.

## Files changed

- `poc2/claims/bind.py`
- `poc2/app/pages.py`
- `poc2/app/server.py`
- `poc2/tests/test_claims_binding_ui.py`
- this plan

## Out of scope (unchanged)

Evidence highlighting, Check/Review productization, extraction pipeline, Packs v2 / ARCHITECTURE.md, candidate persistence on Claims.
