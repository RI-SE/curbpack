package templates_test

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/release/templates"
)

func TestOnePagerFingerprintStable(t *testing.T) {
	dto := templates.OnePagerDTO{
		Score: 100, Passed: true, PackID: "house-policy",
		AttestLine: "UNSIGNED — not cryptographically verified", UnsignedLoud: true,
		Bind: attest.BindInfo{CommitSHA: "abc123", StateHash: "def456"},
	}
	a := templates.OnePagerFingerprint(dto)
	b := templates.OnePagerFingerprint(dto)
	if a != b || a == "" {
		t.Fatalf("fingerprint not stable: %q %q", a, b)
	}
	dto2 := dto
	dto2.Score = 80
	if templates.OnePagerFingerprint(dto2) == a {
		t.Fatal("score change must change fingerprint")
	}
	dto3 := dto
	dto3.ResultDigest = "abcdef0123456789"
	if templates.OnePagerFingerprint(dto3) == a {
		t.Fatal("digest change must change fingerprint")
	}
}

func TestOnePagerFingerprintIgnoresCoverAndReviewedBy(t *testing.T) {
	base := templates.OnePagerDTO{
		Score: 100, Passed: true, PackID: "house-policy",
		AttestLine: "UNSIGNED — not cryptographically verified", UnsignedLoud: true,
		Bind: attest.BindInfo{CommitSHA: "abc123", StateHash: "def456"},
	}
	want := templates.OnePagerFingerprint(base)
	withCover := base
	withCover.CoverRows = []templates.OnePagerCoverRow{{Path: "SECURITY.md", Question: "For human review: present?"}}
	withCover.PackLabels = "House Policy Example"
	if templates.OnePagerFingerprint(withCover) != want {
		t.Fatal("cover rows / pack labels must not change fingerprint")
	}
	withName := base
	withName.Bind.ReviewedBy = "Ada Reviewer"
	if templates.OnePagerFingerprint(withName) != want {
		t.Fatal("reviewed-by must not change fingerprint")
	}
}

func TestBuyerOnePagerCoverBeforeScore(t *testing.T) {
	htmlDoc := templates.BuyerOnePagerHTML(templates.OnePagerDTO{
		RepoName: "sample", Score: 62, Passed: false, PackID: "house-policy",
		PackLabels: "House Policy Example",
		AssuranceClass: "structural_draft", MechanicalSummary: "5 of 7 gates mechanically evidenced",
		AttestLine: "UNSIGNED — not cryptographically verified", UnsignedLoud: true,
		AttestClass: "unsigned",
		CoverRows: []templates.OnePagerCoverRow{
			{Path: "SECURITY.md", Question: "For human review: Is a disclosure path present?"},
		},
		Failures: []templates.OnePagerFailure{
			{GateID: "HOUSE-SECURITY-MD", Severity: "high", Description: "missing"},
		},
		ProvenanceHTML: "<dl></dl>", Timestamp: "2026-08-13T00:00:00Z",
	})
	idx := strings.Index(htmlDoc, "Back — provenance")
	if idx < 0 {
		t.Fatal("missing Back — provenance")
	}
	front := htmlDoc[:idx]
	back := htmlDoc[idx:]
	if strings.Contains(strings.ToLower(front), "hpurl") {
		t.Fatal("front must not use HPURL jargon")
	}
	if !strings.Contains(front, "Files to open") || !strings.Contains(front, "SECURITY.md") {
		t.Fatal("front must lead with files to open")
	}
	if !strings.Contains(front, "House Policy Example") {
		t.Fatal("front must show pack names in plain words")
	}
	if !strings.Contains(front, "Assurance class:") || !strings.Contains(front, "mechanically evidenced") {
		t.Fatal("front must show assurance class and mechanically evidenced summary")
	}
	if strings.Contains(front, "Local gate score") {
		t.Fatal("score meter must not lead the front")
	}
	if !strings.Contains(back, "Local gate score") || !strings.Contains(back, "not certification") {
		t.Fatal("score meter must sit under Back — provenance with not-certification clause")
	}
	if strings.Contains(htmlDoc, "we are CE") || strings.Contains(htmlDoc, "CRA compliant") {
		t.Fatal("claim-unsafe copy in one-pager")
	}
	if !strings.Contains(htmlDoc, "not a certificate of conformity") {
		t.Fatal("must keep certificate disclaimer")
	}
}
