# Pack reference

A Curbpack pack is a versioned JSON definition containing metadata and a set of `rules`. Each rule selects one supported `check` and declares which repository evidence that check examines. Selected packs can be composed through `extends` and `overlays`; Curbpack evaluates the resulting rules against the current repository and reports the result.

Pack citations and `settlement` describe the meaning and source of a rule, but a passing structural check is evidence for human review, not a conformity or certification claim.

The separate `claim` field in `.curbpack.json` is repository configuration. There is no `claims` array or claim object in `pack.json`.

## Pack file

A pack is stored as:

```text
<pack-id>/pack.json
```

Example:

```json
{
  "id": "acme-secure-coding",
  "name": "Acme Secure Coding",
  "version": "0.1.0",
  "assurance_class": "structural_draft",
  "description": "Structural engineering policy checks.",
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

## Pack fields

| Field                   | JSON type         |       Required | Meaning                                  |
| ----------------------- | ----------------- | -------------: | ---------------------------------------- |
| `id`                    | `string`          |            Yes | Pack identifier                          |
| `name`                  | `string`          |            Yes | Human-readable pack name                 |
| `version`               | `string`          |            Yes | Pack version                             |
| `description`           | `string`          |             No | Pack description                         |
| `assurance_class`       | `string`          |            No* | Pack-authored assurance classification   |
| `extends`               | `string`          |             No | Base pack ID                             |
| `overlays`              | `array<string>`   |             No | Additional pack IDs to compose           |
| `overlay`               | JSON object       |             No | RFC 7386 merge patch applied to the pack |
| `jurisdiction`          | `string`          |             No | Pack jurisdiction metadata               |
| `validity`              | `object`          |             No | Pack effective-date window               |
| `supersedes`            | `string`          |             No | Pack superseded by this version          |
| `superseded_by`         | `string`          |             No | Pack that supersedes this one            |
| `citations`             | `array<Citation>` |             No | Pack-level citations                     |
| `recheck_interval_days` | `integer`         |             No | Author-defined citation recheck interval |
| `rules`                 | `array<Rule>`     | Yes, non-empty | Rules evaluated by Curbpack              |

`assurance_class` is not required by normal pack validation, but `curbpack packs import` requires it for imported packs.

### `validity`

```json
{
  "effective_from": "2026-01-01",
  "effective_to": "2027-12-31"
}
```

Both fields are optional strings. Dates may use `YYYY-MM-DD` or RFC3339 format. An inverted date window is rejected.

## Rule fields

Each entry in `rules` has this shape:

| Field                      | JSON type         |                  Required | Meaning                                                          |
| -------------------------- | ----------------- | ------------------------: | ---------------------------------------------------------------- |
| `id`                       | `string`          |                       Yes | Rule identifier; unique within the pack                          |
| `severity`                 | `string`          |                       Yes | Severity label                                                   |
| `type`                     | `string`          | No validation requirement | Rule type label                                                  |
| `check`                    | `string`          |                       Yes | Evaluator check kind                                             |
| `path`                     | `string`          |           Check-dependent | Single repository-relative path                                  |
| `paths`                    | `array<string>`   |           Check-dependent | Multiple repository-relative paths                               |
| `min_bytes`                | `integer`         |                        No | Minimum file size                                                |
| `min_words`                | `integer`         |                        No | Minimum word count                                               |
| `require_headers`          | `array<string>`   |                        No | Required file headings                                           |
| `bind_repo_token`          | `boolean`         |                        No | Require content to contain a resolvable repository/product token |
| `require_tree_paths`       | `array<string>`   |                        No | Repository-relative paths that must exist                        |
| `package`                  | `string`          |           Check-dependent | Dependency package name                                          |
| `banned_versions`          | `array<string>`   |           Check-dependent | Versions refused by dependency checks                            |
| `pattern`                  | `string`          |           Check-dependent | Regular expression used by `text_forbid`                         |
| `max_age_days`             | `integer`         |           Check-dependent | Maximum permitted age for `fresh`                                |
| `since_ref`                | `string`          |           Check-dependent | Git reference used by `fresh`                                    |
| `require_git_author_email` | `string`          |                        No | Required author email for `owned`                                |
| `require_git_author_name`  | `string`          |                        No | Required author name for `owned`                                 |
| `description`              | `string`          |                       Yes | Description of the finding                                       |
| `remediation`              | `string`          | No validation requirement | Suggested remediation text                                       |
| `expected`                 | `string`          | No validation requirement | Expected-state text                                              |
| `settlement`               | `string`          |                 Sometimes | `settles` or `indicative`                                        |
| `citations`                | `array<Citation>` |                        No | Rule-level citations                                             |

All repository paths are validated as jailed relative paths.

## Supported checks

The current evaluator supports eight check kinds.

### `file_present`

Checks one file for presence and optional structural requirements.

Required:

```json
{
  "check": "file_present",
  "path": "SECURITY.md"
}
```

Optional fields:

```text
min_bytes
min_words
require_headers
bind_repo_token
require_tree_paths
```

Example:

```json
{
  "id": "HOUSE-SECURITY-MD",
  "severity": "high",
  "type": "POLICY_VIOLATION",
  "check": "file_present",
  "path": "SECURITY.md",
  "min_bytes": 80,
  "min_words": 20,
  "require_headers": [
    "# Security"
  ],
  "description": "SECURITY.md missing, too short, or lacking required header.",
  "remediation": "Add SECURITY.md with vulnerability reporting and response expectations.",
  "expected": "SECURITY.md present with Security header and substantive content."
}
```

### `annex_file`

Uses the same path and structural fields as `file_present`.

Required:

```json
{
  "check": "annex_file",
  "path": "docs/example.md"
}
```

Example from the current MedTech pack:

```json
{
  "id": "MD-SW-CLASS",
  "severity": "high",
  "type": "POLICY_VIOLATION",
  "check": "annex_file",
  "path": "docs/medtech/software_safety_class.md",
  "min_bytes": 100,
  "require_headers": [
    "# Software Safety Class",
    "## Classification Rationale"
  ],
  "description": "IEC 62304 software safety classification
```
