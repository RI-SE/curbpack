# PLAN.md — docs2 canonical documentation rebuild

## Goal

Build a new `docs2/` beside the existing documentation without changing `docs/` or `site/`.

The work is deliberately split into two phases:

1. **ASSEMBLE** — collect the right existing material into the right `docs2/` files. Preserve substance; do not polish.
2. **REWRITE** — rewrite each `docs2/` document for its audience, verify facts, review it as a cold reader, update it, then integrate the module.

`docs2/` is a candidate canonical documentation set. Existing `docs/` and `site/` are source material, not templates.

---

## Execution contract

Run this plan autonomously.

For every task/module:

- Use a **fresh sub-agent / fresh context**.
- Give the sub-agent only this task plus the explicitly listed source files. Do not preload the whole repository.
- The agent may read, edit, test, and commit locally without asking.
- Do **not** modify `docs/`, `site/`, implementation code, remotes, releases, tags, or branches.
- Do **not** push, create PRs, release, or perform destructive Git operations.
- If a fact is unclear, inspect only the exact code/CLI files listed for that document. Do not infer behavior from old prose.
- Stop only when a required fact is contradictory or cannot be resolved from the repository.

### Per-document loop in Phase 2

Each document uses exactly this loop, with an **independent reviewer context**:

1. **GENERATE** — writer sub-agent rewrites the target document from its assembled `docs2/` draft and listed sources.
2. **REVIEW** — a different fresh reviewer sub-agent receives the generated document plus the listed authoritative sources. It must not see the writer's reasoning. It reports only actionable defects.
3. **UPDATE** — writer/updater sub-agent fixes only the review findings.
4. **VERIFY** — fresh lightweight verification of links, commands, terminology, and scope.

Do not let the writer self-approve its own document. Do not merge generate and review into one pass.

### Commit rule

- Phase 1: one local commit per module after all module files are assembled.
- Phase 2: one local commit per module after all module documents have completed generate → review → update → verify.
- Final integration: one final local commit.

Use deterministic commit messages with the module id:

- Phase 1: `docs2: assemble A1`, `docs2: assemble A2`, ...
- Phase 2: `docs2: rewrite R1`, `docs2: rewrite R2`, ...
- Final integration: `docs2: final integration`

After a successful module commit, update that module in this plan to `Status: DONE` and `Review: PASS`. While work is active use `IN PROGRESS`. Never mark `DONE` before the module integration review passes and the local commit succeeds.

---

## Module integration review contract

Every module-level integration review must be a **fresh reviewer context** and produce exactly one of these outcomes:

- `PASS` — all module acceptance criteria are satisfied; or
- `FINDINGS` — a short numbered list of actionable defects, each naming the affected target file.

Do not create separate review documents. Apply `FINDINGS`, rerun the module integration review, and continue only when it returns `PASS`. Record only the resulting `Review: PASS` in this plan. This keeps review state deterministic without adding review-artifact clutter to `docs2/`.

---

## Target structure

```text
docs2/
  README.md

  getting-started/
    install.md
    first-check.md

  guides/
    developers.md
    ci-cd.md
    reviewers.md
    receiving.md
    authorities.md

  concepts/
    how-it-works.md
    packs.md
    evidence.md
    scan-and-check.md

  reference/
    cli.md
    configuration.md
    outputs.md

  development/
    architecture.md
    testing.md
    contributing.md
```

---

# PHASE 1 — ASSEMBLE

Purpose: create a complete but deliberately rough `docs2/` skeleton by moving/copying the useful substance from existing material into the correct target files.

Rules for this phase:

- Use one fresh sub-agent per **target document**, even when commit grouping is per module. Do not give one assembly agent all sources for a large module.
- Each assembled target starts with a temporary HTML comment `<!-- ASSEMBLY SOURCES: ... -->` listing only the source files actually used. Remove this comment in Phase 2 after verification.
- Prefer extraction/reorganisation over rewriting.
- Do not optimise prose.
- Do not invent explanations or terminology.
- Remove obvious project history, pilot notes, release-process chatter, marketing copy, duplicated disclaimers, and obsolete structure.
- If content is uncertain, add a short HTML comment such as `<!-- VERIFY: ... -->`; do not guess.
- The goal is **right material in right place**, not readability.

## Module A1 — Entry + getting started

Status: `DONE`  
Review: `PASS`

Targets:

- `docs2/README.md`
- `docs2/getting-started/install.md`
- `docs2/getting-started/first-check.md`

Sources:

