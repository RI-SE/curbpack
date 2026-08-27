# Shared Frame v1 — Annexes

Companion to [`shared-frame.md`](shared-frame.md). Pinned to `RI-SE/curbpack@a36aeef`, method 1.3.0 · `refclass:2`, 27 Aug 2026.

**These are annexes on purpose.** Onboarding teaches the seam. Law, research framing, and backlog are looked up when needed, not read on day one.

---

# Annex A — Legal basis

> ⚠️ **Re-verify before any external use.** Every quotation below was taken verbatim from the authenticated English CELEX text earlier in this programme. **Re-fetch and diff against CELEX before publishing, quoting in a paper, or putting any of it in front of a customer.** Article numbering and applicability dates are the two things that move.
>
> ⚠️ **Never paraphrase inside quotation marks.** A reworded quotation of primary law is a worse error than the one any style rule prevents. In particular, NIS 2 says *"cybersecurity risk-management **measures**"* — that stands, verbatim, and the nomenclature fence special-cases it (`NOMEN_DENY_RE` denies `measurement`/`measurand`, never the stem `measur`).

## A.1 The manufacturer — documentation must stay current

**Regulation (EU) 2024/2847 (CRA), Article 31(2):**

> *"The technical documentation … shall be continuously updated, where appropriate, at least during the support period."*

**Article 13(13):**

> *"Manufacturers shall keep the technical documentation and the EU declaration of conformity at the disposal of the market surveillance authorities for at least 10 years after the product with digital elements has been placed on the market or for the support period, whichever is longer."*

**Article 13(8):** *"the support period shall be at least five years"*.

**Article 28(4):**

> *"By drawing up the EU declaration of conformity, the manufacturer shall assume responsibility for the compliance of the product with digital elements."*

**Why this is the anchor.** *"Continuously updated"* is the one CRA obligation a git-native tool is structurally better at than any document management system: ten years of retention, a weekly release cadence, and a manufacturer who has personally assumed responsibility.

## A.2 The release manager — the substantial-modification question

**Article 3(30):**

> *"'substantial modification' means a change to the product with digital elements following its placing on the market, which affects the compliance of the product with digital elements with the essential cybersecurity requirements set out in Part I of Annex I or which results in a modification to the intended purpose for which the product with digital elements has been assessed"*

**Recital 41:**

> *"where a substantial modification occurs that may affect the compliance of a product with digital elements with this Regulation or when the intended purpose of that product changes, it is appropriate that the compliance of the product with digital elements is verified and that, where applicable, it undergoes a new conformity assessment. Where applicable, if the manufacturer undertakes a conformity assessment involving a third party, a change that might lead to a substantial modification should be notified to the third party."*

**Article 69(2):**

> *"Products with digital elements that have been placed on the market before 11 December 2027 shall be subject to the requirements set out in this Regulation only if, from that date, those products are subject to a substantial modification."*

**Why this needs the link set.** Answering Art 3(30) requires knowing which documented claims point at which files, and which of those changed since the last assessed state. `--since` already produces NEW / CLEARED / PERSISTING grouped per document; accepted mappings extend that to claims the nine kinds cannot see.

**The product sentence — note the middle clause:**

> *Since your last attested state, 6 claims in the technical documentation resolve into files that have changed. Art 3(30) asks whether those changes affect the essential requirements or the intended purpose. **That determination is yours.** Here are the six.*

The tool narrows the question and hands it back. It never answers it.

## A.3 The board and the CISO — a personal, non-delegable duty

**Directive (EU) 2022/2555 (NIS 2), Article 20(1):**

> *"Member States shall ensure that the management bodies of essential and important entities approve the cybersecurity risk-management measures taken by those entities in order to comply with Article 21, oversee its implementation and can be held liable for infringements by the entities of that Article."*

**Article 20(2):**

> *"Member States shall ensure that the members of the management bodies of essential and important entities are required to follow training, and shall encourage essential and important entities to offer similar training to their employees on a regular basis, in order that they gain sufficient knowledge and skills to enable them to identify risks and assess cybersecurity risk-management practices and their impact on the services provided by the entity."*

**Why this is the buying use case.** *"Can be held liable"* attaches to named individuals. A board that approves a measure must later be able to say what it approved and on what basis. A re-derivable record — dated, digest-pinned, produced by a published method — is the cheapest defensible answer that exists, and it falls out of a check the engineering team was running anyway.

## A.4 Medical devices — the same question, future tense

