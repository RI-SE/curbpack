package validate_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/validate"
)

// Note: tests avoid `git init` so they run under restricted sandboxes.

func TestLoadEmbeddedPacks(t *testing.T) {
	ps, err := packs.LoadEmbedded()
	if err != nil {
		t.Fatal(err)
	}
	if len(ps) != 3 {
		t.Fatalf("expected 3 packs, got %d", len(ps))
	}
	wl, err := packs.LoadWatchlist()
	if err != nil {
		t.Fatal(err)
	}
	if len(wl.Entries) < 1 {
		t.Fatal("watchlist empty")
	}
}

func TestHousePolicyPass(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodHouse(t, dir)

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Passed {
		t.Fatalf("expected house pass, failures=%v", res.Payload.Failures)
	}
}

func TestHousePolicyMinWords(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), `# Security

x x x x x x x x x x
`+strings.Repeat(" \n", 40))
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("expected min_words failure on SECURITY.md")
	}
	found := false
	for _, f := range res.Payload.Failures {
		if f.GateID == "HOUSE-SECURITY-MD" && strings.Contains(f.SanitizedDescription, "min_words") {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected HOUSE-SECURITY-MD min_words, got %#v", res.Payload.Failures)
	}
}

func TestAntiPlaceholder(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	mustWrite(t, filepath.Join(dir, "package.json"), `{"name":"contoso-gateway","version":"1.0.0"}`+"\n")
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/risk_assessment.md"), `# Risk Assessment

## Product Overview

contoso-gateway — TODO: fill this in with lorem ipsum

## Identified Risks

placeholder content here for testing
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/support_period.md"), `# Support Period

## End of Support

contoso-gateway is supported until 2030-12-31 with security patches.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/user_manual_security.md"), `# User Manual — Security

## Secure Configuration

Use TLS everywhere on contoso-gateway and rotate credentials quarterly with documented runbooks.

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

func TestBindRepoTokenRejectsGenericLLMAnnex(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	mustWrite(t, filepath.Join(dir, "package.json"), `{"name":"acme-sensor","version":"1.0.0"}`+"\n")
	// Structurally complete annex with no product/repo token — hollow green theater.
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/risk_assessment.md"), `# Risk Assessment

## Product Overview

In today's digital landscape, organizations must manage cyber risk for connected products with a structured approach.

## Identified Risks

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R-001   | Generic admin UI risk | High | MFA + lockout |

## Residual Risk Statement

Residual risk is accepted by the product owner after mitigations above.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/support_period.md"), `# Support Period

## End of Support

Security updates are provided for five years from the general availability date of each major release.

## Rationale

Aligned with expected deployment lifetime and spare-parts availability.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/user_manual_security.md"), `# User Manual — Security

## Secure Configuration

Disable default accounts, enforce MFA, and restrict management interfaces to a trusted network.

## Product Disposal

Factory-reset the appliance, shred exported key material, and confirm cloud tenant deletion.
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
		t.Fatal("expected bind_repo_token failure for generic LLM annex")
	}
	foundBind := false
	for _, f := range res.Payload.Failures {
		if f.GateID == "CRA-ANNEX-VII-RISK" && strings.Contains(f.SanitizedDescription, "bind_repo_token") {
			foundBind = true
		}
	}
	if !foundBind {
		t.Fatalf("expected CRA-ANNEX-VII-RISK bind_repo_token, got %#v", res.Payload.Failures)
	}
}

func TestBindRepoTokenPassesWithPackageName(t *testing.T) {
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
		t.Fatalf("expected pass with package.json name token, failures=%v", res.Payload.Failures)
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
	if res.ActionReport == "" || !strings.Contains(res.ActionReport, "Action Report") {
		t.Fatal("missing action report")
	}
	cache := filepath.Join(dir, ".github/curbpack/cache/latest_action_report.md")
	if _, err := os.Stat(cache); err != nil {
		t.Fatal("action report not cached")
	}
}

func TestDiffSkipUntouchedRules(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodCRA(t, dir)
	mustWrite(t, filepath.Join(dir, "README.md"), "# fixture changed\n")

	// file_present / annex_file always evaluate under --diff (missing/short files never appear in porcelain).
	rule := packs.Rule{ID: "x", Check: "annex_file", Path: "docs/annex-vii/risk_assessment.md"}
	changed := map[string]struct{}{"README.md": {}}
	if !packs.RuleTouchesDiff(rule, changed) {
		t.Fatal("annex_file must always evaluate under --diff")
	}
	dep := packs.Rule{ID: "y", Check: "npm_dep_ban", Package: "axios", BannedVersions: []string{"1.6.0"}}
	if !packs.RuleTouchesDiff(dep, changed) {
		t.Fatal("pathless rules always run")
	}
	anti := packs.Rule{ID: "z", Check: "anti_placeholder", Paths: []string{"docs/annex-vii/risk_assessment.md"}}
	if !packs.RuleTouchesDiff(anti, changed) {
		t.Fatal("anti_placeholder on untouched annex must always evaluate under --diff")
	}
}

