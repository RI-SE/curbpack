# Art 14 reporting vs handling clocks

Counsel note for adopters who opt into `cra-baseline`. Structural file gate only — not a live Single Reporting Platform check and not a legal opinion. Not conformity assessment. Not CE marking. Not a notified-body opinion.

Curbpack does not certify Cyber Resilience Act (CRA), NIS2, or AI Act conformity. Humans retain judgment.

## CRA Article 14 reporting ≠ vulnerability handling

| Clock | What it is | What Curbpack gates (opt-in `cra-baseline` only) |
|-------|------------|--------------------------------------------------|
| **Art 14 reporting** (from **11 September 2026**, including products already on the market) | How actively exploited or severe incidents would be reported | In-repo dated rehearsal file `docs/incident/art14-path.md` (headers + anti-placeholder + repo-bound product mention). A **file**, not a live SRP submission. Does **not** gate “EU Login works.” |
| **Vulnerability handling / public SPOC** | Coordinated disclosure and public security contact | **Later clock** than Art 14 reporting. Not this file. House-policy still asks for `SECURITY.md` / `security.txt` as structural docs. |

Official CRA text: [CELEX 32024R2847](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847) (allowlisted). Do not invent article wording from this note.

`--heal` may write a scaffold for the Art 14 path. Scaffold overlap stays **red** until product-specific prose replaces the stub.

## AI Act Article 50 grace is not blanket

AI Act Art 50 transparency obligations apply **2 August 2026**. Marking grace through **2 December 2026** is **only** for systems **already on the market before 2 August 2026** — not a blanket delay for every system. See [Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/) (Digital Omnibus; allowlisted). Never claim the product is CRA-compliant or AI Act–compliant because a Curbpack gate is green.

Pack catalog stays frozen: `house-policy` (default), `cra-baseline` (opt-in), `medtech-iec62304`. No new pack ids. Pin Action / examples at **`@v0.5.2`**.
