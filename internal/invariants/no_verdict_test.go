package invariants_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/release/templates"
	"github.com/afelin/curbpack/internal/validate"
)

// Claim-safe framing on a line (mirrors scripts/claim-safety.sh SAFE_RE spirit).
var noVerdictSafeLine = regexp.MustCompile(`(?i)not (a |an )?(conformity|certif|ce)|never claim|no certification|not cra-compliant|not nis2-compliant|certification_claimed|certification claimed: no|not a certificate|does not certify`)

// Aggregate legal conclusions / certification theater that public renderers must not emit as a Curbpack verdict.
var noVerdictBanned = []*regexp.Regexp{
	regexp.MustCompile(`(?i)\bcra-compliant\b`),
	regexp.MustCompile(`(?i)\bnis2-compliant\b`),
	regexp.MustCompile(`(?i)\bcompliant\b`),
	regexp.MustCompile(`(?i)merge[- ]allow`),
	regexp.MustCompile(`(?i)promote allowed`),
	regexp.MustCompile(`(?i)\bwe are certified\b`),
	regexp.MustCompile(`(?i)product is certified`),
	regexp.MustCompile(`(?i)officially certified`),
	regexp.MustCompile(`(?i)notified[- ]body approved`),
	regexp.MustCompile(`(?i)conformity assessment (complete|passed|successful)`),
	regexp.MustCompile(`(?i)ce marking (issued|granted|obtained)`),
	regexp.MustCompile(`(?i)eu cra baseline`),
	regexp.MustCompile(`(?i)rise[- ](approved|certified)`),
}

