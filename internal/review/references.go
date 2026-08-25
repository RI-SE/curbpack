package review

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// resolveBundleAnchor lifts the in-repository path resolver idea from
// research/ground into the offline review path: a path is confirmed only when
// it exists inside the received bundle. Repo-only anchors stay unconfirmed
// (no network, no supplier tree).
//
// Four Phase 1b resolvers in the review path:
//  1. in-bundle anchor (this function)
//  2. pack citation / claim id (HOUSE-|CRA-|MEDTECH-) — see checkReferences
//  3. manifest coordinate (SBOM/VEX digests) — see checkDigests
//  4. external link via research.ValidateSourceURL — recorded, never fetched,
//     never elevated to confirmed
func resolveBundleAnchor(bundleRoot, cand string, bundleFiles map[string]struct{}) (State, string) {
	cand = filepath.ToSlash(strings.TrimSpace(cand))
	if cand == "" {
		return StateUnconfirmed, "empty path"
	}
	if _, ok := bundleFiles[cand]; ok {
		return StateConfirmed, "in-bundle path: " + cand
	}
	base := filepath.Base(cand)
	if _, ok := bundleFiles[base]; ok {
		return StateConfirmed, "in-bundle basename: " + cand + " → " + base
	}
	abs := filepath.Join(bundleRoot, filepath.FromSlash(cand))
	if st, err := os.Stat(abs); err == nil && !st.IsDir() {
		return StateConfirmed, "in-bundle relative path: " + cand
	}
	if looksLikeRepoPath(cand) {
		return StateUnconfirmed, "repo-shaped path not in bundle: " + cand
	}
	return StateUnconfirmed, "unresolved path: " + cand
}

func referenceKindDetail(kind, detail string) string {
	return fmt.Sprintf("[%s] %s", kind, detail)
}
