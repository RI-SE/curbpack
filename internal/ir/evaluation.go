package ir

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
)

// Versioned crossing contracts (SDD §4.2). Skeleton for W2; freeze under schema/ in W5.
const (
	EvaluationSchemaVersion = "curbpack-evaluation:1"
	RunReceiptSchemaVersion = "curbpack-run-receipt:1"
	// ConformityClaimNone is the only supported machine claim value (not certification).
	ConformityClaimNone = "none"
)

// Evaluation is the deterministic gate outcome. It excludes wall-clock, agent
// identity, and other operational metadata (those belong on RunReceipt).
type Evaluation struct {
	SchemaVersion      string             `json:"schema_version"`
	AsOf               string             `json:"as_of,omitempty"`
	ConcurrencyControl ConcurrencyControl `json:"concurrency_control"`
	StatechartContext  StatechartContext  `json:"statechart_context"`
	Failures           []Failure          `json:"failures"`
	PackID             string             `json:"pack_id,omitempty"`
	ReadinessScore     int                `json:"readiness_score,omitempty"`
	Outcome            string             `json:"outcome,omitempty"`
	SkippedRules       int                `json:"skipped_rules,omitempty"`
	FailedRules        int                `json:"failed_rules,omitempty"`
	EvaluatedRules     int                `json:"evaluated_rules,omitempty"`
	ConformityClaim    string             `json:"conformity_claim"`
}

// RunReceipt records operational metadata for one evaluation run and hashes the
// canonical evaluation it observed. Receipt bytes are not required to be stable
// across wall-clock seconds when SOURCE_DATE_EPOCH is unset.
type RunReceipt struct {
	SchemaVersion    string        `json:"schema_version"`
	EvaluationDigest string        `json:"evaluation_digest"`
	Timestamp        string        `json:"timestamp"`
	AsOf             string        `json:"as_of,omitempty"`
	AgentIdentity    AgentIdentity `json:"agent_identity"`
	ConformityClaim  string        `json:"conformity_claim"`
}

// EvaluationFromLegacy projects a GateFailurePayload onto the canonical evaluation
// surface (drops timestamp and agent identity).
func EvaluationFromLegacy(p GateFailurePayload) Evaluation {
	claim := p.ConformityClaim
	if claim == "" {
		claim = ConformityClaimNone
	}
	return Evaluation{
		SchemaVersion:      EvaluationSchemaVersion,
		ConcurrencyControl: p.ConcurrencyControl,
		StatechartContext:  p.StatechartContext,
		Failures:           append([]Failure(nil), p.Failures...),
		PackID:             p.PackID,
		ReadinessScore:     p.ReadinessScore,
		Outcome:            p.Outcome,
		SkippedRules:       p.SkippedRules,
		FailedRules:        p.FailedRules,
		EvaluatedRules:     p.EvaluatedRules,
		ConformityClaim:    claim,
	}
}

// LegacyFromEvaluation rebuilds GateFailurePayload for readers that still expect
// the mixed IR (timestamp + agent + findings in one document).
func LegacyFromEvaluation(e Evaluation, r RunReceipt) GateFailurePayload {
	claim := e.ConformityClaim
	if claim == "" {
		claim = ConformityClaimNone
	}
	return GateFailurePayload{
		SchemaVersion:      SchemaVersion,
		Timestamp:          r.Timestamp,
		ConcurrencyControl: e.ConcurrencyControl,
		StatechartContext:  e.StatechartContext,
		AgentIdentity:      r.AgentIdentity,
		Failures:           append([]Failure(nil), e.Failures...),
		PackID:             e.PackID,
		ReadinessScore:     e.ReadinessScore,
		Outcome:            e.Outcome,
		SkippedRules:       e.SkippedRules,
		FailedRules:        e.FailedRules,
		EvaluatedRules:     e.EvaluatedRules,
		ConformityClaim:    claim,
	}
}

// MarshalCanonical returns stable JSON for an Evaluation.
func MarshalCanonical(e Evaluation) ([]byte, error) {
	if e.SchemaVersion == "" {
		e.SchemaVersion = EvaluationSchemaVersion
	}
	if e.ConformityClaim == "" {
		e.ConformityClaim = ConformityClaimNone
	}
	if e.Failures == nil {
		e.Failures = []Failure{}
	}
	b, err := json.MarshalIndent(e, "", "  ")
	if err != nil {
		return nil, err
	}
	return append(b, '\n'), nil
}

// ComputeEvaluationDigest returns sha256 hex of canonical evaluation bytes.
func ComputeEvaluationDigest(e Evaluation) (string, error) {
	b, err := MarshalCanonical(e)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(b)
	return fmt.Sprintf("%x", sum[:]), nil
}

// MarshalReceipt returns JSON for a run receipt (operational; may include wall clock).
func MarshalReceipt(r RunReceipt) ([]byte, error) {
	if r.SchemaVersion == "" {
		r.SchemaVersion = RunReceiptSchemaVersion
	}
	if r.ConformityClaim == "" {
		r.ConformityClaim = ConformityClaimNone
	}
	b, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return nil, err
	}
	return append(b, '\n'), nil
}
