# Curbpack ContextPack

> Structural evidence for human review. Not a conformity assessment, CE mark, or certification.

- **Packs:** house-policy
- **Readiness:** 40%
- **OK:** false
- **Certification claimed:** no
- **Agent identity:** `self-declared` (not_installed) — lineage label, not attestation

## Pathway

- **Phase:** `Root / Pathway / AwaitSuggest`
- **Next:** suggest packs
- **Run:** `curbpack pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes`
- **Note:** enum seed only — see docs/getting-started/pathway.md

_Agents: prefer this section over spelunking pathway-seed.json. Stop at human confirms/attest._

## Instrument

- deps: 0 (fp `e3b0c44298fc1c14`)
- secret-hits: 0

## Top failures

| gate_id | severity | description | target_file |
|---|---|---|---|
| HOUSE-DEP-AXIOS-PIN | critical | House policy bans vulnerable axios@1.6.0 pins in package.json. (target absent) | package.json |
| HOUSE-ANTI-PLACEHOLDER | high | House policy docs contain placeholder / boilerplate text. (scaffold body overlap) | SECURITY.md |
| HOUSE-ANTI-PLACEHOLDER | high | House policy docs contain placeholder / boilerplate text. (scaffold body overlap) | .well-known/security.txt |

## Paths

- `buyer_questions`: `.github/curbpack/cache/buyer-questions.md`
- `context_pack`: `.github/curbpack/cache/context-pack.json`
- `context_pack_md`: `.github/curbpack/cache/context-pack.md`
- `explain_packet`: `.github/curbpack/cache/explain-packet.json`
- `instrument`: `.github/curbpack/cache/instrument.json`
- `latest_failure`: `.github/curbpack/cache/latest_failure.json`
- `pathway_seed`: `.github/curbpack/cache/pathway-seed.json`
- `pathway_status_hint`: `curbpack pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes`
- `policy_graph`: `.github/curbpack/graph/policy-graph.json`
- `remediations`: `.github/curbpack/cache/remediations.json`
- `research_brief`: `.github/curbpack/cache/research-brief.md`
- `research_packet`: `.github/curbpack/cache/research-packet.json`
- `research_packet_present`: `false`

_Assistants: run `curbpack check` (exit code authoritative). Never invent gate results or certification claims._
