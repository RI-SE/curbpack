# Write your own pack

A Curbpack pack is a versioned JSON file containing rules that Curbpack evaluates against a repository.

Create your own pack when you need project- or organization-specific checks that are not already covered by the packs available to you.

This guide shows the normal authoring workflow. For the complete field definitions, see [`../reference/packs.md`](../reference/packs.md).

## 1. Create the pack

Create a directory named after the pack and add a `pack.json` file:

```text
packs/
└── acme-secure-coding/
    └── pack.json
```

A small pack might look like this:

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
      "require_headers": [
        "# Security"
      ],
      "description": "SECURITY.md missing or too thin.",
      "remediation": "Add vulnerability reporting and response information.",
      "expected": "SECURITY.md present with required content."
    }
  ]
}
```

The pack contains metadata followed by a non-empty `rules` array.

The example rule checks that `SECURITY.md` exists and satisfies the configured structural requirements.

## 2. Add rules

Each rule selects one supported `check`.

Curbpack currently supports eight check types:

| Check              | What it checks                                                           |
| ------------------ | ------------------------------------------------------------------------ |
| `file_present`     | A required file and optional structural requirements                     |
| `annex_file`       | A required document with the same structural options as `file_present`   |
| `anti_placeholder` | Placeholder text in one or more files                                    |
| `text_forbid`      | Text matching a configured regular expression                            |
| `npm_dep_ban`      | Prohibited npm dependency versions                                       |
| `manifest_dep_ban` | Prohibited dependency versions                                           |
| `fresh`            | Whether a file satisfies a configured freshness condition                |
| `owned`            | Whether a file is bound to the repository and optionally to a Git author |

A rule normally contains:

```text
id
severity
check
description
```

The selected check then determines which additional fields are required.

For example, a simple file check is:

```json
{
  "id": "ACME-SECURITY-MD",
  "severity": "high",
  "type": "POLICY_VIOLATION",
  "check": "file_present",
  "path": "SECURITY.md",
  "min_bytes": 80,
  "min_words": 20,
  "require_headers": [
    "# Security"
  ],
  "description": "SECURITY.md missing or too thin.",
  "remediation": "Add vulnerability reporting and response information.",
  "expected": "SECURITY.md present with required content."
}
```

`file_present` and `annex_file` can also use:

```text
bind_repo_token
require_tree_paths
```

`owned` requires:

```text
path
bind_repo_token: true
```

and can additionally constrain:

```text
require_git_author_email
require_git_author_name
```

For all fields supported by each check, see [`../reference/packs.md`](../reference/packs.md).

## 3. Add pack metadata when needed

A pack can contain additional metadata such as:

```text
description
assurance_class
jurisdiction
validity
supersedes
superseded_by
citations
recheck_interval_days
```

For example, a pack can declare an effective date range:

```json
{
  "validity": {
    "effective_from": "2026-01-01",
    "effective_to": "2027-12-31"
  }
}
```

Both dates are optional. Curbpack accepts `YYYY-MM-DD` and RFC3339 values and rejects an inverted date range.

`assurance_class` is optional during normal pack validation but is required when a pack is added with `curbpack packs import`.

## 4. Add citations when useful

Citations can be attached to the whole pack or to an individual rule.

For example:

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

A citation can contain:

```text
framework
instrument
article
annex
url
effective_from
effective_to
edition
verified_against
verified_on
edition_pinned
```

Citation date ranges are validated.

Citations record the source associated with a pack or rule. They do not turn a passing Curbpack check into a legal or regulatory conclusion.

## 5. Decide what a passing rule means

Rules can use the `settlement` field:

```text
settles
indicative
```

If `settlement` is omitted, its effective value is `settles`.

When a rule contains a citation with a non-empty `framework`, however, `settlement` must be specified explicitly.

For example:

```json
{
  "id": "MD-SW-CLASS",
  "severity": "high",
  "check": "annex_file",
  "path": "docs/medtech/software_safety_class.md",
  "description": "Software safety classification rationale missing.",
  "settlement": "indicative",
  "citations": [
    {
      "framework": "IEC",
      "instrument": "IEC 62304",
      "article": "4.3"
    }
  ]
}
```

Use `indicative` when the repository contains the expected structural evidence but passing the check does not by itself answer the broader question represented by the cited framework.

This distinction is important for checks that can determine whether evidence exists or has the expected structure, but cannot determine whether every statement in that evidence is substantively correct.

## 6. Build on another pack

A pack can reuse rules from other packs.

### Extend one pack

Use `extends` to load a base pack first:

```json
{
  "id": "acme-medtech",
  "name": "Acme MedTech",
  "version": "0.1.0",
  "extends": "cra-baseline",
  "rules": [
    ...
  ]
}
```

The current `medtech-iec62304` pack uses this mechanism to extend `cra-baseline`.

### Add several packs

Use `overlays` for an ordered list of additional packs:

```json
{
  "overlays": [
    "pack-a",
    "pack-b"
  ]
}
```

### Modify the composed pack

The `overlay` field contains an RFC 7386 merge patch applied to the pack object:

```json
{
  "overlay": {
    "jurisdiction": "internal"
  }
}
```

### Composition order

Curbpack composes a pack in this order:

1. `extends`;
2. entries from `overlays`;
3. the requested pack;
4. the pack's `overlay` merge patch.

Rules are then merged by rule ID.

If the same rule ID occurs more than once, the later-loaded rule replaces the earlier rule.

Repeated pack sources are deduplicated, and `extends` cycles are rejected.

Be deliberate when choosing rule IDs, especially when composing packs.

## 7. Make the pack available to Curbpack

For local development, point `CURBPACK_PACKS_DIR` at the parent directory containing your packs:

```bash
export CURBPACK_PACKS_DIR="$PWD/packs"
```

with a structure such as:

```text
packs/
└── acme-secure-coding/
    └── pack.json
