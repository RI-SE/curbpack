package attest

import (
	"os"
	"path/filepath"
	"testing"
)

func TestVerifySSHSignatureRejectsRepositoryAndAmbientKeys(t *testing.T) {
	root := t.TempDir()
	dir := filepath.Join(root, ".github", "curbpack")
	if err := os.MkdirAll(dir, 0755); err != nil {
		t.Fatal(err)
	}
	policy := filepath.Join(dir, "allowed_signers")
	if err := os.WriteFile(policy, []byte("reviewer ssh-ed25519 forged\n"), 0600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("CURBPACK_SIGNER_ID", "reviewer")
	t.Setenv("CURBPACK_ALLOWED_SIGNERS", "")
	t.Setenv("SSH_AUTH_SOCK", filepath.Join(t.TempDir(), "agent.sock"))
	if VerifySSHSignature(root, "hash", "sig") {
		t.Fatal("ambient or repository keys trusted")
	}
	t.Setenv("CURBPACK_ALLOWED_SIGNERS", policy)
	if VerifySSHSignature(root, "hash", "sig") {
		t.Fatal("explicit repository-owned policy trusted")
	}
}

func TestVerifySSHSignature_RejectsEmpty(t *testing.T) {
	for _, input := range [][2]string{{"", "sig"}, {"hash", ""}, {"hash", "agent-bind:x"}} {
		if VerifySSHSignature(t.TempDir(), input[0], input[1]) {
			t.Fatal("invalid signature input verified")
		}
	}
}
