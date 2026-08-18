package workflowdata_test

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/workflowdata"
)

func TestEmbedMatchesExample(t *testing.T) {
	_, thisFile, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	root := filepath.Clean(filepath.Join(filepath.Dir(thisFile), "..", ".."))
	example := filepath.Join(root, "examples", "workflows", "curbpack-check.yml")
	if err := workflowdata.MustMatchExample(example); err != nil {
		t.Fatal(err)
	}
}

func TestInstallOnlyIfMissing(t *testing.T) {
	dir := t.TempDir()
	dest, created, err := workflowdata.Install(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !created {
		t.Fatal("expected create")
	}
	if dest != filepath.Join(dir, filepath.FromSlash(workflowdata.DestRel)) {
		t.Fatalf("dest=%s", dest)
	}
	body, err := os.ReadFile(dest)
	if err != nil {
		t.Fatal(err)
	}
	if string(body) != string(workflowdata.Bytes()) {
		t.Fatal("written body != embed")
	}
	if !strings.Contains(string(body), "Never set CURBPACK_ALLOW_CONFIRM=1 on the Action") {
		t.Fatal("workflow example must warn never set ALLOW_CONFIRM=1 on the Action")
	}
	if !strings.Contains(string(body), "Compose Trivy/Gitleaks") {
		t.Fatal("workflow example must tell adopters to compose Trivy/Gitleaks beside check")
	}

	// Second call must not overwrite.
	marker := []byte("# keep me\n")
	if err := os.WriteFile(dest, marker, 0o644); err != nil {
		t.Fatal(err)
	}
	_, created2, err := workflowdata.Install(dir)
	if err != nil {
		t.Fatal(err)
	}
	if created2 {
		t.Fatal("must not recreate existing workflow")
	}
	got, _ := os.ReadFile(dest)
	if string(got) != string(marker) {
		t.Fatal("existing workflow was overwritten")
	}
}
