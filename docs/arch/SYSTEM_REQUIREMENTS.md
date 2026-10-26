# System requirements

These are the inherited requirement sentences. The ids are stable because the carried test suites cite them. The sentences are not rewritten here.

The word MUST is the word in the source. It does not mean Studio implements the sentence, and it is not a passing curbcheck case. [Outside](../testing/outside.md) is that rule.

Where a sentence conflicts with [Packs v2](../reference/packs2.md) or a subsystem `ARCHITECTURE.md`, those documents win. The disposition column says the current relationship: arrived, simplified, not implemented, or not a curbcheck requirement.

This file is not a second data contract and not a second architecture. [Architecture](ARCHITECTURE.md) and [Packs v2](../reference/packs2.md) own those. [Derived requirements](../req/README.md) are the story requirements.

## Disposition

One row per requirement id in the traceability matrix. The matrix describes test design, not an execution result. A row here does not say the requirement passed because a test once existed.

Matrix row count: 55. Rows whose id came from that matrix: 55. Those two numbers are equal. Rows with new ids are outside that count.

A curbcheck row quotes the requirement. A row that is not a curbcheck requirement gives the reason it is outside curbcheck.

<span style="color:#b00020">Red</span> is not implemented, and it should be. Curbpack already has that behavior.
<span style="color:#c05600">Orange</span> is not implemented, and it has been on hold. Neither curbcheck nor Curbpack has that behavior.

