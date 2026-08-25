package review_test

import (
	"bytes"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func TestSampleReviewPackFixture(t *testing.T) {
	root := filepath.Join("..", "..", "testdata", "sample-review-pack")
	if _, err := filepath.Abs(root); err != nil {
		t.Fatal(err)
	}
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: root, Writer: &buf})
	if err != nil {
		t.Fatal(err)
	}
	if review.HasContradictions(rep) {
		t.Fatalf("frozen sample must not contradict: %+v\n%s", rep.Findings, buf.String())
	}
	if rep.ConfirmedCount == 0 || rep.UnconfirmedCount == 0 {
		t.Fatalf("sample should show state mix (confirmed+unconfirmed); got c=%d u=%d", rep.ConfirmedCount, rep.UnconfirmedCount)
	}
	if !strings.Contains(buf.String(), "Document triage only") {
		t.Fatal("missing disclaimer")
	}
}
