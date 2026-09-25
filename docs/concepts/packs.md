# Packs

A Curbpack pack is a versioned set of rules used to check a product repository.

Each rule describes something Curbpack can evaluate in the repository, for example whether required evidence exists or contains expected information.

The basic relationship is:

```text
pack
  ↓
rules
  ↓
repository evidence
  ↓
curbpack check
  ↓
pass / fail + findings
```

The selected packs define **what Curbpack checks**. The product repository provides **the evidence being checked**.

A pack can represent an organization's own policy or rules based on an external framework. It is a machine-readable checklist, not a legal interpretation, conformity assessment, or certification.

## Selecting packs

A product normally records its selected packs in `.curbpack.json`.

For example:

```json
{
  "packs": [
    "house-policy",
    "medtech-iec62304"
  ]
}
```

`curbpack check` evaluates the rules from the packs selected for the product.

## Extending packs

A pack can extend another pack.

This lets a more specific pack build on a common baseline instead of repeating the same rules.

For example:

```text
baseline pack
      +
sector-specific pack
      ↓
rules checked for the product
```

`curbpack check` evaluates the rules from the selected packs and any packs they extend.

## Packs and review packs

Curbpack uses the word **pack** in two different contexts.

A **pack** used by `curbpack check` contains rules:

```text
pack
  ↓
curbpack check
```

A **review pack** is produced after checking a repository and contains material prepared for review:

```text
check result + supporting material
              ↓
          review-pack/
```

They are separate concepts: one defines what to check; the other contains material resulting from a check.

## More detail

For the exact pack format, configuration, and pack-management commands, see:

* [`../reference/packs.md`](../reference/packs.md)
* [`../reference/configuration.md`](../reference/configuration.md)
