package review_test

import (
	"bytes"
	"encoding/json"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/review"
)

// FG-01: copying a fingerprint marker into a forged one-pager must not yield
// digest:onepager-fp-marker StateConfirmed (presence is not independent verification).
func TestForgedFingerprintMarkerDoesNotConfirm(t *testing.T) {
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
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("# action\n"))
	mustWrite(t, filepath.Join(dir, "03-executive-summary.md"), []byte("# exec\n"))
	digest := ir.ComputeResultDigest(payload)
	// Attacker copies a plausible current-looking marker while forging the body.
	html := `<!DOCTYPE html><html><head>
<!-- curbpack-onepager-fp:deadbeefcafebabe -->
</head><body>
<p>FG01-FORGED-REVIEW-BODY</p>
<dl class="prov">
<dt>Rule packs</dt><dd>house-policy</dd>
<dt>result_digest</dt><dd>` + digest[:12] + `…</dd>
</dl>
</body></html>`
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(html))

	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &bytes.Buffer{}})
	if err != nil {
		t.Fatal(err)
	}
	var marker *review.Finding
	for i := range rep.Findings {
		if rep.Findings[i].ID == "digest:onepager-fp-marker" {
			marker = &rep.Findings[i]
			break
		}
	}
	if marker == nil {
		t.Fatal("missing digest:onepager-fp-marker finding")
	}
	if marker.State == review.StateConfirmed {
		t.Fatalf("FG-01: forged/copied fingerprint marker must not confirm; got %+v", marker)
	}
}
