# Shared Frame v1 — curbpack ⇄ Claim-to-Artifact Mapper

Drop-in for `docs/shared-frame.md`. Written read-only; nothing was applied to any repository.

> **Pin.** Source of record is `RI-SE/curbpack@a36aeef` · review method **1.3.0** · classifier **`refclass:2`** · 27 Aug 2026.
> **Not** any PDF, including v8. The concept document is *intent*; this tree is *record*. When they disagree, the tree wins.
>
> *Pinned to RI-SE merge of the v6 reference-integrity train (`a36aeef`). Treat any fork-local sha as unverifiable by the other party.*
>
> **Mapper hard-invalidate:** a `classifier_version` bump (including `refclass:1` → `refclass:2`) **invalidates** previously accepted links. Soft-note only on `method_version`. `reference:claim:<id>` confirmed means the claim id string is present — **not** that the requirement is met.

**Who this is for.** Both builders, before either writes an adapter. Two to three pages by design — everything demoted from the review lives in [the annexes](shared-frame-annexes.md) as legal basis, research brief, and engineering backlog.

---

## 1. What we are building

A manufacturer's technical documentation makes claims about a codebase. The codebase changes weekly; the documentation does not. Every regulated release therefore starts with the same expensive human act — someone re-establishes which sentence still corresponds to which file — and it is redone from scratch next quarter because nothing recorded the answer in a form the next person could re-run.

**Curbpack answers the deterministic half:** does this asserted reference resolve to something that exists in this tree, byte-identically on your machine and mine? **The Mapper answers the judgement half:** which artifact does this sentence mean, when the sentence does not say — and records the human's answer so it survives the next commit.

Alone, one is a linter and the other is a suggestion engine. Together they are an artifact whose reader can re-derive the result instead of trusting the writer.

---

## 2. The axiom

> **An artifact must never assert something the tool itself caused. A positive claim requires an input the tool cannot manufacture.**

This is not style; it decides arguments. Curbpack never generates the documentation it then checks. The Mapper never emits an unreviewed link as if a human had accepted it. RISE never signs what a regulation *means*, only that a mechanism *held*.

---

## 3. Five invariants

1. **Remove work; never create a list.** Default view is what is already established; the unresolved set goes underneath. Never the reverse.
2. **Determinism exists for the reader, not the writer.** The engine and the published method are free structurally, not generously — the recipient re-runs the computation instead of trusting the sender.
3. **The nine check kinds are frozen, and the honest gap is the feature.** A question the nine cannot express is a question a human answers. Saying so plainly is what makes the answered fraction credible — and it is the Mapper's entire reason to exist.
4. **Identity is not provenance.** Identity is what makes a thing the same thing across time; provenance is how it came to be. Bake provenance into identity and every pack re-issue orphans every link.
5. **Nothing dies silently.** Every gate is a named conversation with a date; every reserved field has an expiry; an unwired field is a defect, not a placeholder.

**And one negative rule belonging to both sides: no similarity score on an edge.** An edge exists because the target was found, or it does not exist. A number between 0 and 1 is an invitation to argue, and the value of the artifact is that there is nothing to argue about.

---

## 4. Settled — do not relitigate

| Position | |
|---|---|
| Rule identity = `BuyerQuestion.GateID` (= `rule.ID`); `pack_digest` is provenance and **must never be baked into linkage identity** | ✅ matches shipped contract |
| Artifact identity = `Finding.ID`, shape `reference:path:<repo-relative-path>` | ✅ published contract |
| Two-axis reconciliation: **artifact state** (UNCHANGED/CHANGED/MISSING) separate from **review freshness** (CURRENT/STALE) | ✅ correct; a stale review of an unchanged file is a different fact from a current review of a changed one |
| Mapper owns discovery + human decision + reconciliation; curbpack owns deterministic resolution + record + delta; **neither owns claim truth or compliance** | ✅ keep the last clause in every version, forever |
| Nine check kinds frozen; Trivy stays outside | ✅ `CONTRIBUTING.md`; `redteam-pilot.sh` case 10 freezes the pack catalogue |
| Deterministic search first; human gate before export | ✅ |

