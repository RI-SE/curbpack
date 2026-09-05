package validate

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/packs"
)

// FG-03: import_reach ignored its declared path and passed missing/unparsable
// src/payment.go. SDD W1 removes the kind entirely (eight closed kinds remain).
func TestImportReachRemovedFromRegistry(t *testing.T) {
	for _, k := range KnownCheckKinds() {
		if string(k) == "import_reach" {
			t.Fatalf("import_reach must not remain registered; found %q", k)
		}
	}
	if _, ok := checkRegistry["import_reach"]; ok {
		t.Fatal("checkRegistry still maps import_reach")
	}
	if len(checkRegistry) != 8 {
		t.Fatalf("want 8 check kinds after import_reach removal, got %d", len(checkRegistry))
	}
}

func TestImportReachUnknownAtEval(t *testing.T) {
	rule := packs.Rule{
		ID:          "FG03-IMPORT-REACH",
		Check:       "import_reach",
		Path:        "docs/anything.md",
		Description: "legacy kind",
		Remediation: "remove",
		Expected:    "gone",
	}
	fs := evalRule(t.TempDir(), rule)
	if len(fs) == 0 {
		t.Fatal("import_reach must not silently pass (FG-03 false-green)")
	}
	if !strings.Contains(fs[0].SanitizedDescription, "Unknown check") {
		t.Fatalf("want unknown-check finding, got %#v", fs[0])
	}
}

func TestImportReachUnsupportedInPackValidate(t *testing.T) {
	p := packs.Pack{
		ID:      "fg03-pack",
		Name:    "fg03",
		Version: "0.0.1",
		Rules: []packs.Rule{{
			ID:          "r1",
			Severity:    "high",
			Type:        "CONTROL",
			Check:       "import_reach",
			Description: "legacy",
			Remediation: "remove",
			Expected:    "gone",
		}},
	}
	err := packs.ValidatePack(p)
	if err == nil {
		t.Fatal("ValidatePack must reject import_reach")
	}
	if !strings.Contains(err.Error(), "unsupported check") {
		t.Fatalf("want unsupported check error, got %v", err)
	}
}