| id | disposition | detail |
| --- | --- | --- |
| MUST-01 | not a curbcheck requirement | It limits what the product may claim. curbcheck does not decide legal conformity. The same sentence is MUST-01 below. `checks/ARCHITECTURE.md` says the check page has no field for a legal conclusion. |
| MUST-02 | not a curbcheck requirement | The fixed sentence on artifacts a buyer or reviewer sees is product wording. It is not a Check. |
| MUST-03 | not a curbcheck requirement | What a reported reference means is a review rule. It is not a Check. |
| MUST-04 | not a curbcheck requirement | Keeping a score or status inside its given scope is a presentation rule. The run result's `pass`, `fail`, and `skipped` values do not carry this requirement. |
| MUST-10 | arrived — Packs v2 §2.6 | A verifier MUST recompute the value it checks. The verifier recomputes the version digest. |
| MUST-11 | arrived — Packs v2 §2.6 | A trust anchor MUST be supplied independently of the artifact. An embedded key or signer entry proves only that the artifact is consistent with itself. The trusted certificate for `name` is independent of the artifact. |
| <span style="color:#b00020">MUST-12</span> | <span style="color:#b00020">not implemented</span> | Digest comparison MUST use the full digest, or a fixed versioned truncation length. The value being checked cannot choose how many characters are compared. |
| MUST-13 | arrived — Packs v2 §2.6 | A signed value MUST be derived again from the fields it claims to bind before a signature is reported as valid. The signature is over the recomputed digest, `name`, and `at`. |
| <span style="color:#c05600">MUST-14</span> | <span style="color:#c05600">not implemented</span> | Integrity, signer authenticity, whether the policy applies, freshness, the evaluation outcome, and the human's decision MUST stay separate fields. SDD v1.2 called the human's decision "human disposition". |
| <span style="color:#b00020">MUST-20</span> | <span style="color:#b00020">not implemented</span> | A run that writes files MUST NOT report a better result than a read-only evaluation of the same tree after those writes, when the tree is unchanged by anything else. |
| MUST-21 | simplified | A rule that examined zero required targets MUST NOT pass. |
| <span style="color:#c05600">MUST-22</span> | <span style="color:#c05600">not implemented</span> | Failed reads, writes, parses, subprocesses, or incomplete walks MUST NOT be omitted, and MUST NOT be reported as success. |
| MUST-23 | simplified | A skipped rule MUST appear in every output of that run, and MUST make the overall result `incomplete`. |
| <span style="color:#b00020">MUST-24</span> | <span style="color:#b00020">not implemented</span> | A required artifact that is present but unreadable MUST be a contradiction or an operational error, never a confirmation. |
| <span style="color:#c05600">MUST-25</span> | <span style="color:#c05600">not implemented</span> | External evidence and source metadata MUST NOT change a check result. |
| <span style="color:#c05600">MUST-30</span> | <span style="color:#c05600">not implemented</span> | Identical explicit evaluation inputs MUST produce byte-identical bytes of the deterministic evaluation record, and identical digests. |
| <span style="color:#b00020">MUST-31</span> | <span style="color:#b00020">not implemented</span> | The evaluation input includes the repository snapshot, the pack bytes, the trust policy, the evaluator version, and the explicit `as_of`. It excludes the implicit wall clock, the user, the home directory, the hostname, the locale, and filesystem order. |
| <span style="color:#c05600">MUST-32</span> | <span style="color:#c05600">not implemented</span> | Ordering that feeds a digest MUST be a total order over every field the digest covers. |
| <span style="color:#c05600">MUST-33</span> | <span style="color:#c05600">not implemented</span> | Digest encodings MUST be injective, by length-prefixing or an equivalent versioned canonical encoding. Two different values MUST NOT encode to the same bytes. |
| <span style="color:#c05600">MUST-34</span> | <span style="color:#c05600">not implemented</span> | Caches are derived. They are not the source of the result. An export MUST consume the exact evaluation it names, not an unverified `latest` file. |
| <span style="color:#c05600">MUST-35</span> | <span style="color:#c05600">not implemented</span> | Cache writes and artifact writes MUST be atomic, and MUST be safe when several processes write at once. An interrupted write cannot replace the last complete record. |
| <span style="color:#c05600">MUST-40</span> | <span style="color:#c05600">not implemented</span> | Repositories, received review packs, configuration, remediation caches, imported packs, source lists, and external evidence are untrusted input. The source-list schema id is `curbpack-source-register:1`. |
| <span style="color:#b00020">MUST-41</span> | <span style="color:#b00020">not implemented</span> | Untrusted content MUST NOT become a subprocess option or a command. |
| MUST-42 | simplified | Reads and writes MUST stay under their declared root after the whole path is resolved, including intermediate symlinks. |
| <span style="color:#c05600">MUST-43</span> | <span style="color:#c05600">not implemented</span> | Untrusted strings MUST be normalized, bounded in length, and escaped once at ingest. Later renderers receive typed values that are already safe to write out. |
| <span style="color:#c05600">MUST-44</span> | <span style="color:#c05600">not implemented</span> | Per-file bytes, total bytes, file count, subprocess time, and captured output MUST have explicit limits before allocation or execution. |
| <span style="color:#b00020">MUST-45</span> | <span style="color:#b00020">not implemented</span> | Repository-local Git configuration that can run commands MUST be neutralized for subprocesses the evaluator starts. |
| <span style="color:#c05600">MUST-46</span> | <span style="color:#c05600">not implemented</span> | Cancellation MUST stop subprocesses and remove incomplete temporary output, without deleting the previous complete artifact. |
| <span style="color:#c05600">MUST-47</span> | <span style="color:#c05600">not implemented</span> | Records produced by default MUST NOT disclose absolute home paths, usernames, environment secrets, credentials, or repository content the schema does not require. |
| <span style="color:#c05600">MUST-48</span> | <span style="color:#c05600">not implemented</span> | Network use is declared per command. Evaluation and review MUST NOT use the network. |
| <span style="color:#c05600">MUST-50</span> | <span style="color:#c05600">not implemented</span> | Caveats, warnings, skips, and qualifications shown to a human MUST appear in the machine-readable output of the same evaluation. |
| MUST-51 | simplified | Terminal text, JSON, the cache, exports, and the process exit status MUST be derived from one deterministic evaluation record. |
| MUST-52 | simplified | The machine-readable outcome is one of `pass`, `findings`, `incomplete`, or `error`. A consumer MUST NOT infer it from prose or from a score. |
| MUST-53 | simplified | Process exit compatibility remains `0` for pass, `1` for findings or an operational failure, and `2` for usage or environment errors. Machine-readable output distinguishes those categories. A later major version may use separate exit codes. |
| MUST-60 | not a curbcheck requirement | Whether a printed command runs is a documentation rule. curbcheck does not execute the commands printed in those files. It is not a Check. |
| MUST-61 | not a curbcheck requirement | A command registry, with side-effect class, audience, machine-readable output, and deprecation, is product documentation. It is not a Check. |
| MUST-62 | not a curbcheck requirement | A major version, checked-in migration examples, and a CHANGELOG entry are release process. They are not a Check. |
| <span style="color:#c05600">MUST-63</span> | <span style="color:#c05600">not implemented</span> | Unknown added fields are ignored safely, and are preserved by any component that reads a document and writes it back out. |
| MUST-70 | not a curbcheck requirement | `--i-am-human` and `CURBPACK_ALLOW_CONFIRM=1` are policy acknowledgements. curbcheck has no such flag. |
| MUST-71 | not a curbcheck requirement | Merge, release, attestation, approval, and an administrator bypass are outside curbcheck. Those actions stay out of the evaluator. It is not a Check. |
| MUST-72 | not a curbcheck requirement | `trust-import`, `review-sign`, `Last tabletop:`, `confirm-*`, `attest`, and `pin-bump` are actions a human takes. curbcheck does not perform them. It is not a Check. |
| MUST-73 | not a curbcheck requirement | Real authority is a credential or a repository decision the agent does not control. It is not a Check. |
| MUST-74 | not a curbcheck requirement | `/rollback` and rollback guidance are instructions to an agent. curbcheck does not edit, revert, or deploy. It is not a Check. |
| MUST-80 | not a curbcheck requirement | A Go standard-library evaluator, with optional OpenSSH as a separate adapter, is an implementation constraint. curbcheck starts as `python3 -m checks`. It is not a Check. |
| <span style="color:#b00020">MUST-81</span> | <span style="color:#b00020">not implemented</span> | `scan`, `check`, evidence production, and `review` work with no server, no database, no account, and no network. |
| MUST-82 | not a curbcheck requirement | A versioned schema and a checked-in example for a format that leaves a repository or an organization are format documentation. They are not a Check. |
| MUST-83 | not a curbcheck requirement | Reproducible release binaries, checksums, least-privilege workflows, and immutable release references are release process. They are not a Check. |
| MUST-84 | not a curbcheck requirement | Calling a platform supported only after its release artifact and a representative workflow have been exercised. It is not a Check. |
| MUST-90 | not a curbcheck requirement | Keeping the canonical public repository and its history is governance. curbcheck does not rewrite that history. It is not a Check. |
| MUST-91 | not a curbcheck requirement | The current license is [Apache-2.0](../../LICENSE). A later licensing commitment is legal review. It is not a Check. |
| MUST-92 | not a curbcheck requirement | Payment, account status, entitlement, and a hosted service are commercial and infrastructure limits. curbcheck has no payment input and does not need a hosted service. It is not a Check. |
| MUST-93 | not a curbcheck requirement | An optional paid service must not change findings or evidence. A passing Check is not something a payment can change. It is not a Check. |
| MUST-94 | not a curbcheck requirement | Keeping earlier strategy documents in history, and marking a consolidation as an experiment, is repository history. It is not a Check. |
| MUST-95 | not a curbcheck requirement | Accurate public vulnerability status, and waiting for coordinated disclosure, is publication practice. It is not a Check. |
| MUST-96 | not a curbcheck requirement | Pricing, target accounts, conversion assumptions, the payment provider, and private adoption metrics stay outside this design baseline. They are not a Check. |
| <span style="color:#c05600">STUDIO-SEL-01</span> | <span style="color:#c05600">not implemented</span> | This id is new. It does not reuse a `MUST-*` id. `curbpack.json` lists pack ids and does not list versions or directory digests (Packs v2 §2.3). The run result records `id`, `version`, and directory digest for the packs loaded in that run. Exit 0 does not compare that set with a previous signature and does not refuse a shorter id list. Do not add a version or digest field to `curbpack.json`. |

