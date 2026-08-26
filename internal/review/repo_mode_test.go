package review_test

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/paths"
	"github.com/afelin/curbpack/internal/review"
)

func TestReferencesOnlySkipsStructure(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "docs/note.md",
		Files: map[string]string{
			"docs/note.md": "# note\n`SECURITY.md`\n",
			"SECURITY.md":  "# sec\n",
		},
	})
	rep, err := review.Run(review.Options{
		BundleRoot:     dir,
		Writer:         &bytes.Buffer{},
		ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"},
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range rep.Findings {
		if strings.HasPrefix(f.ID, "structure:") && !strings.Contains(f.ID, "surface-absent") &&
			!strings.Contains(f.ID, "symlink") && !strings.Contains(f.ID, "jail") &&
			!strings.Contains(f.ID, "airlock") && !strings.Contains(f.ID, "bundle-size") {
			// Pack-layer structure findings must not appear.
			if strings.HasPrefix(f.ID, "structure:01-") || strings.HasPrefix(f.ID, "structure:02-") ||
				strings.HasPrefix(f.ID, "structure:03-") || strings.HasPrefix(f.ID, "structure:buyer-") ||
				strings.HasPrefix(f.ID, "structure:04-") || strings.HasPrefix(f.ID, "structure:context-") {
				t.Fatalf("ReferencesOnly must skip pack structure finding %s", f.ID)
			}
		}
		if strings.HasPrefix(f.ID, "digest:") {
			t.Fatalf("ReferencesOnly must skip pack digest finding %s", f.ID)
		}
	}
	foundPath := false
	for _, f := range rep.Findings {
		if f.ID == "reference:path:SECURITY.md" && f.State == review.StateConfirmed {
			foundPath = true
		}
	}
	if !foundPath {
		t.Fatalf("expected confirmed SECURITY.md path, got %+v", rep.Findings)
	}
}

func TestReferencesOnlyStillDeterministic(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "docs/note.md",
		Files: map[string]string{
			"docs/note.md": "# note\n`docs/a.md`\n",
			"docs/a.md":    "a\n",
		},
	})
	var a, b bytes.Buffer
	ra, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &a, ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"}, Full: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	rb, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &b, ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"}, Full: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if a.String() != b.String() {
		t.Fatal("ReferencesOnly markdown not deterministic")
	}
	ja, _ := json.Marshal(ra)
	jb, _ := json.Marshal(rb)
	if !bytes.Equal(ja, jb) {
		t.Fatal("ReferencesOnly JSON not deterministic")
	}
}