func TestPathTraversalFailClosed(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	wd, _ := os.Getwd()
	root := filepath.Clean(filepath.Join(wd, "../.."))
	t.Setenv("CURBPACK_PACKS_DIR", filepath.Join(root, "testdata/adversarial/packs"))

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"path-traversal"},
		Quiet:    true,
	})
	// Fail closed at pack load (ValidatePack) or as a gate finding — either is OK.
	if err != nil {
		if !strings.Contains(strings.ToLower(err.Error()), "traversal") &&
			!strings.Contains(strings.ToLower(err.Error()), "path") {
			t.Fatalf("expected path refuse in load error, got %v", err)
		}
		return
	}
	if res.Passed {
		t.Fatal("expected traversal failure")
	}
	found := false
	for _, f := range res.Payload.Failures {
		if f.GateID == "ADV-TRAVERSAL" && strings.Contains(strings.ToLower(f.SanitizedDescription), "traversal") {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected ADV-TRAVERSAL traversal fail, got %#v", res.Payload.Failures)
	}
}

func TestInvalidPackageJSONDepBanFail(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodHouse(t, dir)
	mustWrite(t, filepath.Join(dir, "package.json"), "{not-json\n")

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("invalid package.json must fail dep-ban / config gate")
	}
	found := false
	for _, f := range res.Payload.Failures {
		if strings.Contains(strings.ToLower(f.SanitizedDescription), "invalid package.json") {
			found = true
			break
		}
	}
	if !found {
		t.Fatalf("expected invalid package.json failure, got %#v", res.Payload.Failures)
	}
}

func TestBadRegexFailNoPanic(t *testing.T) {
	wd, _ := os.Getwd()
	root := filepath.Clean(filepath.Join(wd, "../.."))
	t.Setenv("CURBPACK_PACKS_DIR", filepath.Join(root, "testdata/adversarial/packs"))
	// Invalid pack regex is rejected at load (ReDoS / schema fail-closed).
	_, err := packs.LoadPack("bad-regex")
	if err == nil {
		t.Fatal("expected pack load to reject invalid pattern")
	}
	if !strings.Contains(err.Error(), "invalid pattern") && !strings.Contains(err.Error(), "pattern") {
		t.Fatalf("expected pattern error, got %v", err)
	}
}

func TestUnknownCheckPackLoad(t *testing.T) {
	wd, _ := os.Getwd()
	root := filepath.Clean(filepath.Join(wd, "../.."))
	t.Setenv("CURBPACK_PACKS_DIR", filepath.Join(root, "testdata/adversarial/packs"))
	_, err := packs.LoadPack("unknown-check")
	if err == nil {
		t.Fatal("expected unsupported check load error")
	}
	if !strings.Contains(err.Error(), "unsupported check") {
		t.Fatalf("unexpected err: %v", err)
	}
}

func TestOCCParentSoftFailNonGitRoot(t *testing.T) {
	dir := t.TempDir()
	writeGoodHouse(t, dir)

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	parent := res.Payload.ConcurrencyControl.ExpectedParentCommitSHA
	if parent != "" {
		t.Fatalf("expected empty OCC parent on non-git root, got %q", parent)
	}
	if strings.HasPrefix(parent, "000") {
		t.Fatal("must not inject zero SHA placeholder")
	}
}

func TestAntiPlaceholderUntouchedStubFails(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), packs.DefaultScaffoldBody("SECURITY.md"))
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), realSecurityTxt)
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("untouched SECURITY.md stub must fail anti_placeholder")
	}
	if !hasScaffoldOverlap(res, "HOUSE-ANTI-PLACEHOLDER", "SECURITY.md") {
		t.Fatalf("expected HOUSE-ANTI-PLACEHOLDER scaffold overlap on SECURITY.md, got %#v", res.Payload.Failures)
	}
}

