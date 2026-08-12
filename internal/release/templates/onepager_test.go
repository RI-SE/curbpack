package templates_test

import (
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
}
