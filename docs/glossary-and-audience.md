# Glossary and audience

**Local pack gates. Humans review. Not conformity assessment.**

Canonical abbreviations and “who reads what.” Expand each term on first use in new prose; this page is the shared dictionary.

## Glossary

| Term | Expansion / meaning |
|------|---------------------|
| **CE** | *Conformité Européenne* marking — legal market-access marking for covered products. CyberReady does **not** issue CE marks or complete CE procedures. |
| **CRA** | EU Cyber Resilience Act — regulatory context that shapes some pack drafts (`cra-baseline`). Pack green is structural evidence for humans, not CRA legal conformity. |
| **SBOM** | Software Bill of Materials — inventory of components (e.g. CycloneDX). CyberReady may emit best-effort SBOM drafts from lockfiles. |
| **SARIF** | Static Analysis Results Interchange Format — machine findings for IDEs/CI (GitHub code scanning). Gate `ruleId` equals `gate_id`. |
| **GRC** | Governance, Risk, and Compliance — typically SaaS platforms. CyberReady is local-first evidence, not a GRC suite. |
| **HPURL** | Hash Pointer URL — local `state_hash` fragment for client-side compare; not a remote notary or certificate. |
| **RKG** | Regulation Knowledge Graph — local export (`packs export-graph` → `policy-graph.json`) for teaching/navigation; not a legal oracle. |
| **IR** | Intermediate Representation — here, structured `GateFailure` JSON (+ markdown twin). |
| **ReDoS** | Regular Expression Denial of Service — pack regexes are length-capped and time-bounded. |
| **OPA** | Open Policy Agent — Rego policy engine. Explicit **non-goal** for CyberReady OSS. |
| **VEX** | Vulnerability Exploitability eXchange — draft OpenVEX may bind pending findings at attest time; not a CVE product. |
| **CLI** | Command-Line Interface — CyberReady’s primary surface (`cyberready`). |
| **IPC** | Inter-Process Communication — optional Unix-domain socket (`cyberready sock`) for integrators. |
| **OSS** | Open-Source Software — this public Apache-2.0 product line. |
| **CI** | Continuous Integration — e.g. GitHub Actions pin `@v0.4.3`. |
| **SCA** | Software Composition Analysis — pair CyberReady with tools such as Trivy/OSV for depth; CyberReady is not an SCA platform. |
| **CVE** | Common Vulnerabilities and Exposures — watchlist∩SBOM is look-here only, not CVE management. |
| **Gate** | A deterministic pack rule evaluation. Exit `0` = gates green for human review — **not** certification. |
| **Pack** | JSON rule set (house policy, CRA-shaped annex drafts, sector templates). Data, not hard-coded industry law. |
| **Review pack** | Folder of evidence artifacts from `prepare-release` (JSON, markdown, optional one-pager). |
| **Attest** | Human-driven binding of a state hash into Git Notes. Unsigned ≠ cryptographically verified. |
| **Explain-packet** | Sanitized teaching surface for optional tutors; never greenlights gates. |
| **Notified body** | Independent organization designated for certain conformity assessment tasks under EU product rules. CyberReady does **not** replace a notified body. |
| **Conformity assessment** | Formal process to show a product meets legal requirements. CyberReady prepares structural evidence for humans — it does **not** perform conformity assessment. |
| **Assurance class** | Pack metadata (e.g. `structural_draft`) stating how strong a claim the pack may imply. Import refuses claim-adjacent theater. |
| **Air-gap** | Offline operation: embedded packs + `packs import`; no network policy brain required. |
| **Fail-open (sock)** | If the optional socket client is absent, CyberReady continues; tutors must not block promote solely on missing sock. |
| **RISE** | Research Institutes of Sweden — development supporter / funder acknowledgment in [`NOTICE`](../NOTICE). **Funder, not certifier** — see [promotion firewall](promotion-firewall.md). |
| **NCSC / FRA** | National cybersecurity authorities (examples: UK NCSC; Sweden FRA in awareness contexts). Awareness links only — never “agency-approved” product claims. |
| **Coreward** | Optional separate private product. Adopters do not need it. Wording: [coreward-pointer.md](coreward-pointer.md). |

## Who should read what

| Audience | Start here | Then | Skip by default |
|----------|------------|------|-----------------|
| **Builder** (product engineer) | [60-second paths](getting-started/60-second-paths.md) · [site builders](../site/for-builders/) | [Daily loop](getting-started/daily-loop.md) · README commands | Integrator sock protocol |
| **Buyer / reviewer** | [Buyer evidence](getting-started/buyer-evidence.md) · [for-reviewers](../site/for-reviewers/) | Sample [one-pager](../site/samples/onepager.html) | Pack authoring, sock bridge |
| **CISO** | [for-authorities](for-authorities.md) · [Intent vs Scope](intent-vs-scope.md) | [Security model](security-model.md) · [strategy boundary](strategy-boundary.md) | [coreward-bridge](coreward-bridge.md) |
| **Authority / auditor** (NCSC/EU-style, internal audit) | [for-authorities](for-authorities.md) · [site Authorities](../site/for-authorities/) | [Promotion firewall](promotion-firewall.md) · white paper | Coreward bridge, GTM folders |
| **Integrator / tutor author** | [Stable contracts](stable-contracts.md) · [coreward-bridge](coreward-bridge.md) | [coreward-pointer](coreward-pointer.md) (aside wording) | Buyer one-pager as “certificate” |

Non-technical readers: stay on [for-authorities](for-authorities.md) and the [site home](../site/) — those pages expand terms and avoid integrator jargon.

See also: [Docs index](README.md) · [Intent vs Scope](intent-vs-scope.md) · [for-authorities](for-authorities.md)
