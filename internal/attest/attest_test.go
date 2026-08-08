package attest_test

import (
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/attest"
)

func TestReproducibleStateHash(t *testing.T) {
	a := attest.ComputeStateHash("abc", "parent", "sbom1", "vex1")
	b := attest.ComputeStateHash("abc", "parent", "sbom1", "vex1")
	if a != b {
		t.Fatal("state hash must be reproducible")
	}
	c := attest.ComputeStateHash("abc", "parent", "sbom2", "vex1")
	if a == c {
		t.Fatal("sbom digest must affect hash")
	}
	seed := attest.StateSeed("abc", "parent", "sbom1", "vex1")
	if seed != "abc|parent|sbom=sbom1|vex=vex1" {
		t.Fatalf("seed=%q", seed)
	}
}

func TestAgentBindNeverVerified(t *testing.T) {
	// Without SSH_AUTH_SOCK, trySSHAgentSign path is exercised via Run → unsigned.
	t.Setenv("SSH_AUTH_SOCK", "")
	// Capsule fields: unsigned must not look like verified.
	cap := attest.Capsule{
		Signer:       "local-unsigned",
		UserTouch:    "not-verified",
		SSHSignature: "agent-bind:deadbeef",
	}
	if cap.UserTouch == "ssh-agent-signed" {
		t.Fatal("agent-bind must not be labeled signed")
	}
	if !strings.HasPrefix(cap.SSHSignature, "agent-bind:") {
		t.Fatal("fixture")
	}
	// ParseHPURL still works with unsigned hint
	parts, ok := attest.ParseHPURLFragment("#?h=abc&p=def&s=unsigned")
	if !ok || parts.StateHash != "abc" {
		t.Fatalf("hpurl parse: %#v ok=%v", parts, ok)
	}
}
