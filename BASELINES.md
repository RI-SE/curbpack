# Baselines

Three-repository tags `baseline/<YYYY-MM-DD>-<NAME>` on Curbpack, CTAM, and cyberready-test-product.

The tagged commits do not include later updates to this registry.

Each create requires `OVERRIDE_TESTS=1`. Tests are not run by the baseline command.

Checkout: `make checkout-baseline NAME=<name>` then `make start-verification-run`.

## baseline/2026-09-17-olof-review-1

- tag: baseline/2026-09-17-olof-review-1
- date: 2026-09-17
- name: olof-review-1
- curbpack: 7c7ed74e8344fe0c688a0e91f0f9d49dccb88d60
- ctam: ed2c2ed959c50e8e4168deca44494e19aa44a0a7
- reference-product: dee885ffb421e4646fea07fbb4a629616c09efc6
- verification: tests were externally verified; OVERRIDE_TESTS=1
