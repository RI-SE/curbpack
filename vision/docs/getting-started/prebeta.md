# Friendly pre-beta: start here

Use this guide to test the merged hardening work. The public installer still
supplies **v0.5.5**, and the pinned Action is a separate version. Neither is the
pre-beta build described here. Do not use the release install commands for this
exercise.

## 1. Run the prepared example

Requirements: Git, Go 1.23 or later, and Bash on macOS/Linux. The first build may
download Go dependencies. From this repository:

```bash
./scripts/test-prebeta.sh
```

For a new checkout after this guide is merged:

```bash
git clone https://github.com/RI-SE/curbpack.git
cd curbpack
./scripts/test-prebeta.sh
```

The script builds **committed HEAD** with a version such as
`0.5.5-prebeta+g40d80909db6b`. It refuses history predating PR #58 and excludes
uncommitted source edits. It invokes that exact binary directly, so an older
`curbpack` elsewhere on PATH cannot affect this test.

Each run retains its own binary and a new folder under `~/curbpack-prebeta-runs/`.
A later rebuild cannot change the binary used by an existing run. It prepares a
passing sandbox example, scans it, checks its gates, creates a complete bundle,
and reviews a copy outside Git. It does not initialize your current repository,
install hooks, sign evidence, or send feedback. Existing run folders are retained.
An operational error stops the exercise and prints the log location.

## 2. Open the results and trigger one gate

The script prints the full folder path. Open its **START-HERE.txt** first.

| File | What to test |
|---|---|
| `build.txt` | The source SHA and labelled pre-beta version are the intended build. |
| `03-scan.txt` | You can distinguish read-only diagnosis from gate pass/fail. |
| `04-check.json` | The prepared demo passes; it does not assess your product. |
| `recipient/review-pack/evidence-bundle.html` | You can open and understand the handoff in your normal browser. |
| `06-review.json` | `pack_audit.integrity` and declared manifest coverage verify. Authenticity remains unverified, applicability not assessed, and the subject commit claimed. |

On macOS, copy the `open ".../evidence-bundle.html"` command printed by the script,
or open that file in Finder. Record any broken layout or unclear wording; the
script does not count a human visual check as passed.

### Remove one file, observe one gate, restore it

Use only the generated `example/` directory, not your product checkout. Run a
baseline check, move **one** file to a temporary backup, check again, then restore
it and recheck. Do not run `share` or `--heal` while the file is absent: those
commands can recreate draft inputs.

| Remove from the prepared example | Expected new failed gate |
|---|---|
| `SECURITY.md` | `HOUSE-SECURITY-MD` |
| `.well-known/security.txt` | `HOUSE-SECURITY-TXT` |

For example, from the run folder (substitute its printed path):

```bash
cd /path/to/run/example
../curbpack-prebeta check --packs house-policy
mv SECURITY.md ../SECURITY.md.saved
../curbpack-prebeta check --packs house-policy   # expected exit 1
mv ../SECURITY.md.saved SECURITY.md
../curbpack-prebeta check --packs house-policy   # expected exit 0
```

Restore the file even if the observed result differs. The house-policy pack
checks these document rules; deleting an arbitrary application test does not
create a test-coverage gate.

## 3. Try a permitted repository

Use a disposable clone. Keep the exact binary path printed by the script:

```bash
/path/printed/by/the/script/curbpack-prebeta version
cd /path/to/disposable/product-clone
/path/printed/by/the/script/curbpack-prebeta scan --packs house-policy
/path/printed/by/the/script/curbpack-prebeta check --packs house-policy
/path/printed/by/the/script/curbpack-prebeta share --packs house-policy --bundle
```

`scan` writes nothing. `check` writes cache/evidence files. `share` can create
missing document drafts, lists every created input, and writes the review pack.
It does not create files merely because a secret-detection rule scans those paths. Use `share --bundle` for the
complete trial; partial-export options are outside this exercise.

