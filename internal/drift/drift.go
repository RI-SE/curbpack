package drift

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/pathway"
	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/tty"
)

const (
	docsPathCap              = 12
	actionRecheckShareAttest = "Re-run curbpack check, curbpack share, then human re-attest when ready"
	securityTxtRel           = ".well-known/security.txt"
	schemaVersion            = "curbpack-drift-report:1"
)

// Signal is one informational drift row (never a boolean pass/fail).
type Signal struct {
	ID     string `json:"id"`
	Detail string `json:"detail"`
}

// Report is the multi-signal human checklist output.
type Report struct {
	Schema           string   `json:"schema"`
	Signals          []Signal `json:"signals"`
	SuggestedActions []string `json:"suggested_actions,omitempty"`
}

// Options for drift report generation.
type Options struct {
	RepoRoot string
	JSONOut  bool
	Writer   io.Writer
}

// Run builds a cache-only drift report. Exit code is always 0 (informational).
func Run(opts Options) error {
	root := opts.RepoRoot
	if root == "" {
		var err error
		root, err = gitutil.RepoRoot("")
		if err != nil {
			return err
		}
	}
	w := opts.Writer
	if w == nil {
		w = os.Stdout
	}

	bind, _ := attest.LatestBind(root)
	head, headErr := gitutil.HeadSHA(root)

	var signals []Signal
	var actions []string

	// attest commit vs HEAD
	if !bind.Found {
		signals = append(signals, Signal{ID: "attest_none", Detail: "No human attest bind found — run curbpack attest when ready"})
		actions = append(actions, "Human: curbpack attest after review when ready")
	} else if headErr != nil {
		signals = append(signals, Signal{ID: "attest_bind_present", Detail: "Attest bind at " + truncate(bind.CommitSHA) + " (HEAD unavailable)"})
	} else if bind.CommitSHA != head {
		signals = append(signals, Signal{
			ID:     "attest_commit_behind",
			Detail: fmt.Sprintf("Code moved since bind — bind %s ≠ HEAD %s", truncate(bind.CommitSHA), truncate(head)),
		})
		actions = append(actions, actionRecheckShareAttest)
	} else {
		signals = append(signals, Signal{ID: "attest_commit_current", Detail: "Attest bind matches HEAD (informational only)"})
	}

	// pack Path/Paths vs attest bind (same set as confirm-prose)
	if bind.Found && headErr == nil {
		if sig, changed := docsSinceAttestSignal(root, bind.CommitSHA, head); sig.ID != "" {
			signals = append(signals, sig)
			if changed {
				actions = append(actions, actionRecheckShareAttest)
			}
		}
	}

	// last_check from cache
	payload, cacheOK := release.LoadCachedGatePayload(root)
	if !cacheOK {
		signals = append(signals, Signal{ID: "check_cache_missing", Detail: "No latest_result.json / latest_failure.json — run curbpack check"})
		actions = append(actions, "Run curbpack check to refresh gate cache")
	} else if headErr != nil {
		signals = append(signals, Signal{ID: "check_cache_present", Detail: "Gate cache present (HEAD unavailable for OCC compare)"})
	} else if payload.ConcurrencyControl.ExpectedParentCommitSHA != head {
		signals = append(signals, Signal{
			ID:     "check_commit_stale",
			Detail: fmt.Sprintf("Cache OCC parent %s ≠ HEAD %s", truncate(payload.ConcurrencyControl.ExpectedParentCommitSHA), truncate(head)),
		})
		actions = append(actions, "Run curbpack check to refresh cache for current HEAD")
	} else {
		signals = append(signals, Signal{ID: "check_cache_present", Detail: "Gate cache matches HEAD commit"})
	}

	// share_stale (cache-only fingerprint)
	passed := len(payload.Failures) == 0
	score := payload.ReadinessScore
	if score == 0 && cacheOK {
		score = tty.ScoreFromFailures(len(payload.Failures))
	}
	sig, detail := release.ShareStaleReport(root, bind, score, passed)
	if sig != "" {
		signals = append(signals, Signal{ID: sig, Detail: detail})
		if sig == "share_stale" || sig == "share_no_review_pack" {
			actions = append(actions, "Run curbpack share to refresh buyer-onepager.html")
		}
	}

	// state_hash informational
	if bind.Found && headErr == nil {
		parentHash := gitutil.ParentNoteHash(root, head)
		expected := attest.ComputeStateHash(head, parentHash, bind.SBOMDigest, bind.VEXDigest)
		if bind.StateHash != expected {
			signals = append(signals, Signal{
				ID:     "state_hash_mismatch",
				Detail: fmt.Sprintf("Bind state_hash ≠ ComputeStateHash(HEAD) — informational only (bind %s)", truncate(bind.CommitSHA)),
			})
		} else {
			signals = append(signals, Signal{ID: "state_hash_current", Detail: "Bind state_hash matches HEAD compute (informational only)"})
		}
	}

	// working tree
	dirty, dirtyKnown := workingTreeSignal(root)
	signals = append(signals, dirty)

	if !dirtyKnown && dirty.ID == "working_tree_dirty" {
		actions = append(actions, "Commit or stash changes before attest")
	}

	// security.txt Contact/Expires — optional, not a gate
	signals = append(signals, securityTxtSignals(root)...)

	report := Report{
		Schema:           schemaVersion,
		Signals:          signals,
		SuggestedActions: uniqueStrings(actions),
	}

	if opts.JSONOut {
		enc := json.NewEncoder(w)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Fprintf(w, "Curbpack drift — human checklist (exit 0 always; not a compliance meter)\n\n")
	for _, s := range signals {
		fmt.Fprintf(w, "  • %-30s %s\n", s.ID+":", s.Detail)
	}
	if len(report.SuggestedActions) > 0 {
		fmt.Fprintf(w, "\nSuggested actions:\n")
		for _, a := range report.SuggestedActions {
			fmt.Fprintf(w, "  → %s\n", a)
		}
	}
	return nil
}

func workingTreeSignal(root string) (Signal, bool) {
	_, err := gitutil.ChangedFiles(root)
	if err != nil {
		return Signal{ID: "working_tree_unknown", Detail: "Cannot determine working tree state — fail-safe"}, false
	}
	if gitutil.IsDirty(root) {
		return Signal{ID: "working_tree_dirty", Detail: "Uncommitted changes present"}, true
	}
	return Signal{ID: "working_tree_clean", Detail: "No uncommitted changes (informational)"}, true
}

func docsSinceAttestSignal(root, bindSHA, head string) (Signal, bool) {
	packIDs, err := config.ResolvePackIDs(root, nil)
	if err != nil || len(packIDs) == 0 {
		return Signal{}, false
	}
	paths, err := pathway.ProsePaths(packIDs)
	if err != nil || len(paths) == 0 {
		return Signal{}, false
	}
	changed, err := gitutil.DiffNameOnly(root, bindSHA, head, paths)
	if err != nil {
		return Signal{}, false
	}
	if len(changed) == 0 {
		return Signal{ID: "docs_unchanged_since_attest", Detail: "Pack Path/Paths files unchanged since bind (informational only)"}, false
	}
	detail := "Pack files moved since bind: " + formatPathList(changed, docsPathCap)
	return Signal{ID: "docs_changed_since_attest", Detail: detail}, true
}

func formatPathList(paths []string, cap int) string {
	if cap < 1 {
		cap = docsPathCap
	}
	if len(paths) <= cap {
		return strings.Join(paths, ", ")
	}
	return strings.Join(paths[:cap], ", ") + fmt.Sprintf(" (+%d more)", len(paths)-cap)
}

func securityTxtSignals(root string) []Signal {
	p := filepath.Join(root, filepath.FromSlash(securityTxtRel))
	body, err := os.ReadFile(p)
	if err != nil {
		return nil
	}
	return parseSecurityTxtSignals(string(body), time.Now())
}

func parseSecurityTxtSignals(body string, now time.Time) []Signal {
	var contact, expires string
	for _, line := range strings.Split(body, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, val, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		key = strings.ToLower(strings.TrimSpace(key))
		val = strings.TrimSpace(val)
		switch key {
		case "contact":
			if contact == "" && val != "" {
				contact = val
			}
		case "expires":
			if expires == "" && val != "" {
				expires = val
			}
		}
	}
	var out []Signal
	if contact == "" {
		out = append(out, Signal{ID: "contact_missing", Detail: securityTxtRel + " has no Contact: line (informational, not a gate)"})
	}
	if t, ok := parseSecurityTxtExpires(expires); ok && now.After(t) {
		out = append(out, Signal{ID: "contact_expires_past", Detail: fmt.Sprintf("%s Expires: %s is past (informational, not a gate)", securityTxtRel, expires)})
	}
	return out
}

func parseSecurityTxtExpires(s string) (time.Time, bool) {
	s = strings.TrimSpace(s)
	if s == "" {
		return time.Time{}, false
	}
	for _, layout := range []string{time.RFC3339, time.RFC3339Nano, "2006-01-02"} {
		if t, err := time.Parse(layout, s); err == nil {
			return t, true
		}
	}
	return time.Time{}, false
}

// BindDriftLine returns at most one dim line for check output when bind is behind HEAD.
func BindDriftLine(root string) string {
	bind, _ := attest.LatestBind(root)
	if !bind.Found {
		return ""
	}
	head, err := gitutil.HeadSHA(root)
	if err != nil || bind.CommitSHA == head {
		return ""
	}
	return fmt.Sprintf("attest bind %s behind HEAD %s — see curbpack drift", truncate(bind.CommitSHA), truncate(head))
}

func truncate(s string) string {
	if len(s) > 12 {
		return s[:12] + "…"
	}
	return s
}

func uniqueStrings(in []string) []string {
	seen := map[string]struct{}{}
	var out []string
	for _, s := range in {
		if _, ok := seen[s]; ok {
			continue
		}
		seen[s] = struct{}{}
		out = append(out, s)
	}
	return out
}

// ForbiddenSummaryFields documents fields that must never appear in drift JSON.
var ForbiddenSummaryFields = []string{"aligned", "no_drift", "pass", "green"}

func ContainsForbiddenSummary(report Report) bool {
	b, _ := json.Marshal(report)
	s := strings.ToLower(string(b))
	for _, f := range ForbiddenSummaryFields {
		if strings.Contains(s, `"`+f+`"`) {
			return true
		}
	}
	return false
}