## Requirements in full

The table above is the curbcheck disposition. A curbcheck row quotes the requirement. A row that is not a curbcheck requirement gives the reason it is outside curbcheck. The sentences below are the requirements. <span style="color:#b00020">Red text</span> is not implemented, and it should be. Curbpack already has that behavior. <span style="color:#c05600">Orange text</span> is not implemented, and it has been on hold. Neither curbcheck nor Curbpack has that behavior. Ids, flags, quoted strings, and the strength of each sentence are unchanged.

## 2. Requirements

- **MUST-01** — Curbpack Studio MUST NOT state or imply conformity, certification, CE marking, notified-body approval, legal market access, or product safety.
- **MUST-02** — Artifacts a buyer or a reviewer sees MUST carry the statement `Prepares evidence for human review — not a conformity assessment.`
- **MUST-03** — A reference reported as found means only that a typed string resolved to the stated local target. It does not establish that a claim is true.
- **MUST-04** — A score, count, signature, or status MUST keep the scope it was given. It MUST NOT be presented as a broader product verdict or a regulatory verdict.

### 2.1 Verification independence

- **MUST-10** — A verifier MUST recompute the value it checks.
- **MUST-11** — A trust anchor MUST be supplied independently of the artifact.
  An embedded key or signer entry proves only that the artifact is consistent with itself.
