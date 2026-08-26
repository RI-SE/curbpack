package review

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
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
//
// repoMode selects Detail wording only (bundle bytes / comparison pin unchanged).
func resolveBundleAnchor(bundleRoot, cand string, bundleFiles map[string]struct{}, repoMode bool) (State, string, Cause, string) {
	cand = filepath.ToSlash(strings.TrimSpace(cand))
	if cand == "" {
		return StateUnconfirmed, "empty path", CauseExtractor, ""
	}
	if _, ok := bundleFiles[cand]; ok {
		prefix := "in-bundle path: "
		if repoMode {
			prefix = "in-repo path: "
		}
		return StateConfirmed, prefix + cand, "", cand
	}
	base := filepath.Base(cand)
	if _, ok := bundleFiles[base]; ok {
		// Resolution hit via basename — identity remains cand; closure uses the hit file.
		hit := cand
		if abs, err := jailJoin(bundleRoot, cand); err != nil || fileMissing(abs) {
			// Basename-only hit: prefer the indexed relative path when cand itself is absent.
			if relHit := findIndexedRel(bundleFiles, base); relHit != "" {
				hit = relHit
			} else {
				hit = base
			}
		}
		prefix := "in-bundle basename: "
		if repoMode {
			prefix = "in-repo basename: "
		}
		return StateConfirmed, prefix + cand + " → " + base, "", hit
	}
	abs, err := jailJoin(bundleRoot, cand)
	if err == nil {
		if st, err := os.Lstat(abs); err == nil && st.Mode()&os.ModeSymlink == 0 && !st.IsDir() {
			prefix := "in-bundle relative path: "
			if repoMode {
				prefix = "in-repo relative path: "
			}
			return StateConfirmed, prefix + cand, "", cand
		}
	}
	if looksLikeRepoPath(cand) {
		detail := "repo-shaped path not in bundle: " + cand
		if repoMode {
			detail = "path not found in repo: " + cand
		}
		return StateUnconfirmed, detail, CauseGenuine, ""
	}
	return StateUnconfirmed, "unresolved path: " + cand, CauseExtractor, ""
}

func fileMissing(abs string) bool {
	_, err := os.Lstat(abs)
	return err != nil
}

func findIndexedRel(bundleFiles map[string]struct{}, base string) string {
	var hits []string
	for p := range bundleFiles {
		if strings.Contains(p, "/") && filepath.Base(p) == base {
			hits = append(hits, p)
		}
	}
	sort.Strings(hits)
	if len(hits) == 0 {
		return ""
	}
	return hits[0]
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
