package review_test

import (
	"bytes"
	"encoding/json"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/review"
)

// FG-04: a one-character claimed digest must not confirm (MUST-12).
func TestShortClaimedDigestDoesNotConfirm(t *testing.T) {
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
	short := string(digest[0])
	html := `<!DOCTYPE html><html><head>
<!-- curbpack-onepager-fp:abcdef0123456789 -->
</head><body>
<dl class="prov">
<dt>result_digest</dt><dd>` + short + `</dd>
</dl>
</body></html>`
	mustWrite(t, filepath.Join(dir, "buyer-onepager.html"), []byte(html))

	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &bytes.Buffer{}})
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range rep.Findings {
		if f.ID == "digest:result-digest-match" && f.State == review.StateConfirmed {
			t.Fatalf("FG-04: one-char claim %q must not confirm; findings=%+v", short, rep.Findings)
		}
	}
	var match *review.Finding
	for i := range rep.Findings {
		if rep.Findings[i].ID == "digest:result-digest-match" {
			match = &rep.Findings[i]
			break
		}
	}
	if match == nil {
		t.Fatal("missing digest:result-digest-match finding")
	}
	if match.State != review.StateContradicted {
		t.Fatalf("want contradicted for short claim, got %s (%s)", match.State, match.Detail)
	}
}

func TestFixedPrefixDigestConfirms(t *testing.T) {
	dir := writeMinimalConsistent(t)
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &bytes.Buffer{}})
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range rep.Findings {
		if f.ID == "digest:result-digest-match" && f.State == review.StateConfirmed {
			return
		}
	}
	t.Fatalf("12-hex prefix claim should still confirm; findings=%+v", rep.Findings)
}
