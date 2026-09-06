// Package outwrite is the shared output containment policy for release packs,
// exports, evidence, and caches.
//
// Policy:
//   - Default destinations stay inside the repository (permitted root = repo).
//   - An explicit output directory is its own permitted root.
//   - Symlink escapes and .git destinations are refused before any write.
//   - Writes are staged, synced, then published by rename.
//   - ExclusiveLock serializes concurrent friendly writers only; O_EXCL is not a
//     hostile filesystem race barrier.
package outwrite

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/afelin/curbpack/internal/pathjail"
)

const (
	// LockFileName is placed under the permitted root for exclusive writers.
	LockFileName = ".curbpack-outwrite.lock"
	// StaleLockAge is when a lock without a live owner may be recovered.
	StaleLockAge = 30 * time.Minute
)

// DirDest resolves a directory destination.
// Empty outDir → dest = repo/defaultRel with permitted root = repo.
// Non-empty outDir → dest = abs(outDir) and permitted root = that directory.
func DirDest(repoRoot, outDir, defaultRel string) (permitted, dest string, err error) {
	repoAbs, err := filepath.Abs(repoRoot)
	if err != nil {
		return "", "", err
	}
	outDir = strings.TrimSpace(outDir)
	if outDir == "" {
		if strings.TrimSpace(defaultRel) == "" {
			return "", "", fmt.Errorf("empty default output path")
		}
		dest, _, err = pathjail.Join(repoAbs, defaultRel)
		if err != nil {
			return "", "", fmt.Errorf("output destination: %w", err)
		}
		return repoAbs, dest, nil
	}
	if pathjail.IsWindowsAbs(outDir) && !filepath.IsAbs(outDir) {
		// Drive/UNC form on a non-Windows host: refuse rather than mis-join.
		return "", "", fmt.Errorf("absolute path refused")
	}
	destAbs, err := filepath.Abs(outDir)
	if err != nil {
		return "", "", err
	}
	if err := ensureContainableDir(destAbs); err != nil {
		return "", "", err
	}
	// Explicit out-dir is its own permitted root; still refuse .git / reserved.
	if err := refuseGitOrReservedAbs(destAbs); err != nil {
		return "", "", err
	}
	return destAbs, destAbs, nil
}

// FileDest resolves a file destination.
// Empty outPath → dest = repo/defaultRel, permitted = repo.
// Relative outPath → dest under repo, permitted = repo.
// Absolute outPath → dest = that path, permitted = its parent directory.
func FileDest(repoRoot, outPath, defaultRel string) (permitted, dest string, err error) {
	repoAbs, err := filepath.Abs(repoRoot)
	if err != nil {
		return "", "", err
	}
	outPath = strings.TrimSpace(outPath)
	if outPath == "" {
		if strings.TrimSpace(defaultRel) == "" {
			return "", "", fmt.Errorf("empty default output path")
		}
		dest, _, err = pathjail.Join(repoAbs, defaultRel)
		if err != nil {
			return "", "", fmt.Errorf("output destination: %w", err)
		}
		return repoAbs, dest, nil
	}
	if pathjail.IsWindowsAbs(outPath) && !filepath.IsAbs(outPath) {
		return "", "", fmt.Errorf("absolute path refused")
	}
	if filepath.IsAbs(outPath) {
		destAbs, err := filepath.Abs(outPath)
		if err != nil {
			return "", "", err
		}
		parent := filepath.Dir(destAbs)
		if err := ensureContainableDir(parent); err != nil {
			return "", "", err
		}
		if err := Contain(parent, destAbs); err != nil {
			return "", "", err
		}
		return parent, destAbs, nil
	}
	dest, _, err = pathjail.Join(repoAbs, outPath)
	if err != nil {
		return "", "", fmt.Errorf("output destination: %w", err)
	}
	return repoAbs, dest, nil
}

// Contain refuses paths that escape permittedRoot after symlink evaluation
// or resolve under .git.
func Contain(permittedRoot, fullPath string) error {
	rootAbs, err := filepath.Abs(permittedRoot)
	if err != nil {
		return err
	}
	fullAbs, err := filepath.Abs(fullPath)
	if err != nil {
		return err
	}
	if err := refuseGitOrReservedAbs(fullAbs); err != nil {
		return err
	}
	return pathjail.ContainAbs(rootAbs, fullAbs)
}

// EnsureDir creates dirAbs when missing, after containment under permittedRoot.
func EnsureDir(permittedRoot, dirAbs string) error {
	if err := Contain(permittedRoot, dirAbs); err != nil {
		return err
	}
	if st, err := os.Lstat(dirAbs); err == nil {
		if st.Mode()&os.ModeSymlink != 0 {
			if err := Contain(permittedRoot, dirAbs); err != nil {
				return err
			}
			return nil
		}
		if !st.IsDir() {
			return fmt.Errorf("output path exists and is not a directory")
		}
		return nil
	} else if !os.IsNotExist(err) {
		return err
	}
	if err := os.MkdirAll(dirAbs, 0o755); err != nil {
		return err
	}
	return Contain(permittedRoot, dirAbs)
}

// WriteFile stages complete contents, syncs, re-checks containment, then renames.
func WriteFile(permittedRoot, destAbs string, data []byte, mode os.FileMode) error {
	if mode == 0 {
		mode = 0o644
	}
	if err := Contain(permittedRoot, destAbs); err != nil {
		return err
	}
	parent := filepath.Dir(destAbs)
	if err := EnsureDir(permittedRoot, parent); err != nil {
		return err
	}
	if st, err := os.Lstat(destAbs); err == nil {
		if st.Mode()&os.ModeSymlink != 0 {
			if err := Contain(permittedRoot, destAbs); err != nil {
				return err
			}
		} else if !st.Mode().IsRegular() {
			return fmt.Errorf("destination must be a regular file")
		}
	} else if !os.IsNotExist(err) {
		return err
	}

	tmp, err := os.CreateTemp(parent, ".curbpack-out-*.tmp")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer func() { _ = os.Remove(tmpName) }()

	if err := tmp.Chmod(mode); err != nil {
		_ = tmp.Close()
		return err
	}
	if _, err := tmp.Write(data); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Sync(); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := Contain(permittedRoot, destAbs); err != nil {
		return err
	}
	return os.Rename(tmpName, destAbs)
}

