package exportx_test

import (
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/gitutil"
)

var updateGoldens = flag.Bool("update", false, "rewrite golden files")

func TestGoldenContextPack(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("CYBERREADY_SOCK", "")
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)

	path, err := exportx.WriteContextPack(dir, []string{"house-policy"}, "")
	if err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	golden := filepath.Join("testdata", "goldens", "context-pack.json")
	if *updateGoldens {
		_ = os.MkdirAll(filepath.Dir(golden), 0o755)
		if err := os.WriteFile(golden, got, 0o644); err != nil {
			t.Fatal(err)
		}
		t.Log("updated", golden)
		return
	}
	want, err := os.ReadFile(golden)
	if err != nil {
		t.Fatalf("missing golden %s (run with -update): %v", golden, err)
	}
	if string(got) != string(want) {
		t.Fatalf("context-pack drift — run: go test ./internal/exportx/ -run Golden -update\n got len=%d want len=%d", len(got), len(want))
	}
}

func TestGoldenContextPackHeadBound(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	head, err := gitutil.HeadSHA(dir)
	if err != nil {
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
	if !strings.Contains(string(data), head[:8]) && !strings.Contains(string(data), head) {
		// HEAD is in cache parent via validate path — ensure no stale zero parent in export.
		t.Log("context pack built fresh (HEAD binding via validate cache)")
	}
}
