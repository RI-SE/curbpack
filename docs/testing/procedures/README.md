# Test setup

A carried case uses repository state R1 and pack input PF-01. The runner is:

```sh
python3 -m checks --repo <prepared-repo> --packs docs/reference/test-packs --out <prepared-repo>/run-result.json
```

`--packs` is the directory. The pack ids live in `curbpack.json`. The runner reads that file and `<prepared-repo>/claims/`. It does not read `.curbpack.json` or `CURBPACK_PACKS_DIR`.

## Prepare the suite repo

From the Studio root, `make test-curbcheck` clones the pinned reference product, restores it by sourcing `tmp/verification-run.sh`, applies R1 with the product's `setup.sh`, and runs the seven carried checks. It does not archive a checkout. The earlier archive of `dee885ffb421e4646fea07fbb4a629616c09efc6` is the record of how TST-01 prepared a tree. It is not this command.

`make test-curbcheck` does this:

1. Clone `git@github.com:RI-SE/cyberready-test-product.git` at the commit in `tests/cyberready-test-product.pin` into `tmp/cyberready-test-product`.
2. Source `tmp/verification-run.sh`, which deletes that clone and clones it again at the same commit.
3. On the clone, `./external_test/curbpack/setup.sh R1 --commit`. The script file is not edited.
4. Write `curbpack.json` with packs `cra-baseline`, `house-policy`, and `medtech-iec62304`.
5. Copy the seven claim files from `docs/reference/test-packs/claims/` into the clone's `claims/`.
6. Run `python3 -m checks --repo <clone> --packs docs/reference/test-packs --out <clone>/run-result.json`.

Stdout `claims 7 exit 0` and no claim status `fail` is the pass. Manual rows are printed after that and are not part of the count.

## TST-01 archive record

TST-01 prepared a tree outside the Studio work tree. Do not edit `/Users/DanielFl/Documents/aProjects/aslak/cyberready-test-product`.

1. Extract reference-product commit `dee885ffb421e4646fea07fbb4a629616c09efc6`:

   ```sh
   git -C /Users/DanielFl/Documents/aProjects/aslak/cyberready-test-product archive dee885ffb421e4646fea07fbb4a629616c09efc6 | tar -x -C <prepared-repo>
   ```

   That tree is R1 content: the starting Glucose Log files. The case does not run `external_test/curbpack/setup.sh` and does not edit `states/R1.sh`.

2. Write `<prepared-repo>/curbpack.json`:

   ```json
   {"packs":["cra-baseline","house-policy","medtech-iec62304"]}
   ```

   Those three ids are PF-01. They are loaded from `docs/reference/test-packs`, not from `external_test/curbpack/packs`.

3. Copy only these files into `<prepared-repo>/claims/`:

   - `CRA-ANNEX-VII-MANUAL.json`
   - `CRA-ANNEX-VII-RISK.json`
   - `CRA-ANNEX-VII-SUPPORT.json`
   - `CRA-ART14-PATH.json`
   - `HOUSE-ANTI-PLACEHOLDER.json`
   - `HOUSE-SECURITY-MD.json`
   - `HOUSE-SECURITY-TXT.json`

   The source of each file is `docs/reference/test-packs/claims/<id>.json`.

4. Commit that tree inside `<prepared-repo>` so `git status --porcelain` there is empty. That commit is not a Studio commit and not a commit on the reference product.
5. Run the argv from the Studio root.
6. Delete `<prepared-repo>`.

Stdout `claims 7 exit 0` and no claim status `fail` is the suite pass. The seven expected statuses are in [cases.md](cases.md).

## Repository states

Definitions: [0. Controlled repository content](0_controlled_repo_setup.md).

| ID | Product effect | This suite |
| --- | --- | --- |
| R1 | Starting Glucose Log content | used by every carried case |
| R2 | R1 with `SECURITY.md` absent, not empty | not run |
| R3 | R1 with heading `## Classification Rationale` removed from `docs/medtech/software_safety_class.md` | not run |
| R4 | demo-app content, token-only honesty-eval `SECURITY.md`, `package.json` name `acme-widget` | not run |
| R5 | demo-app content, thin rule-satisfying honesty-eval `SECURITY.md`, original demo-app `package.json` | not run |
| R6 | R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as `Owner <owner@example.com>` dated `2022-01-01T00:00:00Z` | not run |
| R7 | R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as `Wrong Author <wrong@example.com>` dated `2026-09-13T12:00:00Z` | not run |

The script for R1–R7 remains `external_test/curbpack/setup.sh <id> --commit`, which runs `external_test/curbpack/states/<id>.sh`. This suite does not replace that script.

R8 and R9 are defined in `ctam/docs/testing/procedures.md`. They are in [outside.md](../outside.md). This suite does not run them.

## Pack inputs

Definitions: [1. Pack inputs](1_pack_template_instantiation.md).

PF-01 is the pack set above. PF-02 through PF-17 keep their product effects and are not carried cases. The selector on the reference product remains `external_test/curbpack/mutate_pack.sh <PF-id>`. This suite does not replace that script.

PF-18 and PF-19 are defined in `ctam/docs/testing/procedures.md`. They are in [outside.md](../outside.md).

## Execution configurations

These do not redefine R or PF.

| ID | Condition | Preparation |
| --- | --- | --- |
| EC-01 | Recorded commit and clean worktree in the temporary repo | The commit in step 4 above. `git status --porcelain` is empty. |
| EC-02 | Dirty worktree | Not used by a carried case. |
| EC-03 | Detached HEAD | Not used by a carried case. |
| EC-04 | Shallow clone | Not specified. Not a carried case. |
| EC-05 | Sparse checkout, linked worktree, or submodule | Not specified. Not a carried case. |
| EC-06 | Offline | Not specified. Not a carried case. |
| EC-07 | Locale or timezone variation | Not specified. Not a carried case. |
| EC-08 | Concurrent local execution | Not specified. Not a carried case. |
| EC-09 | Output failure injection | Not specified. Not a carried case. |
| EC-10 | Platform execution | Not specified. Not a carried case. |
