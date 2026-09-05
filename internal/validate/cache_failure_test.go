package validate_test

import (
	"github.com/afelin/curbpack/internal/validate"
	"os"
	"path/filepath"
	"testing"
)

func TestCacheWriteFailureCannotReportPass(t *testing.T) {
	dir := t.TempDir()
	mustRealGitValidate(t, dir)
	writeGoodHouse(t, dir)
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0755); err != nil {
		t.Fatal(err)
	}
	// A directory at a required cache file deterministically forces write failure.
	if err := os.WriteFile(filepath.Join(cache, "latest_failure.json"), []byte("prior complete record"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(filepath.Join(cache, "latest_result.json"), 0755); err != nil {
		t.Fatal(err)
	}
	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	prior, readErr := os.ReadFile(filepath.Join(cache, "latest_failure.json"))
	if readErr != nil || string(prior) != "prior complete record" {
		t.Fatal("failed preflight replaced previous cache")
	}
	if err == nil || res.Passed || res.Payload.Outcome != "error" {
		t.Fatalf("cache failure must fail closed: passed=%v err=%v", res.Passed, err)
	}
}

func TestCacheSymlinkDoesNotWriteOutsideRepository(t *testing.T) {
	dir := t.TempDir()
	mustRealGitValidate(t, dir)
	writeGoodHouse(t, dir)
	outside := t.TempDir()
	parent := filepath.Join(dir, ".github", "curbpack")
	if err := os.MkdirAll(parent, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(parent, "cache")); err != nil {
		t.Skip(err)
	}
	_, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	entries, readErr := os.ReadDir(outside)
	if readErr != nil {
		t.Fatal(readErr)
	}
	if err == nil || len(entries) != 0 {
		t.Fatalf("cache escaped: err=%v files=%v", err, entries)
	}
}
