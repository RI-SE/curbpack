package release_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/release"
)

// FG-01: a forged one-pager that copies the current fingerprint marker but alters
// the body must not suppress rewrite on the next Prepare.
func TestPrepareRewritesForgedOnePagerWithCopiedFingerprint(t *testing.T) {
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
	legit, err := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	fp := extractFP(string(legit))
	if fp == "" {
		t.Fatal("expected fingerprint marker after Prepare")
	}

	const forgeToken = "FG01-FORGED-BODY-CONTENT"
	forged := "<!-- curbpack-onepager-fp:" + fp + " -->\n" +
		"<html><body><p>" + forgeToken + "</p></body></html>\n"
	if err := os.WriteFile(filepath.Join(out, "buyer-onepager.html"), []byte(forged), 0o644); err != nil {
		t.Fatal(err)
	}

	if err := release.Prepare(opts); err != nil {
		t.Fatal(err)
	}
	rewritten, err := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	got := string(rewritten)
	if strings.Contains(got, forgeToken) {
		t.Fatal("FG-01: Prepare must rewrite forged one-pager that only copied the fingerprint marker")
	}
	if extractFP(got) == "" {
		t.Fatal("rewritten one-pager must still carry a fingerprint marker")
	}
	if !strings.Contains(got, "<dt>result_digest</dt>") {
		t.Fatal("rewritten one-pager must restore provenance body")
	}
}
