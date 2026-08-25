package review_test

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/review"
)

func TestReviewMinimalPack(t *testing.T) {
	dir := t.TempDir()
	payload := ir.GateFailurePayload{
		SchemaVersion:  "1",
		PackID:         "house-policy",
		ReadinessScore: 80,
		Failures: []ir.Failure{{
			GateID:   "HOUSE-SECURITY-MD",
			Severity: "high",
			Type:     "missing",
		}},
	}
	raw, _ := json.MarshalIndent(payload, "", "  ")
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), append(raw, '\n'))
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("# action\n\n`SECURITY.md` missing\n"))
	mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("# exec\n\nNot conformity assessment.\n"))
	digest := ir.ComputeResultDigest(payload)
	html := `<!DOCTYPE html><html><head>
<!-- curbpack-onepager-fp:abcdef0123456789 -->
</head><body>
<dl class="prov">
<dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>` + digest[:12] + `…</dd>
</dl>
<p>See https://example.com/docs for context.</p>
</body></html>`
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(html))

	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &buf})
	if err != nil {
		t.Fatal(err)
	}
	if rep.Schema != "curbpack-review-report:2" {
		t.Fatalf("schema: %s", rep.Schema)
	}
	if rep.ClassifierVersion != review.ClassifierVersion {
		t.Fatalf("classifier: %s", rep.ClassifierVersion)
	}
	if rep.ConfirmedCount == 0 {
		t.Fatalf("expected some confirmed findings, got %+v", rep)
	}
	if review.HasContradictions(rep) {
		t.Fatalf("expected no contradictions on minimal consistent pack: %+v", rep.Findings)
	}
	if rep.UnconfirmedGenuine != 1 {
		// SECURITY.md cited but not in bundle
		t.Fatalf("expected 1 genuine unresolved for SECURITY.md, got %d findings=%+v", rep.UnconfirmedGenuine, rep.Findings)
	}
	md := buf.String()
	if !strings.Contains(md, "Document triage only") {
		t.Fatalf("triage missing disclaimer: %s", md)
	}
	if !strings.Contains(md, "genuine unresolved") {
		t.Fatalf("terse output missing genuine line: %s", md)
	}
	banned := []string{"CRA-compliant", "CE marking", "notified-body approved", "we are certified"}
	for _, b := range banned {
		if strings.Contains(strings.ToLower(md), strings.ToLower(b)) {
			t.Fatalf("triage must not emit %q", b)
		}
	}
}

func TestReviewDeterminism(t *testing.T) {
	dir := writeMinimalConsistent(t)
	var a, b bytes.Buffer
	ra, err := review.Run(review.Options{BundleRoot: dir, Writer: &a, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	rb, err := review.Run(review.Options{BundleRoot: dir, Writer: &b, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	if a.String() != b.String() {
		t.Fatal("markdown not byte-identical across runs")
	}
	ja, _ := json.Marshal(ra)
	jb, _ := json.Marshal(rb)
	if !bytes.Equal(ja, jb) {
		t.Fatal("JSON report not byte-identical across runs")
	}
}

func TestReviewMissingRequiredContradicted(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), []byte(`{"schema_version":"1","pack_id":"house-policy","readiness_score":0}`+"\n"))
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &buf, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	if !review.HasContradictions(rep) {
		t.Fatal("missing required layers must contradict")
	}
}

func TestReviewDigestMismatch(t *testing.T) {
	dir := t.TempDir()
	payload := ir.GateFailurePayload{SchemaVersion: "1", PackID: "house-policy", ReadinessScore: 10}
	raw, _ := json.MarshalIndent(payload, "", "  ")
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), append(raw, '\n'))
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("ok\n"))
	mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("ok\n"))
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:deadbeefdeadbeef -->
<dl class="prov"><dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>000000000000…</dd></dl>`))
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, f := range rep.Findings {
		if f.ID == "digest:result-digest-match" && f.State == review.StateContradicted && f.Cause == review.CauseSelfDisagree {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected result_digest contradiction with self_disagree, findings=%+v", rep.Findings)
	}
}

func TestReviewNoGitRequired(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), []byte(`{"schema_version":"1","pack_id":"house-policy","readiness_score":100}`+"\n"))
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("x\n"))
	mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("x\n"))
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:aaaaaaaaaaaaaaaa --><dl></dl>`))
	cwd, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(cwd) })
	if err := os.Chdir(dir); err != nil {
		t.Fatal(err)
	}
	_, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
	if err != nil {
		t.Fatalf("review must work without git cwd: %v", err)
	}
}

