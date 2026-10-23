# Future CI/CD policy

**Status:** Not in force. Studio has no Makefile and no CI workflow. Do not add them during the pilot.

This file takes effect when EP-01 is accepted, by moving it to `policies/cicd.md`. The full layout below is the target. The first slice is only `make test` and `make ci-tests`, both running the same existing test scripts. Docker, scanners, SBOM, and signing wait until there is a real artifact to build, scan, and sign. Omit commands the project does not have.

**Applies to:** Projects that build, test and distribute software. Independent of language, Git provider and CI service.

> **Build once. Test the actual deliverable. Promote the verified artifact.**

## 1. Principles

1. **Scripts do the work.** Every test, security check, build, packaging step and release operation is an independently executable, version-controlled script. Make and CI only invoke the scripts. Neither duplicates their logic.
2. **Few Make commands.** Make is the human interface, not a separate target for every tool. `make` without arguments displays available commands. Individual CI checks are selected with `ONLY=...`.
3. **Local = CI.** The same scripts, configuration and tools run locally and in CI. A dev container can reproduce the Linux CI environment. Windows and macOS deliverables must also be built and verified on their target platforms.
4. **Separate outcomes.** Each executed script reports its own named `[PASS]` or `[FAIL]`, reason and exit status. The aggregate result fails if any mandatory check fails. No silent skips, suppressed errors or CI-only shortcuts.
5. **Immutable candidate.** Build a candidate once per target platform and configuration. Smoke-test and scan the actual executable or production image. Sign and promote exactly those verified bytes and digests, without rebuilding.
6. **Release is deliberate.** PR and branch checks never publish production releases. Promotion and deployment require explicit authorization. Tests do not commit, push, release or destructively modify the working tree.

## 2. Small Make interface

| Command | Meaning |
| --- | --- |
| `make` | Show available commands and short explanations. Default target. |
| `make start` | Start the application locally, where applicable. |
| `make test` | Run all functional tests, with named `[PASS]` / `[FAIL]` and a summary. |
| `make ci-tests` | Run all mandatory CI checks, including functional tests and enabled security checks. |
| `make ci-tests ONLY=sast` | Run only the named check, for development and debugging. |
| `make run-docker-dev` | Start the dev or test container locally, where applicable. |
| `make run-docker-prod` | Start the production container locally, where applicable. |

No `make sast`, `make secrets`, `make vuln`, `make sbom` or `make sign`. Do not add one Make target per script. Projects may omit irrelevant start and Docker commands and may document a genuinely necessary extra user-facing entry point.

`make ci-tests ONLY=vuln` reruns one check. `ONLY` must never reduce a release pipeline's mandatory gate.

## 3. Individually executable scripts

Example layout. Names may vary. Document the registry in one place.

```text
Makefile
scripts/
  test/run.sh
  ci/run.sh
  ci/checks/tests.sh
  ci/checks/sast.sh
  ci/checks/secrets.sh
  ci/checks/vuln.sh
  ci/checks/image-scan.sh
  build/package.sh
  build/docker-dev.sh
  build/docker-prod.sh
  release/sbom.sh
  release/sign.sh
  release/promote.sh
  run/start.sh
  run/docker-dev.sh
  run/docker-prod.sh
```

- Each script can be run directly, without Make or CI, and returns `0` on success and nonzero on failure.
- `scripts/ci/run.sh` runs the registered mandatory checks in a stable order, or exactly one check when `ONLY` is set. An unknown `ONLY` value fails and lists the valid names.
- `make test` and the `tests` CI check execute the same test scripts, not two suites. Tests may use reusable reference-repository states prepared by dedicated setup scripts.
- Use green and red when the terminal supports color. Text labels and exit codes must work without color in CI logs. Show an aggregate summary without hiding an individual failure.
- SBOM generation, artifact signing and promotion are separate scripts, not security tests. Their results are recorded as separate pipeline steps. A check may validate their outputs without generating them again.

## 4. CI orchestration

CI only selects environments and invokes the same commands used locally.

1. **Checks.** `make ci-tests`, or separate jobs using `make ci-tests ONLY=<check>` so each result is visible. The required aggregate gate still includes every mandatory check.
2. **Build.** Call the version-controlled package and Docker build scripts on the supported runners. Retain the versioned candidates, the source commit, and the SHA-256 or image digests.
3. **Verify.** Run independent smoke and end-to-end scripts against the candidate binaries and the production image. The dev image does not stand in for the production image. Use readiness checks and clean up on failure.
4. **Security and evidence.** Invoke the scanner and CycloneDX scripts for the actual built artifacts. Record tool versions, findings and the thresholds that were applied.
5. **Sign and promote.** Only after the required checks have passed. Copy or retag by the verified digest. Do not rebuild. Deploy separately.

Windows EXE, Linux executable, macOS executable and the production container are distinct artifacts. Each one that the project ships is verified. CI must not contain a second implementation of any operation. A future Git hook calls `make ci-tests`, or a documented `ONLY` subset, not its own checks.

## 5. SSDF traceability

Map checks and their retained evidence to NIST SP 800-218, SSDF 1.1. Running one script does not establish conformance to a whole practice.

| Check | Practice |
| --- | --- |
| Tests and end-to-end | PW.8 |
| `sast` | PW.7 |
| `vuln` | PW.4, RV.1 |
| `secrets` | PS.1 |
| SBOM and provenance | PS.3 |
| Signing and release integrity | PS.2 |
| Secure build and deployment configuration | PW.6 |

PW.1 is the design in [`future_architecture.md`](future_architecture.md), not a scanner. Actual coverage, remediation, exceptions and thresholds belong to the project and to `docs/ssdf/`.

**Source:** https://csrc.nist.gov/pubs/sp/800/218/final
