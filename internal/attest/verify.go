package attest

import (
	"os"
	"os/exec"
	"strings"
)

// verifyCommand builds *exec.Cmd (overridable in tests).
var verifyCommand = exec.Command

// VerifySSHSignature returns true only when ssh-keygen -Y verify succeeds for stateHash.
// Never trusts user_touch or signer string fields alone.
func VerifySSHSignature(stateHash, sig string) bool {
	sig = strings.TrimSpace(sig)
	stateHash = strings.TrimSpace(stateHash)
	if stateHash == "" || sig == "" || strings.HasPrefix(sig, "agent-bind:") {
		return false
	}
	if strings.TrimSpace(os.Getenv("SSH_AUTH_SOCK")) == "" {
		// Best-effort: verification needs agent-held key matching signature.
		// Without agent, refuse verified display (honest unsigned).
		return false
	}
	list := verifyCommand("ssh-add", "-L")
	out, err := list.Output()
	if err != nil || len(out) == 0 {
		return false
	}
	lines := strings.Split(strings.TrimSpace(string(out)), "\n")
	first := lines[0]

	tmpPub, err := os.CreateTemp("", "curbpack-verify-*.pub")
	if err != nil {
		return false
	}
	defer os.Remove(tmpPub.Name())
	if _, err := tmpPub.WriteString(first + "\n"); err != nil {
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
	if err := cmd.Run(); err != nil {
		return false
	}
	return true
}
