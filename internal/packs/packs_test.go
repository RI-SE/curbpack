package packs_test

import (
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/packs"
)

func TestValidatePackSchema(t *testing.T) {
	p, err := packs.LoadPack("house-policy")
	if err != nil {
		t.Fatal(err)
	}
	if err := packs.ValidatePack(p); err != nil {
		t.Fatal(err)
	}
	bad := packs.Pack{ID: "x", Name: "X", Version: "1", Rules: []packs.Rule{{
		ID: "r", Check: "nope", Severity: "high", Description: "d",
	}}}
	if err := packs.ValidatePack(bad); err == nil {
		t.Fatal("expected unsupported check error")
	}
}

func TestScaffoldPaths(t *testing.T) {
	paths, err := packs.ScaffoldPaths([]string{"cra-baseline"})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, p := range paths {
		if p == "docs/annex-vii/risk_assessment.md" {
			found = true
		}
	}
	if !found {
		t.Fatalf("missing annex path in %v", paths)
	}
}

func TestRuleTouchesDiffAlwaysRunsFilePresent(t *testing.T) {
	changed := map[string]struct{}{"README.md": {}}
	r := packs.Rule{ID: "HOUSE-SECURITY-MD", Check: "file_present", Path: "SECURITY.md"}
	if !packs.RuleTouchesDiff(r, changed) {
		t.Fatal("file_present must always evaluate under --diff")
	}
	r2 := packs.Rule{ID: "HOUSE-ANTI-PLACEHOLDER", Check: "anti_placeholder", Paths: []string{"SECURITY.md"}}
	if packs.RuleTouchesDiff(r2, changed) {
		t.Fatal("anti_placeholder on untouched SECURITY.md may skip under --diff")
	}
}

func TestValidateRegexPatternLimits(t *testing.T) {
	if err := packs.ValidateRegexPattern(`secret`); err != nil {
		t.Fatal(err)
	}
	long := strings.Repeat("a", packs.MaxRegexPatternLen+1)
	if err := packs.ValidateRegexPattern(long); err == nil {
		t.Fatal("expected length reject")
	}
	// Deep nesting of groups with quantifiers
	nested := "((((a*)*)*)*)*"
	if err := packs.ValidateRegexPattern(nested); err == nil {
		t.Fatal("expected nested quantifier reject")
	}
	if err := packs.ValidateRegexPattern(`(`); err == nil {
		t.Fatal("expected invalid compile")
	}
}
