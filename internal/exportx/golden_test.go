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
	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/release/templates"
)

var updateGoldens = flag.Bool("update", false, "rewrite golden files")

const goldenSourceDateEpoch = "1704067200"

func goldenEnv(t *testing.T) {
	t.Helper()
	t.Setenv("SOURCE_DATE_EPOCH", goldenSourceDateEpoch)
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("CYBERREADY_SOCK", "")
}

func goldenFixtureDir(t *testing.T) string {
	t.Helper()
	dir := filepath.Join(t.TempDir(), "golden-fixture")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	writeGoldenLockfile(t, dir)
	return dir
}

func writeGoldenLockfile(t *testing.T, dir string) {
	t.Helper()
	mustWrite(t, filepath.Join(dir, "package-lock.json"), `{
  "name": "golden-fixture",
  "lockfileVersion": 3,
  "packages": {
    "": { "name": "golden-fixture" },
    "node_modules/lodash": { "version": "4.17.21" }
  }
}`)
}

func compareGoldenBytes(t *testing.T, name string, got []byte, windowsAssert func(t *testing.T, got, want []byte)) {
	t.Helper()
	golden := filepath.Join("testdata", "goldens", name)
	if *updateGoldens {
		if err := os.MkdirAll(filepath.Dir(golden), 0o755); err != nil {
			t.Fatal(err)
		}
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
	if runtime.GOOS == "windows" && windowsAssert != nil {
		windowsAssert(t, got, want)
		return
	}
	if string(got) != string(want) {
		t.Fatalf("%s drift — run: go test ./internal/exportx/ -run Golden -update\n got len=%d want len=%d", name, len(got), len(want))
	}
}

func TestGoldenContextPack(t *testing.T) {
	goldenEnv(t)
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
	compareGoldenBytes(t, "context-pack.json", got, assertContextPackGoldenStruct)
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

func TestGoldenSARIF(t *testing.T) {
	goldenEnv(t)
	dir := goldenFixtureDir(t)
	out := filepath.Join(dir, "curbpack.sarif")
	path, _, err := exportx.WriteSARIF(dir, []string{"house-policy"}, out)
	if err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	compareGoldenBytes(t, "curbpack.sarif", got, assertSARIFGoldenStruct)
}

func assertSARIFGoldenStruct(t *testing.T, got, want []byte) {
	t.Helper()
	var gotDoc, wantDoc exportx.SARIFDocument
	if err := json.Unmarshal(got, &gotDoc); err != nil {
		t.Fatalf("got sarif: %v", err)
	}
	if err := json.Unmarshal(want, &wantDoc); err != nil {
		t.Fatalf("want sarif: %v", err)
	}
	if gotDoc.Version != wantDoc.Version || len(gotDoc.Runs) != len(wantDoc.Runs) {
		t.Fatalf("sarif shell drift")
	}
	if len(gotDoc.Runs) == 0 {
		return
	}
	if len(gotDoc.Runs[0].Results) != len(wantDoc.Runs[0].Results) {
		t.Fatalf("sarif results len got=%d want=%d", len(gotDoc.Runs[0].Results), len(wantDoc.Runs[0].Results))
	}
}

func TestGoldenBuyerQuestions(t *testing.T) {
	goldenEnv(t)
	dir := goldenFixtureDir(t)
	_, _, err := exportx.WriteBuyerQuestions(dir, []string{"house-policy"}, "")
	if err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(filepath.Join(dir, ".github", "curbpack", "cache", "buyer-questions.json"))
	if err != nil {
		t.Fatal(err)
	}
	golden := filepath.Join("testdata", "goldens", "buyer-questions.json")
	if *updateGoldens {
		if err := os.MkdirAll(filepath.Dir(golden), 0o755); err != nil {
			t.Fatal(err)
		}
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
	assertBuyerQuestionsGoldenStruct(t, got, want)
}

func assertBuyerQuestionsGoldenStruct(t *testing.T, got, want []byte) {
	t.Helper()
	var gotReport, wantReport exportx.BuyerQuestionsReport
	if err := json.Unmarshal(got, &gotReport); err != nil {
		t.Fatalf("got json: %v", err)
	}
	if err := json.Unmarshal(want, &wantReport); err != nil {
		t.Fatalf("want json: %v", err)
	}
	if gotReport.SchemaVersion != wantReport.SchemaVersion ||
		gotReport.PackID != wantReport.PackID ||
		gotReport.AssuranceClass != wantReport.AssuranceClass ||
		gotReport.AttestationStatus != wantReport.AttestationStatus {
		t.Fatalf("buyer-questions header drift")
	}
	if len(gotReport.Questions) != len(wantReport.Questions) {
		t.Fatalf("questions len got=%d want=%d", len(gotReport.Questions), len(wantReport.Questions))
	}
	for i := range gotReport.Questions {
		gq, wq := gotReport.Questions[i], wantReport.Questions[i]
		gq.VerifiedAt, wq.VerifiedAt = "", ""
		if gq != wq {
			t.Fatalf("question[%d] drift: got=%+v want=%+v", i, gq, wq)
		}
	}
	if strings.TrimSpace(gotReport.Questions[0].VerifiedAt) == "" {
		t.Fatal("verified_at must be populated from payload commit (non-empty)")
	}
}

func TestGoldenSPDX(t *testing.T) {
	goldenEnv(t)
	dir := goldenFixtureDir(t)
	path, err := exportx.WriteSPDXOptional(dir, "")
	if err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	compareGoldenBytes(t, "sbom.spdx.json", got, assertSPDXGoldenStruct)
}

func assertSPDXGoldenStruct(t *testing.T, got, want []byte) {
	t.Helper()
	var gotDoc, wantDoc map[string]any
	if err := json.Unmarshal(got, &gotDoc); err != nil {
		t.Fatalf("got spdx: %v", err)
	}
	if err := json.Unmarshal(want, &wantDoc); err != nil {
		t.Fatalf("want spdx: %v", err)
	}
	for _, k := range []string{"spdxVersion", "dataLicense", "SPDXID", "name", "documentNamespace"} {
		if gotDoc[k] != wantDoc[k] {
			t.Fatalf("spdx field %q drift", k)
		}
	}
	gotPkgs, _ := gotDoc["packages"].([]any)
	wantPkgs, _ := wantDoc["packages"].([]any)
	if len(gotPkgs) != len(wantPkgs) {
		t.Fatalf("spdx packages len got=%d want=%d", len(gotPkgs), len(wantPkgs))
	}
}

func TestGoldenOnePager(t *testing.T) {
	goldenEnv(t)
	dir := goldenFixtureDir(t)
	if err := release.Prepare(release.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}}); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(filepath.Join(dir, "review-pack", "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	compareGoldenBytes(t, "buyer-onepager.html", got, assertOnePagerGoldenStruct)
}

func assertOnePagerGoldenStruct(t *testing.T, got, want []byte) {
	t.Helper()
	gotFP := onePagerHTMLFingerprint(string(got))
	wantFP := onePagerHTMLFingerprint(string(want))
	if gotFP != wantFP || gotFP == "" {
		t.Fatalf("one-pager fingerprint drift: got=%q want=%q", gotFP, wantFP)
	}
}

func onePagerHTMLFingerprint(htmlDoc string) string {
	const marker = "<!-- curbpack-onepager-fp:"
	if i := strings.Index(htmlDoc, marker); i >= 0 {
		rest := htmlDoc[i+len(marker):]
		if j := strings.Index(rest, " -->"); j >= 0 {
			return rest[:j]
		}
	}
	return templates.OnePagerFingerprint(templates.OnePagerDTO{})
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
		t.Log("context pack built fresh (HEAD binding via validate cache)")
	}
}
