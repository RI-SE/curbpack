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

A Pack is a versioned collection of Requirements. `pack.json` is metadata. The Requirement files sit beside it.

A publisher extracts, reviews, signs and can publish an immutable release. A product selects Pack ids in `curbpack.json`. Check loads those Pack directories. The Pack open in Pack Editor is not automatically the Pack Check evaluates.

### Requirements

A Requirement holds the legal or policy source, `references[]` (`nr`, `locator`, `law_text`), optional guidance, and `discovery_hints`. Hints help Discovery find candidate files. They are not evidence and they are not Checks.

### Claims and Checks

A Claim references exactly one Requirement. One Requirement may have several Claims. One piece of evidence with several questions is one Claim whose `checks[]` holds each question. Put `exist` and `contents` on the same Claim when they are about the same evidence.

`exist` asks whether the paths are files. `contents` asks whether the bytes match the probes. A missing file fails `contents` as well, and the detail says the file is absent. It does not also report a missing header.

This build runs `exist` through `curbcheck-exist`, `contents` through `curbcheck-contents`, and `git_fresh` and `git_author` through `curbcheck-git`. `git_signed` and `git_signer` are registered on that same program and fail with the detail that the check is not implemented. `dep_ban`, `fresh`, and `owned` fail because their commands are not installed. They do not pass. `file_present` and `annex_file` are not in that registry.

### [Evidence](evidence.md)

Evidence is product material the Claim points at: a document, a manifest, or another repository path. Discovery's candidate list is not evidence that has been accepted. A Useful or Poor mark is workspace feedback, not a Claim field.

### Results and review material

The run result is one JSON object for the run that happened. The usual path is `<product-repo>/.curbpack/run-result.json`.

Compile copies that result, the Requirement files and the Claim files the rows name, into one report. The server writes `<product-repo>/docs/reports/review-report.json`.

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

The same inputs should produce the same observation. A dirty worktree can still pass. The Check page then states that the result is not verification of that commit's content. A later run does not rewrite an earlier signed report by itself. When both the saved report and a run result are loaded, the review page says `same run: yes` or `same run: no. This saved report is an older run.` Compiling over an existing file requires the checkbox that the previous decision is not copied.

### Evaluation stays local

The pilot is a local single-user application on `127.0.0.1:8770`. Discovery and model calls stay in the environment that holds the product. Studio does not require a remote certification service, and it does not receive the product in order to assess it for someone else.

## Read more

* [Packs](packs.md)
* [Evidence](evidence.md)
* [Packs v2 product flow](../reference/packs2.md)
* [Architecture: data and responsibility](../arch/ARCHITECTURE.md)
