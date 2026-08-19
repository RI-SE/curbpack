# Claim discipline

**Core principle:** *An artifact must never assert something the tool itself caused.*

Curbpack prepares structural evidence for human review. Every user-visible string—CLI output, gate copy, badge line, attest capsule label, HTML meta tag, or social card—must distinguish what the tool wrote or inferred from what a human did or verified. If the tool scaffolded a file, filled a date stamp, or ran a structural check, the UI must not imply rehearsal, cryptographic verification, regulatory readiness, or market access. Gate green means **documented** (a required artifact exists with expected headers); it does not mean **rehearsed**, **verified**, or **compliant**. When in doubt, refuse the stronger claim and point to the repo artifact a third party can re-run.

## Worked examples (stack)

| Surface | Tool may say | Tool must not say (without human step) |
|---------|--------------|----------------------------------------|
| **Attest capsule** | `CryptoVerified` → display **ssh-agent-signed** (or **UNSIGNED — not cryptographically verified**) from `ssh-keygen -Y verify` at bind resolution | “Verified compliant”, “signed attestation”, or any line that treats `user_touch` alone as proof |
| **Badge** (`curbpack scan --badge`) | Read **`Last tabletop:`** only; emit `not rehearsed` until a human fills that field | Treat **`Drafted:`** (written by `fix --art14`) as rehearsal; **`fix --art14` alone** must still badge `not rehearsed` |
| **Art 14 template** (`fix --art14`) | **`Drafted: YYYY-MM-DD`** — tool date stamp on scaffold | **`Last tabletop:`** with a date — human fills after tabletop |
| **Gate copy** (cra-baseline Art 14 gate) | Documented draft present; structural headers + product mention | **Rehearsed** — only after human **`Last tabletop:`** date |
| **Meta / OG** (Pages) | Fixed calendar date in `<title>`, `og:title`, `og:description`, `<meta description>` (e.g. **11 September 2026**) | Day count in title/OG/meta — countdown belongs in HTML body only (`#art14-countdown`), refreshed by cron/workflow |

## Process rules

1. **Literal third-party-readable output before implementation** — paste the exact CLI line, badge string, gate message, or HTML snippet a stranger would see; implement only after the wording is claim-safe.
2. **Never day count in title / OG / meta description** — social cards and search snippets are cached and do not run JS; see [site README metadata rule](../site/README.md).
3. **Re-check after every copy change** — run [`scripts/claim-safety.sh`](../scripts/claim-safety.sh) (docs + runtime CLI captures).
4. **Public language** — align with [voice and terms](voice-and-terms.md); deny-list blocks certification theater.

See also: [launch readiness](launch-readiness.md) · [promotion firewall](promotion-firewall.md) · [security model](security-model.md)
