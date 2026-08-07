package formhints

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/ir"
)

func TestForFailuresDeterministic(t *testing.T) {
	hints := ForFailures([]ir.Failure{
		{
			GateID: "HOUSE-SECURITY-MD",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "SECURITY.md"},
			Remediation:    ir.Remediation{ActionRequired: "Add SECURITY.md"},
		},
		{
			GateID: "CRA-ANNEX-VII-RISK",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "docs/annex-vii/risk_assessment.md"},
		},
		{
			GateID: "CRA-DEP-AXIOS-PIN",
		},
	})
	if len(hints) != 3 {
		t.Fatalf("want 3 hints, got %d", len(hints))
	}
	if hints[0].File != "SECURITY.md" || !strings.Contains(hints[0].Snippet, "# Security") {
		t.Fatalf("security hint: %+v", hints[0])
	}
	if !strings.Contains(hints[1].Snippet, "# Risk Assessment") {
		t.Fatalf("risk snippet missing: %q", hints[1].Snippet)
	}
	if !strings.Contains(hints[2].Snippet, "not auto-written") {
		t.Fatalf("dep hint should refuse auto-write: %q", hints[2].Snippet)
	}
	text := Format(hints)
	if !strings.Contains(text, "propose-only") {
		t.Fatalf("format missing propose-only: %s", text)
	}
}

func TestApplyStubsProposeOnlyDefault(t *testing.T) {
	dir := t.TempDir()
	// fake .git so tools that walk roots are happy if needed
	_ = os.MkdirAll(filepath.Join(dir, ".git"), 0o755)
	hints := []Hint{{
		GateID:  "HOUSE-SECURITY-TXT",
		File:    ".well-known/security.txt",
		Snippet: "Contact: mailto:t@example.com\nExpires: 2027-12-31T23:59:59.000Z\n",
	}}
	out, err := ApplyStubs(dir, hints)
	if err != nil {
		t.Fatal(err)
	}
	if !out[0].Applied {
		t.Fatal("expected stub applied to missing file")
	}
	b, err := os.ReadFile(filepath.Join(dir, ".well-known", "security.txt"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(b), "Contact:") {
		t.Fatalf("bad content: %s", b)
	}
	// non-empty should not overwrite
	_ = os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("# Security\n\nkeep me\n"), 0o644)
	out2, err := ApplyStubs(dir, []Hint{{
		GateID:  "HOUSE-SECURITY-MD",
		File:    "SECURITY.md",
		Snippet: "OVERWRITE\n",
	}})
	if err != nil {
		t.Fatal(err)
	}
	if out2[0].Applied {
		t.Fatal("must not overwrite non-empty file")
	}
	keep, _ := os.ReadFile(filepath.Join(dir, "SECURITY.md"))
	if strings.Contains(string(keep), "OVERWRITE") {
		t.Fatal("overwrote existing content")
	}
}
