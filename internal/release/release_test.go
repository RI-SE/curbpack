package release_test

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/release/templates"
	"github.com/afelin/curbpack/internal/review"
)

func TestPrepareAggregatesPartialWriteFailures(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	dir := t.TempDir()
	initPassingHouse(t, dir)

	out := filepath.Join(dir, "review-pack")
	if err := os.MkdirAll(out, 0o755); err != nil {
		t.Fatal(err)
	}
	// Block several review-pack writes cross-platform (chmod on dirs is Unix-only).
	for _, name := range []string{
		"01-gate-failures.json",
		"02-action-report.md",
		"03-executive-summary.md",
		"06-gate-failures.sarif",
	} {
		if err := os.MkdirAll(filepath.Join(out, name), 0o755); err != nil {
			t.Fatal(err)
		}
	}

	err := release.Prepare(release.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, OutDir: out})
	if err == nil {
		t.Fatal("expected aggregated write errors")
	}
	var joined interface{ Unwrap() []error }
	if !errors.As(err, &joined) {
		t.Fatalf("expected errors.Join aggregate, got %T: %v", err, err)
	}
	if len(joined.Unwrap()) < 2 {
		t.Fatalf("expected multiple partial failures, got %d: %v", len(joined.Unwrap()), err)
	}
}

