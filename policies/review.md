# Review policy

Review changes against the user story, Packs v2 contract, applicable architecture and actual test results.

- Verify the intended user behavior, incorrect-input behavior, and that existing functions still work.
- Check that the change adds no unnecessary entity, policy, adapter layer or duplicated source of truth.
- For extraction/edit/sign/publication, look specifically for lost provenance, silent overwrites and signatures remaining valid after content changes.
- State findings with file locations and reproduction steps. A review without evidence is not a passed verification.
- The maintainer decides whether a change is accepted; an agent's review is not a substitute for that decision.
