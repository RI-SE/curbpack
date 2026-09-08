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

## 2. Open the results

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

## 3. Try a permitted repository

Use a disposable clone. Keep the exact binary path printed by the script:

```bash
/path/printed/by/the/script/curbpack-prebeta version
cd /path/to/disposable/product-clone
/path/printed/by/the/script/curbpack-prebeta scan --packs house-policy
/path/printed/by/the/script/curbpack-prebeta check --packs house-policy --json
/path/printed/by/the/script/curbpack-prebeta share --packs house-policy --bundle
```

`scan` writes nothing. `check` writes cache/evidence files. `share` can create
missing draft inputs and writes the review pack. Use `share --bundle` for the
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

## 4. Report one useful observation

Use [first-run feedback](https://github.com/RI-SE/curbpack/issues/new?template=first_run_feedback.yml)
or [tester report](https://github.com/RI-SE/curbpack/issues/new?template=tester_report.yml).
Include the build SHA/version, OS/architecture, command, exit code, expected
behavior, and where you got stuck. Review logs for private information before
sharing; do not upload an entire product repository.

Stop the first exercise here. Signing, attestations, Action setup, regulatory
claims and the full governance pathway are later work. Gate results prepare
evidence for human review; they are not conformity assessment.

## Update or rebuild

After maintainer changes merge, use `git pull --ff-only` on a clean `main`
checkout and rerun `./scripts/test-prebeta.sh`. It records the new SHA in a new
run folder. To build only, use `./scripts/build-prebeta.sh`; the binary is
`bin/curbpack-prebeta`. This does not replace a system installation or promote a
release. Keep using the labelled pre-beta path until a new release is announced.

See [the acceptance review](../production-hardening-audit.md#friendly-user-pre-beta-review)
for tested boundaries and deferred qualification work.
