package packs_test

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/packs"
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

func TestValidatePackRefusesPathEscape(t *testing.T) {
	bad := packs.Pack{ID: "evil", Name: "Evil", Version: "1", Rules: []packs.Rule{{
		ID: "ESCAPE", Check: "file_present", Path: "../outside", Severity: "high",
		Description: "escape", Remediation: "fix", Expected: "inside",
	}}}
	if err := packs.ValidatePack(bad); err == nil {
		t.Fatal("expected path traversal refuse")
	}
	bad2 := packs.Pack{ID: "evil", Name: "Evil", Version: "1", Rules: []packs.Rule{{
		ID: "GIT", Check: "file_present", Path: ".git/hooks/pre-commit", Severity: "high",
		Description: "git", Remediation: "fix", Expected: "no",
	}}}
	if err := packs.ValidatePack(bad2); err == nil {
		t.Fatal("expected .git path refuse")
	}
	if err := packs.ValidateRelPath("../outside"); err == nil {
		t.Fatal("ValidateRelPath must refuse ../outside")
	}
}

func TestScaffoldPaths(t *testing.T) {
	paths, err := packs.ScaffoldPaths([]string{"cra-baseline"})
	if err != nil {
		t.Fatal(err)
	}
	want := []string{
		"docs/annex-vii/risk_assessment.md",
		"docs/incident/art14-path.md",
	}
	for _, w := range want {
		found := false
		for _, p := range paths {
			if p == w {
				found = true
				break
			}
		}
		if !found {
			t.Fatalf("missing scaffold path %s in %v", w, paths)
		}
	}
	house, err := packs.ScaffoldPaths([]string{"house-policy"})
	if err != nil {
		t.Fatal(err)
	}
	for _, p := range house {
		if p == "docs/incident/art14-path.md" {
			t.Fatal("Art 14 path must not be a house-policy default scaffold")
		}
	}
}

