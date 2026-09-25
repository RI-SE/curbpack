# Evidence

Evidence is the material in a product repository that Curbpack checks against the selected rules.

It can include documentation, manifests, dependency information, SBOM data, or other repository material referenced by the rules.

The basic relationship is:

```text
rule
  ↓
repository evidence
  ↓
curbpack check
  ↓
pass / fail + findings
  ↓
review material
```

## Evidence and results

Evidence is not the same thing as the result of checking it.

For example:

```text
rule:
SECURITY.md must exist and contain required information

evidence:
SECURITY.md

result:
PASS
```

A passing result means that the identified evidence satisfied the encoded rule.

It does not by itself mean that every statement in the evidence is correct, complete, current, or sufficient for a broader legal, safety, security, or organizational decision.

## Checks and human review

Curbpack checks whether repository evidence satisfies conditions encoded in the selected rules.

For example:

* Is expected evidence present?
* Does it contain required information or structure?
* Has evidence become stale?
* Is prohibited content or a prohibited dependency present?

A human reviewer can then inspect the evidence and decide whether it is substantively adequate for the decision being made.

```text
Curbpack:
Did the evidence satisfy the encoded rule?

Reviewer:
Is the evidence adequate for the decision?
```

## Evidence changes with the repository

Curbpack results describe the repository state that was checked.

When the repository changes, the same rules can be checked again. This makes it possible to detect when evidence disappears, becomes incomplete, becomes stale, or no longer satisfies a rule.

A previous passing result does not say that a later repository state still passes.

## Review material

Curbpack can prepare results and supporting evidence for another person to review.

Review material does not create a new claim, approval, or certification. It packages what was checked and what Curbpack found so that a reviewer can inspect it.

For exact output files, paths, schemas, receipts, and review-pack contents, see:

* [`../reference/outputs.md`](../reference/outputs.md)
