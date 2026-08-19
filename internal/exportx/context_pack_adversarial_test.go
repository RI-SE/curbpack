package exportx_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/ir"
)

func TestWriteContextPack_RejectsStaleCommitCache(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	head, _ := gitutil.HeadSHA(dir)

	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	stale := ir.GateFailurePayload{
		SchemaVersion:  ir.SchemaVersion,
		PackID:         "house-policy",
		ReadinessScore: 100,
		ConcurrencyControl: ir.ConcurrencyControl{
			ExpectedParentCommitSHA: "0000000000000000000000000000000000000000",
		},
	}
	raw, _ := json.Marshal(stale)
	if err := os.WriteFile(filepath.Join(cache, "latest_failure.json"), raw, 0o644); err != nil {
		t.Fatal(err)
	}

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
		t.Fatalf("stale commit cache must re-validate green fixture; head=%s", head)
	}
}

func TestWriteContextPack_RejectsCrossPackCache(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	head, _ := gitutil.HeadSHA(dir)

	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	stale := ir.GateFailurePayload{
		SchemaVersion:  ir.SchemaVersion,
		PackID:         "cra-baseline",
		ReadinessScore: 12,
		Failures: []ir.Failure{{
			GateID: "CRA-FAKE", Severity: "high", Type: "POLICY_VIOLATION",
			SanitizedDescription: "tampered cross-pack cache",
		}},
		ConcurrencyControl: ir.ConcurrencyControl{
			ExpectedParentCommitSHA: head,
		},
	}
	raw, _ := json.Marshal(stale)
	if err := os.WriteFile(filepath.Join(cache, "latest_failure.json"), raw, 0o644); err != nil {
		t.Fatal(err)
	}

	path, err := exportx.WriteContextPack(dir, []string{"house-policy"}, "")
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	s := string(data)
	if strings.Contains(s, "CRA-FAKE") || strings.Contains(s, "tampered cross-pack") {
		t.Fatalf("cross-pack stale cache must not be used: %s", s)
	}
}

func TestWriteContextPack_RejectsTamperedCachePackMismatch(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)
	head, _ := gitutil.HeadSHA(dir)

	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	// Green tampered cache for same pack but wrong commit — must re-validate red.
	stale := ir.GateFailurePayload{
		SchemaVersion:  ir.SchemaVersion,
		PackID:         "house-policy",
		ReadinessScore: 100,
		ConcurrencyControl: ir.ConcurrencyControl{
			ExpectedParentCommitSHA: "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
		},
	}
	raw, _ := json.Marshal(stale)
	if err := os.WriteFile(filepath.Join(cache, "latest_failure.json"), raw, 0o644); err != nil {
		t.Fatal(err)
	}

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
	if pack.OK {
		t.Fatalf("tampered green cache must re-validate; head=%s", head)
	}
}