func TestAntiPlaceholderStubPlusProductNameStillFails(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	mustWrite(t, filepath.Join(dir, "package.json"), `{"name":"acme-widget","version":"1.0.0"}`+"\n")
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), packs.DefaultScaffoldBody("SECURITY.md")+"\n\nacme-widget\n")
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), realSecurityTxt)
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("stub plus product name only must still fail anti_placeholder")
	}
	if !hasScaffoldOverlap(res, "HOUSE-ANTI-PLACEHOLDER", "SECURITY.md") {
		t.Fatalf("expected HOUSE-ANTI-PLACEHOLDER scaffold overlap on SECURITY.md, got %#v", res.Payload.Failures)
	}
}

func TestAntiPlaceholderRealSecurityMDPasses(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodHouse(t, dir)

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Passed {
		t.Fatalf("short real SECURITY.md with required header must pass, failures=%v", res.Payload.Failures)
	}
}

func TestHonestyEvalFolder(t *testing.T) {
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	evalRoot := filepath.Clean(filepath.Join(wd, "../..", "testdata/honesty-eval"))

	fakeSec, err := os.ReadFile(filepath.Join(evalRoot, "fake", "SECURITY.md"))
	if err != nil {
		t.Fatal(err)
	}
	if collapseEval(string(fakeSec)) != collapseEval(packs.DefaultScaffoldBody("SECURITY.md")) {
		t.Fatal("testdata/honesty-eval/fake/SECURITY.md must stay in sync with DefaultScaffoldBody")
	}

	cases := []struct {
		name    string
		subdir  string
		wantRed bool
	}{
		{name: "fake", subdir: "fake", wantRed: true},
		{name: "token-only", subdir: "token-only", wantRed: true},
		{name: "real", subdir: "real", wantRed: false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			initGit(t, dir)
			src := filepath.Join(evalRoot, tc.subdir, "SECURITY.md")
			body, err := os.ReadFile(src)
			if err != nil {
				t.Fatal(err)
			}
			mustWrite(t, filepath.Join(dir, "SECURITY.md"), string(body))
			mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), realSecurityTxt)
			mustWrite(t, filepath.Join(dir, "README.md"), "# Honesty eval fixture\n")
			if tc.subdir == "token-only" {
				mustWrite(t, filepath.Join(dir, "package.json"), `{"name":"acme-widget","version":"1.0.0"}`+"\n")
			}

			res, err := validate.Run(validate.Options{
				RepoRoot: dir,
				PackIDs:  []string{"house-policy"},
				Quiet:    true,
			})
			if err != nil {
				t.Fatal(err)
			}
			if tc.wantRed {
				if res.Passed {
					t.Fatalf("%s write-up must stay red", tc.name)
				}
				if !hasScaffoldOverlap(res, "HOUSE-ANTI-PLACEHOLDER", "SECURITY.md") {
					t.Fatalf("%s: expected scaffold overlap, got %#v", tc.name, res.Payload.Failures)
				}
				return
			}
			if !res.Passed {
				t.Fatalf("real write-up must pass, failures=%v", res.Payload.Failures)
			}
		})
	}
}

func hasScaffoldOverlap(res validate.Result, gateID, file string) bool {
	for _, f := range res.Payload.Failures {
		if f.GateID == gateID &&
			strings.Contains(f.SanitizedDescription, "scaffold body overlap") &&
			(f.ASTCoordinates.TargetFile == file || strings.HasSuffix(f.ASTCoordinates.TargetFile, file)) {
			return true
		}
	}
	return false
}

func collapseEval(s string) string {
	return strings.Join(strings.Fields(s), " ")
}

const realSecurityTxt = `Contact: mailto:security@example.com
Expires: 2028-01-15T00:00:00.000Z
Preferred-Languages: en
`

func TestArt14PathMissingFails(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodCRA(t, dir)
	if err := os.RemoveAll(filepath.Join(dir, "docs/incident")); err != nil {
		t.Fatal(err)
	}

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"cra-baseline"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("missing Art 14 rehearsal file must fail cra-baseline")
	}
	found := false
	for _, f := range res.Payload.Failures {
		if f.GateID == "CRA-ART14-PATH" {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected CRA-ART14-PATH, got %#v", res.Payload.Failures)
	}
}

func TestArt14PathUntouchedStubFailsOverlap(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodCRA(t, dir)
	mustWrite(t, filepath.Join(dir, "docs/incident/art14-path.md"), packs.DefaultScaffoldBody("docs/incident/art14-path.md"))

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"cra-baseline"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("untouched Art 14 stub must fail anti_placeholder")
	}
	if !hasScaffoldOverlap(res, "CRA-ANTI-PLACEHOLDER", "docs/incident/art14-path.md") {
		t.Fatalf("expected CRA-ANTI-PLACEHOLDER scaffold overlap on art14-path.md, got %#v", res.Payload.Failures)
	}
}

