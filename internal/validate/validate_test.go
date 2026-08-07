package validate_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/cyberready/internal/packs"
	"github.com/afelin/cyberready/internal/validate"
)

// Note: tests avoid `git init` so they run under restricted sandboxes.

func TestLoadEmbeddedPacks(t *testing.T) {
	ps, err := packs.LoadEmbedded()
	if err != nil {
		t.Fatal(err)
	}
	if len(ps) != 2 {
		t.Fatalf("expected 2 packs, got %d", len(ps))
	}
	wl, err := packs.LoadWatchlist()
	if err != nil {
		t.Fatal(err)
	}
	if len(wl.Entries) < 1 {
		t.Fatal("watchlist empty")
	}
}

func TestAntiPlaceholder(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/risk_assessment.md"), `# Risk Assessment

## Product Overview

TODO: fill this in with lorem ipsum

## Identified Risks

placeholder content here for testing
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/support_period.md"), `# Support Period

## End of Support

Supported until 2030-12-31 with security patches.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/user_manual_security.md"), `# User Manual — Security

## Secure Configuration

Use TLS everywhere and rotate credentials quarterly with documented runbooks.

## Product Disposal

Wipe customer data and destroy keys before hardware disposal.
`)

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"cra-baseline"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("expected placeholder failure")
	}
	found := false
	for _, f := range res.Payload.Failures {
		if f.GateID == "CRA-ANTI-PLACEHOLDER" {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected CRA-ANTI-PLACEHOLDER, got %#v", res.Payload.Failures)
	}
}

func TestValidatePassFixture(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodCRA(t, dir)

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"cra-baseline"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Passed {
		t.Fatalf("expected pass, failures=%v md=%s", res.Payload.Failures, validate.SemanticMarkdown(res.Payload))
	}
	if res.Score != 100 {
		t.Fatalf("score=%d", res.Score)
	}
}

func writeGoodCRA(t *testing.T, dir string) {
	t.Helper()
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/risk_assessment.md"), `# Risk Assessment

## Product Overview

The Contoso Sensor Gateway forwards telemetry from clinical devices to a hospital EHR over mutually authenticated TLS.

## Identified Risks

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R-001   | Credential stuffing on admin UI | High | MFA + lockout |

## Residual Risk Statement

Residual risk is accepted by the product owner after mitigations above.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/support_period.md"), `# Support Period

## End of Support

Security updates are provided for five years from the general availability date of each major release.

## Rationale

Aligned with expected clinical deployment lifetime and spare-parts availability.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/user_manual_security.md"), `# User Manual — Security

## Secure Configuration

Disable default accounts, enforce MFA, and restrict management interfaces to the hospital VLAN.

## Product Disposal

Factory-reset the appliance, shred exported key material, and confirm cloud tenant deletion.
`)
}

func initGit(t *testing.T, dir string) {
	t.Helper()
	// Fake .git dir — avoids sandbox/git-template permission issues in CI agents.
	if err := os.MkdirAll(filepath.Join(dir, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "README.md"), "# fixture\n")
}

func mustWrite(t *testing.T, path, body string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}
