package attest

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/tty"
)

// Capsule is the Git Notes compliance capsule (Merkle + OCC).
type Capsule struct {
	SchemaVersion   string `json:"schema_version"`
	Timestamp       string `json:"timestamp"`
	CommitSHA       string `json:"commit_sha"`
	StateHash       string `json:"state_hash"`
	ParentStateHash string `json:"parent_state_hash,omitempty"`
	OCCParent       string `json:"expected_parent_commit_sha"`
	Signer          string `json:"signer"`
	SSHSignature    string `json:"ssh_signature,omitempty"`
	UserTouch       string `json:"user_touch"`
	HPURLFragment   string `json:"hpurl_fragment"`
}

// Options for attest.
type Options struct {
	RepoRoot string
	AllowDirty bool
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

	parentHash := gitutil.ParentNoteHash(root, commit)
	seed := fmt.Sprintf("%s|%s|%d", commit, parentHash, time.Now().UnixNano())
	stateHash := fmt.Sprintf("%x", sha256.Sum256([]byte(seed)))

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

	cap := Capsule{
		SchemaVersion:   "v3.29-OCC",
		Timestamp:       time.Now().UTC().Format(time.RFC3339),
		CommitSHA:       commit,
		StateHash:       stateHash,
		ParentStateHash: parentHash,
		OCCParent:       commit,
		Signer:          signer,
		SSHSignature:    sshSig,
		UserTouch:       userTouch,
		HPURLFragment:   fmt.Sprintf("#?h=%s&p=%s&s=%s", stateHash, commit, truncate(sshSig, 32)),
	}

	body, err := json.MarshalIndent(cap, "", "  ")
	if err != nil {
		return Capsule{}, err
	}
	if err := gitutil.NotesAdd(root, commit, string(body)); err != nil {
		return Capsule{}, fmt.Errorf("git notes write: %w", err)
	}

	tty.PrintStatus("Git Notes capsule", true, "refs/notes/cyberready @ "+truncate(commit, 12))
	tty.PrintStatus("HPURL fragment", true, cap.HPURLFragment)
	return cap, nil
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

// trySSHAgentSign best-effort signs via ssh-keygen -Y and SSH_AUTH_SOCK.
func trySSHAgentSign(repoRoot, payload string) (sig string, identity string, ok bool) {
	if strings.TrimSpace(os.Getenv("SSH_AUTH_SOCK")) == "" {
		return "", "", false
	}
	// List identities
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

	// ssh-keygen -Y sign requires allowed signers setup in many environments;
	// fall back to hashing identity material if sign fails.
	cmd := exec.Command("ssh-keygen", "-Y", "sign", "-f", tmpIn.Name(), "-n", "cyberready@attest", tmpIn.Name())
	cmd.Dir = repoRoot
	if err := cmd.Run(); err != nil {
		// Degrade: store fingerprint of public key line as non-crypto binder marker
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
	fmt.Println("====================================================================")
	fmt.Println(tty.C(tty.Dim, "Not a certification — evidence for human review."))
	return nil
}