**Regulation (EU) 2017/745 (MDR), Annex IV, point 8** (EU declaration of conformity contents):

> *"Where applicable, the name and identification number of the notified body, a description of the conformity assessment procedure performed and identification of the certificate or certificates issued;"*

**Annex VII, Section 1.2.3(c)** (requirements to be met by notified bodies):

> *"engage in any activity that may conflict with their independence of judgement or integrity in relation to conformity assessment activities for which they are designated;"*

**Annex IX, Section 4.10:**

> *"Changes to the approved device shall require approval from the notified body which issued the EU technical documentation assessment certificate where such changes could affect the safety and performance of the device or the conditions prescribed for use of the device. Where the manufacturer plans to introduce any of the above-mentioned changes it shall inform the notified body …"*

**Annex X, Section 5.1:**

> *"The applicant shall inform the notified body which issued the EU type-examination certificate of any planned change to the approved type or of its intended purpose and conditions of use."*

**Why this is the hardest case.** *"Plans to introduce"* and *"any planned change"* are **prospective** — under MDR you raise your hand before you ship; under the CRA you assess after. A medtech company running both regimes over one codebase is answering two differently-tensed questions about the same commit. No human keeps that straight at a weekly cadence, which is why the screening question has to be automatic. Annex IV(8) is the void-DoC thought experiment for false green: a structural file that *names* a procedure does not settle *"a description of the conformity assessment procedure performed"*.

## A.5 The assessor — why reproducibility is a legal requirement

**CRA Article 39(6)(b)**, a designation requirement for every notified body:

> *"At all times and for each conformity assessment procedure … a conformity assessment body shall have at its disposal the necessary: … (b) descriptions of procedures in accordance with which conformity assessment is to be carried out, ensuring the transparency of and ability to reproduce those procedures."*

**Article 39(7)(d)**, on assessment personnel:

> *"the ability to draw up certificates, records and reports demonstrating that assessments have been carried out"*

**Article 71(2)**, the clock:

> *"This Regulation shall apply from 11 December 2027. However, Article 14 shall apply from 11 September 2026 and Chapter IV (Articles 35 to 51) shall apply from 11 June 2026."*

**Why it matters here.** *Transparency of and ability to reproduce those procedures* is the exact property the deterministic engine has — the same word for the same thing, supplied in **executable** rather than **described** form. Art 39(7)(d) is why the review record exists as a first-class artifact rather than as console output.

**The caveat that must travel with the claim.** As of **26 June 2026** there were **zero CRA notified bodies designated** (NANDO) and no CRA harmonised standards cited in the OJ. This is a real statutory hook aimed at a cohort that does not yet exist — which is why sequencing is *suppliers now, assessors as they are designated*, and why nobody should build for the assessor first. **Recheck NANDO before any external use of this line.**

## A.6 The boundary shared by every use case

Curbpack never claims compliance, conformity, or certification — and neither does the Mapper. It reports structure; a human decides what the structure means. `scripts/claim-safety.sh` enforces the wording in CI. **The Mapper's export must survive the same check.**

---

# Annex B — Research brief

## B.1 The framing that is worth putting in the paper

Trace-link recovery is a well-explored field, and the established literature **recovers links probabilistically**. Curbpack does the opposite: deterministic, no score, an edge exists only because the target was found. The Mapper is the probabilistic half, with a human as the gate.

**The combination is what is new, not either half.**

## B.2 What the sub-studies then target

| | Targets |
|---|---|
| **RQ1** — retrieval + optional local AI | How much human effort the probabilistic half removes on first pass |
| **RQ2a** — mechanical reuse of a prior review | How much of that removal survives unchanged code |
| **RQ2b** — change flagging | How much survives *changed* code |

**RQ2a/RQ2b are the contribution nobody else is positioned to make**, because measuring survival across change requires a deterministic partner that can say what changed without guessing. Lead with that, not with retrieval quality.

## B.3 Two design notes that affect the study

- **Pilot scope is not generalisation.** Until decision 0a lands, `cra-baseline` is inside the hard-coded `HOUSE|CRA|MEDTECH` namespace and a clean pilot result says nothing about a fourth vertical. State this as a limitation or resolve 0a first.
- **Freshness has two engine axes, not one.** `classifier_version` hard-invalidates an accepted link; `method_version` does not. A study that treats "the tool changed" as one event will attribute reuse loss to the wrong cause.

## B.4 Prioritisation

MVP against the packs that exist. Correct as written in v8 — keep it.

