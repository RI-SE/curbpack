package sbom_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/sbom"
)

func TestCollectPackagesStableOrder(t *testing.T) {
	dir := t.TempDir()
	lock := filepath.Join(dir, "package-lock.json")
	body := `{
  "name": "demo",
  "lockfileVersion": 3,
  "packages": {
    "": { "name": "demo" },
    "node_modules/zod": { "version": "3.22.0" },
    "node_modules/axios": { "version": "1.6.0" },
    "node_modules/lodash": { "version": "4.17.21" }
  }
}`
	if err := os.WriteFile(lock, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	first, _, err := sbom.CollectPackages(dir)
	if err != nil {
		t.Fatal(err)
	}
	second, _, err := sbom.CollectPackages(dir)
	if err != nil {
		t.Fatal(err)
	}
	for i := range first {
		if first[i] != second[i] {
			t.Fatalf("order drift at %d: %+v vs %+v", i, first[i], second[i])
		}
	}
}

func TestBuildCycloneDXStableBytes(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	dir := t.TempDir()
	lock := filepath.Join(dir, "package-lock.json")
	body := `{
  "name": "demo",
  "lockfileVersion": 3,
  "packages": {
    "": { "name": "demo" },
    "node_modules/axios": { "version": "1.6.0" },
    "node_modules/lodash": { "version": "4.17.21" }
  }
}`
	if err := os.WriteFile(lock, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	pkgs, source, err := sbom.CollectPackages(dir)
	if err != nil {
		t.Fatal(err)
	}
	docA := sbom.BuildCycloneDX(dir, pkgs, source)
	docB := sbom.BuildCycloneDX(dir, pkgs, source)
	bA, _ := json.Marshal(docA)
	bB, _ := json.Marshal(docB)
	if string(bA) != string(bB) {
		t.Fatal("cyclonedx marshal not byte-stable")
	}
	out := filepath.Join(dir, "sbom.cdx.json")
	_, path1, err := sbom.WriteCycloneDX(dir, out)
	if err != nil {
		t.Fatal(err)
	}
	data1, _ := os.ReadFile(path1)
	_, _, err = sbom.WriteCycloneDX(dir, out)
	if err != nil {
		t.Fatal(err)
	}
	data2, _ := os.ReadFile(path1)
	if string(data1) != string(data2) {
		t.Fatal("cyclonedx write not byte-stable")
	}
}
