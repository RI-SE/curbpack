# Curbpack — Software Design Document

> **Target state — not a full shipped command catalog.** This document describes design intent. **`curbpack verify` is not a shipped CLI verb** (do not run it; do not resurrect that name). Recipient-side document triage **is shipped** as **`curbpack review <received-pack>`** (offline; confirmed / unconfirmed / contradicted — document only, not a product verdict). Nothing in this doc is certification, CE marking, or notified-body opinion. For repository baseline vs this doc, see [internal SDD gap analysis](internal/sdd-gap-analysis.md). Historical / target-only `verify` sketches: [internal/historical-verify-target.md](internal/historical-verify-target.md).

**Version:** 1.0 · **Date:** 19 August 2026 · **Status:** target state
**Applies to:** `github.com/RI-SE/curbpack`
**Audience:** implementers and the agents working this repository

This document describes the state curbpack is being built toward — the design, the reasoning behind it, and the work required to get there. It is the single source of design intent. Where it conflicts with older notes, plans or specifications, this document wins. **Shipped verbs** live in the CLI help / `AGENTS.md` loop — not in the aspirational tables below.

Two lists in this document are load-bearing and must not be confused:

- **§13 — Never build.** These do **not** exist in the repository. They have been considered and rejected. Do not create them.
- **§14 — Remove.** These **do** exist in the repository today and are to be deleted.

---

## 1. Purpose and scope

Curbpack evaluates a source repository against local rule packs and produces evidence a human can hand to a buyer, an assessor, or a colleague. It runs offline, writes nothing unless asked, and never claims conformity.

**In scope:** evaluating a repository against packs; producing and verifying evidence artifacts; authoring packs; signing and verifying packs and evidence.

**Out of scope:** conformity assessment, certification, legal interpretation, vulnerability management, secret scanning at depth, owning requirements, hosting anything.

---

## 2. What curbpack is, and what it is not

**It is** a deterministic local evaluator with a small closed vocabulary, a signed-artifact model, and a command surface that does not grow when the number of regimes or stakeholders grows.

**It is not** a compliance platform, a questionnaire tool, a requirements management system, or a service. There is no server, no account, no telemetry, and no network call in the evaluation path.

### 2.1 The market reasoning behind the design

Two facts shape everything below.

In the European Union, no CRA harmonised standards are cited in the Official Journal, so no presumption of conformity is available for any product category, and the default product category — the majority — self-assesses irrespective of the technical specification used. In the United States, the uniform secure-software self-attestation and its common form were rescinded in January 2026; each agency now sets its own risk-based requirements.

Both markets therefore require **locally-authored interpretations**. There is no canonical form to fill in and no published standard to copy.

Three consequences drive the design:

1. **House policy is the general case; a regulator-derived pack is the special case.** The product is a rule engine that runs whatever pack you point it at, not a bundle of official rules.
2. **The binding constraint is not which rules exist but who writes them.** Pack authoring must be achievable by someone with no policy expertise. §7 addresses this directly.
3. **No registry.** A registry of authoritative rules requires authoritative rules to distribute, and there are none. What is needed is pack *portability* — hand someone a signed file, they verify who signed it and whether it is current. §8 delivers that at negligible cost.

---

## 3. Design principles

These are invariants. A change that violates one is rejected regardless of its benefit.

1. **Zero external dependencies.** Standard library only. Anything requiring a document parser lives outside this binary.
2. **No network in the evaluator, ever.** Rules and trust arrive as files. URLs are checked against an allowlist, never fetched.
3. **Reuse what is already in the binary or in git before specifying a new format.** Two standing examples: signature verification (§8) and pack authoring (§7).
4. **New capability is a pack primitive, not a command.** The verb count does not grow with regimes or stakeholders.
5. **The check algebra is closed at eight** (§6). A ninth requires a written argument that composition cannot express the requirement.
6. **Deterministic output.** No map iteration into ordered output; no wall-clock without an injectable clock. Byte-reproducibility is the promise to anyone diffing evidence.
7. **An artifact must never assert something the tool itself caused.** Positive claims require an input the tool cannot manufacture. This is the axiom; §12 lists its enforcement points.
8. **Read-only by default.** Writing requires an explicit second command and shows a diff first.
9. **Any text a third party may read is reviewed literally before implementation**, not after.
10. **Every gate ships with an adversarial test that attempts to forge it.**
11. **Ops scripts are net-neutral or they do not merge.**
12. **Five nouns on the public surface** (§11.3). Dates, never countdowns, in anything cached.

