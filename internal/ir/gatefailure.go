// Package ir holds the canonical GateFailure IR lifted from cyberready_cli_mvp_v3_29.
// Do not redesign these JSON field names — agents and Coreward bridge expect them.
package ir

// ConcurrencyControl carries OCC (optimistic concurrency) fields for Git Notes chaining.
type ConcurrencyControl struct {
	ExpectedParentCommitSHA string `json:"expected_parent_commit_sha"`
	StateVersionToken       string `json:"state_version_token"`
}

// StatechartContext describes where in the compliance state machine the failure occurred.
type StatechartContext struct {
	ActiveParentStatePath   []string `json:"active_parent_state_path"`
	FailedOrthogonalRegions []string `json:"failed_orthogonal_regions"`
}

// AgentIdentity identifies the agent/mandate that triggered validation (optional).
type AgentIdentity struct {
	AgentID         string `json:"agent_id"`
	ModelHash       string `json:"model_hash"`
	ActiveMandateID string `json:"active_mandate_id"`
}

// ASTCoordinates pin a failure to a file/symbol when available.
type ASTCoordinates struct {
	TargetFile    string `json:"target_file"`
	NodePath      string `json:"node_path"`
	TargetSymbol  string `json:"target_symbol"`
	FallbackLines string `json:"fallback_lines"`
}

// Remediation tells an agent or human how to reach the expected state.
type Remediation struct {
	ActionRequired string `json:"action_required"`
	ExpectedState  string `json:"expected_state"`
}

// Failure is a single gate violation.
type Failure struct {
	GateID               string         `json:"gate_id"`
	Severity             string         `json:"severity"`
	Type                 string         `json:"type"`
	SanitizedDescription string         `json:"sanitized_description"`
	ASTCoordinates       ASTCoordinates `json:"ast_coordinates"`
	Remediation          Remediation    `json:"remediation"`
}

// SchemaVersion is the GateFailure JSON IR version for agents (stable contract).
const SchemaVersion = "1"

// GateFailurePayload is the dual-rep IR: JSON for machines, Markdown for agents.
type GateFailurePayload struct {
	SchemaVersion      string             `json:"schema_version"`
	Timestamp          string             `json:"timestamp"`
	ConcurrencyControl ConcurrencyControl `json:"concurrency_control"`
	StatechartContext  StatechartContext  `json:"statechart_context"`
	AgentIdentity      AgentIdentity      `json:"agent_identity"`
	Failures           []Failure          `json:"failures"`
	PackID             string             `json:"pack_id,omitempty"`
	ReadinessScore     int                `json:"readiness_score,omitempty"`
}

// PackageManifest is used for deterministic package.json dependency parsing.
type PackageManifest struct {
	Dependencies    map[string]string `json:"dependencies"`
	DevDependencies map[string]string `json:"devDependencies"`
}
