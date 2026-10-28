# Write a Pack, then the Claims that watch it

A Pack is metadata plus Requirement files. The product repository holds the Claims. Check loads the Pack ids named in that product's `curbpack.json` and evaluates the Claims whose Requirements are selected.

Field names are [Packs v2](../reference/packs2.md). Keys that file does not define are rejected or ignored according to `common/validate.py`. Do not add a key beside the contract and expect Check to honor it.

## 1. Create the Pack

A house policy starts as files under the packs root:

```text
packs/
└── acme-secure-coding/
    ├── pack.json
    └── ACME-SECURITY-MD.json
```

`pack.json` is metadata. Membership is `requirement.pack_id`, not a list inside the Pack file.

```json
{
  "id": "acme-secure-coding",
  "name": "Acme Secure Coding",
  "version": "0.1.0",
  "description": "Structural engineering policy checks."
}
```

`id`, `name`, and `version` are required. `description` is the sentence about which products the instrument covers. `version` is the publisher's label, set by hand. It is not a Git commit and not the legal edition. Optional metadata includes `assurance_class`, `jurisdiction`, `source`, and `signed`. `source.edition` on a Requirement is the legal edition, and it is required when that Requirement is published.

`validity`, `supersedes`, `superseded_by`, `citations`, and `recheck_interval_days` are not Pack fields. A new published release is a new `published/<pack-id>/<version>/` directory. It does not overwrite the previous version.

In Pack Editor this starts as **Add document**. You name the document, the official name, the URL, and the adapter. The adapter cannot be changed later. Saving does not extract. **Add section**, then **Extract**, produces unsigned Requirement candidates in a dated working copy. You review `references[].law_text` and `discovery_hints` before anyone signs. A failed Extract must not replace Requirements you already accepted.

A house policy that is not extracted from a statute is still a Requirement. You edit it in the Requirement editor. Guidance for a person who has to fix the product belongs in `remediation_hint`. The Claim's `description` is a positive statement of what the human reviewed.

## 2. The Requirement

`packs/acme-secure-coding/ACME-SECURITY-MD.json`:

```json
{
  "id": "ACME-SECURITY-MD",
  "pack_id": "acme-secure-coding",
  "remediation_hint": "Add vulnerability reporting and response information.",
  "source": {
    "framework": "example",
    "instrument": "Acme secure coding",
    "identifier": "ACME-SECURITY-MD",
    "language": "en",
    "url": "https://example.invalid/acme-secure-coding"
  },
  "references": [
    {
      "nr": 1,
      "locator": "security-reporting",
      "law_text": "The product describes how to report a vulnerability."
    }
  ]
}
```

Required on every Requirement: `id`, `pack_id`, `source`, and a non-empty `references` list. `source` requires `framework`, `instrument`, `identifier`, `language`, and `url`. `edition` is required when the object is published, and whenever the key is present. Each reference needs an integer `nr` starting at 1 in array order, plus `locator` and `law_text`. `pack_id` must equal `pack.json`'s `id`.

`strength` is `MUST`, `SHOULD`, or `MAY` when you set it. `severity` is not a Requirement field. On a Claim, `severity` is the product's triage label: `high`, `medium`, or `critical`. It is not legal strength.

`discovery_hints` may list `concepts`, `path_hints`, `sources`, and `expected_evidence`. Hints help Discovery. Check does not read them.

## 3. The Claim that watches the file

The Claim lives in the product repository, under `claims/`. One Claim, two questions, same file:

```json
{
  "id": "claim-acme-security-md",
  "requirement_id": "ACME-SECURITY-MD",
  "source": "documents",
  "args": { "path": "SECURITY.md" },
  "description": "The reviewed SECURITY.md describes this product's vulnerability reporting.",
  "severity": "high",
  "checks": [
    { "check": "exist", "args": { "paths": ["SECURITY.md"] } },
    {
      "check": "contents",
      "args": {
        "path": "SECURITY.md",
        "probes": [
          { "kind": "size", "bytes": 80, "op": ">=" },
          { "kind": "words", "n": 20, "op": ">=" },
          { "kind": "headers", "headers": ["# Security"] }
        ]
      }
    }
  ]
}
```

`exist` asks whether each path is a file. `contents` asks whether the bytes match the probes. A missing file fails `contents` too, and the detail says the file is absent. It does not also report a missing header.

`headers` are literal substrings. `size` compares the byte length with `op` and `bytes`. `words` compares the word count with `op` and `n`. `pattern` fails the Check when the regular expression matches. `placeholder` fails when the file matches the list in `checks/run.py`. `token` fails when none of the repository tokens appear in the file.

An unsigned Claim can be evaluated. Signing it is a separate human approval. Editing a signed payload drops `signed`.

## 4. Which Check to use

| Question | Check |
| --- | --- |
| Is the file present? | `exist`, argument `paths` |
| Size, word count, headings, a repository token, a forbidden pattern, or placeholder text | `contents` probes `size`, `words`, `headers`, `token`, `pattern`, `placeholder` |
| How old is the last commit that touched the file? | `git_fresh`: `path`, `max_age_days`, `as_of`. This build runs it. It does not also test presence or headings |
| Who is the recorded author of that commit? | `git_author`, with optional `name` and `email`. This is not a signature. This build runs it |
| Did Git accept a signature on that commit? | `git_signed` |
| Who is the verified signer? | `git_signer` |
| Is a dependency pin forbidden? | `dep_ban`. `npm_dep_ban` and `manifest_dep_ban` are aliases |

