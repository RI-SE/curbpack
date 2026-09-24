# Curbpack White Paper

**Local repository checks and evidence preparation for human review**

Curbpack checks a software repository against local rule packs and produces files that can be reviewed or handed to a buyer or auditor. It runs locally and does not claim to certify a product or determine regulatory conformity.

> Not conformity assessment. Not CE marking. Not a notified-body opinion.

Canonical wording: `docs/voice-and-terms.md`.
Public site: https://ri-se.github.io/curbpack/
Pin Action/examples at `@v0.5.2`.

---

## 1. Problem

Software suppliers often need to show that repository documentation and dependencies meet company rules or checklists derived from external requirements.

Manual spreadsheets and checklists are difficult to keep synchronized with the repository. Larger GRC systems can move the working information into a separate service.

Curbpack takes a simpler approach: check the repository locally, record the result, and prepare material that people can review or hand to another organization.

The tool performs checks. People remain responsible for interpreting the result.

## 2. What Curbpack is

Curbpack is a **local command-line tool**.

It evaluates **rule packs** against a Git repository and produces machine-readable and human-readable results.

It can also record a reproducible repository-state digest in Git Notes.

* Packs are data: they contain rules interpreted by Curbpack.
* The default pack when no configuration exists is `house-policy`.
* CRA-related packs are optional.
* A successful check means that the configured checks passed for that repository state.
* It does not mean that the product has been certified or found legally compliant.
* Development is supported by RISE Research Institutes of Sweden as applied research and competence development. RISE does not certify products based on Curbpack results.

## 3. Main evaluation flow

```text
Pack JSON
    |
    v
rule evaluation
    |
    v
structured result
    |
    v
review files
    |
    v
optional human review and signing
```

The evaluator currently supports eight check kinds:

* `annex_file`
* `file_present`
* `anti_placeholder`
* `npm_dep_ban`
* `manifest_dep_ban`
* `text_forbid`
* `fresh`
* `owned`

Rule packs can change, but the evaluator supports a defined set of check kinds.

Normal `check` operation does not require a remote policy service.

An optional MCP example calls the CLI. An optional Unix-socket integration exists under `examples/mcp/`; it is not part of the main binary.

### Typical workflows

All workflows eventually use the same local `check`.

A repository can be prepared in several ways:

```text
new repository
    |
    +---- guided setup
    |
existing documentation
    |
    +---- configure packs
    |
CI
    |
    +---- run check
              |
              v
        review package
              |
              v
         human review
              |
              v
      optional attestation
```

A guided setup may help select packs and prepare documentation before checking.

An existing project can configure its documentation and packs directly.

CI can run `check` without using the guided setup.

After the checks pass, Curbpack can prepare a package for human review and, optionally, record an attestation.

## 4. Ways to start

Every workflow ends with `curbpack check`.

Optional drafting and research functions do not replace the checks.

| Workflow                   | What it does                                                                                                                                                                                                                                               |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Guided setup**           | Uses the `pathway` commands to collect basic project information, suggest packs from the known catalogue, record human pack selection, optionally gather source material, help prepare drafts, check citations, and then run the normal repository checks. |
| **Existing documentation** | Uses documentation already present in the repository and configures Curbpack to check the relevant files.                                                                                                                                                  |
| **CI**                     | Runs `curbpack check` directly.                                                                                                                                                                                                                            |

### `pathway`

`pathway` is an optional guided setup function.

It records basic project information and can suggest packs from the configured catalogue.

The generated setup data is not itself a check result and is not used as proof of compliance.

Commands such as `confirm-packs`, `confirm-prose`, and `confirm-share` record decisions that are expected to be made by a human.

The current implementation requires `--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1` for these confirmation operations.

These mechanisms record an explicit acknowledgement; they are not proof of a person's identity.

Automation may inspect status, make suggestions, record notes, run checks, and prepare material, but it must not silently replace decisions requiring human approval.

### Pack rule map

After pack selection, `packs export-graph` can create a local map showing the rules contained in the selected packs.

This map is intended to help navigate the rules when preparing documentation.

It is not regulation text and does not replace `check`.

In simple terms:

> select packs → prepare repository → run checks → prepare material for review

## 5. Main functions

