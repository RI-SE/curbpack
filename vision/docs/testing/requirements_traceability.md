# Requirement traceability

This file maps the normative requirements in
[`docs/software-design-document.md`](../software-design-document.md) to
existing test and review evidence.

Coverage state describes the current test design, not an execution result.
Actual Pass/Fail and final requirement assessments belong to records from a
verification run.

| Coverage state | Meaning |
|---|---|
| Executable coverage | Existing executable cases would produce sufficient evidence for the requirement. |
| Specified but not executable | Catalogue scope exists, but no executable procedure. |
| Partial | Existing design produces relevant evidence that does not cover the whole requirement. |
| Unmapped | No defensible existing case or review activity. |

`CR-*` references are independent review activities.

Verification method is Test, Inspection, Review, Analysis, or a justified
combination. It does not change coverage state.

| Requirement | Source | Test suite | Existing test case(s) / review | Current coverage state | Verification method | Notes |
|---|---|---|---|---|---|---|
| MUST-01 | SDD §1.1 | CL | CL-001 | Partial | Inspection + Review | The executable review covers selected public and generated surfaces, not every possible Curbpack statement. |
| MUST-02 | SDD §1.1 | CL, RP | CL-002; RP-001, RP-002 | Partial | Inspection | Existing cases compare boundary statements but do not require the exact sentence on every buyer/reviewer artefact. |
| MUST-03 | SDD §1.1 | — | — | Unmapped | Review | No existing case verifies the meaning assigned to a reported reference. Review assigned from that meaning; string-resolution Test is not mapped. |
| MUST-04 | SDD §1.1 | RP, CL | RP-001, RP-002; CL-002 | Partial | Test + Review | Machine and human outputs are compared, but signatures and every scoped score or status are not covered. |
| MUST-10 | SDD §2.1 | — | — | Unmapped | Test | No existing case requires the verifier to recompute the value it checks. |
| MUST-11 | SDD §2.1 | — | — | Unmapped | Test | No existing case requires an independently supplied trust anchor. |
| MUST-12 | SDD §2.1 | — | — | Unmapped | Test | No existing case verifies full or fixed-version digest comparison length. |
| MUST-13 | SDD §2.1 | — | — | Unmapped | Test | No existing case re-derives a signed value before signature verification. |
| MUST-14 | SDD §2.1 | — | — | Unmapped | Inspection + Analysis | No existing case keeps every listed trust and disposition dimension separate. |
| MUST-20 | SDD §2.2 | — | — | Unmapped | Test | No existing case compares a write-producing run with a read-only evaluation of the resulting unchanged tree. |
| MUST-21 | SDD §2.2 | — | — | Unmapped | Test | No existing case verifies that a rule examining zero required targets cannot pass. |
| MUST-22 | SDD §2.2 | PK, EV, OP | PK-002, PK-004, PK-005; EV-004; OP-001–OP-006; CR-08 | Partial | Test + Review | Some parse and unsupported-input paths are executable; read, write, subprocess, walk, and other failure paths remain incomplete. |
| MUST-23 | SDD §2.2 | EV | EV-005; REG-SKIP-01 | Partial | Test | EV-005 is executable for `--diff` skip (`outcome=incomplete`, `skipped_rules`). The skipped-rule identifier is not present in every output channel; see REG-SKIP-01. |
| MUST-24 | SDD §2.2 | EV | EV-004 | Partial | Test | The check path for an unreadable required `SECURITY.md` is executable and stops as an operational error, not a pass. Other unreadable-artifact paths are not this case. |
| MUST-25 | SDD §2.2 | — | — | Unmapped | Test | No existing case varies external evidence or source metadata while holding gate inputs fixed. |
| MUST-30 | SDD §2.3 | DT | DT-001 | Partial | Test | DT-001 compares semantic result fields and exit status across repeated runs, not byte-identical canonical evaluation bytes (INV-04); a pass does not close MUST-30. |
| MUST-31 | SDD §2.3 | DT, PV | PV-001–PV-007 | Partial | Test | Executable PV cases cover only repository-snapshot, pack-byte, evaluator-version, and explicit-as_of slices; a pass does not close MUST-31. Locale, timezone, and the remaining exclude boundary are deferred. |
| MUST-32 | SDD §2.3 | — | — | Unmapped | Analysis | EV-008 concerns outcome order-independence, not total ordering of every field that feeds a digest. |
| MUST-33 | SDD §2.3 | — | — | Unmapped | Analysis | No existing case tests injectivity of the canonical digest encoding. |
| MUST-34 | SDD §2.3 | — | — | Unmapped | Test | No existing case proves cache non-authority or rejection of an unverified `latest` record. |
| MUST-35 | SDD §2.3 | RB, OP | RB-004; OP-005, OP-006 | Specified but not executable | Test | Concurrency, interruption, and cache-failure cases lack repeatable procedures. |
| MUST-40 | SDD §2.4 | PK, FS | PK-002–PK-005; FS-001–FS-007; CR-01, CR-02 | Partial | Test + Review | Pack and path inputs are partly exercised; the complete untrusted-input set is not. |
| MUST-41 | SDD §2.4 | — | — | Unmapped | Test | No existing case passes an untrusted option-shaped value to a subprocess boundary. |
| MUST-42 | SDD §2.4 | FS | FS-001–FS-004; CR-02 | Partial | Test + Review | Relative traversal is executable; absolute and intermediate-symlink paths are not. |
| MUST-43 | SDD §2.4 | — | — | Unmapped | Inspection + Analysis | Existing cases do not establish normalization, bounds, single escaping, and typed downstream values together. Inspection + Analysis assigned because no mapped case covers that conjunction. |
| MUST-44 | SDD §2.4 | RB | RB-001–RB-003; CR-11 | Partial | Inspection + Review | Resource conditions and review are identified, but executable limits are not specified. |
| MUST-45 | SDD §2.4 | — | — | Unmapped | Test | No existing case tests neutralization of executable repository-local Git configuration. |
| MUST-46 | SDD §2.4 | OP | OP-005 | Specified but not executable | Test | Controlled cancellation and preservation of the previous complete artefact are not yet executable. |
| MUST-47 | SDD §2.4 | NB | NB-002; CR-10 | Partial | Inspection + Review | Data exposure is selected for observation and review, but default-record field coverage is not executable. |
| MUST-48 | SDD §2.4 | NB | NB-001, NB-002; CR-10 | Specified but not executable | Inspection + Review | Network isolation and observation procedures are not defined. Inspection + Review assigned from command declarations and CR-10; Test of isolation is not yet defined. |
| MUST-50 | SDD §2.5 | — | — | Unmapped | Test | Existing Review Pack comparisons check machine-to-human consistency, not that human caveats, warnings, skips, and qualifications appear in machine output. |
| MUST-51 | SDD §2.5 | — | — | Unmapped | Analysis | Existing consistency comparisons do not establish derivation from one canonical evaluation. |
| MUST-52 | SDD §2.5 | — | — | Unmapped | Inspection + Review | No existing case requires the complete machine-outcome enum or prohibits inference from prose or score. |
| MUST-53 | SDD §2.5 | EV, OP | EV-001, EV-002; OP-001–OP-006; CR-08 | Partial | Test + Review | Pass and finding exit behavior is executable; usage, environment, and operational distinctions are incomplete. |
| MUST-60 | SDD §2.6 | UV | UV-001, UV-003; CR-09 | Partial | Test + Review | Selected documented paths are executed, not every printed operator- or agent-facing command. |
| MUST-61 | SDD §2.6 | — | — | Unmapped | Inspection | No existing case verifies the complete command registry metadata. |
| MUST-62 | SDD §2.6 | — | — | Unmapped | Inspection + Review | Existing release cases do not define a breaking-change fixture covering version, migration, and CHANGELOG evidence. |
| MUST-63 | SDD §2.6 | — | — | Unmapped | Test | No existing case round-trips a document with unknown additive fields. |
| MUST-70 | SDD §2.7 | — | — | Unmapped | Review | No existing case verifies the acknowledgement-only meaning of the flag and environment variable. |
| MUST-71 | SDD §2.7 | RP | RP-007; CR-07 | Partial | Review | Independent review addresses automated approval paths; the functional case is not executable and not all prohibited acts are covered. |
| MUST-72 | SDD §2.7 | RP | RP-006; CR-07 | Partial | Inspection + Review | Review covers some automated approval and signing paths; the complete enumerated human-authority act set is not exercised. |
| MUST-73 | SDD §2.7 | — | — | Unmapped | Review | No existing case verifies authority through an independent credential or repository decision. |
| MUST-74 | SDD §2.7 | — | — | Unmapped | Review | No existing case verifies that rollback guidance remains instructional. |
| MUST-80 | SDD §2.8 | RL | RL-005; CR-09 | Partial | Inspection + Review | Dependency and release review is selected, but the standard-library and optional-adapter boundary lacks an executable case. |
| MUST-81 | SDD §2.8 | NB | NB-001 | Partial | Test | Catalogue scope covers offline check behaviour; scan, evidence production, and review are not specified. |
| MUST-82 | SDD §2.8 | — | — | Unmapped | Inspection | No existing case checks every crossing format for a versioned schema and golden example. |
| MUST-83 | SDD §2.8 | RL | RL-004, RL-005; CR-09 | Partial | Inspection + Review | Source correspondence is executable; reproducible inputs, workflow privilege, and immutable references are not fully covered. |
| MUST-84 | SDD §2.8 | RL | RL-001–RL-003; CR-09 | Partial | Test + Review | Release evidence can be reviewed, but representative per-platform execution procedures are not specified. |
| MUST-90 | SDD §2.9 | — | — | Unmapped | Inspection + Review | No existing case verifies preservation of the canonical public repository and history. |
| MUST-91 | SDD §2.9 | — | — | Unmapped | Inspection + Review | No existing case verifies release licensing and authority for future commitments. |
| MUST-92 | SDD §2.9 | — | — | Unmapped | Inspection | Offline testing does not currently exercise payment, account, entitlement, or hosted-service availability. Inspection assigned; Test of those dependencies is not mapped. |
| MUST-93 | SDD §2.9 | — | — | Unmapped | Review | No optional commercial-service fixture or case exists. |
| MUST-94 | SDD §2.9 | — | — | Unmapped | Inspection | No existing case verifies historical strategy retention and experiment labelling. |
| MUST-95 | SDD §2.9 | — | — | Unmapped | Review | No existing case verifies public vulnerability-status claims and coordinated disclosure handling. |
| MUST-96 | SDD §2.9 | — | — | Unmapped | Inspection | No existing case verifies exclusion of commercial assumptions and private metrics from the product SDD. |
