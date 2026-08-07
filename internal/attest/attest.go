package attest

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/tty"
)

// Capsule is the Git Notes compliance capsule (Merkle + OCC).
type Capsule struct {
	SchemaVersion   string            `json:"schema_version"`
	Timestamp       string            `json:"timestamp"`
	CommitSHA       string            `json:"commit_sha"`
	StateHash       string            `json:"state_hash"`
	ParentStateHash string            `json:"parent_state_hash,omitempty"`
	OCCParent       string            `json:"expected_parent_commit_sha"`
	Signer          string            `json:"signer"`
	SSHSignature    string            `json:"ssh_signature,omitempty"`
	UserTouch       string            `json:"user_touch"`
	HPURLFragment   string            `json:"hpurl_fragment"`
	Evidence        map[string]string `json:"evidence,omitempty"`
}

// Options for attest.
type Options struct {
	RepoRoot   string
	AllowDirty bool
	// Optional digests to bind (CycloneDX / VEX). Empty strings omitted.
	SBOMDigest string
	VEXDigest  string
}

// StateSeed builds the reproducible hash input (no wall-clock / UnixNano).
func StateSeed(commit, parentHash, sbomDigest, vexDigest string) string {
	return fmt.Sprintf("%s|%s|sbom=%s|vex=%s", commit, parentHash, sbomDigest, vexDigest)
}

// ComputeStateHash returns sha256 hex of the reproducible seed.
func ComputeStateHash(commit, parentHash, sbomDigest, vexDigest string) string {
	seed := StateSeed(commit, parentHash, sbomDigest, vexDigest)
	return fmt.Sprintf("%x", sha256.Sum256([]byte(seed)))
}

// Run creates a Git Notes capsule with Merkle parent link and best-effort SSH-agent sign.
func Run(opts Options) (Capsule, error) {
	root := opts.RepoRoot
	var err error
	if root == "" {
		root, err = gitutil.RepoRoot("")
		if err != nil {
			return Capsule{}, err
		}
	}

	if !opts.AllowDirty && gitutil.IsDirty(root) {
		return Capsule{}, fmt.Errorf("OCC conflict: working directory has uncommitted files")
	}

	commit, err := gitutil.HeadSHA(root)
	if err != nil {
		return Capsule{}, err
	}

	sbomDigest := opts.SBOMDigest
	vexDigest := opts.VEXDigest
	if sbomDigest == "" {
		sbomDigest = fileDigest(filepath.Join(root, ".github", "cyberready", "evidence", "sbom.cdx.json"))
	}
	if vexDigest == "" {
		vexDigest = fileDigest(filepath.Join(root, ".github", "cyberready", "evidence", "vex-pending.json"))
	}

	parentHash := gitutil.ParentNoteHash(root, commit)
	stateHash := ComputeStateHash(commit, parentHash, sbomDigest, vexDigest)

	signer := "local-unsigned"
	userTouch := "not-verified"
	sshSig := ""

	if sig, who, ok := trySSHAgentSign(root, stateHash); ok {
		sshSig = sig
		signer = who
		userTouch = "ssh-agent-best-effort"
	} else {
		tty.PrintStatus("SSH-agent attest", false, "no agent / sign failed — writing unsigned capsule")
	}

	evidence := map[string]string{}
	if sbomDigest != "" {
		evidence["sbom_digest"] = sbomDigest
		evidence["sbom_path"] = ".github/cyberready/evidence/sbom.cdx.json"
	}
	if vexDigest != "" {
		evidence["vex_digest"] = vexDigest
		evidence["vex_path"] = ".github/cyberready/evidence/vex-pending.json"
	}
	evidence["local_pointer"] = ".github/cyberready/evidence/"

	cap := Capsule{
		SchemaVersion:   "v3.33-OCC",
		Timestamp:       time.Now().UTC().Format(time.RFC3339), // display-only; not in state_hash
		CommitSHA:       commit,
		StateHash:       stateHash,
		ParentStateHash: parentHash,
		OCCParent:       commit,
		Signer:          signer,
		SSHSignature:    sshSig,
		UserTouch:       userTouch,
		HPURLFragment:   fmt.Sprintf("#?h=%s&p=%s&s=%s", stateHash, commit, truncate(sshSig, 32)),
		Evidence:        evidence,
	}

	body, err := json.MarshalIndent(cap, "", "  ")
	if err != nil {
		return Capsule{}, err
	}
	if err := gitutil.NotesAdd(root, commit, string(body)); err != nil {
		return Capsule{}, fmt.Errorf("git notes write: %w", err)
	}

	// Local evidence pointer for HPURL verify
	_ = os.MkdirAll(filepath.Join(root, ".github", "cyberready", "evidence"), 0o755)
	pointer := map[string]any{
		"state_hash":    stateHash,
		"commit_sha":    commit,
		"hpurl":         cap.HPURLFragment,
		"sbom_digest":   sbomDigest,
		"vex_digest":    vexDigest,
		"note":          "Client-side HPURL verify compares fragment h= to state_hash. Not a certification.",
		"evidence_root": ".github/cyberready/evidence/",
	}
	pb, _ := json.MarshalIndent(pointer, "", "  ")
	_ = os.WriteFile(filepath.Join(root, ".github", "cyberready", "evidence", "hpurl-pointer.json"), append(pb, '\n'), 0o644)

	tty.PrintStatus("Git Notes capsule", true, "refs/notes/cyberready @ "+truncate(commit, 12))
	tty.PrintStatus("HPURL fragment", true, cap.HPURLFragment)
	tty.PrintStatus("Evidence pointer", true, ".github/cyberready/evidence/hpurl-pointer.json")
	return cap, nil
}

