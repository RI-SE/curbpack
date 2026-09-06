# Crossing-format compatibility (MVP)

Curbpack crossing formats are versioned by `schema_version` / `schema` string.
This page is the one-page policy for readers; fuller JSON Schema freeze remains
future work (W5).

## Formats

| Contract | Golden | Deterministic |
|---|---|---|
| GateFailure IR (`schema_version` `"1"`) | [gate-failure-1.golden.json](gate-failure-1.golden.json) | Findings yes; timestamp/agent on receipt side |
| `curbpack-evaluation:1` | [curbpack-evaluation-1.golden.json](curbpack-evaluation-1.golden.json) | Yes |
| `curbpack-run-receipt:1` | [curbpack-run-receipt-1.golden.json](curbpack-run-receipt-1.golden.json) | Receipt timestamps may vary; `evaluation_digest` binds the evaluation |
| Explain-packet (`schema_version` `"1"`) | [explain-packet-1.golden.json](explain-packet-1.golden.json) | Airlocked text; readiness kept for machines |
| ContextPack (`schema_version` `"1"`) | [context-pack-1.golden.json](context-pack-1.golden.json) | Washed assistant snapshot |
| `curbpack-review-report:2` | [review-report-2.golden.json](review-report-2.golden.json) | Document triage only |
| `curbpack-source-register:1` | [curbpack-source-register-1.golden.json](curbpack-source-register-1.golden.json) | Illustrative forward shape |
| `curbpack-external-evidence:1` | [curbpack-external-evidence-1.golden.json](curbpack-external-evidence-1.golden.json) | Illustrative forward shape |

## Rules

1. **Additive fields** — unknown fields MUST be ignored by readers and preserved
   by any component that round-trips the document (MUST-63).
2. **Historical digests** — `readiness_score` and other pre-count fields remain
   readable. New emissions also carry `failed_rules` / `evaluated_rules` /
   `skipped_rules` and `conformity_claim: "none"`. Result digests that historically
   omitted these fields stay readable; tip evaluation digests include the claim.
3. **Breaking changes** — rename or semantic change of a required field requires
   a new `schema_version` major (MUST-62) plus a CHANGELOG entry and golden.
4. **`conformity_claim`** — tip value is always `"none"`. Absence on historical
   documents means the same: no conformity assessment.
5. **Trends** — compare tallies only across compatible `pack_id` (and matching
   schema when both present). Do not invent percent grades from digests.
6. **Human surfaces** — terminal, one-pager, action report, ask, and demo show
   failed/evaluated/skipped counts. They must not present readiness as a percent
   grade or thermometer. JSON may still include `readiness_score` for fingerprint
   and historical compatibility.

Not certification. Not a notified-body decision.
