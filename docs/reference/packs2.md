# Packs v2 (design sketch)

**Status:** design intent — implementation follows.
Imported from Curbpack commit `b07b8deb9fed331b493241251087ce7ce648f5e4`. The former companion `packs.md` (v1) and `dataflow.md` are historical references, not Studio specifications.

**Names — curbpack is the ecosystem; products stand alone**

| Product | Form | Job |
|---------|------|-----|
| **curbpack** | brand / format / trust | Packs, requirements, claims, `curbpack.json` |
| **Requirements** | CLI + UI | Extract/import Requirements; human review, edit and seal |
| **curbpack-claims** | CLI + UI | Discover evidence; configure, maintain and sign Claims with `checks[]` |
| **curbpack-scaffold** | UI | Bootstrap stubs / layout for remaining gaps |
| **curbcheck** | CLI | Evaluate claims read-only (stdout + exit code) |
| **curbpack-compile** | CLI | Build reports / share artefacts |
| **curbpack-review** | UI | Review received packs / evidence |

Shared data model below; each product owns its UX. **Discover** is a mode inside `curbpack-claims` (first bind + later re-hunt), not a separate product.

---

## 1. Layers

```text
PACK/                          # directory sealed by the pack seal; each requirement is sealed too
  pack.json
  <requirement files>          # one or more files. Grouping is packaging, not the model.

CLAIMS/                        # product-owned Claim files, one JSON format
  <claim files>                 # unchecked proposals can be saved, but not published

available_checks.json           # Check definitions: id, CLI tool, args JSON Schema
curbcheck                       # evaluates configured Checks in Claim files
```


| Layer                    | Owner                        | Mutable after sign?      | Role                                                |
| ------------------------ | ---------------------------- | ------------------------ | --------------------------------------------------- |
| **Pack + requirements**  | Expert / pack publisher      | No (new version instead) | **What** must hold, including `discovery_hints`. A local working copy is a separate payload. It is a draft until it is approved and sealed. |
| **Repo `curbpack.json`** | Product repo                 | Yes                      | Packs + shared `hunt` scope (all packs)             |
| **Claims**               | Product repo / human reviewer | Yes (repo-owned; editing invalidates the seal) | Evidence, human rationale and zero or more configured Checks |
| **Check definitions**    | curbcheck (or plugins)       | Tool release             | **How** to evaluate `args`                            |


**v2** splits pack, claim, and check; repo `curbpack.json` holds shared hunt.

The product team chooses a published collection by pack id. The version they are using is `version` on the local `pack.json` for that id. That file is what Curbpack already loads (embedded pack, or a directory such as an air-gapped import). A content hash checks those bytes. It is not the version number.

---

## 2. Core structs

### 2.1 Pack

Pack is **metadata only**. Membership is `requirement.pack_id → pack.id`.

```json
{
  "id": "house-policy",
  "name": "House Policy Example",
  "version": "0.1.0",
  "assurance_class": "structural_draft",
  "description": "…",
  "jurisdiction": "EU",
  "source": {
    "framework": "EU",
    "instrument": "house policy",
    "url": "…"
  },
  "signed": {
    "at": "2026-10-01T08:00:00Z",
    "name": "Daniel Flodin",
    "signature": "<base64>"
  }
}
```

On disk, requirements live **under** the pack directory for packaging; the **relational** link is `pack_id` on the requirement.

`version` is the publisher's version number, set by hand, for example `1.0.0`. It is not a Git commit and not a content hash. It is not the legal edition. That is `source.edition` on the requirement. A tag or a content hash can identify the bytes of a fetched tree. Neither one is this version number.

The pack `signed.signature` seals the **entire pack directory** (every file under it, canonical path order + content hashes). Add, remove, or rewrite any file and the pack check fails.

Which products an instrument covers is the pack `description`, written once. CRA covering products with digital elements is that sentence. There is no separate field for it. It is not copied onto every requirement. A requirement's own `applicability` is only the "where" clause in that requirement's `law_text`.

---

### 2.2 Requirement

Policy identity + **`pack_id`** (FK). `discovery_hints` is part of this object (§2.7). `origin` is omitted on the publisher's requirement.

The Check definitions own their args schemas. A Claim contains `checks[]`, each entry holding `check` and `args`. Who may hold the signing key is the company's choice. The seal reports the name whose certificate verifies.

```json
{
  "id": "CRA-ANNEX-VII-RISK",
  "pack_id": "cra-baseline",
  "remediation_hint": "Populate a product-specific risk assessment (no placeholders).",
  "source": {
    "framework": "EU",
    "instrument": "CRA",
    "identifier": "CELEX:32024R2847",
    "edition": "2024-11-20",
    "language": "en",
    "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847"
  },
  "references": [
    {
      "nr": 1,
      "locator": "VII.3",
      "law_text": "an assessment of the cybersecurity risks against which the product with digital elements is designed, developed, produced, delivered and maintained pursuant to Article 13…"
    }
  ],
  "discovery_hints": {
    "concepts": [
      "risk assessment",
      "cybersecurity risk",
      "threat model",
      "identified risks",
      "residual risk"
    ],
    "path_hints": [
      "*risk*assessment*",
      "*threat*model*",
      "*CRA*ASSESSMENT*",
      "*THREAT*"
    ],
    "sources": [
      { "source": "documents" },
      { "source": "git" }
    ],
    "expected_evidence": ["process description", "requirement"]
  },
  "signed": {
    "at": "2026-10-01T08:00:00Z",
    "name": "Daniel Flodin",
    "signature": "<base64>"
  }
}
```