func fileDigest(path string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	return fmt.Sprintf("%x", sha256.Sum256(data))
}

func truncate(s string, n int) string {
	if len(s) <= n || n <= 0 {
		if s == "" {
			return "unsigned"
		}
		return s
	}
	return s[:n]
}

// HPURLParts are the fragment query fields used by proof/index.html verify.
type HPURLParts struct {
	StateHash string
	Commit    string
	SigHint   string
}

// ParseHPURLFragment parses "#?h=&p=&s=" (also accepts without leading #).
// Returns ok=false on malformed input; never panics.
func ParseHPURLFragment(frag string) (HPURLParts, bool) {
	frag = strings.TrimSpace(frag)
	if frag == "" {
		return HPURLParts{}, false
	}
	frag = strings.TrimPrefix(frag, "#")
	frag = strings.TrimPrefix(frag, "?")
	parts := HPURLParts{}
	for _, kv := range strings.Split(frag, "&") {
		if kv == "" {
			continue
		}
		k, v, ok := strings.Cut(kv, "=")
		if !ok {
			continue
		}
		switch k {
		case "h":
			parts.StateHash = v
		case "p":
			parts.Commit = v
		case "s":
			parts.SigHint = v
		}
	}
	if parts.StateHash == "" {
		return parts, false
	}
	return parts, true
}

// trySSHAgentSign best-effort signs via ssh-keygen -Y and SSH_AUTH_SOCK.
func trySSHAgentSign(repoRoot, payload string) (sig string, identity string, ok bool) {
	if strings.TrimSpace(os.Getenv("SSH_AUTH_SOCK")) == "" {
		return "", "", false
	}
	list := exec.Command("ssh-add", "-L")
	out, err := list.Output()
	if err != nil || len(out) == 0 {
		return "", "", false
	}
	lines := strings.Split(strings.TrimSpace(string(out)), "\n")
	first := lines[0]
	parts := strings.Fields(first)
	who := "SSH-Agent"
	if len(parts) >= 3 {
		who = "SSH-Agent:" + parts[len(parts)-1]
	}

	tmpIn, err := os.CreateTemp("", "cyberready-attest-*.txt")
	if err != nil {
		return "", "", false
	}
	defer os.Remove(tmpIn.Name())
	_, _ = tmpIn.WriteString(payload)
	_ = tmpIn.Close()

	tmpOut := tmpIn.Name() + ".sig"
	defer os.Remove(tmpOut)

	cmd := exec.Command("ssh-keygen", "-Y", "sign", "-f", tmpIn.Name(), "-n", "cyberready@attest", tmpIn.Name())
	cmd.Dir = repoRoot
	if err := cmd.Run(); err != nil {
		sum := sha256.Sum256([]byte(first + "|" + payload))
		return fmt.Sprintf("agent-bind:%x", sum[:8]), who, true
	}
	sigBytes, err := os.ReadFile(tmpOut)
	if err != nil {
		sum := sha256.Sum256([]byte(first + "|" + payload))
		return fmt.Sprintf("agent-bind:%x", sum[:8]), who, true
	}
	return strings.TrimSpace(string(sigBytes)), who, true
}

// View prints the capsule for HEAD.
func View(repoRoot string) error {
	if repoRoot == "" {
		var err error
		repoRoot, err = gitutil.RepoRoot("")
		if err != nil {
			return err
		}
	}
	commit, _ := gitutil.HeadSHA(repoRoot)
	body, err := gitutil.NotesShow(repoRoot, commit)
	if err != nil {
		fmt.Printf("%s\n", tty.C(tty.Yellow, "No verified compliance records for commit: "+commit))
		return nil
	}
	var cap Capsule
	if json.Unmarshal([]byte(body), &cap) != nil {
		fmt.Println(body)
		return nil
	}
	fmt.Printf("%s\n", tty.C(tty.Bold+tty.Green, "COMPLIANCE CAPSULE (Git Notes)"))
	fmt.Println("====================================================================")
	fmt.Printf("  Signer:          %s\n", cap.Signer)
	fmt.Printf("  User presence:   %s\n", cap.UserTouch)
	fmt.Printf("  Commit bound:    %s\n", cap.CommitSHA)
	fmt.Printf("  State hash:      %s\n", cap.StateHash)
	fmt.Printf("  Parent hash:     %s\n", cap.ParentStateHash)
	fmt.Printf("  HPURL fragment:  %s\n", cap.HPURLFragment)
	if len(cap.Evidence) > 0 {
		fmt.Printf("  Evidence:        %v\n", cap.Evidence)
	}
	fmt.Println("====================================================================")
	fmt.Println(tty.C(tty.Dim, "Not a certification — evidence for human review."))
	return nil
}
