# Buyer questions (human review checklist)

> Local pack gates. Humans review. Not conformity assessment.
> Not CE / not notified-body.

- **Packs:** house-policy
- **Assurance class:** `structural_draft`
- **Attestation status:** `none`

| gate_id | severity | human_question | artifact_path | assurance_class | remediation_hint |
|---|---|---|---|---|---|
| HOUSE-SECURITY-MD | high | For human review: SECURITY.md missing, too short, or lacking required header? | SECURITY.md | structural_draft | Add SECURITY.md with vulnerability reporting and response expectations. |
| HOUSE-SECURITY-TXT | medium | For human review: security.txt missing under .well-known/ (RFC 9116 style)? | .well-known/security.txt | structural_draft | Create .well-known/security.txt with Contact and Expires fields. |
| HOUSE-DEP-AXIOS-PIN | critical | For human review: House policy bans vulnerable axios@1.6.0 pins in package.json? | package.json | structural_draft | Upgrade axios to a patched release and refresh the lockfile. |
| HOUSE-SECRET-PATHS | critical | For human review: Likely secrets or private key material found in tracked policy docs or common agent secret paths? | README.md, SECURITY.md, .well-known/security.txt, .env, .env.local, credentials.json, service-account.json, id_rsa | structural_draft | Remove credentials from docs and agent-oops paths; rotate any exposed secrets; use a secret manager. |
| HOUSE-ANTI-PLACEHOLDER | high | For human review: House policy docs contain placeholder / boilerplate text? | .well-known/security.txt | structural_draft | Replace TODO / lorem ipsum / [insert ...] with real contact and process details. |
