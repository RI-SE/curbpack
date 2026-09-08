package ir

// InputIdentity records what was actually evaluated, without embedding sources.
// SubjectCommit is a producer claim for offline consumers, not independent proof.
type InputIdentity struct {
	Method              string          `json:"method"`
	ToolVersion         string          `json:"tool_version"`
	SubjectCommit       string          `json:"subject_commit,omitempty"`
	SubjectCommitStatus string          `json:"subject_commit_status"`
	PackSources         []PackSource    `json:"pack_sources"`
	Files               []InputFile     `json:"files"`
	GitInputs           []GitInput      `json:"git_inputs"`
	Scope               EvaluationScope `json:"scope"`
	RepoToken           string          `json:"repo_token,omitempty"`
	TrustPolicy         string          `json:"trust_policy"`
}

type PackSource struct {
	ID      string `json:"id"`
	Version string `json:"version"`
	SHA256  string `json:"sha256"`
}

type InputFile struct {
	Path   string `json:"path"`
	State  string `json:"state"` // file | directory | missing | refused
	SHA256 string `json:"sha256,omitempty"`
}

type GitInput struct {
	Path           string `json:"path"`
	State          string `json:"state"`
	MetadataSHA256 string `json:"metadata_sha256,omitempty"`
	SinceRef       string `json:"since_ref,omitempty"`
	SinceCommit    string `json:"since_commit,omitempty"`
	TouchedSince   bool   `json:"touched_since"`
}

type EvaluationScope struct {
	Mode           string   `json:"mode"` // full | diff
	RuleIDs        []string `json:"rule_ids"`
	SkippedRuleIDs []string `json:"skipped_rule_ids"`
	ChangedPaths   []string `json:"changed_paths"`
}
