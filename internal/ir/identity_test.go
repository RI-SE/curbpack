package ir_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
)

func clearIdentityEnv(t *testing.T) {
	t.Helper()
	t.Setenv("CURBPACK_AGENT_ID", "")
	t.Setenv("CURBPACK_MODEL_HASH", "")
	t.Setenv("CURBPACK_MANDATE_ID", "")
	t.Setenv("CYBERREADY_AGENT_ID", "")
	t.Setenv("CYBERREADY_MODEL_HASH", "")
	t.Setenv("CYBERREADY_MANDATE_ID", "")
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("CYBERREADY_SOCK", "")
}

func TestResolveAgentIdentity_SelfDeclaredNotInstalled(t *testing.T) {
	clearIdentityEnv(t)
	t.Setenv("CURBPACK_AGENT_ID", "agent-x")
	t.Setenv("CURBPACK_MODEL_HASH", "hash-y")
	t.Setenv("CURBPACK_MANDATE_ID", "mandate-z")

	id := ir.ResolveAgentIdentity()
	if id.AgentID != "agent-x" || id.ModelHash != "hash-y" || id.ActiveMandateID != "mandate-z" {
		t.Fatalf("env not applied: %#v", id)
	}
	if id.Source != ir.SourceSelfDeclared {
		t.Fatalf("source=%q want %s", id.Source, ir.SourceSelfDeclared)
	}
	if id.Reason != ir.ReasonNotInstalled {
		t.Fatalf("reason=%q want %s (fail-open, not a gate)", id.Reason, ir.ReasonNotInstalled)
	}
}

func TestResolveAgentIdentity_SockMissingUnavailable(t *testing.T) {
	clearIdentityEnv(t)
	t.Setenv("CURBPACK_AGENT_ID", "agent-x")
	t.Setenv("CURBPACK_SOCK", filepath.Join(t.TempDir(), "missing.sock"))

	id := ir.ResolveAgentIdentity()
	if id.Source != ir.SourceSelfDeclared {
		t.Fatalf("source=%q want self-declared when sock absent", id.Source)
	}
	if id.Reason != ir.ReasonUnavailable {
		t.Fatalf("reason=%q want %s", id.Reason, ir.ReasonUnavailable)
	}
	if id.AgentID != "agent-x" {
		t.Fatalf("env identity must survive fail-open: %#v", id)
	}
}

func TestResolveAgentIdentity_SockPresentBridge(t *testing.T) {
	clearIdentityEnv(t)
	dir := t.TempDir()
	sockPath := filepath.Join(dir, "curbpack.sock")
	if err := os.WriteFile(sockPath, []byte(""), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("CURBPACK_AGENT_ID", "bridge-agent")
	t.Setenv("CURBPACK_MODEL_HASH", "bridge-hash")
	t.Setenv("CURBPACK_MANDATE_ID", "bridge-mandate")
	t.Setenv("CURBPACK_SOCK", sockPath)

	id := ir.ResolveAgentIdentity()
	if id.Source != ir.SourceBridge {
		t.Fatalf("source=%q want %s", id.Source, ir.SourceBridge)
	}
	if id.Reason != "" {
		t.Fatalf("reason=%q want empty when sock present", id.Reason)
	}
	if id.AgentID != "bridge-agent" || id.ModelHash != "bridge-hash" || id.ActiveMandateID != "bridge-mandate" {
		t.Fatalf("bridge still uses env payload (no new sock ops): %#v", id)
	}
}

func TestResolveAgentIdentity_EmptyEnvStillFailOpen(t *testing.T) {
	clearIdentityEnv(t)
	id := ir.ResolveAgentIdentity()
	if id.Source != ir.SourceSelfDeclared || id.Reason != ir.ReasonNotInstalled {
		t.Fatalf("empty env must fail-open: %#v", id)
	}
	if id.AgentID != "" || id.ModelHash != "" || id.ActiveMandateID != "" {
		t.Fatalf("must not invent identity: %#v", id)
	}
}