---

## 5. Post-#30 — consume these, do not rebuild them

Three things shipped after the v8 concept was verified. Each removes work from the Mapper.

| Shipped | Where | Consume it as |
|---|---|---|
| `BuyerQuestion.Answered` / `Evidence` / `VerifiedAt` | `internal/exportx/buyer_questions.go:25–27` | **The structural answer already exists.** Map only the residual set the nine kinds cannot express |
| `Report.SubjectCommit` / `SubjectStateHash` | `internal/review/review.go:109–112` | **Read `subject_commit` as `repository.commit`.** Do not shell out to `git rev-parse` — a Mapper-computed and a record-supplied commit can disagree, and that class of defect takes a week to find |
| Method `1.3.0` + classifier `refclass:2` | `review.go` + `internal/claimid` | **Hard-invalidate accepted links on `classifier_version` change; soft-note on `method_version`.** `parent_record_digest` / `review --verify-chain` chain prior records. v8 keys freshness on `pack_versions` only, which covers pack drift but not engine drift |

**One silent trap.** `buyer_questions.go:63,166`: when `res.SkippedRules > 0` (diff mode), **every `Answered` is forced false and `answers_suppressed` is set true.** A consumer reading `answered` without reading `answers_suppressed` concludes everything failed. **Refuse the import** rather than warn.

**What is still absent, stated plainly:** the `edges` writer does not exist. Of v8 §7's pilot steps, running `review --repo --json` and reading `GateID`/`Finding.ID`/`Source` work today; **exporting an accepted mapping into `edges` does not, on either side.** That step is item 7 below, and it is the one with a clock on it.

---

## 6. The seam — freeze this before any adapter

```
FROM curbpack, PER RECORD:
  subject_commit         -> Mapper's repository.commit       (read it; do not compute it)
  subject_state_hash     -> chain anchor    (empty = NOT CHAINED, not "chain broken")
  classifier_version     -> HARD invalidation of accepted links
  method_version         -> SOFT note; does not invalidate

FROM curbpack, PER FINDING:
  id     : reference:path:<p> | reference:claim:<rule-id> | reference:url:<short>
           | structure:<file> | digest:<key>
  source : the document the reference was extracted from — THIS IS THE EDGE
  state  : confirmed | unconfirmed | contradicted        (no score, ever)
  cause  : producer | extractor | genuine | external | self_disagree

FROM curbpack, PER RULE:
  gate_id            -> the join key (== rule.ID). NEVER contains a digest
  answered           -> structural check passed
  answers_suppressed -> IF TRUE, REFUSE THE IMPORT

TO curbpack (the reserved `edges` payload):
  gate_id, finding_id, source,
  reviewed_by, reviewed_at, review_state = approved,
  reviewed_against: { pack_versions, classifier_version, method_version }
```

**Rule for the last block: nothing enters `edges` that a human has not accepted.** That is the axiom applied at the seam.

**One semantic that is easy to misread.** `reference:claim:<rule-id>` is emitted with `StateConfirmed` and the detail *"Pack claim id present in document"* (`review.go:679–683`). **Confirmed means the string is present. It does not mean the requirement is met.** Render it as *"the documentation cites this rule"* — never as a green tick beside a requirement. That would assert something curbpack did not say.

---

## 7. The Mapper, in one screen

1. **Curbpack already answers the structural rules.** Import `buyer-questions.json`; refuse if `answers_suppressed: true`.
2. **Your job is the residual set** — the claims the nine kinds cannot express. Not every rule.
3. **Join on `gate_id`; identify artifacts by `Finding.ID`.** Never bake `pack_digest` into either.
4. **Read `subject_commit` / `subject_state_hash`.** Empty hash means not chained, not broken.
5. **Hard-invalidate on `classifier_version`; soft-note on `method_version`.**
6. **Nothing enters `edges` without human ACCEPTED.**
7. **Claim-id namespace (0a decided — Option A):** [`internal/claimid`](../internal/claimid) widens the pattern with a deny-list; classifier is **`refclass:2`**. Unknown namespaces may still drop as `unknown-claim-namespace` — consumers must not treat absence as “requirement unmet.”

