# Manual rows for the curbcheck run

`make test-curbcheck` prints these ids. They are not a pass. A missing filled protocol does not fail the seven carried checks.

The questions are the code-review steps from Curbpack `docs/testing/procedures/2_code_review_procedures.md`. They read the same run the seven checks produce. The blank protocol stays `docs/testing/generated_code_review_protocol_template.md`. A filled protocol stays outside this repository.

| id | Question |
| --- | --- |
| CR-01 | Can malformed, ambiguous, duplicate, conflicting or unsupported rules be accepted or interpreted inconsistently? |
| CR-02 | Can paths escape the repository, enter excluded administrative content, follow unsafe links or observe unintended state? |
| CR-03 | Do supported checks implement the documented result states and failure semantics? |
| CR-04 | Are finding identifiers derived from inputs in scope of the selected pack and stable under equivalent runs? |
| CR-05 | Are repository state, pack identity, tool version and other required provenance bound to output without unsupported inference? |
| CR-06 | Can a human-facing derivative omit, reverse or soften a machine finding or add unsupported assurance? |
| CR-07 | Can automation approve, sign, overwrite human history or cause generated material to be treated as reviewed evidence? |
| CR-08 | Can operational failure, cache failure or incomplete output appear as success? |
| CR-09 | Are dependencies, build inputs, permissions, tags, checksums and release artefacts controlled and reviewable? |
| CR-10 | Can repository content, local paths, secrets or credentials leave the intended boundary? |
| CR-11 | Can malformed or large input cause unsafe termination, unbounded resource use or silent truncation that yields a valid result? |
