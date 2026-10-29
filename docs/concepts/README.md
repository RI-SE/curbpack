# Studio concepts and principles

Studio checks a product repository against Claims that a person configured for selected Requirements, and prepares that result for a separate human decision.

Software projects change over time. Code, dependencies, documentation and policies do not always change together. Evidence that was once present can disappear, become incomplete, or stop matching the arguments a Claim is watching.

## How the work is split

```text
selected Packs, named by the product's curbpack.json
      +
Claims in the product repository
      +
the product working tree
      ↓
Run curbcheck
      ↓
one run result: pass / fail / skipped
      ↓
compiled review report
      ↓
human decision and review-sign
```

The selected Requirements say **what the provision requires**, including `discovery_hints`.

The product repository provides **the evidence**.

A Claim says **which evidence a person associates with one Requirement**, and `checks[]` say **which technical questions to ask**.

The run result records **what those questions observed**.

Review records **what a person decided** about that run. Compile does not run Checks. Signing the report does not sign the Requirement or the Claim.

The activities can be repeated independently. A product change is a new Check run. A new sealed Requirement can be followed by a new Discovery. Neither of those restarts Extract. The cover links each area and does not order them.

## Main concepts

### [Packs](packs.md)

A Pack is a versioned collection of Requirements. `pack.json` is metadata only. Requirement files sit in the same version directory, `<packs_dir>/<pack-id>/<pack-version>/`.

A product selects Pack ids in `curbpack.json`. Check loads `<packs_dir>/<pack-id>/<pack-version>/pack.json` and the Requirement files beside it. A local working copy is a separate payload. Check loads the `pack.json` already present for the selected id.

### Requirements

A Requirement holds the legal or policy source, `references[]` (`nr`, `locator`, `law_text`), optional guidance, and `discovery_hints`. Hints help Discovery find candidate files. They are not evidence and they are not Checks.

### Claims and Checks

A Claim references exactly one Requirement. One Requirement may have several Claims. One piece of evidence with several questions is one Claim whose `checks[]` holds each question. Put `exist` and `contents` on the same Claim when they are about the same evidence.

`exist` asks whether the paths are files. `contents` asks whether the bytes match the probes. A missing file fails `contents` as well, and the detail says the file is absent. It does not also report a missing header.

This build runs `exist` through `curbcheck-exist`, `contents` through `curbcheck-contents`, `git_fresh` and `git_author` through `curbcheck-git`, and `dep_ban` through `curbcheck-node`. `git_signed` and `git_signer` are registered on that same Git program and fail with the detail that the check is not implemented. `fresh` and `owned` fail because their commands are not installed. They do not pass. `file_present` and `annex_file` are not in that registry.

### [Evidence](evidence.md)

Evidence is product material the Claim points at: a document, a manifest, or another repository path. Discovery's candidate list is not evidence that has been accepted. A Useful or Poor mark is workspace feedback, not a Claim field.

### Results and review material

The run result is one JSON object for the run that happened. When it is written to disk, the file is `<results_dir>/run-result_<UTC>.json`, one new file per run. The created-file default for `results_dir` is `.curbpack`.

Compile copies that run result into one review report at `<reports_dir>/review-report_<UTC>.json`. The created-file default for `reports_dir` is `curbpack/reports`. The report carries `run_result`, `requirements`, `claims`, and `appendix`. When a person has recorded them, it also carries `decision` and `signed`.

## Principles

### Studio prepares observations; people make decisions

A passing Check means the evidence satisfied the arguments on that Check.

It does not by itself establish legal compliance, safety, certification, approval, or suitability for release.

### Human authority stays human

Extract can propose unsigned Requirements. Discovery can propose candidate paths. An unsigned Claim can be evaluated. None of those is an approval.

Signing a Requirement, signing a Claim, and signing a review report are three different seals. A typed name is not an inference of organisational authority. Local Ed25519 keys are created when someone signs. They are not X.509 certificates. Signing does not commit, tag or push.

### Studio must not validate what it created

Scaffold can write a stub file and refuses to overwrite an existing one. A stub is product content a person still has to replace. A Check that passes on a stub has observed the stub. It has not observed a real assessment.

Material created by Extract or Discovery does not become evidence of human work because the tool produced it.

### Results should be reproducible

A run result belongs to the Pack ids, each Pack's `version`, the pack-directory digest, the Claim digests, the Check arguments, and the Git `commit` and `worktree` when Git has a HEAD.

The same inputs should produce the same observation. A dirty worktree can still pass. The Check page then states that the result is not verification of that commit's content. A later run writes a new run-result file and does not rewrite an earlier review report. A later compile writes a new `review-report_<UTC>.json` and leaves the earlier report in place. When both a saved report and a run result are loaded, the review page says `same run: yes` or `same run: no. This saved report is an older run.`

### Evaluation stays local

The pilot is a local single-user application on `127.0.0.1:8770`. Discovery and model calls stay in the environment that holds the product. Studio does not require a remote certification service, and it does not receive the product in order to assess it for someone else.

## Read more

* [Packs](packs.md)
* [Evidence](evidence.md)
* [Packs v2](../reference/packs2.md) — Pack, Requirement, Claim, Check, signing, and run-result fields
* [Workspace](../reference/workspace.md) — `curbpack.json` keys, created-file values, and on-disk paths
* [Architecture: data and responsibility](../arch/ARCHITECTURE.md)
