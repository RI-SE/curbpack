package redact

import (
	"fmt"
	"strings"
)

// Counts are public gate tallies for human/agent surfaces. They are not a grade.
type Counts struct {
	Failed    int
	Evaluated int
	Skipped   int
}

// FromRules builds Counts from failure count, skipped rules, and total pack rules.
func FromRules(failed, skipped, totalRules int) Counts {
	if failed < 0 {
		failed = 0
	}
	if skipped < 0 {
		skipped = 0
	}
	evaluated := totalRules - skipped
	if evaluated < 0 {
		evaluated = 0
	}
	return Counts{Failed: failed, Evaluated: evaluated, Skipped: skipped}
}

// Line is the stable public tally line (no percent, no thermometer).
func (c Counts) Line(gatesOpen bool) string {
	state := "gates=green"
	if gatesOpen {
		state = "gates=open"
	}
	return fmt.Sprintf("failed=%d evaluated=%d skipped=%d %s", c.Failed, c.Evaluated, c.Skipped, state)
}

// SummaryMarkdown is a bullet line for action reports / context packs.
func (c Counts) SummaryMarkdown() string {
	return fmt.Sprintf("- **Failed / evaluated / skipped:** %d / %d / %d\n", c.Failed, c.Evaluated, c.Skipped)
}

// Compatible reports whether two eval snapshots may be compared for a trend.
func Compatible(packA, packB, schemaA, schemaB string) bool {
	packA = strings.TrimSpace(packA)
	packB = strings.TrimSpace(packB)
	if packA == "" || packB == "" {
		return false
	}
	if packA != packB {
		return false
	}
	schemaA = strings.TrimSpace(schemaA)
	schemaB = strings.TrimSpace(schemaB)
	if schemaA != "" && schemaB != "" && schemaA != schemaB {
		return false
	}
	return true
}

// TrendLine returns at most one quiet delta when priors are compatible.
func TrendLine(priorOK bool, priorPack, nowPack, priorSchema, nowSchema string, priorFailed, nowFailed int) string {
	if !priorOK || !Compatible(priorPack, nowPack, priorSchema, nowSchema) {
		return ""
	}
	if priorFailed != nowFailed {
		return fmt.Sprintf("Δ failed %d→%d · evidence cache updated", priorFailed, nowFailed)
	}
	return "gates tally unchanged · evidence cache updated"
}