| Input                               | Command or operation        | Output                                          | Human role                                     |
| ----------------------------------- | --------------------------- | ----------------------------------------------- | ---------------------------------------------- |
| Git repository + pack configuration | `init`                      | Curbpack project files and configuration        | Select the appropriate packs                   |
| Project information                 | `pathway suggest`           | Suggestions from the known pack catalogue       | Confirm pack selection                         |
| Selected packs                      | `packs export-graph`        | Map of packs and their rules                    | Use as navigation when preparing documentation |
| Repository                          | `check` / `validate`        | Structured findings and report                  | Correct failed checks                          |
| Check findings                      | `ask --propose`             | Suggested changes                               | Decide whether and how to apply them           |
| Allowed source URLs                 | `research [--fetch]`        | Source material and summary                     | Use when preparing documentation               |
| Draft Markdown                      | `research --cite-check`     | Citation check                                  | Correct missing citations                      |
| Draft alternatives                  | Assistant + human           | Alternative draft text                          | Select or edit the text                        |
| Repository with passing checks      | `share` / `prepare-release` | Review package and summary                      | Review before sending                          |
| Received review package             | `review <dir>`              | Consistency and verification results            | Interpret the result                           |
| Repository + packs                  | `review --repo .`           | Repository review result                        | Interpret the result                           |
| Repository state                    | `attest`                    | Git Notes record and related generated material | Explicit human approval                        |
| Attestation data                    | local verification          | Hash/signature verification result              | Interpret the verification result              |

## 6. Current functions

| Area                          | Function                                                                                                                |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Init / doctor / demo**      | Creates initial project files, checks the local environment, and provides a demonstration workflow.                     |
| **check / validate**          | Runs the configured repository checks. `--heal` can create certain missing starter files and then run the checks again. |
| **ask --propose**             | Explains check findings and suggests possible changes.                                                                  |
| **pathway**                   | Optional guided setup with status, suggestions, notes, and explicit confirmation commands.                              |
| **research / citation check** | Collects source material from allowed sources and checks whether configured claims have citations.                      |
| **export / share**            | Produces additional representations and packages of Curbpack results for review or handoff.                             |
| **prepare-release / attest**  | Prepares review material and optionally records an attestation.                                                         |
| **review**                    | Reviews a received package or configured repository material and reports whether expected information can be confirmed. |
| **local verification**        | Checks hashes and signature-related information associated with an attestation.                                         |
| **packs**                     | Lists, imports, inspects, and exports information about rule packs.                                                     |
| **Platforms**                 | Release binaries are provided for macOS, Linux, and Windows amd64.                                                      |
| **GitHub Action**             | Runs Curbpack in supported CI environments.                                                                             |
| **Optional MCP integration**  | Thin integration layer around the CLI.                                                                                  |

The evaluator currently supports these eight check kinds:

`annex_file`, `file_present`, `anti_placeholder`, `npm_dep_ban`, `manifest_dep_ban`, `text_forbid`, `fresh`, and `owned`.

Process exit codes are:

* `0` — successful command / checks passed
* `1` — failed checks or check-path error
* `2` — usage or environment error

## 7. Example workflow

### 1. Prepare the repository

For a new setup, use the optional `pathway` commands to collect project information and select packs.

Existing projects can configure packs and documentation directly.

### 2. Run the checks

Run:

```sh
curbpack check
```

A failed check may report issues such as:

* a missing required file;
* prohibited wording;
* missing dependency information;
* another rule defined by the selected pack.

The command returns a non-zero exit code while findings remain.

### 3. Correct the findings

Correct the repository.

`curbpack check --heal` can create supported missing starter files.

`curbpack ask ... --propose` can suggest possible changes.

Suggestions are not automatically approved changes.

### 4. Run the checks again

Run `curbpack check` again.

Exit code `0` means that the configured checks passed for the evaluated repository state.

It is not a certification result.

### 5. Prepare material for review

`curbpack share` or `curbpack prepare-release` can create a review package and summary.

The material can then be inspected before it is sent to another organization.

### 6. Optional attestation

A human may run `attest` when appropriate.

An unsigned record is not cryptographically verified.

If signing is used, the resulting signature and hashes can be checked separately.

Existing-document and CI workflows skip the guided setup and run the checks directly.

## 8. What the generated files show

Different Curbpack outputs support different purposes.

| Artifact                                    | What it shows                                                                          |
| ------------------------------------------- | -------------------------------------------------------------------------------------- |
| Check JSON / action report                  | Result of configured repository checks                                                 |
| SARIF export                                | The same findings represented for CI or IDE tooling                                    |
| Buyer questions / context export / overview | Additional material derived from the repository and Curbpack results                   |
| `pathway` data / research material          | Setup and source information used while preparing documentation                        |
| Review package / buyer summary              | Material assembled for another person or organization to inspect                       |
| CycloneDX SBOM / OpenVEX drafts             | Generated software inventory and vulnerability-related draft data                      |
| Git Notes attestation                       | Data recorded for a repository state; may optionally contain a cryptographic signature |
| Explanation material                        | Sanitized information intended to help explain findings                                |

