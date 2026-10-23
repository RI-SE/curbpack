# EP-03 — SSDF security baseline and evidence

**Status:** Draft; not authorized for broad implementation. **Priority:** Fix any confirmed security release blocker first; finish EP-01 pilot before the remaining work.  
**Reference:** NIST SP 800-218, SSDF v1.1: https://csrc.nist.gov/pubs/sp/800/218/final

## Goal

**As a maintainer**, I want demonstrable security controls and negative tests for Studio's real trust boundaries, so that we can deliver software without false PASS results and explain which SSDF practices we actually implement.

This is an **evidence and risk-reduction epic**, not an assertion or certificate of "SSDF compliance". Reuse `docs/ssdf/harness.md`, `policies/security.md`, `policies/testing.md` and the existing CI script interface; do not duplicate them.

## Baseline and findings

- Existing code/tests already check parts of evidence paths, signature verification, Check/Review integrity and Git identity. Keep these tests.
- The proposed `scripts/security/` suite was executed against **`curbpack-studio-review(2).zip` (23 October 2026), not current HEAD**: 14 cases PASS; 2 cases FAIL. Both failures show `pack_id` escaping expected workspace/published directory boundaries in `requirements/workspace.py`. HTTP exploitability and the current HEAD are **not yet verified**.
- `docs/ssdf/harness.md` identifies unverified GitHub protections, development environments, independent analysis/SAST, security-test breadth, CI gates and vulnerability intake. These are **verification gaps**, not assertions that current HEAD lacks them.
- The old Curbpack "redteam" script is **not** the baseline: import only demonstrably useful attack scenarios, never test-name hype.

## Stories (in priority order)

| Story | Outcome | Priority / scope |
| --- | --- | --- |
| [SEC-01](stories/SEC-01-security-evidence-baseline.md) | Verify current HEAD, relevant threat boundaries and SSDF evidence/gaps | P0, short inventory |
| [SEC-02](stories/SEC-02-confine-pack-selection.md) | Reject `pack_id` path escape without breaking valid Pack selection | P0 **if reproduced**; release blocker if reachable by untrusted input |
| SEC-03 | Not this epic. The functional suite is [SYS-02](../../01-pack-editor/stories/SYS-02-one-test-suite.md). Separate scripts remain only for scanner checks that do not exist yet (SEC-04). | Later |
| SEC-04 | Add justified SAST, secrets and dependency-vulnerability checks as **independent scripts**, each runnable locally and in CI, with explicit fail/waiver rules | P1, not empty Make targets |
| SEC-05 | Verify GitHub branch/CI permissions, secret handling, dependency inputs and SHA-256 provenance of published artifacts | P1, reuse delivery chain; no Docker/signing project |
| SEC-06 | Provide a practical vulnerability intake, severity/ownership, remediation, exception and retest loop; record a real finding end-to-end | P1, existing issues/workflow |

Only SEC-01 and SEC-02 are expanded into story files now. Define and approve the other stories when they are scheduled, not as speculative implementation plans.

## Acceptance

1. For **each in-scope SSDF practice**, `docs/ssdf/harness.md` records practice/task ID, actual control, dated observation or test output, owner and status: **Verified / Gap / Not applicable (reason) / Not assessed**. No status is inferred from a policy or a passing tool alone.
2. The `pack_id` traversal finding is either reproduced and fixed with failing-then-passing tests on current HEAD, or disproved with reproducible evidence. If externally reachable, resolve it before distributing the pilot to external testers.
3. Applicable tests challenge false PASS, forged signatures, repository boundary violations and tampered Review data. Normal valid paths continue to work. Every test has a reproducible fixture, expected result and nonzero exit on failure.
4. Every enabled security check is its own runnable script, callable locally and through the same CI entry point. Mandatory failures are visible and fail the gate. Missing/disabled checks are never counted as PASS.
5. At least one security finding is recorded through triage, disposition, fix or risk acceptance, and retest; remaining gaps have owners and priorities.
6. A reviewer can reproduce the supporting evidence for the claims made. **No blanket SSDF-compliance statement** is issued solely by completing this epic.

## Outside this epic

No new security framework, R-state harness, generic fuzz platform, Docker deployment, CI rewrite, artificial test taxonomy, duplicate policies, or changes to Packs v2 without a separately approved contract decision. Release packaging, signing and SBOM work remain governed by `docs/agile/future_cicd.md` when explicitly scheduled. Preserve today's pilot delivery scope except for confirmed security release blockers.
