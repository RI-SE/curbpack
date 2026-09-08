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

func TestRunRejectsInvalidPriorBeforeOutput(t *testing.T) {
	for _, damage := range []string{"schema", "contents", "missing"} {
		t.Run(damage, func(t *testing.T) {
			prior := review.Report{Schema: review.SchemaVersion}
			prior.RecordDigest = review.ComputeRecordDigest(prior)
			switch damage {
			case "schema":
				prior.Schema = "unknown"
				prior.RecordDigest = review.ComputeRecordDigest(prior)
			case "contents":
				prior.ConfirmedCount++
			case "missing":
				prior.RecordDigest = ""
			}
			var output bytes.Buffer
			rep, err := review.Run(review.Options{BundleRoot: t.TempDir(), Writer: &output, Prior: &prior})
			if err == nil || rep.RecordDigest != "" || output.Len() != 0 {
				t.Fatalf("invalid baseline produced a report: digest=%q output=%q err=%v", rep.RecordDigest, output.String(), err)
			}
		})
	}
}
