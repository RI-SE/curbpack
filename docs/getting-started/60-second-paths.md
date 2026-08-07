# 60-second paths

CyberReady prepares evidence for **human review**. It does **not** certify conformity.

Cold-start default pack: **`house-policy`** (lowest regulatory anxiety). CRA / medtech are opt-in via `--packs`.

## Human

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
cyberready doctor
cyberready demo                          # safe sandbox — prints one-pager path (no browser)
# cyberready demo --open                 # opt-in: open the one-pager in the OS browser
# Sample without re-demo: site/samples/onepager.html
# or on your repo:
cd my-product && cyberready init --packs house-policy --hooks --skill --ide
cyberready check
```

## Agent

```bash
cyberready init --packs house-policy --skill --ide
# Skill lands at .cursor/skills/cyberready/SKILL.md
cyberready check
cyberready check --form-hints            # propose-only snippets
# optional: cyberready check --form-hints --apply-stub   # write missing stubs only
```

Agent rule: after doc/dep edits, re-run `check`. Never claim certification.

## Decision-maker

1. Open the supplier’s `review-pack/buyer-onepager.html` (from `prepare-release` or the Action artifact), or the committed sample at `site/samples/onepager.html`.
2. Or open the HPURL proof page (`proof/index.html`) with a hash fragment.
3. One screen: thermometer, top gaps, disclaimer — no account required. Not a certificate.

> Prepares evidence for human review — not a conformity assessment.