---

## 4. Architecture

```
                        ┌──────────────────────────────┐
   pack files  ────────▶│  compose  → validate         │
   (local, embedded,    │  (extends / overlays)        │
    or imported)        └──────────────┬───────────────┘
                                       ▼
   repository ─────────▶┌──────────────────────────────┐
   (read-only)          │  evaluator — 8 primitives    │
                        │  offline, deterministic      │
                        └──────────────┬───────────────┘
                                       ▼
                        ┌──────────────────────────────┐
                        │  canonical report model      │
                        └──────┬───────┬───────┬───────┘
                               ▼       ▼       ▼
                          terminal  artifacts  exit code
                                       │
                        ┌──────────────▼───────────────┐
   allowed_signers ────▶│  sign / verify (ssh-keygen)  │
   (human-imported)     └──────────────────────────────┘
```

**Component responsibilities**

| Component | Responsibility |
|---|---|
| `internal/packs` | Load, compose (`extends`/`overlays`), validate packs. Owns the pack schema and the check-kind registry. |
| `internal/validate` | Evaluate a composed pack against a repository. Owns the path jail. Produces findings only. |
| `internal/report` *(new)* | The single canonical report model. All artifacts render from it. |
| `internal/sign` *(new)* | Sign and verify via `ssh-keygen -Y`. Owns namespaces and validity evaluation. |
| `internal/cli` | Table-driven verb registry; flag parsing; exit-code mapping. |
| `internal/clock` | Injectable time. The only source of "now". |

**Exit-code contract:** `0` gates pass · `1` findings remain or operational error · `2` usage or environment. Leaf packages wrap a single exported `ErrUsage` sentinel; `ExitCode` matches with `errors.Is`.

---

## 5. Data model

### 5.1 Pack

```jsonc
{
  "id": "acme-house",
  "name": "Acme house policy",
  "version": "1.2.0",
  "assurance_class": "…",        // COMPUTED at load, never authored — see §5.3
  "extends": "cra-baseline",      // optional single parent
  "overlays": ["…"],              // optional merge-patch sources
  "jurisdiction": "EU",
  "validity":  { "effective_from": "…", "effective_to": "…" },
  "supersedes": "…", "superseded_by": "…",
  "citations": [ { "framework": "…", "instrument": "…", "article": "…",
                   "url": "…", "effective_from": "…", "effective_to": "…" } ],
  "provenance": {                 // optional; see §8.4
    "source":     { "title": "…", "publisher": "…", "uri": "…", "sha256": "…", "retrieved": "…" },
    "derivation": { "method": "manual|assisted|from-repo", "by": "…", "at": "…" },
    "valid_as_of": "…"
  },
  "review": {                     // optional; human-only — see §8.5
    "reviewer_identity": "…", "signature": "…", "at": "…"
  },
  "rules": [ … ]
}
```

**Validity is enforced at compose time at both levels.** A pack past `effective_to` is refused. A rule whose citations are all past their `effective_to` is reported as stale, not silently evaluated.

### 5.2 Rule

Common fields: `id`, `severity`, `check`, `description`, `remediation`, `expected`, `citations`, and an optional `origin` (`authored` | `from-repo` | `promoted`). Check-specific fields are defined per primitive in §6.

### 5.3 Assurance class — computed, never declared

`assurance_class` is derived at load time from which primitives a pack actually uses against what its declared scope requires. It is not an author-supplied field.

Every artifact that leaves the building carries both the class and the coverage statement: **"mechanically evidenced: X of Y."**

**Why:** a declared field can be inflated by whoever writes the pack. A derived one cannot. This is what makes it safe to have many packs.

### 5.4 Canonical report model

One `Report` type — metadata, findings, coverage, provenance, verification result — with thin renderers for terminal, JSON, markdown, SARIF and HTML. Field names are declared once.