None of these files is, by itself, a certificate of conformity.

A successful check reports the result of configured rules against a particular repository state.

## 9. Attestation and installation integrity

The attestation state hash is derived from:

```text
commit | parent | sbom_digest | vex_digest
```

Wall-clock time is not included in that hash.

Possible signing states include:

| State                     | Meaning                                                              |
| ------------------------- | -------------------------------------------------------------------- |
| `ssh-agent-signed`        | An SSH signature was produced                                        |
| `not-verified` / unsigned | The record exists but no verified cryptographic signature is present |

Synthetic `agent-bind:` values are not accepted as verified signatures.

Installation through `install.sh`, `install.ps1`, and the GitHub Action verifies release checksums using SHA-256 and fails if the checksum does not match.

Network pack updates require a SHA-256 pin.

Offline pack import is also supported.

`curbpack doctor --repair` repairs local PATH or alias configuration. It does not download or automatically update Curbpack.

## 10. What Curbpack does not claim

Curbpack does not:

* certify regulatory conformity;
* issue or grant CE marking;
* replace notified bodies, auditors, or legal advisers;
* guarantee that software contains no vulnerabilities;
* claim that passing checks establishes market access.

Development is supported by RISE Research Institutes of Sweden as applied research and competence development.

RISE does not certify products based on Curbpack check results.

Public project pages hosted by RISE identify and describe the project. They do not constitute approval of products using Curbpack.

Public wording must not claim that a product is “RISE-approved”, “NCSC-approved”, or approved by another authority unless such approval actually exists.

Repository scripts currently check some documentation wording automatically.

## 11. Limitations

* Results depend on the quality and coverage of the selected packs.
* A pack with few or weak rules can give an incomplete picture.
* Regex and text checks are limited heuristics, not full program analysis.
* SBOM and VEX generation is best-effort and currently based on supported dependency formats.
* The local CLI is released for macOS, Linux, and Windows amd64.
* GitHub Action support is limited to the documented runner platforms.
* The optional Unix-socket integration is platform-specific.
* `doctor --repair` only repairs local configuration; it does not reinstall a missing binary.
* Local hash verification does not provide an external notary service.
* `pathway suggest` selects from the known pack catalogue. It does not create new regulations or pack identifiers.

## 12. Terms

| Term                      | Meaning                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| **CE**                    | European conformity marking. Curbpack does not issue CE marks.                                |
| **CRA**                   | EU Cyber Resilience Act. Some packs may contain checks derived from CRA-related requirements. |
| **`pathway`**             | Optional guided setup commands.                                                               |
| **Citation check**        | Checks whether configured claims contain citations to the prepared source material.           |
| **Research material**     | Sources and summaries used while preparing documentation.                                     |
| **SBOM**                  | Software Bill of Materials.                                                                   |
| **SARIF**                 | Static Analysis Results Interchange Format.                                                   |
| **GRC**                   | Governance, Risk and Compliance software.                                                     |
| **Rule pack**             | A set of rules evaluated by Curbpack.                                                         |
| **Review package**        | Files assembled for human review or handoff.                                                  |
| **Buyer summary**         | Short summary intended for a receiving organization.                                          |
| **Context export**        | Repository and result information exported for another tool or workflow.                      |
| **Repository evidence**   | Repository files and generated results used during review.                                    |
| **Notified body**         | An organization designated to perform specified conformity-assessment activities.             |
| **Conformity assessment** | Formal process for determining whether applicable conformity requirements are fulfilled.      |
| **VEX**                   | Vulnerability Exploitability eXchange.                                                        |
| **ReDoS**                 | Regular expression denial of service.                                                         |
| **OPA**                   | Open Policy Agent.                                                                            |

## 13. Related documentation

* Public project site: https://ri-se.github.io/curbpack/
* Product scope: `docs/intent-vs-scope.md`
* Information for authorities: `docs/for-authorities.md`
* Security model: `docs/security-model.md`
* Installation and commands: repository README
* Wording rules: `docs/voice-and-terms.md`
* CLI workflow: `docs/assistant-loop.md`

---

*Document version aligned with the Curbpack open-source line `@v0.5.2`.*
