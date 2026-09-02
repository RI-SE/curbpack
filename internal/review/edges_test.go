package review_test

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func edgesFixturePath(t *testing.T) string {
	t.Helper()
	return filepath.Join("testdata", "edges_ctam_example.json")
}

func reportWithInstallFinding() review.Report {
	return review.Report{
		Findings: []review.Finding{
			{ID: "reference:path:scripts/install.sh", State: review.StateConfirmed},
		},
	}
}

func TestValidateEdges_approved_ok(t *testing.T) {
	edges, err := review.LoadEdgesFile(edgesFixturePath(t))
	if err != nil {
		t.Fatal(err)
	}
	rep := reportWithInstallFinding()
	if err := review.ValidateEdges(rep, edges); err != nil {
		t.Fatal(err)
	}
}

func TestValidateEdges_refuse_non_approved(t *testing.T) {
	edges, err := review.LoadEdgesFile(edgesFixturePath(t))
	if err != nil {
		t.Fatal(err)
	}
	edges[0].ReviewState = "confirmed"
	rep := reportWithInstallFinding()
	if err := review.ValidateEdges(rep, edges); err == nil {
		t.Fatal("expected refusal for non-approved review_state")
	}
}

func TestValidateEdges_refuse_unknown_finding(t *testing.T) {
	edges, err := review.LoadEdgesFile(edgesFixturePath(t))
	if err != nil {
		t.Fatal(err)
	}
	rep := review.Report{Findings: []review.Finding{{ID: "reference:path:other"}}}
	if err := review.ValidateEdges(rep, edges); err == nil {
		t.Fatal("expected refusal for unknown finding_id")
	}
}

func TestValidateEdges_refuse_score_field(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "bad.json")
	const raw = `{"edges":[{"gate_id":"G","finding_id":"reference:path:scripts/install.sh","source":"S","reviewed_by":"u","reviewed_at":"2026-01-01T00:00:00Z","review_state":"approved","reviewed_against":{"pack_versions":"p@1","classifier_version":"refclass:2","method_version":"1.3.0"},"confidence":0.9}]}`
	if err := os.WriteFile(path, []byte(raw), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := review.LoadEdgesFile(path); err == nil {
		t.Fatal("expected refusal for unknown confidence field")
	}
}

func TestAttachEdges_record_digest_changes(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "docs/note.md",
		Files: map[string]string{
			"docs/note.md":       "# note\n`scripts/install.sh`\n",
			"scripts/install.sh": "# install\n",
		},
	})
	edges, err := review.LoadEdgesFile(edgesFixturePath(t))
	if err != nil {
		t.Fatal(err)
	}
	r0, err := review.Run(review.Options{
		BundleRoot: dir, Writer: ioDiscard{}, ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"},
	})
	if err != nil {
		t.Fatal(err)
	}
	r1, err := review.Run(review.Options{
		BundleRoot: dir, Writer: ioDiscard{}, ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"}, Edges: edges,
	})
	if err != nil {
		t.Fatal(err)
	}
	if r0.RecordDigest == r1.RecordDigest {
		t.Fatalf("record_digest must include edges: %s vs %s", r0.RecordDigest, r1.RecordDigest)
	}
	if len(r1.Edges) != 1 {
		t.Fatalf("edges: %+v", r1.Edges)
	}
}

func TestWriteJSON_edges_omitempty(t *testing.T) {
	rep := review.Report{Schema: review.SchemaVersion, Findings: []review.Finding{}}
	var buf bytes.Buffer
	if err := review.WriteJSON(rep, &buf); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(buf.String(), `"edges"`) {
		t.Fatalf("edges must be omitted when empty: %s", buf.String())
	}
}

func TestLoadEdgesFile_refuse_symlink(t *testing.T) {
	dir := t.TempDir()
	target := filepath.Join(dir, "real.json")
	if err := os.WriteFile(target, []byte(`{"edges":[]}`), 0o644); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(dir, "link.json")
	if err := os.Symlink(target, link); err != nil {
		t.Skip("symlink unsupported:", err)
	}
	if _, err := review.LoadEdgesFile(link); err == nil {
		t.Fatal("expected symlink refusal")
	}
}

func TestEdgesFile_roundtrip_marshal(t *testing.T) {
	edges, err := review.LoadEdgesFile(edgesFixturePath(t))
	if err != nil {
		t.Fatal(err)
	}
	b, err := json.Marshal(edges[0].ReviewedAgainst.PackVersions)
	if err != nil {
		t.Fatal(err)
	}
	if string(b) != `"house-policy@0.1.0"` {
		t.Fatalf("pack_versions raw: %s", b)
	}
}
