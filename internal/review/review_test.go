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
	if rep.ConfirmedCount == 0 {
		t.Fatalf("expected some confirmed findings, got %+v", rep)
	}
	if review.HasContradictions(rep) {
		t.Fatalf("expected no contradictions on minimal consistent pack: %+v", rep.Findings)
	}
	md := buf.String()
	if !strings.Contains(md, "Document triage only") {
		t.Fatalf("triage missing disclaimer: %s", md)
	}
	if !strings.Contains(md, "Unconfirmed") {
		t.Fatalf("expected unconfirmed section for external URL: %s", md)
	}
	// No product verdict language
	banned := []string{"CRA-compliant", "CE marking", "notified-body approved", "we are certified"}
	for _, b := range banned {
		if strings.Contains(strings.ToLower(md), strings.ToLower(b)) {
			t.Fatalf("triage must not emit %q", b)
		}
	}
}

func TestReviewMissingRequiredContradicted(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "01-gate-failures.json"), []byte(`{"schema_version":"1","pack_id":"house-policy","readiness_score":0}`+"\n"))
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &buf})
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
		if f.ID == "digest:result-digest-match" && f.State == review.StateContradicted {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected result_digest contradiction, findings=%+v", rep.Findings)
	}
}

func TestReviewNoGitRequired(t *testing.T) {
	// Bundle outside any git repo — temp dir is enough.
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

type ioDiscard struct{}

func (ioDiscard) Write(p []byte) (int, error) { return len(p), nil }

func mustWrite(t *testing.T, path string, data []byte) {
	t.Helper()
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatal(err)
	}
}