- <span style="color:#b00020">**MUST-12** — Digest comparison MUST use the full digest, or a fixed versioned truncation length. The value being checked cannot choose how many characters are compared.</span>
- **MUST-13** — A signed value MUST be derived again from the fields it claims to bind before a signature is reported as valid.
- <span style="color:#c05600">**MUST-14** — Integrity, signer authenticity, whether the policy applies, freshness, the evaluation outcome, and the human's decision MUST stay separate fields. SDD v1.2 called the human's decision "human disposition".</span>

### 2.2 Evidence integrity

- <span style="color:#b00020">**MUST-20** — A run that writes files MUST NOT report a better result than a read-only evaluation of the same tree after those writes, when the tree is unchanged by anything else.</span>
- **MUST-21** — A rule that examined zero required targets MUST NOT pass.
- <span style="color:#c05600">**MUST-22** — Failed reads, writes, parses, subprocesses, or incomplete walks MUST NOT be omitted, and MUST NOT be reported as success.</span>
- **MUST-23** — A skipped rule MUST appear in every output of that run, and MUST make the overall result `incomplete`.
- <span style="color:#b00020">**MUST-24** — A required artifact that is present but unreadable MUST be a contradiction or an operational error, never a confirmation.</span>
- <span style="color:#c05600">**MUST-25** — External evidence and source metadata MUST NOT change a check result.</span>

### 2.3 Determinism and cache integrity

- <span style="color:#c05600">**MUST-30** — Identical explicit evaluation inputs MUST produce byte-identical bytes of the deterministic evaluation record, and identical digests.</span>
- <span style="color:#b00020">**MUST-31** — The evaluation input includes the repository snapshot, the pack bytes, the trust policy, the evaluator version, and the explicit `as_of`. It excludes the implicit wall clock, the user, the home directory, the hostname, the locale, and filesystem order.</span>
- <span style="color:#c05600">**MUST-32** — Ordering that feeds a digest MUST be a total order over every field the digest covers.</span>
- <span style="color:#c05600">**MUST-33** — Digest encodings MUST be injective, by length-prefixing or an equivalent versioned canonical encoding. Two different values MUST NOT encode to the same bytes.</span>
- <span style="color:#c05600">**MUST-34** — Caches are derived. They are not the source of the result. An export MUST consume the exact evaluation it names, not an unverified `latest` file.</span>
- <span style="color:#c05600">**MUST-35** — Cache writes and artifact writes MUST be atomic, and MUST be safe when several processes write at once. An interrupted write cannot replace the last complete record.</span>

### 2.4 Untrusted input, resources, and privacy

- <span style="color:#c05600">**MUST-40** — Repositories, received review packs, configuration, remediation caches, imported packs, source lists, and external evidence are untrusted input. The source-list schema id is `curbpack-source-register:1`.</span>
- <span style="color:#b00020">**MUST-41** — Untrusted content MUST NOT become a subprocess option or a command.</span>
- **MUST-42** — Reads and writes MUST stay under their declared root after the whole path is resolved, including intermediate symlinks.
- <span style="color:#c05600">**MUST-43** — Untrusted strings MUST be normalized, bounded in length, and escaped once at ingest. Later renderers receive typed values that are already safe to write out.</span>
- <span style="color:#c05600">**MUST-44** — Per-file bytes, total bytes, file count, subprocess time, and captured output MUST have explicit limits before allocation or execution.</span>
- <span style="color:#b00020">**MUST-45** — Repository-local Git configuration that can run commands MUST be neutralized for subprocesses the evaluator starts.</span>
- <span style="color:#c05600">**MUST-46** — Cancellation MUST stop subprocesses and remove incomplete temporary output, without deleting the previous complete artifact.</span>
- <span style="color:#c05600">**MUST-47** — Records produced by default MUST NOT disclose absolute home paths, usernames, environment secrets, credentials, or repository content the schema does not require.</span>
- <span style="color:#c05600">**MUST-48** — Network use is declared per command. Evaluation and review MUST NOT use the network.</span>