**Why:** a finding is currently re-declared across eight structures and four hardcoded table headers; renaming one field touches roughly thirty-nine sites with no test that catches a desync. One model, N renderers, one place to add a field.

---

## 6. The check algebra

Eight primitives. Closed. Every regime is expressed by composing them; none requires new Go.

| Primitive | Question it answers | Status |
|---|---|---|
| `exists` | Is the artifact there? | shipped |
| `structured` | Does it have the required shape? | shipped |
| `content-forbids` | Does it contain what it must not? | shipped |
| `manifest-constrains` | Does a dependency violate a constraint? | shipped |
| `owned` | Is there a named responsible party? | shipped |
| `fresh` | Was it reviewed recently enough? | shipped |
| **`references`** | Do its citations resolve to real artifacts? | **to build** |
| `traces` | Does A link to B, and does B exist? | deferred — §15 Wave D |

### 6.1 `references`

Asserts that a document's citations resolve to artifacts that exist in this tree. This is what makes an answer *grounded* rather than asserted, and grounded answers are what a recipient accepts without asking again.

```json
{
  "id": "CRA-RISK-EVIDENCE",
  "check": "references",
  "severity": "high",
  "path": "docs/annex-vii/risk_assessment.md",
  "link_pattern": "\\[[^\\]]+\\]\\(([^)]+)\\)",
  "must_resolve": ["repo_path", "test_name", "commit_sha"],
  "min_resolved": 1
}
```

| Resolver | Resolution |
|---|---|
| `repo_path` | Existing path jail plus `Lstat`; must exist; must not escape the root |
| `test_name` | Matches `func Test…`, `def test_…`, `it(…)`, `describe(…)`; one cached pass over source |
| `commit_sha` | `git cat-file -e` with context and timeout; never network |
| `url_allowlisted` | Host present in the pack's citation allowlist — **link-only, never fetched** |

`url_allowlisted` resolves without a request by design: a URL is resolved if the pack vouches for the host, not if a server answers. The evaluator stays offline and results stay deterministic.

**Output:** names the unresolved links. Never a bare count.

**Tests:** dangling relative path; symlink escape; case-insensitive filesystem; CRLF; a link inside a code fence must be ignored; zero links present; `min_resolved` boundary.

### 6.2 `traces` — when it lands

Emits **linkage evidence for artifacts in this repository**. Every output carries that scope statement verbatim.

**Why the constraint:** in regulated practice, requirements are owned by a requirements-management system or a spreadsheet, and the traceability matrix is generated there. Curbpack supplements that; it does not replace it. Claiming otherwise puts the tool in a contest it loses and creates a defect class where the deliverable is wrong.

An empty `from` set is a finding, not a vacuous pass.

### 6.3 Check-kind registry

One descriptor per primitive:

```go
type CheckKind struct {
    Name        string
    Validate    func(Rule) error
    Eval        func(ctx, Rule) []ir.Failure
    ScaffoldFor func(Rule) []string
    TouchesDiff func(Rule, changed []string) bool
    HintFor     func(Rule) formhints.Hint
}
var kinds = map[string]CheckKind{ … }
```

The allow-map, the evaluation switch, the scaffold switch, the diff switch and the documentation table all derive from `kinds`. The documentation table is generated in a test so it cannot drift.

**Why:** adding a check type currently requires edits at roughly ten sites across six files.

---

## 7. Pack authoring

Pack authoring is the binding constraint on adoption. An organisation that cannot produce a pack cannot use the tool for anything beyond the three shipped ones. Three mechanisms, in order of leverage.

### 7.1 Authoring by example — `packs init --from-repo`

```
curbpack packs init --from-repo ../our-best-service --id acme-house --out packs/acme-house.json
```

Points at a repository that already behaves acceptably and emits a pack describing what it does. Detection reuses the existing primitives in reverse; no new checking logic is written.

| Observed in the exemplar | Emitted rule |
|---|---|
| `SECURITY.md` present with headings and substance | `exists` + `structured` |
| `CODEOWNERS` covering a documentation path | `owned` |
| A document modified within the last N months | `fresh` |
| A pinned or excluded dependency version | `manifest-constrains` |
| No secret-shaped strings on tracked paths | `content-forbids` |
| Document links that resolve to real files | `references` |

