# Warm-start regulatory pathway

One shared phase vocabulary across seed → GateFailure statechart → ContextPack → `pathway status` → HPURL verify.

Deterministic closed-world pack suggest → guarded HITL confirms → RKG house draft → check/share → human attest → client-side HPURL verify.

CLI exit codes remain source of truth. Chat and MCP never stamp confirms or attest. Catalog stays frozen to `house-policy`, `cra-baseline`, `medtech-iec62304` (plus imported partner packs). Pin Action examples at **`@v0.4.3`**.

Prepares evidence for human review — not a conformity assessment.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## Phase vocabulary (canonical)

Parent path (emit everywhere):

`Root / Pathway / {AwaitSuggest|AwaitPackConfirm|AwaitActivate|AwaitHealOrProse|AwaitProseConfirm|AwaitCheck|AwaitShare|AwaitShareConfirm|AwaitAttest|AwaitHPURLVerify}`

Orthogonal regions under pack eval (unchanged): `PackEval` / rule regions in GateFailure. Pathway ticks are **parent path**, not fake pack regions.

Human-only events: `confirm-packs`, `confirm-prose`, `confirm-share`, `attest`. Agents may `suggest` / `status` / `check` / `share` / heal / propose only. Illegal confirm order → usage exit 2.

## Layers (L0–L10)

| Layer | Job | Machine | Human |
|-------|-----|---------|-------|
| **L0** | Enum seed | `pathway suggest` flags | Answer ≤6 enum questions |
| **L1** | Closed-world packs | Go lookup → frozen trio (+ partner note) | — |
| **L2** | Tick packs | `pathway confirm-packs` (+ RKG export) | Yes / change / house-only |
| **L2.5** | Research sidecar | `cyberready research` (+ optional `--fetch`) | Read brief; not a gate |
| **L3** | Activate | `init --packs` / `check --heal` | — |
| **L4** | House draft | RKG + research packet `requirements[]`/`sources[]`; `ask --propose` / form-hints; cite-or-refuse | Edit real prose |
| **L5** | Tick prose | `cite-check` green → `pathway confirm-prose` | “I own this wording” |
| **L6** | Check | `check` (+ hooks); GateFailure path = pathway phase | Fix on red |
| **L7** | Share | `share` (ContextPack includes pathway next) | — |
| **L8** | Tick share | `pathway confirm-share` | Review buyer-Qs / one-pager |
| **L9** | Sign | — | `attest` (OCC / `--allow-dirty`) |
| **L10** | Verify | status → `open proof/index.html` | Paste `hpurl-pointer.json` `state_hash` |

## Composed loop

```bash
cyberready pathway status          # human next ask (default); --technical for phase path
cyberready pathway suggest --product=…   # closed-world
# human: confirm-packs → research (optional) → init/heal → edit prose → cite-check → confirm-prose
cyberready research                # allowlisted packet + brief; never gates check
cyberready check                   # GateFailure statechart = pathway phase + pack regions
cyberready share                   # ContextPack includes pathway next + research paths
# human: confirm-share → attest
cyberready pathway status          # next: verify HPURL client-side
```

Agents: read ContextPack + `pathway status`; never invent packs/findings; stop at human gates. Prefer ContextPack over spelunking `pathway-seed.json`. Dual public entry: **Write→Check** (optional warm-start) vs **Bring-docs→Check** (files on pack paths — no portal PDF ingest).

## Closed-world suggest map

| Inputs | `proposed_packs` |
|--------|------------------|
| default / hygiene / house-first | `["house-policy"]` |
| shipping + eu-docs | `["house-policy","cra-baseline"]` |
| medtech=yes | `["medtech-iec62304"]` (extends CRA) |
| sector=other | `["house-policy"]` + `next_hint: write-your-own-pack` |

`--ce-context` is **context only** — never changes packs to CE-positive. Never invent pack ids. Confirm intersects with `packs list` ∪ imported.

Multi-industry (Depth B): `sector=other` → house-policy + [write-your-own-pack](../write-your-own-pack.md) / overlays / `packs import`. No new embedded packs; freeze closed.