```

You can now list the packs Curbpack can see:

```bash
curbpack packs list
```

Inspect pack loading and composition with:

```bash
curbpack packs doctor
```

You can also export the composed pack graph:

```bash
curbpack packs export-graph
```

Curbpack also includes built-in embedded packs.

## 8. Import a pack

A local pack bundle can be imported with:

```bash
curbpack packs import ./bundle-dir
```

Imported packs are validated before they are accepted.

An imported pack must specify `assurance_class`.

For pack development, using `CURBPACK_PACKS_DIR` is often simpler because you can edit the local `pack.json` and immediately run the checks again.

## 9. Select the pack

Select the pack when initializing a product repository:

```bash
curbpack init --packs acme-secure-coding
```

or record the selected pack in `.curbpack.json`:

```json
{
  "packs": [
    "acme-secure-coding"
  ]
}
```

If the pack extends or overlays other packs, those are included when Curbpack composes the selected pack.

## 10. Run the checks

Run:

```bash
curbpack check
```

Curbpack:

1. resolves the selected pack;
2. loads its dependencies;
3. validates the pack definitions;
4. composes their rules;
5. evaluates those rules against the repository.

If a rule fails, update either the product evidence or the pack definition as appropriate and run:

```bash
curbpack check
```

again.

A passing rule means that the implemented check passed against the repository state that was evaluated.

It does not by itself establish certification, regulatory conformity, or the truth of a broader substantive claim.

## 11. Fix invalid packs

Packs are validated when loaded.

Validation rejects, among other things:

* missing pack `id`, `name`, or `version`;
* an empty `rules` array;
* duplicate rule IDs within a pack;
* missing rule `id`, `check`, `severity`, or `description`;
* unsupported check types;
* missing fields required by a check;
* invalid or unsafe repository-relative paths;
* invalid `text_forbid` regular expressions;
* invalid date ranges;
* invalid `settlement` values;
* framework-cited rules without explicit `settlement`;
* unknown pack dependencies;
* invalid composition cycles.

Invalid packs fail loading rather than being silently skipped.

Correct the pack definition and run the command again.

## 12. Use `--diff` only for local incremental checks

During development you can use:

```bash
curbpack check --diff
```

to limit evaluation based on changed files.

Some checks, including `file_present` and `annex_file`, are still evaluated regardless of the changed-file set.

`--diff` is an incremental mode. Do not use its result as a substitute for a full repository check when preparing release or review material.

Run:

```bash
curbpack check
```

for the complete repository check.

## Minimal workflow

A complete local authoring workflow can be as small as:

```bash
mkdir -p packs/acme-secure-coding

# create packs/acme-secure-coding/pack.json

export CURBPACK_PACKS_DIR="$PWD/packs"

curbpack packs list
curbpack packs doctor

curbpack init --packs acme-secure-coding
curbpack check
```

Then edit the pack or product evidence and run `curbpack check` again.

## Related reference

For exact syntax and supported fields, see:

* [`../reference/packs.md`](../reference/packs.md)
* [`../reference/configuration.md`](../reference/configuration.md)
* [`../reference/cli.md`](../reference/cli.md)