Output is a **draft**, `assurance_class: derived_draft`, every rule carrying `origin: from-repo` and the exemplar's commit SHA. A human edits and promotes it.

**Why this shape:** it converts "write a policy," which needs expertise and does not happen, into "point at your best repository," which is trivial. It respects the axiom — the tool asserts nothing about the target repository, it reports what the exemplar contains, and `derived_draft` says exactly that.

### 7.2 Promotion from a finding

```
curbpack packs add --from-finding HOUSE-SECURITY-MD --to packs/acme-house.json
```

The evaluator already knows the shape of every rule it runs; promoting one into a house pack is a copy.

### 7.3 The asker publishes the pack

The party doing the asking — an OEM, an agency, a buyer, an association — has both the motive and the standing to define requirements for its own supply chain. `ask-my-suppliers` derives a question set from a pack; it also emits the pack.

This closes the loop with no new infrastructure:

```
asker publishes signed pack → supplier runs it locally →
supplier returns signed evidence → asker runs recipient triage
  (TARGET ONLY — not shipped: historically sketched as `curbpack verify`;
   intended ship name for document triage is `curbpack review`)
```

No questionnaire round-trip, no portal, no registry. Not conformity assessment.

---

## 8. Trust and signatures

### 8.1 Design decision

Signing and verification use **OpenSSH signatures and `allowed_signers`**. No bespoke key format, no certificate chain, no custom bundle schema, no revocation infrastructure.

**Why:** the binary already invokes `ssh-keygen -Y verify`. `allowed_signers` already carries identity, public key, namespace and `valid-after` / `valid-before`. Every developer already holds a key in this format, and git already uses it for signed commits and tags. The alternative — a bespoke bundle, ledger and signature format — is roughly six days of work and a new attack surface to obtain properties that already exist.

### 8.2 Operations

> **TARGET / NOT SHIPPED (signing / trust-import):** the `packs sign` / `trust import` lines below are design sketches. Pack signing / trust-import remain Wave B. **Recipient document triage is SHIPPED** as `curbpack review` (§9.1). Historical name `curbpack verify` is not a CLI verb. Not certification.

```
curbpack packs sign <pack>                     # TARGET: ssh-keygen -Y sign -n <namespace>
curbpack packs trust import <allowed_signers>  # HUMAN-ONLY — see §12; not built yet
# SHIPPED document triage (not the historical verify name):
# curbpack review <received-pack| --repo …>
```

### 8.3 Verdict states

| State | Condition | Behaviour |
|---|---|---|
| `verified` | Signature valid, signer within validity window | Proceed |
| `expired` | Signature valid, signer outside window | Warn; explicit override, logged |
| `unverified` | Signature absent or verification failed | Loud; structurally unreachable from the positive rendering |

Default is hard fail with a logged override.

### 8.4 Two namespaces, two liabilities

| Namespace | Covers | Claim made |
|---|---|---|
| `curbpack-source` | A source document's bytes and digest | *This is the document, unmodified, as of this date* |
| `curbpack-derivation` | A pack derived from it | *This is our reading of it* |

Verified separately, rendered in distinct visual classes, never collapsible. A source attestation without a derivation signature is a valid and useful low-liability artifact.

**Failure attribution**, stated in `docs/security-model.md`:

1. Source content wrong, derivation signature valid → source issue.
2. Derivation signature covers a non-conforming extraction → pack publisher issue.
3. Verification reports failure and the consumer proceeds → integrator issue.
4. A derived artifact claims authority the source never granted → **the failure this design exists to prevent**.

### 8.5 Reviewer attestation

A pack version may carry a signature over its digest in the `curbpack-review` namespace by a key in `allowed_signers`. Absent, it renders as `unreviewed`. There is no third state and no default.

**Why not a date field:** a date the tool can compute is not evidence a human looked. The failure this prevents is a pack that stays technically fresh while becoming substantively wrong because the reviewer left.

### 8.6 Sunset and handover

Both fall out of `valid-before` with no additional mechanism. When a signer's window lapses, every pack it signed verifies as `expired`, everywhere, with no network call and no action by anyone. Renewal is an affirmative act by a live human holding the key, so abandonment announces itself. Handover adds the successor with `valid-after` and closes the predecessor with `valid-before`; consumers re-import once.

