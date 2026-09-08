# Production hardening audit — 8 September 2026

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

`review --since` now verifies the prior report's schema and recomputes its record
digest before emitting a trend or linking a new report. The shared engine also
applies this check to holding-report exports. Altered contents and missing or
fabricated digests previously returned success in both CLI review modes; the
[behavioral regressions](../internal/cli/review_since_test.go) now require exit 2
without report output. [Historical report tests](../internal/review/historical_audit_test.go)
preserve the original digest and accept it as a baseline. This is an integrity
check, not proof of who supplied a report or whether its claims are true.

Release and cache writers now coordinate through a repository lease. Release
mappers do not acquire nested locks by assuming process identity. Explicit
outside pack directories also receive their own lock. `O_EXCL` provides
cooperative writer exclusion; it is **not** protection against hostile concurrent
filesystem mutation. Release files are staged as a set, verified, and published with a completion
manifest last. Readers recheck every declared artifact. Interrupted renames may
leave a mixed directory that fails verification; this is not a filesystem
transaction or a guarantee against power loss. See the [batch writer](../internal/outwrite/batch.go).

After an interrupted command, use `curbpack recover-lock <permitted-output-root>`.
Recovery refuses live or unverifiable owners, malformed locks and symlink locks.
An interrupted recovery can leave a `.recovery` guard that requires operator
inspection. Recovery does not validate interrupted outputs: rerun the command
and verify the resulting artifacts.

## Remaining acceptance work, in order

1. Finish the interruption and native platform matrix on the final revision:
   concurrent producer processes, interrupted staging/publication, unwritable
   destinations and Windows runtime behavior. A blocked late destination now
   preserves earlier artifacts in the [publication regressions](../internal/release/publication_test.go).
2. Complete crossing-surface redaction review. Explain, ContextPack and review
   capture explicit custom-home context. Canonical or signed evidence must not
   be silently rewritten by a derived-output sanitizer. Test all remaining
   release/export formats before declaring this acceptance gate complete.
3. Review applicability policy separately from hash consistency. `as_of` drives
   freshness and is bound in canonical identity; an offline recipient still
   needs to select its intended subject, pack policy and time requirements.
   Auxiliary SBOM/VEX bytes are bound by the manifest, not by the gate verdict.
4. Run final uncached tests, build, vet, race, gauntlet, browser checks and the
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

## W2 continuation after the repair checkpoint

The continuation adds `curbpack-evaluation:2` and `curbpack-run-receipt:2`, keeping
historical v1 adapters. Evaluated file mutations and rule mutations now change
canonical identity even when findings are unchanged. Packs are captured once
per composition. `as_of` is explicit in the evaluation and accepted by producer
commands; Git freshness uses that instant. Operational state remains in receipts.

The [time/cache tests](../internal/validate/time_cache_contract_test.go) separately
exercise fresh emission and later reads, altered immutable objects, failed
pointer publication, explicit freshness instants, and relocation with custom
HOME, temporary directories and locale changes. The [input mutation test](../internal/validate/input_identity_test.go)
failed on the repair checkpoint before this continuation. [Versioned schemas and
compatibility rules](../schema/COMPATIBILITY.md) describe the new contract.

Exports verify immutable cache objects and compare current input identity before
reuse. Historical mutable aliases cannot supply a trend or override a fresh
evaluation. New result digests bind the evaluation digest; historical records
without that field retain their algorithm. Pack validity/applicability and
auxiliary artifact meaning must not be inferred from gate outcome alone.

## Completed-set publication and offline audit extension

The [release writer](../internal/release/release.go) builds artifacts in memory,
preflights all destinations, stages all bytes and publishes
`pack-manifest.json` last. `evaluation.json` and `run-receipt.json` travel with
new packs. The one-pager hashes the current staged SBOM/VEX bytes, and its
mechanical tally excludes skipped gates. `share` includes its companion files
in that same set and propagates preparation/bundle failures. Its legacy copy
helper also uses repository containment; see the [share boundary test](../internal/cli/share_boundary_test.go).