func TestPrepareEmitsResultDigestAndStaysUnsigned(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	dir := t.TempDir()
	initPassingHouse(t, dir)
	out := filepath.Join(dir, "review-pack")
	if err := release.Prepare(release.Options{
		RepoRoot: dir, PackIDs: []string{"house-policy"}, OutDir: out, AllowFailingGates: true,
	}); err != nil {
		t.Fatal(err)
	}
	htmlDoc, err := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	s := string(htmlDoc)
	if !strings.Contains(s, "<dt>result_digest</dt>") {
		t.Fatal("one-pager must emit result_digest from payload")
	}
	if !strings.Contains(s, "UNSIGNED") {
		t.Fatal("emitting digests must not drop UNSIGNED trust rendering")
	}
	// Share → review stays consistent and unsigned (no crypto upgrade from digests).
	rep, err := review.Run(review.Options{BundleRoot: out, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	if review.HasContradictions(rep) {
		t.Fatalf("fresh prepare-release pack must not contradict: %+v", rep.Findings)
	}
	matched := false
	for _, f := range rep.Findings {
		if f.ID == "digest:result-digest-match" && f.State == review.StateConfirmed {
			matched = true
		}
	}
	if !matched {
		t.Fatalf("expected result_digest match finding, got %+v", rep.Findings)
	}
}

func TestPrepareRewritesOnePagerWhenDigestsMissing(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	dir := t.TempDir()
	initPassingHouse(t, dir)
	out := filepath.Join(dir, "review-pack")
	opts := release.Options{
		RepoRoot: dir, PackIDs: []string{"house-policy"}, OutDir: out, AllowFailingGates: true,
	}
	if err := release.Prepare(opts); err != nil {
		t.Fatal(err)
	}
	// Simulate pre-digest one-pager: strip digests and stamp gate-only fingerprint
	// (empty ResultDigest/SBOMDigest/VEXDigest) so writeOnePagerIfChanged would skip
	// without the digest seed fix.
	prev, err := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	stripped := string(prev)
	for _, key := range []string{"result_digest", "sbom_digest", "vex_digest"} {
		// Remove <dt>key</dt><dd>…</dd> lines (and bind variants).
		for {
			dt := "<dt>" + key
			i := strings.Index(stripped, dt)
			if i < 0 {
				break
			}
			j := strings.Index(stripped[i:], "</dd>")
			if j < 0 {
				break
			}
			stripped = stripped[:i] + stripped[i+j+len("</dd>"):]
		}
	}
	gateOnly := templates.OnePagerFingerprint(templates.OnePagerDTO{
		Score: 100, Passed: true, PackID: "house-policy",
		AttestLine: "UNSIGNED — not cryptographically verified", UnsignedLoud: true,
	})
	const marker = "<!-- curbpack-onepager-fp:"
	if i := strings.Index(stripped, marker); i >= 0 {
		rest := stripped[i+len(marker):]
		if j := strings.Index(rest, " -->"); j >= 0 {
			stripped = stripped[:i] + marker + gateOnly + " -->" + rest[j+len(" -->"):]
		}
	}
	if strings.Contains(stripped, "<dt>result_digest</dt>") {
		t.Fatal("setup: digests should be stripped before rewrite test")
	}
	if err := os.WriteFile(filepath.Join(out, "buyer-onepager.html"), []byte(stripped), 0o644); err != nil {
		t.Fatal(err)
	}

	if err := release.Prepare(opts); err != nil {
		t.Fatal(err)
	}
	rewritten, err := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	s := string(rewritten)
	if !strings.Contains(s, "<dt>result_digest</dt>") {
		t.Fatal("Prepare must rewrite one-pager to include result_digest")
	}
	if _, err := os.Stat(filepath.Join(out, "04-sbom.cdx.json")); err == nil {
		if !strings.Contains(s, "<dt>sbom_digest</dt>") {
			t.Fatal("Prepare must emit sbom_digest when SBOM file exists")
		}
	}
	if _, err := os.Stat(filepath.Join(out, "05-vex-draft.json")); err == nil {
		if !strings.Contains(s, "<dt>vex_digest</dt>") {
			t.Fatal("Prepare must emit vex_digest when VEX file exists")
		}
	}
	fp1 := extractFP(s)
	if fp1 == "" || fp1 == gateOnly {
		t.Fatalf("rewritten fp must include digests (got %q, gate-only %q)", fp1, gateOnly)
	}

	// Second identical Prepare → fingerprint match → no rewrite (content stable aside from Generated).
	before := s
	if err := release.Prepare(opts); err != nil {
		t.Fatal(err)
	}
	again, err := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	if extractFP(string(again)) != fp1 {
		t.Fatal("second Prepare must keep fingerprint (unchanged)")
	}
	// Marker-stable skip: body may only differ on Generated timestamp line.
	if stripGenerated(before) != stripGenerated(string(again)) {
		t.Fatal("second Prepare must not rewrite one-pager body beyond Generated line")
	}

	bind, _ := attest.LatestBind(dir)
	payload, ok := release.LoadCachedGatePayload(dir)
	if !ok {
		t.Fatal("expected gate cache after Prepare")
	}
	passed := len(payload.Failures) == 0
	sig, detail := release.ShareStaleReport(dir, bind, payload.ReadinessScore, passed)
	if sig != "share_current" {
		t.Fatalf("ShareStale with digests: want share_current, got %s (%s)", sig, detail)
	}
}

func extractFP(htmlDoc string) string {
	const marker = "<!-- curbpack-onepager-fp:"
	if i := strings.Index(htmlDoc, marker); i >= 0 {
		rest := htmlDoc[i+len(marker):]
		if j := strings.Index(rest, " -->"); j >= 0 {
			return rest[:j]
		}
	}
	return ""
}

func stripGenerated(htmlDoc string) string {
	var b strings.Builder
	for _, line := range strings.Split(htmlDoc, "\n") {
		if strings.Contains(line, "Generated ") {
			continue
		}
		b.WriteString(line)
		b.WriteByte('\n')
	}
	return b.String()
}

type ioDiscard struct{}

func (ioDiscard) Write(p []byte) (int, error) { return len(p), nil }

func initPassingHouse(t *testing.T, dir string) {
	t.Helper()
	write := func(rel, body string) {
		t.Helper()
		p := filepath.Join(dir, rel)
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	write("README.md", "# Project\n")
	write(".well-known/security.txt", "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	write("SECURITY.md", "# Security Policy\n\n## Reporting\n\nReport vulnerabilities to security@example.com.\n\n## Supported Versions\n\nLatest release.\n\n## Disclosure\n\nCoordinated disclosure.\n\n"+strings.Repeat("word ", 40))
	runGit(t, dir, "init", "-q")
	runGit(t, dir, "config", "user.email", "release@curbpack.local")
	runGit(t, dir, "config", "user.name", "Release")
	runGit(t, dir, "add", ".")
	runGit(t, dir, "commit", "-m", "init", "-q")
}

func runGit(t *testing.T, dir string, args ...string) {
	t.Helper()
	cmd := exec.Command("git", args...)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v\n%s", args, err, out)
	}
}
