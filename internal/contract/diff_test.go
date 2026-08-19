package contract_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/sbom"
	"github.com/afelin/curbpack/internal/validate"
)

func TestGateIDSetsEqualCheckValidate(t *testing.T) {
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

	a := sortedGateIDs(checkRes.Payload.Failures)
	b := sortedGateIDs(validateRes.Payload.Failures)
	if strings.Join(a, ",") != strings.Join(b, ",") {
		t.Fatalf("check≠validate gate_ids: %v vs %v", a, b)
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
	sbomPath := filepath.Join(dir, ".github/curbpack/evidence/sbom.cdx.json")
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
	want := attest.ComputeStateHash(cap.CommitSHA, cap.ParentStateHash, d1, cap.Evidence["vex_digest"], cap.Evidence["result_digest"], cap.Evidence["pack_ids"])
	if cap.StateHash != want {
		t.Fatalf("state_hash=%q want %q (ComputeStateHash sole authority)", cap.StateHash, want)
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

func TestSARIFRuleIDEqualsGateID(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)
	path, n, err := exportx.WriteSARIF(dir, []string{"house-policy"}, filepath.Join(dir, "out.sarif"))
	if err != nil {
		t.Fatal(err)
	}
	if n == 0 {
		t.Fatal("expected non-empty SARIF results on failure")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var doc exportx.SARIFDocument
	if err := json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	gates := map[string]bool{}
	for _, f := range res.Payload.Failures {
		gates[f.GateID] = true
	}
	for _, r := range doc.Runs[0].Results {
		if !gates[r.RuleID] {
			t.Fatalf("SARIF ruleId %q not in gate_ids", r.RuleID)
		}
	}
}

func TestExplainPacketAirlock(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)
	path, err := exportx.WriteExplainPacket(dir, []string{"house-policy"}, "")
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := exportx.PacketLooksAirlocked(data); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(data), "<untrusted_metadata>") {
		t.Fatal("missing untrusted_metadata wrapper")
	}
}

func TestAgentIdentityFromEnv(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("CYBERREADY_SOCK", "")
	t.Setenv("CURBPACK_AGENT_ID", "agent-x")
	t.Setenv("CURBPACK_MODEL_HASH", "hash-y")
	t.Setenv("CURBPACK_MANDATE_ID", "mandate-z")
	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	id := res.Payload.AgentIdentity
	if id.AgentID != "agent-x" || id.ModelHash != "hash-y" || id.ActiveMandateID != "mandate-z" {
		t.Fatalf("agent identity env not applied: %#v", id)
	}
	if id.Source != ir.SourceSelfDeclared {
		t.Fatalf("source=%q want self-declared", id.Source)
	}
	if id.Reason != ir.ReasonNotInstalled {
		t.Fatalf("reason=%q want not_installed (fail-open)", id.Reason)
	}
}

func TestAgentIdentitySockFailOpenDoesNotFailCheck(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	t.Setenv("CURBPACK_SOCK", filepath.Join(dir, "absent.sock"))
	t.Setenv("CYBERREADY_SOCK", "")
	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Passed {
		t.Fatalf("missing sock must fail-open, not fail check: %#v", res.Payload.Failures)
	}
	if res.Payload.AgentIdentity.Source != ir.SourceSelfDeclared {
		t.Fatalf("source=%q", res.Payload.AgentIdentity.Source)
	}
	if res.Payload.AgentIdentity.Reason != ir.ReasonUnavailable {
		t.Fatalf("reason=%q want unavailable", res.Payload.AgentIdentity.Reason)
	}
}

func TestAgentIdentityBridgeWhenSockPresent(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	sockPath := filepath.Join(dir, "curbpack.sock")
	mustWrite(t, sockPath, "")
	t.Setenv("CURBPACK_SOCK", sockPath)
	t.Setenv("CYBERREADY_SOCK", "")
	t.Setenv("CURBPACK_AGENT_ID", "bridge-agent")
	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Passed {
		t.Fatalf("bridge label must not fail check: %#v", res.Payload.Failures)
	}
	id := res.Payload.AgentIdentity
	if id.Source != ir.SourceBridge || id.AgentID != "bridge-agent" || id.Reason != "" {
		t.Fatalf("want bridge from env+sock presence: %#v", id)
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

// --diff must not false-green when a committed heal stub is untouched and only README changed.
func TestDiffOnlyStillFailsScaffoldOverlap(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), packs.DefaultScaffoldBody("SECURITY.md"))
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
	run("git", "commit", "-m", "heal stub", "-q")
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\ntouched\n")

	diffRes, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, DiffOnly: true, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if diffRes.Passed {
		t.Fatal("--diff must not pass when committed SECURITY.md is still a heal stub")
	}
	found := false
	for _, f := range diffRes.Payload.Failures {
		if f.GateID == "HOUSE-ANTI-PLACEHOLDER" && strings.Contains(f.SanitizedDescription, "scaffold body overlap") {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected HOUSE-ANTI-PLACEHOLDER scaffold body overlap under --diff, got %#v", diffRes.Payload.Failures)
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
	run("git", "config", "user.email", "contract@curbpack.local")
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
