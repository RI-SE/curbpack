# Curbpack — GitHub Copilot

Local pack gates. Humans review. Not conformity assessment.

- After edits in an initialized repo, run `curbpack check` (exit code = pass/fail).
- On red: `curbpack check --heal`, then `curbpack ask .github/curbpack/cache/latest_failure.json --propose`. Propose-only; never attest; never claim CE/certification.
- On green: optional `curbpack export --context-pack` (one washed artifact for PR/review).
- Prefer ContextPack / GateFailure IR over inventing findings. Pin Action `@v0.5.2`.
- Repository policy: product PRs target RI-SE/curbpack only — see `docs/internal/fork-policy.md`.
- Full contract: docs/assistant-loop.md
