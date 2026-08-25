# A2 / A3 — 10-minute human runbook

**Human-only.** Agents cannot close these gates. **No invites** until **A2 ∧ A3** both pass.

Live stranger install SoR: **v0.5.4** via `main` scripts (Action pin stays **`@v0.5.2`**).

Canonical site: https://ri-se.github.io/curbpack/  
Feedback: [first_run_feedback](https://github.com/RI-SE/curbpack/issues/new?template=first_run_feedback.yml) · [tester_report](https://github.com/RI-SE/curbpack/issues/new?template=tester_report.yml)

---

## A2 — OG / social (~5 min)

**Goal:** logged-out phone confirms social cards for the Pages home look claim-safe (no certification theater).

### Copy-paste checklist

1. On a **logged-out** phone (or private browser with no GitHub session):
2. Paste into **Slack** (unfurl): https://ri-se.github.io/curbpack/
3. Paste into **LinkedIn** composer (preview): same URL
4. Optional: [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) if cache looks stale
5. Skim title + description — must **not** imply CE / notified-body / conformity assessment

### Pass / fail

| Result | When |
|--------|------|
| **PASS** | Slack + LinkedIn both unfurl; wording is claim-safe; record date in [launch-readiness.md](../internal/launch-readiness.md) A2 row |
| **FAIL** | Broken/missing card, wrong URL, or certification-sounding copy — stop; fix site meta before invites |

---

## A3 — Tier-3 stranger path (~5–10 min)

**Goal:** fresh human curl → doctor → demo → `scan` on a **permitted** git repo; prove **v0.5.4** honesty strings. Agent smoke ≠ A3.

### Copy-paste checklist

```bash
# 1. Fresh shell — prefer PATH without a workspace/dev curbpack binary
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
# If needed: new terminal, or: export PATH="$HOME/.local/bin:$PATH"

curbpack version          # MUST print 0.5.4 (not 0.5.3)
curbpack doctor
curbpack demo

cd /path/to/permitted/git/repo
before="$(git status --porcelain)"
curbpack scan
after="$(git status --porcelain)"
test "$before" = "$after" && echo porcelain_ok
```

**Assert (all required):**

- [ ] `curbpack version` → **0.5.4**
- [ ] Scan shows **Exit 0**
- [ ] Scan shows **Scan complete** (repository unchanged)
- [ ] `git status --porcelain` empty / unchanged (`porcelain_ok`)
- [ ] Ignore any `Next (optional):` line — tryout stops after scan

Do **not** use `…/v0.5.4/scripts/install.sh` (tag tree baked older manifest default).

### Record

File [first_run_feedback](https://github.com/RI-SE/curbpack/issues/new?template=first_run_feedback.yml) or [tester_report](https://github.com/RI-SE/curbpack/issues/new?template=tester_report.yml).  
Do **not** use Discussion #4 (Discussions OFF).

### Pass / fail

| Result | When |
|--------|------|
| **PASS** | All asserts above; feedback filed; update [launch-readiness.md](../internal/launch-readiness.md) Tier-3 / A3 to human-recorded |
| **FAIL** | Wrong version, non-zero exit, missing Scan complete, dirty porcelain, or no feedback filed — stop; no invites |

---

## Invite gate

```text
invites := A2_PASS ∧ A3_PASS
```

Until both: **do not send** the invite wave ([rise-tryout.md](rise-tryout.md) stays PREP only).

See also: [launch-readiness.md](../internal/launch-readiness.md) · [pre-stranger-handoff.md](pre-stranger-handoff.md) · [rise-tryout.md](rise-tryout.md)