func TestReferencesOnlyDigestsStillComputed(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "docs/note.md",
		Files: map[string]string{
			"docs/note.md": "# note\n`SECURITY.md`\n",
			"SECURITY.md":  "# sec\n",
		},
	})
	rep, err := review.Run(review.Options{
		BundleRoot:     dir,
		Writer:         &bytes.Buffer{},
		ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"},
		JSONOut:        true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if rep.BundleDigest == "" || rep.RecordDigest == "" {
		t.Fatalf("digests empty: bundle=%q record=%q", rep.BundleDigest, rep.RecordDigest)
	}
	if rep.DigestScope != review.DigestScopeClosure {
		t.Fatalf("digest_scope=%q want %q", rep.DigestScope, review.DigestScopeClosure)
	}
}

func TestDigestScopeRecorded(t *testing.T) {
	bundle := writeMinimalConsistent(t)
	br, err := review.Run(review.Options{BundleRoot: bundle, Writer: &bytes.Buffer{}, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if br.DigestScope != review.DigestScopeBundle {
		t.Fatalf("bundle digest_scope=%q", br.DigestScope)
	}
	repo := writeFixture(t, fixtureSpec{
		Shape: shapeRepo, Surface: "n.md",
		Files: map[string]string{"n.md": "ok\n"},
	})
	rr, err := review.Run(review.Options{
		BundleRoot: repo, Writer: &bytes.Buffer{}, JSONOut: true,
		ReferencesOnly: true, TriageSurfaces: []string{"n.md"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if rr.DigestScope != review.DigestScopeClosure {
		t.Fatalf("closure digest_scope=%q", rr.DigestScope)
	}
}

func TestSurfaceAbsentEmitted(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape: shapeRepo,
		Files: map[string]string{"present.md": "ok\n"},
	})
	rep, err := review.Run(review.Options{
		BundleRoot:     dir,
		Writer:         &bytes.Buffer{},
		ReferencesOnly: true,
		TriageSurfaces: []string{"present.md", "SECURITY.md"},
	})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, f := range rep.Findings {
		if f.ID == "structure:surface-absent:SECURITY.md" && f.State == review.StateUnconfirmed {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected structure:surface-absent for SECURITY.md, got %+v", rep.Findings)
	}
}

func TestRepoWalkIgnoresDotGit(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "note.md",
		Files: map[string]string{
			"note.md":           "`tracked.md`\n",
			"tracked.md":        "t\n",
			".git/objects/fake": "should-not-enter-closure\n",
		},
		Dirs: []string{".git/objects"},
	})
	rep, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, ReferencesOnly: true,
		TriageSurfaces: []string{"note.md"}, JSONOut: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	// Path under .git must not resolve via the walk index.
	for _, f := range rep.Findings {
		if strings.Contains(f.Detail, ".git/objects") && f.State == review.StateConfirmed {
			t.Fatalf("must not confirm .git path: %+v", f)
		}
	}
	_ = rep.BundleDigest
}

func TestRepoWalkIgnoresCacheAndEvidence(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "note.md",
		Files: map[string]string{
			"note.md": "`ok.md`\n",
			"ok.md":   "ok\n",
			filepath.ToSlash(filepath.Join(paths.CacheRel, "noise.txt")):    "cache\n",
			filepath.ToSlash(filepath.Join(paths.EvidenceRel, "noise.txt")): "ev\n",
			filepath.ToSlash(filepath.Join(paths.GraphRel, "noise.txt")):    "g\n",
		},
	})
	before, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, ReferencesOnly: true,
		TriageSurfaces: []string{"note.md"}, JSONOut: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	// Mutate ignored trees — closure digest must not move.
	mustWrite(t, filepath.Join(dir, paths.CacheRel, "noise.txt"), []byte("cache-CHANGED\n"))
	mustWrite(t, filepath.Join(dir, paths.EvidenceRel, "noise.txt"), []byte("ev-CHANGED\n"))
	mustWrite(t, filepath.Join(dir, paths.GraphRel, "noise.txt"), []byte("g-CHANGED\n"))
	after, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, ReferencesOnly: true,
		TriageSurfaces: []string{"note.md"}, JSONOut: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if before.BundleDigest != after.BundleDigest {
		t.Fatalf("ignore list leak: digest moved %s → %s", before.BundleDigest, after.BundleDigest)
	}
}

func TestClosureDigestStableUnderUnrelatedEdit(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "note.md",
		Files: map[string]string{
			"note.md":   "`hit.md`\n",
			"hit.md":    "hit\n",
			"README.md": "unrelated\n",
		},
	})
	opts := review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, ReferencesOnly: true,
		TriageSurfaces: []string{"note.md"}, JSONOut: true,
	}
	before, err := review.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "README.md"), []byte("unrelated CHANGED\n"))
	after, err := review.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	if before.BundleDigest != after.BundleDigest {
		t.Fatalf("unrelated edit moved closure digest: %s → %s", before.BundleDigest, after.BundleDigest)
	}
	if before.RecordDigest != after.RecordDigest {
		t.Fatalf("unrelated edit moved record_digest with identical findings")
	}
}

func TestClosureDigestChangesWhenResolvedTargetChanges(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "note.md",
		Files: map[string]string{
			"note.md": "`hit.md`\n",
			"hit.md":  "hit\n",
		},
	})
	opts := review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, ReferencesOnly: true,
		TriageSurfaces: []string{"note.md"}, JSONOut: true,
	}
	before, err := review.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "hit.md"), []byte("hit CHANGED\n"))
	after, err := review.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	if before.BundleDigest == after.BundleDigest {
		t.Fatal("resolved target change must move closure digest")
	}
}

func TestClosureDigestChangesWhenUnresolvedTargetAppears(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "note.md",
		Files: map[string]string{
			"note.md": "`later.md`\n",
		},
	})
	opts := review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, ReferencesOnly: true,
		TriageSurfaces: []string{"note.md"}, JSONOut: true,
	}
	before, err := review.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "later.md"), []byte("now present\n"))
	after, err := review.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	if before.BundleDigest == after.BundleDigest {
		t.Fatal("appearing target must move closure digest")
	}
	confirmed := false
	for _, f := range after.Findings {
		if f.ID == "reference:path:later.md" && f.State == review.StateConfirmed {
			confirmed = true
		}
	}
	if !confirmed {
		t.Fatal("later.md should become confirmed")
	}
}

