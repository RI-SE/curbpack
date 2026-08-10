# CyberReady+ White Paper

**Local evidence preparation for human review**

CyberReady checks your repository against local rule packs and writes a review pack you can hand to a buyer or auditor—on your machine, without claiming certification.

> Not conformity assessment. Not CE marking. Not a notified-body opinion.

Canonical voice: [`docs/voice-and-terms.md`](../docs/voice-and-terms.md).

---

## 1. Problem

Software suppliers must show documentation and dependency hygiene against house rules or regulatory-shaped checklists. Spreadsheets drift. Cloud governance-risk-compliance (GRC) platforms move source of truth off the machine and blur who decided what.

Teams need a local habit: check the tree, write evidence humans can hand to a buyer or auditor, and keep judgment with people—not a certificate of conformity.

## 2. Position

CyberReady+ is a **local-first command-line interface (CLI)**. It evaluates **rule packs** (JSON rule sets) against a git repository, emits machine- and human-readable findings, and can bind a reproducible state digest into Git Notes.

- Packs are **data** (checklists shaped like regulatory annex drafts—not law).
- Default cold start is **house-policy**. Cyber Resilience Act (CRA)–shaped packs are opt-in only.
- Humans retain judgment; gate pass means gates passed on this tree for human review.

## 3. Architecture

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
- **No remote policy service** required for daily `check`.
- Optional Unix-domain socket for IDE/integrator IPC — continues if unused; socket defaults to a private path with mode `0600`.

## 4. Worked example

1. **Red findings** — e.g. missing `SECURITY.md`, forbidden claim-adjacent wording, incomplete dependency pin note. `cyberready check` exits non-zero; machine-readable findings (JSON) and a short markdown report list severity and remediation.
2. **Remediate** — add the disclosure path, remove certification theater, record the pin; optionally `cyberready check --heal` for missing stubs only.
3. **Re-check** — gates passed on this tree (exit 0). Local gate score is not certification.
4. **Review pack** — `prepare-release` writes layered reports and a buyer one-pager (supplier evidence summary).
5. **Optional attest** — a human runs `attest` when ready. Until ssh-agent signed: **UNSIGNED — not cryptographically verified**.

A committed teaching sample (before/after): [`site/samples/onepager.html`](../site/samples/onepager.html).

## 5. Evidence catalog and trust levels

| Artifact | Trust level (honest) |
|----------|----------------------|
| Gate JSON / action report | Structural evidence — reproducible locally; not a legal finding |
| SARIF export | Same gates in CI/IDE format — not certification |
| Buyer-questions / ContextPack / lay-of-land | Human checklist, washed assistant snapshot, map — not a CVE product |
| Review pack / buyer one-pager | Procurement snapshot — not a certificate of conformity |
| CycloneDX SBOM / OpenVEX drafts | Best-effort inventory and draft notes |
| Git Notes attest capsule | **ssh-agent-signed** = signature present; **unsigned** ≠ verified |
| Explain-packet | Sanitized tutor surface — never greenlights gates |

**Unsigned ≠ verified.** Green readiness % is a **local gate score on this tree**, not a certification score.

## 6. Attestation and install integrity

State hash seed: `commit|parent|sbom_digest|vex_digest` (no wall-clock in the hash).

| State | Meaning |
|-------|---------|
| `ssh-agent-signed` | Real SSH signature produced |
| `not-verified` / unsigned | Capsule present; **not** cryptographically verified |

Synthetic `agent-bind:` tokens are never accepted as verified signatures.

Install paths (`install.sh`, GitHub Action) verify release `checksums.txt` with sha256 and fail closed on mismatch. Network pack updates require a sha256 pin; offline import is preferred.

## 7. Non-claims and RISE neutrality

CyberReady does not:

- Certify conformity or grant CE marking
- Replace notified bodies, auditors, or legal counsel
- Guarantee absence of vulnerabilities
- Claim that green gates equal market access

Development supported by RISE Research Institutes of Sweden as an applied research / competence object. RISE does not certify products that use CyberReady gate results.

Never claim “RISE-approved,” “NCSC-approved,” or agency-endorsed product claims. Public wording: [promotion firewall](../docs/promotion-firewall.md) · [voice and terms](../docs/voice-and-terms.md). CI enforces via `scripts/claim-safety.sh`.

## 8. Limitations

- Pack coverage is only as good as pack authors; thin packs create false confidence.
- Regex and text checks are heuristics with size/time guards — not full program analysis.
- SBOM/VEX generation is best-effort from common Node lockfiles.
- Windows is unsupported for release binaries and the sock bridge.
- Client-side hash-pointer verify does not imply remote notary services.

## 9. Glossary

| Term | Meaning in this paper |
|------|------------------------|
| **CE** | European conformity marking — CyberReady does not issue CE marks |
| **CRA** | EU Cyber Resilience Act — shapes some pack drafts; gate green ≠ legal conformity |
| **SBOM** | Software Bill of Materials (e.g. CycloneDX drafts) |
| **SARIF** | Static Analysis Results Interchange Format for CI/IDEs |
| **GRC** | Governance, Risk, Compliance platforms — not what CyberReady is |
| **Rule pack** | JSON checklist of gates; data, not hard-coded law |
| **Review pack** | Evidence folder for human review |
| **Buyer one-pager** | Supplier evidence summary HTML |
| **Structural evidence** | Documentation and dependency checks for humans |
| **Notified body** | Independent conformity-assessment organization — not replaced by this tool |
| **Conformity assessment** | Formal legal process — CyberReady prepares human-review evidence only |
| **VEX** | Vulnerability Exploitability eXchange — draft OpenVEX at attest |
| **ReDoS** | Regular expression denial-of-service — packs are length/time guarded |
| **OPA** | Open Policy Agent — explicit non-goal for OSS |

Full audience map: [`docs/glossary-and-audience.md`](../docs/glossary-and-audience.md). Authorities brief: [`docs/for-authorities.md`](../docs/for-authorities.md).

## 10. Related surfaces

- Product narrative: public static site under `site/`
- Adoption clarity: `docs/intent-vs-scope.md`
- Authorities / CISO: `docs/for-authorities.md`
- Security plain language: `docs/security-model.md`
- Install and commands: repository README
- Voice canon: `docs/voice-and-terms.md`

---

*Document version aligned with CyberReady+ open-source line. No go-to-market playbooks or CI runbooks are included here by design.*

> **Optional, separate product:** Coreward is a private tutor/enforce client that may consume CyberReady explain-packets over an optional Unix socket. CyberReady is fully self-sustaining without it — adopters do not need Coreward. Brief architecture note (public Pages, not the private repo): https://afelin.github.io/coreward/
