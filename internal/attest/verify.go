package attest

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// AllowedSignersRel is retained for source compatibility. Repository-supplied
// keys are not an independent trust policy and are no longer used to verify.
const AllowedSignersRel = ".github/curbpack/allowed_signers"

// VerifySSHSignature verifies the signed state hash, not the truth of its claims.
// The operator must explicitly select an external OpenSSH allowed_signers file
// and principal. Missing policy/tool, invalid input, and timeout return false.
// There is no ambient ssh-agent or repository-key fallback.
func VerifySSHSignature(repoRoot, stateHash, sig string) bool {
	sig = strings.TrimSpace(sig)
	stateHash = strings.TrimSpace(stateHash)
	policy := strings.TrimSpace(os.Getenv("CURBPACK_ALLOWED_SIGNERS"))
	principal := strings.TrimSpace(os.Getenv("CURBPACK_SIGNER_ID"))
	if stateHash == "" || sig == "" || len(stateHash) > 4096 || len(sig) > 64*1024 || strings.HasPrefix(sig, "agent-bind:") || principal == "" || strings.ContainsAny(principal, "\r\n\x00") || !filepath.IsAbs(policy) {
		return false
	}
	resolved, err := filepath.EvalSymlinks(policy)
	if err != nil {
		return false
	}
	if repoRoot != "" {
		root, err := filepath.Abs(repoRoot)
		if err != nil {
			return false
		}
		root, err = filepath.EvalSymlinks(root)
		if err != nil {
			return false
		}
		rel, err := filepath.Rel(root, resolved)
		if err != nil {
			return false
		}
		if rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
			return false
		}
	}
	st, err := os.Stat(resolved)
	if err != nil || !st.Mode().IsRegular() || st.Size() > 1024*1024 {
		return false
	}
	dir, err := os.MkdirTemp("", "curbpack-verify-*")
	if err != nil {
		return false
	}
	defer os.RemoveAll(dir)
	signature := filepath.Join(dir, "signature")
	if err := os.WriteFile(signature, []byte(sig+"\n"), 0600); err != nil {
		return false
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, "ssh-keygen", "-Y", "verify", "-f", resolved, "-I", principal, "-n", "curbpack@attest", "-s", signature)
	cmd.Stdin = strings.NewReader(stateHash)
	return cmd.Run() == nil
}
