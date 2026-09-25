# Contributing

This page describes the current contribution process for the Curbpack repository.

For instructions on using Curbpack in a product repository, see [Getting started](../user-guides/getting-started.md) and the [Developer guide](../user-guides/developers.md).

## Workflow

A normal contribution follows this process:

1. Create a branch.
2. Make one coherent change.
3. Run the required local checks.
4. Commit the change.
5. Open a pull request.
6. Address review comments.
7. Merge after review and required checks have passed.

Keep pull requests focused. Avoid mixing unrelated refactoring, cleanup, documentation changes, and behavior changes.

## Git hooks

The repository currently uses Git hooks as part of the development process.

Use the hooks provided by the repository and do not normally bypass them.

If a hook fails, fix the reported problem or determine whether the check itself needs to be changed.

## Local validation

Before opening a pull request, run:

```sh
go test ./...
make test
```

For the full test procedure, suite structure, and verification requirements, see [Testing](../testing/README.md).

For changes affecting documentation, CLI text, packs, regulatory or assurance wording, security-sensitive code, or related repository policy, also run:

```sh
./scripts/claim-safety.sh
./scripts/redteam-pilot.sh
```

Run `curbpack check` after changes that affect repository documentation, dependencies, packs, or Curbpack-generated evidence.

Run any additional tests relevant to the code being changed.

## Pull requests

A pull request should:

* have one clear purpose;
* explain what changes and why;
* state which tests or checks were run;
* identify changes to public commands, outputs, configuration, packs, or stored formats;
* identify security-sensitive changes.

Changes to public behavior should update the corresponding documentation in the same pull request.

## Actions requiring human approval

Some operations represent explicit human decisions and must not be performed automatically on behalf of a maintainer.

These currently include:

* `trust-import`
* `review-sign`
* `confirm-*`
* `attest`
* `pin-bump`

Do not automatically confirm, attest, sign, import signer/trust-policy data, or change pinned versions without the required human approval.

Options such as `--i-am-human` are explicit acknowledgements in the current implementation. They are not proof of identity and must not be used by automation to pretend that a human made the decision.

A successful Curbpack check does not by itself authorize a merge, release, confirmation, attestation, or approval.

## Maintainer rules

Contributions must preserve the current product scope:

* Curbpack checks repository evidence against configured rules.
* It prepares results for human review.
* It does not perform certification or conformity assessment.
* Generated text must not imply that a human reviewed or approved something when they did not.
* Public functionality must not depend on private RISE tools.

Changes to pinned versions, pack identifiers, signing, signer and attestation configuration, or similar protected configuration require explicit maintainer review.

## Security-sensitive changes

Take extra care with changes involving:

* signatures and attestation verification;
* signer-policy and allowed-signers handling;
* pinned versions and pack identifiers;
* human-only commands such as `confirm-*`, `attest`, and `trust-import`.
