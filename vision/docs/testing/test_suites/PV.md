# PV — State and provenance

## Objective

The result must identify the examined repository state, Curbpack version,
selected pack identity and other required method information sufficiently for
independent review and reproduction.

## Test basis

Requirements addressed by this suite:

- MUST-31

Other test basis:

- SDD §1 portable-evidence and independent-inspection product claim.
- SDD §7.3 frozen, independently authored evidence expectations.

A test execution is always part of a test run that starts with [Prepare a verification run](../procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare R1 via product `setup.sh` on that already-restored baseline. Then apply EC as the case states. PV-006 keeps that same R1 checkout and selects PF-06 with `mutate_pack.sh`. It does not create an R-id or a `tmp/R*` repository.

## Test suite overview


| ID     | Test case / purpose                                               | Requirements addressed | Test class | Procedure status |
| ------ | ----------------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| PV-001 | Clean committed HEAD SHA on the result (EC-01)                    | MUST-31                | A          | Executable       |
| PV-002 | Dirty working-tree bytes in cache file identity (EC-02)           | MUST-31                | A          | Executable       |
| PV-003 | Detached HEAD is not reported as a named branch (EC-03)           | —                      | A          | Executable       |
| PV-004 | Shallow clone / other Git-state variants (EC-04, EC-05)           | —                      | C          | To be specified  |
| PV-005 | Pack id, version, and sha256 on cache pack_sources                | MUST-31                | A          | Executable       |
| PV-006 | Pack-byte substitution visible in cache pack_sources              | MUST-31                | A          | Executable       |
| PV-007 | Evaluator version and explicit as_of on cache/receipt             | MUST-31                | A          | Executable       |


---

## PV-001 — Verify that a clean committed HEAD SHA is present on the result

### Requirements

- MUST-31

This case covers only the commit-SHA slice of MUST-31’s repository-snapshot
clause, on a clean EC-01 tree. It records `concurrency_control.expected_parent_commit_sha`
on stdout and `subject_commit` with `subject_commit_status` `claimed` in the
cache file. It does not show that the evaluation input is the repository
snapshot: tree bytes, dirty-state identity, pack bytes, trust policy,
evaluator version, and explicit `as_of` are not this case. A pass does not
close MUST-31.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `git rev-parse HEAD`                                                                                                                             | Prints the 40-character commit SHA of this prepared tree. Record it.                                                                                                                                                                                                                                                                                            |


### TEST STEPS


| Step | Action                                                                          | Expected result                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"`                                   | The command completes successfully. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. `concurrency_control.expected_parent_commit_sha` equals the SHA from SETUP step 5. Verify the last fields against Fig. 1. |
| 2    | `echo $?`                                                                       | The exit status is `0`.                                                                                                                                                                                         |
| 3    | `grep -A2 subject_commit .github/curbpack/cache/latest_evaluation.json`         | `subject_commit` equals the SHA from SETUP step 5. `subject_commit_status` is `claimed`.                                                                                                                        |


```json
{
  "failures": null,
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 100,
  "outcome": "pass",
  "evaluated_rules": 15,
  "conformity_claim": "none"
}
```

**Fig. 1.** Example of the last fields after Step 1. Same R1 / PF-01 / EC-01 check as EV-001.

Empty lists in this JSON are encoded as `null`, not `[]`. This applies to both `failures` and `failed_orthogonal_regions`. A successful result has `"outcome": "pass"` and no failure objects under `failures`. `state_version_token` is `v3.33-OCC`.

---

## PV-002 — Verify that dirty working-tree bytes appear in cache file identity

### Requirements

- MUST-31

This case covers only whether dirty `SECURITY.md` bytes change
`input_identity.files[].sha256` in the cache file. Observed: stdout
`check --json` still reports `expected_parent_commit_sha` and
`subject_commit` as the HEAD commit. It does not refuse, and it does not
print a dirty-tree field. That is not identification of the working tree as
the evaluation input. A pass does not close MUST-31’s repository-snapshot
clause.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3. Step 6 appends to `SECURITY.md`. That edit is EC-02 stimulus, not a new R-id.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-02](../procedures/README.md#execution-configurations) — established and verified by steps 6–7. After step 6 the working tree is no longer EC-01.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `git rev-parse HEAD`                                                                                                                             | Prints the 40-character commit SHA. Record it.                                                                                                                                                                                                                                                                                                                  |
| 6    | `printf '\nPV-002 uncommitted marker\n' >> SECURITY.md`                                                                                          | The file `SECURITY.md` now contains that extra line.                                                                                                                                                                                                                                                                                                            |
| 7    | `git status --porcelain`                                                                                                                         | ` M SECURITY.md`                                                                                                                                                                                                                                                                                                                                                |


### TEST STEPS


| Step | Action                                                                           | Expected result                                                                                                                                                                                                 |
| ---- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"`                                    | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Last fields match Fig. 2. `concurrency_control.expected_parent_commit_sha` equals the SHA from SETUP step 5. The command does not refuse. |
| 2    | `echo $?`                                                                        | The exit status is `0`.                                                                                                                                                                                         |
| 3    | `openssl dgst -sha256 SECURITY.md`                                               | Prints the working-tree digest of the dirty file. Record it.                                                                                                                                                    |
| 4    | `grep -A6 '"path": "SECURITY.md"' .github/curbpack/cache/latest_evaluation.json` | `state` is `file`. `sha256` equals the digest from Step 3, not the committed blob. `subject_commit` is still the SHA from SETUP step 5. `subject_commit_status` is `claimed`. |


```json
{
  "failures": null,
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 100,
  "outcome": "pass",
  "evaluated_rules": 15,
  "conformity_claim": "none"
}
```

**Fig. 2.** Example of the last fields after Step 1. Same last fields as Fig. 1. The dirty tree is not a fail of the pack rules.

---

## PV-003 — Verify that detached HEAD is not reported as a named branch

### Requirements

This case does not verify a specified requirement.

Other test basis:

- Catalogue purpose for EC-03: the result must not name a Git branch when HEAD is detached.

MUST-31’s repository-snapshot clause is commit/tree identity, not branch vs
detached HEAD. Observed: `check --json` reports the detached commit SHA and
does not print a branch name. It has no separate detached-HEAD field. A pass
on this case does not address MUST-31.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3. Step 5 detaches HEAD. That is EC-03 stimulus, not a new R-id.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-03](../procedures/README.md#execution-configurations) — established and verified by steps 5–7.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `git checkout --detach HEAD`                                                                                                                     | HEAD is detached at the current commit.                                                                                                                                                                                                                                                                                                                         |
| 6    | `git symbolic-ref -q HEAD; echo $?`                                                                                                              | The printed status is `1`. If the status is `0`, stop: HEAD still names a branch, so the case cannot be run.                                                                                                                                                                                                                                                    |
| 7    | `git rev-parse HEAD`                                                                                                                             | Prints the 40-character commit SHA. Record it.                                                                                                                                                                                                                                                                                                                  |


### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                                 |
| ---- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Last fields match Fig. 3. `concurrency_control.expected_parent_commit_sha` equals the SHA from SETUP step 7. The JSON does not name a Git branch. |
| 2    | `echo $?`                                     | The exit status is `0`.                                                                                                                                                                                         |


```json
{
  "failures": null,
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 100,
  "outcome": "pass",
  "evaluated_rules": 15,
  "conformity_claim": "none"
}
```

**Fig. 3.** Example of the last fields after Step 1.

---

## PV-004 — Verify shallow clone / other Git-state variants

### Requirements

This case does not verify a specified requirement.

Other test basis:

- Intended later: MUST-31 repository-snapshot variants under EC-04 and EC-05.

EC-04 and EC-05 are not yet specified. Do not invent those procedures here.
A pass cannot close MUST-31 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## PV-005 — Verify that pack id, version, and sha256 are present on cache pack_sources

### Requirements

- MUST-31

This case covers only pack identity records: stdout `pack_id` tokens plus
cache `input_identity.pack_sources` id, version, and sha256. That is not
MUST-31’s pack-bytes clause (byte substitution is PV-006). Trust policy is
not this case. PF-02 does not exist yet; do not invent a second instance.
A pass does not close MUST-31.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | Note the `id` and `version` in each selected `pack.json` under `external_test/curbpack/packs/`. Separately read `external_test/curbpack/packs/SOURCE.txt`. | `house-policy` version `0.1.0`, `cra-baseline` version `0.1.0`, `medtech-iec62304` version `0.2.0`. `SOURCE.txt` records a source repository and commit. That file does not contain pack IDs or versions. |


### TEST STEPS


| Step | Action                                                         | Expected result                                                                                                                                                                                                 |
| ---- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"`                  | The command completes successfully. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. Last fields match Fig. 4. `pack_id` is `house-policy,medtech-iec62304`. |
| 2    | `echo $?`                                                      | The exit status is `0`.                                                                                                                                                                                         |
| 3    | Read `pack_sources` in `.github/curbpack/cache/latest_evaluation.json` | The three PF-01 copies from SETUP step 5 are listed with those ids, versions, and the sha256 values in Fig. 5. The JSON does not claim Curbpack inferred the `SOURCE.txt` source commit. |


```json
{
  "failures": null,
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 100,
  "outcome": "pass",
  "evaluated_rules": 15,
  "conformity_claim": "none"
}
```

**Fig. 4.** Example of the last fields after Step 1. Same last fields as Fig. 1.


```json
{
  "pack_sources": [
    {
      "id": "house-policy",
      "version": "0.1.0",
      "sha256": "eb74fd06241b79608d614bb27c15e8afccf33ea54a5f9d1629ea09e167391e5d"
    },
    {
      "id": "cra-baseline",
      "version": "0.1.0",
      "sha256": "dd8987bcda3765290c8989fd69c97886f911702ba08896605389f5035c515499"
    },
    {
      "id": "medtech-iec62304",
      "version": "0.2.0",
      "sha256": "e041b748ee87341603b116763bedaa7269773e6a4c7e035d776da661f08dd469"
    }
  ]
}
```

**Fig. 5.** Example of `input_identity.pack_sources` in `latest_evaluation.json` after Step 1. `cra-baseline` is present here even though it is not a token in stdout `pack_id`.

---

## PV-006 — Verify that pack-byte substitution is visible in cache pack_sources

### Requirements

- MUST-31

This case covers only the cache-file slice of MUST-31’s pack-bytes clause:
a trailing-space mutation of `house-policy/pack.json` changes
`pack_sources` sha256 and `comparison_key` in `latest_evaluation.json`.
Observed: stdout `pack_id` and the last fields do not change. Reading only
stdout `pack_id` does not show the substitution. Trust policy, repository
snapshot, evaluator version, and explicit `as_of` are not this case. A pass
does not close MUST-31.

The pack is the stimulus. R1 is only the git root required to run `check`.
This case does not invent a new R-id.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack inputs: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) selected by `verification-run.sh`, then [PF-06](../procedures/1_pack_template_instantiation.md) selected by SETUP step 6. This is not an R-id and not a `tmp/R*` repository.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `curbpack check --json --as-of "$AS_OF_DATE"` while PF-01 is still selected. Write `.comparison_key` from `.github/curbpack/cache/latest_evaluation.json` to `$CURBPACK_ROOT/tmp/pv-006/pf01-comparison_key`. | Exit status is `0`. The PF-01 `comparison_key` file contains a non-empty string that is not `null`. This retained key is declared evidence for TEST STEPS 3, not the TEST STEPS stimulus. Otherwise, stop. |
| 6    | `./external_test/curbpack/mutate_pack.sh PF-06`                                                                                                  | Prints `mutate_pack.sh: PF-06` and installs `pf-fixtures/PF-06/house-policy/pack.json` onto `external_test/curbpack/packs/house-policy/pack.json`. `CURBPACK_PACKS_DIR` stays the verification-run value. Remain at `$REFERENCE_PRODUCT_ROOT`. |
| 7    | `ls "$CURBPACK_PACKS_DIR/house-policy/pack.json"`                                                                                                | The trailing-space `house-policy` pack file is present. Otherwise, stop.                                                                                                                                                                                                                                                                                         |


### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                                 |
| ---- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | The command completes. Last fields still match Fig. 4. stdout `pack_id` is still `house-policy,medtech-iec62304`. The run is not rejected. |
| 2    | `echo $?`                                     | The exit status is `0`.                                                                                                                                                                                         |
| 3    | Compare `pack_sources` in `.github/curbpack/cache/latest_evaluation.json` with Fig. 5. Compare `.comparison_key` with the PF-01 control file from SETUP step 5. | `house-policy` `sha256` is the Fig. 6 value, not the Fig. 5 value. `cra-baseline` and `medtech-iec62304` sha256 values are unchanged. `comparison_key` differs from the recorded PF-01 control. The substitution is not silent. |


```json
{
  "id": "house-policy",
  "version": "0.1.0",
  "sha256": "36f850200a1f5500d8add750d1567f6f790ff721e6946c2c048eecdb3122e5e8"
}
```

**Fig. 6.** Example of the `house-policy` `pack_sources` row after Step 1.

---

## PV-007 — Verify that evaluator version and explicit as_of appear on cache and receipt files

### Requirements

- MUST-31

This case covers only two MUST-31 include clauses, and only on cache/receipt
files: `input_identity.tool_version` (evaluator version) and receipt
`as_of_source` `explicit`. Observed: stdout `check --json` does not contain
`tool_version`, `method`, or `platform`.

