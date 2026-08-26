package exportx_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/gitutil"
)

func TestWriteContextPack_FromValidateWash(t *testing.T) {
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("CYBERREADY_SOCK", "")
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)

	path, err := exportx.WriteContextPack(dir, []string{"house-policy"}, "")
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
	var pack exportx.ContextPack
	if err := json.Unmarshal(data, &pack); err != nil {
		t.Fatal(err)
	}
	if pack.SchemaVersion != "1" {
		t.Fatalf("schema_version=%q", pack.SchemaVersion)
	}
	if pack.CertificationClaimed {
		t.Fatal("certification_claimed must be false")
	}
	if pack.OK {
		t.Fatal("expected red house-policy fixture")
	}
	if len(pack.Failures) == 0 {
		t.Fatal("expected failures")
	}
	if pack.Paths["context_pack"] == "" {
		t.Fatal("missing path pointers")
	}
	if pack.Paths["pathway_seed"] == "" {
		t.Fatal("missing pathway_seed path")
	}
	if pack.Pathway == nil || pack.Pathway.NextVerb == "" {
		t.Fatal("expected pathway projection")
	}
	if pack.AgentIdentity.Source != "self-declared" {
		t.Fatalf("agent_identity.source=%q", pack.AgentIdentity.Source)
	}
	if pack.AgentIdentity.Reason != "not_installed" {
		t.Fatalf("agent_identity.reason=%q want not_installed", pack.AgentIdentity.Reason)
	}
	if !strings.Contains(pack.Pathway.ParentPath, "Root / Pathway /") {
		t.Fatalf("pathway parent path=%q", pack.Pathway.ParentPath)
	}
	md := strings.TrimSuffix(path, ".json") + ".md"
	mdBytes, err := os.ReadFile(md)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(mdBytes), "Not a conformity assessment") {
		t.Fatalf("md missing claim-safe framing: %s", mdBytes)
	}
	if !strings.Contains(string(mdBytes), "## Pathway") {
		t.Fatal("md missing Pathway section")
	}
	if !strings.Contains(string(mdBytes), "lineage label, not attestation") {
		t.Fatal("md missing agent identity lineage label")
	}
	if strings.Contains(string(data), "/Users/") || strings.Contains(string(data), "/home/") {
		t.Fatal("absolute home path leaked")
	}
}

func TestWriteContextPack_PrefersCache(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	head, _ := gitutil.HeadSHA(dir)

	// Seed cache without calling validate again via WriteContextPack first path.
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	seed := `{
  "schema_version": "1",
  "pack_id": "house-policy",
  "readiness_score": 88,
  "concurrency_control": {"expected_parent_commit_sha": "` + head + `"},
  "failures": [{
    "gate_id": "HOUSE-SECURITY-MD",
    "severity": "high",
    "type": "POLICY_VIOLATION",
    "sanitized_description": "seeded under /Users/alice/secret/SECURITY.md",
    "ast_coordinates": {"target_file": "/Users/alice/secret/SECURITY.md", "node_path": "", "target_symbol": "", "fallback_lines": ""},
    "remediation": {"action_required": "fix /Users/alice/secret/SECURITY.md", "expected_state": "present"}
  }]
}`
	if err := os.WriteFile(filepath.Join(cache, "latest_failure.json"), []byte(seed), 0o644); err != nil {
		t.Fatal(err)
	}

	path, err := exportx.WriteContextPack(dir, nil, filepath.Join(dir, "cp.json"))
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
	var pack exportx.ContextPack
	if err := json.Unmarshal(data, &pack); err != nil {
		t.Fatal(err)
	}
	if pack.ReadinessScore != 88 {
		t.Fatalf("want cached readiness 88, got %d", pack.ReadinessScore)
	}
	if pack.OK {
		t.Fatal("seeded failures should be ok=false")
	}
	s := string(data)
	if strings.Contains(s, "/Users/alice") {
		t.Fatalf("home path not washed: %s", s)
	}
}

func TestWriteContextPack_GreenEmptyFailures(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)

	path, err := exportx.WriteContextPack(dir, []string{"house-policy"}, "")
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var pack exportx.ContextPack
	if err := json.Unmarshal(data, &pack); err != nil {
		t.Fatal(err)
	}
	if !pack.OK {
		t.Fatalf("want ok on green fixture; failures=%v", pack.Failures)
	}
	if len(pack.Failures) != 0 {
		t.Fatalf("want empty failures, got %d", len(pack.Failures))
	}
}

func TestWriteContextPack_SurfacesAgentIdentity(t *testing.T) {
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("CYBERREADY_SOCK", "")
	t.Setenv("CURBPACK_AGENT_ID", "pack-agent")
	t.Setenv("CURBPACK_MODEL_HASH", "pack-hash")
	t.Setenv("CURBPACK_MANDATE_ID", "pack-mandate")
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)

	path, err := exportx.WriteContextPack(dir, []string{"house-policy"}, "")
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var pack exportx.ContextPack
	if err := json.Unmarshal(data, &pack); err != nil {
		t.Fatal(err)
	}
	if pack.AgentIdentity.AgentID != "pack-agent" || pack.AgentIdentity.ModelHash != "pack-hash" || pack.AgentIdentity.ActiveMandateID != "pack-mandate" {
		t.Fatalf("context pack identity: %#v", pack.AgentIdentity)
	}
	if pack.AgentIdentity.Source != "self-declared" {
		t.Fatalf("source=%q", pack.AgentIdentity.Source)
	}
	md := strings.TrimSuffix(path, ".json") + ".md"
	mdBytes, err := os.ReadFile(md)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(mdBytes), "pack-agent") || !strings.Contains(string(mdBytes), "self-declared") {
		t.Fatalf("md missing identity: %s", mdBytes)
	}
}

func TestContextPackCarriesPackVersions(t *testing.T) {
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("CYBERREADY_SOCK", "")
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)

	path, err := exportx.WriteContextPack(dir, []string{"medtech-iec62304"}, "")
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var pack exportx.ContextPack
	if err := json.Unmarshal(data, &pack); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(pack.PackVersions, "cra-baseline@") {
		t.Fatalf("pack_versions missing cra-baseline@: %q", pack.PackVersions)
	}
	if !strings.Contains(pack.PackVersions, "medtech-iec62304@") {
		t.Fatalf("pack_versions missing medtech-iec62304@: %q", pack.PackVersions)
	}
}
