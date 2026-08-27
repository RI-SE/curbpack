package review_test

import (
	"bytes"
	"encoding/json"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func TestParentRecordDigestSetBeforeDigestJSON(t *testing.T) {
	root := repoRoot(t)
	pack := filepath.Join(root, "testdata", "comparison-bundle-2026-1")
	prior, err := review.Run(review.Options{BundleRoot: pack, Writer: &bytes.Buffer{}, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if prior.RecordDigest == "" {
		t.Fatal("prior digest empty")
	}
	child, err := review.Run(review.Options{
		BundleRoot: pack, Writer: &bytes.Buffer{}, JSONOut: true, Prior: &prior,
	})
	if err != nil {
		t.Fatal(err)
	}
	if child.ParentRecordDigest != prior.RecordDigest {
		t.Fatalf("parent_record_digest=%q want %q", child.ParentRecordDigest, prior.RecordDigest)
	}
	// Parent must be inside hashed JSON (child digest differs from prior).
	if child.RecordDigest == prior.RecordDigest {
		t.Fatal("child record_digest must change when parent is set")
	}
	raw, _ := json.Marshal(child)
	if !bytes.Contains(raw, []byte(`"parent_record_digest"`)) {
		t.Fatal("json missing parent_record_digest")
	}
}
