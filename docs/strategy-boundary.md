# Strategy boundary (public vs private)

**Local pack gates. Humans review. Not conformity assessment.**

One page so strangers cannot confuse public CyberReady with private Coreward, CE, or a security program.

| In CyberReady (public) | In Coreward (private) | Never as product claim |
|------------------------|------------------------|-------------------------|
| Packs, `check`, IR, SARIF, buyer-questions, lay-of-land, attest honesty, Action, sock **server** | Mandate/KYA/TSS, hosted verify, paid vertical packs, enforce-before-execute | CE, NIS2-compliant, RISE-certified, Conformant |

## Public CyberReady

- Deterministic local **judge** + instrument panel + fail-open sock server.
- Evidence habit for product repos — not CVE management, not a security program.
- Pin stays `@v0.4.3` unless a contract-breaking change forces a later patch.
- Pack catalog frozen to three ids until freeze review + partner habit proof unlock.

## Private Coreward (documented only here)

- Optional tutor / enforce **client** that must **re-check** gates.
- Never greenlights from explain-packets or sock responses alone.
- Monetization (hosted verify, paid packs, KYA/mandate) stays **out** of this repo.

## Explicit non-goals for OSS PRs

PRs that add OPA/Rego, LSP, syscall tracers, FIDO defaults, or new pack ids without freeze unlock will be **rejected**. See [CONTRIBUTING](../CONTRIBUTING.md).

**v3.33** = internal R&D / EE north star only — **not mirrored** into the public adoption roadmap. Do not port v3.33 EE surfaces into OSS PRs.

## Compose, do not conquer

Pair CyberReady with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth. Watchlist∩SBOM is look-here only — not a vulnerability product.

See also: [Intent vs Scope](intent-vs-scope.md) · [Stable contracts](stable-contracts.md) · [Coreward bridge](coreward-bridge.md) · [Security model](security-model.md)

---

Coreward integration work is planned separately; this repo only freezes the public contracts.
