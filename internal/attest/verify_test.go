package attest

import (
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestVerifySSHSignature_AllowedSignersPolicy(t *testing.T) {
	skipSSHAgentOnWindows(t)
	root := t.TempDir()
	policyDir := filepath.Join(root, ".github", "curbpack")
	if err := os.MkdirAll(policyDir, 0o755); err != nil {
		t.Fatal(err)
	}
	keyLine := "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeKeyMaterialForCurbpackTests fake@cyberready"
	if err := os.WriteFile(filepath.Join(policyDir, "allowed_signers"), []byte(keyLine+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}

	bin := t.TempDir()
	installFakeVerifySSH(t, bin)
	old := verifyCommand
	verifyCommand = func(name string, arg ...string) *exec.Cmd {
		return exec.Command(filepath.Join(bin, name), arg...)
	}
	t.Cleanup(func() { verifyCommand = old })

	t.Setenv("SSH_AUTH_SOCK", "")
	sig := "FAKE-SSH-SIG:ok namespace=curbpack@attest"
	if !VerifySSHSignature(root, "state-hash-payload", sig) {
		t.Fatal("expected verify via allowed_signers policy without ssh-agent")
	}
	if VerifySSHSignature(root, "state-hash-payload", "agent-bind:synthetic") {
		t.Fatal("agent-bind must not verify")
	}
}

func installFakeVerifySSH(t *testing.T, bin string) {
	t.Helper()
	sshKeygen := `#!/bin/sh
subcmd=""
prev=""
for a in "$@"; do
  if [ "$prev" = "-Y" ]; then subcmd="$a"; fi
  prev="$a"
done
if [ "$subcmd" != "verify" ]; then
  echo "fake ssh-keygen: only verify supported" >&2
  exit 2
fi
sig=""
data=""
prev=""
for a in "$@"; do
  if [ "$prev" = "-s" ]; then sig="$a"; fi
  prev="$a"
done
for a in "$@"; do data="$a"; done
if [ ! -f "$sig" ]; then
  echo "fake ssh-keygen: missing sig file" >&2
  exit 3
fi
if ! grep -q 'FAKE-SSH-SIG' "$sig"; then
  exit 1
fi
exit 0
`
	mustExec(t, filepath.Join(bin, "ssh-keygen"), sshKeygen)
	// ssh-add should not be called when policy file is present; stub anyway.
	mustExec(t, filepath.Join(bin, "ssh-add"), "#!/bin/sh\necho 'should-not-be-used'\n")
}

func TestVerifySSHSignature_FallbackSSHAgent(t *testing.T) {
	skipSSHAgentOnWindows(t)
	bin := t.TempDir()
	keyLine := "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeKeyMaterialForCurbpackTests fake@cyberready"
	installFakeVerifySSH(t, bin)
	mustExec(t, filepath.Join(bin, "ssh-add"), "#!/bin/sh\necho '"+keyLine+"'\n")

	old := verifyCommand
	verifyCommand = func(name string, arg ...string) *exec.Cmd {
		return exec.Command(filepath.Join(bin, name), arg...)
	}
	t.Cleanup(func() { verifyCommand = old })

	t.Setenv("SSH_AUTH_SOCK", filepath.Join(t.TempDir(), "agent.sock"))
	sig := "FAKE-SSH-SIG:ok namespace=curbpack@attest"
	if !VerifySSHSignature("", "state-hash-payload", sig) {
		t.Fatal("expected verify via ssh-add fallback")
	}
}

func TestVerifySSHSignature_RejectsEmpty(t *testing.T) {
	if VerifySSHSignature(t.TempDir(), "", "sig") {
		t.Fatal("empty hash")
	}
	if VerifySSHSignature(t.TempDir(), "hash", "") {
		t.Fatal("empty sig")
	}
	if VerifySSHSignature(t.TempDir(), "hash", "agent-bind:x") {
		t.Fatal("agent-bind prefix")
	}
}
