# Create a Requirements Pack

A Pack is a reusable collection of Requirements. You can create one from legislation, a standard, a company policy, or another source of requirements.

This guide shows how to create a Pack in Curbpack Studio, review the Requirements, sign them, and export the Pack for use by a product team.

## 1. Open Pack Editor

Start Curbpack Studio and choose the repository where you want to create and maintain the Pack.

This may be a shared repository containing Packs used by several products, or a product repository that maintains its own Packs.

Open **Pack Editor** from the Studio cover page.

## 2. Create a Pack

Create a Pack from source material such as legislation, a standard, or a company policy.

Choose **Add document**.

Enter the information requested by Studio, including:

- a name for the source;
- its official name;
- the source URL;
- the adapter used to read it.

Choose the adapter carefully. The adapter determines how Studio divides that source into candidate Requirements.

## 3. Select the source material

Add the section of the source that you want to work with.

A source can contain more material than is relevant to one Pack. Select the section that contains the Requirements you intend to review and maintain.

## 4. Extract candidate Requirements

Choose **Extract**.

Studio uses the selected adapter to propose candidate Requirements from the source material.

Extraction is assistance, not approval. Every extracted Requirement is a draft until a person has reviewed and signed it.

A failed extraction must not replace Requirements that have already been reviewed and accepted.

## 5. Review each Requirement

Open each candidate in the Requirement editor and check that it accurately represents the source.

Review at least the following:

- **Source passage:** Does `law_text` contain the relevant source passage rather than a summary created during extraction?
- **Derived properties:** Are properties such as `strength` and `applicability` supported by the source passage?
- **Locator:** Does the reference identify the correct article, section, paragraph, annex, or policy provision?
- **Source information:** Are the instrument, edition, language, identifier, and URL correct?
- **Remediation hint:** Would the guidance help a product team understand what may need to change?
- **Discovery hints:** Are the concepts and path hints useful for finding possible evidence in a product repository?

Edit incorrect or unclear fields before signing.

A company policy that was not extracted from legislation is still a Requirement. You can author and review it directly in the Requirement editor.

## 6. Sign the Requirement

When the Requirement correctly represents the source, choose **Sign**.

Signing records that a person has reviewed and approved that Requirement. Extraction does not sign it automatically.

If the signed Requirement is later changed, review and sign the changed version again.

Repeat the review and signing process for every Requirement that should belong to the Pack.

## 7. Review the Pack

Before exporting, inspect the Pack as a whole:

- Does the Pack have a clear name and purpose?
- Does its version identify this release of the Pack?
- Are the intended Requirements present?
- Have the Requirements been reviewed and signed?
- Are source references and editions consistent?
- Are duplicate or obsolete Requirement candidates removed?

The Pack should be understandable without access to the extraction conversation or temporary Studio data.

## 8. Export the Pack

When the Pack is ready, export it from Studio.

The exported Pack can be:

- shared with another team;
- stored in a shared Git repository;
- added to a product repository;
- reviewed and maintained using your organisation's normal procedures.

Exporting the Pack does not determine whether a product fulfils its Requirements. It makes the reviewed Requirements available for products to select and use.

## 9. Use the Pack in a product

The product repository's `curbpack.json` determines which Packs the product uses.

Once the Pack is selected, the product team can use its Requirements when looking for evidence and creating Claims. Claims belong to the product repository, not to the reusable Pack.

Creating, checking, and signing product Claims is covered separately in the product-team guidance.

## Minimal workflow

```text
Choose the repository where the Pack will live
        ↓
Open Pack Editor
        ↓
Add source material
        ↓
Extract candidate Requirements
        ↓
Review the source passages and derived information
        ↓
Sign approved Requirements
        ↓
Review the Pack
        ↓
Export the Pack
        ↓
Select it for a product through curbpack.json
```

## Related documentation

- [Getting Started](getting-started.md) — first walkthrough of Curbpack Studio
- [Packs v2](../reference/packs2.md) — exact Pack and Requirement fields
- [Workspace](../reference/workspace.md) — repository configuration and paths
- [Developer guide](developers.md) — using Curbpack with a product repository
