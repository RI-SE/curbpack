# Compile — Studio component architecture

**Status:** Target component contract, 2026-11-06. `studio/compile/` is the target owner; current `compile/` and `review/compile.py` are migration inputs.

## Ownership

Compile builds an **unsigned review report from recorded Run Results and relevant snapshots** and renders supported outputs such as JSON and PDF. It does **not** execute Checks, decide whether results pass, obtain human review decisions, sign Review reports or mutate prior Run Results.

The target `studio/compile/router.py` owns any Compile REST endpoints. Its thin optional CLI and router call the same headless `studio/compile/impl/` operations. A GUI page is optional and must be thin TypeScript using REST. `studio/app.py` registers routers only. `studio/review/` owns review decisions and signing; `curbcheck/` owns Checks and Run Result creation. `review_decision` is defined in `docs/reference/studio-internal.md`.

## Operations and preservation

| Operation | Contract |
|---|---|
| Load Run Result | Read previously recorded output from the configured Results location; do not rerun Checks |
| Resolve report inputs | Obtain the specified Requirement/Claim snapshots for this Run Result; verify identity/digest against recorded facts; do not silently use different current versions |
| Compile JSON report | Assemble one validated report using the normative Packs v2 / outputs contract; no `decision` or new `signed` block |
| Save/load report | Write to configured Reports location with explicit overwrite/retention semantics; preserve earlier report until the user authorizes a replacement |
| Render PDF | Deterministically render the already compiled report; do not reopen evidence or reinterpret results |

VL-05 adds a historical **read-only resolver in Review**, reusable where needed to obtain exact historical inputs. It does not transfer signing or decision responsibility to Compile. If a required exact object cannot be resolved, report the condition explicitly, not a convenient current substitute. Do not introduce another persistent report schema without approval.

## PDF component (existing behavior to retain)

- Offline renderer accepts an existing validated review-report JSON and writes a readable paginated PDF without altering the source report.
- Include the checked product revision, Pack/Requirement/Claim context, configured Checks and outcomes, recorded signer/decision facts as available, and explicit limits of verification. A recorded signature is not claimed verified unless verification actually ran.
- Support Unicode, long paths and multipage content without clipping; escape user-supplied markup.
- Failed rendering does not destroy an existing PDF and does not modify source data. Do not silently overwrite an output path.
- Keep the existing `compile-pdf.py` CLI behavior working throughout migration until an accepted explicit CLI replacement is provided.

## Verification

Tests cover headless JSON compilation, validation, original Run Result preservation, signed report preservation, exact digest/object relationships, PDF readability and Unicode/multipage layout, failures without clobbering, and REST/CLI use of the same operations. Include existing `tests/test_compile_pdf.py` and Review compilation regressions in the EP-02 parity map.