---

## 8. Decisions

### 0a · The claim-id namespace — **DECIDED (Option A)**

Shipped in [`internal/claimid`](../internal/claimid): pattern `[A-Z][A-Z0-9]{1,15}-[A-Z0-9-]+` plus deny-list / deny-prefixes for common non-claims (`SPDX-*`, `RFC-*`, `SHA-*`, …). Single definition site for review + research extractors.

| Option | Trade | Outcome |
|---|---|---|
| **A — widen the pattern** + deny-list | No pack dependency; deny-list can rot | **Chosen** — classifier bumped to `refclass:2` |
| **B — derive from composed packs** | Zero false positives; pack-dependent reproducibility | Deferred; may revisit if deny-list cost dominates |

**Mapper impact:** hard-invalidate accepted links keyed under `refclass:1`. Soft-note only for method `1.2.0` → `1.3.0`.

### 0b · The `edges` schema — **OPEN**

Freeze §6's last block. One conversation. Blocks the `edges` writer only. **No `edges` writer ships while 0b is open (W7 gated).**

---

## 9. This week

```
Daniel:  run `curbpack review --repo . --json` on three real trees; read source + id
         (ten minutes, more informative than any spec — needs nothing from anyone)
Aslak:   stable-contracts gaps — add `reference:claim`, `subject_commit`,
         `subject_state_hash`; fix the stale 1.1.1 links            [minutes]
Both:    0b edges schema freeze (0a closed as Option A / refclass:2)

Then:
Daniel:  import buyer-questions (refuse suppressed); hard-invalidate on refclass:2; MVP UI on the residual set
Aslak:   keep pin → merge SHA after land; no edges writer until 0b

Milestone that earns the `edges` reservation:
         one human-accepted dummy mapping, end to end, into `edges`
         — the reservation is DELETED at product release v0.6.0 if unused
```

**Nobody waits for perfect contracts.** Daniel's first item runs today; only the adapter write waits on **0b**.

---

## 10. Never

- **Curbpack never generates the documentation it then checks.** `anti_placeholder` exists to catch exactly this. Removing work must never mean removing the human's authorship of their own claims.
- **RISE never signs an interpretation.** The pack author signs the reading; RISE CI counter-signs the mechanism — lint, citations resolve, author signature verifies, claim-safety passes. No human at RISE reads anything.
- **Never a tenth check kind** to fit an awkward question. It buys one question and costs the credibility of the other nine.
- **Never a score on an edge.**
- **Never a model, a network call in the evaluation path, or a persistent index inside curbpack.** Those live on the Mapper's side by design.
- **Never a parallel "map every rule" UI.** Post-#30 that duplicates answer polarity and is negative value.
- **Never the word "measurement"** for what either tool does — curbpack counts things and reports states. RISE operates the national metrology institute; that vocabulary is theirs. **And never a check that denies the stem `measur`** — NIS 2 says *"cybersecurity risk-management measures"* verbatim, and denying the stem would corrupt quoted law.
- **Never a compliance claim** — not in the tool, not in the Mapper, not in the paper, not in a slide. `scripts/claim-safety.sh` enforces this in CI; **the Mapper's export must survive the same check.** No field named `compliant`, no boolean called `passed_requirement`.

---

## Annexes

[**shared-frame-annexes.md**](shared-frame-annexes.md) — **A**: legal basis, verbatim, with a re-verify banner. **B**: research brief and RQ framing. **C**: engineering backlog demoted from the v8 review.

*Structural evidence for human review. Not conformity assessment. Not CE marking. Not a notified-body opinion.*
