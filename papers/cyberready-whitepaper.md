# CyberReady+ White Paper

**Local evidence preparation for human review**  
Technical description of architecture, packs-as-data, dual representation, evidence artifacts, trust boundaries, and limitations.

> CyberReady prepares evidence for **human review**. It does **not** certify conformity, issue CE marks, or replace a notified body or auditor.

---

## 1. Problem framing

Software suppliers and product teams must show documentation and dependency hygiene against house rules or regulatory-shaped checklists. Spreadsheets and ad-hoc scripts drift. Cloud “compliance platforms” move source of truth off the machine and blur who decided what.

CyberReady+ is a **local-first command-line interface (CLI)**. It evaluates **packs** (JSON rule sets) against a git repository, emits machine- and human-readable findings, and can bind a reproducible state digest into Git Notes. Judgment stays with people.

## 2. Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Pack JSON  │────▶│  Validate    │────▶│ GateFailure IR  │
│  (embedded  │     │  engine      │     │ JSON + markdown │
│  or dir)    │     └──────────────┘     └────────┬────────┘
└─────────────┘                                   │
                                                  ▼
                                    ┌─────────────────────────┐
                                    │ Review pack / evidence  │
                                    │ + optional attest note  │
                                    └─────────────────────────┘
```

- **Engine:** industry-agnostic check kinds (`file_present`, `text_forbid`, dependency bans, etc.).
- **Packs:** data only — CRA-shaped annex drafts, house policy, sector templates.
- **No remote policy brain** required for daily `check`.

Optional: Unix-domain socket bridge for IDE agents (Coreward). Fail-open if absent. Socket defaults to a private path with mode `0600`.

## 3. Packs as data

Packs ship embedded in the binary and may be overridden via `CYBERREADY_PACKS_DIR`. Schema validation rejects unknown check types and oversized or pathological regex patterns at load time.

Network pack updates are **disabled unless** both `CYBERREADY_PACKS_URL` and `CYBERREADY_PACKS_SHA256` are set. Air-gap import is the preferred refresh path.

Watchlists are informational and never fail validation.

## 4. Dual representation

Every validate/check run produces:

1. **JSON intermediate representation (IR)** — `GateFailure` payloads with `schema_version`, severities, remediations.
2. **Semantic markdown** — agent- and human-readable action report.

Exit codes are stable: `0` pass, `1` gate failures / operational error, `2` usage / environment.

## 5. Evidence artifacts

| Artifact | Role |
|----------|------|
| Review pack layers | Gate JSON, action report, executive summary |
| Buyer one-pager HTML | Single-screen snapshot for procurement (not a certificate) |
| CycloneDX (best-effort) | SBOM from lockfiles when present |
| OpenVEX draft | Pending findings bound at attest time |
| HPURL pointer | Local `state_hash` for client-side fragment verify |
| Git Notes capsule | Commit-bound capsule; signature optional |

`prepare-release` skips rewriting the one-pager when the gate fingerprint is unchanged. Daily `check` does not generate or open the one-pager.

## 6. Attestation and trust boundaries

State hash seed: `commit|parent|sbom_digest|vex_digest` (no wall-clock in the hash).

| State | Meaning |
|-------|---------|
| `ssh-agent-signed` | Real SSH signature produced |
| `not-verified` / unsigned | Capsule present; **not** cryptographically verified |

Synthetic `agent-bind:` tokens are never accepted as verified signatures. Unsigned ≠ verified.

Install paths (`install.sh`, GitHub Action) verify release `checksums.txt` with sha256 and fail closed on mismatch.

## 7. Non-claims

CyberReady does not:

- Certify conformity or grant CE marking
- Replace notified bodies, auditors, or legal counsel
- Guarantee absence of vulnerabilities
- Claim that green gates equal market access

Public marketing and CI claim-safety scanners enforce this language.

## 8. Limitations

- Pack coverage is only as good as pack authors; false confidence is possible if packs are thin.
- Regex and text checks are heuristics with size/time guards — not full program analysis.
- SBOM/VEX generation is best-effort from common Node lockfiles.
- Windows is unsupported for release binaries and the sock bridge.
- Client-side HPURL verify does not imply remote notary services.

## 9. Related surfaces

- Product narrative: public static site under `site/`
- Security plain language: `docs/security-model.md`
- Install and commands: repository README

---

*Document version aligned with CyberReady+ open-source line. No go-to-market playbooks or CI runbooks are included here by design.*