- `README.md`
- `docs/README.md`
- `docs/intent-vs-scope.md`
- `docs/getting-started/install.md`
- `docs/getting-started/troubleshooting.md`
- `docs/getting-started/60-second-paths.md`
- `docs/getting-started/daily-loop.md`
- `docs/assistant-loop.md`
- `site/index.html`
- `site/for-builders/index.html`

Assembly constraints:

- Do not preserve the existing "ladder" structure as an information architecture.
- Do not mix GitHub Actions into CLI installation.
- Do not carry over `Pin sentence`, `install pin`, internal release-gate prose, pilot history, or repeated legal disclaimers.
- Primary install flow should have material for: install CLI → `doctor` → `demo` → next step.
- First-check material should distinguish read-only observation from gate evaluation without polishing the explanation yet.

Run the module integration review. Resolve all findings until `PASS`, then commit with the module id and update status.

## Module A2 — Developer use + CI/CD

Status: `DONE`  
Review: `PASS`

Targets:

- `docs2/guides/developers.md`
- `docs2/guides/ci-cd.md`

Sources:

- `README.md`
- `docs/getting-started/60-second-paths.md`
- `docs/getting-started/daily-loop.md`
- `docs/assistant-loop.md`
- `docs/strategy-boundary.md`
- `examples/workflows/curbpack-check.yml`
- `action.yml`

Assembly constraints:

- `developers.md` means a software engineer **using Curbpack on a product/repository**, not a Curbpack maintainer.
- `ci-cd.md` is a separate use case from local installation.
- Generic CLI-in-pipeline is the base model.
- GitHub Actions is one concrete integration example, not the definition of CI/CD.
- Do not invent GitLab/Jenkins/Azure-specific integrations. Generic CLI examples may mention them as environments only if no product-specific behavior is claimed.

Run the module integration review. Resolve all findings until `PASS`, then commit with the module id and update status.

## Module A3 — Reviewer + receiving

Status: `DONE`  
Review: `PASS`

Targets:

- `docs2/guides/reviewers.md`
- `docs2/guides/receiving.md`

Sources:

- `site/for-reviewers/index.html`
- `site/receiving-submissions/index.html`
- `docs/getting-started/buyer-evidence.md`
- `docs/for-authorities.md`
- `docs/stable-contracts.md`

Assembly constraints:

- Separate "how to interpret evidence" from "how to receive/triage a supplier submission".
- Keep trust-boundary substance.
- Remove marketing CTA text and duplicated artifact descriptions.

Run the module integration review. Resolve all findings until `PASS`, then commit with the module id and update status.

## Module A4 — Authorities / auditors / CISOs

Status: `DONE`  
Review: `PASS`

Target:

- `docs2/guides/authorities.md`

Sources:

- `docs/for-authorities.md`
- `site/for-authorities/index.html`
- `docs/intent-vs-scope.md`
- `docs/security-model.md`

Assembly constraints:

- This is the one audience where a concise "what this does not establish" section is relevant.
- Preserve evidence-status and human-decision boundaries.
- Remove artifact-name dumping unless needed to support an authority/auditor task.
- Remove pilot/commercial/internal strategy material.

Run the module integration review. Resolve all findings until `PASS`, then commit with the module id and update status.

## Module A5 — Concepts

Status: `DONE`  
Review: `PASS`

Targets:

- `docs2/concepts/how-it-works.md`
- `docs2/concepts/packs.md`
- `docs2/concepts/evidence.md`
- `docs2/concepts/scan-and-check.md`

Per-target sources (do not load all of them into one context):

- `how-it-works.md`: `site/how-it-works/index.html`, `README.md`, `docs/assistant-loop.md`, `docs/intent-vs-scope.md`
- `packs.md`: `docs/write-your-own-pack.md`, `docs/packs-update.md`, `docs/stable-contracts.md`, `docs/intent-vs-scope.md`
- `evidence.md`: `docs/for-authorities.md`, `docs/security-model.md`, `docs/stable-contracts.md`, `docs/getting-started/buyer-evidence.md`
- `scan-and-check.md`: `README.md`, `docs/getting-started/60-second-paths.md`, `docs/assistant-loop.md`

Assembly constraints:

- Concepts must be product concepts, not project-history concepts.
- `scan-and-check.md` must collect the material needed to explain observation/reporting versus gate decision.
- `evidence.md` may collect artifact/trust information, but do not preserve old artifact lists merely because they exist.
- Do not promote deferred features to current behavior.

Run the module integration review. Resolve all findings until `PASS`, then commit with the module id and update status.

## Module A6 — Reference

