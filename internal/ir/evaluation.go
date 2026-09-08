package ir

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
)

// Versioned crossing contracts (SDD §4.2); v1 is retained for historical readers.
// Complete v2 schemas and goldens live under schema/.
const (
	EvaluationSchemaVersion       = "curbpack-evaluation:2"
	LegacyEvaluationSchemaVersion = "curbpack-evaluation:1"
	RunReceiptSchemaVersion       = "curbpack-run-receipt:2"
	// ConformityClaimNone is the only supported machine claim value (not certification).
	ConformityClaimNone = "none"
)

// Evaluation is the deterministic gate outcome. It excludes wall-clock, agent
// identity, and other operational metadata (those belong on RunReceipt).
type Evaluation struct {
	SchemaVersion      string             `json:"schema_version"`
	AsOf               string             `json:"as_of,omitempty"`
	Identity           InputIdentity      `json:"input_identity,omitempty"`
	ComparisonKey      string             `json:"comparison_key,omitempty"`
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
	SchemaVersion            string             `json:"schema_version"`
	EvaluationDigest         string             `json:"evaluation_digest"`
	Timestamp                string             `json:"timestamp"`
	AsOf                     string             `json:"as_of,omitempty"`
	AgentIdentity            AgentIdentity      `json:"agent_identity"`
	ConformityClaim          string             `json:"conformity_claim"`
	AsOfSource               string             `json:"as_of_source,omitempty"`
	Platform                 string             `json:"platform,omitempty"`
	ToolVersion              string             `json:"tool_version,omitempty"`
	EvaluationDurationMillis int64              `json:"evaluation_duration_ms"`
	ConcurrencyControl       ConcurrencyControl `json:"concurrency_control"`
	StatechartContext        StatechartContext  `json:"statechart_context"`
}

// EvaluationFromLegacy projects a GateFailurePayload onto the canonical evaluation
// surface (drops timestamp and agent identity).
func EvaluationFromLegacy(p GateFailurePayload) Evaluation {
	claim := p.ConformityClaim
	return Evaluation{
		SchemaVersion:      LegacyEvaluationSchemaVersion,
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
	occ, state := e.ConcurrencyControl, e.StatechartContext
	if e.SchemaVersion == EvaluationSchemaVersion {
		occ, state = r.ConcurrencyControl, r.StatechartContext
	}
	payload := GateFailurePayload{
		SchemaVersion:      SchemaVersion,
		Timestamp:          r.Timestamp,
		ConcurrencyControl: occ,
		StatechartContext:  state,
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
	if e.SchemaVersion == EvaluationSchemaVersion {
		payload.EvaluationDigest = r.EvaluationDigest
		payload.ComparisonKey = e.ComparisonKey
		payload.AsOf = e.AsOf
	}
	return payload
}

// MarshalCanonical returns stable JSON for an Evaluation.
func MarshalCanonical(e Evaluation) ([]byte, error) {
	if e.SchemaVersion == "" {
		e.SchemaVersion = EvaluationSchemaVersion
	}
	if e.ConformityClaim == "" && e.SchemaVersion == EvaluationSchemaVersion {
		e.ConformityClaim = ConformityClaimNone
	}
	if e.Failures == nil {
		e.Failures = []Failure{}
	}
	var value any = e
	if e.SchemaVersion == EvaluationSchemaVersion {
		// Explicit projection: no operational metadata can enter canonical bytes.
		value = struct {
			SchemaVersion   string        `json:"schema_version"`
			AsOf            string        `json:"as_of"`
			Identity        InputIdentity `json:"input_identity"`
			ComparisonKey   string        `json:"comparison_key"`
			Failures        []Failure     `json:"failures"`
			PackID          string        `json:"pack_id"`
			ReadinessScore  int           `json:"readiness_score"`
			Outcome         string        `json:"outcome"`
			SkippedRules    int           `json:"skipped_rules"`
			FailedRules     int           `json:"failed_rules"`
			EvaluatedRules  int           `json:"evaluated_rules"`
			ConformityClaim string        `json:"conformity_claim"`
		}{e.SchemaVersion, e.AsOf, e.Identity, e.ComparisonKey, e.Failures, e.PackID, e.ReadinessScore, e.Outcome, e.SkippedRules, e.FailedRules, e.EvaluatedRules, e.ConformityClaim}
	} else if e.SchemaVersion == LegacyEvaluationSchemaVersion {
		// Freeze the historical v1 field set, including its former operational fields.
		value = struct {
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
			ConformityClaim    string             `json:"conformity_claim,omitempty"`
		}{e.SchemaVersion, e.AsOf, e.ConcurrencyControl, e.StatechartContext, e.Failures, e.PackID, e.ReadinessScore, e.Outcome, e.SkippedRules, e.FailedRules, e.EvaluatedRules, e.ConformityClaim}
	} else {
		return nil, fmt.Errorf("unsupported evaluation schema %q", e.SchemaVersion)
	}
	b, err := json.MarshalIndent(value, "", "  ")
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

// ParseCanonical rejects fields or encodings not covered by the canonical digest.
func ParseCanonical(data []byte) (Evaluation, error) {
	var e Evaluation
	if err := json.Unmarshal(data, &e); err != nil {
		return Evaluation{}, err
	}
	canonical, err := MarshalCanonical(e)
	if err != nil {
		return Evaluation{}, err
	}
	if !bytes.Equal(data, canonical) {
		return Evaluation{}, fmt.Errorf("evaluation is not canonical or contains unbound fields")
	}
	if e.SchemaVersion == EvaluationSchemaVersion {
		if err := ValidateEvaluation(e); err != nil {
			return Evaluation{}, err
		}
	}
	return e, nil
}

// ParseReceipt refuses unknown or duplicate fields and noncanonical encodings.
func ParseReceipt(data []byte) (RunReceipt, error) {
	var r RunReceipt
	if err := json.Unmarshal(data, &r); err != nil {
		return r, err
	}
	canonical, err := MarshalReceipt(r)
	if err != nil {
		return r, err
	}
	if !bytes.Equal(data, canonical) {
		return r, fmt.Errorf("noncanonical or unrecognized receipt fields")
	}
	return r, nil
}