---

# Annex C — Engineering backlog

Demoted from the v8 review. **Aslak's side unless marked otherwise. None of it blocks Daniel's first item.**

| # | Item | Severity | Cost |
|---|---|---|---|
| C1 | **Contract gaps in `docs/stable-contracts.md`.** `reference:claim:<rule-id>` is emitted at `review.go:675` but missing from the `Finding.ID` shapes row (`:105`) — and it is exactly the shape the join needs. `subject_commit` / `subject_state_hash` are emitted on every record and appear nowhere in the table, while `subject_commit` *is* the export's `repository.commit` | **High** — an uncontracted field an external consumer depends on can be renamed by someone acting in good faith | minutes |
| C2 | **Stale method cross-links.** The Method row (`:100`) and the See-also line (`:112`) point at `review-method-1.1.1.md` while code is 1.2.0. `TestMethodVersionMatchesClassifier` guards the method document's existence and content, not the cross-links — a small blind spot in an otherwise well-defended file | Low | minutes |
| C3 | **Claim-id namespace ceiling** (`review.go:141`). See Shared Frame §8 decision 0a. **Highest severity because it is silent**, and a `refclass` bump gets more expensive with every accepted mapping in the field | **High** | ~1 day after 0a |
| C4 | **Silent rule override in `Compose`.** Later packs win on rule id (`byRule[r.ID] = r`) with nothing recording that an override happened. Half-addressed — `context-pack.json` carries `pack_versions`, so the *set* of packs is visible; **per-rule provenance (`rule_id → delivering pack@version`) is still missing.** Raised by Daniel in an earlier round and correct then | Medium — the third thing the freshness axis would like and does not have | ~1 day |
| C5 | **`edges` writer-adapter**, both sides. Blocks on 0b. **This is the reservation clock** — the field is deleted at product release v0.6.0 if unused (`docs/internal/edges-reservation-expiry.md`) | The only hard deadline | — |
| C6 | **HPURL formatter.** `ParseHPURLFragment` exists (`attest.go:223`); there is no formatter. Not blocking anything today | Low | ~hours |

---

# Ledger

| Claim | Status |
|---|---|
| Main `a36aeef`, method `1.3.0`, classifier `refclass:2` | **VERIFIED** — RI-SE #31 merge, 27 Aug 2026 |
| Prior pin `eac1ab3` / method `1.2.0` / `refclass:1` | **SUPERSEDED** — hard-invalidate Mapper links on classifier bump |
| `4a519d7` not reachable on `RI-SE/curbpack` at depth 50 | **VERIFIED, scoped** — may exist fork-locally; unverifiable from here |
| `Answered`/`Evidence`/`VerifiedAt` shipped; `AnswersSuppressed` forced when `SkippedRules > 0` | **VERIFIED** — `buyer_questions.go:25–27, 63, 89–95, 166` |
| `SubjectCommit` / `SubjectStateHash` shipped | **VERIFIED** — `review.go:109–112`; method 1.2.0 §2 |
| `reClaimID` hard-codes `HOUSE\|CRA\|MEDTECH`; non-matching prefixes yield no finding and no dropped entry | **VERIFIED** — `review.go:141, 670`; `references.go:36` |
| `reference:claim` absent from the shapes row; `subject_*` absent from the table; Method links stale at 1.1.1 | **VERIFIED** — `docs/stable-contracts.md:100, 105, 112` |
| `reference:claim` findings carry `StateConfirmed` | **VERIFIED** — `review.go:679–683` |
| `edges` reserved, expires at product release v0.6.0 | **VERIFIED** — `docs/internal/edges-reservation-expiry.md` |
| Nine check kinds, no domain branches | **VERIFIED** — `internal/packs/packs.go:22` |
| CRA, NIS 2, MDR quotations as given | **VERIFIED verbatim** against authenticated English CELEX earlier in this programme. **Not re-fetched today** — CELEX fetch was unavailable in this session. Re-verify before external use |
| Zero CRA notified bodies designated; no CRA harmonised standards cited in the OJ | **VERIFIED as of 26 Jun 2026** (NANDO). Recheck before any external use |
| Option B (pack-derived claim ids) better than Option A | **REASONED, NOT TESTED — OPEN DECISION.** Do not implement as chosen |
| That accepted mappings measurably reduce human effort | **UNVERIFIED — that is what RQ1 is for** |

*Structural evidence for human review. Not conformity assessment. Not CE marking. Not a notified-body opinion.*
