# Contributing

Thanks for helping. Curbpack prepares **evidence for human review** — not a conformity assessment.

## Dev loop

```bash
go test ./...
./scripts/claim-safety.sh
./scripts/redteam-pilot.sh   # required merge check name: redteam-pilot
```

Run **claim-safety + redteam-pilot** green before opening a PR that touches docs, CLI strings, packs, or trust-adjacent paths.

Optional activation smoke (maintainer bar defaults to 600s; use `TTG_MAX_SECONDS=60` for a tight local run):

```bash
./scripts/time-to-green.sh
TTG_MAX_SECONDS=60 ./scripts/time-to-green.sh
```

Agent loop (edit → check → instrument → heal/ask; never auto-attest): see the Agentic coding subsection in [`docs/intent-vs-scope.md`](docs/intent-vs-scope.md).

## First-move failed?

Prefer the **First move stuck** issue template: path A/B/C + the step that failed. That shape beats a vague “it didn’t work.”

## Claim safety

Do not introduce certification / CE / notified-body language. Run `scripts/claim-safety.sh` before opening a PR that touches docs or CLI strings. Public co-promotion rules: [`docs/promotion-firewall.md`](docs/promotion-firewall.md) (RISE = funder, not certifier).

## Trust surface

Action binary resolve, `SafeJoin` / pack path jail, attest honesty, claim-safety, and explain-packet airlock are under freeze through the **v0.4.x** line — bugfixes only. See `docs/security-model.md`. Pin stays `@v0.5.2` until the next freeze review.

## Strategy boundary (contributors)

- Do **not** port v3.33 EE / R&D surfaces into OSS PRs — v3.33 is internal north star only ([strategy boundary](docs/strategy-boundary.md)).
- PRs that add OPA/Rego, LSP, syscall tracers, FIDO defaults, or **new pack ids** without freeze unlock will be **rejected**. Pack allowlist is enforced by `scripts/redteam-pilot.sh`.
- Sock ops + GateFailure / explain-packet shapes are frozen in [stable contracts](docs/stable-contracts.md); breaking them requires a major pin bump.

### Packs vs check kinds (governance)

**Packs are infinitely malleable. The nine check kinds are frozen.**

National variations, guidance changes, and new standards are **pack version bumps** authored by domain owners — no Go change, no binary release. The pack format already carries jurisdiction, validity windows, citations, extends/overlays, supersession, and private pack dirs.

A tenth check kind breaks comparison-scheme digests: two participants on different binary versions could no longer produce the same digest on the same bundle. A requirement that cannot be expressed with the nine — `annex_file`, `file_present`, `anti_placeholder`, `npm_dep_ban`, `manifest_dep_ban`, `text_forbid`, `import_reach`, `fresh`, `owned` — is a signal to say *this does not fit the tool*, not to grow the tool. See [docs/method/review-method-1.1.1.md](docs/method/review-method-1.1.1.md).

### Review / reference graph prohibitions

These apply to `review` and related surfaces (including `--repo`):

1. **No model ships here.** Not embedded, not downloaded, not called.
2. **No network call.** `review` records URLs and never fetches them.
3. **No persistent index.** The record is a file the caller redirects; rebuild every run.
4. **No similarity, fuzzy match, threshold, or confidence score on an edge.** An edge exists because the target was found. Outcomes are `confirmed` / `unconfirmed` / `contradicted` only.

### Low-maintenance covenant (rules 7–9)

5–6 live in product design docs; contributors must uphold:

7. **Anything that can rot must be guarded by a test that fails when it rots** — method docs, reserved names, and frozen fixtures need failing guards (see `TestMethodVersionMatchesClassifier`, comparison digest pin).
8. **Delete rather than deprecate** — a reserved name with no implementation gets an expiry date (`edges` expires at v1.2.0 if unused), not a permanent home.
9. **Every shipped capability has a named consumer in the same commit** — an unwired feature is a maintenance cost with no benefit.

## Non-product docs

`docs/gtm-oss/` is quarantined. Do not link it from the product site, README hero, or Action copy.
