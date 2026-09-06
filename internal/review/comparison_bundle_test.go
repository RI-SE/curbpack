package review_test

import (
	"bytes"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

// pinnedComparisonRecordDigest is the expected record_digest for
// testdata/comparison-bundle-2026-1 under MethodVersion 1.3.0 / refclass:2.
//
// Update this pin whenever MethodVersion (or classifier / digest algorithm /
// bundle bytes) changes — method_version is inside the digested record, so a
// bump is an expected deliberate failure, not a mystery breakage.
const pinnedComparisonRecordDigest = "7e7a8de08bef231703953f1457468682d8967ae44448815b3e34e05cb706a2b4"

func TestComparisonBundleDigestPinned(t *testing.T) {
	root := repoRoot(t)
	pack := filepath.Join(root, "testdata", "comparison-bundle-2026-1")
	rep, err := review.Run(review.Options{BundleRoot: pack, Writer: &bytes.Buffer{}, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if rep.RecordDigest != pinnedComparisonRecordDigest {
		t.Fatalf("record_digest=%s want %s (update pin + docs/method when MethodVersion/bundle changes)",
			rep.RecordDigest, pinnedComparisonRecordDigest)
	}
	if rep.MethodVersion != review.MethodVersion {
		t.Fatalf("method_version=%q", rep.MethodVersion)
	}
	if rep.BundleDigest == "" {
		t.Fatal("bundle_digest empty")
	}
	if rep.ConfirmedCount < 15 {
		t.Fatalf("comparison bundle too thin: confirmed=%d", rep.ConfirmedCount)
	}
	if rep.UnconfirmedGenuine < 1 {
		t.Fatal("want at least one genuine unconfirmed reference")
	}
	if rep.UnconfirmedExternal < 1 {
		t.Fatal("want at least one external reference")
	}
}