### 8.7 Self-contained artifacts

An evidence bundle embeds the signer entry for its signer and the digest of the pack it was evaluated against. A recipient holding only the file and the binary can verify everything.

**Why:** the design target is that the evidence verifies itself — no registry, no server, no account, no network, no trusted third party. Anything that must be fetched to verify is a dependency, and dependencies are what make evidence stop working.

---

## 9. Command surface

The verb count does not grow with regimes or stakeholders. Each stakeholder uses an existing verb with a different flag or a different pack.

| Verb | Purpose | Writes? |
|---|---|---|
| `scan` | Read-only diagnosis of this repository | No |
| `fix --<gap>` | Write one templated file, diff shown, confirmation required | Yes, one file |
| `init` | Configuration, hooks, editor integration — offered after first value | Yes |
| `check` | Evaluate; exit code authoritative | Cache only |
| `ask-my-suppliers` | Emit the question set and the pack | Yes, to a durable path |
| ~~`verify`~~ → **`review`** *(TARGET)* | Recipient document triage / artifact check | **No** — **not a shipped CLI verb**; do not run `curbpack verify` |
| `packs init --from-repo` | Author a pack by example | Yes, one file |
| `packs sign` / `packs trust import` | Sign a pack / import signers | Yes |
| `export --<format>` | SARIF, context pack, buyer questions | Yes |
| `attest` | Human-only capsule | Yes |
| `doctor` | Environment diagnosis | No |

### 9.1 Recipient triage (`review`) — why it exists *(SHIPPED)*

> **Shipped:** `curbpack review <received-pack>` triages a curbpack-native review-pack offline (no git, no network). States are **confirmed** / **unconfirmed** / **contradicted** about the **document** — never a product verdict. Historical SDD text used the verb name `verify`; **do not implement `curbpack verify`**. Not certification, not a conformity gate.

Curbpack today serves producers. Buyers, assessors and distributors receive HTML they cannot check. One read-only verb converts every artifact recipient into a potential installer — and the recipient is the party deciding whether a supplier keeps the contract. A producer install serves one repository; a recipient install serves every supplier that recipient has.

Output: the verdict, which claims resolve to real artifacts, which do not, and what could not be checked. Offline, no account. Structural evidence for human review only.

---

## 10. Artifacts

Every artifact that leaves the building carries, without exception:

- the computed `assurance_class` and **"mechanically evidenced: X of Y"**;
- the verification verdict, in the vocabulary of §8.3;
- the claim boundary: *prepares evidence for human review — not a conformity assessment*;
- the footer: *Generated locally by curbpack. Nothing was uploaded. Review the artifact yourself (`curbpack review` — document triage; **`curbpack verify` is not a CLI verb**).*

That footer converts a claim into an invitation, which is both the honest framing and the distribution mechanism.

Artifacts are byte-reproducible for identical inputs. Timestamps come from the injectable clock. Ordered output is sorted explicitly.

---

## 11. Communication surface

### 11.1 Front door

The README and the site lead with the dated obligation and one command. Article 14 reporting starts 11 September 2026. The first screen states the date, the single read-only command, and the fact that nothing is written or uploaded. Everything else is below the fold.

Metadata — `<title>`, `og:title`, `og:description`, any generated card image — carries **the date, never a day count**. Cached surfaces do not re-render, so a countdown baked into metadata freezes and becomes wrong.

The countdown is rendered into the HTML at build time with a scheduled daily rebuild, and refined client-side. It has three defined states: before, on the day, and after.

### 11.2 Repository identity

`RI-SE/curbpack` is the public source of truth: releases, install scripts, GitHub Action, and docs. The Go module path remains `github.com/afelin/curbpack` until a future semver-major migration.

### 11.3 Vocabulary

Five nouns on the public surface. Internal terms stay internal. A first-time reader should not need a glossary to understand the first screen.

`house-policy` is presented as the general case, not as an example. The three shipped packs are `house-policy`, `cra-baseline` and `medtech-iec62304`; a `packs/community/` namespace, clearly labelled unverified, opens when there is a second author.

---

## 12. Agent interface

