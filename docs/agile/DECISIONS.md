# Agreed design decisions and open questions

**Updated:** 2026-11-19

This document records decisions that govern ongoing and future Curbpack work. It is not a replacement for normative contracts, architecture specifications, user stories or acceptance tests.

Completed stories remain historical records. Later decisions take precedence for subsequent work without retroactively changing those stories. See [decision addendum](DECISIONS_ADDENDUM_2026-11-19.md) for agreed examples and boundaries.

## 1. Authority and documentation

The following documents have distinct responsibilities:

| Document | Authority |
|---|---|
| `docs/reference/packs2.md` | Normative persistent data contracts, approved by humans / Product Owner |
| `docs/arch/ARCHITECTURE.md` | Approved overall system architecture |
| Subsystem `ARCHITECTURE.md` files | Subsystem responsibilities and internal boundaries, consistent with the overall architecture |
| `docs/reference/workspace.md` | Workspace configuration and path contracts |
| `docs/agile/` | Planned changes, dependencies and acceptance criteria |
| `docs/req/` and `docs/test/` | Derived requirements and verification |

Packs v2 defines the meaning and persistent structure of Pack, Requirement, Claim, signatures and related records.

**Contract direction:**

`packs2.md` (human-approved specification) → Pydantic implementation → generated JSON Schema.

Pydantic is not an independent normative authority. Any mismatch must be resolved against the approved Packs v2 contract. Contract changes require explicit human approval.

The architecture documents must not redefine Packs v2 fields or semantics.

## 2. Target architecture — EP-02

EP-02 establishes the target architecture for Curbpack.

`docs/agile/epics/02-modularize-studio/CURBPACK_ARCHITECTURE.md` is the **approved detailed target**, and `docs/arch/ARCHITECTURE.md` is its normative system-level entry point. They describe one architecture. Existing subsystem documents are subordinate to these boundaries and the Packs v2 contract. Their historical versions remain in Git.

The approved design is:

- **Curbpack Studio:** A modular monolith with a thin application shell.
- **Subsystem ownership:** Each functional area owns its backend operations, REST endpoints and UI where applicable.
- **Backend:** Business logic is independent of HTTP and UI.
- **REST:** Thin subsystem-owned routers using explicit validated contracts.
- **UI:** Thin TypeScript pages that invoke backend operations.
- **Curbcheck:** Independently usable execution system with Python API and CLI.
- **Shared models:** Pydantic implementations of the human-approved persistent contracts.

EP-02 migrates existing functionality to the approved architecture while preserving observable behavior. Architecture migration is not permission to remove functionality or redesign workflows.

Do not introduce additional frameworks, layers or empty packages merely to match an illustrative directory tree.

## 3. Standalone tools — EP-09

EP-09 must conform to the architecture established by EP-02.

Standalone **CLI interfaces remain a goal** where useful. CLI and REST interfaces must reuse the same backend operations instead of implementing separate business logic.

Independent GUI applications are no longer required.

Curbcheck remains independently executable. Studio integrates Curbcheck through its public Python API without duplicating the Check engine.

EP-09 does not establish an alternative application architecture, HTTP ownership model or persistent data contract.

## 4. Pack identity, exchange and traceability — EP-11

The revised **EP-11 — Pack identity, exchange and traceability** supersedes the former Pack version lifecycle epic and its retired stories.

The scope VR-00 and VL-00 through VL-06 is reported complete (2026-11-19).

Agreed principles:

- Pack and Requirement identities are namespace-qualified. Packs with the same `pack_id` but different namespaces may coexist and be selected in one product.
- One active, editable copy per qualified Pack identity `(namespace, pack_id)` in the workspace. Curbpack does not keep a parallel version catalog as its own history. Git holds the history of committed content. Curbpack performs no automatic Git operations.
- `origin` records declared provenance; it is not automatically verified lineage. It references the latest explicitly accepted source at Take Ownership or Update, not every source of copied fields. Do not add `sources[]` or silently rewrite `origin`.
- Editing a Pack from another namespace requires explicit Take Ownership of a new local Pack copy. The accepting organization owns the result and uses its own namespace; selective cross-namespace field transfer uses Compare.
- `draft` / `reviewed` status is independent of signing.
- Embedded signatures and trusted signed Git commits are supported verification mechanisms.
- Signature validity must be reported explicitly. Signing does not imply approval or compliance.
- Export is non-blocking and independent of signing or publication.
- A Claim binds to the exact Requirement identity and payload digest.
- Curbcheck executes configured Checks even when a Requirement binding is stale or missing; the discrepancy is reported separately.
- Run Results and Review preserve the information needed to identify and resolve historical Requirements, Claims and Check results.
- Local Git history may be used to recover exact historical objects by identity and digest. A claimed `origin` is checked against the identified local source when available, otherwise a user-selected source; missing/unverifiable origins are reported without blocking Import or Update.

Any corresponding changes to Packs v2 and workspace configuration must be explicitly incorporated into `docs/reference/packs2.md` and `docs/reference/workspace.md`.

The previously proposed persistent `has_update` queue, separate Publish lifecycle and SQLite version index are not current EP-11 requirements.

Packs v2 files remain the system of record. Git provides repository history. Curbpack does not impose branch, commit, stash or push workflows; optional Git automation may be added separately.

## 5. Export and Import

EP-01's completed **PE-11 — Export Pack** established directory export for the pilot.

EP-11's **VL-02 — Import and export Pack ZIP** extends that functionality. Its accepted requirements take precedence for the new exchange workflow.

