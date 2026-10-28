Temporary maintainer note. Delete `docs/development/` when this crosswalk is no longer needed. The user guide is [Pack authors](../user-guides/pack-developers.md).

# Write a Pack, then the Claims that watch it

The old pack was one `pack.json` whose `rules` array was what `curbpack check` evaluated. You wrote it when the organisation needed a check the packs you already had did not contain. The field list lived in `reference/packs.md`.

Studio stores a Pack and a Requirement as Packs v2 describes them. The product stores the Claim. The examples below keep the old JSON so the mapping stays checkable, then show the objects Studio actually persists. Field names that are not in [Packs v2](../reference/packs2.md) are not quietly reused.

## 1. Create the Pack

The old tree was:

```text
packs/
└── acme-secure-coding/
    └── pack.json
```

with the rules inline:

```json
{
  "id": "acme-secure-coding",
  "name": "Acme Secure Coding",
  "version": "0.1.0",
  "assurance_class": "structural_draft",
  "description": "Structural engineering policy checks.",
  "jurisdiction": "internal",
  "rules": [
    {
      "id": "ACME-SECURITY-MD",
      "severity": "high",
      "type": "POLICY_VIOLATION",
      "check": "file_present",
      "path": "SECURITY.md",
      "min_bytes": 80,
      "min_words": 20,
      "require_headers": ["# Security"],
      "description": "SECURITY.md missing or too thin.",
      "remediation": "Add vulnerability reporting and response information.",
      "expected": "SECURITY.md present with required content."
    }
  ]
}
```

**Changed.** `rules` is not a field of `pack.json`. Membership is `requirement.pack_id`. The Pack file is metadata: `id`, `name`, `version`, `description`, and optionally `assurance_class`, `jurisdiction`, `source`, and `signed`. `version` is the publisher's label, set by hand.

In Pack Editor this starts as **Add document**, not as a hand-written rules file. You name the document, the official name, the URL, and the adapter. Saving does not extract. **Add section**, then **Extract**, produces unsigned Requirement candidates in a dated working copy. You review `references[].law_text` and `discovery_hints` before anyone signs.

A house policy that is not extracted from a statute is still a Requirement. You edit it in the Requirement editor. The old rule's `remediation` text belongs in `remediation_hint`. The old `description` of the failure belongs in the Claim's `description`, as a positive statement of what the human reviewed, not as an error string.

`severity` and `type` are not Requirement fields. `severity` on a Claim is the product's triage label (`high`, `medium`, or `critical`). It is not legal `strength`.

The file-present rule becomes two Checks on one Claim, in the product repository, after a Requirement exists:

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

`file_present` is not a Check id. `min_bytes` is a `size` probe. `min_words` is a `words` probe. `require_headers` is a `headers` probe of literal substrings. `expected` is not a Claim field.

## 2. Where each old check went

The CLI supported eight check types on the rule. The questions are still the questions. The ids and the place they are stored have changed.

| Old check | What it asked | Studio |
| --- | --- | --- |
| `file_present` | File present, and optionally size, words, headers, a repo token, extra paths | `exist` for presence. `contents` probes `size`, `words`, `headers`, `token` for the rest. Not one bag of fields. |
| `annex_file` | Same structural options, used for an annex document | The same pair of Checks. It was an alias of `file_present` and is not a Check id. |
| `anti_placeholder` | Placeholder text | `contents` probe `placeholder`. The patterns are the list in `checks/run.py`. |
| `text_forbid` | A regular expression that must not match | `contents` probe `pattern`. The Check fails when the expression matches. |
| `npm_dep_ban` | A banned npm version | `dep_ban`. The name `npm_dep_ban` is an alias. Specified. This build does not execute it as a pass. |
| `manifest_dep_ban` | A banned manifest version | Alias of `dep_ban`. Same limitation. |
| `fresh` | A freshness condition | `git_fresh`, with `path`, `max_age_days`, and `as_of`. The id `fresh` is not a Check id. Specified in Packs v2 §4.1. |
| `owned` | Path bound to the repository, optionally to a Git author | `git_author` for the recorded author. `git_signed` and `git_signer` for signature questions. `owned` is not a Check id. |

`bind_repo_token: true` is the `token` probe. `require_tree_paths` is more paths on `exist` or `contents`, not a separate flag. `require_git_author_email` and `require_git_author_name` are `name` and `email` on `git_author`. They compare to the author of the last commit that touched the path. They do not verify a signature.

