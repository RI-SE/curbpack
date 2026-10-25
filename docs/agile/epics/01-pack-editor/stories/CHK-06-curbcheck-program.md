# CHK-06 — Ship curbcheck as its own program

**Epic:** EP-01
**Status:** Ready
**Depends on:** CHK-02

## Story

As a maintainer, I want CI to build **curbcheck** as one file, so a person can run the checker on a product repository without the Studio application and without a source tree.

**curbcheck** is the program. It has the same arguments as `python3 -m checks`: `--repo`, `--packs`, `--out`, and `--skip`. It runs the Checks that this build already runs, by calling **curbcheck-exist**, **curbcheck-contents**, and **curbcheck-git**. Those three tools and `checks/available_checks.json` are inside that one file. `git_signed` and `git_signer` stay not implemented. `fresh`, `owned`, and `dep_ban` stay unavailable. Git itself stays the `git` already on the machine.

**Curbpack Studio** stays the application. Its packaged file does not gain `checks/bin`. From a source checkout, `python3 -m checks` still runs the same Checks by starting those three tools as separate programs.

## Acceptance

1. `make package` on macOS ARM64 writes `dist/curbcheck-macos-arm64` and `dist/curbpack-studio-macos-arm64`. On Windows x64 it writes `dist/curbcheck-windows-x64.exe` and `dist/curbpack-studio-windows-x64.exe`. `dist/SHA256SUMS` names every file that package wrote.
2. The built curbcheck, given a repository, a packs directory, and `--out`, writes a run result. A Claim whose only Check is `exist` or `contents` can pass. A Claim whose Check is `git_fresh` or `git_author` can pass when the product repository and `git` allow it. A Claim whose Check is `dep_ban` fails because `curbcheck-dep-ban` is not in the file.
3. The packaged Studio file is still only the application. It does not contain `curbcheck-exist`, `curbcheck-contents`, or `curbcheck-git` as programs beside the application.
4. `python3 -m checks --repo --packs --out` from this repository still runs `exist`, `contents`, `git_fresh`, and `git_author` through the programs in `checks/bin/`.
5. The package job uploads the curbcheck file next to the Studio file. A sentence in the install or CI guide that tells a person to run this program names it `curbcheck`. `docs/concepts/README.md` no longer says those four Checks run in process.
6. The package directory stays `checks/`. curbcheck does not import `app`, `requirements.ui`, `claims.ui`, review, or scaffold.

## Out of scope

- Implementing `dep_ban`, `fresh`, `owned`, `git_signed`, or `git_signer`.
- Putting the check programs inside the Studio file.
- Renaming the package `checks/`, the module start `python3 -m checks`, the page `/check`, or the JSON field `check`.
- `daniel/ny_sdd/`, the reference-product fixture, and the verification-run story.
- Switching `make test` from the source tree onto the built file.