| Field | Role |
|-------|------|
| `id` | Stable requirement id |
| `pack_id` | FK → pack |
| `strength` | `MUST`, `SHOULD`, or `MAY`, only when that word is pointable in a `law_text` on this requirement. CRA "shall" is `MUST`. Omit the key otherwise. |
| `responsible` | Who the duty names, only when that party is pointable in a `law_text` on this requirement. Omit the key otherwise. |
| `applicability` | The "where" clause in a `law_text` on this requirement (Annex VII 1(c): where the product is hardware). Omit the key otherwise. Not 24765 `condition`. Not `note`. |
| `exceptions` | The exception written in a `law_text` on this requirement. Omit the key otherwise. |
| `scope` | The enumeration written in a `law_text` on this requirement (Article 13(3)'s list of what the assessment comprises). Omit the key otherwise. |
| `remediation_hint` | Publisher advice. Part of the requirement version and seal. A changed hint is a new version. |
| `source.identifier` | Act id the human looked up, e.g. `CELEX:32024R2847`. Not a semver. Not `pack.version`. |
| `source.edition` | The point in time the human looked up (OJ date or later consolidation date). Part of the seal. |
| `source.language` | Language of `law_text`. One value for the requirement. Needed when `url` does not say it. |
| `source.url` | The one address the passages were cut from. Every reference in the requirement shares it, so it is not repeated on `references[]`. EUR-Lex text view or, for the OJ publication, the ELI `…/oj/eng` url. |
| `references[]` | One or more passages from that same source. Another CELEX is another requirement. All of them are in `source.language`. |
| `references[].nr` | Sequence number on this requirement, starting at 1, unique, in the same order as the array. Not the article number. |
| `references[].locator` | Address inside the instrument, e.g. `13(4)`, `VII.3`. |
| `references[].law_text` | Verbatim passage. The requirement's meaning is this text plus the properties extracted from it. |
| `note` | Optional human comment. Omit the key when there is nothing to say. `check` does not read it. Not a second law text, and not `applicability`. |
| `discovery_hints` | Candidate-discovery hints. Part of the signed payload. See §2.7. `check` does not read them. |
| `origin` | Optional. Omit on the publisher's requirement. Set when a local working copy is created from a published version, not when `discovery_hints` is later edited. `pack` and `version` name that published version. Included in the digest. Change `version` only when a newer published version is actually taken in and accepted. |
| `origin.pack` | Id of the published pack, the same id as `pack.id`. |
| `origin.version` | That pack's `version` at the release that was taken in. Not a Git commit and not a content hash. |
| `signed` | Required on a published requirement. Omitted on a local draft. Present when an approved local version uses this seal. The publisher's signature verifies only the publisher's bytes. See §2.6. |

There is no `description` and no `expected` on the requirement. The meaning is `law_text` and the properties extracted from it. "Draft suitable for human review" is not a requirement field. There is no `severity` on the requirement. There is no `statement`, no `limitations`, and no `mandatory` or `verification` flag. There is no `source_digest`.

`strength`, `responsible`, `applicability`, `exceptions`, and `scope` are omitted when the words are not in a `law_text` on this requirement. The Annex VII risk passage does not contain "shall"; that word sits in the annex introduction and in Article 13, so this example has no `strength`.

`signed` is required on a published requirement. The publisher's requirement has no `origin`. Fetching that pack verifies those bytes and does not add `origin`. Creating a local working copy sets `origin` immediately and leaves the fetched pack unchanged. The copy is an unsigned draft. Adding `origin` changes the payload, so the publisher's signature does not cover the draft. Copying does not approve it. When someone approves the draft, that version is sealed and is then an approved requirement version. A later edit, including `discovery_hints`, is another draft until it is approved and sealed. `origin` stays put until a newer published version is accepted.

Several references are only inside one instrument. Extract may propose a merge. The human signs the merged requirement, or splits and signs the separate requirements. Nothing is merged without that sign-off. If a human merges or splits Requirements later, corresponding Claim references must be reviewed and deliberately rebound. A Claim still points at exactly one Requirement. The operation is not an automatic dependency graph.

A requirement originates from **one** legal or policy instrument, the same one as its pack. `source.instrument` is repeated on the requirement so the seal still says which act it is after the file is copied. Query "all requirements in pack P" = `WHERE pack_id = P`.

---

### 2.3 Repo config (`curbpack.json`)

Visible at repo root as **`curbpack.json`**.

Owns: which published collections apply, requirement include/exclude, and **shared hunt scope** (same for all packs).

`packs` lists pack ids. It does not list versions. The version the team is using is `version` on the local `pack.json` for that id, the file Curbpack loads for the id. Keeping that file (in git, or in the air-gapped pack directory) is what makes the choice reproducible without a network. A newer publication is visible only when its `pack.json` has reached the environment. Nothing fetches it on its own. Compare that file's `version` with the version the team is already using, and with `origin.version` on each local requirement. Those are different facts.

```json
{
  "packs": ["house-policy", "cra-baseline"],
  "exclude_requirements": [
    "CRA-ART14-PATH"
  ],
  "hunt": {
    "sources": [{ "source": "documents" }],
    "exclude_path_globs": ["**/node_modules/**", "*FUTURE_*"],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"]
  }
}
```

Semantics: evaluate **all** requirements with `pack_id` in `packs`, minus `exclude_requirements`.
Hunt merge: repo `hunt`, then that requirement's `discovery_hints` (§2.7).

**Alternative (explicit include):**

```json
{
  "packs": ["house-policy"],
  "requirements": [
    "HOUSE-SECURITY-REPORTING",
    "HOUSE-SECURITY-TXT"
  ],
  "hunt": {
    "sources": [
      { "source": "documents" },
      { "source": "git" }
    ],
    "exclude_path_globs": ["**/node_modules/**"]
  }
}
```

Semantics: only these requirement ids (each belongs to a selected pack). Use either exclude-style or include-style per repo.

This file records the pack id, not the version. The version is on the local `pack.json`.

---


### 2.4 Claim

A Claim identifies a piece of evidence, the relevant part(s) of that evidence, and the human rationale for how it supports one Requirement.

A Requirement may have any number of Claims, but each Claim supports exactly one Requirement. If the same document supports two Requirements, two separate Claims are created.

A Claim may have zero or more Checks that monitor technical conditions associated with the reviewed evidence. Their results help determine whether the human approval needs to be reconsidered.

The same Claim JSON object is used for saving, editing, publishing, checking, signing and reviewing. There is no separate draft or runtime format.

| Field | Meaning |
| --- | --- |
| `id` | Stable Claim identity within the product's Claim collection. |
| `requirement_id` | The one Requirement this Claim supports. |
| `source` | Source adapter identifier, such as `documents` or `git`. |
| `args` | Source-specific arguments identifying the evidence and, where applicable, the regions supporting the Claim. |
| `description` | The human rationale explaining how the identified evidence supports the Requirement. |
| `severity` | Optional product triage: `high`, `medium`, or `critical`; not the Requirement's legal `strength`. |
| `checks` | Zero or more `{ "check": <id>, "args": <object> }` entries, defined in §2.5. |
| `signed` | Optional Claim signature (§2.6). |

A file-backed Claim with two Checks:

```json
{
  "id": "claim-house-security-md",
  "requirement_id": "HOUSE-SECURITY-REPORTING",
  "source": "git",
  "args": {
    "path": "SECURITY.md"
  },
  "description": "The reviewed SECURITY.md describes the product's security reporting process.",
  "severity": "high",
  "checks": [
    {
      "check": "exist",
      "args": {
        "paths": ["SECURITY.md"]
      }
    },
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

**Source adapters**

`Claim.source` uses the same source adapter namespace as `discovery_hints.sources`.

Discovery uses a source adapter to find candidate evidence. A Claim uses that adapter to identify the specific evidence and relevant regions supporting its assertion. The adapter defines the applicable `args` for each operation.

For example, a text-file source adapter may accept region selectors. Their exact structure belongs to the adapter, not to the generic Claim schema.

`Claim.source` is unrelated to `Requirement.source`, which identifies the legal instrument.

Source `args` and `checks[].args` serve different purposes:

- Source arguments identify the evidence being reviewed.
- Check arguments configure the technical conditions being monitored.

A Check may examine the same artefact, a particular region, or related material. Its arguments need not duplicate the Claim's source arguments.

**Claim lifecycle**

A Claim with `"checks": []` is a saved evidence proposal. It retains its source, arguments and rationale and can be revisited and edited. It has nothing to execute and is excluded when publishing Claims.

Discovery may suggest evidence, but a suggestion does not automatically create a saved Claim. Saving is an explicit user action.

A Claim with one or more schema-valid Checks may be saved, published and tested without signing. Publication selects the applicable Claim files; it does not approve them. No separate publication format or `published` flag is introduced.

Human approval is recorded by signing the Claim after reviewing the evidence and its configured Checks.

A Claim signature covers the Claim JSON, including `source`, source `args`, `description` and `checks`. It does not automatically seal the external evidence artefact's contents.

A subsequent Check failure indicates that a monitored condition may no longer hold and that the Claim may need human reassessment. It neither silently revokes the signature nor automatically establishes non-compliance.

Editing a signed Claim changes its digest and requires renewed approval and signing. Creating a new Claim must not overwrite an existing file; modifications use an explicit edit operation.

**Field boundaries**

Legal text, `discovery_hints` and `remediation_hint` remain on the Requirement.

`expected`, `remediation`, `settlement`, `retired`, retrieval scores, model rationales and Useful/Poor votes are not Claim fields. Operational Discovery feedback remains separate from the signed Claim.

Template-generated Claims use the same schema. Scaffold markers, when needed, belong in generated documentation rather than in special Claim status fields.

The Review Report distinguishes unsigned or unverifiable Claims from failed Checks (§3.1).
---

### 2.5 Check definitions

A Claim may have any number of Checks. Each entry in `checks[]` has exactly the common pair **`check`** (registered Check id) and **`args`** (parameters validated against that Check's JSON Schema). The saved Claim and the input read by `curbcheck` use this same structure.

`available_checks.json` lists the Check types. For each Check it records its **id**, the **CLI tool** implementing it and the **JSON Schema** for its `args`. The registry is authoritative for both the Check configuration UI and Check validation/dispatch. Adding a registered Check implementation must not require changing the generic Claim schema or hardcoding new argument fields in the UI.

An illustrative registry entry (file layout and invocation details can be refined without changing the Claim format):

```json
{
  "checks": [
    {
      "id": "exist",
      "command": "curbcheck-exist",
      "args_schema": {
        "type": "object",
        "required": ["paths"],
        "properties": {
          "paths": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 1
          }
        },
        "additionalProperties": false
      }
    }
  ]
}
```

All UIs that configure Checks use that registry to enumerate types, render the appropriate input fields and validate submitted `args`. Unknown `check` ids or invalid arguments are errors, not successful evaluations. The implementation runs the CLI tool selected by the registered `check` id; the Claim itself does not contain a command to execute.

The built-in `contents` Check defines a `probes` array **inside its own `args`**. `probes` is not a new generic architectural layer and is not present on all Checks. Its exact format belongs to the `contents` argument schema (§4).

```json
{
  "checks": [
    { "check": "exist", "args": { "paths": ["README.md"] } },
    {
      "check": "contents",
      "args": {
        "path": "README.md",
        "probes": [
          { "kind": "headers", "headers": ["Purpose"] }
        ]
      }
    }
  ]
}
```

The last example shows the `checks` property **within** a Claim, not a different document type. Checks can be executed before sign-off. Passing them proves only their specified technical conditions held for the tested inputs.

---

### 2.6 Signing

Four signed object categories, different jobs:

1. **Requirement** — authenticity of that payload. The version digest is the whole requirement with `signed` removed, so `id`, `pack_id`, `source`, `references`, `discovery_hints`, `remediation_hint`, `note`, `origin` when present, and any property that is present are all in it. `check` does not read `note` or `discovery_hints`; a change to either is still a new requirement version, because both are part of the payload.
2. **Pack** — integrity of the **whole pack directory** (completeness + no swapped files).
3. **Claim** — source and source arguments locating the reviewed evidence, the human rationale, and the complete `checks[]` configuration approved by the human.
4. **Review report** — the run result and the reviewer's recorded decision.

Same `signed` shape (shown inside its enclosing object):

```json
{
  "signed": {
    "at": "2026-10-01T08:00:00Z",
    "name": "Arne Anka",
    "signature": "<base64>"
  }
}
```

| Field | Role |
|-------|------|
| `at` | When sealed (UTC). Covered by the signature. |
| `name` | Signer display name. Must match the certificate that verifies. Covered by the signature. |
| `signature` | Seal bytes. Excluded from the corresponding object digest. |

**Version digest:** for a Requirement, Claim or Review Report, canonical JSON of the **entire object** with its whole `signed` block removed. Thus a Claim digest includes the Claim-level `source` and `args`, `description`, `severity`, every entry of `checks[]` and each Check's `args`. A changed payload is a new version. A new `signed.at` alone does not change this digest.

**Signature input:** the applicable version digest, plus `name`, plus `at`. Sign with the signer's certificate. Write base64 into `signed.signature`. Verification uses the trusted certificate for `name`. A publisher signature verifies only a payload whose bytes are the publisher's, which means no `origin` and no local edit to a publisher Requirement. It does not verify a modified working copy. An unsigned Claim can still be evaluated; a Check pass is not a signature.

**Pack seal:** directory digest of the pack folder — every relative path sorted, each file’s bytes hashed, then combine — with `pack.json`’s `signed.signature` cleared for the digest → sign that digest → write base64 into `pack.json`’s `signed.signature`.

**Check:** recompute the version digest, verify the signature over version digest + `name` + `at` with the trusted certificate for `name`.

DSSE and Sigstore are not a prerequisite. The seal is the `signed` block in this section. A later change to either of them needs a requirement from the party who relies on the signature, a test that verification still works with no network, a dependency analysis, and a fixture for the migration.

A signed Git commit does not write the `signed` block. When `signed` is present, the reading shows that block. When `signed` is absent and the requirement's bytes are in a signed Git commit, the reading shows a Git commit: the signing key, the time stated on that commit, that commit as the version, and whether the commit signature verifies. When neither exists, the requirement is an unsigned draft, not an approved requirement version. The same reading applies to a claim and to the pack. `discovery_hints` has no seal of its own; it is inside the requirement payload. Git records the history of the files. It is not a signature chain, not a version graph, and not a merge. Nothing joins RISE's signature to a later local signature, and nothing merges an upstream release into a working copy. SourceSafe, ClearCase, and a copied folder have no commit to consult. A verified signed Git commit authenticates its recorded content; whether its signer was authorized to approve a particular Claim remains an organisational responsibility. It is not a substitute for reading the Claim and its Check results.

There is no separate signing document, no `approved_for_pilot_use` decision on the seal, and no reviewer role field. The person who judges that the claims are sufficient signs the review report (`review-sign`). That signature is not the requirement seal. The report uses the same `signed` shape. Its version digest is the report with `signed` removed.

The signed report includes the run result (§3.1), the signature-status appendix for Claims evaluated or included in the report, and the reviewer's decision in their own words. A person may accept the material, ask for a change, or hand the question to whoever the organisation holds responsible. Those are examples of what the words can say. Curbpack does not route them, assign them, or decide that the signer was authorized to decide. The organisation does. The decision text is inside the version digest, so the five facts below are how the signature is read.

**Reading a signature.** For a requirement, a claim, a review report, or a Git commit used as a seal, show these five facts and nothing else in their place:

| Shown | Source |
| --- | --- |
| What was signed | The object: a requirement, a claim, the review report, or a Git commit. The pack directory seal is read the same way; what it covers is the directory digest. |
| Who | The identity the signature binds to. On a `signed` block that is `name`, and it must be the identity on the certificate that verifies. On a signed Git commit it is the signing key. The Git author string is not that identity. |
| When | The stated time. On a `signed` block that is `at` (UTC). On a signed Git commit it is the time stated on that commit. That commit time is not a separate cryptographically verified signing timestamp. |
| Which version | The exact content the signature covers: the version digest. For a requirement, claim, or report that is the canonical JSON with the whole `signed` block removed. The signature is over that digest plus `name` plus `at`. This is not `pack.version` and not `origin.version`. For a Git commit it is that commit. For the pack directory it is the directory digest. |
| Verifiable | Yes, if the trusted certificate for that identity verifies the signature over that digest, `name`, and `at`. Otherwise the reason, which is one of the following. |

Not verifiable, and why:

- No `signed` block and no signed Git commit. The object is unsigned. A requirement in that state is a draft, not an approved requirement version.
- The certificate for `name` is not available. Verification does not fetch it.
- The certificate does not verify the signature, or `name` is not the identity on that certificate.
- The current bytes are not the digest that was signed. A changed `discovery_hints`, `origin`, or any other part of the payload is this case.
- Someone offers the Git author or committer string as the signer. That string is not a signature.

Kalle's requirement, after his hint edit, reads as: a requirement; Kalle; `2026-11-02T09:00:00Z`; the digest of that payload, which still has `origin.version` `"1.0.0"`. It verifies only with Kalle's certificate over that digest, his name, and that time. RISE's certificate does not verify it. The collection version the team is using stays on `pack.json` and is not this digest.

**Which collection, which origin, who signed.** Three different facts.

RISE publishes `cra-baseline` with `pack.version` `"1.0.0"`. The requirement has no `origin`. RISE signs it. The product team chooses that collection: `curbpack.json` lists `cra-baseline`, and their local `pack.json` says `"1.0.0"`. Fetching or importing those files does not alter them. Offline, this is the copy they already have. No network is required to read it.

They create a working copy of the requirement. `origin` is set at that moment to `{ "pack": "cra-baseline", "version": "1.0.0" }`. The hints are still the ones RISE published. The copy is unsigned. It is a draft. RISE's signature does not cover it. RISE's file is unchanged. Approving the draft seals it. That sealed payload is the approved local version.

Kalle later changes `discovery_hints`. `origin` stays `"1.0.0"`. He approves the edit and signs that payload. `signed.name` is Kalle. Git records the edit. His signature does not extend RISE's, and nothing syncs the copy back to RISE.

RISE publishes `1.1.0`, again with no `origin`, signed by RISE. The team can see that a new version exists only once that `pack.json` has reached them. Kalle's requirement still has `origin.version` `"1.0.0"` and Kalle's signature, including while the new file is sitting there unread into the requirement. When the team has reviewed `1.1.0` and taken it into the working copy, `origin.version` becomes `"1.1.0"` and the person who approves that copy signs it. The local `pack.json` they use then says `"1.1.0"` as well. Until that acceptance, the requirement they are evaluating is still the one Kalle signed against `1.0.0`.

The pack the team is using at the start:

```json
{ "id": "cra-baseline", "version": "1.0.0" }
```

RISE's requirement in that publication. No `origin`. Signed by RISE:

```json
{
  "id": "CRA-ANNEX-VII-RISK",
  "pack_id": "cra-baseline",
  "discovery_hints": { "path_hints": ["*risk*assessment*"] },
  "signed": { "name": "RISE", "at": "2026-10-01T08:00:00Z", "signature": "<rise-1.0.0>" }
}
```

Working copy, just created. `origin` is already set. Hints are still RISE's. Unsigned draft:

```json
{
  "id": "CRA-ANNEX-VII-RISK",
  "pack_id": "cra-baseline",
  "origin": { "pack": "cra-baseline", "version": "1.0.0" },
  "discovery_hints": { "path_hints": ["*risk*assessment*"] }
}
```

The same copy after it is approved. Signed by the person who approved it, not by RISE:

```json
{
  "id": "CRA-ANNEX-VII-RISK",
  "pack_id": "cra-baseline",
  "origin": { "pack": "cra-baseline", "version": "1.0.0" },
  "discovery_hints": { "path_hints": ["*risk*assessment*"] },
  "signed": { "name": "<approver of the copy>", "at": "2026-10-15T09:00:00Z", "signature": "<copy>" }
}
```

After Kalle changes the hints and approves that version. The team is still on collection `1.0.0`. The requirement still builds on `1.0.0`. The signer is now Kalle:

```json
{
  "id": "CRA-ANNEX-VII-RISK",
  "pack_id": "cra-baseline",
  "origin": { "pack": "cra-baseline", "version": "1.0.0" },
  "discovery_hints": { "path_hints": ["*risk*assessment*", "docs/security/*"] },
  "signed": { "name": "Kalle", "at": "2026-11-02T09:00:00Z", "signature": "<kalle>" }
}
```

RISE's later publication, untouched, no `origin`, signed by RISE. Visible locally only as this file, once it has arrived:

```json
{ "id": "cra-baseline", "version": "1.1.0" }
```

```json
{
  "id": "CRA-ANNEX-VII-RISK",
  "pack_id": "cra-baseline",
  "discovery_hints": { "path_hints": ["*risk*assessment*", "*cybersecurity*risk*"] },
  "signed": { "name": "RISE", "at": "2026-12-01T08:00:00Z", "signature": "<rise-1.1.0>" }
}
```

While that file is present and not yet accepted, Kalle's requirement above is still the one in use: `origin.version` `"1.0.0"`, `signed.name` `"Kalle"`. After `1.1.0` is reviewed and taken in, the local `pack.json` the team uses says `"1.1.0"`, `origin.version` becomes `"1.1.0"`, and the person who approves that requirement signs it.

A content hash of a fetched tree checks integrity. It is not `pack.version`, and it is not `origin.version`.

---

### 2.7 `discovery_hints`

One object, stored on the requirement. Not a separate file, not a separate seal, and not outside the version digest. Fields:

| Field | Role |
|-------|------|
| `concepts` | Terms for candidate discovery |
| `path_hints` | Globs for candidate discovery |
| `sources` | Where a hunt may look. Each entry is a `source` id plus optional `args`, the same split as `check` + `args`. |
| `expected_evidence` | What kind of artifact is sought. |

The publisher's hints are inside the publisher's signature. A product team may change the hints, or any other part of the requirement. That edit is a draft until it is approved and sealed. RISE's signature still verifies only RISE's published bytes.

`source` here is how material is reached. It is not `requirement.source`, which names the legal instrument. `documents`, `git`, ClearCase, and DOORS are source ids. `args` carries whatever that id needs, and is omitted when it needs nothing. The model does not fix a list of ids, and it does not assume markdown files or Git. A requirement that sets `sources` uses that list. Otherwise the repo `hunt` list is used.

The PoC implements one reach: files in the working tree now, matched by `path_hints` or by `concepts` in the file text. It reads neither the discovery source id nor source `args`. It does not search Git history, commit messages, or older blobs. `expected_evidence` is stored and the PoC does not match on it. That is the PoC's limit. `check` does not read hunt output. Discovery suggestions are not reviewed Claims. When a suggestion is saved as a Claim, that Claim uses its own `source` + `args` to identify the actual evidence; these are distinct from the Requirement's discovery source list.

---

## 3. Evaluation of Claims

`curbcheck` reads **exactly the Claim format defined in §2.4**. There is no derived Claim or separate evaluation-unit object. It processes each eligible Claim (`checks` non-empty), validates each entry in `checks[]` against the trusted registry, and executes the registered implementation with that entry's `args`. One Claim may contain multiple Checks of the same type with different arguments.

For every Check, the runner identifies the enclosing Claim by its `id` and the configured Check by its **zero-based array index** within that Claim's `checks[]`. The Claim digest (the canonical whole Claim without `signed`) identifies the precise configuration that ran. Changing Check order changes the Claim digest; results from another digest must not be presented as results of the current configuration.

A Claim with `checks: []` is omitted from execution and from the published executable set. A missing or unknown Check id, a missing implementation, or invalid arguments must fail validation or produce an explicit non-passing result. They must never count as a pass.

### 3.1 Run result

`curbcheck` writes **one result document**. CI, developer tools, `curbpack-compile` and `curbpack-review` read this result. Compile copies it into the evidence/review bundle; Review does not generate a second, competing run result.

```json
{
  "commit": "<git HEAD, omitted when this run did not use git>",
  "worktree": "clean",
  "packs": [
    {
      "id": "cra-baseline",
      "version": "1.0.0",
      "digest": "<pack directory digest>"
    }
  ],
  "tool": "curbcheck",
  "tool_version": "<the build that ran>",
  "claims": [
    {
      "id": "CRA-ANNEX-VII-RISK",
      "digest": "<whole Claim version digest>",
      "status": "fail",
      "checks": [
        {
          "index": 0,
          "check": "exist",
          "args": {
            "paths": [
              "docs/annex-vii/risk_assessment.md"
            ]
          },
          "status": "pass"
        },
        {
          "index": 1,
          "check": "contents",
          "args": {
            "path": "docs/annex-vii/risk_assessment.md",
            "probes": [
              {
                "kind": "size",
                "bytes": 200,
                "op": ">="
              },
              {
                "kind": "headers",
                "headers": [
                  "# Risk Assessment",
                  "## Product Overview",
                  "## Identified Risks"
                ]
              },
              {
                "kind": "token"
              }
            ]
          },
          "status": "fail",
          "detail": "Required header ## Identified Risks not found"
        }
      ]
    }
  ]
}
```

`commit` and `worktree` are present only when Git was used. `worktree` is `clean` or `dirty` according to uncommitted local changes. A dirty run is allowed, but it must not be presented as verification of the referenced commit's exact content. `packs[]` identifies loaded Requirement collections by `id`, their local `pack.version`, and directory digest. It does not report `origin.version`. `tool` and `tool_version` identify the checker build; Check types do not have independent version fields in the Claim format.

There is **one result entry per executed Claim**, with a `checks[]` result for **each configured Check**, including passes. Each Check result includes `index`, `check`, the `args` used, `status`, and a `detail` when required. `index` disambiguates repeated Check ids and is interpreted only together with the Claim `id` and `digest`.

Each Check status is `pass`, `fail`, or `skipped`. A missing required file is `fail`; unavailable/unsupported execution must be explicit and non-passing. `detail` is omitted for `pass`, required for `skipped`, and included for `fail` to explain the cause. `skipped` is never `pass`.

The enclosing Claim status is **`fail` if any Check fails; otherwise `skipped` if any Check is skipped; otherwise `pass`**. No Claim with empty Checks is evaluated or reported as a passing Claim. Process exit is 0 only when at least one Check actually executed and every included Claim and Check passed. Otherwise it is nonzero; exit code is not a JSON field. These are mechanical Check outcomes, not legal compliance judgments.

The run result references the Claim digests actually executed. A compiler or reviewer must not silently associate a result with a newer Claim carrying the same `id` but a different digest. If the exact Claim version cannot be retrieved, report the provenance gap rather than claiming that a changed Claim was checked. The later Review Report reports these outcomes and separately provides an appendix of **unsigned Claims** and **Claims with unverifiable signatures** within the reported/published Claim set, naming the related Requirement ids and Claim ids. Unpublished, unchecked researcher proposals are outside that report scope. Missing or invalid signatures must not be silently converted into failed Check outcomes. This appendix belongs to the review/reporting output, **not** the `curbcheck` run-result JSON.

---

## 4. Built-in checks → args schemas

These are the built-in Check types whose argument schemas are registered in `available_checks.json`. Each Check type answers a specific technical question using its own `args`. A Claim may combine several types.

Historical implementation note (not the target contract): the running v1 code had the old `file_present` bag (`min_bytes`, `min_words`, `require_headers`, `bind_repo_token`, `require_tree_paths`), and `fresh` calls that function first, so a stale file can fail on a missing header. These are intended Check-type semantics; the registered JSON Schemas are authoritative for argument validation. `annex_file` was an alias of that legacy bag.

| check id | args | Question |
| --- | --- | --- |
| `exist` | `paths` (one or more) | Each path is present. Nothing about the bytes. |
| `contents` | `path` or `paths`, `probes` | The bytes satisfy every probe. A missing required file fails this Check too, with a detail that the file is absent. It does not answer the byte question. `paths` is for the same probes on each file. |
| `git_fresh` | `path`, `max_age_days`, `as_of` | Age of that file's last commit, measured from `as_of`. Does not repeat `exist` or `contents`. |
| `git_signed` | `path`, and exactly one trust input | Whether Git accepts a signature on that commit. |
| `git_author` | `path`, and `name` or `email` or both | The recorded author of that commit. Not a signature. |
| `git_signer` | `path`, `signer`, and exactly one trust input | The verified signer of that commit. Not the author field. |
| `dep_ban` | `package`, `banned_versions` | A dependency pin is forbidden. |

`npm_dep_ban` and `manifest_dep_ban` are aliases of `dep_ban`.

`fresh`, `since_ref`, and `owned` are not Check ids. The four Git Checks below replace those questions. Their rules are §4.1.

Only `contents.args` has the `probes` argument shown below. No prompts or LLM calls are involved in these Checks.

| kind | args | Match |
| --- | --- | --- |
| `size` | `bytes`, `op` (`>`, `>=`, `<`, `<=`) | File length. Old `min_bytes: 200` is `op: ">="`. |
| `words` | `n`, `op` | Word count. |
| `headers` | `headers` (list of strings) | Each string is a literal substring. Not a regexp. |
| `token` | — | Bytes contain the repo token (directory name, `package.json` name, or `go.mod` module). |
| `pattern` | `pattern` | Forbidden regexp: the `contents` Check fails when it matches (legacy `text_forbid`). |
| `placeholder` | — | Fail if built-in placeholder patterns are detected (legacy `anti_placeholder`). |

A Check that only needs a file to exist uses `exist`. Size, headers and repo token are `probes` of one `contents` Check. The reviewer may attach both Checks to the **same Claim** about that evidence, or create another Claim for a separate human assertion about another evidence item. The number of Checks does not determine the number of Claims.

```json
{ "check": "exist", "args": { "paths": ["docs/annex-vii/risk_assessment.md"] } }
```

```json
{
  "check": "contents",
  "args": {
    "path": "docs/annex-vii/risk_assessment.md",
    "probes": [
      { "kind": "size", "bytes": 200, "op": ">=" },
      { "kind": "headers", "headers": ["# Risk Assessment", "## Product Overview", "## Identified Risks"] },
      { "kind": "token" }
    ]
  }
}
```

```json
{ "check": "exist", "args": { "paths": ["README.md"] } }
```

```json
{
  "check": "git_fresh",
  "args": {
    "path": "docs/annex-vii/risk_assessment.md",
    "max_age_days": 90,
    "as_of": "2026-10-23T06:00:00Z"
  }
}
```

### 4.1 Git provenance

`git_fresh`, `git_signed`, `git_author`, and `git_signer` are four Check ids on one registry command, `curbcheck-git`. Each id has its own args schema and its own `pass`, `fail`, or `skipped` result. A Claim lists them as ordinary `checks[]` entries. There is no grouping object and no sub-check.

The relevant commit for `path` is the last commit reachable from the run's HEAD that changes that path. History is not followed across a rename. All four Checks use that commit. The run-level `commit` stays HEAD. These Checks add no Check-result field. `detail` is omitted on `pass`. On `fail`, `detail` names the cause and, when a commit was found, that commit id. The evidence path is `args.path`.

A missing path, an untracked path, or a worktree file that differs from the blob at HEAD is `fail`, and `detail` names that condition. A deleted or never-committed path is `fail`.

`skipped` is only the caller-supplied skip of the whole Claim. These Checks have no fourth status. An unavailable `git` binary is `fail`.

`git_fresh` requires `path`, `max_age_days`, and `as_of`. `max_age_days` is an integer greater than or equal to 0. `as_of` is an RFC 3339 instant. Compare the relevant commit's committer timestamp with `as_of`. Age in whole days is `floor((as_of - committer_time) / 86400)`. The Check passes when that age is less than or equal to `max_age_days`. A committer time after `as_of` is `fail`. The Check does not read the wall clock. `as_of` is retained because it is part of `args`. A file last changed on Monday, with `max_age_days` 2 and `as_of` on Friday, fails even when Friday's HEAD did not change that file.

`git_signed` requires `path` and exactly one trust input. `allowed_signers` is a relative path inside the repository to an SSH allowed-signers file. `openpgp` has only the value `repo` and selects the repository's existing OpenPGP Git configuration. A missing signature, a signature Git rejects, a missing trust input, and a missing `git` binary are separate `fail` details. The Check does not fetch keys and does not read Claim `signed`.

`git_author` requires `path` and at least one of `name` and `email`. Each present value is compared with the relevant commit's author name or author email as an exact case-sensitive string. The Check does not verify a signature.

`git_signer` requires `path`, `signer`, and the same exactly-one trust input as `git_signed`. `signer` is compared, as an exact case-sensitive string, with the signer identity reported by a signature Git accepts under that trust input. `git_author` and `git_signer` do not read each other's result. A matching author with a missing or different signer is `pass` for `git_author` and `fail` for `git_signer`.

```json
{ "check": "git_signed", "args": { "path": "docs/annex-vii/risk_assessment.md", "allowed_signers": ".git-allowed-signers" } }
```

```json
{ "check": "git_signed", "args": { "path": "docs/annex-vii/risk_assessment.md", "openpgp": "repo" } }
```

```json
{ "check": "git_author", "args": { "path": "docs/annex-vii/risk_assessment.md", "name": "Anna", "email": "anna@example.com" } }
```

```json
{ "check": "git_signer", "args": { "path": "docs/annex-vii/risk_assessment.md", "signer": "Anna", "allowed_signers": ".git-allowed-signers" } }
```

---


**Important:** `contents` fails if a required path is absent. A secret-scanning or placeholder template must not list optional, non-existing files as if their absence were a success. Any different optional-path behavior requires its own registered Check/schema decision; do not silently change `contents`.

---

## 5. Example Claims adapted from earlier rules

These examples retain the earlier Requirement IDs and the meaningful parts of each Check's `args`. They are **illustrative Claim assertions**, not evidence that the reference files are legally adequate. One Claim may combine multiple Checks. `description` now states the human proposition, not an error message. Claim-level `source` + `args` identify what the human inspected independently of `checks[]`.

Historical v1 `file_present` with size or headers corresponds to a registered `contents` Check. A file-presence-only test uses `exist`; `git_fresh` does not repeat those tests. This section does not change the existing Check schemas.

**Caution on these inherited templates:** `contents` fails on missing paths; samples containing optional paths may not be suitable to ship as enforceable defaults without narrowing the file list or using another explicitly defined Check. A default Claim must not be treated as human-approved merely because it is supplied by a publisher.

### 5.1 house-policy

**HOUSE-SECURITY-MD**

```json
{
  "id": "HOUSE-SECURITY-MD",
  "requirement_id": "HOUSE-SECURITY-REPORTING",
  "severity": "high",
  "source": "documents",
  "args": {
    "path": "SECURITY.md"
  },
  "description": "The reviewed SECURITY.md describes the product security-reporting process.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": "SECURITY.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 80,
            "op": ">="
          },
          {
            "kind": "words",
            "n": 20,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# Security"
            ]
          }
        ]
      }
    }
  ]
}
```

**HOUSE-SECURITY-TXT**

```json
{
  "id": "HOUSE-SECURITY-TXT",
  "requirement_id": "HOUSE-SECURITY-TXT",
  "severity": "medium",
  "source": "documents",
  "args": {
    "path": ".well-known/security.txt"
  },
  "description": "The reviewed security.txt provides a substantive security contact statement.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": ".well-known/security.txt",
        "probes": [
          {
            "kind": "size",
            "bytes": 40,
            "op": ">="
          },
          {
            "kind": "words",
            "n": 5,
            "op": ">="
          }
        ]
      }
    }
  ]
}
```

**HOUSE-DEP-AXIOS-PIN**

```json
{
  "id": "HOUSE-DEP-AXIOS-PIN",
  "requirement_id": "HOUSE-DEP-AXIOS",
  "severity": "critical",
  "source": "documents",
  "args": {
    "path": "package.json"
  },
  "description": "The reviewed dependency manifest does not pin a prohibited axios version.",
  "checks": [
    {
      "check": "dep_ban",
      "args": {
        "package": "axios",
        "banned_versions": [
          "1.6.0",
          "^1.6.0",
          "~1.6.0"
        ]
      }
    }
  ]
}
```

The `package.json` source reference is illustrative. The `dep_ban` implementation must specify which actual manifest(s) it inspects; do not infer them from this example alone.

**HOUSE-SECRET-PATHS**

```json
{
  "id": "HOUSE-SECRET-PATHS",
  "requirement_id": "HOUSE-NO-SECRETS-IN-DOCS",
  "severity": "critical",
  "source": "documents",
  "args": {
    "paths": [
      "README.md",
      "SECURITY.md",
      ".well-known/security.txt",
      ".env",
      ".env.local",
      "credentials.json",
      "service-account.json",
      "id_rsa"
    ]
  },
  "description": "The reviewed set of relevant product files contains no prohibited credentials or private-key material.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "paths": [
          "README.md",
          "SECURITY.md",
          ".well-known/security.txt",
          ".env",
          ".env.local",
          "credentials.json",
          "service-account.json",
          "id_rsa"
        ],
        "probes": [
          {
            "kind": "pattern",
            "pattern": "(?i)(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----|api[_-]?key\\s*[:=]\\s*[\\'\\\"]?[a-zA-Z0-9]{20,})"
          }
        ]
      }
    }
  ]
}
```

This retains the historical list for comparison only. Optional missing paths cause `contents` to fail; do not use it unchanged as a production default. The original pasted regexp contained invalid JSON escaping and is normalized here.

**HOUSE-ANTI-PLACEHOLDER**

```json
{
  "id": "HOUSE-ANTI-PLACEHOLDER",
  "requirement_id": "HOUSE-NO-PLACEHOLDER-SECURITY-DOCS",
  "severity": "high",
  "source": "documents",
  "args": {
    "paths": [
      "SECURITY.md",
      ".well-known/security.txt"
    ]
  },
  "description": "The reviewed security documentation contains no unresolved placeholder text.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "paths": [
          "SECURITY.md",
          ".well-known/security.txt"
        ],
        "probes": [
          {
            "kind": "placeholder"
          }
        ]
      }
    }
  ]
}
```

### 5.2 cra-baseline

**CRA-ANNEX-VII-RISK**

```json
{
  "id": "CRA-ANNEX-VII-RISK",
  "requirement_id": "CRA-ANNEX-VII-RISK",
  "severity": "high",
  "source": "git",
  "args": {
    "path": "docs/annex-vii/risk_assessment.md",
    "regions": [
      {
        "quote": "## Identified Risks"
      }
    ]
  },
  "description": "The reviewed risk assessment documents the product-specific cybersecurity risks.",
  "checks": [
    {
      "check": "exist",
      "args": {
        "paths": [
          "docs/annex-vii/risk_assessment.md"
        ]
      }
    },
    {
      "check": "contents",
      "args": {
        "path": "docs/annex-vii/risk_assessment.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 200,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# Risk Assessment",
              "## Product Overview",
              "## Identified Risks"
            ]
          },
          {
            "kind": "token"
          }
        ]
      }
    }
  ]
}
```

The `exist` and `contents` entries are **two Checks on this one Claim** about the risk-assessment evidence. If README.md is independently accepted as evidence for the same Requirement, it may have its own Claim.

**CRA-ANNEX-VII-SUPPORT**

```json
{
  "id": "CRA-ANNEX-VII-SUPPORT",
  "requirement_id": "CRA-ANNEX-VII-SUPPORT",
  "severity": "high",
  "source": "documents",
  "args": {
    "path": "docs/annex-vii/support_period.md"
  },
  "description": "The reviewed support-period document explains the chosen support period.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": "docs/annex-vii/support_period.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 120,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# Support Period",
              "## End of Support"
            ]
          },
          {
            "kind": "token"
          }
        ]
      }
    }
  ]
}
```

**CRA-ANNEX-VII-MANUAL**

```json
{
  "id": "CRA-ANNEX-VII-MANUAL",
  "requirement_id": "CRA-ANNEX-VII-MANUAL",
  "severity": "medium",
  "source": "documents",
  "args": {
    "path": "docs/annex-vii/user_manual_security.md"
  },
  "description": "The reviewed user manual describes the relevant security instructions.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": "docs/annex-vii/user_manual_security.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 150,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# User Manual — Security",
              "## Secure Configuration",
              "## Product Disposal"
            ]
          },
          {
            "kind": "token"
          }
        ]
      }
    }
  ]
}
```

**CRA-ART14-PATH**

```json
{
  "id": "CRA-ART14-PATH",
  "requirement_id": "CRA-ART14-PATH",
  "severity": "medium",
  "source": "documents",
  "args": {
    "path": "docs/incident/art14-path.md"
  },
  "description": "The reviewed incident process describes the applicable reporting path.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": "docs/incident/art14-path.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 200,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# Art 14 reporting path",
              "## Reporting clock (CRA Art 14)",
              "## Handling clock (not this file)",
              "## Named owner",
              "## Rehearsal dated artifact"
            ]
          },
          {
            "kind": "token"
          }
        ]
      }
    }
  ]
}
```

**CRA-ANTI-PLACEHOLDER**

```json
{
  "id": "CRA-ANTI-PLACEHOLDER",
  "requirement_id": "CRA-NO-PLACEHOLDER-ANNEX",
  "severity": "critical",
  "source": "documents",
  "args": {
    "paths": [
      "docs/annex-vii/risk_assessment.md",
      "docs/annex-vii/support_period.md",
      "docs/annex-vii/user_manual_security.md",
      "docs/incident/art14-path.md"
    ]
  },
  "description": "The reviewed Annex VII documentation contains no unresolved placeholder text.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "paths": [
          "docs/annex-vii/risk_assessment.md",
          "docs/annex-vii/support_period.md",
          "docs/annex-vii/user_manual_security.md",
          "docs/incident/art14-path.md"
        ],
        "probes": [
          {
            "kind": "placeholder"
          }
        ]
      }
    }
  ]
}
```

**CRA-DEP-AXIOS-PIN**

```json
{
  "id": "CRA-DEP-AXIOS-PIN",
  "requirement_id": "CRA-DEP-AXIOS",
  "severity": "critical",
  "source": "documents",
  "args": {
    "path": "package.json"
  },
  "description": "The reviewed dependency manifest does not pin a prohibited axios version.",
  "checks": [
    {
      "check": "dep_ban",
      "args": {
        "package": "axios",
        "banned_versions": [
          "1.6.0",
          "^1.6.0",
          "~1.6.0"
        ]
      }
    }
  ]
}
```

The `package.json` source reference is illustrative. The `dep_ban` implementation must specify which actual manifest(s) it inspects; do not infer them from this example alone.

### 5.3 medtech-iec62304

**MD-SW-CLASS**

```json
{
  "id": "MD-SW-CLASS",
  "requirement_id": "MD-SW-CLASS",
  "severity": "high",
  "source": "documents",
  "args": {
    "path": "docs/medtech/software_safety_class.md"
  },
  "description": "The reviewed document explains the product software safety classification.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": "docs/medtech/software_safety_class.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 100,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# Software Safety Class",
              "## Classification Rationale"
            ]
          }
        ]
      }
    }
  ]
}
```

**MD-SOUP**

```json
{
  "id": "MD-SOUP",
  "requirement_id": "MD-SOUP",
  "severity": "high",
  "source": "documents",
  "args": {
    "path": "docs/medtech/soup_list.md"
  },
  "description": "The reviewed document identifies the software-of-unknown-provenance inventory.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": "docs/medtech/soup_list.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 80,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# SOUP List",
              "## Items"
            ]
          }
        ]
      }
    }
  ]
}
```

**MD-PROBLEM-RESOLUTION**

```json
{
  "id": "MD-PROBLEM-RESOLUTION",
  "requirement_id": "MD-PROBLEM-RESOLUTION",
  "severity": "medium",
  "source": "documents",
  "args": {
    "path": "docs/medtech/problem_resolution.md"
  },
  "description": "The reviewed document describes the problem-resolution process.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "path": "docs/medtech/problem_resolution.md",
        "probes": [
          {
            "kind": "size",
            "bytes": 80,
            "op": ">="
          },
          {
            "kind": "headers",
            "headers": [
              "# Problem Resolution",
              "## Process"
            ]
          }
        ]
      }
    }
  ]
}
```

**MD-ANTI-PLACEHOLDER**

```json
{
  "id": "MD-ANTI-PLACEHOLDER",
  "requirement_id": "MD-NO-PLACEHOLDER",
  "severity": "critical",
  "source": "documents",
  "args": {
    "paths": [
      "docs/medtech/software_safety_class.md",
      "docs/medtech/soup_list.md",
      "docs/medtech/problem_resolution.md"
    ]
  },
  "description": "The reviewed MedTech documentation contains no unresolved placeholder text.",
  "checks": [
    {
      "check": "contents",
      "args": {
        "paths": [
          "docs/medtech/software_safety_class.md",
          "docs/medtech/soup_list.md",
          "docs/medtech/problem_resolution.md"
        ],
        "probes": [
          {
            "kind": "placeholder"
          }
        ]
      }
    }
  ]
}
```

---

## 6. Product flow

### Cold start

1. **Requirements** - extract or import reviewed Requirements and use the agreed signed Requirement Pack. The previous product name `curbpack-extract` is legacy terminology, not a new subsystem or data format.
2. **Discovery within Claims** - for a selected product repository and Requirement, use `hunt` + `discovery_hints` to find potential evidence. A human may also add a finding by selecting a source and its `args` and writing a rationale. Retrieval findings and assessment scores are suggestions, not approved Claims.
3. **Researcher work** - the human inspects the real evidence, maintains a Claim (possibly with `checks: []`), chooses registered Checks, and sets each Check's schema-validated `args`. Useful/Poor feedback and AI scores remain operational work data, not Claim fields.
4. **Publish and test** - select Claims whose `checks[]` is non-empty and valid. Publish/export those **same Claim JSON objects**, including unsigned ones; do not require signing and do not create a second runtime format. `curbcheck` can test the same eligible set locally. It writes one run result with an outcome for every Check under every evaluated Claim (§3).
5. **Review and sign Claims** - after the human has inspected the evidence and its configured Checks, they may approve each Claim by signing it. A Check pass alone never signs or approves anything.
6. **Compile and final Review** - compile the existing run result, preserve Claim digests, and present a review report. Its appendix lists unsigned and unverifiable Claims with Requirement IDs. The reviewer may sign their own decision on the report separately.

Publishing means **selection of eligible Claim files**, not creation of a new Claim variant or an approval state. Claims with `checks: []` stay in researcher storage/repo but are not selected for the published executable collection and do not execute. Exact packaging commands, publication target and installation-specific paths are left to the implementation architecture; the selection rule and JSON format are fixed here.

There is no special 'publish draft' stage. It is normal to iterate: configure Checks, publish/test the unsigned Claims, inspect failures, adjust the evidence or Check arguments, and test again before signing.

### Steady state

Claims are durable product-owned assertions. Checks can run locally or in CI without an interactive UI. They monitor the conditions described by their individual `args`.

| Trigger | Human action |
| --- | --- |
| A configured Check fails | Examine the affected evidence and the exact failed Check; repair evidence or explicitly edit/rebind the Claim. Do not automatically infer legal non-compliance. |
| Evidence moves or changes | Update the Claim's `source`/`args` and any affected Check `args`; re-evaluate and renew the seal if the Claim payload changed. |
| A new Check implementation becomes available | Register its trusted executable and JSON Schema, then configure it on applicable Claims. Do not change the generic Claim shape. |
| A Requirement is added, removed or changed in a new Pack version | Show which Claims are unbound, require review or need retirement/rebinding; do not silently rewrite them. |
| Requirement text or `discovery_hints` changes | The Requirements editor manages its own approval and seal. Offer a new Discover run; existing Claims remain unchanged until a human reviews them. |
| A Claim with no Checks is saved | Preserve it as a proposal. No Check executes and it is not selected for publication. |
| A Claim is edited after signing | The modified payload is no longer approved by that signature; require renewed human review/signing, never silently preserve an invalid seal. |

In normal operation, `curbcheck` is the automated daily pulse; Claims management is used when evidence, checks, Requirements or review decisions change. A full re-Discovery is not required for every Check run.

- Multiple Claims may support a single Requirement; a Claim supports exactly one Requirement.
- Multiple Checks may monitor one Claim, and each Check has its own `args`.
- Repository-wide source exclusions and prioritization remain in `curbpack.json`.

---

## 7. Defaults / demo / starter

- Ship **template Claims** with configured Checks that pass on the **reference product**, after validating their evidence and arguments.
- On other repositories the same Checks may fail until the evidence or configured arguments are reviewed and adapted; this does not automatically reject the Claim's legal adequacy.
- Onboarding starters (heal/fix-style) are a separate sellable SKU.
- Scaffold docs may carry a first-line status marker; humans clear it via git.

## 8. End-to-end consistency example

The following is a contract-level acceptance scenario, not an additional Claim schema:

1. Load Requirement `CRA-ANNEX-VII-RISK` and a product repository. Discover `docs/annex-vii/risk_assessment.md` as a possible evidence location.
2. A human reads the file, creates a Claim with `requirement_id`, `source` plus source-specific `args` identifying the file and any selected regions, their rationale in `description`, and initially `checks: []`. The saved Claim is still a proposal; nothing runs and it is not selected for publication.
3. The human adds two entries to the **same Claim**: `exist` with `paths`, and `contents` with `path` plus its type-specific `probes`. The generic UI obtains both argument schemas from the Check registry.
4. Publish/select the Claim while it is **unsigned**. The published object is exactly the same JSON schema; `curbcheck` runs both Checks and records two indexed results beneath the Claim `id` and digest. This is a test, not human approval.
5. The human inspects the evidence and results, then signs the entire Claim. The signature covers `source` and its `args`, the rationale, and both Checks with their arguments.
6. A later content change makes `contents` fail while `exist` passes. The Check result reports that discrepancy. The signature of the previously approved Claim does not magically disappear; the reviewer must determine whether the approval is still justified. Editing the Claim's contents/configuration creates a different digest and requires renewed signing.
7. The final Review Report shows technical outcomes and also identifies each unsigned or unverifiable Claim (with Requirement id) in an appendix. A missing Claim signature is **not** presented as a failed Check.

This scenario and the JSON examples in §§2-5 must agree. No implementation may treat `checks[]` as a list of separate Claims, synthesize a second Claim format, or use a Check pass as evidence of legal compliance.

---

## 9. Implementation boundaries

- **Source-specific evidence addressing:** A Claim always has one `source` id and one source-specific `args` object. Source adapters define how their arguments identify an artefact and its relevant regions. For example, `git` can use `args.path`; another source may use a URL or document identifier. A region selector (where supported) is part of those source-specific arguments, not a new generic `evidence[]` layer. This sketch does not introduce a Git commit-hash field.
- **Claim publication:** Select saved Claims with at least one schema-valid Check. The same Claim JSON files are used for checking and review; no additional Claim schema, publication flag or sign-before-test requirement is defined. Export destination and delivery commands are packaging concerns, not a new data model.
- **Check registry:** `available_checks.json` describes ids, CLI implementations and argument JSON Schemas. The concrete installation and command invocation mechanism must be implemented consistently with the registry. Do not replace registry-driven UI with a hardcoded Check form.
- **Compatibility:** Earlier Claim files and run results with a single top-level `check` + `args` are not the format in this design. Migration must be explicit and tested. Existing signatures cannot be carried over to changed Claim payloads; preserve history instead of treating converted Claims as previously approved.

Nothing in this sketch changes the Pack, Requirement or `curbpack.json` format beyond correcting explanatory references to Claims and Checks.
