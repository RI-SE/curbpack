# Intent vs Scope

**Local pack gates. Humans review. Not conformity assessment.**

Sixty-second clarity for buyers, auditors, and agents. Gate pass is **evidence for human review** — not conformity assessment, CE marking, or certification.

Authorities / CISO path: [for-authorities](for-authorities.md). Abbreviations: [glossary](glossary-and-audience.md).

| Column | Content |
|--------|---------|
| **Intent (why)** | SMEs and suppliers need continuous, local, shareable *evidence* for buyers, auditors, and agents — without GRC SaaS or uploading IP to a cloud policy brain. |
| **CyberReady+ scope (now)** | Pack JSON gates, `check` / `heal`, review-pack, CycloneDX / OpenVEX drafts, Git Notes attest, HPURL pointer, Action + SARIF, optional sock `validate_delta`, local regulation knowledge graph export, explain-packets for tutors, `export --lay-of-land` / `instrument.json` instrument map. |
| **Not in scope (OSS)** | Conformity assessment, CE, OPA/Rego, LSP, syscall tracers, FIDO/EFOS, DNSSEC, cloud policy brain, LLM-as-judge, badge marketplace, gtm-oss on site, second pin, pack catalog growth before partner habit proof. |
| **Pack catalog freeze** | Only `house-policy`, `cra-baseline`, `medtech-iec62304` (ids). Enforced by `scripts/redteam-pilot.sh` allowlist; unlock only via freeze review + explicit PR (no CI env escape hatch). |
| **v3.33 spec** | Internal R&D / EE north star only — **not mirrored** into OSS; not the adoption contract. |
| **IP / chat boundary** | Raw source and secrets never leave the machine for “compliance chat.” Only sanitized GateFailure / RKG explain-packets may leave for an optional tutor the operator explicitly chooses. |
| **Promotion bar** | `./scripts/redteam-pilot.sh` green. |

## Deterministic judge (main flow)

```
repo → CyberReady (gates, packs, RKG, attest)
         ↓
   review-pack / exports (evidence for humans)
         ↓
   human judgment (attest when ready)
```

CyberReady decides pass/fail. Optional chat tutors (any local or operator-chosen assistant) may draft prose from an airlocked explain-packet — they never greenlight gates and never write attest capsules. After any proposed fix you must re-check (`validate_delta` / `cyberready check`). Recorded loop: [`scripts/dogfood-explain-recheck.sh`](../scripts/dogfood-explain-recheck.sh).

## Agentic coding: instrument panel / not AI security product

Agents and humans share one loop: edit → `cyberready check` → read the instrument panel (covenant + optional Δ readiness/deps/secret-hits) → on red heal/ask; on green optional `--lay-of-land` / `--buyer-questions` for humans. This is **not** an AI security product, SCA/CVE platform, or certification engine. Hooks keep agent PRs honest; tutors still require re-`validate_delta` / re-check before any “fixed” claim.

### Compose with SCA / secret scanners

CyberReady is an **instrument panel / evidence habit** for product repos. Pair it with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth. Explicitly: **not** a security program; watchlist∩SBOM is look-here only — not a CVE product.

**Activate in 60s:** [getting-started / 60-second paths](getting-started/60-second-paths.md).

See also: [For authorities](for-authorities.md) · [Strategy boundary](strategy-boundary.md) · [Stable contracts](stable-contracts.md) · [Promotion firewall](promotion-firewall.md) · [Write your own pack](write-your-own-pack.md) · [Security model](security-model.md)

---

> **Optional, separate product:** Coreward is a private tutor/enforce client that may consume CyberReady explain-packets over an optional Unix socket. CyberReady is fully self-sustaining without it — adopters do not need Coreward. Brief architecture note (public Pages, not the private repo): https://afelin.github.io/coreward/
