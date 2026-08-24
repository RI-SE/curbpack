# Curbpack — agent contract

**Local pack gates. Humans review. Not conformity assessment.**

Design intent: [docs/software-design-document.md](docs/software-design-document.md). Canonical loop: [docs/assistant-loop.md](docs/assistant-loop.md). Warm-start pathway: [docs/getting-started/pathway.md](docs/getting-started/pathway.md). Cursor skill source: `internal/skilldata/SKILL.md` (installed by `curbpack init`).

## Loop (opens read-only)

An agent's first action never mutates the repository.

```bash
curbpack scan              # read-only diagnosis — no init, no hooks, no score
# optional: curbpack fix --<gap>   # one templated file; diff shown; human confirm
curbpack init              # when ready — house-policy default
curbpack check             # exit code authoritative
# red: curbpack check --heal && curbpack ask .github/curbpack/cache/latest_failure.json --propose
# green: curbpack ask-my-suppliers  # durable buyer checklist + pack draft
# optional pathway sidecar (never gates check):
curbpack pathway status    # human next ask by default (--technical for phase path)
# optional research sidecar (never gates check): curbpack research [--fetch] [--gate-id=…]
```

Pathway/research/dual-draft flows remain valid for warm-start users — see [assistant-loop.md](docs/assistant-loop.md). When both apply, **scan before init/check**.

## Human-only acts

Enumerated. Gate: explicit human confirmation flag or environment variable. A TTY alone is not sufficient.

```
trust-import · review-sign · Last tabletop: · confirm-* · attest · pin-bump
```

- **trust-import** — `curbpack packs trust import` (not built yet; contract-only until Wave B).
- **review-sign** — pack reviewer attestation signatures.
- **Last tabletop:** — badge reads this field only; agents must not fill it.
- **confirm-*** — `pathway confirm-packs|confirm-prose|confirm-share` with `--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1`.
- **attest** — human capsule after review; never auto-attest.
- **pin-bump** — Action/examples pin stays **`@v0.5.2`** until human approves bump.

## Rules (short)

1. After doc/dep edits → run `curbpack check` (exit code authoritative).
2. On red → `curbpack check --heal` then `curbpack ask … --propose` — never invent certification; never auto-attest.
3. On green → optional `curbpack export --context-pack` / `--buyer-questions` for humans.
4. Prefer ContextPack + dual-rep IR over guessing cache files.
5. Pin Action / examples at **`@v0.5.2`**. Never claim CE / notified-body approval.
6. **Pathway:** call `curbpack pathway status|suggest|note` only — never forge `pathway-seed.json` or invent pack ids. Stop for human `confirm-*` and `attest`. Prefer ContextPack pathway next + RKG after confirm-packs; post-attest next is local proof verify (human). MCP never confirms/attests. Seed is not a gate input.
7. **Research (optional sidecar):** `curbpack research` builds allowlisted citation packet + human brief — **never** inputs to check pass/fail. After confirm-packs / before prose: draft from packet; every factual assertion needs a repo artifact (path, config, test name, commit, metric, claim id) or an allowlisted cite (`[^src-N]` / `<!-- cite:src-N -->` / allowlisted URL). Heal stubs are not grounding. `confirm-prose` is AND: every displayed prose path must be independent (mixed stub+real still refuses). Run `curbpack research --cite-check <draft.md>` before asking a human for `confirm-prose` (confirm-prose also refuse-ungrounded). On red, optional `research --gate-id=<id>`. Link-only if no `--fetch`.
8. **Dual-draft HITL:** always propose Option A and Option B, state **Recommended: A|B** with ≤3 reasons (from seed notes / last_pick / requirements), stop for human pick; then cite-check; record via `curbpack pathway note --set last_draft_pick=A|B|edited`.
9. **Claim discipline:** an artifact must never assert something the tool caused — see [docs/claim-discipline.md](docs/claim-discipline.md).

Do **not** treat chat tutors as a gate greenlight. Re-check locally.

Optional MCP wrapper (CLI remains SoR): [examples/mcp/](examples/mcp/).
