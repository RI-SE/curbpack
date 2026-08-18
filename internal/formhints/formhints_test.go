package formhints

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/remediation"
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

func TestApplyStubsRefusesTraversal(t *testing.T) {
	dir := t.TempDir()
	_, err := ApplyStubs(dir, []Hint{{
		GateID:  "X",
		File:    "../../../etc/passwd",
		Snippet: "nope\n",
	}})
	if err == nil {
		t.Fatal("expected traversal error")
	}
}

func TestApplyStubsHealsEmptyFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "SECURITY.md")
	if err := os.WriteFile(path, []byte{}, 0o644); err != nil {
		t.Fatal(err)
	}
	out, err := ApplyStubs(dir, []Hint{{
		GateID:  "HOUSE-SECURITY-MD",
		File:    "SECURITY.md",
		Snippet: "# Security\n\nhealed\n",
	}})
	if err != nil {
		t.Fatal(err)
	}
	if !out[0].Applied {
		t.Fatal("expected empty file healed")
	}
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(b), "healed") {
		t.Fatalf("empty heal missing content: %q", b)
	}
}

func TestApplyStubsRefusesSymlink(t *testing.T) {
	dir := t.TempDir()
	target := filepath.Join(dir, "outside.md")
	if err := os.WriteFile(target, []byte("secret\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(dir, "SECURITY.md")
	if err := os.Symlink(target, link); err != nil {
		t.Fatal(err)
	}
	_, err := ApplyStubs(dir, []Hint{{
		GateID:  "HOUSE-SECURITY-MD",
		File:    "SECURITY.md",
		Snippet: "OVERWRITE\n",
	}})
	if err == nil || !strings.Contains(err.Error(), "symlink") {
		t.Fatalf("want symlink refuse, got %v", err)
	}
	keep, _ := os.ReadFile(target)
	if strings.Contains(string(keep), "OVERWRITE") {
		t.Fatal("must not follow symlink and overwrite target")
	}
}

func TestResolveFilePrefersPackPath(t *testing.T) {
	hints := ForFailures([]ir.Failure{
		{
			GateID:         "MD-SW-CLASS",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "docs/medtech/software_safety_class.md"},
		},
		{
			GateID:         "MD-SOUP",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "docs/medtech/soup_list.md"},
		},
		{
			GateID:         "MD-PROBLEM-RESOLUTION",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "docs/medtech/problem_resolution.md"},
		},
	})
	want := []string{
		"docs/medtech/software_safety_class.md",
		"docs/medtech/soup_list.md",
		"docs/medtech/problem_resolution.md",
	}
	if len(hints) != len(want) {
		t.Fatalf("want %d hints, got %d", len(want), len(hints))
	}
	for i, h := range hints {
		if h.File != want[i] {
			t.Fatalf("hint %d file=%q want %q", i, h.File, want[i])
		}
		if strings.Contains(h.File, "iec62304") {
			t.Fatalf("stale iec62304 path: %q", h.File)
		}
	}
}

func TestResolveFileMedtechBasenameOnlyIR(t *testing.T) {
	hints := ForFailures([]ir.Failure{
		{
			GateID:         "MD-SW-CLASS",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "software_safety_class.md"},
		},
		{
			GateID:         "MD-SOUP",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "soup_list.md"},
		},
		{
			GateID:         "MD-PROBLEM-RESOLUTION",
			ASTCoordinates: ir.ASTCoordinates{TargetFile: "problem_resolution.md"},
		},
	})
	want := []string{
		"docs/medtech/software_safety_class.md",
		"docs/medtech/soup_list.md",
		"docs/medtech/problem_resolution.md",
	}
	if len(hints) != len(want) {
		t.Fatalf("want %d hints, got %d", len(want), len(hints))
	}
	for i, h := range hints {
		if h.File != want[i] {
			t.Fatalf("basename-only IR hint %d file=%q want %q", i, h.File, want[i])
		}
		if strings.Contains(h.File, "iec62304") {
			t.Fatalf("stale iec62304 path: %q", h.File)
		}
	}
	if !strings.Contains(hints[0].Snippet, "# Software Safety Class") {
		t.Fatalf("safety snippet missing header: %q", hints[0].Snippet)
	}
	if !strings.Contains(hints[1].Snippet, "# SOUP List") {
		t.Fatalf("soup snippet missing header: %q", hints[1].Snippet)
	}
	if !strings.Contains(hints[2].Snippet, "# Problem Resolution") {
		t.Fatalf("problem snippet missing header: %q", hints[2].Snippet)
	}
}

func TestResolveFileMedtechEmptyTargetGuessesPackPath(t *testing.T) {
	hints := ForFailures([]ir.Failure{
		{GateID: "MD-SW-CLASS"},
		{GateID: "MD-SOUP"},
		{GateID: "MD-PROBLEM-RESOLUTION"},
	})
	want := []string{
		"docs/medtech/software_safety_class.md",
		"docs/medtech/soup_list.md",
		"docs/medtech/problem_resolution.md",
	}
	if len(hints) != len(want) {
		t.Fatalf("want %d hints, got %d", len(want), len(hints))
	}
	for i, h := range hints {
		if h.File != want[i] {
			t.Fatalf("empty-target hint %d file=%q want %q", i, h.File, want[i])
		}
	}
}

func TestCachePreferredSnippet(t *testing.T) {
	dir := t.TempDir()
	c := remediation.Cache{Entries: map[string]remediation.Entry{
		"HOUSE-SECURITY-MD": {
			GateID:  "HOUSE-SECURITY-MD",
			File:    "SECURITY.md",
			Snippet: "# Security\n\nCached reporting body with enough words for house policy gates here.\n",
		},
	}}
	hints := ForFailuresCached([]ir.Failure{{
		GateID:         "HOUSE-SECURITY-MD",
		ASTCoordinates: ir.ASTCoordinates{TargetFile: "SECURITY.md"},
	}}, c)
	if !hints[0].FromCache || !strings.Contains(hints[0].Snippet, "Cached reporting") {
		t.Fatalf("want cache hit: %+v", hints[0])
	}
	out, err := ApplyStubs(dir, hints)
	if err != nil {
		t.Fatal(err)
	}
	if err := PersistCache(dir, out); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dir, ".github/curbpack/cache/remediations.json")); err != nil {
		t.Fatal(err)
	}
}
