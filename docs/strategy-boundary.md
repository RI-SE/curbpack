# Strategy boundary

**Local pack gates. Humans review. Not conformity assessment.**

CyberReady is a **standalone** public OSS product. Strangers must be able to adopt it without any private sibling tool. This page keeps claim boundaries honest.

| In CyberReady (public, enough to adopt) | Never as product claim |
|-----------------------------------------|-------------------------|
| Packs, `check`, IR, SARIF, buyer-questions, lay-of-land, attest honesty, Action, optional sock **server** | Never claim CE, NIS2-compliant, RISE-certified, agency-endorsed, or Conformant |

## Public CyberReady (self-sustaining)

- Deterministic local **judge** + instrument panel + fail-open optional sock server.
- Evidence habit for product repos — not CVE management, not a security program.
- Pin stays `@v0.4.3` unless a contract-breaking change forces a later patch.
- Pack catalog frozen to three ids until freeze review + partner habit proof unlock.
- Authorities / CISO brief: [for-authorities](for-authorities.md). Glossary: [glossary-and-audience](glossary-and-audience.md).

## Explicit non-goals for OSS PRs

PRs that add OPA/Rego, LSP, syscall tracers, FIDO defaults, or new pack ids without freeze unlock will be **rejected**. See [CONTRIBUTING](../CONTRIBUTING.md).

**v3.33** = internal R&D / EE north star only — **not mirrored** into the public adoption roadmap. Do not port v3.33 EE surfaces into OSS PRs.

## Compose, do not conquer

Pair CyberReady with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth. Watchlist∩SBOM is look-here only — not a vulnerability product.

Stakeholder demand vs stack evidence (Done / Polish / Ops / Reject): [GitHub-readiness gap matrix](github-readiness-gaps.md).

See also: [Intent vs Scope](intent-vs-scope.md) · [Stable contracts](stable-contracts.md) · [Security model](security-model.md) · [Launch readiness](launch-readiness.md) · [Coreward pointer](coreward-pointer.md)

---

> **Optional, separate product:** Coreward is a private tutor/enforce client that may consume CyberReady explain-packets over an optional Unix socket. CyberReady is fully self-sustaining without it — adopters do not need Coreward. Brief architecture note (public Pages, not the private repo): https://afelin.github.io/coreward/