func TestClassifyReferenceGolden(t *testing.T) {
	cases := []struct {
		in   string
		want review.RefKind
	}{
		{"HOUSE-SECURITY-MD", review.RefClaim},
		{"CRA-VULN-HANDLING", review.RefClaim},
		{"MEDTECH-RISK-1", review.RefClaim},
		{"https://example.com/x", review.RefURL},
		{"docs/foo.md", review.RefPath},
		{"SECURITY.md", review.RefPath},
		{"README.md", review.RefPath},
		{"true", review.RefDrop},
		{"schema_version", review.RefDrop},
		{"v0.5.2", review.RefDrop},
		{"abcdef012345", review.RefDrop},
		{"", review.RefDrop},
	}
	for _, tc := range cases {
		if got := review.ClassifyReference(tc.in); got != tc.want {
			t.Errorf("ClassifyReference(%q)=%q want %q", tc.in, got, tc.want)
		}
	}
}

func TestOneStatePerPathIdentity(t *testing.T) {
	dir := t.TempDir()
	payload := ir.GateFailurePayload{SchemaVersion: "1", PackID: "house-policy", ReadinessScore: 50}
	raw, _ := json.MarshalIndent(payload, "", "  ")
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), append(raw, '\n'))
	// Cite both docs/x.md and x.md — two identities even if same basename resolution.
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("see `docs/x.md` and `x.md` and `HOUSE-SECURITY-MD`\n"))
	mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("ok\n"))
	mustWrite(t, filepath.Join(dir, "x.md"), []byte("content\n"))
	digest := ir.ComputeResultDigest(payload)
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:bbbbbbbbbbbbbbbb -->
<dl class="prov"><dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>`+digest[:12]+`…</dd></dl>`))

	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	var pathFindings []review.Finding
	for _, f := range rep.Findings {
		if strings.HasPrefix(f.ID, "reference:path:") {
			pathFindings = append(pathFindings, f)
		}
	}
	if len(pathFindings) != 2 {
		t.Fatalf("want 2 path identities, got %d: %+v", len(pathFindings), pathFindings)
	}
	// Claim must not also appear as a path key.
	for _, f := range rep.Findings {
		if strings.Contains(f.ID, "reference:path:") && strings.Contains(f.ID, "HOUSE-SECURITY-MD") {
			t.Fatalf("claim id must not enter path resolver: %s", f.ID)
		}
	}
}

func TestSensitivityMatrix(t *testing.T) {
	t.Run("absent_path_genuine", func(t *testing.T) {
		dir := writeMinimalConsistent(t)
		mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("missing `docs/absent.md`\n"))
		rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
		if err != nil {
			t.Fatal(err)
		}
		ok := false
		for _, f := range rep.Findings {
			if f.ID == "reference:path:docs/absent.md" && f.State == review.StateUnconfirmed && f.Cause == review.CauseGenuine {
				ok = true
			}
		}
		if !ok || rep.UnconfirmedGenuine < 1 {
			t.Fatalf("want unconfirmed+genuine for absent path, got %+v", rep.Findings)
		}
	})
	t.Run("altered_result_digest", func(t *testing.T) {
		dir := t.TempDir()
		payload := ir.GateFailurePayload{SchemaVersion: "1", PackID: "house-policy", ReadinessScore: 10}
		raw, _ := json.MarshalIndent(payload, "", "  ")
		mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), append(raw, '\n'))
		mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("ok\n"))
		mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("ok\n"))
		mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:cccccccccccc -->
<dl><dt>result_digest</dt><dd>111111111111…</dd></dl>`))
		rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
		if err != nil {
			t.Fatal(err)
		}
		ok := false
		for _, f := range rep.Findings {
			if f.ID == "digest:result-digest-match" && f.State == review.StateContradicted && f.Cause == review.CauseSelfDisagree {
				ok = true
			}
		}
		if !ok {
			t.Fatalf("want contradicted+self_disagree for altered digest: %+v", rep.Findings)
		}
	})
	t.Run("wrong_sbom_digest", func(t *testing.T) {
		dir := writeMinimalConsistent(t)
		mustWrite(t, filepath.Join(dir, "04-sbom.cdx.json"), []byte(`{"bomFormat":"CycloneDX"}`+"\n"))
		// Rewrite onepager with wrong sbom_digest
		payload := mustPayload(t, dir)
		digest := ir.ComputeResultDigest(payload)
		mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:dddddddddddd -->
<dl class="prov">
<dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>`+digest[:12]+`…</dd>
<dt>sbom_digest</dt><dd>ffffffffffff…</dd>
</dl>`))
		rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
		if err != nil {
			t.Fatal(err)
		}
		ok := false
		for _, f := range rep.Findings {
			if f.ID == "digest:sbom_digest" && f.State == review.StateContradicted && f.Cause == review.CauseSelfDisagree {
				ok = true
			}
		}
		if !ok {
			t.Fatalf("want sbom digest contradiction: %+v", rep.Findings)
		}
	})
}

func TestSpecificityKnownGood(t *testing.T) {
	dir := writeMinimalConsistent(t)
	// Put SECURITY.md in bundle so the path cite confirms; no external URLs.
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), []byte("# security\n"))
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("see `SECURITY.md`\n"))
	payload := mustPayload(t, dir)
	digest := ir.ComputeResultDigest(payload)
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:eeeeeeeeeeeeeeee -->
<dl class="prov"><dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>`+digest[:12]+`…</dd></dl>`))

	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	if rep.UnconfirmedGenuine != 0 {
		t.Fatalf("specificity: UnconfirmedGenuine want 0 got %d findings=%+v", rep.UnconfirmedGenuine, rep.Findings)
	}
	if rep.ContradictedCount != 0 {
		t.Fatalf("specificity: ContradictedCount want 0 got %d findings=%+v", rep.ContradictedCount, rep.Findings)
	}
}

