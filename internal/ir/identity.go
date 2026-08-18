package ir

import (
	"os"

	"github.com/afelin/curbpack/internal/paths"
)

const (
	// SourceSelfDeclared is env-only lineage (CURBPACK_AGENT_ID / MODEL_HASH / MANDATE_ID).
	SourceSelfDeclared = "self-declared"
	// SourceBridge means the optional Coreward sock path is present (no new sock ops).
	SourceBridge = "bridge"
	// ReasonNotInstalled is fail-open when CURBPACK_SOCK / CYBERREADY_SOCK is unset.
	ReasonNotInstalled = "not_installed"
	// ReasonUnavailable is fail-open when sock env is set but the path is missing.
	ReasonUnavailable = "unavailable"
)

// ResolveAgentIdentity reads optional lineage env and labels Coreward sock presence.
// Missing sock fail-opens (reason=not_installed) — never a check fail.
// Does not Dial, does not add sock ops, and does not invent merge-allow.
func ResolveAgentIdentity() AgentIdentity {
	id := AgentIdentity{
		AgentID:         paths.Env("AGENT_ID"),
		ModelHash:       paths.Env("MODEL_HASH"),
		ActiveMandateID: paths.Env("MANDATE_ID"),
		Source:          SourceSelfDeclared,
		Reason:          ReasonNotInstalled,
	}
	sockPath := paths.Env("SOCK")
	if sockPath == "" {
		return id
	}
	st, err := os.Stat(sockPath)
	if err != nil || st.IsDir() {
		id.Reason = ReasonUnavailable
		return id
	}
	id.Source = SourceBridge
	id.Reason = ""
	return id
}
