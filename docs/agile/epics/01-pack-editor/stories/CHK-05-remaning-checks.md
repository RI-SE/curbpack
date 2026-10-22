# CHK-05 – Git provenance Checks

**Epic:** EP-01 – Complete Functional Pilot  
**Status:** Draft – behavior contracts required before implementation

## User story

**As a user**, I want to check the Git history of evidence referenced by a Claim, so that I can verify when it was changed, whether the relevant commit was signed, and who authored or signed it.

## Scope

- Use **one Git checker tool** to execute several independently registered Checks.
- Each registered Check has its own ID, argument schema and **individual PASS / FAIL / SKIP result**.
- A Claim can contain several of these Checks using the **existing Packs v2 `checks[]` structure**. No sub-checks or new persistent data model.
- Intended Checks to specify before coding:
  - `git_fresh`: assess when the evidence file was last changed in the checked Git history.
  - `git_signed`: verify the signature on the relevant commit.
  - `git_author`: check the recorded author of that commit.
  - `git_signer`: check the verified signer identity, where a specific signer is required.
- The names above are **proposed Check IDs**, not yet approved changes to Packs v2 or the published Check catalog.
- Keep existing `exist` and `contents` Checks unchanged.

## Acceptance criteria

1. The Check catalog can expose multiple Check IDs implemented by the same checker tool; each entry declares its own arguments.
2. A user can attach and configure multiple Git Checks on the same Claim without a new grouping mechanism.
3. Each configured Check executes independently and reports its own status and an understandable reason. A failed signature Check must not hide a successful freshness Check, or vice versa.
4. Evaluation is anchored to the product revision actually being checked. The result identifies the relevant evidence path and Git commit, so the observation can be traced back.
5. Missing evidence, absent Git metadata, unverifiable signatures, dirty/uncommitted evidence, invalid arguments or unsupported cases must **never** produce a false PASS. The precise FAIL / SKIP / execution-error handling follows the approved Check contract.
6. A commit's author identity is not treated as proof of who signed it. Signature validity and signer trust are explicitly distinguished.
7. The Check result can be included without loss or reinterpretation in the existing Check → Compile → Review workflow.
8. Tests cover PASS, FAIL, missing or invalid input, and a Claim with multiple independent Git Checks. Previously passing `exist` / `contents` tests remain green.

## Required contracts before implementation

Derive testable requirements in `docs/req/checks.md` and align the normative Packs v2 Check definitions and catalog **before** asking an agent to implement these Checks. Specify:

- Which Git commit is relevant to a file, and what happens when the file is new, deleted, renamed or changed in the working tree.
- `git_fresh`: reference time (`as_of` or equivalent), commit timestamp choice, age comparison and boundary conditions; how the reference time is retained for reproducibility.
- `git_signed`: which signatures are supported, what constitutes verification and which trust configuration is used.
- `git_author` versus `git_signer`: what exact identity fields are compared, and how an asserted author is kept distinct from a verified signer.
- Exact argument schemas and PASS / FAIL / SKIP / error behavior for every Check.

Do not invent these semantics in implementation code. **CHK-05 is not Ready for Implementation until these contracts and corresponding tests are approved.**

## Out of scope

- The old ambiguous `owned` Check is not to be implemented under that name as part of this story without an explicit Packs v2 compatibility decision.
- `dep_ban`, CVE evaluation, SBOM inventory, Trivy integration and dependency policy are separate work.
- No new checker framework, Claim schema, GUI redesign or EP-02 refactoring.