// TestNoVerdictSurface enumerates public renderers/templates and asserts none emit
// aggregate legal conclusions. Does not strip GateFailurePayload.readiness_score
// (one-pager fingerprint still hashes the back-of-page score).
func TestNoVerdictSurface(t *testing.T) {
	assertReadinessScoreKept(t)

	onePager := templates.BuyerOnePagerHTML(templates.OnePagerDTO{
		RepoName: "sample", Score: 62, Passed: false, PackID: "house-policy",
		PackLabels:   "House Policy Example",
		AttestLine:   "UNSIGNED — not cryptographically verified",
		UnsignedLoud: true, AttestClass: "unsigned",
		CoverRows: []templates.OnePagerCoverRow{
			{Path: "SECURITY.md", Question: "For human review: Is a disclosure path present?"},
		},
		Failures: []templates.OnePagerFailure{
			{GateID: "HOUSE-SECURITY-MD", Severity: "high", Description: "missing"},
		},
		Bind:           attest.BindInfo{CommitSHA: "abc123", StateHash: "def456"},
		ProvenanceHTML: "<dl></dl>", Timestamp: "2026-08-18T00:00:00Z",
	})
	onePagerPass := templates.BuyerOnePagerHTML(templates.OnePagerDTO{
		RepoName: "sample", Score: 100, Passed: true, PackID: "house-policy",
		AttestLine: "ssh-agent signed", AttestClass: "ok",
		Timestamp: "2026-08-18T00:00:00Z",
	})
	if !strings.Contains(onePager, "Local gate score") || !strings.Contains(onePager, "62%") {
		t.Fatal("one-pager must keep the back-of-page gate score (fingerprint seed)")
	}

	bundle := templates.EvidenceBundleHTML(templates.BundleDTO{
		RepoName: "sample", Score: 80, Passed: true, Timestamp: "2026-08-18T00:00:00Z",
		Remediation: false, OnePagerBody: "<p>embed</p>",
	})
	bundleRed := templates.EvidenceBundleHTML(templates.BundleDTO{
		RepoName: "sample", Score: 40, Passed: false, Timestamp: "2026-08-18T00:00:00Z",
		Remediation: true,
	})

	sarif := exportx.FromGateFailures(ir.GateFailurePayload{
		PackID:         "house-policy",
		ReadinessScore: 60,
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			Severity:             "high",
			SanitizedDescription: "SECURITY.md missing",
			ASTCoordinates:       ir.ASTCoordinates{TargetFile: "SECURITY.md"},
		}},
	}, "")
	sarifJSON, err := json.Marshal(sarif)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(sarifJSON), `"certification_claimed":false`) {
		t.Fatal("SARIF covenant must keep certification_claimed false")
	}
	if !strings.Contains(string(sarifJSON), `"instrument_panel":true`) {
		t.Fatal("SARIF covenant must keep instrument_panel true")
	}

	dir := t.TempDir()
	mustGit(t, dir)
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")
	buyerPath, _, err := exportx.WriteBuyerQuestions(dir, []string{"house-policy", "cra-baseline"}, filepath.Join(dir, "buyer-questions.md"))
	if err != nil {
		t.Fatal(err)
	}
	buyerMD, err := os.ReadFile(buyerPath)
	if err != nil {
		t.Fatal(err)
	}
	buyerJSON, err := os.ReadFile(strings.TrimSuffix(buyerPath, ".md") + ".json")
	if err != nil {
		t.Fatal(err)
	}

	cpPath, err := exportx.WriteContextPack(dir, []string{"house-policy"}, filepath.Join(dir, "context-pack.json"))
	if err != nil {
		t.Fatal(err)
	}
	cpJSON, err := os.ReadFile(cpPath)
	if err != nil {
		t.Fatal(err)
	}
	cpMD, err := os.ReadFile(strings.TrimSuffix(cpPath, ".json") + ".md")
	if err != nil {
		t.Fatal(err)
	}
	var cp exportx.ContextPack
	if err := json.Unmarshal(cpJSON, &cp); err != nil {
		t.Fatal(err)
	}
	if cp.CertificationClaimed {
		t.Fatal("ContextPack note must keep certification_claimed false")
	}
	if !strings.Contains(strings.ToLower(cp.Note), "not a conformity") {
		t.Fatalf("ContextPack note missing fence: %q", cp.Note)
	}

	action := validate.ActionReportMarkdown(ir.GateFailurePayload{
		PackID: "house-policy", ReadinessScore: 60,
		Failures: []ir.Failure{{GateID: "X", Severity: "low", Type: "T", SanitizedDescription: "d"}},
	}, 0)
	if !strings.Contains(action, "60%") {
		t.Fatal("action report must still show readiness_score")
	}

	surfaces := []struct {
		name string
		body string
	}{
		{"one-pager", onePager},
		{"one-pager-pass", onePagerPass},
		{"proof", templates.ProofPageHTML()},
		{"buyer-questions-md", string(buyerMD)},
		{"buyer-questions-json", string(buyerJSON)},
		{"bundle", bundle},
		{"bundle-red", bundleRed},
		{"context-pack-note", cp.Note},
		{"context-pack-md", string(cpMD)},
		{"context-pack-json", string(cpJSON)},
		{"sarif-covenant", string(sarifJSON)},
		{"action-report", action},
	}
	if len(surfaces) < 8 {
		t.Fatal("enumerate one-pager, proof, buyer-questions, bundle, ContextPack note, SARIF covenant")
	}
	for _, s := range surfaces {
		if hits := bannedVerdictHits(s.body); len(hits) > 0 {
			t.Errorf("%s emits banned verdict %v", s.name, hits)
		}
	}
}

func assertReadinessScoreKept(t *testing.T) {
	t.Helper()
	f, ok := reflect.TypeOf(ir.GateFailurePayload{}).FieldByName("ReadinessScore")
	if !ok {
		t.Fatal("do not strip ReadinessScore from GateFailurePayload until fingerprint redesign")
	}
	if !strings.Contains(f.Tag.Get("json"), "readiness_score") {
		t.Fatalf("readiness_score JSON tag must remain, got %q", f.Tag.Get("json"))
	}
	b, err := json.Marshal(ir.GateFailurePayload{ReadinessScore: 60, SchemaVersion: ir.SchemaVersion})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(b), `"readiness_score":60`) {
		t.Fatalf("GateFailurePayload must still serialize readiness_score: %s", b)
	}
}

func bannedVerdictHits(text string) []string {
	var hits []string
	for i, line := range strings.Split(text, "\n") {
		if strings.TrimSpace(line) == "" || noVerdictSafeLine.MatchString(line) {
			continue
		}
		for _, re := range noVerdictBanned {
			if m := re.FindString(line); m != "" {
				hits = append(hits, m+" @"+itoa(i+1))
			}
		}
	}
	return hits
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	var buf [16]byte
	i := len(buf)
	for n > 0 {
		i--
		buf[i] = byte('0' + n%10)
		n /= 10
	}
	return string(buf[i:])
}