Status: `DONE`  
Review: `PASS`

Targets:

- `docs2/reference/cli.md`
- `docs2/reference/configuration.md`
- `docs2/reference/outputs.md`

Sources:

- `docs/stable-contracts.md`
- `docs/getting-started/install.md`
- `README.md`

Do not perform open-ended repository discovery in Phase 1; code/runtime help belongs to Phase 2 verification.

Assembly constraints:

- Reference is factual, compact, and non-narrative.
- Do not copy tutorials or policy essays into reference pages.
- Add `<!-- VERIFY: ... -->` for command names, flags, exit codes, paths, defaults, or aliases that must be checked against code/runtime help in Phase 2.

Run the module integration review. Resolve all findings until `PASS`, then commit with the module id and update status.

## Module A7 — Development

Status: `DONE`  
Review: `PASS`

Targets:

- `docs2/development/architecture.md`
- `docs2/development/testing.md`
- `docs2/development/contributing.md`

Per-target sources (separate fresh context per target):

- `architecture.md`: `docs/software-design-document.md`, `docs/security-model.md`, `docs/assistant-loop.md`
- `testing.md`: `docs/testing/README.md`, `docs/testing/strategy.md`, `docs/testing/test_suites/README.md`, `docs/testing/test_suites/EV.md`, `CONTRIBUTING.md`
- `contributing.md`: `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, `SECURITY.md`, `docs/claim-discipline.md`, `docs/strategy-boundary.md`

Assembly constraints:

- This section is for Curbpack maintainers/contributors.
- Keep product-use guidance out of this section unless needed for contribution workflow.
- Architecture material must be treated as potentially stale until verified against package layout in Phase 2.
- Testing page should collect the verification model and taxonomy, not every testcase.

Run the module integration review. Resolve all findings until `PASS`, then commit with the module id and update status.

## Phase 1 integration check

Status: `DONE`  
Review: `PASS`

Use a fresh sub-agent.

Check only:

- every target file exists;
- every target has content from the intended sources;
- no target is obviously empty or a dump of an entire old file;
- no source document was modified;
- no `site/` file was modified;
- obvious duplicate sections are flagged for Phase 2 rather than polished now.

Do not rewrite prose in this integration check.

---

# PHASE 2 — REWRITE + VERIFY

Purpose: make each assembled document concise, readable, audience-specific, and factually grounded.

Run **one fresh sub-agent per document**. After all documents in a module are complete, run a fresh module-level integration sub-agent and commit the module.

Global writing rules:

- Plain technical English.
- Assume competent software engineers where appropriate; do not explain basics such as what PATH is unless needed for an actual failure mode.
- Introduce Curbpack-specific terms before using them.
- Prefer familiar terms (`version`, `release`, `GitHub Actions`) over invented/internal jargon (`install pin`, `pin sentence`, `three ladders`).
- Do not repeat legal disclaimers on every page.
- Describe what the product does before cataloguing what it does not do.
- Do not expose release-process internals in user documentation.
- Do not preserve existing structure merely because it exists.
- No marketing filler.
- No AI-style throat-clearing or redundant summary sections.

## Module R1 — Entry + getting started

Status: `DONE`  
Review: `PASS`

### `docs2/README.md`

Read:

- assembled `docs2/README.md`
- `README.md`
- `docs/intent-vs-scope.md`

Verify from:

- `internal/cli/cli.go`
- `internal/cli/registry.go`
- runtime `curbpack --help` if available

Required structure:

1. What Curbpack is — 2–4 sentences
2. Start here — role/task links
3. Minimal product flow
4. Deeper/reference links

Acceptance:

- reader can choose the right next page in <30 seconds;
- no release history or CI detail;
- no unexplained Curbpack jargon.

### `docs2/getting-started/install.md`

Read:

- assembled target
- `docs/getting-started/install.md`
- `docs/getting-started/troubleshooting.md`

Verify from:

- `scripts/install.sh`
- `scripts/install.ps1`
- `internal/platform/install_marker.go`
- doctor implementation / flags actually used by the repo

Required structure:

1. Install on macOS/Linux
2. Install on Windows
3. Verify: `curbpack doctor`
4. Try it: `curbpack demo`
5. Problems → troubleshooting link
6. Next → first check

Acceptance:

- no GitHub Actions;
- no ladders;
- no release-gate/manifest explanation;
- primary path visible without scrolling through edge cases.

### `docs2/getting-started/first-check.md`

Read:

- assembled target
- `docs/getting-started/60-second-paths.md`
- `docs/getting-started/daily-loop.md`

Verify from:

- `internal/cli/scan.go`
- `internal/cli/init.go`
- check command implementation/help
- `internal/config/config.go`

Required structure:

1. Go to product repository
2. Observe/read-only scan
3. Initialise if needed
4. Check
5. Understand red/green result
6. Next actions

Acceptance:

- difference between scan and check is understandable;
- no deep pathway/research/release discussion;
- all commands verified.

Run module integration review; update findings; commit.

## Module R2 — Developer use + CI/CD

Status: `DONE`  
Review: `PASS`

### `docs2/guides/developers.md`

Read assembled target plus only the user-facing source material listed in A2.

Verify from CLI help/registry for commands actually mentioned.

Required structure:

1. Normal local loop
2. Existing docs vs starting from scratch
3. Handling findings
4. Handoff/review output
5. Links to CI/CD and concepts

Acceptance:

- audience is a developer using Curbpack, not contributing to it;
- no Curbpack maintainer process;
- no duplicated install guide.

### `docs2/guides/ci-cd.md`

Read assembled target, `examples/workflows/curbpack-check.yml`, `action.yml`.

Verify from:

- `action.yml`
- CLI commands used in generic pipeline examples

Required structure:

1. CI/CD model: run the same check non-interactively
2. Generic CLI pipeline example
3. GitHub Actions example
4. Outputs / exit behavior relevant to pipelines
5. Other CI systems: use the generic CLI path

Acceptance:

- GitHub Actions clearly separate from CLI installation;
- GitHub-specific `uses: ...@...` appears only in the GitHub subsection;
- no invented GitLab/Jenkins/Azure integration.

Run module integration review; update findings; commit.

## Module R3 — Reviewer + receiving

Status: `DONE`  
Review: `PASS`

### `docs2/guides/reviewers.md`

Verify command/state claims against review CLI help and schemas used by the repo.

Required structure:

1. What you received
2. What the evidence can show
3. How to inspect/reproduce it
4. Signed/unsigned meaning if applicable
5. What requires human judgment

### `docs2/guides/receiving.md`

Verify `review` modes/flags against current CLI implementation/help.

Required structure:

1. Receive submission
2. Keep original intact
3. Review/triage
4. Optional chain/repo modes if actually supported
5. Escalate findings / handoff

Run module integration review; update findings; commit.

## Module R4 — Authorities / auditors / CISOs

Status: `DONE`  
Review: `PASS`

### `docs2/guides/authorities.md`

Verify claims against current pack defaults, CLI help, and actual evidence outputs.

Required structure:

1. What Curbpack does
2. What evidence it produces / what that evidence demonstrates
3. Reproducibility and offline use
4. What cannot be concluded from a green result
5. Human/organisational responsibility
6. Links to technical reference

Acceptance:

- legal/regulatory boundaries are concise and relevant;
- no `Trust level (honest)` wording;
- no unexplained SARIF/ContextPack/OpenVEX/Git Notes dumping;
- no claim of certification, authority approval, or market access.

Commit after review/update.

## Module R5 — Concepts

Status: `DONE`  
Review: `PASS`

### `docs2/concepts/how-it-works.md`

Verify primary command flow against CLI registry/implementation.

Required structure:

1. Inputs
2. Observe repository/evidence
3. Scan/report
4. Check against selected rules/configuration
5. Build review material
6. Human decision

Do not force current implementation package names into the conceptual model.

### `docs2/concepts/packs.md`

Verify against pack loader/composition/check-kind implementation.

Required structure:

1. What a pack is
2. Rules/checks
3. Composition
4. Selecting/updating packs
5. Writing your own pack → dedicated link

### `docs2/concepts/evidence.md`

Verify emitted artifact names/paths against current implementation.

Required structure:

1. Evidence model
2. Structural evidence vs claims
3. Reproducibility/identity
4. Human review material
5. Optional/specialised formats in a compact reference link

### `docs2/concepts/scan-and-check.md`

Verify from scan/check implementations and CLI help.

Required structure:

1. `scan`: observe and report
2. `check`: evaluate against selected rules/configuration
3. Inputs/outputs of each
4. Exit/result semantics
5. When to use each

Acceptance for module:

- concepts form one coherent mental model;
- terminology is consistent across all four pages;
- no feature-name inventory disguised as architecture.

Run module integration review; update findings; commit.

## Module R6 — Reference

Status: `NOT STARTED`  
Review: `NOT RUN`

### `docs2/reference/cli.md`

Authoritative sources:

- `internal/cli/registry.go`
- `internal/cli/cli.go`
- `internal/cli/help.go`
- runtime help where available

Structure:

- command table
- aliases
- key flags by command
- exit codes
- advanced commands clearly marked

### `docs2/reference/configuration.md`

Authoritative sources:

- `internal/config/config.go`
- `internal/paths/paths.go`
- targeted grep for `CURBPACK_` environment variables

Structure:

- config file
- pack/config selection precedence
- environment variables
- paths/cache locations where configuration-relevant

### `docs2/reference/outputs.md`

Authoritative sources:

- `internal/paths/paths.go`
- actual output-producing packages/commands referenced by the assembled draft

Structure:

- command → output table
- output path
- format
- when created
- intended consumer

Acceptance:

- reference pages contain facts, not tutorials;
- every listed flag/path/output exists in current code;
- no historical names unless explicitly labelled compatibility/legacy.

Run module integration review; update findings; commit.

## Module R7 — Development

Status: `NOT STARTED`  
Review: `NOT RUN`

### `docs2/development/architecture.md`

Read assembled target and current package layout.

Required structure:

1. Product responsibilities
2. Main runtime flow
3. Major implementation areas
4. Trust/write boundaries
5. Pointers to detailed code/reference

Acceptance:

- describes current code, not an old target SDD;
- distinguishes architectural responsibility from every small Go package;
- does not present every package as a top-level subsystem.

### `docs2/development/testing.md`

Read assembled target plus current testing docs and actual test/run entry points.

Required structure:

1. Test strategy / levels
2. Go package tests
3. Broader verification suites
4. How to run each level
5. Traceability / records

Acceptance:

- explicitly distinguishes `go test ./...` from broader verification suites;
- does not imply every `*_test.go` is necessarily a unit test;
- current executable vs planned suites are accurately described.

### `docs2/development/contributing.md`

Read assembled target plus current contributor policy sources.

Required structure:

1. Set up development checkout
2. Change workflow
3. Required local verification
4. Documentation/claim discipline
5. Security reporting
6. PR handoff

Acceptance:

- only contributor/maintainer material lives here;
- no duplicated product-user tutorial.

Run module integration review; update findings; commit.

### Anti-slop gate

Before committing any module, the module reviewer must reject it if any of these are true:

- a page introduces a new product concept not present in authoritative sources;
- a page inherits an old heading/term only because the source had it;
- a page explains internal release/process mechanics to a user who does not need them;
- a page duplicates more than one paragraph of another `docs2/` page instead of linking;
- a page contains generic filler that can be removed without losing information;
- a command, flag, path, default, artifact, or exit code is stated without verification where verification is required;
- a page uses Curbpack-specific terminology before defining it;
- a reviewer only says “looks good” without checking the acceptance criteria.

---

# PHASE 3 — FINAL INTEGRATION

Status: `NOT STARTED`  
Review: `NOT RUN`

Use one fresh sub-agent with only `docs2/` plus exact code files needed to resolve factual conflicts.

Perform a cold-reader walkthrough from `docs2/README.md` for these paths:

1. New developer installing and checking a repo.
2. Developer adding Curbpack to CI/CD.
3. Reviewer receiving evidence.
4. Authority/auditor trying to understand what a result means.
5. Curbpack contributor trying to understand architecture/testing.

Check:

- navigation and relative links;
- broken links;
- duplicated material;
- terminology introduced before use;
- same concept named differently across pages;
- commands in the wrong guide;
- CI/CD leaking into installation;
- maintainer/release internals leaking into user docs;
- disclaimers repeated without audience need;
- unexplained artifact names;
- contradictions with current CLI/code;
- pages that are still substantially longer than their task requires.

Then:

1. Write `docs2/REVIEW.md` with only actionable findings.
2. Fix all findings that do not require product decisions.
3. Re-run the walkthrough.
4. Leave unresolved product decisions clearly listed in `docs2/REVIEW.md`.
5. Commit final integration locally.

Do not modify or delete `docs/` or `site/` in this plan.

---

# Done criteria

The plan is complete when:

- every target file exists under `docs2/`;
- every file has passed generate → review → update → verify;
- every module has its own local commit;
- `docs2/README.md` routes each audience cleanly;
- install, local use, CI/CD, reviewing, authority interpretation, concepts, reference, and Curbpack development are visibly separated;
- current code/CLI is authoritative for behavioral facts;
- existing `docs/` and `site/` remain unchanged;
- final cold-reader review has no unresolved usability or factual defects except explicitly recorded product decisions.