```bash
cyberready pathway suggest \
  --product=hygiene \
  --eu-docs=no \
  --medtech=no \
  --sector=none \
  --house-first=yes
```

## Anti-hallucination + passive chat

1. **Pack ids:** only from `pathway suggest` / `packs list` — never invent.
2. **Findings:** only from check JSON / ContextPack / SARIF `ruleId` — never invent gate results.
3. **Law:** no regulation-text KB; L4 navigates **RKG** + **research packet** allowlisted URLs (optional `--fetch` excerpts) — never invented regulation text; cite-or-refuse.
4. **Prose:** propose diffs; human applies; heal = stubs only; Claims section lines need cite markers.
5. **Ticks / attest:** human CLI only; not MCP; not “user said OK in chat” without `confirm-*`. Cite-check refuse blocks `confirm-prose` when packet present.
6. **Claims:** claim-safety + fixed fence on seed + exports.
7. **Enums:** suggest flags are closed sets; reject free strings.
8. **Passive chat (Play INV-04):** MCP/chat propose only; phase from ContextPack / `pathway status` — never forge seed or greenlight.

Residual risk (accepted): human-accepted but wrong SECURITY.md — mitigated by review ticks + attest + buyer-questions, not model cleverness.

## HITL checklist

- [ ] `pathway suggest` (enums) → review `proposed_packs`
- [ ] Human: `pathway confirm-packs` (exports RKG)
- [ ] `cyberready research` (optional `--fetch`) — human brief; never gates check
- [ ] `init --packs …` + `check --heal` + edit real prose via RKG / research requirements + cite markers
- [ ] `cyberready research --cite-check <draft.md>` green
- [ ] Human: `pathway confirm-prose`
- [ ] `check` green (or shareable red with ContextPack)
- [ ] `share` → human: `pathway confirm-share`
- [ ] Human: `attest` (agents **stop** here)
- [ ] Human: open `proof/index.html` + paste `hpurl-pointer.json` `state_hash`

`pathway status` prints a **plain-English next ask** by default (`--technical` for phase path + next). Use it as the only status UI.

## Claim fence

Fixed string on every seed write:

> Prepares evidence for human review — not a conformity assessment.

## Seed schema

**Path:** `.github/cyberready/cache/pathway-seed.json`  
**Writer:** only `cyberready pathway`  
**Not** a check pass/fail input.

```json
{
  "schema_version": 1,
  "answers": {
    "product": "hygiene",
    "eu_docs": "no",
    "medtech": "no",
    "sector": "none",
    "house_first": "yes",
    "ce_context": "none"
  },
  "proposed_packs": ["house-policy"],
  "human_ticks": {
    "packs_confirmed": false,
    "prose_owned": false,
    "share_reviewed": false
  },
  "claim": "Prepares evidence for human review — not a conformity assessment."
}
```

## Smoke path (to HPURL verify stop)

```bash
cyberready pathway status
cyberready pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes
# human:
cyberready pathway confirm-packs
cyberready init --packs house-policy   # if not already configured
cyberready research                    # optional allowlisted brief
cyberready check --heal
# edit prose with cite markers; then:
cyberready research --cite-check SECURITY.md   # example path
# human:
cyberready pathway confirm-prose
cyberready check
cyberready share
# human:
cyberready pathway confirm-share
# STOP — human only:
# cyberready attest
# cyberready pathway status   # → verify HPURL (human) / open proof/index.html
```

Agents print the next `pathway status` line and wait. MCP has **no** confirm/attest tools. HPURL stays off home/builders — pathway / proof / for-reviewers only.

## Related

- [Assistant loop](../assistant-loop.md) · [Cold start](house-policy-cold-start.md) · [60-second paths](60-second-paths.md) · [Buyer evidence](buyer-evidence.md)
- [Write your own pack](../write-your-own-pack.md) · [Voice and terms](../voice-and-terms.md) · [Stable contracts](../stable-contracts.md)
