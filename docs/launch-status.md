# Launch status and audit limitations

Assessment date: 2026-09-05. **Production qualification is incomplete.** The
released CLI can be installed and used for local structural diagnosis. Its
output must not be treated as a complete security audit, an approval, or proof of
regulatory conformity.

## Released, merged, and under review

| Surface | Verified state | Evidence |
|---|---|---|
| Public install | v0.5.4; fresh macOS install, version check, and write-free scan passed | [Release](https://github.com/RI-SE/curbpack/releases/tag/v0.5.4), [manifest](../scripts/install-manifest.json), [install smoke](../scripts/release-smoke-install-scan.sh) |
| Main at audit start | `b6c471751c97f8a95165344274be858cc9cff33c`; newer audit-integrity fixes than v0.5.4 | [Commit](https://github.com/RI-SE/curbpack/commit/b6c471751c97f8a95165344274be858cc9cff33c), [CI run](https://github.com/RI-SE/curbpack/actions/runs/33985475860) |
| Seven historical false-green findings | Repair commits for FG-01 through FG-07 merged after the SDD baseline; absent from the published v0.5.4 binaries | [PRs 42–49](https://github.com/RI-SE/curbpack/pulls?q=is%3Apr+is%3Amerged), [SDD baseline register](software-design-document.md#81-open-false-green-paths) |
| This hardening change | Source changes and tests under review; no release tag, installer pin change, or production deployment | [Changelog](../CHANGELOG.md), [release gate](../scripts/release-gate.json) |
| Private vulnerability reporting | Enabled during this audit | [Private reporting entry point](https://github.com/RI-SE/curbpack/security/advisories/new), [security policy](../SECURITY.md) |

The SDD's measurements remain a historical snapshot of its explicitly pinned
baseline. They are not a live release dashboard. Passing CI on newer source does
not update the binaries installed by users.

## Reproduced defects and repairs in this change

| Defect | Repair and reproducible evidence |
|---|---|
| A pass and an incomplete evaluation can have the same result digest; ordering equal-gate failures also changes the digest | Bind completeness fields and order all hashed failure fields: [digest tests](../internal/ir/digest_outcome_test.go), [implementation](../internal/ir/digest.go) |
| The documented `ask failure.json --propose` command rejects its arguments | Accept flags before or after the path, retaining `--` and invalid-argument rejection: [tests](../internal/cli/ask_flags_test.go) |
| Evaluation cache write failure can return success; cache directory symlinks can write outside the repository | Fail closed and replace complete cache files through temporary files: [regressions](../internal/validate/cache_failure_test.go), [cache writer](../internal/validate/cache_write.go) |
| A regular file beneath a symlinked ancestor can escape the path check | Resolve the whole existing path, including ancestors; refuse resolved `.git` aliases: [regressions](../internal/pathjail/ancestor_symlink_test.go), [containment](../internal/pathjail/pathjail.go) |
| Real OpenSSH verification fails; repository or ambient agent keys are used as trust policy | Use stdin and explicit principal with an external operator-selected policy; fail closed without that policy: [real-binary test](../internal/attest/verify_real_test.go), [trust setup](security-model.md#attestation-honesty) |
| Release dispatch can label the current checkout with another tag; reruns can replace published assets | Check out the requested tag, verify its commit, test source, refuse overwrite, and create a draft: [workflow](../.github/workflows/release.yml), [real Git tests](../scripts/release-ref-test.sh) |
| CI can hide failed release installation behind a successful workspace build | Run the [fail-closed release install smoke](../scripts/release-smoke-install-scan.sh) in [CI](../.github/workflows/ci.yml) |
| Public social PNG contains an XML error page | Correct invalid SVG bytes and regenerate the 1200 × 630 [card](../site/assets/og-campaign.png) from [source](../site/assets/og-campaign.svg) |
| Public wording overstates determinism and identifies signatures as human approval | Narrow homepage and buyer-facing language to structural checks and signature evidence: [home](../site/index.html), [one-pager template](../internal/release/templates/onepager.go) |
| Security policy advertises unavailable reporting paths and an unverified response promise | Enable private reporting, link it directly, remove the unverified mailbox/SLA and deferred npm support claim: [policy](../SECURITY.md) |

Regression tests were executed against the original behavior before their repair.
The changed complete-pass digest was independently recomputed with SHA-256; the
one-pager golden changes only its digest/fingerprint and the reviewed wording.

## Compatibility and interpretation

- Regenerate review packs that contain `outcome` or `skipped_rules` and were
  produced before the digest repair. Their old digest did not bind those fields;
  a mismatch must not fall back to that digest. Historical records without either
  field remain readable, but do not prove evaluation completeness.
- Verification now requires absolute `CURBPACK_ALLOWED_SIGNERS` and an explicit
  `CURBPACK_SIGNER_ID`. The policy must be outside the repository under review.
  Establish its keys independently. Missing tools/policy or failed verification
  leaves the signature unverified.
- A signature verifies use of a key for the signed state hash. Human presence,
  approval, authorization, claim truth, and complete evidence recomputation are
  separate questions. See [OpenSSH](https://man.openbsd.org/ssh-keygen.1#ALLOWED_SIGNERS).
- Cache persistence errors now return failure. JSON check/validate output carries
  `outcome: error` when evaluation completed but its cache could not be persisted.
  An older cache may remain after failure; it must not be interpreted as a new run.
- A legacy result digest binds selected structural fields, not every claim,
  referenced byte, rule-pack byte, or evaluation input. It is not a complete
  independently verifiable evaluation identity.

## Remaining production gates

These are not closed by compiling binaries or by the passing regression tests.

| Gate | Remaining work | Source |
|---|---|---|
| Canonical evaluation and receipt | Separate wall-clock, agent and pathway metadata from canonical evaluation; bind complete rule/input bytes and explicit `as_of`; freeze the versioned format | [SDD W2 and W5](software-design-document.md#12-sequential-work-packages), [current payload](../internal/ir/gatefailure.go) |
| Transactional persistence and hostile concurrency | Cache files are individually replaced, but three aliases are not one transaction. Descriptor-based containment and concurrent directory replacement remain outside the path-check guarantee | [cache writer](../internal/validate/cache_write.go), [path jail](../internal/pathjail/pathjail.go) |
| Resource and command guarantees | Evaluator-wide byte/file/subprocess budgets, interruption recovery, command effects, and consistent typed operational errors across every command | [SDD requirements](software-design-document.md#2-constitutional-invariants), [command implementation](../internal/cli/cli.go) |
| Independent trust assessment | Typed authenticity/integrity/completeness results, full evidence recomputation, and outside review of trust/digest changes | [SDD W4](software-design-document.md#12-sequential-work-packages), [bind resolution](../internal/attest/bind.go) |
| Release qualification | Review this change; run required CI on its final commit, qualify all supported OS paths, then authorize a new release and installer advertisement | [release workflow](../.github/workflows/release.yml), [required contexts](../.github/required-checks.json) |
| Human launch checks | Record fresh-machine use and logged-out social preview checks; confirm the responsible support owner | [human runbook](getting-started/a2-a3-human-runbook.md), [validation log](getting-started/stranger-validation-log.md) |

Use `scan` for structural diagnosis and inspect findings. `scan` exit 0 means the
diagnosis completed; it does not mean gates passed. A complete `check` is the local
gate result. A buyer must review scope, missing evidence, provenance and trust
separately. No agent has completed human confirmations, attestation, release
approval, or the external-user validation log during this audit.