| Result | Meaning |
|---|---|
| `scan` exit 0 | Diagnosis completed; findings may remain. |
| `check` / `share` exit 0 | Selected gates passed for this evaluation. |
| `check` / `share` exit 1 | Findings or an operational error; read the diagnostic. A remediation pack may still be produced. |
| `review` exit 0 | No contradicted triage findings; read the separate trust dimensions. |
| Exit 2 | Usage/environment problem; read the diagnostic. |

For a repeatable evaluation date, add `--as-of YYYY-MM-DD` to `check` and `share`.
Otherwise they select the current UTC date. Do not reuse the historical audit's
September 2026 date by accident.

### Review the handoff for your role

Open **review-pack/evidence-bundle.html** and start at **What to do next**. Keep
the whole folder together: HTML alone is a reading copy, not the verifiable pack.
The overview shows all review tasks, their mechanical results, and which source
evidence is not included. Request needed documents through an approved channel;
do not send credentials, private keys or an entire repository.

| Your task | Next action | Decision to record |
|---|---|---|
| Internal producer | Address findings, run `check`, then `review --repo .` for document references. | Is the evidence ready for someone else to review? |
| Buyer or insurer | Confirm product, version and intended use; request missing evidence. | Is more evidence needed for the purchase or coverage decision? |
| Reviewer or auditor | Run `review review-pack`, inspect evidence and record questions. | What is supported, unresolved or outside this review? |
| Agent or automation | Use `check --json` and `review review-pack --json`; retain exit codes and separate trust results. | Escalate unresolved findings; do not approve or sign. |

Use plain command output for the walkthrough. JSON is optional machine output;
legacy fields such as `readiness_score` are not the human readiness verdict.
A gate pass does not run your application tests or establish product safety.
Signing is separate; an unsigned friendly test can finish with a useful observation.

## 4. Report one useful observation

Use [first-run feedback](https://github.com/RI-SE/curbpack/issues/new?template=first_run_feedback.yml)
or [tester report](https://github.com/RI-SE/curbpack/issues/new?template=tester_report.yml).
Start with the generated `feedback.txt`: it contains the tool build SHA/version,
OS/architecture and completed command names, without home paths or Git identity.
Add the expected behavior and where you got stuck. Review your own added text
before sharing. Do not upload the run folder, raw logs or a product repository.

Stop the first exercise here. Signing, attestations, Action setup, regulatory
claims and the full governance pathway are later work. Gate results prepare
evidence for human review; they are not conformity assessment.

## Privacy boundaries

The runner does not submit feedback, upload artifacts or publish anything. New
run folders and log files are private to the creating account by default. The
prepared example ignores inherited `GIT_*` settings and personal/global Git
configuration, uses an empty Git template, and keeps the demo's generic author
identity. These controls do not alter the tester's actual Git configuration.

Private logs intentionally retain local paths and diagnostics to make failures
debuggable. Product checks can contain product-derived content. Do not treat
those logs as automatically safe to share. `feedback.txt` and `START-HERE.txt`
avoid absolute home/source paths; they retain useful, non-secret tool metadata.
Exports use declared package metadata or a neutral subject label, not the local
checkout folder name. Review declared metadata before sharing.
Public source attribution, module names, evaluation hashes and dates are not
removed or relabelled as anonymous evidence.

The first Go build may contact the configured dependency/toolchain services.
This is not a claim of zero network traffic from installed development tools,
or a guarantee that arbitrary product content can never contain a secret.
The privacy regression can be run with Python 3:
`python3 scripts/test_prebeta_privacy.py`. It supplies a synthetic personal Git
identity and hook, then checks that neither reaches the example or share text.

## Update or rebuild

After maintainer changes merge, use `git pull --ff-only` on a clean `main`
checkout and rerun `./scripts/test-prebeta.sh`. It records the new SHA in a new
run folder. To build only, use `./scripts/build-prebeta.sh`; the binary is
`bin/curbpack-prebeta`. This does not replace a system installation or promote a
release. Keep using the labelled pre-beta path until a new release is announced.

See [the acceptance review](../production-hardening-audit.md#friendly-user-pre-beta-review)
for tested boundaries and deferred qualification work.
