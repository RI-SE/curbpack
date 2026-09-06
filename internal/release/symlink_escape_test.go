package release_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/release"
)

// TestPrepareRefusesReviewPackSymlinkEscape is the behavioral regression for the
// Codex finding: default review-pack as a symlink must not write outside the repo.
func TestPrepareRefusesReviewPackSymlinkEscape(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	repo := t.TempDir()
	outside := t.TempDir()
	initPassingHouse(t, repo)

	if err := os.Symlink(outside, filepath.Join(repo, "review-pack")); err != nil {
		t.Skip(err)
	}

	err := release.Prepare(release.Options{
		RepoRoot:          repo,
		PackIDs:           []string{"house-policy"},
		AllowFailingGates: true,
	})
	if err == nil {
		t.Fatal("expected prepare-release to refuse review-pack symlink escape")
	}
	if !strings.Contains(err.Error(), "escapes") && !strings.Contains(err.Error(), "output destination") && !strings.Contains(err.Error(), "symlink") {
		t.Fatalf("expected containment error, got: %v", err)
	}

	entries, _ := os.ReadDir(outside)
	for _, e := range entries {
		if strings.HasPrefix(e.Name(), "0") || e.Name() == "buyer-onepager.html" || e.Name() == "proof-index.html" {
			t.Fatalf("wrote review-pack artifact outside repo via symlink: %s", e.Name())
		}
	}
}

func TestPrepareDefaultStaysInsideRepo(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	repo := t.TempDir()
	initPassingHouse(t, repo)
	if err := release.Prepare(release.Options{
		RepoRoot:          repo,
		PackIDs:           []string{"house-policy"},
		AllowFailingGates: true,
	}); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(repo, "review-pack", "01-gate-failures.json")); err != nil {
		t.Fatal(err)
	}
}
