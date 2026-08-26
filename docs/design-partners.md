# Design partners

Product brief for five external repos that keep Action `@v0.5.2` or `init`+hooks green. Outreach is human-operated; this file is the ask + scoreboard. Public [`ADOPTERS.md`](../ADOPTERS.md) rows only on partner opt-in — never invent entries.

**Local pack gates. Humans review. Not conformity assessment.**

| Field | Content |
|-------|---------|
| Ask | Add Action `@v0.5.2` **or** `curbpack init` + hooks; keep for 14 days |
| Success | First green &lt;10 min; second green ≤7 days; “judge clicked without pitch?” Y/N |
| Forbidden asks | Certification claims; uploading IP to a cloud policy brain |
| Weekly ritual | 15-min note: path taken (A/B/C), stall step, keep/kill |

## Scoreboard (template)

Object owner fills rows during outreach. Empty slots are fine — **no fake logos**. Update [`ADOPTERS.md`](../ADOPTERS.md) only when a partner opts in.

| Partner | Path (A/B/C) | First green | Second green ≤7d | Judge clicked Y/N | Keep/Kill | Notes |
|---------|--------------|-------------|------------------|-------------------|-----------|-------|
| _(slot 1 — OSS)_ | | | | | | |
| _(slot 2 — OSS)_ | | | | | | |
| _(slot 3 — SME)_ | | | | | | |
| _(slot 4 — SME)_ | | | | | | |
| _(slot 5 — optional later Coreward-as-consumer)_ | | | | | | Curbpack contracts only this round; live Coreward dogfood is a later plan |

Paths: **A** = safe try (`doctor`/`demo`) · **B** = product repo (`init`+hooks) · **C** = CI Action `@v0.5.2`.

## Target mix

| Slot | Profile |
|------|---------|
| 2 | OSS maintainers (Curbpack adopters) |
| 2 | SME / supplier-ish product repos |
| 1 | Optional later: Coreward-as-consumer (not required this round) |

## Partner issue shape

Prefer [First move stuck](../.github/ISSUE_TEMPLATE/first_move_stuck.yml) when activation fails. Prefer Discussions “I went green” when it works.

Do **not** send partners to `docs/gtm-oss/` (non-product).

## What we count

- First-move completion (≥4/5)
- Second green within 7 days (≥3/5)
- Pin / “is this certified?” / main≠tag support → ~0

Stars are not the scoreboard.

**Look here (not a CVE product):** after green, `curbpack export --lay-of-land` surfaces an informational watchlist∩SBOM join inside the shareable map. Point partners at that file when they ask “what should I look at?” — do not pitch vulnerability management.

## Object-owner cadence checklist

Ship the rhythm in-repo; the calendar is human-operated.

| Cadence | Action |
|---------|--------|
| Every merge | `redteam-pilot` required green |
| Weekly | Run `./scripts/time-to-green.sh`; skim partner notes; **zero** new trust-surface features |
| Biweekly | Kill/keep on friction from first-move issues |
| Day 30 of freeze | Explicit freeze review: renew, narrow, or cut next bugfix-only tag — `v0.5.0` is the current instrument-panel pin; next cut only after freeze review |

### Explicit nos

OPA/LSP/tracers · badge marketplace · `gtm-oss` on site · CE language · second pin · expanding pack catalog before 5 partners have week-2 greens.

**Pack catalog freeze:** only `house-policy`, `cra-baseline`, `medtech-iec62304`. `scripts/redteam-pilot.sh` fails on any new pack id under `packs/` or the embed twin. Unlock requires freeze review + an explicit PR that updates the allowlist — not an env escape hatch in CI.

Also mirrored in [launch readiness](internal/launch-readiness.md), [Intent vs Scope](intent-vs-scope.md), and [Promotion firewall](promotion-firewall.md).