The existing [offline review engine](../internal/review/pack_audit.go) now validates
manifest schema, exact sizes/full SHA-256 hashes, canonical evaluation/receipt
contracts, and the historical payload adapter binding. No second verifier engine
or network/Git dependency was added. Its optional `curbpack-pack-audit:1` report
extension separates integrity, authenticity, completeness and applicability.
A verified manifest establishes internal consistency only. Authenticity remains
unverified without an independently selected signer policy; an offline subject
commit remains claimed. Extra unlisted files make completeness unverified.
Legacy packs remain reviewable with unknown manifest coverage.

[Publication and offline tests](../internal/release/publication_test.go) cover
altered/missing artifacts, removed manifests, unbound evaluation/receipt fields,
unlisted files and symlinked artifact leaves. Fresh pack generation and subsequent
review run separately; review succeeds outside Git under a different HOME/TMPDIR,
locale and invalid epoch. [Historical report fixtures](../internal/review/historical_audit_test.go)
retain their original digest, while current comparison reports deliberately bind
the new optional audit extension. Historical golden files were retained.

## Distribution and browser checks — 8 September 2026

The published [v0.5.5 assets](https://github.com/RI-SE/curbpack/releases/tag/v0.5.5)
were downloaded and all five binary SHA-256 values matched the release checksum
file. The [shell installer](../scripts/install.sh), pinned explicitly to v0.5.5,
installed into a disposable directory on macOS amd64. Its installed `version`
and read-only `scan` both exited zero. These checks concern the published binary,
which does not include this repair branch. No Linux or Windows installation is
claimed from downloads or cross-compilation; the local Docker daemon was not
available for a Linux container smoke.

The [public asset suite](../scripts/test_public_assets.py) passed all 17 tests,
including its real Chrome homepage checks at the defined viewport sizes and its
no-external-resource assertions. New schemas/goldens and an actual offline audit
report also passed Draft 2020-12 JSON Schema validation using a temporary test
dependency outside the repository.

## Tester handoff for this run

Use `codex/production-hardening-repairs` until a human merges the successor PR.
The default installer and public Action pin still select published versions;
they do not install this branch. The CLI's preserved version string is not a
substitute for recording the tested Git commit.

```bash
git clone --single-branch --branch codex/production-hardening-repairs https://github.com/RI-SE/curbpack.git curbpack-test
cd curbpack-test
git rev-parse HEAD
go build -o ./bin/curbpack ./cmd/curbpack
./bin/curbpack scan
./bin/curbpack check --json --as-of 2026-09-08
```

For a received completed pack, run `curbpack review <received-pack> --json` and
inspect `pack_audit`'s four dimensions. Integrity verified does not mean signer
trust, recipient applicability or conformity. Missing/unlisted artifacts and
historical coverage remain explicit. Do not use a deliberately altered pack as
release evidence. Human review/merge, release and pin promotion remain separate.

The final uncached Go suite passed. Affected packages passed race checks, with
review/CLI rerun after their final fixture/help updates. Vet, the gauntlet and
claim-safety checks passed, as did the focused behavioral script including the
actual Action resolver. Windows CLI cross-compilation passed; it is not a native
Windows installation test. See the remaining acceptance list above before any
broad production-readiness claim.

## Friendly-user pre-beta review

**8 September 2026: recommend merge for a small, explicitly selected source-build
pre-beta after the PR's final checks pass.** This is an engineering review by an
agent, not a recorded independent human trial, product certification or a broad
production-readiness declaration. The bundle completion defect found during
this review is fixed in this PR: `share --bundle` now stages the HTML with the
current one-pager and includes it in the completion manifest. The
[CLI regression](../internal/cli/share_bundle_audit_test.go) fails before the fix,
verifies fresh coverage, and detects changed bundle bytes afterward.

### Feasible checks conducted

| Check | Evidence and result |
|---|---|
| Actual local producer and recipient journey | Built CLI: `doctor`, write-free `scan`, `check --as-of 2026-09-08`, `demo`, `share --bundle`, copy pack to a folder outside Git, `review --json`. Run under custom HOME/TMPDIR and a path containing spaces; offline review also uses an invalid epoch. Fresh integrity and declared manifest coverage verify; authenticity remains unverified, applicability not assessed and subject commit claimed. |
| Changed or missing handoff bytes | Changed/deleted `evidence-bundle.html` fails the integrity verdict and returns nonzero. [Regression](../internal/cli/share_bundle_audit_test.go), [broader artifact tests](../internal/release/publication_test.go). |
| Cooperative interruption | Actual CLI paused while holding its writer lock: a second producer is refused and live-owner recovery is refused. After killing that process, explicit `recover-lock` succeeds; a fresh `share --bundle` and review verify again. This is one controlled process-interruption case, not arbitrary interrupted-renames or power-loss coverage. |
| Privacy of this handoff | No actual custom HOME/TMPDIR strings in any generated pack file. [Explicit-context tests](../internal/exportx/explain_boundary_test.go) and publication privacy refusal remain in force; this is not exhaustive secret detection. |
| Signature mechanism | [Real OpenSSH regression](../internal/attest/verify_real_test.go) passed with a disposable key and separate trust policy. No product/user attestation was created. |
| Website and social assets | 17 public-asset/browser tests passed. Live Pages OG title, description, canonical URL and 1200 × 630 PNG verified over HTTP. Slack/LinkedIn unfurls and a logged-out phone were not tested. |
| Release versus candidate | Published v0.5.5 installation and write-free scan are tested separately on this macOS host. The source candidate is identified by its Git SHA, even though its CLI version text still says 0.5.5. Native Linux/Windows release-installer testing remains separate from source CI. |

These checks exercise producer behavior and recipient evidence. They do not
substitute for observing whether a new person understands the output unaided.

### Pragmatic scope

Start with a few friendly users on permitted, disposable clones, using the
source candidate and the default `house-policy` pack. Use local diagnosis and
unsigned evidence handoff. Record the Git SHA, OS/architecture, command, exit
code and where the user got stuck. Report friction through the existing
[first-run feedback](https://github.com/RI-SE/curbpack/issues/new?template=first_run_feedback.yml)
or [tester report](https://github.com/RI-SE/curbpack/issues/new?template=tester_report.yml).
The repository owner coordinates support; no response-time promise is made.

For this trial, use the complete `share --bundle` recipe. Advanced partial
exports (`--skip-prepare-release`), signing/trust administration, CI Action
adoption and regulated decision-making are outside the trial scope. Keep the
recipient's intended commit, pack selection and evaluation date alongside the
pack; the tool does not infer that recipient policy.

Do not wait for enterprise-scale qualification to observe this limited local
journey. Keep the remaining native installation, arbitrary interruption,
redaction and applicability-policy work in the acceptance register. Before a
public install campaign, publish and smoke-test a new release containing the
repairs, then make any separately approved install/Action pin updates. The
[human runbook](getting-started/a2-a3-human-runbook.md) still records the actual
human and social checks; no A2/A3 pass is fabricated by this review.

### Copyable candidate trial

Go 1.23 or later and Git are required. Until merge, use the PR branch:

```bash
git clone --single-branch --branch codex/production-hardening-repairs https://github.com/RI-SE/curbpack.git curbpack-prebeta
cd curbpack-prebeta
git rev-parse HEAD                    # include this SHA in feedback
go build -o ./bin/curbpack ./cmd/curbpack
./bin/curbpack doctor
./bin/curbpack scan                   # read-only diagnosis, not a gate pass
./bin/curbpack demo                   # disposable built-in example
```

Then run the built binary by absolute path in a permitted disposable clone:

```bash
/path/to/curbpack-prebeta/bin/curbpack scan
/path/to/curbpack-prebeta/bin/curbpack check --json --as-of 2026-09-08
/path/to/curbpack-prebeta/bin/curbpack share --bundle --as-of 2026-09-08
```

The date above reproduces this review; select the intended date for later
freshness checks. `check` and `share` write local artifacts. A failing gate
returns nonzero; `share` can still produce a clearly labelled remediation pack.
Read the diagnostic rather than treating every nonzero result as a crash.
Copy the entire `review-pack` directory to a separate folder, open
`evidence-bundle.html`, and run:

```bash
/path/to/curbpack-prebeta/bin/curbpack review /path/to/received/review-pack --json
```

Expected distinctions: verified artifact integrity/manifest coverage does not
mean trusted authorship, complete product evidence or applicability to the
recipient. A review exit of zero alone is not a launch approval.
