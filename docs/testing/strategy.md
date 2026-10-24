# Verification strategy

This suite verifies seven carried claims against one prepared repository. The runner is `python3 -m checks` with `--repo`, `--packs docs/reference/test-packs`, and `--out`, as [README.md](README.md) states. It reads `curbpack.json`. It does not read `.curbpack.json` or `CURBPACK_PACKS_DIR`.

## System under test

The system under test is that runner and the Packs v2 packs it loads. The reference product is test input. It is the Glucose Log tree at commit `dee885ffb421e4646fea07fbb4a629616c09efc6`, plus the `curbpack.json` and `claims/` files the procedure adds in a temporary checkout.

A passing check is not a legal conformity determination.

## Repository state and pack input

[R1](procedures/0_controlled_repo_setup.md) is the product content for every carried case. [R2](procedures/0_controlled_repo_setup.md) through [R7](procedures/0_controlled_repo_setup.md) keep the product effects in that file. This suite does not run them.

[PF-01](procedures/1_pack_template_instantiation.md) is pack ids `cra-baseline`, `house-policy`, and `medtech-iec62304`. PF-02 through PF-17 keep the product effects in that file. This suite does not run them.

R8, R9, PF-18, and PF-19 stay defined in `ctam/docs/testing/procedures.md`. They are listed in [outside.md](outside.md). This suite does not run them.

State scripts under the reference product are not edited and are not replaced.

## Carried cases

The carried cases are the seven ids in [procedures/cases.md](procedures/cases.md). Each expected status is `pass`. The process exits 0 only when all seven are `pass` and the fail count is 0.

## Outside

[outside.md](outside.md) lists every id this suite does not carry: the two claims that cannot pass, the four CTAM ids, and every `MUST-*` from `daniel/ny_sdd/docs/REQUIREMENTS.md`. No carried case names a `MUST-*` id. A row in that file is not a pass.

## Results

| Status | Meaning |
| --- | --- |
| pass | The claim row status is `pass`. |
| fail | The claim row status is not `pass`. Fail is not a pass of the suite. |

The suite verdict is exit 0 when the pass count is 7 and the fail count is 0. Any other exit is not a pass.
