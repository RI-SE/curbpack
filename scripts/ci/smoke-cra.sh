#!/usr/bin/env bash
# CI smoke: CRA fixture green check + prepare-release
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
FIX=$(mktemp -d)
cd "$FIX"
git init -q
git config user.email "ci@curbpack.local"
git config user.name "CI"
git commit --allow-empty -m init -q
"$BIN" init --packs cra-baseline --yes
printf '%s\n' '# contoso-gateway' > README.md
printf '%s\n' '{"name":"contoso-gateway","version":"1.0.0","dependencies":{}}' > package.json
mkdir -p docs/annex-vii docs/incident
cat > docs/annex-vii/risk_assessment.md <<'EOF'
# Risk Assessment

## Product Overview

The contoso-gateway product forwards telemetry from clinical devices to a hospital EHR over mutually authenticated TLS.

## Identified Risks

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R-001   | Credential stuffing on admin UI | High | MFA + lockout |

## Residual Risk Statement

Residual risk is accepted by the product owner after mitigations above.
EOF
cat > docs/annex-vii/support_period.md <<'EOF'
# Support Period

## End of Support

Security updates for contoso-gateway are provided for five years from the general availability date of each major release.

## Rationale

Aligned with expected clinical deployment lifetime and spare-parts availability.
EOF
cat > docs/annex-vii/user_manual_security.md <<'EOF'
# User Manual — Security

## Secure Configuration

Disable default accounts on contoso-gateway, enforce MFA, and restrict management interfaces to the hospital VLAN.

## Product Disposal

Factory-reset the appliance, shred exported key material, and confirm cloud tenant deletion.
EOF
cat > docs/incident/art14-path.md <<'EOF'
# Art 14 reporting path

## Reporting clock (CRA Art 14)

For contoso-gateway, actively exploited or severe incidents are reported by the on-call owner using the in-repo rehearsal dated 2026-04-12. This is a file record for CRA Article 14 reporting (clock from 11 September 2026, including products already on the market). It is not a live Single Reporting Platform check and does not assert that EU Login works.

## Handling clock (not this file)

Vulnerability handling and public security contact for contoso-gateway are documented separately. They sit on a later clock than Article 14 reporting and are not this rehearsal.

## Named owner

Product security on-call for contoso-gateway owns the reporting path. Escalation is the engineering manager of record in SECURITY.md.

## Rehearsal dated artifact

Last tabletop: 2026-04-12. Record: this file plus the incident mail template under docs/incident/ (in-repo). Not a live submission.
EOF
"$BIN" check
"$BIN" prepare-release
test -f review-pack/buyer-onepager.html
test -f .github/curbpack/cache/latest_action_report.md
