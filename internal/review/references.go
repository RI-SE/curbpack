package review

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// RefKind is the reference classifier outcome (ClassifierVersion / refclass:1).
type RefKind string

const (
	RefClaim RefKind = "claim"
	RefURL   RefKind = "url"
	RefPath  RefKind = "path"
	RefDrop  RefKind = "drop"
)

// ClassifyReference encodes the reference definition:
//
//	claim — HOUSE|CRA|MEDTECH-…
//	url   — https://…
//	path  — contains / or known extension or exact SECURITY.md / README.md
//	drop  — everything else (markup, booleans, JSON keys, versions, truncated hashes)
func ClassifyReference(token string) RefKind {
	s := strings.TrimSpace(token)
	if s == "" {
		return RefDrop
	}
	if strings.HasPrefix(s, "https://") {
		return RefURL
	}
	if reClaimID.MatchString(s) && reClaimID.FindString(s) == s {
		return RefClaim
	}
	if looksLikeRepoPath(s) {
		return RefPath
	}
	return RefDrop
}

// resolveBundleAnchor lifts the in-repository path resolver idea from
// research/ground into the offline review path: a path is confirmed only when
// it exists inside the received bundle. Repo-only anchors stay unconfirmed
// (no network, no supplier tree).
//
// Identity rule: finding identity is the cleaned relative path as cited.
// Basename fallback affects resolution only — never identity — so docs/x.md
// and x.md remain two keys even if both resolve to the same file.
func resolveBundleAnchor(bundleRoot, cand string, bundleFiles map[string]struct{}) (State, string, Cause) {
	cand = filepath.ToSlash(strings.TrimSpace(cand))
	if cand == "" {
		return StateUnconfirmed, "empty path", CauseExtractor
	}
	if _, ok := bundleFiles[cand]; ok {
		return StateConfirmed, "in-bundle path: " + cand, ""
	}
	base := filepath.Base(cand)
	if _, ok := bundleFiles[base]; ok {
		// Resolution hit via basename — identity remains cand.
		return StateConfirmed, "in-bundle basename: " + cand + " → " + base, ""
	}
	abs, err := jailJoin(bundleRoot, cand)
	if err == nil {
		if st, err := os.Lstat(abs); err == nil && st.Mode()&os.ModeSymlink == 0 && !st.IsDir() {
			return StateConfirmed, "in-bundle relative path: " + cand, ""
		}
	}
	if looksLikeRepoPath(cand) {
		return StateUnconfirmed, "repo-shaped path not in bundle: " + cand, CauseGenuine
	}
	return StateUnconfirmed, "unresolved path: " + cand, CauseExtractor
}

func looksLikeRepoPath(s string) bool {
	if strings.Contains(s, "/") || strings.HasSuffix(s, ".md") || strings.HasSuffix(s, ".json") ||
		strings.HasSuffix(s, ".yml") || strings.HasSuffix(s, ".yaml") ||
		strings.HasSuffix(s, ".go") || strings.HasSuffix(s, ".txt") {
		return true
	}
	return strings.EqualFold(s, "SECURITY.md") || strings.EqualFold(s, "README.md")
}

func referenceKindDetail(kind, detail string) string {
	return fmt.Sprintf("[%s] %s", kind, detail)
}
