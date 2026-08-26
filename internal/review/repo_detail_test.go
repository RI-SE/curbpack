package review_test

import (
	"bytes"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

// B2: repo-mode Detail wording only — assert Detail/markdown, not whole JSON.
func TestRepoModeDetailWording(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "docs/note.md",
		Files: map[string]string{
			"docs/note.md": "# note\n`SECURITY.md`\n`docs/missing.md`\n",
			"SECURITY.md":  "# sec\n",
		},
	})
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{
		BundleRoot:     dir,
		Writer:         &buf,
		Full:           true,
		ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"},
	})
	if err != nil {
		t.Fatal(err)
	}
	md := buf.String()
	var confirmed, missing string
	for _, f := range rep.Findings {
		switch f.ID {
		case "reference:path:SECURITY.md":
			confirmed = f.Detail
		case "reference:path:docs/missing.md":
			missing = f.Detail
		}
	}
	if confirmed == "" || missing == "" {
		t.Fatalf("missing findings: confirmed=%q missing=%q findings=%+v", confirmed, missing, rep.Findings)
	}
	if !strings.Contains(confirmed, "in-repo path:") && !strings.Contains(confirmed, "in-repo basename:") && !strings.Contains(confirmed, "in-repo relative path:") {
		t.Fatalf("repo confirmed Detail must use in-repo wording: %q", confirmed)
	}
	if strings.Contains(confirmed, "in-bundle") {
		t.Fatalf("repo confirmed Detail must not say in-bundle: %q", confirmed)
	}
	if !strings.Contains(missing, "path not found in repo:") {
		t.Fatalf("repo missing Detail want path not found in repo: got %q", missing)
	}
	if strings.Contains(missing, "not in bundle") {
		t.Fatalf("repo missing Detail must not say not in bundle: %q", missing)
	}
	if !strings.Contains(md, "in-repo") {
		t.Fatalf("markdown should surface in-repo Detail: %s", md)
	}
	if strings.Contains(md, "repo-shaped path not in bundle") {
		t.Fatalf("markdown must not use bundle-mode genuine wording: %s", md)
	}
}

func TestBundleModeDetailWordingUnchanged(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Surface: "02-action-report.md",
		Refs: fixtureRefs{
			Paths: []string{"docs/does-not-exist-xyz.md"},
		},
	})
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &buf, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, f := range rep.Findings {
		if f.ID == "reference:path:docs/does-not-exist-xyz.md" {
			found = true
			if !strings.Contains(f.Detail, "repo-shaped path not in bundle:") {
				t.Fatalf("bundle genuine Detail unchanged want: %q", f.Detail)
			}
			if strings.Contains(f.Detail, "path not found in repo:") {
				t.Fatalf("bundle must not use repo-mode wording: %q", f.Detail)
			}
		}
		if strings.HasPrefix(f.ID, "reference:path:") && f.State == review.StateConfirmed {
			if strings.Contains(f.Detail, "in-repo ") {
				t.Fatalf("bundle confirmed must not use in-repo wording: %q", f.Detail)
			}
		}
	}
	if !found {
		t.Fatal("expected genuine unresolved path finding in bundle mode")
	}
}

func TestTriageSurfacesAlwaysOnReport(t *testing.T) {
	bundle := writeMinimalConsistent(t)
	rep, err := review.Run(review.Options{BundleRoot: bundle, Writer: &bytes.Buffer{}, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if len(rep.TriageSurfaces) == 0 {
		t.Fatal("triage_surfaces empty on bundle report")
	}
	if rep.SurfacesDigest == "" {
		t.Fatal("surfaces_digest empty on bundle report")
	}
	for i := 1; i < len(rep.TriageSurfaces); i++ {
		if rep.TriageSurfaces[i-1] > rep.TriageSurfaces[i] {
			t.Fatalf("triage_surfaces not sorted: %v", rep.TriageSurfaces)
		}
	}

	repo := writeFixture(t, fixtureSpec{
		Shape: shapeRepo, Surface: "n.md",
		Files: map[string]string{"n.md": "ok\n", "z.md": "z\n"},
	})
	rr, err := review.Run(review.Options{
		BundleRoot: repo, Writer: &bytes.Buffer{}, JSONOut: true,
		ReferencesOnly: true, TriageSurfaces: []string{"z.md", "n.md"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(rr.TriageSurfaces) != 2 || rr.TriageSurfaces[0] != "n.md" || rr.TriageSurfaces[1] != "z.md" {
		t.Fatalf("want sorted [n.md z.md], got %v", rr.TriageSurfaces)
	}
	if rr.SurfacesDigest == "" {
		t.Fatal("surfaces_digest empty on repo report")
	}
}
