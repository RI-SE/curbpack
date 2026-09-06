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
	if strings.Contains(rel, `\`) {
		rel = strings.ReplaceAll(rel, `\`, `/`)
	}
	if invalidPathChars(rel) {
		return "", "", fmt.Errorf("invalid path characters")
	}
	if filepath.IsAbs(rel) || strings.HasPrefix(filepath.ToSlash(rel), "/") || IsWindowsAbs(rel) {
		return "", "", fmt.Errorf("absolute path refused")
	}
	clean := filepath.Clean(rel)
	slash = filepath.ToSlash(clean)
	if slash == ".." || strings.HasPrefix(slash, "../") {
		return "", "", fmt.Errorf("path traversal refused")
	}
	if err := refuseWindowsHazardSegments(slash); err != nil {
		return "", "", err
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
	if err := ContainAbs(rootAbs, fullAbs); err != nil {
		return "", "", err
	}
	return full, slash, nil
}

// ContainAbs refuses fullAbs when it escapes rootAbs after symlink evaluation
// or resolves under .git.
func ContainAbs(rootAbs, fullAbs string) error {
	if err := containUnderRoot(rootAbs, fullAbs); err != nil {
		return err
	}
	return containAfterEvalSymlinks(rootAbs, fullAbs)
}

// IsWindowsAbs reports drive-letter and UNC forms even on non-Windows hosts.
func IsWindowsAbs(p string) bool {
	if len(p) >= 3 {
		drive := p[0]
		if (drive >= 'A' && drive <= 'Z') || (drive >= 'a' && drive <= 'z') {
			if p[1] == ':' && (p[2] == '\\' || p[2] == '/') {
				return true
			}
		}
	}
	if strings.HasPrefix(p, `\\`) || strings.HasPrefix(p, `//`) {
		// UNC \\server\share or //server/share (not a single rooted Unix path).
		rest := strings.TrimLeft(p, `\/`)
		return strings.ContainsAny(rest, `\/`)
	}
	return false
}

// NormalizeSegment strips Windows trailing dots/spaces that can alias names.
func NormalizeSegment(seg string) string {
	seg = strings.TrimRight(seg, " .")
	return seg
}

// IsReservedDeviceName reports Windows reserved device basenames (CON, PRN, …).
func IsReservedDeviceName(seg string) bool {
	base := seg
	if i := strings.IndexAny(seg, "."); i >= 0 {
		base = seg[:i]
	}
	base = strings.ToUpper(NormalizeSegment(base))
	switch base {
	case "CON", "PRN", "AUX", "NUL":
		return true
	}
	if len(base) == 4 {
		prefix := base[:3]
		n := base[3]
		if (prefix == "COM" || prefix == "LPT") && n >= '1' && n <= '9' {
			return true
		}
	}
	return false
}

func refuseWindowsHazardSegments(slash string) error {
	for _, seg := range strings.Split(slash, "/") {
		if seg == "" || seg == "." || seg == ".." {
			continue
		}
		if IsReservedDeviceName(seg) {
			return fmt.Errorf("reserved device name refused")
		}
		norm := NormalizeSegment(seg)
		if strings.EqualFold(norm, ".git") {
			return fmt.Errorf("path under .git refused")
		}
	}
	return nil
}

// ValidateRel validates a relative path without joining to a repo root.
func ValidateRel(rel string) error {
	_, _, err := Join(string(os.PathSeparator)+"repo", rel)
	return err
}

// UnderGit reports whether slash path is under .git (case-insensitive; Windows
// trailing-dot/space aliases and backslash separators included).
func UnderGit(slash string) bool {
	slash = filepath.ToSlash(slash)
	for _, p := range strings.Split(slash, "/") {
		if strings.EqualFold(NormalizeSegment(p), ".git") {
			return true
		}
	}
	return false
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
	if err := containUnderRoot(rootEval, targetEval); err != nil {
		return err
	}
	rel, err := filepath.Rel(rootEval, targetEval)
	if err != nil {
		return err
	}
	if UnderGit(filepath.ToSlash(rel)) {
		return fmt.Errorf("resolved path under .git refused")
	}
	return nil
}

func evalExisting(path string) (string, error) {
	path = filepath.Clean(path)
	_, lerr := os.Lstat(path)
	if lerr == nil {
		// EvalSymlinks resolves ancestors too; Lstat on the leaf alone cannot
		// detect a regular file reached through a symlinked directory.
		resolved, err := filepath.EvalSymlinks(path)
		if err != nil {
			return "", fmt.Errorf("symlink resolution refused: %w", err)
		}
		return filepath.Abs(resolved)
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
	if strings.Contains(rel, `\`) {
		rel = strings.ReplaceAll(rel, `\`, `/`)
	}
	if invalidPathChars(rel) {
		return false
	}
	if filepath.IsAbs(rel) || strings.HasPrefix(filepath.ToSlash(rel), "/") || IsWindowsAbs(rel) {
		return false
	}
	clean := filepath.ToSlash(filepath.Clean(rel))
	if clean == ".." || strings.HasPrefix(clean, "../") {
		return false
	}
	if refuseWindowsHazardSegments(clean) != nil {
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
