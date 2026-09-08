# Crossing-format compatibility (MVP)

Curbpack crossing formats are versioned by `schema_version` / `schema` string.
Evaluation and receipt v2 have explicit JSON Schemas and semantic validators.
Other rows below retain their existing compatibility scope.

## Formats

| Contract | Golden | Deterministic |
|---|---|---|
| GateFailure IR (`schema_version` `"1"`) | [gate-failure-1.golden.json](gate-failure-1.golden.json) | Findings yes; timestamp/agent on receipt side |
| `curbpack-evaluation:1` | [historical example](curbpack-evaluation-1.golden.json) | Historical partial identity; do not promote to a complete v2 evaluation |
| `curbpack-evaluation:2` | [schema](curbpack-evaluation-2.schema.json), [golden](curbpack-evaluation-2.golden.json) | Yes for identical complete input identity and explicit `as_of` |
| `curbpack-run-receipt:2` | [schema](curbpack-run-receipt-2.schema.json), [golden](curbpack-run-receipt-2.golden.json) | Operational metadata; binds full evaluation digest |
| `curbpack-run-receipt:1` | [curbpack-run-receipt-1.golden.json](curbpack-run-receipt-1.golden.json) | Receipt timestamps may vary; `evaluation_digest` binds the evaluation |
| Explain-packet (`schema_version` `"1"`) | [explain-packet-1.golden.json](explain-packet-1.golden.json) | Airlocked text; readiness kept for machines |
| ContextPack (`schema_version` `"1"`) | [context-pack-1.golden.json](context-pack-1.golden.json) | Washed assistant snapshot |
| `curbpack-review-report:2` | [review-report-2.golden.json](review-report-2.golden.json) | Document triage only |
| `curbpack-source-register:1` | [curbpack-source-register-1.golden.json](curbpack-source-register-1.golden.json) | Illustrative forward shape |
| `curbpack-external-evidence:1` | [curbpack-external-evidence-1.golden.json](curbpack-external-evidence-1.golden.json) | Illustrative forward shape |

## Rules

1. **Additive fields** — unknown fields MUST be ignored by readers and preserved
   by any component that round-trips historical documents (MUST-63). Canonical
   v2 evaluation readers reject unbound fields and noncanonical bytes; a changed
   canonical field set requires a versioned contract.
2. **Historical digests** — `readiness_score` and other pre-count fields remain
   readable. New emissions also carry `failed_rules` / `evaluated_rules` /
   `skipped_rules` and `conformity_claim: "none"`. Result digests that historically
   omitted these fields stay readable. V2 evaluation bytes bind the complete
   input identity. New result digests bind `evaluation_digest` with a versioned
   domain marker; its absence retains the frozen historical algorithm. V1
   evaluation objects without `conformity_claim` do not gain it during hashing.
3. **Breaking changes** — rename or semantic change of a required field requires
   a new `schema_version` major (MUST-62) plus a CHANGELOG entry and golden.
4. **`conformity_claim`** — tip value is always `"none"`. Absence on historical
   documents means the same: no conformity assessment.
5. **Trends** — require verified evaluations with matching schema and full
   `comparison_key`: method, tool version, exact pack digests, time, trust-policy
   mode and evaluated/skipped scope. Missing identity suppresses a trend.
6. **Human surfaces** — terminal, one-pager, action report, ask, and demo show
   failed/evaluated/skipped counts. They must not present readiness as a percent
   grade or thermometer. JSON may still include `readiness_score` for fingerprint
   and historical compatibility.

Not certification. Not a notified-body decision.

## V2 time and cache

`check`, `validate`, `prepare-release` and `share` accept `--as-of` as a UTC date
or RFC3339 instant. It is normalized and recorded. Without an explicit argument,
a valid `SOURCE_DATE_EPOCH` supplies the instant; otherwise the command captures
today's UTC date. Invalid supplied epochs fail even when `--as-of` is explicit.
Freshness consumes that recorded instant rather than consulting the wall clock.

The canonical evaluation includes exact pack-source SHA-256 digests, evaluated
file digests or explicit missing/refused states, relevant Git metadata identity,
subject commit status, and full/diff rule scope. Git subject identity is a
producer claim to an offline reviewer. Operational workflow state, agent
identity, execution duration/platform and receipt timestamp are outside the
canonical evaluation.

Cache objects live under `evaluations/<sha256>.json` and `receipts/<sha256>.json`.
The `latest.json` pointer advances atomically after both objects and legacy
aliases are written. Readers recompute object digests and validate the binding;
mutable `latest_failure.json` and `latest_result.json` are compatibility outputs,
not an independent evidence source. An interrupted write can leave unreferenced
objects. It does not advance the authoritative pointer. A complete release-pack
publication record is a separate remaining acceptance item.

## Pack completion and audit extensions

`curbpack-pack-manifest:1` binds exact artifact paths, sizes and full SHA-256
hashes, including canonical evaluation and operational receipt bytes. The writer
publishes this file last after staging and verifying the declared set. Readers
must verify the whole manifest; a filename or an old manifest alone is not
completion evidence. Unknown fields and noncanonical manifest/receipt encodings
are refused by the versioned parser. Hash consistency is not signer trust.

`curbpack-pack-audit:1` is an optional `pack_audit` extension on the existing
review report. It is included in that report's digest when present. Its omission
preserves historical report digest bytes, tested against the unchanged prior
comparison report fixture. Integrity, authenticity, completeness and
applicability carry separate statuses. The current offline engine does not
establish signer authenticity or recipient applicability. `subject_commit` is
claimed unless independently established; no such upgrade occurs in bundle mode.
Both new formats require `conformity_claim: none`.
