package attest

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/gitutil"
)

// BindInfo is the last human attest bind (not necessarily HEAD).
type BindInfo struct {
	CommitSHA  string // last human bind
	StateHash  string
	Signer     string
	UserTouch  string
	SBOMDigest string
	VEXDigest  string
	Source     string // "hpurl-pointer" | "git-notes"
	Found      bool
}

type hpurlPointer struct {
	StateHash  string `json:"state_hash"`
	CommitSHA  string `json:"commit_sha"`
	SBOMDigest string `json:"sbom_digest"`
	VEXDigest  string `json:"vex_digest"`
}

// HeadCommit returns current HEAD via fixed HeadSHA (propagates errors).
func HeadCommit(repoRoot string) (string, error) {
	return gitutil.HeadSHA(repoRoot)
}

// LatestBind resolves the last human attest bind:
//  1. hpurl-pointer.json → verify note on commit
//  2. LatestNoteCommit (notes list / HEAD walk; curbpack then cyberready)
func LatestBind(repoRoot string) (BindInfo, error) {
	info := BindInfo{}
	ptrPath := filepath.Join(repoRoot, ".github", "curbpack", "evidence", "hpurl-pointer.json")
	if b, err := os.ReadFile(ptrPath); err == nil {
		var ptr hpurlPointer
		if json.Unmarshal(b, &ptr) == nil && strings.TrimSpace(ptr.CommitSHA) != "" {
			if body, err := gitutil.NotesShow(repoRoot, ptr.CommitSHA); err == nil && strings.TrimSpace(body) != "" {
				if cap, ok := parseCapsule(body); ok {
					info = bindFromCapsule(cap, ptr.SBOMDigest, ptr.VEXDigest)
					info.Source = "hpurl-pointer"
					info.Found = true
					return info, nil
				}
			}
		}
	}
	commit, err := gitutil.LatestNoteCommit(repoRoot)
	if err != nil || commit == "" {
		return info, nil // Found: false — not an error
	}
	body, err := gitutil.NotesShow(repoRoot, commit)
	if err != nil || strings.TrimSpace(body) == "" {
		return info, nil
	}
	cap, ok := parseCapsule(body)
	if !ok {
		return info, nil
	}
	info = bindFromCapsule(cap, "", "")
	info.Source = "git-notes"
	info.Found = true
	return info, nil
}

func parseCapsule(body string) (Capsule, bool) {
	var cap Capsule
	if json.Unmarshal([]byte(body), &cap) != nil {
		return Capsule{}, false
	}
	return cap, cap.CommitSHA != "" || cap.StateHash != ""
}

func bindFromCapsule(cap Capsule, sbomOverride, vexOverride string) BindInfo {
	info := BindInfo{
		CommitSHA: cap.CommitSHA,
		StateHash: cap.StateHash,
		Signer:    cap.Signer,
		UserTouch: cap.UserTouch,
	}
	if cap.Evidence != nil {
		info.SBOMDigest = cap.Evidence["sbom_digest"]
		info.VEXDigest = cap.Evidence["vex_digest"]
	}
	if sbomOverride != "" {
		info.SBOMDigest = sbomOverride
	}
	if vexOverride != "" {
		info.VEXDigest = vexOverride
	}
	if info.Signer == "" {
		info.Signer = "local-unsigned"
	}
	if info.UserTouch == "" {
		info.UserTouch = "not-verified"
	}
	return info
}

// AttestDisplay maps BindInfo to buyer-facing attest line/class.
func AttestDisplay(bind BindInfo) (line, class string, unsignedLoud bool) {
	line = "UNSIGNED — not cryptographically verified"
	class = "unsigned"
	unsignedLoud = true
	if !bind.Found {
		return line, class, unsignedLoud
	}
	if bind.UserTouch == "ssh-agent-signed" && bind.StateHash != "" {
		line = "ssh-agent-signed"
		class = "ok"
		unsignedLoud = false
	}
	return line, class, unsignedLoud
}