Packs v2 §5 rewrites the house-policy, cra-baseline, and medtech-iec62304 rules as example Claims. Those examples are illustrations, not a statement that the reference files are legally adequate.

## 3. Pack metadata that moved or stopped

The old pack also allowed:

```text
validity.effective_from / validity.effective_to
supersedes / superseded_by
citations
recheck_interval_days
```

A validity object accepted `YYYY-MM-DD` or RFC3339 and rejected an inverted range. `assurance_class` was optional until `curbpack packs import`, which required it.

**Changed.** Packs v2 §2.1 does not define `validity`, `supersedes`, `superseded_by`, `citations`, or `recheck_interval_days` on `pack.json`. Do not add them beside the contract and expect Check to honor them. The legal edition is `source.edition` on the Requirement. A new published release is a new `published/<pack-id>/<version>/` directory. It does not overwrite the previous version. That is the successor relationship the publisher gets. There is no `supersedes` field.

`assurance_class` remains an optional metadata field in the Pack example, including `structural_draft`. Studio's import of a published directory copies those bytes and checks the seals the publication contract requires. Do not carry over the v1 rule that import fails closed on a missing `assurance_class` unless the validator you are running rejects it. `common/validate.py` is that validator.

## 4. Citations

A citation used to sit on the pack or on the rule:

```json
{
  "citations": [
    {
      "framework": "IEC",
      "instrument": "IEC 62304",
      "article": "4.3",
      "edition": "2026",
      "verified_on": "2026-09-01"
    }
  ]
}
```

The allowed citation fields were `framework`, `instrument`, `article`, `annex`, `url`, `effective_from`, `effective_to`, `edition`, `verified_against`, `verified_on`, `edition_pinned`. Date ranges were validated. A citation did not turn a passing check into a legal conclusion.

**Changed.** The Requirement `source` holds `framework`, `instrument`, `identifier`, `edition`, `language`, and `url`. Each supporting passage is a `references[]` entry with `nr`, `locator`, and `law_text`. `article` and `annex` become the `locator` when that is the passage you mean. `verified_on`, `verified_against`, and `edition_pinned` are not Requirement fields. If someone verified the text on a date, that fact belongs in a review `decision` or in your own record, not in an invented key.

## 5. What a pass means

Rules carried `settlement`: `settles` or `indicative`. Omitted, it defaulted to `settles`. A citation with a non-empty `framework` forced `settlement` to be explicit. The medtech example was:

```json
{
  "id": "MD-SW-CLASS",
  "severity": "high",
  "check": "annex_file",
  "path": "docs/medtech/software_safety_class.md",
  "description": "Software safety classification rationale missing.",
  "settlement": "indicative",
  "citations": [
    { "framework": "IEC", "instrument": "IEC 62304", "article": "4.3" }
  ]
}
```

`indicative` meant the file had the expected structure and the check did not answer the cited instrument.

**Changed.** `settlement` is not a field. The indicative reading is mandatory for every pass, cited or not. The review page says so in standing text, and the report schema rejects `compliant` and `meets_cra`. You do not get a stricter rule by omitting a flag, and you do not get a legal conclusion by setting one.

The same example, as objects Studio can store, is a Requirement whose `source.instrument` is IEC 62304 and whose `locator` is `4.3`, plus a Claim whose `contents` probe names `## Classification Rationale` if that heading is what the product team chose to watch. The heading is their choice. The standard did not require that English string.

## 6. Building on another Pack

`extends` loaded a base pack first. `medtech-iec62304` extended `cra-baseline`. `overlays` was an ordered list of additional packs. `overlay` was an RFC 7386 merge patch. Composition order was extends, then overlays, then the pack, then the patch. Rules merged by id. A later id replaced an earlier one. Cycles were rejected. Repeated sources were deduplicated.

**Changed.** None of `extends`, `overlays`, or `overlay` is applied. Listing `cra-baseline` and another Pack id in `curbpack.json` selects both. It does not merge Requirement files and it does not let a later id replace an earlier one. A `requires` Check that merely looks for a Pack id in `curbpack.json` is an idea in `docs/agile/DECISIONS.md`. It is not implemented, and a pass on it would still not be compliance.

To carry a provision forward, publish the Requirement in the Pack that owns it, or write a new Requirement that cites the same passage. Do not patch someone else's sealed directory in place.

## 7. Make the Pack visible

Local development used to be:

