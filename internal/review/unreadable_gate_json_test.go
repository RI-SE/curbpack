package review_test

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

// FG-06: a present but unreadable required gate JSON must not confirm structure
// and then silently drop parse/digest findings (INV-06, INV-07).
func TestUnreadableRequiredGateJSONKeepsParseFindings(t *testing.T) {
	dir := writeMinimalConsistent(t)
	gate := filepath.Join(dir, "01-gate-failures.json")
	if err := os.Chmod(gate, 0o000); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Chmod(gate, 0o644) })

	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &bytes.Buffer{}})
	if err != nil {
		t.Fatal(err)
	}

	var structure *review.Finding
	var parse *review.Finding
	for i := range rep.Findings {
		f := &rep.Findings[i]
		switch f.ID {
		case "structure:01-gate-failures.json":
			structure = f
		case "digest:gate-json-parse":
			parse = f
		}
	}
	if structure == nil {
		t.Fatal("missing structure:01-gate-failures.json finding")
	}
	if structure.State == review.StateConfirmed {
		t.Fatalf("FG-06: unreadable required gate JSON must not confirm structure; got %+v", structure)
	}
	if parse == nil {
		t.Fatal("FG-06: parse finding disappeared for unreadable required gate JSON")
	}
	if parse.State != review.StateContradicted {
		t.Fatalf("FG-06: parse finding must be contradicted; got %+v", parse)
	}
}
