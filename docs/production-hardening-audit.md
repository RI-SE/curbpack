# Production hardening audit — 7 September 2026

**Decision: hold the broad production-readiness claim.** Cursor's committed work
is preserved, and Codex is repairing it following the operator's explicit handoff.
No merge, release, attestation, outreach or Action pin promotion is authorized by
passing tests.

## Baseline and ownership

The inspected baseline is main `afa0df0d498bd481d482efdf5fdcf8b8debee82b`,
including merged [#53](https://github.com/RI-SE/curbpack/pull/53),
[#54](https://github.com/RI-SE/curbpack/pull/54),
[#55](https://github.com/RI-SE/curbpack/pull/55) and
[#56](https://github.com/RI-SE/curbpack/pull/56).
[#57](https://github.com/RI-SE/curbpack/pull/57) was open at
`97b6ca2b9b4239f7d9c0eda786c493eca3a43317` when inspected. That commit is the
preserved parent of `codex/production-hardening-repairs`. The operator registry
records the ownership transfer in ops commit `c7d3131`; online preflight passed.

## Reproduced defects and repairs

These are behavioral findings, independent of the nine previously green PR
checks. Tests ran against disposable archived trees before product repairs.

| Finding | Repair on this branch | Regression source |
|---|---|---|
| An old lock owned by a live process could be stolen | Lock age never establishes owner death; acquisition never recovers automatically | [lock tests](../internal/outwrite/audit_contract_test.go) |
| Independent goroutines shared a lock solely because their PID matched | Each caller needs its own exclusive acquisition or an explicitly passed lease | [lock implementation](../internal/outwrite/outwrite.go) |
| Releasing an old handle deleted a successor's lock | Idempotent release checks file identity and preserves replacements | [lock tests](../internal/outwrite/audit_contract_test.go) |
| Refused `.git` destinations still created directories | Containment precedes directory creation | [lock tests](../internal/outwrite/audit_contract_test.go) |
| An explicit output root with several missing ancestors followed an alias into `.git` | Resolve every existing ancestor and check the resolved absolute root and target | [path jail](../internal/pathjail/pathjail.go), [lock tests](../internal/outwrite/audit_contract_test.go) |
| Release preparation overwrote an outside file through `vex-pending.json` | Build evidence in memory and publish through the original contained repository destination; standalone SBOM/VEX writers use the same output policy | [release test](../internal/release/write_boundary_test.go) |
| Two findings from one gate became `failed=2 evaluated=1` | Count distinct failed gate identities while retaining all finding rows | [gate-count test](../internal/validate/gate_count_test.go) |
| A custom HOME reached the published explain packet, followed by a CLI error | Capture explicit redaction context, sanitize typed findings/citations/hints before JSON encoding, and verify before publication | [explain test](../internal/exportx/explain_boundary_test.go) |

Release and cache writers now coordinate through a repository lease. Release
mappers do not acquire nested locks by assuming process identity. Explicit
outside pack directories also receive their own lock. `O_EXCL` provides
cooperative writer exclusion; it is **not** protection against hostile concurrent
filesystem mutation. Files are individually staged and renamed; complete pack
and alias-set transactions remain unfinished.

After an interrupted command, use `curbpack recover-lock <permitted-output-root>`.
Recovery refuses live or unverifiable owners, malformed locks and symlink locks.
An interrupted recovery can leave a `.recovery` guard that requires operator
inspection. Recovery does not validate interrupted outputs: rerun the command
and verify the resulting artifacts.

## Remaining acceptance work, in order

1. Complete output-set staging and interruption semantics. Add an authoritative
   completion record so readers cannot treat a partial pack as complete. Cover
   unwritable destinations, concurrent producer processes and interruption.
2. Complete W2 using the [SDD contract](software-design-document.md#32-target-architecture):
   explicit `as_of`, exact pack/method/input identity, immutable evaluations by
   full digest, a verified pointer, and operational state exclusively in receipts.
   In the inspected baseline, changing evaluated file bytes or rule patterns
   while preserving the same findings did **not** change evaluation bytes. This
   is missing identity, not proof of determinism. Freshness still uses ambient
   time. Historical readers and result digests need adapters and regression tests.
3. Complete reader/redaction coverage across every crossing surface. The #57
   trend predicate compares pack ID and schema only; changed pack bytes and
   evaluation scope are not yet bound. Do not claim those trends are comparable.
   Missing historical evaluated totals must be shown as unknown, not invented.
4. Extend the existing offline [review engine](../internal/review/review.go) with
   versioned schema and artifact-integrity checks. Separate integrity,
   authenticity, completeness and applicability. Subject commit remains a claim
   unless independently established; embedded signing material is not a trust
   anchor.
5. Run final uncached tests, build, vet, race, gauntlet, browser checks and the
   platform installation matrix on the final revision. Cross-compilation is not
   a Windows installation test. Preserve the distinctions in the
   [release evidence record](../scripts/release-gate.json).

## Earlier launch attachment: reconciliation

The attachment describes a proposed user journey, with some historical defects
and versions. It is not evidence that all nine items still need implementation.

| Attachment item | Current audit disposition |
|---|---|
| Redirected `init` silently does nothing | Not reproduced: both inspected binaries wrote configuration and printed 1,442 characters with all streams redirected. Keep an executable CLI regression before changing init. |
| Honest post-init next step and tallies | Scaffold remains a draft; failed-gate counts repaired above. Recheck every public reader and incomplete evaluation. |
| Release-asset installer | Retain the current verified-asset resolver and test actual downloads/install behavior per advertised OS. |
| CLI and Action version consistency | Preserve distinct CLI release and human-approved Action pin; no automatic pin bump. |
| Legacy cyberready names | Preserve historical compatibility contracts; audit public wording rather than blanket-delete legacy readers. |
| Scan front door, one-pager and countdown | Revalidate from final built CLI and rendered website; do not infer scan's error contract from an old attachment. |
| Living demo, fork, badge and Pages | Existing local demo is available. Any additional hosted demo, public fork or deployment remains a human publication decision. |
| Automation / optional / human map | Document actual effects and manual controls; do not infer telemetry or retention guarantees from aspiration. |
| RI-SE routing | [Agent contract](../AGENTS.md) identifies RI-SE/curbpack as the public source of truth. No full-tree private-fork synchronization. |

## Repair checkpoint verification

Local uncached `go test ./... -count=1` passed after these repairs. Affected
packages also passed `go test -race`, and `go vet ./...` passed. The fresh built
CLI's repository `check --json` reported `outcome: pass`, with five evaluated
gates. The [focused behavioral script](../scripts/production-hardening-test.sh)
and actual Action resolver tests passed. Public asset mutations passed 17 test
groups with one opt-in live API group skipped. The Windows CLI cross-compiled;
Windows runtime output-boundary tests have been added to the existing CI job.
These results cover the repair checkpoint, not the unfinished acceptance work.
