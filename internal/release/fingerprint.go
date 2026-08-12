package release

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/release/templates"
)

// LoadCachedGatePayload reads latest_result.json, falls back to latest_failure.json.
func LoadCachedGatePayload(repoRoot string) (ir.GateFailurePayload, bool) {
	cacheDir := filepath.Join(repoRoot, ".github", "curbpack", "cache")
	for _, name := range []string{"latest_result.json", "latest_failure.json"} {
		b, err := os.ReadFile(filepath.Join(cacheDir, name))
		if err != nil {
			continue
		}
		var payload ir.GateFailurePayload
		if json.Unmarshal(b, &payload) == nil {
			return payload, true
		}
	}
	return ir.GateFailurePayload{}, false
}

// FingerprintFromGatePayload computes the same stable marker as buyerOnePager without HTML.
func FingerprintFromGatePayload(payload ir.GateFailurePayload, bind attest.BindInfo, score int, passed bool) string {
	line, _, unsignedLoud := attest.AttestDisplay(bind)
	var failures []templates.OnePagerFailure
	for _, f := range payload.Failures {
		failures = append(failures, templates.OnePagerFailure{
			GateID: f.GateID, Severity: f.Severity,
		})
	}
	return templates.OnePagerFingerprint(templates.OnePagerDTO{
		Score: score, Passed: passed, PackID: payload.PackID,
		Failures: failures, Bind: bind, AttestLine: line, UnsignedLoud: unsignedLoud,
	})
}

// ShareStaleReport compares on-disk buyer-onepager.html fp to expected fp from cache+bind.
// Returns signal id and human detail (empty signal when no comparison possible).
func ShareStaleReport(repoRoot string, bind attest.BindInfo, score int, passed bool) (signal, detail string) {
	onepagerPath := filepath.Join(repoRoot, "review-pack", "buyer-onepager.html")
	prev, err := os.ReadFile(onepagerPath)
	if err != nil {
		return "share_no_review_pack", "review-pack/buyer-onepager.html missing — run curbpack share"
	}
	payload, ok := LoadCachedGatePayload(repoRoot)
	if !ok {
		return "share_cache_missing", "no gate cache JSON — run curbpack check or share"
	}
	expected := FingerprintFromGatePayload(payload, bind, score, passed)
	onDisk := extractOnePagerFP(string(prev))
	if onDisk == "" {
		return "share_stale", "buyer-onepager.html missing fingerprint marker — re-run share"
	}
	if onDisk != expected {
		return "share_stale", fmt.Sprintf("on-disk fp %s ≠ expected %s from cache+bind", onDisk, expected)
	}
	return "share_current", "buyer-onepager fingerprint matches cache+bind"
}

func extractOnePagerFP(htmlDoc string) string {
	const marker = "<!-- curbpack-onepager-fp:"
	if i := strings.Index(htmlDoc, marker); i >= 0 {
		rest := htmlDoc[i+len(marker):]
		if j := strings.Index(rest, " -->"); j >= 0 {
			return rest[:j]
		}
	}
	return onePagerFingerprint(htmlDoc)
}