```bash
export CURBPACK_PACKS_DIR="$PWD/packs"
curbpack packs list
curbpack packs doctor
curbpack packs export-graph
```

Embedded packs shipped inside the CLI.

**Changed.** There is no `CURBPACK_PACKS_DIR` and no `packs doctor` or `export-graph`. Pack Editor lists the editable Packs in the workspace. `curbcheck` loads `<curbpack>/packs/<pack-id>/pack.json`. `--packs` replaces that directory:

```sh
curbcheck --repo /path/to/product --packs /path/to/packs
```

A missing Pack directory is an error, and the runner writes nothing.

## 8. Import

`curbpack packs import ./bundle-dir` validated a bundle and required `assurance_class`. Editing under `CURBPACK_PACKS_DIR` was the faster loop because the next `curbpack check` reread `pack.json`.

**Changed.** The catalog buttons are **Add**, **Edit**, and **Publish**. There is no button labeled Import, and there is no `CURBPACK_PACKS_DIR` reload loop.

The requirements architecture specifies a separate import: copy a published Pack directory byte for byte, refuse different bytes at the same id and version, and do not set `origin`. That operation is not a control on the current catalog. Do not invent the click path.

What the screen does have is a dated working copy. **Extract** allocates one. **Publish** on a copy whose Requirements have no `origin` runs **Seal Pack directory** and **Publish release**. Publish release refuses an existing version. The form shows `pack.version` read-only. A Requirement that already has `origin` uses **Approve and sign**. That keeps `origin` and does not create `published/<pack-id>/<version>/`.

## 9. Select the Pack for a product

`curbpack init --packs acme-secure-coding` wrote `.curbpack.json`. If the pack extended other packs, those rules were included at check time.

```json
{
  "packs": ["acme-secure-coding"]
}
```

**Changed.** The file name is `curbpack.json`. The `packs` array is still a list of ids, and it still does not list versions. The version is `version` on the loaded `pack.json`. Extended packs are not pulled in. Add an id only when that Pack should be evaluated.

`exclude_requirements` or `requirements` narrows which Requirement ids run. Hunt globs live in the same file. See Packs v2 §2.3.

## 10. Run the Checks

`curbpack check` resolved the selected pack, loaded dependencies, validated definitions, composed rules, and evaluated them.

The Studio runner loads the selected Pack directories, loads Claim files under `<curbpack>/claims/`, skips Claims with an empty `checks` array, and writes one run result. A Claim whose `requirement_id` is not selected is an error and writes nothing. A selected Requirement with no executed Claim produces no row.

```sh
curbcheck --repo /path/to/product
```

Exit 0 only when at least one Check ran and every row passed. Then change the evidence or the Claim and run it again. A pass means the arguments held for that tree. It does not certify the product.

You can test an unsigned Claim. Signing is the human approval afterwards, not a precondition for the run.

## 11. Invalid objects

The old loader rejected, and did not skip:

* missing pack `id`, `name`, or `version`;
* an empty `rules` array;
* duplicate rule ids;
* a rule missing `id`, `check`, `severity`, or `description`;
* an unsupported check type;
* missing fields required by a check;
* an unsafe repository-relative path;
* an invalid `text_forbid` expression;
* an invalid date range;
* an invalid `settlement`;
* a framework citation without explicit `settlement`;
* an unknown pack dependency;
* a composition cycle.

**Changed.** Several of those keys do not exist, so the rejection cannot exist either. An empty `rules` array is not a Packs v2 condition. A Claim with `checks: []` is a saved proposal. It is omitted from the run. It is not a validation failure.

What Studio does reject, at the write boundary, includes a Check id absent from `available_checks.json`, Check arguments that fail that id's schema, and a path that escapes the repository. A registered id with no in-process implementation does not pass. It is not silently treated as success. Unknown keys on a review report are rejected. The precise messages come from `common/validate.py` and the Check runner, not from the list above.

## 12. Incremental check

`curbpack check --diff` (alias `--delta`) limited evaluation to changed files, except `file_present` and `annex_file`, which still ran. The result was not a substitute for a full check before review or release.

**Changed.** There is no `--diff`. Every run evaluates the selected Claims that have Checks. That is the full check for the selection in `curbpack.json`.

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

Seal and Publish release when you are the publisher and the Requirements have no `origin`. A product team can Check a Pack that is already selected without publishing a new version.

## Related reference

* [Packs v2](../reference/packs2.md)
* [Packs](../concepts/packs.md)
* [CLI disposition](cli.md)
