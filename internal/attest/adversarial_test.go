package attest_test

import (
	"encoding/json"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/gitutil"
)

func TestAttestDisplay_forgedUserTouchNotVerified(t *testing.T) {
	bind := attest.BindInfo{
		Found:        true,
		UserTouch:    "ssh-agent-signed",
		StateHash:    "deadbeef",
		SSHSignature: "",
	}
	line, class, loud := attest.AttestDisplay(bind)
	if !loud || class != "unsigned" {
		t.Fatalf("forged user_touch must stay unsigned: line=%q class=%q loud=%v", line, class, loud)
	}
	if line == "ssh-agent-signed" {
		t.Fatal("must not display verified from user_touch alone")
	}
}

func TestAttestDisplay_agentBindNotVerified(t *testing.T) {
	bind := attest.BindInfo{
		Found:        true,
		UserTouch:    "ssh-agent-signed",
		StateHash:    "abc",
		SSHSignature: "agent-bind:synthetic",
	}
	_, _, loud := attest.AttestDisplay(bind)
	if !loud {
		t.Fatal("agent-bind signature must not show verified")
	}
}

func TestLatestBind_forgedNoteWrongStateHash(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	head, _ := gitutil.HeadSHA(dir)
	cap := attest.Capsule{
		SchemaVersion: attest.SchemaVersion,
		CommitSHA:     head,
		StateHash:     "forged-not-matching-note",
		Signer:        "attacker",
		UserTouch:     "ssh-agent-signed",
		SSHSignature:  "agent-bind:fake",
	}
	body, _ := json.Marshal(cap)
	if err := gitutil.NotesAdd(dir, head, string(body)); err != nil {
		t.Fatal(err)
	}
	bind, err := attest.LatestBind(dir)
	if err != nil {
		t.Fatal(err)
	}
	if bind.CryptoVerified {
		t.Fatal("forged note must not resolve crypto verified")
	}
	line, _, loud := attest.AttestDisplay(bind)
	if !loud || line == "ssh-agent-signed" {
		t.Fatalf("display must refuse forged note: %q loud=%v", line, loud)
	}
}