`method` and `platform` are recorded on those files. Platform is operational
receipt data in SDD §3.2; it is not a MUST-31 evaluation input. Absence of
home path, username, and hostname in one cache file is not proof that MUST-31
excludes user, home directory, hostname, locale, implicit wall clock, or
filesystem order. Trust policy is not this case. A pass does not close
MUST-31.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |


### TEST STEPS


| Step | Action                                                               | Expected result                                                                                                                                                                                                 |
| ---- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"`                        | The command completes successfully. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. Last fields match Fig. 1. stdout does not contain `tool_version`, `method`, or `platform`. |
| 2    | `echo $?`                                                            | The exit status is `0`.                                                                                                                                                                                         |
| 3    | Read `.github/curbpack/cache/latest_evaluation.json` `input_identity` | `method` is `curbpack-gates:2`. `tool_version` is the frozen Curbpack tool version (this run: `0.5.5`). The file has no home path, username, or hostname. |
| 4    | Read `.github/curbpack/cache/latest_receipt.json`                     | `tool_version` matches Step 3. `platform` is present as `GOOS/GOARCH` (example on this run: `darwin/arm64`). `as_of_source` is `explicit`. Ignore `timestamp` and `evaluation_duration_ms`. |


```json
{
  "method": "curbpack-gates:2",
  "tool_version": "0.5.5"
}
```

**Fig. 7.** Example of the method and tool-version fields in `latest_evaluation.json` `input_identity` after Step 1.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. A required case that treats an
  omitted or substituted identity field as present on the channel it names
  is a failure. Recorded stdout omissions in PV-002, PV-006, and PV-007 are
  expected observations, not suite failures.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