func TestRuleTouchesDiffAlwaysRunsFilePresent(t *testing.T) {
	changed := map[string]struct{}{"README.md": {}}
	r := packs.Rule{ID: "HOUSE-SECURITY-MD", Check: "file_present", Path: "SECURITY.md"}
	if !packs.RuleTouchesDiff(r, changed) {
		t.Fatal("file_present must always evaluate under --diff")
	}
	r2 := packs.Rule{ID: "HOUSE-ANTI-PLACEHOLDER", Check: "anti_placeholder", Paths: []string{"SECURITY.md"}}
	if !packs.RuleTouchesDiff(r2, changed) {
		t.Fatal("anti_placeholder on untouched SECURITY.md must always evaluate under --diff")
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
	// Deep nesting of groups with quantifiers is accepted when RE2-valid and under length.
	nested := "((((a*)*)*)*)*"
	if err := packs.ValidateRegexPattern(nested); err != nil {
		t.Fatalf("expected nested pattern under length to accept: %v", err)
	}
	if err := packs.ValidateRegexPattern(`(`); err == nil {
		t.Fatal("expected invalid compile")
	}
}

func TestComposeMedtechExtendsCRA(t *testing.T) {
	p, sources, err := packs.Compose([]string{"medtech-iec62304"})
	if err != nil {
		t.Fatal(err)
	}
	if len(sources) < 2 {
		t.Fatalf("expected cra+medtech sources, got %v", sources)
	}
	ids := map[string]bool{}
	for _, r := range p.Rules {
		ids[r.ID] = true
	}
	if !ids["CRA-ANNEX-VII-RISK"] || !ids["MD-SW-CLASS"] {
		t.Fatalf("composed rules missing CRA or MD: %v", ids)
	}
}

func TestComposeExtendsCycle(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("CURBPACK_PACKS_DIR", dir)
	mustPack(t, dir, "a", `{"id":"a","name":"A","version":"1","extends":"b","rules":[{"id":"A1","severity":"high","type":"POLICY_VIOLATION","check":"file_present","path":"SECURITY.md","description":"d","remediation":"r","expected":"e"}]}`)
	mustPack(t, dir, "b", `{"id":"b","name":"B","version":"1","extends":"a","rules":[{"id":"B1","severity":"high","type":"POLICY_VIOLATION","check":"file_present","path":"README.md","description":"d","remediation":"r","expected":"e"}]}`)
	if _, _, err := packs.Compose([]string{"a"}); err == nil {
		t.Fatal("expected cycle error")
	}
}

func TestValidatePackCitationDates(t *testing.T) {
	bad := packs.Pack{ID: "x", Name: "X", Version: "1", Citations: []packs.Citation{{
		EffectiveFrom: "2026-12-31", EffectiveTo: "2026-01-01",
	}}, Rules: []packs.Rule{{
		ID: "r", Check: "file_present", Path: "SECURITY.md", Severity: "high",
		Description: "d", Remediation: "r", Expected: "e",
	}}}
	if err := packs.ValidatePack(bad); err == nil {
		t.Fatal("expected inverted citation window error")
	}
}

func TestValidatePackFrameworkRequiresSettlement(t *testing.T) {
	bad := packs.Pack{ID: "x", Name: "X", Version: "1", Rules: []packs.Rule{{
		ID: "R1", Check: "file_present", Path: "SECURITY.md", Severity: "high",
		Description: "d", Remediation: "r", Expected: "e",
		Citations: []packs.Citation{{Framework: "EU", Instrument: "CRA"}},
	}}}
	err := packs.ValidatePack(bad)
	if err == nil {
		t.Fatal("expected settlement required when framework citation present")
	}
	if !strings.Contains(err.Error(), "settlement required") {
		t.Fatalf("unexpected err: %v", err)
	}
	bad.Rules[0].Settlement = "maybe"
	if err := packs.ValidatePack(bad); err == nil {
		t.Fatal("expected invalid settlement value")
	}
	bad.Rules[0].Settlement = packs.SettlementIndicative
	if err := packs.ValidatePack(bad); err != nil {
		t.Fatal(err)
	}
}

func TestCRAAnnexRulesIndicative(t *testing.T) {
	p, err := packs.LoadPack("cra-baseline")
	if err != nil {
		t.Fatal(err)
	}
	for _, r := range p.Rules {
		if r.ID == "CRA-DEP-AXIOS-PIN" {
			if packs.EffectiveSettlement(r) != packs.SettlementSettles {
				t.Fatalf("%s settlement=%q want settles", r.ID, r.Settlement)
			}
			continue
		}
		if packs.EffectiveSettlement(r) != packs.SettlementIndicative {
			t.Fatalf("%s settlement=%q want indicative", r.ID, r.Settlement)
		}
		if !packs.RuleHasFrameworkCitation(r) {
			t.Fatalf("%s missing rule-level framework citation", r.ID)
		}
	}
	md, err := packs.LoadPack("medtech-iec62304")
	if err != nil {
		t.Fatal(err)
	}
	for _, r := range md.Rules {
		if packs.EffectiveSettlement(r) != packs.SettlementIndicative {
			t.Fatalf("%s settlement=%q want indicative", r.ID, r.Settlement)
		}
	}
}

func TestBuildPolicyGraphSchema(t *testing.T) {
	g, err := packs.BuildPolicyGraph([]string{"house-policy"})
	if err != nil {
		t.Fatal(err)
	}
	if g.SchemaVersion != packs.GraphSchemaVersion {
		t.Fatalf("schema_version=%q", g.SchemaVersion)
	}
	if len(g.Nodes) == 0 || len(g.Edges) == 0 {
		t.Fatal("expected nodes and edges")
	}
}

func TestExportTreeMatchesEmbeddedPackJSON(t *testing.T) {
	_, thisFile, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	root := filepath.Clean(filepath.Join(filepath.Dir(thisFile), "..", ".."))
	for _, id := range []string{"cra-baseline", "house-policy", "medtech-iec62304"} {
		exportB, err := os.ReadFile(filepath.Join(root, "packs", id, "pack.json"))
		if err != nil {
			t.Fatal(err)
		}
		embedB, err := os.ReadFile(filepath.Join(root, "internal", "packs", "data", id, "pack.json"))
		if err != nil {
			t.Fatal(err)
		}
		if string(exportB) != string(embedB) {
			t.Fatalf("pack.json twins drifted for %s (packs/%s/pack.json vs internal/packs/data/%s/pack.json)", id, id, id)
		}
	}
}

func TestScaffoldOverlap_HealStubAndToken(t *testing.T) {
	rel := "SECURITY.md"
	stub := packs.DefaultScaffoldBody(rel)
	if !packs.ScaffoldOverlap(stub, rel, "") {
		t.Fatal("exact DefaultScaffoldBody must overlap")
	}
	if packs.ScaffoldOverlap("# Security\n\nHouse policy prose.\n", rel, "") {
		t.Fatal("human prose must not overlap")
	}
	withToken := stub + "\nacme-widget\n"
	if !packs.ScaffoldOverlap(withToken, rel, "acme-widget") {
		t.Fatal("stub plus token insertion must still overlap")
	}
}

func mustPack(t *testing.T, dir, id, body string) {
	t.Helper()
	d := filepath.Join(dir, id)
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(d, "pack.json"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}
