# 2. Code and release review

Independent review of the frozen Curbpack source and the shipped release.
This is not a functional test suite. Functional cases are in
[../test_suites/](../test_suites/README.md).

A separate verification assignment (for example a 160-hour engagement)
selects how much of this procedure to run. The assignment is not part of
this file.

## Objective

Independently review implementation and release paths relevant to the required
test results and verify the available CI and release evidence for the frozen
source or release.

## What this is

Read the source that corresponds to the tested release. Look for
implementation paths that can cause:

- an incorrect **pass**;
- repository escape or observation of unintended state;
- data leaving the documented boundary;
- human-facing output that omits, reverses, or softens a finding, or adds
  unsupported assurance;
- automation creating or overwriting human approval;
- a release that cannot be tied to the stated source.

Then look at the CI and release evidence that claims to belong to that
same source. If it is missing, stale, or not reproducible, reproduce the
item or record that you could not.

## Who may do it

The reviewer is independent of the line that built the freeze under
review: not the author of the change, and not reporting through that
author’s manager for this work. Record competence (what you actually
know: Go, GitHub releases, this product) and any conflict.

That independence requirement matches the *role* of an independent
security review (Commission Implementing Regulation (EU) 2024/2690
Annex point 2.3, as explained in ENISA’s technical implementation
guidance). This procedure does **not** perform a NIS 2 entity review and
does not establish NIS 2, CRA, or CE conformity.

Secure-development evidence (tests, code review records, SAST) is in
scope as *inputs* to this review, in the sense of Annex point 6.2. Using
those artefacts is not a 6.2 audit of RISE or of the supplier.

## How to do it

1. Freeze the Curbpack commit (and release tag/assets if a shipped
   artefact is in scope). Do not review a moving `main`.
2. Copy
   [generated_code_review_protocol_template.md](../generated_code_review_protocol_template.md)
   **outside this repository**, one file per CR-id
   (`{run-id}_CR-01.md`, …). Do not commit filled protocols here.
3. For each CR-id below: read the named area in the frozen tree, answer
   the required question, and write observed behaviour and a conclusion
   on that protocol copy.
4. Use the engineering-evidence table for CI/release artefacts that
   belong to the freeze. Scanner warning counts are not a pass/fail.
   A warning becomes a product finding only after you judge reachability
   and relevance to Curbpack’s intended use.
5. Stop for a finding when a path can produce a false pass, escape,
   leak, bogus approval, or an unverifiable release. Record it; do not
   silently “note for later” if it is Critical or High.

## What to look for

| ID | Area | Required question |
|---|---|---|
| CR-01 | Pack parsing and validation | Can malformed, ambiguous, duplicate, conflicting or unsupported rules be accepted or interpreted inconsistently? |
| CR-02 | Repository traversal and file access | Can paths escape the repository, enter excluded administrative content, follow unsafe links or observe unintended state? |
| CR-03 | Check evaluation | Do supported checks implement the documented result states and failure semantics? |
| CR-04 | Finding identity | Are finding identifiers derived from inputs in scope of the selected pack and stable under equivalent runs? |
| CR-05 | State and provenance | Are repository state, pack identity, tool version and other required provenance bound to output without unsupported inference? |
| CR-06 | Review Pack generation | Can a human-facing derivative omit, reverse or soften a machine finding or add unsupported assurance? |
| CR-07 | Attestation and automated change paths | Can automation approve, sign, overwrite human history or cause generated material to be treated as reviewed evidence? |
| CR-08 | Exit status, cache and partial output | Can operational failure, cache failure or incomplete output appear as success? |
| CR-09 | Dependencies and release workflow | Are dependencies, build inputs, permissions, tags, checksums and release artefacts controlled and reviewable? |
| CR-10 | Data exposure | Can repository content, local paths, secrets or credentials leave the intended boundary? |
| CR-11 | Resource handling | Can malformed or large input cause unsafe termination, unbounded resource use or silent truncation that yields a valid result? |

## Engineering and release evidence

Use only evidence that demonstrably belongs to the frozen source.

| Baseline item | Evidence required |
|---|---|
| Complete Go test suite | All packages at the frozen source. |
| Race detection | Packages/workflows where the platform and code path support it. |
| Formatting and static analysis | gofmt and go vet, or documented organisation-approved equivalents. |
| Go vulnerability analysis | Normally govulncheck against the frozen module graph. |
| Secret scanning | Tracked repository and release-workflow material. |
| Security-focused static analysis | One primary analyser; additional tools only for a defined coverage gap. |
| Builds | Every publicly supported target. |
| Release controls | Permissions, pinned third-party actions, immutable tag handling, checksums and source-to-binary traceability. |
| Shipped artefact installation | Clean install and basic execution on each publicly claimed platform. Detailed functional platform checks remain in the RL suite. |

## What this is not

Do not write that Curbpack, RISE, or the assignment is NIS 2-compliant,
CRA-compliant, certified, or CE-marked. A CR conclusion is about this
freeze of this tool, against the questions above.
