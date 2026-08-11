# Glossary and audience

**Local pack gates. Humans review. Not conformity assessment.**

Canonical abbreviations and “who reads what.” Expand each term on first use in new prose; this page is the shared dictionary. Public sentence voice and preferred terms: [voice and terms](voice-and-terms.md).

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
| **Gate** / **check** | A deterministic rule-pack evaluation. Exit `0` = gates passed on this tree for human review — **not** certification. |
| **Rule pack** / **pack** | JSON rule set (house-policy by default; CRA-shaped annex drafts or sector templates when opted in). Data, not hard-coded industry law. |
| **Review pack** | Folder of evidence for human review from `prepare-release` (JSON, markdown, optional buyer one-pager). |
| **Buyer one-pager** | Supplier evidence summary HTML — local gate score on this tree, not a certificate. |
| **Warm-start** / **pathway** | Optional interview that suggests checklists (`cyberready pathway`); seeds packs + human ticks — not a gate input. |
| **Research brief** | Allowlisted human brief from `cyberready research` — informational; never check pass/fail. |
| **Cite-check** | `cyberready research --cite-check <draft.md>` — refuses uncited Claims before `confirm-prose`. |
| **Three ways in** | Write→Check, Bring-docs→Check, or CI — same local `check`. |
| **Write→Check** | Way in: draft house docs (optional pathway), then check. |
| **Bring-docs→Check** | Way in: place existing policies on pack paths, then check (no portal PDF ingest). |
| **Dual-draft** | Always propose Option A and Option B plus **Recommended: A\|B** (≤3 reasons); human picks. |
| **Structural evidence** | Documentation and dependency checks produced locally for human judgment. |
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

| Audience | First sentence | Start here | Then | Skip by default |
|----------|----------------|------------|------|-----------------|
| **Builder** (product engineer) | Install, init, and check—green gates in your repo in under ten minutes. | [60-second paths](getting-started/60-second-paths.md) · [pathway](getting-started/pathway.md) · [site builders](../site/for-builders/) | [Daily loop](getting-started/daily-loop.md) · README commands | Integrator sock protocol |
| **Buyer / reviewer** | Ask the supplier for a buyer one-pager and, if needed, the review pack—then use the trust table. | [Buyer evidence](getting-started/buyer-evidence.md) · [for-reviewers](../site/for-reviewers/) | Sample [one-pager](../site/samples/onepager.html) | Pack authoring, sock bridge |
| **CISO** | CyberReady prepares structural evidence for human review; it does not perform conformity assessment. | [for-authorities](for-authorities.md) · [Intent vs Scope](intent-vs-scope.md) | [Security model](security-model.md) · [strategy boundary](strategy-boundary.md) | [coreward-bridge](coreward-bridge.md) |
| **Authority / auditor** (NCSC/EU-style, internal audit) | CyberReady prepares structural evidence for human review; it does not perform conformity assessment. | [for-authorities](for-authorities.md) · [site Authorities](../site/for-authorities/) | [Promotion firewall](promotion-firewall.md) · white paper | Coreward bridge, GTM folders |
| **Integrator / tutor author** | Optional socket and explain-packets for integrators—CyberReady stays self-sustaining without them. | [Stable contracts](stable-contracts.md) · [coreward-bridge](coreward-bridge.md) | [coreward-pointer](coreward-pointer.md) (aside wording) | Buyer one-pager as “certificate” |

Non-technical readers: stay on [for-authorities](for-authorities.md) and the [site home](../site/) — those pages expand terms and avoid integrator jargon.

See also: [Voice and terms](voice-and-terms.md) · [Docs index](README.md) · [Intent vs Scope](intent-vs-scope.md) · [for-authorities](for-authorities.md)
