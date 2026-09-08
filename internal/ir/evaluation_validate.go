package ir

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"path"
	"regexp"
	"strings"
	"time"
)

var fullSHA256 = regexp.MustCompile(`^[0-9a-f]{64}$`)
var commitSHA = regexp.MustCompile(`^([0-9a-f]{40}|[0-9a-f]{64})$`)

// ComparisonIdentity binds the method and evaluated scope, excluding input
// contents so a compatible producer can describe a change in findings.
func ComparisonIdentity(i InputIdentity, asOf string) string {
	b, _ := json.Marshal(struct {
		Method      string
		ToolVersion string
		Packs       []PackSource
		Scope       EvaluationScope
		AsOf        string
		TrustPolicy string
	}{i.Method, i.ToolVersion, i.PackSources, i.Scope, asOf, i.TrustPolicy})
	return fmt.Sprintf("%x", sha256.Sum256(b))
}

// ValidateEvaluation is a pure contract check for complete v2 evaluations.
// It neither establishes signer trust nor independently confirms the subject.
func ValidateEvaluation(e Evaluation) error {
	if e.SchemaVersion != EvaluationSchemaVersion {
		return fmt.Errorf("unsupported complete evaluation schema")
	}
	if e.ConformityClaim != ConformityClaimNone {
		return fmt.Errorf("conformity_claim must be none")
	}
	t, err := time.Parse(time.RFC3339, e.AsOf)
	if err != nil || t.UTC().Format(time.RFC3339) != e.AsOf {
		return fmt.Errorf("as_of must be a canonical UTC RFC3339 instant")
	}
	i := e.Identity
	if i.Method != "curbpack-gates:2" || i.ToolVersion == "" || i.TrustPolicy != "none" {
		return fmt.Errorf("unsupported or missing evaluation method/trust policy")
	}
	switch i.SubjectCommitStatus {
	case "claimed":
		if !commitSHA.MatchString(i.SubjectCommit) {
			return fmt.Errorf("claimed subject requires a full commit id")
		}
	case "unavailable":
		if i.SubjectCommit != "" {
			return fmt.Errorf("unavailable subject has a commit claim")
		}
	default:
		return fmt.Errorf("invalid subject commit status")
	}
	if i.PackSources == nil || len(i.PackSources) == 0 || i.Files == nil || i.GitInputs == nil || i.Scope.RuleIDs == nil || i.Scope.SkippedRuleIDs == nil || i.Scope.ChangedPaths == nil || e.Failures == nil {
		return fmt.Errorf("evaluation collections must be present arrays")
	}
	packsSeen := map[string]bool{}
	for _, p := range i.PackSources {
		if p.ID == "" || p.Version == "" || !fullSHA256.MatchString(p.SHA256) || packsSeen[p.ID] {
			return fmt.Errorf("invalid or duplicate pack source")
		}
		packsSeen[p.ID] = true
	}
	filesSeen := map[string]bool{}
	for _, f := range i.Files {
		if filesSeen[f.Path] {
			return fmt.Errorf("duplicate input path")
		}
		filesSeen[f.Path] = true
		if f.State == "refused" {
			if f.SHA256 != "" || !strings.HasPrefix(f.Path, "refused:") || !fullSHA256.MatchString(strings.TrimPrefix(f.Path, "refused:")) {
				return fmt.Errorf("invalid refused input identity")
			}
			continue
		}
		if !validInputPath(f.Path) {
			return fmt.Errorf("invalid input path")
		}
		switch f.State {
		case "file":
			if !fullSHA256.MatchString(f.SHA256) {
				return fmt.Errorf("file input requires SHA-256")
			}
		case "directory", "missing":
			if f.SHA256 != "" {
				return fmt.Errorf("non-file input has content hash")
			}
		default:
			return fmt.Errorf("invalid input state")
		}
	}
	for _, g := range i.GitInputs {
		if !validInputPath(g.Path) {
			return fmt.Errorf("invalid Git input path")
		}
		if g.State != "available" && g.State != "unavailable" {
			return fmt.Errorf("invalid Git input state")
		}
		if g.MetadataSHA256 != "" && !fullSHA256.MatchString(g.MetadataSHA256) {
			return fmt.Errorf("invalid Git metadata digest")
		}
		if g.State == "available" && !fullSHA256.MatchString(g.MetadataSHA256) {
			return fmt.Errorf("available Git input requires metadata digest")
		}
		if g.SinceCommit != "" && !commitSHA.MatchString(g.SinceCommit) {
			return fmt.Errorf("invalid resolved since commit")
		}
		if g.SinceRef == "" && (g.SinceCommit != "" || g.TouchedSince) {
			return fmt.Errorf("since evidence has no reference")
		}
		if g.State == "available" && g.SinceRef != "" && g.SinceCommit == "" {
			return fmt.Errorf("available since evidence requires a resolved commit")
		}
	}
	seenPaths := map[string]bool{}
	for _, p := range i.Scope.ChangedPaths {
		if !validInputPath(p) || seenPaths[p] {
			return fmt.Errorf("invalid or duplicate changed path")
		}
		seenPaths[p] = true
	}
	if i.Scope.Mode != "full" && i.Scope.Mode != "diff" {
		return fmt.Errorf("invalid evaluation scope")
	}
	if i.Scope.Mode == "full" && (len(i.Scope.SkippedRuleIDs) > 0 || len(i.Scope.ChangedPaths) > 0) {
		return fmt.Errorf("full scope cannot contain diff skips")
	}
	evaluated := map[string]bool{}
	for _, id := range i.Scope.RuleIDs {
		if id == "" || evaluated[id] {
			return fmt.Errorf("duplicate or empty evaluated gate")
		}
		evaluated[id] = true
	}
	skipped := map[string]bool{}
	for _, id := range i.Scope.SkippedRuleIDs {
		if id == "" || evaluated[id] || skipped[id] {
			return fmt.Errorf("invalid skipped gate")
		}
		skipped[id] = true
	}
	for _, f := range e.Failures {
		if !evaluated[f.GateID] {
			return fmt.Errorf("finding belongs to an unevaluated gate")
		}
	}
	if e.FailedRules != UniqueFailedGates(e.Failures) || e.EvaluatedRules != len(evaluated) || e.SkippedRules != len(skipped) {
		return fmt.Errorf("gate tallies do not match evaluated scope")
	}
	switch e.Outcome {
	case OutcomePass:
		if len(e.Failures) > 0 || len(skipped) > 0 {
			return fmt.Errorf("pass with findings or skips")
		}
	case OutcomeFindings:
		if len(e.Failures) == 0 || len(skipped) > 0 {
			return fmt.Errorf("findings outcome disagrees with scope")
		}
	case OutcomeIncomplete:
		if len(skipped) == 0 {
			return fmt.Errorf("incomplete outcome requires explicit skips")
		}
	case OutcomeError:
	default:
		return fmt.Errorf("invalid evaluation outcome")
	}
	if !fullSHA256.MatchString(e.ComparisonKey) || e.ComparisonKey != ComparisonIdentity(i, e.AsOf) {
		return fmt.Errorf("comparison identity mismatch")
	}
	return nil
}

