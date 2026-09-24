# Curbpack concepts and principles

Curbpack checks a software repository against selected rules and prepares the result for human review.

Software projects change over time. Code, dependencies, documentation, and policies do not always change together. Evidence that was once valid can therefore disappear, become incomplete, or stop matching the current product.

Curbpack helps make those relationships visible.

## How Curbpack works

The repository is the working unit.

The product selects one or more packs. The packs contain the rules Curbpack uses to check evidence in the repository.

```text
selected packs
      +
product repository
      ↓
curbpack check
      ↓
pass / fail + findings
      ↓
review material
      ↓
human review
```

The selected packs define **what is checked**.

The repository provides **the evidence being checked**.

Curbpack records **the result of those checks** and can prepare material for another person to review.
## Main concepts

### [Packs](packs.md)

Packs are versioned sets of rules.

They can represent an organization's own policies or rules based on an external framework. A product selects the packs that apply to it.

### Rules

A rule is an individual check defined by a pack.

Rules describe what Curbpack evaluates in the product repository.

### [Evidence](evidence.md)

Evidence is the repository material that Curbpack checks against the selected rules.

This can include documentation, manifests, dependency information, SBOM data, and other product material.

### Results and review material

A Curbpack result describes what happened when the selected rules were checked against a particular repository state.

A finding records where repository evidence did not satisfy a rule.

Curbpack can also prepare the result and supporting material for review by QA, security, compliance, buyers, auditors, authorities, or other reviewers.


## Principles

### Curbpack prepares evidence; people make decisions

A passing Curbpack check means that the evidence satisfied the rules encoded in the selected packs.

It does not by itself establish legal compliance, safety, certification, approval, or suitability for release.

Curbpack prepares review material. People decide what the result means.

### Human authority stays human

Automation can inspect repositories, evaluate rules, report findings, and prepare material for review.

Actions that represent human confirmation, attestation, approval, or sign-off remain human actions.

### Curbpack must not validate what it created

Curbpack can help create starter material or proposed changes.

Material created by the tool must not become evidence of human work merely because Curbpack created it.

The evidence must still represent something that is actually true about the product.

### Results should be reproducible

A Curbpack result belongs to the repository state, selected packs, and evaluation inputs that produced it.

Running the same check against the same inputs should produce the same result.

### Evaluation stays local

Curbpack evaluates the product repository locally.

Review material can then be handed to another person or organization without requiring Curbpack to receive or assess the product itself.

## Read more

* [Packs](packs.md)
* [Evidence](evidence.md)

For commands, configuration, file formats, and other exact behavior, see the reference documentation under `../reference/`.
