# Post kill-test gates (compress-after)

> Maintainer note. Structural evidence for human review — not conformity assessment.

## Rule

**Intake**, **packs lint**, and **`--batch`** (strategy phases 2–4) stay **gated** until either:

1. **Phase 6 kill-test** completes with an acceptable outcome (see [phase6-kill-test.md](phase6-kill-test.md)), **or**
2. An **explicit human risk accept** is recorded (written maintainer decision — not an agent invent, not a chat greenlight).

Do **not** implement intake, packs-lint expansion, or `--batch` while this gate is closed.

## Why

The reader wedge (`curbpack review` + review-pack triage) must prove distributional value on real packs before we widen intake/batch surface. Shipping those paths early creates operational load without a falsifiable product signal.

## Out of scope here

- Implementing intake / packs lint / `--batch`
- Pin bumps, trust-import, attest, or HPURL work
- Claiming certification or CE / notified-body outcomes from kill-test metrics
