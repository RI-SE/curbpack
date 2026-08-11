package paths

import (
	"os"
	"path/filepath"
	"testing"
)

func TestConfigDualReadWriteNew(t *testing.T) {
	root := t.TempDir()
	legacy := filepath.Join(root, LegacyConfigFile)
	if err := os.WriteFile(legacy, []byte(`{"packs":["house-policy"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	got := ResolveConfigPath(root)
	if got != legacy {
		t.Fatalf("expected legacy config, got %s", got)
	}
	neu := ConfigPath(root)
	if err := os.WriteFile(neu, []byte(`{"packs":["cra-baseline"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	got = ResolveConfigPath(root)
	if got != neu {
		t.Fatalf("expected new config to win, got %s", got)
	}
}

func TestCacheDualReadWriteNew(t *testing.T) {
	root := t.TempDir()
	legacyCache := filepath.Join(root, filepath.FromSlash(LegacyCacheRel))
	if err := os.MkdirAll(legacyCache, 0o755); err != nil {
		t.Fatal(err)
	}
	legacyFile := filepath.Join(legacyCache, "latest_failure.json")
	if err := os.WriteFile(legacyFile, []byte(`{}`), 0o644); err != nil {
		t.Fatal(err)
	}
	if got := ResolveUnderCache(root, "latest_failure.json"); got != legacyFile {
		t.Fatalf("expected legacy cache file, got %s", got)
	}
	writeDir := CacheDir(root)
	if err := os.MkdirAll(writeDir, 0o755); err != nil {
		t.Fatal(err)
	}
	neuFile := filepath.Join(writeDir, "latest_failure.json")
	if err := os.WriteFile(neuFile, []byte(`{"ok":true}`), 0o644); err != nil {
		t.Fatal(err)
	}
	if got := ResolveUnderCache(root, "latest_failure.json"); got != neuFile {
		t.Fatalf("expected new cache file to win, got %s", got)
	}
}

func TestEnvPreferNew(t *testing.T) {
	t.Setenv("CURBPACK_SOCK", "/tmp/curb.sock")
	t.Setenv("CYBERREADY_SOCK", "/tmp/legacy.sock")
	if got := Env("SOCK"); got != "/tmp/curb.sock" {
		t.Fatalf("Env SOCK: got %q", got)
	}
	t.Setenv("CURBPACK_SOCK", "")
	if got := Env("SOCK"); got != "/tmp/legacy.sock" {
		t.Fatalf("Env SOCK fallback: got %q", got)
	}
}
