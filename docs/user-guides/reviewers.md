# Reviewing

This guide is for anyone reviewing Curbpack results and supporting evidence, for example QA, security, compliance, buyers, auditors, or authorities.

A reviewer will normally receive a `review-pack/`. Curbpack prepares the result and supporting material for review. The reviewer decides what that material means for the decision being made.

## 1. What is in the review pack?

The current review pack contains several layers of information:

| File                          | What it is for                                                                |
| ----------------------------- | ----------------------------------------------------------------------------- |
| `01-gate-failures.json`       | Machine-readable findings from the Curbpack check                             |
| `02-action-report.md`         | Detailed human-readable report of findings and suggested actions              |
| `03-executive-summary.md`     | Short summary of the result                                                   |
| `04-sbom-summary.json`        | Summary of software components                                                |
| `04-sbom.cdx.json`            | CycloneDX SBOM when available                                                 |
| `05-vex-draft.json`           | Draft vulnerability/exploitability information derived from relevant findings |
| `06-gate-failures.sarif`      | Findings in SARIF format for other tools                                      |
| `07-watchlist-sbom-join.json` | Informational join between watchlist and SBOM data                            |
| `buyer-onepager.html`         | Human-readable summary for the recipient                                      |
| `proof-index.html`            | Local verification page                                                       |
| `evaluation.json`             | Evaluation data when available                                                |
| `run-receipt.json`            | Receipt associated with the evaluation                                        |

Additional evidence or supporting files may also be included depending on how the review pack was created.

Keep the received review pack unchanged if you need to preserve the original handoff.

## 2. Start with the human-readable result

Start with:

```text
03-executive-summary.md
```

for an overview.

Then inspect:

```text
02-action-report.md
```

for the detailed findings.

`buyer-onepager.html` provides another human-readable summary intended for the recipient.

Use:

```text
01-gate-failures.json
evaluation.json
run-receipt.json
```

when you need the machine-readable findings or more detail about the evaluated result.

For the complete description of generated artifacts, see [`../reference/outputs.md`](../reference/outputs.md).

## 3. Understand what Curbpack checked

Curbpack evaluates rules from the selected packs against evidence in the repository.

```text
pack rule
     ↓
repository evidence identified by Curbpack
     ↓
curbpack check
     ↓
pass / fail + findings
```

A passing result means that the evidence Curbpack found satisfied the pack rule.

For example, a rule may require a security document to exist and contain specific sections. If the file is present and satisfies those checks, the rule passes.

This is evidence that the **check** passed. It is not by itself proof that every statement in the document is correct, complete, current, or legally sufficient.

## 4. Review the received material with Curbpack

A received review pack can also be inspected with:

```bash
curbpack review <review-pack>
```

This performs offline triage of the material in the review pack. It does not require Git or network access.

The triage states are:

* `confirmed`
* `unconfirmed`
* `contradicted`

`curbpack review` examines material that has already been prepared for review. It does not re-run the original `curbpack check` against the product repository and it does not replace human judgment.

For additional review modes and flags, see [`../reference/cli.md`](../reference/cli.md).

## 5. Inspect the evidence

For important findings, inspect the referenced evidence and ask:

* Does the evidence actually support the claim or requirement being reviewed?
* Is the evidence current and specific to this product?
* Does the content reflect actual practice, or merely satisfy the structural check?
* Are there contradictions or important facts outside the evidence Curbpack checked?
* Is additional domain, legal, safety, or security review required?

The distinction is:

```text
Curbpack:
Did the identified evidence satisfy the pack rule?

Reviewer:
Is that evidence substantively adequate for the decision being made?
```

## 6. What a green result means

A green result means that the selected Curbpack rules passed for the evaluated repository state.

It does not by itself establish:

* legal compliance,
* certification,
* CE marking,
* notified-body approval,
* regulator or RISE endorsement.

Curbpack prepares review material. The reviewer decides what the evidence means.

## Technical reference

* [`../reference/outputs.md`](../reference/outputs.md)
* [`../reference/cli.md`](../reference/cli.md)
* [`../reference/configuration.md`](../reference/configuration.md)
* [`../concepts/evidence.md`](../concepts/evidence.md)
