package contract_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/attest"
	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/release"
	"github.com/afelin/cyberready/internal/sbom"
	"github.com/afelin/cyberready/internal/sock"
	"github.com/afelin/cyberready/internal/validate"
)

func TestGateIDSetsEqualCheckValidateSock(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)

	checkRes, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	validateRes, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	sockRes := sock.ValidateDelta(dir)

	a := sortedGateIDs(checkRes.Payload.Failures)
	b := sortedGateIDs(validateRes.Payload.Failures)
	c := sortedGateIDs(sockRes.Failures)
	if strings.Join(a, ",") != strings.Join(b, ",") {
		t.Fatalf("check≠validate gate_ids: %v vs %v", a, b)
	}
	if strings.Join(a, ",") != strings.Join(c, ",") {
		t.Fatalf("check≠sock gate_ids: %v vs %v", a, c)
	}
	if sockRes.Payload == nil {
		t.Fatal("sock payload nil")
	}
	d := sortedGateIDs(sockRes.Payload.Failures)
	if strings.Join(a, ",") != strings.Join(d, ",") {
		t.Fatal("sock payload gate_ids diverge")
	}
}

func TestSBOMDigestPrepareReleaseMatchesAttestBind(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	mustWrite(t, filepath.Join(dir, "package.json"), `{"name":"demo","dependencies":{"left-pad":"1.3.0"}}`+"\n")

	if err := release.Prepare(release.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, AllowFailingGates: true}); err != nil {
		t.Fatal(err)
	}
	sbomPath := filepath.Join(dir, ".github/cyberready/evidence/sbom.cdx.json")
	d1 := sbom.FileDigest(sbomPath)
	if d1 == "" {
		t.Fatal("missing sbom digest after prepare-release")
	}
	cap, err := attest.Run(attest.Options{RepoRoot: dir, AllowDirty: true, SBOMDigest: d1})
	if err != nil {
		t.Fatal(err)
	}
	if cap.Evidence["sbom_digest"] != d1 {
		t.Fatalf("attest sbom_digest=%q want %q", cap.Evidence["sbom_digest"], d1)
	}
	seed := attest.StateSeed(cap.CommitSHA, cap.ParentStateHash, d1, cap.Evidence["vex_digest"])
	if !strings.Contains(seed, "sbom="+d1) {
		t.Fatalf("seed missing sbom digest: %s", seed)
	}
}

func TestJSONSchemaVersionPresent(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	b, err := json.Marshal(res.Payload)
	if err != nil {
		t.Fatal(err)
	}
	var m map[string]any
	if err := json.Unmarshal(b, &m); err != nil {
		t.Fatal(err)
	}
	sv, _ := m["schema_version"].(string)
	if sv == "" {
		t.Fatalf("schema_version missing: %s", b)
	}
}

// --diff must not false-green when required files are missing / failing but untouched in porcelain.
func TestDiffOnlyStillFailsMissingSecurityMD(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)
	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	run("git", "add", "-A")
	run("git", "commit", "-m", "base", "-q")
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\ntouched\n")

	diffRes, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, DiffOnly: true, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	fullRes, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, DiffOnly: false, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if diffRes.Passed {
		t.Fatal("--diff must not pass when SECURITY.md is missing")
	}
	if fullRes.Passed {
		t.Fatal("full scan should fail")
	}
	found := false
	for _, f := range diffRes.Payload.Failures {
		if f.GateID == "HOUSE-SECURITY-MD" {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected HOUSE-SECURITY-MD under --diff, got %#v", diffRes.Payload.Failures)
	}
}

func sortedGateIDs(fs []ir.Failure) []string {
	out := make([]string, 0, len(fs))
	for _, f := range fs {
		out = append(out, f.GateID)
	}
	sort.Strings(out)
	return out
}

func mustRealGit(t *testing.T, dir string) {
	t.Helper()
	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	run("git", "init", "-q")
	run("git", "config", "user.email", "contract@cyberready.local")
	run("git", "config", "user.name", "Contract")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
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

func writeMinimalHouseFail(t *testing.T, dir string) {
	t.Helper()
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	// SECURITY.md missing → HOUSE-SECURITY-MD failure
}

func writeGoodHouse(t *testing.T, dir string) {
	t.Helper()
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), `# Security Policy

## Reporting

Report vulnerabilities to security@example.com with reproduction steps.

## Supported Versions

We support the latest major release with security patches for twelve months.

## Disclosure

Coordinated disclosure within 90 days after fix availability.
`+strings.Repeat("word ", 40)+"\n")
}