### 2.5 Same result in every output

- <span style="color:#c05600">**MUST-50** — Caveats, warnings, skips, and qualifications shown to a human MUST appear in the machine-readable output of the same evaluation.</span>
- **MUST-51** — Terminal text, JSON, the cache, exports, and the process exit status MUST be derived from one deterministic evaluation record.
- **MUST-52** — The machine-readable outcome is one of `pass`, `findings`, `incomplete`, or `error`. A consumer MUST NOT infer it from prose or from a score.
- **MUST-53** — Process exit compatibility remains `0` for pass, `1` for findings or an operational failure, and `2` for usage or environment errors. Machine-readable output distinguishes those categories. A later major version may use separate exit codes.

### 2.6 Documentation and compatibility

- **MUST-60** — Every command printed in a file for an agent or an operator MUST run as printed.
- **MUST-61** — Every command has, in one registry, its side-effect class, its audience, whether it has machine-readable output, and whether it is deprecated. The schema name of the side-effect class is `EffectClass`.
- **MUST-62** — A breaking schema change or a breaking CLI change requires a major version, checked-in migration examples, and a CHANGELOG entry.
- <span style="color:#c05600">**MUST-63** — Unknown added fields are ignored safely, and are preserved by any component that reads a document and writes it back out.</span>

### 2.7 Human and agent authority

- **MUST-70** — `--i-am-human` and `CURBPACK_ALLOW_CONFIRM=1` are policy acknowledgements. They are not technical proof that a human is present.
- **MUST-71** — Agents MUST NOT merge, release, attest, approve, enable auto-merge, use an administrator bypass, or treat a passing result as authorization.
- **MUST-72** — The actions that require a human are `trust-import`, `review-sign`, `Last tabletop:`, `confirm-*`, `attest`, and `pin-bump`. `pin-bump` is a change to the pinned release.
- **MUST-73** — Real authority is a credential, or a repository decision, that the agent does not control. A command-line flag is not that authority.
- **MUST-74** — `/rollback` and rollback guidance are instructions. An agent does not edit, revert, or deploy from that instruction alone.

### 2.8 Portability and release integrity

- **MUST-80** — The evaluator uses the Go standard library and has no third-party Go runtime dependency. Optional OpenSSH operations are a separate adapter, and that adapter is reported separately.
- <span style="color:#b00020">**MUST-81** — `scan`, `check`, evidence production, and `review` work with no server, no database, no account, and no network.</span>
- **MUST-82** — Every format that leaves a repository or an organization has a versioned schema and at least one checked-in example.
- **MUST-83** — Release binaries have reproducible build inputs, checksums, least-privilege workflows, and immutable release references.
- **MUST-84** — A platform is called supported only when its release artifact and a representative workflow have been exercised. Windows is not yet supported.

### 2.9 Product record and sustainability

- **MUST-90** — The canonical public repository and its history are not replaced, and are not rewritten, to improve how the project looks.
- **MUST-91** — Current official releases remain under their published [Apache-2.0 license](../../LICENSE). A later licensing commitment requires documented RI-SE authority and legal review.
- **MUST-92** — Local evaluation and offline review MUST NOT depend on payment, account status, entitlement, or a hosted service being up.
- **MUST-93** — An optional paid service MUST NOT change findings, the meaning of evidence, verification, or access to artifacts that were already exported.
- **MUST-94** — Earlier public strategy documents stay in history. When they are consolidated, they are marked as experiments. They are not rewritten as if they had been commitments.
- **MUST-95** — Public vulnerability status is accurate. Detail that would help an attacker may wait for coordinated disclosure until a fix is available.
- **MUST-96** — Pricing, target accounts, conversion assumptions, the choice of payment provider, and private adoption metrics stay outside this design baseline.

## 10. Communication, including operation without writing code

The primary path is the six tools. The limit on what the product may claim is MUST-01. A local check result is not a human review.
