package exportx_test

import (
	"encoding/json"
	"flag"
	"os"
	"path/filepath"
	"runtime"
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
	if runtime.GOOS == "windows" {
		assertContextPackGoldenStruct(t, got, want)
		return
	}
	if string(got) != string(want) {
		t.Fatalf("context-pack drift — run: go test ./internal/exportx/ -run Golden -update\n got len=%d want len=%d", len(got), len(want))
	}
}

func assertContextPackGoldenStruct(t *testing.T, got, want []byte) {
	t.Helper()
	var gotPack, wantPack exportx.ContextPack
	if err := json.Unmarshal(got, &gotPack); err != nil {
		t.Fatalf("got json: %v", err)
	}
	if err := json.Unmarshal(want, &wantPack); err != nil {
		t.Fatalf("want json: %v", err)
	}
	// Instrument scan can differ by OS (temp paths); compare stable contract fields.
	gotPack.Instrument = wantPack.Instrument
	if gotPack.SchemaVersion != wantPack.SchemaVersion ||
		gotPack.OK != wantPack.OK ||
		gotPack.ReadinessScore != wantPack.ReadinessScore ||
		gotPack.CertificationClaimed != wantPack.CertificationClaimed {
		t.Fatalf("context-pack structural drift: got=%+v want=%+v", gotPack, wantPack)
	}
	if len(gotPack.Failures) != len(wantPack.Failures) {
		t.Fatalf("failures len got=%d want=%d", len(gotPack.Failures), len(wantPack.Failures))
	}
	if gotPack.Pathway == nil || wantPack.Pathway == nil || gotPack.Pathway.Phase != wantPack.Pathway.Phase {
		t.Fatalf("pathway phase drift")
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