// ExclusiveLock is a cooperative lock for concurrent friendly writers.
type ExclusiveLock struct {
	path   string
	f      *os.File
	nested bool // same-process re-entry; Release is a no-op
}

// Acquire takes an exclusive lock file under permittedRoot.
// Same-process re-entry (nested writers under one lock) returns a nested handle.
// Stale locks (dead owner PID or older than StaleLockAge) are removed once.
// This does not claim protection against a hostile filesystem race.
func Acquire(permittedRoot string) (*ExclusiveLock, error) {
	rootAbs, err := filepath.Abs(permittedRoot)
	if err != nil {
		return nil, err
	}
	if st, err := os.Lstat(rootAbs); err != nil {
		if os.IsNotExist(err) {
			if err := os.MkdirAll(rootAbs, 0o755); err != nil {
				return nil, err
			}
		} else {
			return nil, err
		}
	} else if !st.IsDir() && st.Mode()&os.ModeSymlink == 0 {
		return nil, fmt.Errorf("lock root is not a directory")
	}
	if err := refuseGitOrReservedAbs(rootAbs); err != nil {
		return nil, err
	}
	lockPath := filepath.Join(rootAbs, LockFileName)
	if err := Contain(rootAbs, lockPath); err != nil {
		return nil, err
	}
	if body, err := os.ReadFile(lockPath); err == nil {
		for _, line := range strings.Split(string(body), "\n") {
			if strings.HasPrefix(line, "pid=") {
				if pid, _ := strconv.Atoi(strings.TrimPrefix(line, "pid=")); pid == os.Getpid() {
					return &ExclusiveLock{path: lockPath, nested: true}, nil
				}
				break
			}
		}
	}
	f, err := os.OpenFile(lockPath, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o644)
	if err != nil {
		if !os.IsExist(err) {
			return nil, err
		}
		if !recoverStaleLock(lockPath) {
			return nil, fmt.Errorf("exclusive writer lock busy at %s (concurrent friendly writers only; not a hostile FS race barrier)", lockPath)
		}
		f, err = os.OpenFile(lockPath, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o644)
		if err != nil {
			return nil, fmt.Errorf("exclusive writer lock busy at %s (concurrent friendly writers only; not a hostile FS race barrier)", lockPath)
		}
	}
	body := fmt.Sprintf("pid=%d\nstarted=%s\nnote=cooperative-lock-not-hostile-fs-barrier\n",
		os.Getpid(), time.Now().UTC().Format(time.RFC3339))
	if _, werr := f.WriteString(body); werr != nil {
		_ = f.Close()
		_ = os.Remove(lockPath)
		return nil, werr
	}
	_ = f.Sync()
	return &ExclusiveLock{path: lockPath, f: f}, nil
}

// Release drops the exclusive lock.
func (l *ExclusiveLock) Release() error {
	if l == nil {
		return nil
	}
	if l.nested {
		return nil
	}
	var err error
	if l.f != nil {
		err = l.f.Close()
		l.f = nil
	}
	if rerr := os.Remove(l.path); rerr != nil && !os.IsNotExist(rerr) && err == nil {
		err = rerr
	}
	return err
}

func recoverStaleLock(path string) bool {
	st, err := os.Lstat(path)
	if err != nil {
		return false
	}
	if st.Mode()&os.ModeSymlink != 0 {
		return os.Remove(path) == nil
	}
	body, err := os.ReadFile(path)
	if err != nil {
		return false
	}
	pid := 0
	for _, line := range strings.Split(string(body), "\n") {
		if strings.HasPrefix(line, "pid=") {
			pid, _ = strconv.Atoi(strings.TrimPrefix(line, "pid="))
			break
		}
	}
	if pid > 0 && !pidAlive(pid) {
		return os.Remove(path) == nil
	}
	if time.Since(st.ModTime()) > StaleLockAge {
		return os.Remove(path) == nil
	}
	return false
}

func ensureContainableDir(dirAbs string) error {
	if err := refuseGitOrReservedAbs(dirAbs); err != nil {
		return err
	}
	if _, err := os.Lstat(dirAbs); err == nil {
		resolved, err := filepath.EvalSymlinks(dirAbs)
		if err != nil {
			return fmt.Errorf("symlink resolution refused: %w", err)
		}
		return refuseGitOrReservedAbs(resolved)
	}
	parent := filepath.Dir(dirAbs)
	if parent == dirAbs {
		return nil
	}
	if _, err := os.Lstat(parent); err == nil {
		resolved, err := filepath.EvalSymlinks(parent)
		if err != nil {
			return fmt.Errorf("symlink resolution refused: %w", err)
		}
		return refuseGitOrReservedAbs(filepath.Join(resolved, filepath.Base(dirAbs)))
	}
	return nil
}

func refuseGitOrReservedAbs(abs string) error {
	slash := filepath.ToSlash(abs)
	for _, p := range strings.Split(slash, "/") {
		if pathjail.IsReservedDeviceName(p) {
			return fmt.Errorf("reserved device name refused")
		}
		if strings.EqualFold(pathjail.NormalizeSegment(p), ".git") {
			return fmt.Errorf("path under .git refused")
		}
	}
	return nil
}
