package exportx_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/exportx"
)

func TestExplainCustomHomeIsRemovedBeforePublication(t *testing.T) {
	root := t.TempDir()
	mustRealGit(t, root)
	packs := t.TempDir()
	home := filepath.Join(t.TempDir(), "staff", "person")
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)
	t.Setenv("CURBPACK_PACKS_DIR", packs)
	pack := map[string]any{"id": "audit", "name": "Audit", "version": "1.0.0", "citations": []map[string]any{{"url": home + "/citation.md"}}, "rules": []map[string]any{{"id": "ONE", "check": "file_present", "path": "missing.txt", "severity": "high", "type": "POLICY_VIOLATION", "description": "See " + home + "/memo.txt", "remediation": "Read " + home + "/instructions.md"}}}
	b, err := json.Marshal(pack)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(packs, "audit"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(packs, "audit", "pack.json"), b, 0600); err != nil {
		t.Fatal(err)
	}
	path, err := exportx.WriteExplainPacket(root, []string{"audit"}, "")
	if err != nil {
		t.Fatal(err)
	}
	b, err = os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(b), home) {
		t.Fatal("custom home was published in explain packet")
	}
	if err := exportx.PacketLooksAirlocked(b); err != nil {
		t.Fatal(err)
	}
	var pkt exportx.ExplainPacket
	if err := json.Unmarshal(b, &pkt); err != nil {
		t.Fatal(err)
	}
	inner := strings.TrimSuffix(strings.TrimPrefix(pkt.Untrusted, "<untrusted_metadata>"), "</untrusted_metadata>")
	if !json.Valid([]byte(inner)) {
		t.Fatal("redaction broke embedded JSON")
	}
}
