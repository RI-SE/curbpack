package packs_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/packs"
)

func TestDoctorCitationUnverifiedAndStale(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("CURBPACK_PACKS_DIR", dir)

	// Override house-policy so DoctorPacks (which walks builtin ids) loads ACMP-shaped currency fields.
	p := packs.Pack{
		ID:                  "house-policy",
		Name:                "House Policy (currency fixture)",
		Version:             "9.9.9",
		Description:         "Informational fixture for packs doctor citation currency.",
		RecheckIntervalDays: 30,
		Citations: []packs.Citation{{
			Framework:       "ISO",
			Instrument:      "ISO 10007",
			Article:         "configuration management",
			Edition:         "ACMP-2100 shape",
			VerifiedAgainst: "ISO 10007:2017",
			VerifiedOn:      "2020-01-01",
		}},
		Rules: []packs.Rule{{
			ID: "HOUSE-SECURITY-MD", Check: "file_present", Path: "SECURITY.md",
			Severity: "high", Description: "d", Remediation: "r", Expected: "e",
			Settlement: packs.SettlementIndicative,
			Citations: []packs.Citation{{
				Framework: "ISO", Instrument: "ISO 10007",
			}},
		}},
	}
	b, err := json.MarshalIndent(p, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	packDir := filepath.Join(dir, "house-policy")
	if err := os.MkdirAll(packDir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(packDir, "pack.json"), append(b, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}

	f, err := packs.DoctorPacks()
	if err != nil {
		t.Fatal(err)
	}
	foundUnverified := false
	for _, u := range f.Unverified {
		if strings.Contains(u, "HOUSE-SECURITY-MD") || strings.Contains(u, "missing verified_on") {
			foundUnverified = true
			break
		}
	}
	if !foundUnverified {
		t.Fatalf("expected unverified findings, got %v", f.Unverified)
	}
	foundStale := false
	for _, s := range f.Stale {
		if strings.Contains(s, "2020-01-01") || strings.Contains(s, "recheck_interval") {
			foundStale = true
			break
		}
	}
	if !foundStale {
		t.Fatalf("expected stale findings, got %v", f.Stale)
	}
}

func TestDoctorBuiltinFrameworkUnverified(t *testing.T) {
	f, err := packs.DoctorPacks()
	if err != nil {
		t.Fatal(err)
	}
	// CRA/medtech rule-level framework cites lack verified_on → advisory unverified (exit 0 at CLI).
	if len(f.Unverified) == 0 {
		t.Fatal("expected builtin framework citations without verified_on to be unverified")
	}
}
