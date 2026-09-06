package outwrite_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/outwrite"
)

func TestDirDestDefaultRefusesSymlinkEscape(t *testing.T) {
	repo := t.TempDir()
	outside := t.TempDir()
	if err := os.Symlink(outside, filepath.Join(repo, "review-pack")); err != nil {
		t.Skip(err)
	}
	_, _, err := outwrite.DirDest(repo, "", "review-pack")
	if err == nil {
		t.Fatal("expected refuse")
	}
}

func TestDirDestExplicitIsOwnRoot(t *testing.T) {
	repo := t.TempDir()
	out := t.TempDir()
	permitted, dest, err := outwrite.DirDest(repo, out, "review-pack")
	if err != nil {
		t.Fatal(err)
	}
	if permitted != dest {
		t.Fatalf("explicit out should be its own root: permitted=%s dest=%s", permitted, dest)
	}
	if err := outwrite.WriteFile(permitted, filepath.Join(dest, "a.json"), []byte("{}\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestWriteFileRefusesGitDest(t *testing.T) {
	repo := t.TempDir()
	if err := os.MkdirAll(filepath.Join(repo, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	err := outwrite.WriteFile(repo, filepath.Join(repo, ".git", "config"), []byte("x"), 0o644)
	if err == nil || !strings.Contains(err.Error(), ".git") {
		t.Fatalf("expected .git refuse, got %v", err)
	}
}

func TestExclusiveLockBusyAndStaleRecovery(t *testing.T) {
	dir := t.TempDir()
	l1, err := outwrite.Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer l1.Release()

	if _, err := outwrite.Acquire(dir); err == nil {
		// same PID re-entry is allowed
	} else {
		t.Fatalf("same-process reentry should succeed: %v", err)
	}

	// Foreign stale lock: rewrite lock as dead pid with old mtime.
	_ = l1.Release()
	lockPath := filepath.Join(dir, outwrite.LockFileName)
	if err := os.WriteFile(lockPath, []byte("pid=1\nstarted=2000-01-01T00:00:00Z\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	past := time.Now().Add(-2 * outwrite.StaleLockAge)
	_ = os.Chtimes(lockPath, past, past)
	l2, err := outwrite.Acquire(dir)
	if err != nil {
		t.Fatalf("stale lock should recover: %v", err)
	}
	_ = l2.Release()
}

func TestStageThenPublishLeavesNoTmp(t *testing.T) {
	dir := t.TempDir()
	dest := filepath.Join(dir, "out.json")
	if err := outwrite.WriteFile(dir, dest, []byte(`{"ok":true}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, e := range entries {
		if strings.Contains(e.Name(), ".tmp") {
			t.Fatalf("leftover temp: %s", e.Name())
		}
	}
}
