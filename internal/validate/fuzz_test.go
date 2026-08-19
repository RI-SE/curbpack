package validate

import (
	"path/filepath"
	"regexp"
	"testing"
	"unicode/utf8"
)

func FuzzSafeJoin(f *testing.F) {
	for _, s := range []string{
		"SECURITY.md",
		"../etc/passwd",
		"/abs",
		"docs/../docs/x",
		"..",
		"a/../../b",
		"okay/path.md",
		"",
		".",
		"a\\b",
		".Git/config",
		"docs/.git/hooks/x",
	} {
		f.Add(s)
	}
	root := f.TempDir()
	f.Fuzz(func(t *testing.T, rel string) {
		if !utf8.ValidString(rel) {
			return
		}
		full, clean, err := SafeJoin(root, rel)
		if err != nil {
			return // refused paths are ok; success-path invariants below
		}
		if filepath.IsAbs(rel) {
			t.Fatalf("abs accepted: %q", rel)
		}
		if clean == ".." || len(clean) >= 3 && clean[:3] == "../" {
			t.Fatalf("traversal clean=%q", clean)
		}
		rootAbs, _ := filepath.Abs(root)
		fullAbs, _ := filepath.Abs(full)
		sep := string(filepath.Separator)
		if fullAbs != rootAbs && !hasPrefixPath(fullAbs, rootAbs+sep) {
			t.Fatalf("escape: full=%q root=%q", fullAbs, rootAbs)
		}
	})
}

func hasPrefixPath(path, prefix string) bool {
	return len(path) >= len(prefix) && path[:len(prefix)] == prefix
}

func FuzzTextForbidRegex(f *testing.F) {
	for _, s := range []string{"TODO", "(a+)+$", "[unclosed", "(?i)secret", ".*", "a{1,100}"} {
		f.Add(s)
	}
	f.Fuzz(func(t *testing.T, pattern string) {
		if !utf8.ValidString(pattern) || len(pattern) > 256 {
			return
		}
		// Must not panic; invalid patterns become gate failures in production.
		_, _ = regexp.Compile(pattern)
	})
}
