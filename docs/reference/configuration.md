# Configuration reference

Curbpack configuration is stored in `.curbpack.json` in the product repository.

This page describes the current configuration file, pack-selection precedence, supported runtime configuration, and Curbpack repository paths.

## `.curbpack.json`

### Fields

| Field     | JSON type       | Optional | Behavior                             |
| --------- | --------------- | -------: | ------------------------------------ |
| `packs`   | `array<string>` |      Yes | Pack IDs selected for the repository |
| `hooks`   | `boolean`       |      Yes | Stored hook setting                  |
| `version` | `string`        |      Yes | Stored configuration version         |
| `claim`   | `string`        |      Yes | Stored claim text                    |

### Example

```json
{
  "packs": [
    "house-policy",
    "medtech-iec62304"
  ]
}
```

`curbpack init` creates `.curbpack.json`. The `packs` entry identifies the packs that `curbpack check` evaluates unless the selection is overridden on the command line.

### `claim`

When Curbpack writes configuration and `claim` is empty, the current implementation inserts its built-in default claim text.

## Pack selection

For the normal check path, active pack IDs are resolved in this order:

1. pack IDs supplied on the command line;
2. `packs` from `.curbpack.json`;
3. fallback pack `house-policy`.

For example:

```bash
curbpack check --packs house-policy,cra-baseline
```

uses the CLI selection for that invocation instead of the `packs` entry in `.curbpack.json`.

### `scan`

`scan` uses a different fallback when no pack selection is available.

Its resolution order is:

1. pack IDs supplied on the command line;
2. `packs` from `.curbpack.json`;
3. fallback pack `cra-baseline`.

## Pack sources

Curbpack normally loads pack definitions embedded in the executable.

A local pack directory can override the embedded pack definitions:

```bash
export CURBPACK_PACKS_DIR=/path/to/packs
```

For pack ID `<pack-id>`, Curbpack looks for:

```text
<directory>/<pack-id>/pack.json
```

The local definition takes precedence over the embedded definition when present.

If the local lookup fails with an error other than the file not existing, pack loading fails rather than silently falling back to the embedded pack.

The structure of `pack.json` is documented separately in the pack reference.

## Runtime environment variables

### Pack loading and updates

| Variable                | Value                           | Behavior                                                 |
| ----------------------- | ------------------------------- | -------------------------------------------------------- |
| `CURBPACK_PACKS_DIR`    | filesystem path                 | Overrides the source directory used for pack definitions |
| `CURBPACK_PACKS_URL`    | URL/string                      | Source used by `curbpack packs update`                   |
| `CURBPACK_PACKS_SHA256` | 64-character hexadecimal string | Integrity pin required by `curbpack packs update`        |

`curbpack packs update` requires both `CURBPACK_PACKS_URL` and a valid `CURBPACK_PACKS_SHA256`. The network update is refused when the required pin is missing or invalid.

### Human confirmation and explain export

| Variable                       | Value | Behavior                                                                |
| ------------------------------ | ----- | ----------------------------------------------------------------------- |
| `CURBPACK_ALLOW_CONFIRM`       | `"1"` | Allows human confirmation commands (`confirm-*`) that require this setting |
| `CURBPACK_EXPLAIN_ALLOW_CLOUD` | `"1"` | Enables cloud explain export                                            |

Cloud explain export is disabled unless explicitly enabled.

### Attestation verification

| Variable                   | Value           | Behavior                                                         |
| -------------------------- | --------------- | ---------------------------------------------------------------- |
| `CURBPACK_ALLOWED_SIGNERS` | filesystem path | Optional signer-policy path used during attestation verification |
| `CURBPACK_SIGNER_ID`       | string          | Principal identity used during attestation verification          |

### Advanced / integration-specific

These variables are not part of the normal `.curbpack.json` and pack-selection flow. They support optional identity and bridge integrations.

| Variable              | Value       | Behavior                                                                 |
| --------------------- | ----------- | ------------------------------------------------------------------------ |
| `CURBPACK_AGENT_ID`   | string      | Self-declared identity input included in the IR identity payload         |
| `CURBPACK_MODEL_HASH` | string      | Self-declared model identity input included in the IR identity payload   |
| `CURBPACK_MANDATE_ID` | string      | Self-declared mandate identity input included in the IR identity payload |
| `CURBPACK_SOCK`       | socket path | Socket path used by socket-backed identity or bridge flows               |

## Repository paths

Current Curbpack repository state is stored under the following paths:

| Purpose       | Path                        |
| ------------- | --------------------------- |
| Configuration | `.curbpack.json`            |
| Cache         | `.github/curbpack/cache`    |
| Evidence      | `.github/curbpack/evidence` |
| Graph         | `.github/curbpack/graph`    |

These paths are used for Curbpack configuration and generated repository state. Individual commands may create additional output; see the output reference for generated artifacts.
