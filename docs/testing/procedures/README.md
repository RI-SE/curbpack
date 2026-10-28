# Test setup

A carried case uses repository state R1 and pack input PF-01. The runner is:

```sh
python3 -m checks \
  --repo <prepared-repo> \
  --packs <prepared-repo>/external_test/curbpack-studio/packs \
  --out <prepared-repo>/run-result.json
```

`--packs` is the Studio fixture directory on the clone. The pack ids live in `curbpack.json`. The runner reads that file and `<prepared-repo>/claims/`. It does not read `.curbpack.json` or `CURBPACK_PACKS_DIR`.

## Prepare a verification run

Do this once before any case. From the Studio root:

```sh
make start-verification-run
source tmp/verification-run.sh
```

`scripts/start-verification-run.sh` records the Studio commit, the pin in `tests/cyberready-test-product.pin`, and today's date. It clones into `tmp/cyberready-test-product`. Sourcing the filled file deletes that clone and clones it again at the pin, then prints `Verification run configuration: OK`.

Start every independent case by sourcing `tmp/verification-run.sh` again.

## Prepare the carried cases (R1, PF-01)

On the clone, after the source:

1. Apply R1 with the Studio fixture. The script file is not edited.

   ```sh
   cd "$REFERENCE_PRODUCT_ROOT/external_test/curbpack-studio"
   SUT=curbpack-studio ./setup.sh R1 --commit
   ```

2. Write `$REFERENCE_PRODUCT_ROOT/curbpack.json`:

   ```json
   {"packs":["cra-baseline","house-policy","medtech-iec62304"]}
   ```

3. Copy only these files from `external_test/curbpack-studio/claims/` into `$REFERENCE_PRODUCT_ROOT/claims/`:

   - `CRA-ANNEX-VII-MANUAL.json`
   - `CRA-ANNEX-VII-RISK.json`
   - `CRA-ANNEX-VII-SUPPORT.json`
   - `CRA-ART14-PATH.json`
   - `HOUSE-ANTI-PLACEHOLDER.json`
   - `HOUSE-SECURITY-MD.json`
   - `HOUSE-SECURITY-TXT.json`

4. From the Studio root, run the argv in the section above with `--repo` and `--packs` pointing at the clone.

Stdout `claims 7 exit 0` and no claim status `fail` is the pass. Manual rows are printed by `make test-curbcheck` and are not part of the count. The seven expected statuses are in [cases.md](cases.md).

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

The Studio script is `external_test/curbpack-studio/setup.sh <id> --commit`, which runs `external_test/curbpack-studio/states/<id>.sh`. Those state files stay byte-identical to `external_test/curbpack/states/`. This suite does not replace them.

R8 and R9 are defined in `../ctam/docs/testing/procedures.md`. They are in [outside.md](../outside.md). This suite does not run them.

## Pack inputs

Definitions: [1. Pack inputs](1_pack_template_instantiation.md).

PF-01 is the pack set above, loaded from `external_test/curbpack-studio/packs` on the clone. PF-02 through PF-17 keep their product effects and are not carried cases. The selector remains `external_test/curbpack-studio/mutate_pack.sh <PF-id>`. This suite does not replace that script.

PF-18 and PF-19 are defined in `../ctam/docs/testing/procedures.md`. They are in [outside.md](../outside.md).

## Execution configurations

These do not redefine R or PF.

| ID | Condition | Preparation |
| --- | --- | --- |
| EC-01 | Recorded commit and clean worktree after `setup.sh R1 --commit` when that commit leaves a clean tree | R1 on the pin leaves the tree unmodified |
| EC-02 | Dirty worktree | Not used by a carried case. |
| EC-03 | Detached HEAD | Not used by a carried case. |
| EC-04 | Shallow clone | Not specified. Not a carried case. |
| EC-05 | Sparse checkout, linked worktree, or submodule | Not specified. Not a carried case. |
| EC-06 | Offline | Not specified. Not a carried case. |
| EC-07 | Locale or timezone variation | Not specified. Not a carried case. |
| EC-08 | Concurrent local execution | Not specified. Not a carried case. |
| EC-09 | Output failure injection | Not specified. Not a carried case. |
| EC-10 | Platform execution | Not specified. Not a carried case. |

## TST-01 archive record

TST-01 prepared a tree outside the Studio work tree with `git archive` of `dee885ffb421e4646fea07fbb4a629616c09efc6` and packs from `docs/reference/test-packs`. That record is not this command. After REF-01 the carried run uses the clone, `external_test/curbpack-studio`, and the steps above.
