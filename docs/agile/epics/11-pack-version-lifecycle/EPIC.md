# EP-11 — Pack identity, exchange and traceability

**Status:** Draft. Implementation is authorized through individual accepted stories.

## Goal

Enable Curbpack to exchange, modify and verify Packs and Requirements across organizations while preserving identity, provenance and traceability from Requirements through Claims to Check results.

Curbpack verifies and reports technical facts. The publisher is responsible for the content, modifications and declared origin. Release decisions belong to the organization using the results.

## Principles

- **Identity:** Packs and Requirements have namespace-qualified identities.
- **Origin:** A publisher declares the source of copied objects and takes responsibility for that declaration.
- **Ownership:** Editing a Pack from another namespace requires explicit acceptance of responsibility for a new local copy.
- **Status:** Review status is a declaration, independent of signature validity.
- **Signatures:** Object signatures and verified signed Git commits provide authentication. A Pack can be signed with unsigned Requirements.
- **Exchange:** Export and Import preserve Packs v2 content and signatures. Neither requires all Requirements to be signed.
- **Traceability:** Claims reference exact Requirement payloads; Run Results preserve the Claim and Requirement relationships.
- **Review:** Historical objects can be resolved by identity and digest, including through local Git history.
- **Reporting:** Curbcheck executes configured Checks and reports findings independently. Release policy may evaluate those findings separately.

Packs v2 files remain the system of record. Git provides file history. A separate versions database is not required.

## User journey

```text
Extract source ──┐
                 ├── Requirements workspace
Import Pack ZIP ─┘         │
                           ├── Compare / Apply / Edit
                           ├── Sign Requirement or Pack
                           └── Export Pack ZIP

Edit foreign Pack
    └── Confirm ownership
          └── Local Pack copy with origin

Requirement
    └── Claim (Requirement identity + digest)
          └── Checks
                └── Run Result
                      └── Review
                            └── Resolve historical chain
```

## Stories

| ID | User goal | Depends on |
|---|---|---|
| [VR-00](stories/VR-00.md) | Consistent signature verification and non-blocking export | — |
| [VL-00](stories/VL-00.md) | Namespace, origin and status contracts | VR-00 |
| [VL-01](stories/VL-01.md) | Take ownership when editing a foreign Pack | VL-00 |
| [VL-02](stories/VL-02.md) | Import and export Packs as ZIP through the Requirements workflow | VL-01 |
| [VL-03](stories/VL-03.md) | Review Requirement changes in a form instead of JSON diff | VL-02 |
| [VL-04](stories/VL-04.md) | Bind Claims to exact Requirement identities and digests | VL-00 |
| [VL-05](stories/VL-05.md) | Resolve historical Requirement–Claim–Check chains for Review | VL-04 |

Each story defines its own behavior and Given/When/Then acceptance criteria. This epic establishes their shared purpose and execution order, not a second set of requirements.

## Epic acceptance

The epic is complete when all listed stories are accepted and their automated tests pass, with existing supported workflows preserved.

## Relation to existing functionality

Existing Extract, Compare, Apply, signing, Claims, curbcheck and Review implementations are reused and extended through the applicable stories.

The former EP-11 stories covering persistent update queues, a separate Publish lifecycle and a SQLite versions index have been retired.

Git remains responsible for repository history; Curbpack is responsible for identifying, verifying and reporting the objects and relationships used in its workflows.