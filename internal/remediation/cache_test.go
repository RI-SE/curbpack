package remediation_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/cyberready/internal/remediation"
)

func TestCacheRoundTrip(t *testing.T) {
	dir := t.TempDir()
	c := remediation.Cache{Version: 1, Entries: map[string]remediation.Entry{}}
	remediation.Upsert(&c, remediation.Entry{
		GateID:  "HOUSE-SECURITY-MD",
		File:    "SECURITY.md",
		Snippet: "# Security\n\nReporting details for coordinated disclosure process here.\n",
		Action:  "Add SECURITY.md",
	})
	if err := remediation.Save(dir, c); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, ".github", "cyberready", "cache", "remediations.json")
	if _, err := os.Stat(path); err != nil {
		t.Fatal(err)
	}
	got, err := remediation.Load(dir)
	if err != nil {
		t.Fatal(err)
	}
	e, ok := remediation.Lookup(got, "HOUSE-SECURITY-MD")
	if !ok || e.File != "SECURITY.md" || e.Snippet == "" {
		t.Fatalf("lookup: %+v ok=%v", e, ok)
	}
}

func TestLoadMissing(t *testing.T) {
	c, err := remediation.Load(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if len(c.Entries) != 0 {
		t.Fatalf("want empty, got %+v", c.Entries)
	}
}
