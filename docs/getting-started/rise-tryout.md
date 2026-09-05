# RISE tryout — first scan

**One RI-SE entry link for the 3 → 10 → 20 → 100 first-run rollout.** Purpose: test installation and one local `scan` only.

**Pins (do not confuse):** install scripts download the CLI binary from RI-SE releases (currently **v0.5.5**); the GitHub Action pin stays **`@v0.5.2`** — unrelated and frozen until human tabletop.

Installation is provided from the canonical Curbpack release repository. Full install SoR: [install.md](install.md). Recovery: [troubleshooting.md](troubleshooting.md). Do not copy alternate pins from this page.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## Steps

1. Install (canonical release repository — **RI-SE/curbpack only**; other forks may 404):

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
```

If `curbpack: command not found`, open a **new** terminal, or run:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.ps1 | iex
```

Open a **new** PowerShell window if `curbpack` is not found.

2. Choose a **git repository you are permitted to inspect**, then `cd` into its root (confirm the path).
3. Run `curbpack scan`. Cold `scan` defaults to `cra-baseline`; `init` defaults to `house-policy` — this tryout still **stops after scan**.
4. **Stop after scan.** Do not run `init`, `check`, `share`, `attest`, pathway commands, or `./scripts/pilot-receipt.sh` for this tryout. Look for `Exit 0` + `Scan complete — repository unchanged.` (always). If the CLI prints `Next:` or `Next (optional): …`, that is the full golden path later — **ignore it for this tryout**.

Optional write-free check:

```bash
before="$(git status --porcelain)"
curbpack scan
after="$(git status --porcelain)"
test "$before" = "$after"
```

The native scan is local and read-only. Exit 0 means diagnosis completed, not that all gates passed. `Scan complete — repository unchanged.` closes the tryout — the repository was not modified.

Stuck? [troubleshooting.md](troubleshooting.md). No product repo handy? `curbpack demo`.

## Optional feedback

Feedback is **not required** to complete the tryout.

→ [Open first-run feedback](https://github.com/RI-SE/curbpack/issues/new?template=first_run_feedback.yml)

Do not include repository contents, internal paths, customer information, personal data, credentials, secrets, or detailed security findings in feedback.

Alternatives: paste a sanitised note in Teams, or finish without sharing. (GitHub Discussions are not enabled on RI-SE/curbpack — do not use that path.)

## Related

- A2/A3 human runbook (before invites): [a2-a3-human-runbook.md](a2-a3-human-runbook.md)
- Cohort scorecard (aggregates + friction; may show n=1 prep): [first-run-cohort-scorecard.md](first-run-cohort-scorecard.md)
- Stranger log: [stranger-validation-log.md](stranger-validation-log.md)
- Pilot frame (separate track): [rise-pilot-offer.md](rise-pilot-offer.md)