The agent contract is `internal/skilldata/SKILL.md`, installed into the user's editor by `curbpack init`, mirrored in intent by `AGENTS.md` and `CLAUDE.md`. All three describe the same loop.

**The loop opens read-only:** `scan` → `fix` on a specific gap → `check` after `init` → `ask-my-suppliers` on green. An agent's first action never mutates the repository.

**Human-only acts.** Enumerated, enforced in one place, one test each, stated verbatim in the contract:

```
trust-import · review-sign · Last tabletop: · confirm-* · attest · pin-bump
```

Gate: explicit human confirmation flag or environment variable. A TTY alone is not sufficient.

**Why trust-import is on that list:** the neutrality property — *nobody has to trust the tool's author at runtime, they trust the key they chose to import* — assumes a human chose. If an agent imports whatever the documentation suggests, nobody chose anything and the property is fiction. Trust import must be an act only a human can perform.

**Why `Last tabletop:` is on that list:** it is the field the badge reads. If an agent can fill it, the tool manufactures the claim it is supposed to be reporting.

---

## 13. Never build

**None of the following exist in this repository. They have been considered and rejected. Do not create them.**

| Not to be built | Reason |
|---|---|
| A rules registry, node platform, portal or directory | No authoritative rules exist to distribute — zero harmonised standards published, no US common form. Pack portability (§8) covers the real need. Revisit only when harmonised standards are cited in the Official Journal **and** a named party asks to publish one. Both conditions. |
| `trust-bundle:1`, a key-ledger schema, or any bespoke signature or key format | §8.1 — `allowed_signers` already provides identity, namespace, validity windows, revocation and handover. |
| JSON-LD or PROV-O vocabulary in the binary | Provenance is expressed by two signature namespaces and a `provenance` block. A serialisation vocabulary adds a parser and a specification for no additional capability. |
| Time-anchor ledgers, Merkle batch roots, post-quantum batch signing | If long-horizon re-anchoring is ever needed it is a signed tag on an archive commit, not a subsystem. |
| Certificate chains or PKI machinery | §8.1. |
| A graph database, a query language, or a persisted graph | The graph is a deterministic in-memory derivation exported as JSON. Queries are plain Go functions. |
| A traceability matrix presented as an audit deliverable | §6.2. Curbpack emits linkage evidence with a mandatory scope statement, or nothing. |
| Telemetry, beacons, usage reporting, phone-home of any kind | Contradicts the zero-egress promise, which is the core of the product. A written boundary, not a judgement call. |
| Background daemons or self-restoring services | Reads as malware-adjacent to the security reviewers who are the buying audience. |
| Document parsers in the binary — PDF, XML, JSON-LD | The largest attack surface in document tooling, and it destroys zero-dependency on contact. |
| Browser runtimes, WASM, embedded UI frameworks | The proposition is one static binary. |
| Anything that owns requirements | §6.2. |
| A ninth check primitive | §3 principle 5, without the written argument. |

### 13.1 Never re-introduce

- **Any positive rendering reachable without a real verification result.** Every "ok", "signed", "rehearsed" or "verified" state must be gated on an input the tool cannot manufacture.
- **A day count in cached metadata.** §11.1.
- **A pack-declared `assurance_class`.** §5.3.
- **A second copy of the agent skill file.** One source, installed by `init`.

---

## 14. Remove from the repository

**These exist today and are to be deleted.** Verified present on `feat/pr4-funnel`.

| Path / item | Reason |
|---|---|
| `internal/sock/` (`sock.go`, `sock_test.go`) | One caller; the MCP example re-implements most of it over the CLI; carries a frozen public contract and its own attack surface. Delete, along with its section in `docs/stable-contracts.md` and the contract test that pins it. |
| `matchWithTimeout` in `internal/validate/validate.go` (3 occurrences) | Go's regexp engine does not backtrack, so this guards against a failure mode that cannot occur, and it leaks a goroutine on timeout. |
| `testdata/fuzz/` (20 files) | Unreferenced. Go's corpus convention places seeds under the package's own `testdata/fuzz/<FuzzTarget>/`. Either move them there and make the fuzz target assert something, or delete both. |
| `writeIfChanged`, `attestInfo` / `loadAttestInfo`, and the `var _ = ir.Failure{}` import anchor in `internal/release/release.go` | Dead code; the anchor exists only to retain a now-unused import. |
| `scripts/cite-check.sh` | Unreferenced by any workflow or script. |
| `scripts/time-to-green-windows.ps1` | Unreferenced by any workflow. |
| `scripts/dogfood-explain-recheck.sh` | Referenced only by prose. Wire it into the nightly workflow or delete it. |

