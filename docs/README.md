# Curbpack Documentation
 
Start with the shortest path for what you need to do.

## Start Here
The first table lets you navigate based on your current role and the second table maps a concrete goal to some nifty dockument
| You are | Start here |
| --- | --- |
| **New user** | [Install](user-guides/install.md) · [Getting Started](user-guides/getting-started.md) |
| **Builder / product team** | [Builder Guide](user-guides/developers.md) · [CI/CD](user-guides/ci-cd.md) |
| **Buyer / reviewer** | [Reviewer Guide](user-guides/reviewers.md) |
| **Authority / auditor** | [Reviewer Guide](user-guides/reviewers.md) |
| **Pack author** | [Pack Author Guide](user-guides/pack-developers.md) |
| **Curbpack contributor** | [Contributor Guide](development/README.md) · [Testing](testing/README.md) |

| Goal                                                      | Read                                            |
| --------------------------------------------------------- | ----------------------------------------------- |
| Install Curbpack                                          | [Install Curbpack](user-guides/install.md)           |
| Try Curbpack on the reference product                     | [Getting started](user-guides/getting-started.md)    |
| Use Curbpack in a product repository                      | [Developer guide](user-guides/developers.md)         |
| Run Curbpack in CI/CD                                     | [CI/CD guide](user-guides/ci-cd.md)                  |
| Review Curbpack results, evidence, and review material | [Reviewer guide](user-guides/reviewers.md)           |
| Write or maintain a rule pack                          | [Pack development](user-guides/pack-developers.md)   |

## Common Tasks

| Task                                                            | Read                                                  |
| --------------------------------------------------------------- | ----------------------------------------------------- |
| Select and configure packs                                      | [Configuration reference](reference/configuration.md) |
| Understand how packs work                                       | [Packs](concepts/packs.md)                            |
| Understand repository evidence and results                      | [Evidence](concepts/evidence.md)                      |
| Understand the main Curbpack flow, including `scan` and `check` | [Concepts overview](concepts/README.md)               |
| Prepare material for another person to review                   | [Developer guide](user-guides/developers.md)               |
| Review received material                                        | [Reviewer guide](user-guides/reviewers.md)                 |
| Create or maintain a custom pack                                | [Pack development](user-guides/pack-developers.md)         |
| Run the verification test suites                                | [Testing](testing/README.md)                          |

## Understanding the Curbpack Concepts

| Subject                                                | Read                                         |
| ------------------------------------------------------ | -------------------------------------------- |
| What Curbpack does and how the main parts fit together | [Concepts overview](concepts/README.md)      |
| Packs and rules                                        | [Packs](concepts/packs.md)                   |
| Evidence and review material                           | [Evidence](concepts/evidence.md)             |
| Current implementation architecture                    | [Architecture](development/architecture.md) |

## Technical Reference

Use the reference documentation when you need exact commands, fields, paths, or output formats.

| Reference                                   | Purpose                                                     |
| ------------------------------------------- | ----------------------------------------------------------- |
| [CLI](reference/cli.md)                     | Commands, flags, aliases, and exit codes                    |
| [Configuration](reference/configuration.md) | `.curbpack.json`, pack selection, and environment variables |
| [Packs](reference/packs.md)                 | Pack schema, rule fields, check types, and composition      |
| [Outputs](reference/outputs.md)             | Generated files, formats, and locations                     |

 
## Papers and Background Material

Longer background and research material is kept under:

* [Papers](papers/)

These documents provide context and discussion. They are not the primary source for command or configuration behavior.