func TestThreatSymlinkSkipped(t *testing.T) {
	dir := writeMinimalConsistent(t)
	target := filepath.Join(dir, "secret.txt")
	mustWrite(t, target, []byte("should-not-read\n"))
	link := filepath.Join(dir, "02-action-report.md")
	_ = os.Remove(link)
	if err := os.Symlink(target, link); err != nil {
		t.Skip("symlink not supported:", err)
	}
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	// Required layer as symlink → contradicted structure
	found := false
	for _, f := range rep.Findings {
		if f.ID == "structure:02-action-report.md" && f.State == review.StateContradicted {
			found = true
		}
	}
	if !found {
		t.Fatalf("symlink required layer must contradict: %+v", rep.Findings)
	}
}

func TestThreatSizeCapFinding(t *testing.T) {
	dir := t.TempDir()
	// Oversized gate JSON → truncation finding (not silent).
	big := bytes.Repeat([]byte("a"), 9<<20)
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), big)
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("x\n"))
	mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("x\n"))
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:ffffffffffffffff --><dl></dl>`))
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, f := range rep.Findings {
		if f.ID == "digest:gate-json-size" && f.State == review.StateContradicted {
			found = true
		}
	}
	if !found {
		t.Fatalf("size cap must emit finding: %+v", rep.Findings)
	}
}

func TestExtractorVisibleInTerse(t *testing.T) {
	dir := writeMinimalConsistent(t)
	// No path/claim/url → extractor reference:none; also drop-shaped backticks
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("flag `true` and `schema_version`\n"))
	payload := mustPayload(t, dir)
	digest := ir.ComputeResultDigest(payload)
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:abcabcabcabcabcd -->
<dl class="prov"><dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>`+digest[:12]+`…</dd></dl>`))
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &buf})
	if err != nil {
		t.Fatal(err)
	}
	if rep.DroppedCount < 1 {
		t.Fatalf("expected dropped tokens, got %d", rep.DroppedCount)
	}
	if rep.UnconfirmedExtractor < 1 {
		t.Fatalf("expected extractor unconfirmed, got %d", rep.UnconfirmedExtractor)
	}
	if !strings.Contains(buf.String(), "extractor") {
		t.Fatalf("terse line must show extractor when >0: %s", buf.String())
	}
}

