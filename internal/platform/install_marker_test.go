package platform

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestReadMarkerStripsBOM(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("CURBPACK_INSTALL_DIR", dir)
	path := filepath.Join(dir, "install-marker.json")
	payload := append([]byte{0xEF, 0xBB, 0xBF}, []byte(`{
  "schema": "curbpack-install-marker:1",
  "version": "v0.5.2",
  "install_dir": "`+filepath.ToSlash(dir)+`",
  "binary": "curbpack",
  "installed_at": "2026-08-12T00:00:00Z",
  "goos": "test"
}
`)...)
	if err := os.WriteFile(path, payload, 0o644); err != nil {
		t.Fatal(err)
	}
	m, err := ReadMarker()
	if err != nil {
		t.Fatalf("ReadMarker: %v", err)
	}
	if m.Schema != MarkerSchema || m.Version != "v0.5.2" {
		t.Fatalf("unexpected marker: %+v", m)
	}
}

func TestReadMarkerCustomInstallDir(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("CURBPACK_INSTALL_DIR", dir)
	if err := WriteMarker("v0.5.2", dir, filepath.Join(dir, BinaryName())); err != nil {
		t.Fatal(err)
	}
	m, err := ReadMarker()
	if err != nil {
		t.Fatalf("ReadMarker: %v", err)
	}
	if m.InstallDir != dir {
		t.Fatalf("install_dir=%q want %q", m.InstallDir, dir)
	}
	// Round-trip JSON must not include a BOM when we write via Go.
	b, err := os.ReadFile(filepath.Join(dir, "install-marker.json"))
	if err != nil {
		t.Fatal(err)
	}
	if len(b) >= 3 && b[0] == 0xEF && b[1] == 0xBB && b[2] == 0xBF {
		t.Fatal("WriteMarker must not emit UTF-8 BOM")
	}
	var raw map[string]any
	if err := json.Unmarshal(b, &raw); err != nil {
		t.Fatal(err)
	}
}

func TestDefaultInstallDirRespectsEnv(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("CURBPACK_INSTALL_DIR", dir)
	got, err := DefaultInstallDir()
	if err != nil {
		t.Fatal(err)
	}
	if got != dir {
		t.Fatalf("DefaultInstallDir=%q want %q", got, dir)
	}
}
