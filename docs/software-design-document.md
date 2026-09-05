# Curbpack — Software Design Document

**Version:** 1.2 (launch release baseline, draft for human review)

**Status:** Constitutional target with a verified current-state register

**Verified baseline:** `RI-SE/curbpack@99870c57fde2d3d4eb2b5a6e60455eafb39a2007`

**Verification date:** 2026-09-04

**Implementation:** Go 1.23; no `go.mod` `require` block

**Canonical repository:** `RI-SE/curbpack`

> Curbpack prepares structural evidence for human review. It is not a
> conformity assessment, certification, CE-marking decision, notified-body
> opinion, or legal conclusion under [Regulation (EU) 2024/2847](https://eur-lex.europa.eu/eli/reg/2024/2847/oj).

This document supersedes SDD v1.0 and the proposed v1.1 text. It preserves
their load-bearing decisions, records superseded decisions explicitly, and
separates shipped behavior from target architecture. It is a release baseline,
not a claim that the design will never change.

---

## 0. Reading and evidence rules

Four statement classes appear here.

| Marker | Meaning | Required evidence |
|---|---|---|
| **MUST / MUST NOT** | Constitutional behavior | A mapped evaluation or named human governance control |
| **Decided** | Architecture selected for the next implementation slice | An ADR or SDD revision to change it |
| **Current** | Verified behavior at the pinned baseline | Command output, code, test, manifest, or repository history |
| **Target** | Approved direction not yet shipped | An implementation work package and acceptance evaluation |

Rules for this document:

1. A MUST without a mapped invariant or governance control is an SDD defect.
2. A test describing intended behavior is not proof that runtime behavior holds.
3. A control called enforced must be technically enforced. Otherwise it is policy.
4. Current and Target must not be combined into one architecture diagram or status.
5. Green automation is evidence for human review, never authorization to merge,
   release, attest, approve, bypass, or claim compliance.

Original-source policy:

- Product behavior links to implementation, tests, help, or manifests.
- Legal claims link to official legislation.
- Format claims link to the standards owner or canonical schema.
- External-tool claims link to the tool owner's documentation.
- Business hypotheses and target-customer material do not belong in this SDD.
- Search-result links and unattributed summaries are not sources.

---

## 1. Purpose, actors, and refusals

Curbpack evaluates a source repository against versioned local rule packs and
produces portable evidence that another person can inspect offline.

| Actor | Job |
|---|---|
| **Publisher** | Express requirements as a versioned pack and distribute it |
| **Producer** | Evaluate a repository locally and return evidence |
| **Reviewer** | Triage the received evidence without trusting the producer's claims |
| **Agent** | Operate declared commands and propose changes; never decide or authorize |

The exchange model is deliberately file-based:

```text
publisher supplies pack and independent trust policy
  -> producer evaluates a repository locally
  -> producer returns evaluation, receipt, and evidence
  -> reviewer independently checks integrity, authenticity, and content
```

### 1.1 Claim boundary

- **MUST-01** — Curbpack MUST NOT state or imply conformity, certification,
  CE marking, notified-body approval, legal market access, or product safety.
- **MUST-02** — Buyer-facing and reviewer-facing artifacts MUST carry the
  statement `Prepares evidence for human review — not a conformity assessment.`
- **MUST-03** — A reference reported as found means only that a typed string
  resolved to the stated local target. It does not establish claim truth.
- **MUST-04** — A score, count, signature, or status MUST retain its scope and
  MUST NOT be promoted into a broader product or regulatory verdict.

**Decided.** Restraint is a product requirement. A reviewer must be able to see
what was evaluated, what was not evaluated, and which conclusions remain human.

---

## 2. Constitutional requirements

### 2.1 Verification independence

- **MUST-10** — A verifier MUST recompute the value it checks.
- **MUST-11** — A trust anchor MUST be supplied independently from the artifact.
  An embedded key or signer entry proves self-consistency only.
- **MUST-12** — Digest comparison MUST use the full digest or a fixed,
  versioned truncation length. The claimed value cannot choose comparison length.
- **MUST-13** — A signed value MUST be re-derived from the fields it claims to
  bind before signature success is reported.
- **MUST-14** — Integrity, signer authenticity, policy applicability, freshness,
  evaluation outcome, and human disposition MUST remain separate dimensions.

### 2.2 Evidence integrity

- **MUST-20** — A run that writes files MUST NOT report a better result than a
  read-only evaluation over the resulting unchanged tree.
- **MUST-21** — A rule that examined zero required targets MUST NOT pass.
- **MUST-22** — Failed reads, writes, parses, subprocesses, or incomplete walks
  MUST NOT be omitted or reported as success.
- **MUST-23** — A skipped rule MUST appear in every output channel and MUST make
  the aggregate outcome `incomplete`.
- **MUST-24** — A required artifact that is present but unreadable MUST be a
  contradiction or operational error, never a confirmation.
- **MUST-25** — External evidence and source metadata MUST NOT change a gate result.

### 2.3 Determinism and cache integrity

- **MUST-30** — Identical explicit evaluation inputs MUST produce byte-identical
  canonical evaluation bytes and identical digests.
- **MUST-31** — The evaluation input includes repository snapshot, pack bytes,
  trust policy, evaluator version, and explicit `as_of`; it excludes implicit
  wall clock, user, home directory, hostname, locale, and filesystem order.
- **MUST-32** — Ordering that feeds a digest MUST be total over every covered field.
- **MUST-33** — Digest encodings MUST be injective through length-prefixing or an
  equivalent versioned canonical encoding.
- **MUST-34** — Caches are derived and non-authoritative. Exports MUST consume the
  exact evaluation they identify, not an unverified `latest` file.
- **MUST-35** — Cache and artifact writes MUST be atomic and safe under concurrent
  processes. Interrupted writes cannot replace the last complete record.

### 2.4 Untrusted input, resources, and privacy

- **MUST-40** — Repositories, review packs, configuration, remediation caches,
  imported packs, source registers, and external evidence are untrusted input.
- **MUST-41** — Untrusted content MUST NOT become a subprocess option or command.
- **MUST-42** — Reads and writes MUST remain under their declared root after
  resolving the complete path, including intermediate symlinks.
- **MUST-43** — Untrusted strings MUST be normalized, length-bounded, and escaped
  once at ingest; downstream renderers receive typed safe values.
- **MUST-44** — Per-file bytes, total bytes, file count, subprocess time, and
  captured output MUST have explicit limits before allocation or execution.
- **MUST-45** — Repository-local Git configuration that can execute commands MUST
  be neutralized for evaluator subprocesses.
- **MUST-46** — Cancellation MUST terminate subprocesses and remove incomplete
  temporary output without deleting the previous complete artifact.
- **MUST-47** — Default records MUST NOT disclose absolute home paths, usernames,
  environment secrets, credentials, or repository content not required by schema.
- **MUST-48** — Network capability is declared per command. Evaluation and review
  MUST NOT perform network access.

### 2.5 Channel and outcome parity

- **MUST-50** — Human caveats, warnings, skips, and qualifications MUST appear in
  machine output for the same evaluation.
- **MUST-51** — Terminal, JSON, cache, export, and exit status MUST derive from
  one canonical evaluation.
- **MUST-52** — Machine outcome is one of `pass`, `findings`, `incomplete`, or
  `error`; a consumer MUST NOT infer it from prose or a score.
- **MUST-53** — Existing process exit compatibility remains `0` pass, `1`
  findings or operational failure, and `2` usage or environment. Machine output
  distinguishes categories until a major version may separate exit codes.

### 2.6 Documentation and compatibility

- **MUST-60** — Every command printed in an agent-facing or operator-facing file
  MUST execute as printed.
- **MUST-61** — Every command has a declared effect class, audience, machine-output
  support, and deprecation state in one registry.
- **MUST-62** — Breaking schema or CLI changes require a major version, golden
  migration fixtures, and a CHANGELOG entry.
- **MUST-63** — Unknown additive fields are ignored safely and preserved by any
  component that round-trips their containing document.

### 2.7 Human and agent authority

- **MUST-70** — `--i-am-human` and `CURBPACK_ALLOW_CONFIRM=1` are policy
  acknowledgements, not technical proof of humanity.
- **MUST-71** — Agents MUST NOT merge, release, attest, approve, enable auto-merge,
  use an administrator bypass, or treat green output as authorization.
- **MUST-72** — Human-authority acts are `trust-import`, `review-sign`,
  `Last tabletop:`, `confirm-*`, `attest`, and `pin-bump`.
- **MUST-73** — Genuine authority rests on a credential or repository decision
  the agent does not control, not on a command-line flag.
- **MUST-74** — `/rollback` and rollback guidance are instructional. An agent does
  not mutate, revert, or deploy automatically from that instruction alone.

### 2.8 Portability and release integrity

- **MUST-80** — The evaluator uses the Go standard library and has no third-party
  Go runtime dependency. Optional OpenSSH operations are a separately reported adapter.
- **MUST-81** — `scan`, `check`, evidence production, and `review` work without a
  server, database, account, or network.
- **MUST-82** — Every format crossing a repository or organization boundary has
  a versioned schema and at least one golden example.
- **MUST-83** — Release binaries have reproducible build inputs, checksums, least-
  privilege workflows, and immutable release references.
- **MUST-84** — A platform is called supported only when its release artifact and
  representative workflow are exercised. Windows remains supporting until promoted.

### 2.9 Product trust and sustainability

- **MUST-90** — The canonical public repository and history are not replaced or
  rewritten to improve presentation.
- **MUST-91** — Current official releases remain under their published
  [Apache-2.0 license](../LICENSE). Future licensing commitments require documented
  RI-SE authority and legal review.
- **MUST-92** — Local evaluation and offline review MUST NOT depend on payment,
  account status, entitlement, or hosted-service availability.
- **MUST-93** — Optional commercial services MUST NOT change findings, evidence
  semantics, verification, or access to previously exported artifacts.
- **MUST-94** — Earlier public strategy documents remain in history and are
  identified as experiments when consolidated, not silently recast as commitments.
- **MUST-95** — Public vulnerability status is honest. Exploitable detail may use
  coordinated disclosure under [SECURITY.md](../SECURITY.md) until remediation.
- **MUST-96** — Pricing, target accounts, conversion assumptions, payment-provider
  choice, and private adoption metrics remain outside the product SDD.

---

## 3. Architecture

### 3.1 Current architecture

At the verified baseline, pack composition and evaluation produce
`ir.GateFailurePayload`; terminal, cache, Action, exports, release artifacts,
and review use related but separate structures. The current implementation is
documented by [`internal/validate`](../internal/validate/),
[`internal/ir`](../internal/ir/), [`internal/exportx`](../internal/exportx/),
[`internal/release`](../internal/release/), and [`internal/review`](../internal/review/).

Current limitations:

- The payload mixes deterministic findings with wall-clock and agent metadata;
  `--diff` skips now set `outcome=incomplete` and `skipped_rules` in the same IR (FG-05).
- Cache writes use direct `os.WriteFile` calls and `latest_*` names.
- Findings and trust states are re-declared across components.
- Digest comparison uses a fixed 12-hex prefix floor (MUST-12 / FG-04 closed);
  shorter claimed values cannot confirm.
- `review --verify-chain` recomputes parent and child `record_digest` values and
  requires `child.parent_record_digest` to equal the recomputed parent digest
  (FG-07 closed).
- Attestation can fall back to keys from the current SSH agent.
- The OpenSSH verifier invocation omits the required signer identity and is
  covered by a fake binary rather than a real-signature integration test.
- No crossing format has a schema under a canonical `schema/` directory.

### 3.2 Target architecture

```text
explicit inputs
  repository snapshot + pack bytes + trust policy + evaluator version + as_of
                              |
                              v
                    deterministic evaluation
                              |
                 +------------+-------------+
                 |                          |
       canonical evaluation         operational run receipt
       findings/skips/outcome        duration/platform/tool
                 |                          |
                 +------------+-------------+
                              v
                 terminal / JSON / SARIF / HTML
```

Five concerns remain separate:

1. **Evaluation** is deterministic and side-effect free except for returning data.
2. **Run receipt** records operational metadata and hashes the evaluation it observed.
3. **Rendering** consumes the canonical evaluation; it does not re-decide outcomes.
4. **Workspace effects** declare and contain cache, scaffold, export, and external effects.
5. **Trust assessment** reports integrity, authenticity, applicability, freshness,
   evaluation outcome, and human disposition independently.

### 3.3 Verification boundary

The target verifier is a pure function over independently supplied values:

```text
artifact bytes + claimed contract + trusted policy -> typed trust assessment
```

It does not write, call Git, read environment variables, fetch a URL, or discover
its trust anchor inside the artifact being checked. A self-contained bundle can
prove internal consistency; it cannot prove that its embedded signer is trusted.

### 3.4 Cache model

Each canonical evaluation is stored by its full digest. A `latest` pointer may
exist for operator convenience, but it is written atomically and is never an
evidence source. Exports name and verify the evaluation digest they consume.

---

## 4. Public data contracts

### 4.1 Pack and rule

The existing pack model remains: identity, name, version, composition,
jurisdiction, validity, citations, provenance, and rules. A rule carries stable
identity, severity, check kind, description, remediation, expected state,
citations, and check-specific fields. Current definitions live in
[`internal/packs/packs.go`](../internal/packs/packs.go).

Pack-authored `assurance_class` is legacy input, not proof. Target artifacts
report typed coverage and unevaluated scope. A scalar score cannot substitute
for findings, skips, or coverage.

Validity is evaluated against explicit `as_of`, never implicit wall clock in a
canonical evaluation. Source retrieval time belongs to source metadata or a run
receipt and is supplied as data.

### 4.2 Versioned target schemas

| Contract | Purpose | Deterministic |
|---|---|---|
| `curbpack-evaluation:1` | Subject, pack coordinates, outcome, findings, skips, caveats, digest | Yes |
| `curbpack-run-receipt:1` | Evaluation digest, duration, platform, tool version, artifact hashes, `as_of` | No; hashes deterministic evaluation |
| `curbpack-source-register:1` | Generic original-source provenance | Yes for supplied entries |
| `curbpack-external-evidence:1` | Arbitrary external artifact metadata without importing its verdict | Yes for supplied entries |

`Outcome` is `pass | findings | incomplete | error`.

`EffectClass` is `read_only | cache_write | workspace_write | external_effect |
human_authority`.

`TrustAssessment` contains separate integrity, authenticity, freshness,
applicability, evaluation, and disposition values.

The generic source entry contains `id`, `class`, `title`, `publisher`, `locator`,
`version`, `digest`, and `scope`. Source classes are generic. The core schema has
no customer, payment, target-industry, or vendor-specific field.

### 4.3 External interoperability

External evidence enters through files. Safe initial interchange candidates are
[SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html),
[SPDX](https://spdx.dev/specifications/),
[CycloneDX](https://cyclonedx.org/specification/overview/), and
[ReqIF](https://www.omg.org/reqif/). Scanner output and QMS exports remain
outside the evaluator unless a versioned adapter is justified by a named
consumer and fixture. Imported tool verdicts remain attributed external claims;
Curbpack does not promote them into its own outcome.

CTAM and any future consumer use the same public files. Curbpack does not import
their libraries, require their credentials, or depend on their availability.

---

## 5. Check algebra and command model

### 5.1 Check kinds

**Current.** Eight kinds are registered in
[`internal/validate/checks.go`](../internal/validate/checks.go):
`annex_file`, `file_present`, `anti_placeholder`, `npm_dep_ban`,
`manifest_dep_ban`, `text_forbid`, `fresh`, and `owned`.

**Decided.** `import_reach` was removed because it ignored its declared target,
passed missing or unparsable input, and had no embedded-pack consumer. The
eight kinds form the closed evaluator algebra. `references` belongs
to offline review; human-approved trace edges belong to an external crossing
format. Neither becomes a tenth evaluator kind without an ADR proving that
composition and external evidence are insufficient.

Every check descriptor will own validation, evaluation, scaffolding, diff
behavior, form hints, effect information, and documentation. Generated tests
keep the registry and documentation aligned.

### 5.2 Command surface

**Current.** The command registry contains 20 top-level commands in
[`internal/cli/registry.go`](../internal/cli/registry.go).

**Target primary workflow:** `scan`, `init`, `check`, `fix`, `share`, `review`.
Specialist commands remain available under advanced help until evidence supports
consolidation. The registry becomes the source for effect class, audience,
machine-output support, aliases, and deprecation metadata.

`check --heal` compatibility:

- v0.6 keeps it as a deprecated path implemented as explicit stub remediation
  followed by a fresh full check.
- New documentation uses `fix --stubs --preview`, human confirmation, then `check`.
- v0.7 removes `--heal` only after Action, hook, Cursor, Codex, and Claude
  migration evaluations pass.
- The implementation is shared; compatibility does not create a second healing path.

---

## 6. Trust and signatures

### 6.1 v0.x decision

OpenSSH signatures remain an optional adapter around the standard-library
evaluator. Current code is in [`internal/attest`](../internal/attest/).

The target contract is stricter than current behavior:

- The verifier receives `allowed_signers` independently from the artifact.
- It does not fall back to arbitrary keys in the reviewer's SSH agent.
- Missing OpenSSH yields `authenticity: not_checked`, never verified.
- Invalid, unknown-signer, expired, and policy-inapplicable remain distinct.
- An expired signature may support a separate continuity disposition but cannot
  become verified through an override.
- Source, derivation, review, and release use distinct namespaces.
- The signed evaluation digest is re-derived before signature verification.

DSSE or Sigstore requires a later ADR with a relying-party requirement,
offline-operability evaluation, dependency analysis, and migration fixture.
It is not a v0.x prerequisite.

---

## 7. Assurance method

### 7.1 Evaluation levels

| Level | Question |
|---|---|
| **Unit** | Does one function satisfy its contract? |
| **Functional** | Does one command produce the required observable behavior? |
| **Integration** | Does the behavior hold against real filesystems, Git, tools, and hostile input? |
| **Acceptance** | Does the publisher-producer-reviewer journey produce usable evidence? |

Fuzzing, mutation, race detection, repeated execution, and model comparison are
techniques applied at a level, not additional levels. An LLM may propose or
annotate an evaluation; it does not determine pass or fail.

### 7.2 Assurance catalogue

`testdata/assurance/catalog.json` is the target catalogue for constitutional
invariants, escaped defects, crossing integrations, and operator journeys.
Ordinary Go tests remain auto-discovered and uncatalogued.

Each entry has `id`, `level`, `basis`, `observable`, `executor`,
`fixture_or_pin`, `criticality`, `status`, and `known_limitation`.

Prefixes are `INV-*` constitutional invariant, `REG-*` escaped defect,
`INT-*` crossing integration, and `ACC-*` operator journey.

Constitutional traceability is explicit. A requirement may map to more than one
invariant when its observable crosses boundaries.

| Invariant | Constitutional requirements |
|---|---|
| `INV-01` Claim boundary | MUST-01 through MUST-04 |
| `INV-02` Independent verification | MUST-10 through MUST-14 |
| `INV-03` Write/read result equivalence | MUST-20 |
| `INV-04` Deterministic canonical evaluation | MUST-30 through MUST-33 |
| `INV-05` Path, subprocess, and input containment | MUST-40 through MUST-42, MUST-45, MUST-48 |
| `INV-06` Resource bounds and privacy | MUST-43, MUST-44, MUST-46, MUST-47 |
| `INV-07` Complete and channel-consistent outcomes | MUST-21 through MUST-25, MUST-50 through MUST-53 |
| `INV-08` Atomic, non-authoritative cache | MUST-34, MUST-35 |
| `INV-09` Command truth and effect declaration | MUST-60 through MUST-63 |
| `INV-10` Human authority | MUST-70 through MUST-74 |
| `INV-11` Versioned crossing schemas | MUST-62, MUST-63, MUST-82 |
| `INV-12` Portability and release integrity | MUST-80, MUST-81, MUST-83, MUST-84 |
| `INV-13` Public trust and sustainability | MUST-90 through MUST-96 |

### 7.3 Change proof

- Constitutional and escaped-defect changes begin with a failing evaluation
  committed before the implementation commit.
- Routine refactors do not require artificial failing commits.
- Positive, negative, and adversarial cases cover every gate.
- Write paths prove preview, containment, idempotence, interruption recovery,
  and equivalence with a subsequent read-only evaluation.
- Deterministic behavior uses exact exit status, typed JSON, bytes, and digests,
  not prose substrings.
- Expected results are independently authored or frozen; the implementation
  cannot generate its own oracle.
- Pull requests include an operator-readable before/after acceptance transcript.

### 7.4 Balanced release scoreboard

| Metric | Release target | Baseline status |
|---|---:|---|
| `false_green_paths_open` | 0 | **0 open** |
| `reference_green_pass_rate` | 100% | Unmeasured; private positive fixture pending |
| `required_mutation_detection_rate` | 100% | Public gauntlet 10/10; full corpus pending |
| `incomplete_reported_as_pass` | 0 | Passing: `--diff` skip records incomplete + skipped_rules in cache |
| `channel_parity_failures` | 0 | Passing: FG-01–FG-07 closed |
| `time_to_first_valid_evidence` | <= 60 s | Passing: 6 s local baseline |

No global statement-coverage threshold is a release gate. Coverage guides test
selection; risk-to-evaluation traceability controls release.

The private reference product repository is the positive fixture. Tests operate
on disposable copies. Each mutation removes or corrupts one expected property
and must produce the specified failure. Private holdouts reduce overfitting to
the public corpus.

Required metamorphic cases: repository relocation, environment variation,
ordering, repeated execution, heal-then-check equivalence, tampered artifacts,
stale cache, concurrent writers, interruption, and changed `as_of`.

---

## 8. Verified baseline and invariant register

Measurements below were executed at the pinned baseline. Coverage used
`go test ./... -coverprofile`; counts used repository searches.

| Measure | Result |
|---|---|
| Go test / fuzz declarations | 434: 431 tests, 3 fuzz targets |
| Go test files | 100 |
| `t.Run` subtests | 23 |
| Statement coverage | 57.2% |
| Registered top-level commands | 20 |
| Registered check kinds | 8 |
| Embedded packs | 3 |
| Required CI contexts | 5 in [required-checks.json](../.github/required-checks.json) |
| Third-party Go requirements | 0 in [go.mod](../go.mod) |
| Canonical schema files | 0 |
| `go test ./...` | **Failing when run uncached**; heal-equivalence JSON includes wall-clock time |
| `go test -race ./...` | Passing at the pinned baseline; rerun after the timing fix |
| `go build ./...`, `go vet ./...` | Passing |
| Claim safety | Passing |
| Red-team pilot | 15 passed, 0 failed |
| Gauntlet | 10 matched, 0 failed |
| Time to green | 6 seconds under 60-second gate |
| Current install release | v0.5.4 in [install-manifest.json](../scripts/install-manifest.json) |
| Documented Action pin | Current fixed release in [action.yml](../action.yml); deliberate human pin-bump gate |

Invariant status:

| INV | Subject | Status at baseline |
|---|---|---|
| INV-01 | Claim boundary | Passing automated claim-safety; human regulatory review pending |
| INV-02 | Independent verification | **Failing** |
| INV-03 | Write/read result equivalence | Heal outcome parity passes; exact JSON parity is timing-dependent |
| INV-04 | Deterministic canonical evaluation | **Failing**; evaluation and receipt not separated |
| INV-05 | Path, subprocess, and untrusted-input containment | Partial; path jail passes; evaluator Git config neutralized and option-shaped refs fail closed |
| INV-06 | Resource bounds and privacy | Partial; review caps exist, evaluator-wide budgets do not |
| INV-07 | Channel and outcome parity | Partial; FG false-greens closed; broader receipt/parity work remains in later WPs |
| INV-08 | Atomic, non-authoritative cache | **Failing** |
| INV-09 | Command truth and effect declaration | **Failing** |
| INV-10 | Human authority described accurately | **Failing**; acknowledgement is labelled as a gate |
| INV-11 | Versioned crossing schemas | **Failing** |
| INV-12 | Release and platform integrity | Partial; Windows supporting, module identity migration open |
| INV-13 | Public trust and sustainability | Target pending authorized human review |

### 8.1 Open false-green paths

The v1.1 reproduction established seven paths. The heal-consistency repair in
[`99870c5`](https://github.com/RI-SE/curbpack/commit/99870c57fde2d3d4eb2b5a6e60455eafb39a2007)
closed the original outcome-parity defect. Current-baseline execution then
identified a separate chain-verification path. FG-01 through FG-07 are closed;
`false_green_paths_open` is 0.

Closed:

| ID | Prior path | Evidence |
|---|---|---|
| FG-03 | `import_reach` ignored the declared path and passed missing or unparsable `src/payment.go`; kind removed from registry and pack validate (eight kinds remain) | [`checks.go`](../internal/validate/checks.go), [`validate.go`](../internal/validate/validate.go), [`packs.go`](../internal/packs/packs.go), [`import_reach_removed_test.go`](../internal/validate/import_reach_removed_test.go) | INV-05, INV-07 |
| FG-02 | Repository-derived JSON was embedded raw in a script element and could alter offline bundle presentation; embed now uses JSON Unicode escapes for `&`, `<`, and `>` (MUST-43) | [`bundle.go`](../internal/release/templates/bundle.go), [`script_embed_test.go`](../internal/release/templates/script_embed_test.go) |
| FG-05 | `--diff` could skip rules while machine cache recorded a complete-looking score without skip state; cache and JSON now carry `outcome=incomplete` and `skipped_rules` (MUST-23, MUST-52) | [`validate.go`](../internal/validate/validate.go), [`gatefailure.go`](../internal/ir/gatefailure.go), [`diff_skip_cache_test.go`](../internal/validate/diff_skip_cache_test.go) |
| FG-01 | A forged one-pager that copied the current fingerprint marker could suppress rewrite and present the marker as confirmed; rewrite now compares content fingerprints, and marker presence is unconfirmed/producer | [`release.go`](../internal/release/release.go), [`review.go`](../internal/review/review.go), [`fingerprint_forge_test.go`](../internal/release/fingerprint_forge_test.go) |
| FG-04 | A one-character claimed digest could confirm because comparison length derived from the claim; fixed 12-hex floor (MUST-12) | [`review.go`](../internal/review/review.go), [`digest_prefix_test.go`](../internal/review/digest_prefix_test.go), [`release.go`](../internal/release/release.go) |
| FG-06 | A present but unreadable required gate JSON layer was first confirmed and its parse/digest findings could disappear; structure now requires a successful open, and loadPayload keeps a contradicted parse finding | [`review.go`](../internal/review/review.go), [`unreadable_gate_json_test.go`](../internal/review/unreadable_gate_json_test.go) |
| FG-07 | `review --verify-chain` accepted fabricated reports when the child copied a parent-supplied digest string without recomputation | [`review.go`](../internal/cli/review.go), [`review_verify_chain_test.go`](../internal/cli/review_verify_chain_test.go) |
| REG-HEAL-01 | `check --heal` returned 100/0/exit-0 while immediate `check` returned 60/2/exit-1; score, findings, and exit parity are repaired, but byte parity remains open under INV-04 | [`check_json_heal_test.go`](../internal/cli/check_json_heal_test.go), [PR #40](https://github.com/RI-SE/curbpack/pull/40) |

Additional open violations are tracked separately from the false-green count:

- Evaluator Git subprocesses neutralize repository-local executable configuration
  (`-c` overrides + stripped dangerous `GIT_*` env) and reject option-shaped refs
  (MUST-41, MUST-45); see [`gitutil.go`](../internal/gitutil/gitutil.go) and
  [`git_harden_test.go`](../internal/gitutil/git_harden_test.go).
- The documented `curbpack ask <path> --propose` order fails because Go flag
  parsing stops at the positional argument.
- Direct cache writes are non-atomic and cache-write failure is warning-only.
- Current records include implicit time and environment-derived identity.
- `go test ./... -count=1` fails because the heal-equivalence test compares JSON
  records whose wall-clock timestamps can cross a one-second boundary.
- The real `ssh-keygen -Y verify` invocation fails because it omits `-I` and does
  not provide the signed message on standard input; current tests stub the binary.
- Confirm policy agent-contract wording aligns with MUST-70: `--i-am-human` or
  `CURBPACK_ALLOW_CONFIRM=1` required; TTY alone is not enough (whitepaper +
  agent docs; `TestConfirmPolicyWording_NoTTYAloneAuth`).
- Public surfaces still say that the gate is deterministic and "cannot be argued
  with," describe green as expensive to fake, and contain a stale static countdown.
  These claims are contradicted or unsupported by the current verified baseline
  (follow-on wording; not MUST-70).
- The Go module path remains `github.com/afelin/curbpack` while the public source
  of truth is `RI-SE/curbpack`; migration requires a major-version plan.

---

## 9. Product trust, history, and sustainable operation

### 9.1 Public trust record

Early public documents combined product contracts, discovery experiments,
adoption operations, and commercial hypotheses. The public history is retained.
Notable originating commits include
[`2cae2cc`](https://github.com/RI-SE/curbpack/commit/2cae2cc971f2317f35bd88aae6a0f3a611aac37e),
[`86f1dc8`](https://github.com/RI-SE/curbpack/commit/86f1dc813e559326e05ab1875981e6e873cec8fc),
[`4ee93d0`](https://github.com/RI-SE/curbpack/commit/4ee93d06906c88974294528fcb5e57955141cf3e),
[`8c2ed48`](https://github.com/RI-SE/curbpack/commit/8c2ed488180bfc12d4d9db682b3aa6f60cab9056),
and [`ae34408`](https://github.com/RI-SE/curbpack/commit/ae34408c8d1f4d19247e2d1cd81adfab2e2ab9aa).

Consolidating those files means:

- current product contracts move into this SDD and stable contract documents;
- historical experiments remain discoverable through commits and CHANGELOG;
- obsolete operating templates may leave the current documentation tree through
  an explicit, reviewable commit;
- no deletion is represented as erasure of the historical record;
- any discovery of credentials, personal data, contractual material, or legally
  restricted information starts a separate incident process.

### 9.2 Commercial boundary

Current releases are Apache-2.0 and independently usable. Optional future paid
services may include maintained packs, private distribution, supplier-program
coordination, onboarding, training, and support.

Payment controls hosted convenience only. It cannot unlock correctness, alter a
finding, suppress evidence, establish trust, or revoke access to previously
exported files. Producers can run the evaluator and answer a publisher without
being charged per scan, finding, repository, or response.

Detailed pricing, target accounts, sales operations, provider choices, and
adoption economics live in private operator governance. A hosted service starts
only after its private adoption gate is met and a human owner authorizes it.

### 9.3 Infrastructure boundary

GitHub is the current source, build, release, and static distribution plane.
Cloudflare may later host a replaceable edge for pack distribution, invitations,
receipt intake, or payment webhooks. Oracle remains out until measured workload
requires back-office storage or compute. Neither becomes an evaluator or offline
verification dependency.

---

## 10. Communication and no-code operation

The README, site, CLI, agent skill, Action, and generated artifacts share one
vocabulary and one claim boundary. Public surfaces lead with the read-only first
step and distinguish local gate outcome from human review.

For a no-code operator:

- the primary path contains no more than the six commands in §5.2;
- every write shows its target and preview before confirmation;
- every failure gives one next action and non-destructive rollback guidance;
- cockpit comments show state, evidence, next action, and rollback without
  requiring log inspection;
- agents stage named paths and stop at human-authority boundaries;
- advanced commands do not crowd the first-use help surface.

Dates in cached public metadata are literal dates, never countdown values.
Generated text and containers must remain readable on supported desktop and
mobile surfaces.

---

## 11. Scope fence

Do not build these into the public evaluator:

- a server, database, account requirement, or hosted policy brain;
- a model that decides pass, fail, trust, or compliance;
- telemetry, beacons, automatic source upload, or phone-home behavior;
- a registry, marketplace, or supplier portal before the private adoption gate;
- payment, entitlement, or license checks in evaluation or verification;
- bespoke PKI, certificate-chain, or revocation infrastructure;
- embedded PDF, office-document, or broad XML parsers;
- a persistent graph database or query language;
- a tenth evaluator check kind without the §5.1 ADR;
- autonomous merge, release, attestation, approval, deployment, or rollback;
- a second assurance catalogue or a global coverage-percentage gate.

Capability that does not name a consumer, invariant, and deletion condition does
not enter the implementation roadmap.

---

## 12. Sequential work packages

Each package is a separate reversible pull request unless a human approves a
smaller merge grouping. A later package does not start before its entry gate.

| WP | Work | Entry gate | Exit evaluation | Rollback |
|---|---|---|---|---|
| **W0** | Adopt SDD v1.2 | Current baseline reproduced | One-file review; all statuses sourced | Revert SDD commit |
| **W1** | Correct contradicted public claims; close FG-01 through FG-07; remove `import_reach`; neutralize executable Git configuration and validate option-like Git inputs | W0 human-merged | `false_green_paths_open=0`; hostile Git configuration cannot execute; option-shaped refs fail closed; regressions red before fix | Revert each independent fix |
| **W2** | Canonical evaluation, typed outcome, receipt split, atomic content-addressed cache | W1 complete | Repeated bytes/digests equal; interruption and concurrency tests | Preserve legacy readers behind adapter |
| **W3** | Command metadata and explicit remediation; correct `ask` syntax and human-acknowledgement wording; deprecate `--heal` | W2 stable | Generated command-truth tests and Agent/Action/hook/no-code migration matrix | Restore compatibility alias only |
| **W4** | Independent OpenSSH trust policy and typed trust assessment | W2 stable | Real-binary sign/verify tests; no embedded or agent-fallback trust; missing or unusable OpenSSH reports `not_checked` | Disable optional authenticity adapter |
| **W5** | Four versioned schemas and generic external evidence | W2 model frozen | Golden round trips and unknown-field compatibility | Keep schemas supporting until promoted |
| **W6** | Release identity, immutable references, Windows promotion evidence, module-path plan | W1-W5 required slices green | Install/action/release matrix and checksums | Retain prior release and pins |
| **W7** | Consolidate historical public documents after W1 has corrected current product claims | W1 complete; RI-SE wording review | Links, claim safety, history references, current pins | Revert documentation commit |
| **W8** | Optional hosted coordination and payment | Private adoption gate and human budget owner | Core works during hosted outage and after entitlement expiry | Disable hosted service; files remain usable |

W0 is the only product-repository change authorized by this document's adoption
pull request. W1 and later require their own reservations, evaluations, and review.

---

## 13. Release and change control

| Change | Required control |
|---|---|
| Behavioral change | Reproduction, mapped evaluation, acceptance transcript |
| Constitutional or escaped-defect change | Failing evaluation commit before fix commit |
| New evaluator kind | ADR proving existing composition and external evidence insufficient |
| Trust, digest, attestation, or crypto | Outside human review before merge |
| Crossing format | Versioned schema, golden example, compatibility test |
| New required CI context | Three clean supporting runs, then human ruleset change |
| Public licensing or durability commitment | Documented RI-SE authority and legal review |
| Hosted or payment capability | Private adoption gate and explicit human authorization |

Required release evidence includes `git diff --check`, `go test ./...`,
`go test -race ./...`, `go vet ./...`, `go build ./...`, required-context
validation, claim safety, red-team, gauntlet, and the 60-second time-to-green
gate. Windows evidence is supporting until promoted under this table.

An agent that encounters the same blocking evaluation three times stops and
revises the plan. It does not weaken the evaluation, retry indefinitely, or
declare the condition accepted.

Concurrent writers use registered independent clones, one agent-prefixed story
branch each, WIP of one, non-overlapping path reservations, advisory preflight,
and named-path staging. Unknown work is preserved; no agent force-removes or
discards another checkout.

---

## 14. Acceptance of this baseline

SDD v1.2 is accepted only when a human reviewer can determine:

1. what Curbpack evaluates and refuses to claim;
2. what is shipped, failing, unverified, and targeted;
3. which trust dimension supports each displayed status;
4. which evidence can be reproduced without Curbpack infrastructure;
5. which capabilities may become paid and which remain independently usable;
6. why earlier strategy material changed and where its history remains;
7. which evaluation and human control maps to every MUST;
8. how each work package is proven and reverted.

Approval of this SDD authorizes review of W0 only. It does not merge W0,
authorize W1, qualify v0.6.0, approve public organizational commitments, or
start a hosted service.

---

## 15. Document history

| Version | Change |
|---|---|
| 1.2 | Launch release baseline: reconciles v1.0 product design, v1.1 assurance requirements, current implementation, balanced evaluations, explicit effects and outcomes, independent trust, public-history transparency, and sustainable commercial boundaries. |
| 1.1 | Proposed constitutional invariants and reproduced false-green register; not adopted as the repository SDD. |
| 1.0 | Initial target architecture, pack/check design, trust sketches, command model, and build waves. |

A future revision must update verified status, supersede a decision with reasons,
or change a constitutional requirement. Editorial churn alone does not earn a
new SDD version.