A Pack ZIP represents the existing Packs v2 directory content. No separate exchange manifest or alternative Pack schema is introduced.

Export does not require a signed Pack or individually signed Requirements. Import preserves the received Pack content, identity, origin and signatures, subject to the validation and collision rules defined by VL-02.

Imported Packs enter the existing Requirements workflow. Cross-namespace modifications follow VL-01 ownership rules.

The former requirement for a separate Publish operation is not part of the new workflow.

## 6. Existing pilot decisions retained

These decisions describe established behavior and remain applicable unless explicitly superseded by accepted later work.

### Pack Editor

- The application start page displays the available tools.
- Pack Editor has two navigation levels: a Pack list and each Pack's Sections / Sources list.
- The Pack list identifies the Pack, regulatory document and adapter.
- The Sections view retains source-level Extract and Edit actions.
- Add Source belongs to the Sections view.
- The existing source editor, extraction workflow, Requirement editor, comparison and signing capabilities must be preserved.
- An adapter supplies document-specific extraction behavior. No additional Packs v2 field or mandatory YAML format is implied.

### Extraction and review

- Extract uses the selected source and adapter.
- Extraction is additive: it proposes new Requirements and uses Compare for identified overlaps; absent results never remove existing or locally authored Requirements.
- Users explicitly review and apply or discard differences, including field-level Compare decisions.
- Unchanged Requirement content and unrelated fields are preserved.
- Requirements retain traceability to their original regulatory documents, editions and supporting passages.
- Changes to signed payloads require renewed signing.
- The improved form-based Compare workflow is specified by VL-03.

### Workspace

- One selected repository is the primary product-workspace context.
- Product workspace configuration belongs in `curbpack.json`.
- Studio application configuration belongs in `curbpack-studio.json`.
- The established directory concepts include Packs, Claims, Run Results and Review Reports.
- `docs/reference/workspace.md` remains authoritative for concrete configuration fields and path resolution until amended by an accepted contract change.
- New namespace and identity requirements from VL-00 must be incorporated into that document. Persisted Extract/Discovery jobs and feedback are normal repository files; only disposable caches need not be retained. Studio may show current Git clean/dirty/unavailable status without performing Git operations.

### Human responsibility

Curbpack evaluates configured technical checks and provides evidence for human review. It does not issue conformity assessments or CE decisions.

Signature validity, review status, technical Check outcomes and organizational release decisions are distinct facts. The organization controls who may approve, sign and distribute; Curbpack verifies technical facts rather than organizational mandates. Run Results and Review Reports are immutable historical snapshots.

## 7. Implementation sequence

Previously agreed implementation sequence (historical plan):

1. Reconcile the open backlog and architecture documents with these decisions.
2. Implement VR-00 — signature verification.
3. Implement VL-00 — namespace, origin and status contracts.
4. Continue EP-02 — behavior-preserving architecture migration. EP-02 does not implement EP-11 behavior.
5. Implement VL-01–VL-06 under the placement rule in EP-11: target component ownership, headless backend, and Pydantic models of the approved Packs v2 contracts; new pages in TypeScript; the existing HTTP server as a thin adapter until FastAPI is introduced. Existing Python pages change only where required to expose that functionality. No new business logic in Python pages.
6. Complete remaining EP-09 standalone CLI work.

**Current checkpoint (2026-11-19):** EP-11 VR-00/VL-00–VL-06 and EP-02 stages 0–3 are reported complete. Pause EP-02 before stage 4; prioritize packaging and end-to-end verification for the next pilot. EP-15 Update Pack remains a draft, not authorized implementation.

**EP-15 (draft):** Update Pack will compare BASE/LOCAL/NEW, reuse field-level Compare and explicit Apply, and identify affected Requirements/Claims without automatic rebinding or Check execution. Exact Requirement digests and `match`/`stale`/`missing` remain authoritative; metadata-only or Discovery-hint changes may be suggested for explicit rebind without substantive Claim re-review. Upstream removals are resolved per Requirement (keep/remove), with Claims unchanged automatically. Historical reports are never rewritten. A future bulk replace option is not part of the initial Update workflow.

Independent epics may proceed when their own prerequisites are satisfied.

Security defects and confirmed blockers are handled according to their severity rather than deferred solely because of this ordering.

## 8. Open questions

The following remain undecided and must not be resolved implicitly by coding agents:

- The exact path format of the one active, editable copy per `(namespace, pack_id)`.
- The precise semantics of source rows versus adapter-enumerated legal sections where current behavior does not already establish them.
- Whether one Extract operation should support multiple sections.
- Public repository visibility and authorization for remote publication.

These questions do not authorize new features. Git workflow automation, organizational authorization enforcement and a separate release-policy evaluator are deferred, not required for the current pilot.

## 9. Deferred ideas

- A general standalone Pack/directory comparison tool.
- Pack inheritance, `extends`, or automatic merging between Pack identities.
- An optional version index if a concrete performance or query requirement later justifies it.
- Additional standalone UI applications.

Deferred ideas require separate approval and are not acceptance criteria for current stories.

## 10. Change discipline

When a new decision replaces an earlier one:

1. Record the decision and its rationale here.
2. Update the affected normative contract or architecture document.
3. Reconcile only open epics, stories, requirements and tests that govern future work.
4. Preserve completed stories as historical records.
5. Do not change product code merely to reconcile documentation.

**One authoritative contract per responsibility. No competing architecture specifications. No inferred requirements from historical stories.**
