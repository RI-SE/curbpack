package release_test

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/release/templates"
)

func TestShareStale_missing_onepager(t *testing.T) {
	dir := t.TempDir()
	sig, _ := release.ShareStaleReport(dir, attest.BindInfo{}, 80, true)
	if sig != "share_no_review_pack" {
		t.Fatalf("want share_no_review_pack, got %s", sig)
	}
}

func TestShareStale_cache_missing(t *testing.T) {
	dir := t.TempDir()
	_ = os.MkdirAll(filepath.Join(dir, "review-pack"), 0o755)
	_ = os.WriteFile(filepath.Join(dir, "review-pack", "buyer-onepager.html"), []byte("<!-- curbpack-onepager-fp:abc -->"), 0o644)
	sig, _ := release.ShareStaleReport(dir, attest.BindInfo{}, 80, true)
	if sig != "share_cache_missing" {
		t.Fatalf("want share_cache_missing, got %s", sig)
	}
}

func TestShareStale_match(t *testing.T) {
	dir := t.TempDir()
	payload := ir.GateFailurePayload{PackID: "house-policy", Failures: nil, ReadinessScore: 100}
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	_ = os.MkdirAll(cache, 0o755)
	raw, _ := json.Marshal(payload)
	_ = os.WriteFile(filepath.Join(cache, "latest_result.json"), raw, 0o644)
	bind := attest.BindInfo{Found: false}
	packDir := filepath.Join(dir, "review-pack")
	fp := release.FingerprintFromGatePayload(payload, bind, 100, true, packDir)
	htmlDoc := templates.BuyerOnePagerHTML(templates.OnePagerDTO{
		RepoName: "test", Score: 100, Passed: true, PackID: "house-policy",
		Timestamp: "2026-01-01T00:00:00Z", AttestLine: "UNSIGNED — not cryptographically verified",
		AttestClass: "unsigned", UnsignedLoud: true,
		ProvenanceHTML: "<dl></dl>", FooterPrefix: "x · ",
		ResultDigest:   ir.ComputeResultDigest(payload),
	})
	if !strings.Contains(htmlDoc, fp) {
		t.Fatalf("html missing fp marker %s", fp)
	}
	_ = os.MkdirAll(packDir, 0o755)
	_ = os.WriteFile(filepath.Join(packDir, "buyer-onepager.html"), []byte(htmlDoc), 0o644)
	sig, _ := release.ShareStaleReport(dir, bind, 100, true)
	if sig != "share_current" {
		t.Fatalf("want share_current, got %s", sig)
	}
}

func TestShareStale_mismatch(t *testing.T) {
	dir := t.TempDir()
	payload := ir.GateFailurePayload{PackID: "house-policy", ReadinessScore: 80}
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	_ = os.MkdirAll(cache, 0o755)
	raw, _ := json.Marshal(payload)
	_ = os.WriteFile(filepath.Join(cache, "latest_result.json"), raw, 0o644)
	_ = os.MkdirAll(filepath.Join(dir, "review-pack"), 0o755)
	_ = os.WriteFile(filepath.Join(dir, "review-pack", "buyer-onepager.html"), []byte("<!-- curbpack-onepager-fp:deadbeef -->"), 0o644)
	sig, _ := release.ShareStaleReport(dir, attest.BindInfo{}, 80, true)
	if sig != "share_stale" {
		t.Fatalf("want share_stale, got %s", sig)
	}
}

func TestFingerprintFromGatePayload_MatchesHTML(t *testing.T) {
	payload := ir.GateFailurePayload{
		PackID: "house-policy",
		Failures: []ir.Failure{
			{GateID: "G-1", Severity: "high"},
		},
	}
	bind := attest.BindInfo{CommitSHA: "abc", StateHash: "def"}
	rd := ir.ComputeResultDigest(payload)
	dto := templates.OnePagerDTO{
		Score: 80, Passed: false, PackID: payload.PackID,
		Failures: []templates.OnePagerFailure{{GateID: "G-1", Severity: "high"}},
		Bind: bind, AttestLine: "UNSIGNED — not cryptographically verified",
		UnsignedLoud: true, ResultDigest: rd,
	}
	htmlFP := templates.OnePagerFingerprint(dto)
	payloadFP := release.FingerprintFromGatePayload(payload, bind, 80, false, "")
	if htmlFP != payloadFP {
		t.Fatalf("fp mismatch html=%s payload=%s", htmlFP, payloadFP)
	}
}

func TestShareStale_coherentWithDigests(t *testing.T) {
	dir := t.TempDir()
	payload := ir.GateFailurePayload{PackID: "house-policy", ReadinessScore: 100}
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	_ = os.MkdirAll(cache, 0o755)
	raw, _ := json.Marshal(payload)
	_ = os.WriteFile(filepath.Join(cache, "latest_result.json"), raw, 0o644)
	packDir := filepath.Join(dir, "review-pack")
	_ = os.MkdirAll(packDir, 0o755)
	sbom := []byte(`{"bomFormat":"CycloneDX","specVersion":"1.5","components":[]}`)
	_ = os.WriteFile(filepath.Join(packDir, "04-sbom.cdx.json"), sbom, 0o644)
	vex := []byte(`{"@context":"https://openvex.dev/ns","statements":[]}`)
	_ = os.WriteFile(filepath.Join(packDir, "05-vex-draft.json"), vex, 0o644)
	bind := attest.BindInfo{Found: false}
	fp := release.FingerprintFromGatePayload(payload, bind, 100, true, packDir)
	htmlDoc := templates.BuyerOnePagerHTML(templates.OnePagerDTO{
		RepoName: "test", Score: 100, Passed: true, PackID: "house-policy",
		Timestamp: "2026-01-01T00:00:00Z", AttestLine: "UNSIGNED — not cryptographically verified",
		AttestClass: "unsigned", UnsignedLoud: true,
		ProvenanceHTML: "<dl><dt>result_digest</dt><dd>x</dd></dl>", FooterPrefix: "x · ",
		ResultDigest:   ir.ComputeResultDigest(payload),
		SBOMDigest:     mustFileSHA(t, filepath.Join(packDir, "04-sbom.cdx.json")),
		VEXDigest:      mustFileSHA(t, filepath.Join(packDir, "05-vex-draft.json")),
	})
	if !strings.Contains(htmlDoc, fp) {
		t.Fatalf("html missing fp %s", fp)
	}
	_ = os.WriteFile(filepath.Join(packDir, "buyer-onepager.html"), []byte(htmlDoc), 0o644)
	sig, detail := release.ShareStaleReport(dir, bind, 100, true)
	if sig != "share_current" {
		t.Fatalf("want share_current with digests present, got %s (%s)", sig, detail)
	}
}

func mustFileSHA(t *testing.T, path string) string {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(b)
	return fmt.Sprintf("%x", sum)
}