func validInputPath(s string) bool {
	if s == "" || strings.HasPrefix(s, "/") || strings.ContainsAny(s, `\\:`) || path.Clean(s) != s || s == ".." || strings.HasPrefix(s, "../") {
		return false
	}
	for _, part := range strings.Split(s, "/") {
		if strings.EqualFold(strings.TrimRight(part, " ."), ".git") {
			return false
		}
	}
	for _, r := range s {
		if r < 32 {
			return false
		}
	}
	return true
}

// ValidateReceipt checks a receipt's binding without inferring signer trust.
func ValidateReceipt(r RunReceipt, e Evaluation, digest string) error {
	if r.SchemaVersion != RunReceiptSchemaVersion || r.EvaluationDigest != digest || r.AsOf != e.AsOf || r.ConformityClaim != ConformityClaimNone {
		return fmt.Errorf("receipt binding mismatch")
	}
	if _, err := time.Parse(time.RFC3339, r.Timestamp); err != nil {
		return fmt.Errorf("invalid receipt timestamp")
	}
	if r.Platform == "" || r.ToolVersion != e.Identity.ToolVersion || r.EvaluationDurationMillis < 0 || r.ConcurrencyControl.ExpectedParentCommitSHA != e.Identity.SubjectCommit {
		return fmt.Errorf("invalid receipt execution metadata")
	}
	switch r.AsOfSource {
	case "explicit", "SOURCE_DATE_EPOCH", "utc-date-default":
	default:
		return fmt.Errorf("invalid as_of source")
	}
	return nil
}
