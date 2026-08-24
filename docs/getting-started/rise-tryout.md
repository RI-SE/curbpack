# RISE tryout — first scan

**One RI-SE entry link for the 3 → 10 → 20 → 100 first-run rollout.** Purpose: test installation and one local `scan` only.

Installation is provided from the canonical Curbpack release repository. Full install SoR: [install.md](install.md). Recovery: [troubleshooting.md](troubleshooting.md). Do not copy alternate pins from this page.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## Steps

1. Install (canonical release repository):

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.sh | sh
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.ps1 | iex
```

2. Choose a **git repository you are permitted to inspect**, then `cd` into its root (confirm the path).
3. Run `curbpack scan`.
4. **Stop after scan.** Do not run `init`, `check`, `share`, `attest`, pathway commands, or `./scripts/pilot-receipt.sh` for this tryout.

Optional write-free check:

```bash
before="$(git status --porcelain)"
curbpack scan
after="$(git status --porcelain)"
test "$before" = "$after"
```

The native scan is local and read-only. Exit 0 means diagnosis completed, not that all gates passed.

Stuck? [troubleshooting.md](troubleshooting.md). No product repo handy? `curbpack demo`.

## Optional feedback

Feedback is **not required** to complete the tryout.

→ [Open first-run feedback](https://github.com/afelin/curbpack/issues/new?template=first_run_feedback.yml)

Do not include repository contents, internal paths, customer information, personal data, credentials, secrets, or detailed security findings in feedback.

Alternatives: paste a sanitised note in Teams, or finish without sharing.

Optional community: [Curbpack Discussions](https://github.com/afelin/curbpack/discussions) for release notes and future tester calls (no auto-enrol).

## Related

- Cohort scorecard (empty template + aggregates): [first-run-cohort-scorecard.md](first-run-cohort-scorecard.md)
- Stranger log: [stranger-validation-log.md](stranger-validation-log.md)
- Pilot frame (separate track): [rise-pilot-offer.md](rise-pilot-offer.md)
