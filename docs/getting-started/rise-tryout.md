# RISE tryout — first scan

**One RI-SE entry link for the 3 → 10 → 20 → 100 first-run rollout.** Purpose: test installation and one local `scan` only.

Commands and the verified install pin live only in [install.md](install.md). Recovery: [troubleshooting.md](troubleshooting.md). Do not copy alternate pins from this page.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## Steps

1. Follow [install.md](install.md) **Ladder 0** (canonical pinned release).
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

Stuck? [troubleshooting.md](troubleshooting.md). No product repo handy? `curbpack demo` (same install SoR).

## Optional feedback

Feedback is **not required** to complete the tryout.

Use the **canonical** issue form (RI-SE mirror Issues are not the feedback destination):

→ [Open first-run feedback on afelin/curbpack](https://github.com/afelin/curbpack/issues/new?template=first_run_feedback.yml)

Do not include repository contents, internal paths, customer information, personal data, credentials, secrets, or detailed security findings in feedback.

Alternatives: paste a sanitised note in Teams, or finish without sharing.

Optional community: [Curbpack Discussions](https://github.com/afelin/curbpack/discussions) for release notes and future tester calls (no auto-enrol).

## Related

- Cohort scorecard (empty template + aggregates): [first-run-cohort-scorecard.md](first-run-cohort-scorecard.md)
- Stranger log: [stranger-validation-log.md](stranger-validation-log.md)
- Pilot frame (separate track): [rise-pilot-offer.md](rise-pilot-offer.md)
