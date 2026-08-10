# CyberReady — GitHub Copilot

Local pack gates. Humans review. Not conformity assessment.

- After edits in an initialized repo, run `cyberready check` (exit code = pass/fail).
- On red: `cyberready check --heal`, then `cyberready ask .github/cyberready/cache/latest_failure.json --propose`. Propose-only; never attest; never claim CE/certification.
- On green: optional `cyberready export --context-pack` (one washed artifact for PR/review).
- Prefer ContextPack / GateFailure IR over inventing findings. Pin Action `@v0.4.3`.
- Full contract: docs/assistant-loop.md
