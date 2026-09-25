# Curbpack User Guides

These user guides show how to use Curbpack from installation through development, CI, and review.

| Guide | What it shows |
|---|---|
| [Install Curbpack](install.md) | Install and verify the Curbpack CLI |
| [Getting started](getting-started.md) | Try Curbpack on the reference product and understand packs, evidence, and check results |
| [Developer guide](developers.md) | Use Curbpack in a real product repository and handle findings |
| [CI/CD](ci-cd.md) | Run `curbpack check` automatically in CI |
| [Reviewers](reviewers.md) | Review Curbpack results and supporting evidence |
| [Troubleshooting](troubleshooting.md) | Solve common installation and runtime problems |

## Typical Workflow

1. **Install Curbpack** - Install the CLI and make sure the `curbpack` command is available. **Guide:** [Install Curbpack](install.md)
2. **Run `curbpack doctor`** - Check that the installation and local environment are usable. **Guide:** [Install Curbpack](install.md)
3. **Run `curbpack demo`** - Run the built-in demonstration as a quick smoke test. **Guide:** [Install Curbpack](install.md)
4. **Try Curbpack on the reference product** - Learn how packs, evidence, checks, and results relate. **Guide:** [Getting started](getting-started.md)
5. **Scan your own repository** - Inspect an existing repository before initializing Curbpack. **Guide:** [Developer guide](developers.md)
6. **Initialize Curbpack** - Configure Curbpack and select the packs to use. **Guide:** [Developer guide](developers.md)
7. **Run `curbpack check`** - Evaluate the repository against the selected rules. **Guide:** [Developer guide](developers.md)
8. **Understand and fix findings** - Inspect failed checks and supporting evidence, then make the necessary changes. **Guide:** [Developer guide](developers.md)
9. **Run `curbpack check` again** - Re-run the checks after changes. **Guide:** [Developer guide](developers.md)
10. **Share review material** - Prepare the results and supporting material for another person to review. **Guide:** [Developer guide](developers.md)
11. **Human attests** - A human records an attestation for the reviewed repository state. **Guide:** [Developer guide](developers.md)
12. **Reviewer receives the review pack** - The reviewer receives the results and supporting evidence. **Guide:** [Reviewers](reviewers.md)
13. **Review the material** - Inspect the supplied findings, results, and evidence. **Guide:** [Reviewers](reviewers.md)
14. **Run `check` or `drift` after later changes** - Re-check the repository when it changes and, where useful, inspect drift from an earlier state. **Guide:** [Developer guide](developers.md)

CI can run the same `curbpack check` automatically during development. See [CI/CD](ci-cd.md).

Developers normally follow the workflow from installation through sharing. Reviewers normally start when they receive the review material.

## Reference Documentation

For exact commands, configuration, output formats, and pack structure, use the reference documentation under [References](../reference/README.md).
