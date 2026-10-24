# Agentic development harness — NIST SSDF evidence map

**Historical source:** CTAM `policies/work-items.md`, `policies/review.md`, and PoC2 `impl/pilot/REQUIREMENTS_IMPLEMENTATION_PLAN.md`. This file maps existing controls; it does not replace these rules.

**Reference:** NIST SP 800-218 SSDF v1.1 (2022), https://csrc.nist.gov/pubs/sp/800/218/final. Mapping is a control plan, **not a claim of SSDF compliance**. The automated plan check validates structure only, not secure behavior.

| SSDF practice | Project rule / control | Observable evidence | Remaining gap / verification |
| --- | --- | --- | --- |
| PO.1 — security requirements | Story → approved system requirements before implementation | `docs/req/` ID and plan mapping | Review each item's security relevance and acceptance; not yet audited across all stories |
| PO.4 — criteria for security checks | Defined test-first acceptance and no unverified PASS | Plan checkpoint, red/green logs, `policies/testing.md` | CI/security gates and severity thresholds need project-specific decisions |
| PO.5 — secure development environments | Restrict secrets, generated workspaces and cloud use | `.gitignore`, staged diff review, `policies/security.md` | Verify local machine, Cursor, secrets handling and approved toolchain separately |
| PS.1 — protect code | Local commits, guarded remote changes and no history rewrite | Git commit history, staging diff, explicit approvals | GitHub branch protection/access rules are **not** established by this harness |
| PW.1/PW.2 — secure design and review | Review requirements, Packs v2 and subsystem architecture before code | Approved plan and documented conflicts / risks | Threat-model depth and independent reviewer not automatically supplied |
| PW.5 — secure coding | Minimum in-scope change, strict boundary and input validation review | Code diff and completed review log | Coding standards and static analyzer config require verification |
| PW.7 — code review/analysis | Skeptical diff review, findings recorded before commit | Actual review results logged in per-story plan | Human/automated independent review and SAST coverage not automatically present |
| PW.8 — code testing | RED → GREEN and impacted regression evidence | Test commands, observed results, reproducible fixtures | Security test breadth, CI execution and coverage require separate validation |
| RV.1 — identify and confirm vulnerabilities | Record actionable security findings and blockers | Plan work log + issue/decision record | No vulnerability intake/triage process yet demonstrated |

**Before claiming any practice implemented:** inspect actual configuration, run/observe its control and record dated evidence. Security Agents, SAST, dependency scanners and cloud integrations are optional until explicitly approved and correctly configured for RISE data classification.