`git_signed`, `git_signer`, and `dep_ban` are in `checks/available_checks.json`. This build validates their arguments and then fails the row with the detail that the check is not implemented. The same is true of the registered ids `fresh` and `owned`. A fail of that kind is not a pass. `file_present` and `annex_file` are not registry ids.

Packs v2 §5 shows example Claims for a house policy, a CRA baseline, and a medical-software pack. Those examples are illustrations of shape. They are not a statement that a particular product file is legally adequate.

## 5. Citations

The Requirement `source` holds `framework`, `instrument`, `identifier`, `edition`, `language`, and `url`. Each supporting passage is a `references[]` entry with `nr`, `locator`, and `law_text`. An article or an annex number is the `locator` when that is the passage you mean.

A date on which someone compared the text with a publication belongs in a review `decision` or in your own record. It is not a Requirement field.

For a safety-class note, the Requirement can cite the instrument and the locator, and the Claim can watch a heading the product team chose. The heading is their choice. The instrument did not require that English string. The getting-started exercise uses `## Classification Rationale` on `docs/medtech/software_safety_class.md` for that reason.

## 6. What a pass means

A pass means the arguments held for the bytes that were read.

It does not answer the cited instrument. The review page says so in standing text. The report schema rejects `compliant` and `meets_cra`. There is no flag that turns a structural pass into a legal conclusion, and there is no flag whose absence does that either.

## 7. Several Packs

Listing two ids in `curbpack.json` selects both Packs. It does not merge Requirement files and it does not let one Pack replace fields in the other. Studio does not apply `extends`, `overlays`, or `overlay`.

To carry a provision forward, publish the Requirement in the Pack that owns it, or write a new Requirement that cites the same passage. Do not patch someone else's sealed directory in place.

`exclude_requirements` removes those ids from the selected Packs. The alternative is a `requirements` list, which includes only those ids. One file uses one of those styles, not both.

## 8. Where Check finds the Pack

`curbcheck` loads packs from `<curbpack>/packs/<pack-id>/pack.json`. `--packs` replaces that directory. The value is the directory of `<pack-id>/pack.json`:

```sh
curbcheck --repo /path/to/product --packs /path/to/packs
```

The browser does the same thing with the workspace you started: `packs/` and `product/`. The Pack open in Pack Editor is not that selection. The cover says so on the Check link.

The catalog buttons are **Add**, **Edit**, and **Publish**. Copying a published directory unchanged into a local working copy is specified in the requirements architecture. It is not a control on the current catalog.

## 9. Sign, seal, publish

**Sign** is used when the Requirement has no `origin`. **Approve and sign** is used when the Requirement has `origin`, which means the copy descends from a published Pack. Approval keeps `origin`. It does not publish the publisher's release.

**Seal Pack directory** seals that directory. **Publish release** creates `published/<pack-id>/<version>/` and refuses to overwrite an existing version. The Publish form shows `pack.version` as a read-only field.

A product team can Check a Pack that is already selected without publishing a new version.

## 10. Select the Pack for a product

```json
{
  "packs": ["acme-secure-coding"]
}
```

`packs` lists ids, not versions. The version in use is `version` on the loaded `pack.json`. Nothing fetches a newer publication on its own.

Every Claim under `product/claims/` must name a Requirement in that selection. Otherwise the runner stops with an error and writes no result.

## 11. Run the Checks

Every run evaluates the selected Claims that have Checks. A Claim saved with `checks: []` is omitted from the run. It is not a validation failure.

Exit 0 means at least one Check ran and every row passed. No rows, a fail, or a skip is exit 1. A usage error, including `--skip` without `claim-id=reason`, is exit 2.

You can test an unsigned Claim. Signing is the human approval afterwards, not a precondition for the run.

## 12. Invalid objects

The write boundary rejects, among other things:

* a Pack missing `id` or `version`;
* a Requirement missing `id`, `pack_id`, `source`, or `references`;
* a `source` missing `framework`, `instrument`, `identifier`, `language`, or `url`;
* `references[].nr` that is not `1, 2, 3, …` in array order;
* a `pack_id` that does not match the Pack directory;
* unknown keys on the object;
* a Check id absent from `checks/available_checks.json`;
* Check arguments that fail that id's schema;
* a path that escapes the repository.

A registered id with no in-process implementation does not pass. Unknown keys on a review report are rejected, including `compliant` and `meets_cra`. The messages come from `common/validate.py` and the Check runner.

## Minimal workflow

```text
Pack Editor: Add document, Add section, Extract
        ↓
review the candidate, edit, Sign or Approve and sign
        ↓
product curbpack.json names the Pack id
        ↓
Discovery, then save a Claim with checks[]
        ↓
curbcheck --repo ...
        ↓
read the rows, change the product or the Claim, run again
```

## Related reference

* [Packs v2](../reference/packs2.md)
* [Packs](../concepts/packs.md)
* [Getting started](getting-started.md) — the same two-Check shape on Glucose Log