func TestArt14PathNotInHousePolicy(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodHouse(t, dir)

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Passed {
		t.Fatalf("house-policy must not require Art 14 path, failures=%v", res.Payload.Failures)
	}
	for _, f := range res.Payload.Failures {
		if f.GateID == "CRA-ART14-PATH" {
			t.Fatal("house-policy must not emit CRA-ART14-PATH")
		}
	}
}

func TestSessionNotesDoNotAffectCheckPassFail(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	writeGoodHouse(t, dir)

	baseline, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}

	seedPath := filepath.Join(dir, ".github", "curbpack", "cache", "pathway-seed.json")
	mustWrite(t, seedPath, `{
  "schema_version": 1,
  "answers": {"product":"hygiene","eu_docs":"no","medtech":"no","sector":"none","house_first":"yes","ce_context":"none"},
  "proposed_packs": ["house-policy"],
  "human_ticks": {"packs_confirmed": false, "prose_owned": false, "share_reviewed": false},
  "session_notes": ["ignore this for gates", "product prefers short SECURITY.md"],
  "corrections": {"product_name": "Acme"},
  "last_draft_pick": "A",
  "claim": "Prepares evidence for human review — not a conformity assessment."
}
`)

	withNotes, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if baseline.Passed != withNotes.Passed {
		t.Fatalf("pass/fail diverged: baseline=%v withNotes=%v", baseline.Passed, withNotes.Passed)
	}
	if len(baseline.Payload.Failures) != len(withNotes.Payload.Failures) {
		t.Fatalf("failure count diverged: %d vs %d", len(baseline.Payload.Failures), len(withNotes.Payload.Failures))
	}
	for i := range baseline.Payload.Failures {
		if baseline.Payload.Failures[i].GateID != withNotes.Payload.Failures[i].GateID {
			t.Fatalf("gate ids diverged at %d: %q vs %q", i, baseline.Payload.Failures[i].GateID, withNotes.Payload.Failures[i].GateID)
		}
	}
}

func writeGoodHouse(t *testing.T, dir string) {
	t.Helper()
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), `# Security

## Reporting

Email security@example.com with vulnerability details for coordinated disclosure.

## Response

We acknowledge within two business days and coordinate responsible disclosure timelines carefully.
`)
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), `Contact: mailto:security@example.com
Expires: 2028-01-15T00:00:00.000Z
Preferred-Languages: en
`)
	mustWrite(t, filepath.Join(dir, "README.md"), "# Contoso Gateway\n\nProduct overview for operators.\n")
}

func writeGoodCRA(t *testing.T, dir string) {
	t.Helper()
	mustWrite(t, filepath.Join(dir, "package.json"), `{"name":"contoso-gateway","version":"1.0.0","dependencies":{}}`+"\n")
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/risk_assessment.md"), `# Risk Assessment

## Product Overview

The contoso-gateway product forwards telemetry from clinical devices to a hospital EHR over mutually authenticated TLS.

## Identified Risks

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R-001   | Credential stuffing on admin UI | High | MFA + lockout |

## Residual Risk Statement

Residual risk is accepted by the product owner after mitigations above.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/support_period.md"), `# Support Period

## End of Support

Security updates for contoso-gateway are provided for five years from the general availability date of each major release.

## Rationale

Aligned with expected clinical deployment lifetime and spare-parts availability.
`)
	mustWrite(t, filepath.Join(dir, "docs/annex-vii/user_manual_security.md"), `# User Manual — Security

## Secure Configuration

Disable default accounts on contoso-gateway, enforce MFA, and restrict management interfaces to the hospital VLAN.

## Product Disposal

Factory-reset the appliance, shred exported key material, and confirm cloud tenant deletion.
`)
	mustWrite(t, filepath.Join(dir, "docs/incident/art14-path.md"), art14GoodBody)
}

const art14GoodBody = `# Art 14 reporting path

## Reporting clock (CRA Art 14)

For contoso-gateway, actively exploited or severe incidents are reported by the on-call owner using the in-repo rehearsal dated 2026-04-12. This is a file record for CRA Article 14 reporting (clock from 11 September 2026, including products already on the market). It is not a live Single Reporting Platform check and does not assert that EU Login works.

## Handling clock (not this file)

Vulnerability handling and public security contact for contoso-gateway are documented separately. They sit on a later clock than Article 14 reporting and are not this rehearsal.

## Named owner

Product security on-call for contoso-gateway owns the reporting path. Escalation is the engineering manager of record in SECURITY.md.

## Rehearsal dated artifact

Last tabletop: 2026-04-12. Record: this file plus the incident mail template under docs/incident/ (in-repo). Not a live submission.
`

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
