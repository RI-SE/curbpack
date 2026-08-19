// Package pathjail is the canonical relative-path containment helper for repo trees.
package pathjail

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Join resolves rel under root with symlink-aware containment and .git jail (fail closed).
func Join(root, rel string) (full, slash string, err error) {
	rel = strings.TrimSpace(rel)
	if rel == "" {
		return "", "", fmt.Errorf("empty path")
	}
	if invalidPathChars(rel) {
		return "", "", fmt.Errorf("invalid path characters")
	}
	if filepath.IsAbs(rel) || strings.HasPrefix(filepath.ToSlash(rel), "/") {
		return "", "", fmt.Errorf("absolute path refused")
	}
	clean := filepath.Clean(rel)
	slash = filepath.ToSlash(clean)
	if slash == ".." || strings.HasPrefix(slash, "../") {
		return "", "", fmt.Errorf("path traversal refused")
	}
	if UnderGit(slash) {
		return "", "", fmt.Errorf("path under .git refused")
	}
	rootAbs, err := filepath.Abs(root)
	if err != nil {
		return "", "", err
	}
	full = filepath.Join(root, clean)
	fullAbs, err := filepath.Abs(full)
	if err != nil {
		return "", "", err
	}
	if err := containUnderRoot(rootAbs, fullAbs); err != nil {
		return "", "", err
	}
	if err := containAfterEvalSymlinks(rootAbs, fullAbs); err != nil {
		return "", "", err
	}
	return full, slash, nil
}

// ValidateRel validates a relative path without joining to a repo root.
func ValidateRel(rel string) error {
	_, _, err := Join(string(os.PathSeparator)+"repo", rel)
	return err
}

// UnderGit reports whether slash path is under .git (case-insensitive first segment).
func UnderGit(slash string) bool {
	low := strings.ToLower(slash)
	if low == ".git" {
		return true
	}
	return strings.HasPrefix(low, ".git/")
}

func containUnderRoot(rootAbs, fullAbs string) error {
	sep := string(os.PathSeparator)
	if fullAbs != rootAbs && !strings.HasPrefix(fullAbs, rootAbs+sep) {
		return fmt.Errorf("path escapes repository root")
	}
	return nil
}

func containAfterEvalSymlinks(rootAbs, fullAbs string) error {
	rootEval, err := evalExisting(rootAbs)
	if err != nil {
		return err
	}
	targetEval, err := evalExisting(fullAbs)
	if err != nil {
		return err
	}
	return containUnderRoot(rootEval, targetEval)
}

func evalExisting(path string) (string, error) {
	path = filepath.Clean(path)
	st, lerr := os.Lstat(path)
	if lerr == nil {
		if st.Mode()&os.ModeSymlink != 0 {
			resolved, err := filepath.EvalSymlinks(path)
			if err != nil {
				return "", fmt.Errorf("symlink resolution refused: %w", err)
			}
			return filepath.Abs(resolved)
		}
		return filepath.Abs(path)
	}
	if !os.IsNotExist(lerr) {
		return "", lerr
	}
	parent := filepath.Dir(path)
	if parent == path {
		return filepath.Abs(path)
	}
	parentEval, err := evalExisting(parent)
	if err != nil {
		return "", err
	}
	return filepath.Join(parentEval, filepath.Base(path)), nil
}

// AllowedRel is an independent oracle for fuzz/property tests (must agree with Join).
func AllowedRel(rel string) bool {
	rel = strings.TrimSpace(rel)
	if rel == "" {
		return false
	}
	if invalidPathChars(rel) {
		return false
	}
	if filepath.IsAbs(rel) || strings.HasPrefix(filepath.ToSlash(rel), "/") {
		return false
	}
	clean := filepath.ToSlash(filepath.Clean(rel))
	if clean == ".." || strings.HasPrefix(clean, "../") {
		return false
	}
	if UnderGit(clean) {
		return false
	}
	return true
}

func invalidPathChars(rel string) bool {
	if strings.ContainsRune(rel, 0) {
		return true
	}
	for _, r := range rel {
		if r < 32 {
			return true
		}
	}
	return false
}