**Verify then fix:** `auditASTReachability` is invoked from the main evaluation loop in `internal/validate/validate.go`. Confirm it is not also reachable from `evalRule`; if it is, the same violation produces two findings under a hardcoded gate identifier and the pack's own rule identifier never appears. The fix is to call it only from the rule path and stamp the rule's identifier and severity onto the returned finding.

---

## 15. Build order

Each wave states a precondition. Work that cannot name its consumer does not start.

### Wave A — now. No precondition.

| Item | Estimate |
|---|---|
| Agent contract parity across `AGENTS.md`, `CLAUDE.md`, `internal/skilldata/SKILL.md` (§12) | 2 h |
| Add trust-import to the human-only act list | 0.5 d |
| Pin signature scope on existing pointers to scheme, host and path | 2 h |
| Zero-install distribution — `npx`, Docker, Homebrew | 1–2 d |
| Present `house-policy` as the general case in docs and site (§11.3) | 1 h |
| Removals in §14 | 0.5 d |

### Wave B — value core. Precondition: at least three repositories not owned by the maintainer have run `scan` twice.

| Item | Estimate |
|---|---|
| Check-kind registry (§6.3) | 1 d |
| `references` (§6.1) | 2 d |
| Recipient triage / `review` (§9.1; SHIPPED; historical name `verify`) | done |
| Signing, trust import, three verdict states (§8) | 1 d |
| `packs init --from-repo` (§7.1) | 2 d |
| Computed `assurance_class`, reviewer attestation, self-contained bundle | 1.5 d |
| Asker publishes the pack (§7.3) | 0.5 d |
| Canonical report model (§5.4) | 3 d |

### Wave C — a first external publisher. Precondition: a named owner with a budget line, at an organisation that is doing the asking.

A publisher is a git repository, an `allowed_signers` file, a signing key and a CI job that signs on tag. Not a platform.

### Wave D — traceability. Precondition: a named user in a safety-critical regime has asked for linkage evidence, having been told it is not the audit matrix.

`traces` · the graph's observed half and its `satisfied_by` join · linkage export with the mandatory scope statement.

### Wave E — later. `packs/community/` when a second author exists · archival single-file export · a registry only under the two conditions in §13.

**Nothing in Wave B or later starts before the current distribution work ships.** The nearest regulatory date is 23 days out and does not repeat.

---

## 16. Test obligations

| Area | Required |
|---|---|
| Every gate | An adversarial test that attempts to forge it — a capsule claiming a signature it does not have, an edited result cache, a symlink escape |
| Every primitive | The failure table in its section |
| Artifacts | Byte-for-byte goldens with an injectable clock, and a rendered before/after in the pull request for any golden that changes |
| Determinism | A repeated-run test asserting identical bytes for identical input |
| Human-only acts | One test per entry in the §12 list asserting the act fails without explicit human confirmation |
| Check-kind registry | A generated documentation table compared against `kinds` |
| Test selection | Assert the count of tests that ran, never only the exit code — a selector matching zero tests exits zero |

---

## 17. Open questions

Resolve before Wave B is planned. Both are cheap. Resolve by consider the best route as of now to follow hypotheitically and cheapest.

1. **Does `ssh-keygen -Y` express what §8 needs** — multiple signers per artifact, and namespace separation between source, derivation and review attestations? One afternoon. If not, §8.1 fails and a bundle format returns.
2. **Does a pack derived from a good repository beat a blank template?** Test §7.1 against three internal repositories. If a human rewrites all of it anyway, `--from-repo` is ceremony and should be cut before it is built.

---

## Gap analysis

See [sdd-gap-analysis.md](internal/sdd-gap-analysis.md) for repository baseline vs this document (§14 removals, Wave B deferrals, check-name mapping, command surface).