func TestContextPackNotTriageSurface(t *testing.T) {
	dir := writeMinimalConsistent(t)
	// Cache paths only in context-pack.md — assistant export, not assessor claim surface.
	mustWrite(t, filepath.Join(dir, "context-pack.md"), []byte(
		"# Context pack\n\nSee `.github/curbpack/cache/latest_failure.json` and `.github/curbpack/cache/latest_result.json`.\n",
	))
	mustWrite(t, filepath.Join(dir, "context-pack.json"), []byte(`{"schema":"curbpack-context-pack:1"}`+"\n"))
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range rep.Findings {
		if strings.Contains(f.ID, "reference:path:") && strings.Contains(f.ID, ".github/curbpack/cache") {
			t.Fatalf("cache paths in context-pack.md must not become reference findings: %s", f.ID)
		}
		if f.State == review.StateUnconfirmed && f.Cause == review.CauseGenuine &&
			strings.Contains(f.Detail, ".github/curbpack/cache") {
			t.Fatalf("cache paths must not flood genuine: %+v", f)
		}
	}
	// Structure check for context-pack.json remains.
	foundJSON := false
	for _, f := range rep.Findings {
		if f.ID == "structure:context-pack.json" && f.State == review.StateConfirmed {
			foundJSON = true
		}
	}
	if !foundJSON {
		t.Fatal("optional structure check for context-pack.json must remain")
	}
}

func TestAirlockRedactThenEmit(t *testing.T) {
	dir := writeMinimalConsistent(t)
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte(
		"suspicious cite `/Users/evil/.ssh/id_rsa` in action report\n",
	))
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &buf, Full: true})
	if err != nil {
		t.Fatalf("home-path cite must not fail airlock after redact-then-emit: %v", err)
	}
	out := buf.String()
	if strings.Contains(out, "/Users/evil") {
		t.Fatalf("emitted triage must not echo home path: %s", out)
	}
	if !strings.Contains(out, "<redacted:home-path>") {
		t.Fatalf("expected home-path redaction placeholder in output: %s", out)
	}
	found := false
	for _, f := range rep.Findings {
		if f.ID == "structure:airlock-redacted" && f.State == review.StateContradicted && f.Cause == review.CauseSelfDisagree {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected structure:airlock-redacted contradicted finding, got %+v", rep.Findings)
	}
	if !review.HasContradictions(rep) {
		t.Fatal("airlock redaction is a contradiction (bundle echoed unsafe material)")
	}
}

func writeMinimalConsistent(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	payload := ir.GateFailurePayload{SchemaVersion: "1", PackID: "house-policy", ReadinessScore: 80}
	raw, _ := json.MarshalIndent(payload, "", "  ")
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), append(raw, '\n'))
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("ok\n"))
	mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("ok\n"))
	digest := ir.ComputeResultDigest(payload)
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(`<!-- curbpack-onepager-fp:aaaaaaaaaaaaaaaa -->
<dl class="prov"><dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>`+digest[:12]+`…</dd></dl>`))
	return dir
}

func mustPayload(t *testing.T, dir string) ir.GateFailurePayload {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join(dir, "01-gate-failures.json"))
	if err != nil {
		t.Fatal(err)
	}
	var p ir.GateFailurePayload
	if err := json.Unmarshal(raw, &p); err != nil {
		t.Fatal(err)
	}
	return p
}

type ioDiscard struct{}

func (ioDiscard) Write(p []byte) (int, error) { return len(p), nil }

func mustWrite(t *testing.T, path string, data []byte) {
	t.Helper()
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatal(err)
	}
}