func TestBundleWalkUnchanged(t *testing.T) {
	dir := writeMinimalConsistent(t)
	// Place noise that repo-mode would ignore; bundle mode must still hash everything walked.
	if err := os.MkdirAll(filepath.Join(dir, "node_modules"), 0o755); err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "node_modules", "x.txt"), []byte("noise\n"))
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &bytes.Buffer{}, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if rep.DigestScope != review.DigestScopeBundle {
		t.Fatalf("scope=%q", rep.DigestScope)
	}
	dir2 := writeMinimalConsistent(t)
	rep2, err := review.Run(review.Options{BundleRoot: dir2, Writer: &bytes.Buffer{}, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if rep.BundleDigest == rep2.BundleDigest {
		t.Fatal("bundle mode must include node_modules file in tree digest")
	}
}

func TestRepoWalkRefusesSymlinkedDocDir(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape: shapeRepo,
		Files: map[string]string{
			"real/note.md": "`x.md`\n",
			"x.md":         "x\n",
		},
	})
	link := filepath.Join(dir, "docs")
	if err := os.Symlink(filepath.Join(dir, "real"), link); err != nil {
		t.Skipf("symlink unsupported: %v", err)
	}
	rep, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, ReferencesOnly: true,
		TriageSurfaces: []string{"docs/note.md"},
	})
	if err != nil {
		t.Fatal(err)
	}
	// Surface under symlink may be unreadable (Lstat on join) → surface-absent,
	// and/or walk emits structure:symlink.
	saw := false
	for _, f := range rep.Findings {
		if strings.Contains(f.ID, "symlink") || strings.Contains(f.ID, "surface-absent") {
			saw = true
			if f.State == review.StateConfirmed {
				t.Fatalf("symlink path must not confirm quietly: %+v", f)
			}
		}
	}
	if !saw {
		t.Fatalf("expected symlink or surface-absent finding, got %+v", rep.Findings)
	}
}

func TestModeEquivalenceOnReferences(t *testing.T) {
	// One directory that is both a valid review-pack and a document tree.
	dir := writeFixture(t, fixtureSpec{
		Shape: shapeBundle,
		Files: map[string]string{
			"SECURITY.md": "sec\n",
		},
		Surface: "02-action-report.md",
		Refs: fixtureRefs{
			Paths:  []string{"SECURITY.md", "docs/missing.md"},
			Claims: []string{"HOUSE-SECURITY-MD"},
			URLs:   []string{"https://example.com/docs"},
		},
	})
	surfaces := []string{"02-action-report.md"}
	bundle, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, JSONOut: true,
		TriageSurfaces: surfaces,
	})
	if err != nil {
		t.Fatal(err)
	}
	repo, err := review.Run(review.Options{
		BundleRoot: dir, Writer: &bytes.Buffer{}, JSONOut: true,
		ReferencesOnly: true, TriageSurfaces: surfaces,
	})
	if err != nil {
		t.Fatal(err)
	}
	refKey := func(f review.Finding) string {
		return f.ID + "|" + string(f.State) + "|" + string(f.Cause) + "|" + f.Source
	}
	bundleRefs := map[string]review.Finding{}
	for _, f := range bundle.Findings {
		if strings.HasPrefix(f.ID, "reference:") {
			bundleRefs[refKey(f)] = f
		}
	}
	repoRefs := map[string]review.Finding{}
	for _, f := range repo.Findings {
		if strings.HasPrefix(f.ID, "reference:") {
			repoRefs[refKey(f)] = f
		}
	}
	if len(bundleRefs) == 0 {
		t.Fatal("expected reference findings")
	}
	if len(bundleRefs) != len(repoRefs) {
		t.Fatalf("reference count bundle=%d repo=%d\nbundle=%v\nrepo=%v",
			len(bundleRefs), len(repoRefs), keysOfFindings(bundleRefs), keysOfFindings(repoRefs))
	}
	for k := range bundleRefs {
		if _, ok := repoRefs[k]; !ok {
			t.Fatalf("missing in repo mode: %s", k)
		}
	}
}

func keysOfFindings(m map[string]review.Finding) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
