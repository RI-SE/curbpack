# Launch status and audit limitations

Assessment date: 2026-09-06. **Production qualification is incomplete.** The
released CLI can be installed and used for local structural diagnosis. Its
output must not be treated as a complete security audit, an approval, or proof of
regulatory conformity.

## Released, merged, and under review

<!-- curbpack-release:start -->
CLI release **v0.5.5** published **2026-09-05** ([release](https://github.com/RI-SE/curbpack/releases/tag/v0.5.5)); advertised on `main` **2026-09-05** ([advertise PR](https://github.com/RI-SE/curbpack/pull/51)).
<!-- curbpack-release:end -->

| Surface | Verified state | Evidence |
|---|---|---|
| Public install | **Released = v0.5.5**; `main` advertises after tag-smoke | [Release](https://github.com/RI-SE/curbpack/releases/tag/v0.5.5), [manifest](../scripts/install-manifest.json), [install smoke](../scripts/release-smoke-install-scan.sh) |
| Tag / merge tip | Annotated `v0.5.5` on merge SHA `78441d1102b63b7df0fd24b7af3f374cd99ea496` (PR [#50](https://github.com/RI-SE/curbpack/pull/50)) | [Tag](https://github.com/RI-SE/curbpack/releases/tag/v0.5.5), [release run](https://github.com/RI-SE/curbpack/actions/runs/33991663995) |
| Platforms smoked | **macOS local:** `CURBPACK_VERSION=v0.5.5` install → `curbpack version` = `0.5.5` → write-free `scan` (porcelain empty). **Linux / Windows:** release assets + `checksums.txt` HTTP 200; PR #50 CI `test (ubuntu-latest)`, `smoke`, and `windows-smoke` green on tip — **not** separate `CURBPACK_VERSION=v0.5.5` install-script smokes on those hosts | Local smoke transcript; [CI run](https://github.com/RI-SE/curbpack/actions/runs/33991451572); asset HTTP 200 checks |
| Seven historical false-green findings | FG-01 through FG-07 closed on tip included in v0.5.5; zero open in that seven-item catalog only. Additional Action and output-write defects remain below | [SDD register](software-design-document.md#81-open-false-green-paths), `./scripts/redteam-pilot.sh` 15 passed / 0 failed on tip |
| Action pin | Remains **`@v0.5.2`** (no pin-bump) | [release gate](../scripts/release-gate.json), examples / Action docs |
| Private vulnerability reporting | Enabled | [Private reporting](https://github.com/RI-SE/curbpack/security/advisories/new), [security policy](../SECURITY.md) |

Passing CI on source does not by itself update stranger installs until `main`
advertises the smoke-verified tag via the install manifest.

## Repairs included in v0.5.5

| Defect | Repair and reproducible evidence |
|---|---|
| A pass and an incomplete evaluation can have the same result digest; ordering equal-gate failures also changes the digest | Bind completeness fields and order all hashed failure fields: [digest tests](../internal/ir/digest_outcome_test.go), [implementation](../internal/ir/digest.go) |
| The documented `ask failure.json --propose` command rejects its arguments | Accept flags before or after the path, retaining `--` and invalid-argument rejection: [tests](../internal/cli/ask_flags_test.go) |
| Evaluation cache write failure can return success; cache directory symlinks can write outside the repository | Fail closed and replace complete cache files through temporary files: [regressions](../internal/validate/cache_failure_test.go), [cache writer](../internal/validate/cache_write.go) |
| A regular file beneath a symlinked ancestor can escape the path check | Resolve the whole existing path, including ancestors; refuse resolved `.git` aliases: [regressions](../internal/pathjail/ancestor_symlink_test.go), [containment](../internal/pathjail/pathjail.go) |
| Real OpenSSH verification fails; repository or ambient agent keys are used as trust policy | Use stdin and explicit principal with an external operator-selected policy; fail closed without that policy: [real-binary test](../internal/attest/verify_real_test.go), [trust setup](security-model.md#attestation-honesty) |
| Release dispatch can label the current checkout with another tag; reruns can replace published assets | Check out the requested tag, verify its commit, test source, refuse overwrite, and create a draft: [workflow](../.github/workflows/release.yml), [real Git tests](../scripts/release-ref-test.sh) |
| Hostile `CURBPACK_VERSION` can path-traverse download URLs while keeping binary + checksums self-consistent | Refuse non-`latest` / non-release-tag grammar before URL construction: [install-version-test](../scripts/install-version-test.sh), [install.sh](../scripts/install.sh), [install.ps1](../scripts/install.ps1) |
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
| **Post-launch: Action `inputs.version` shell interpolation** | Closed structurally: inputs / step outputs reach shell and JS via env; version/boolean validated as data ([action-resolve-bin.sh](../scripts/action-resolve-bin.sh), [action-resolve-test.sh](../scripts/action-resolve-test.sh)). Pin stays **`@v0.5.2`** until a human pin-bump tabletop | [action.yml](../action.yml), [required contexts](../.github/required-checks.json) |
| Human launch checks | Record fresh-machine use and logged-out social preview checks; confirm the responsible support owner | [human runbook](getting-started/a2-a3-human-runbook.md), [validation log](getting-started/stranger-validation-log.md) |

Use `scan` for structural diagnosis and inspect findings. `scan` exit 0 means the
diagnosis completed; it does not mean gates passed. A complete `check` is the local
gate result. A buyer must review scope, missing evidence, provenance and trust
separately. No agent has completed human confirmations, attestation, Action
pin-bump, or the external-user validation log during this launch.

## Sequential hardening checklist

The CUR-01 corrections do not close production qualification. Each work package
needs fresh verification and human review; invitations still require A2 and A3.

| Order | Work package | State |
|---|---|---|
| 1 | CUR-01: explicit release/advertisement evidence; declared resource checks including samples; complete static homepage CSS | Corrections on this branch; run `python3 scripts/test_public_assets.py` and `python3 scripts/check-public-assets.py --verify-release` |
| 2 | Action execution: reject consumer-controlled source builds; treat inputs as shell/JavaScript data | In progress on Action P1 — [resolver](../scripts/action-resolve-bin.sh); consumer path = checksum-pinned download only; dogfood source only via explicit RI-SE env |
| 3 | Contained, staged output writes; exclusive writers and interruption recovery; Windows path cases | Open — default `review-pack` symlink escape reproduced in [release writer](../internal/release/release.go); pull concurrency/path work forward |
| 4 | W2 canonical evaluation/receipt split, explicit `as_of`, complete identity, versioned cache; producer and reader determinism | Open — the three-site CUR-CLOCK substitution alone is insufficient; [SDD](software-design-document.md#12-sequential-work-packages) |
| 5 | Explicit redaction context; failed/evaluated/skipped counts; comparable trends; `conformity_claim: none`; schemas and compatibility | Open — preserve custom-home leak detection and historical machine contracts |
| 6 | Extend existing offline bundle review with schema/integrity validation and separate trust results | Open — share the existing review engine rather than introducing an independent verifier |

The public-assets command checks declared HTML/CSS resources and disallows module
loading syntax; it does not prove that arbitrary JavaScript cannot make network
requests. Its release statements use required records and GitHub event checks,
not local tag availability or nearest-date inference. Publication, advertisement,
and historical operational actions are separate events.

Homepage CSS is checked in and used only by the homepage. Rebuild it with
`./scripts/build-homepage-css.sh`; verify reproducibility with `--check`. The
pinned [Tailwind CLI](https://v3.tailwindcss.com/docs/installation) is a build-time
tool; the public site and Pages deployment do not download a CSS compiler.
The browser regression in `scripts/test_public_assets.py` runs in CI with
Playwright 1.62.1. For local execution, provide Node/Playwright and set
`CURBPACK_BROWSER_TESTS=1` (optionally `CURBPACK_BROWSER_CHANNEL=chrome` to use
installed Chrome). It checks desktop/mobile borders, links, transforms and
secondary-page overflow with external page resources blocked.

## Six readers (one record, one verify path)

> A new reader earns a new **question**, not a new **artifact**.

| Reader | Question of the record | Holds the repo? | Served at v0.5.5 / `17a18ed` |
|---|---|---|---|
| **QA** | Does this evidence correspond to the tree we tested? | yes | partly — `subject_commit` present but *claimed* |
| **Management** | Are we ready, and is it improving? | no | badly — via score-as-percentage surfaces |
| **Incident / PSIRT** | Which shipped artifact contained this component? | no | not at all |
| **Legal / compliance** | What exactly are we claiming, and can we defend it? | no | prose only; no machine `conformity_claim` field yet |
| **Reviewer** (peer, agent, CTAM) | Does the artifact conform to its own method? | yes | best served of the six |
| **Buyer / auditor** | Can I trust this without trusting you? | no | partly — `curbpack review <received-pack> --json` already provides offline structure/digest/reference triage; independent authenticity and complete input identity remain open |

Differences = queries over the same bytes. Per-reader renderings go to the refusal log.
