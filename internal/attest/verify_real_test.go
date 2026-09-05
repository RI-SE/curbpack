package attest

import (
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestVerifySSHSignatureRealOpenSSH(t *testing.T) {
	keygen, err := exec.LookPath("ssh-keygen")
	if err != nil {
		t.Skip("OpenSSH unavailable")
	}
	dir := t.TempDir()
	key := filepath.Join(dir, "key")
	message := filepath.Join(dir, "message")
	run := func(args ...string) {
		t.Helper()
		if out, err := exec.Command(keygen, args...).CombinedOutput(); err != nil {
			t.Fatalf("ssh-keygen: %v %s", err, out)
		}
	}
	run("-q", "-t", "ed25519", "-N", "", "-f", key)
	pub, err := os.ReadFile(key + ".pub")
	if err != nil {
		t.Fatal(err)
	}
	policy := filepath.Join(dir, "allowed_signers")
	if err := os.WriteFile(policy, append([]byte("reviewer "), pub...), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(message, []byte("state-hash-payload"), 0600); err != nil {
		t.Fatal(err)
	}
	run("-Y", "sign", "-f", key, "-n", "curbpack@attest", message)
	sig, err := os.ReadFile(message + ".sig")
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("SSH_AUTH_SOCK", "")
	t.Setenv("CURBPACK_ALLOWED_SIGNERS", policy)
	t.Setenv("CURBPACK_SIGNER_ID", "reviewer")
	root := t.TempDir()
	if !VerifySSHSignature(root, "state-hash-payload", string(sig)) {
		t.Fatal("real OpenSSH signature must verify with independent policy")
	}
	if VerifySSHSignature(root, "tampered", string(sig)) {
		t.Fatal("tampered message verified")
	}
	t.Setenv("CURBPACK_SIGNER_ID", "stranger")
	if VerifySSHSignature(root, "state-hash-payload", string(sig)) {
		t.Fatal("untrusted principal verified")
	}
	t.Setenv("CURBPACK_SIGNER_ID", "reviewer")
	t.Setenv("CURBPACK_ALLOWED_SIGNERS", filepath.Join(dir, "missing"))
	if VerifySSHSignature(root, "state-hash-payload", string(sig)) {
		t.Fatal("missing policy verified")
	}
	t.Setenv("CURBPACK_ALLOWED_SIGNERS", "")
	if VerifySSHSignature(root, "state-hash-payload", string(sig)) {
		t.Fatal("missing external policy verified")
	}
}
