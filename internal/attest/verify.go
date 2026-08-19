package attest

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// AllowedSignersRel is the repo-relative path listing public keys permitted to verify attest signatures.
const AllowedSignersRel = ".github/curbpack/allowed_signers"

// verifyCommand builds *exec.Cmd (overridable in tests).
var verifyCommand = exec.Command

// VerifySSHSignature returns true only when ssh-keygen -Y verify succeeds for stateHash.
// Keys are taken from the repo allowed_signers policy when present; otherwise all ssh-add -L keys.
// Never trusts user_touch or signer string fields alone.
func VerifySSHSignature(repoRoot, stateHash, sig string) bool {
	sig = strings.TrimSpace(sig)
	stateHash = strings.TrimSpace(stateHash)
	if stateHash == "" || sig == "" || strings.HasPrefix(sig, "agent-bind:") {
		return false
	}
	for _, keyLine := range verificationKeys(repoRoot) {
		if verifyWithPublicKey(keyLine, stateHash, sig) {
			return true
		}
	}
	return false
}

func verificationKeys(repoRoot string) []string {
	if repoRoot != "" {
		policy := filepath.Join(repoRoot, AllowedSignersRel)
		if b, err := os.ReadFile(policy); err == nil {
			var keys []string
			for _, line := range strings.Split(string(b), "\n") {
				line = strings.TrimSpace(line)
				if line == "" || strings.HasPrefix(line, "#") {
					continue
				}
				keys = append(keys, line)
			}
			if len(keys) > 0 {
				return keys
			}
		}
	}
	return sshAgentPublicKeys()
}

func sshAgentPublicKeys() []string {
	if strings.TrimSpace(os.Getenv("SSH_AUTH_SOCK")) == "" {
		return nil
	}
	list := verifyCommand("ssh-add", "-L")
	out, err := list.Output()
	if err != nil || len(out) == 0 {
		return nil
	}
	var keys []string
	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		line = strings.TrimSpace(line)
		if line != "" {
			keys = append(keys, line)
		}
	}
	return keys
}

func verifyWithPublicKey(pubKeyLine, stateHash, sig string) bool {
	tmpPub, err := os.CreateTemp("", "curbpack-verify-*.pub")
	if err != nil {
		return false
	}
	defer os.Remove(tmpPub.Name())
	if _, err := tmpPub.WriteString(pubKeyLine + "\n"); err != nil {
		_ = tmpPub.Close()
		return false
	}
	_ = tmpPub.Close()

	tmpIn, err := os.CreateTemp("", "curbpack-verify-*.txt")
	if err != nil {
		return false
	}
	defer os.Remove(tmpIn.Name())
	if _, err := tmpIn.WriteString(stateHash); err != nil {
		_ = tmpIn.Close()
		return false
	}
	_ = tmpIn.Close()

	tmpSig := tmpIn.Name() + ".sig"
	defer os.Remove(tmpSig)
	if err := os.WriteFile(tmpSig, []byte(sig+"\n"), 0o644); err != nil {
		return false
	}

	cmd := verifyCommand("ssh-keygen", "-Y", "verify", "-f", tmpPub.Name(), "-n", "curbpack@attest", "-s", tmpSig, tmpIn.Name())
	return cmd.Run() == nil
}
