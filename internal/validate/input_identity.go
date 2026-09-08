package validate

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/buildinfo"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
)

const evaluationMethod = "curbpack-gates:2"

func hashBytes(b []byte) string  { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func hashValue(value any) string { b, _ := json.Marshal(value); return hashBytes(b) }

// captureInputs binds every source used by the current check registry, including
// missing paths and Git metadata. Output/cache paths are not recursively scanned.
// Compare captures before and after evaluation to detect cooperative mutation.
func captureInputs(root string, pack packs.Pack, sources []packs.SourceIdentity, diff bool, changed map[string]struct{}) (ir.InputIdentity, error) {
	identity := ir.InputIdentity{Method: evaluationMethod, ToolVersion: buildinfo.Version, SubjectCommitStatus: "claimed", TrustPolicy: "none", PackSources: []ir.PackSource{}, Files: []ir.InputFile{}, GitInputs: []ir.GitInput{}, Scope: ir.EvaluationScope{Mode: "full", RuleIDs: []string{}, SkippedRuleIDs: []string{}, ChangedPaths: []string{}}}
	head, err := gitutil.HeadSHA(root)
	if err != nil {
		identity.SubjectCommitStatus = "unavailable"
	} else {
		identity.SubjectCommit = head
	}
	for _, p := range sources {
		identity.PackSources = append(identity.PackSources, ir.PackSource{ID: p.ID, Version: p.Version, SHA256: p.SHA256})
	}
	if diff {
		identity.Scope.Mode = "diff"
		for p := range changed {
			identity.Scope.ChangedPaths = append(identity.Scope.ChangedPaths, filepath.ToSlash(filepath.Clean(p)))
		}
		sort.Strings(identity.Scope.ChangedPaths)
	}
	paths := map[string]bool{".curbpack.json": true, ".cyberready.json": true}
	for _, rule := range pack.Rules {
		if diff && !packs.RuleTouchesDiff(rule, changed) {
			identity.Scope.SkippedRuleIDs = append(identity.Scope.SkippedRuleIDs, rule.ID)
			continue
		}
		identity.Scope.RuleIDs = append(identity.Scope.RuleIDs, rule.ID)
		if rule.Path != "" {
			paths[rule.Path] = true
		}
		for _, p := range rule.Paths {
			paths[p] = true
		}
		for _, p := range rule.RequireTreePaths {
			paths[p] = true
		}
		if rule.Check == "npm_dep_ban" || rule.Check == "manifest_dep_ban" {
			paths["package.json"] = true
		}
		if rule.BindRepoToken || rule.Check == "anti_placeholder" {
			paths["package.json"], paths["go.mod"] = true, true
			identity.RepoToken, _ = packs.RepoToken(root)
		}
		if rule.Check == "owned" || rule.Check == "fresh" {
			g := ir.GitInput{Path: filepath.ToSlash(rule.Path), State: "available", SinceRef: rule.SinceRef}
			meta, err := gitutil.FileLastCommit(root, rule.Path)
			if err != nil {
				g.State = "unavailable"
			} else {
				g.MetadataSHA256 = hashValue(meta)
			}
			if rule.SinceRef != "" {
				commit, err := gitutil.ResolveCommit(root, rule.SinceRef)
				if err != nil {
					g.State = "unavailable"
				} else {
					g.SinceCommit = commit
				}
				touched, err := gitutil.FileTouchedSinceRef(root, rule.SinceRef, rule.Path)
				if err != nil {
					g.State = "unavailable"
				} else {
					g.TouchedSince = touched
				}
			}
			identity.GitInputs = append(identity.GitInputs, g)
		}
	}
	ordered := make([]string, 0, len(paths))
	for p := range paths {
		ordered = append(ordered, p)
	}
	sort.Strings(ordered)
	for _, p := range ordered {
		full, rel, err := SafeJoin(root, p)
		if err != nil {
			identity.Files = append(identity.Files, ir.InputFile{Path: "refused:" + hashBytes([]byte(p)), State: "refused"})
			continue
		}
		file := ir.InputFile{Path: rel}
		st, err := os.Stat(full)
		switch {
		case os.IsNotExist(err):
			file.State = "missing"
		case err != nil:
			return ir.InputIdentity{}, fmt.Errorf("input %s: %w", rel, err)
		case st.IsDir():
			file.State = "directory"
		case !st.Mode().IsRegular():
			return ir.InputIdentity{}, fmt.Errorf("input %s is not a regular file or directory", rel)
		default:
			data, err := os.ReadFile(full)
			if err != nil {
				return ir.InputIdentity{}, fmt.Errorf("read input %s: %w", rel, err)
			}
			file.State = "file"
			file.SHA256 = hashBytes(data)
		}
		identity.Files = append(identity.Files, file)
	}
	return identity, nil
}

// comparisonKey binds the method, rule bytes, time and scope; repository input
// contents may change in a trend. Partial/different scopes never share a key.
func comparisonKey(identity ir.InputIdentity, asOf string) string {
	return ir.ComparisonIdentity(identity, asOf)
}

func equivalentInputs(a, b ir.InputIdentity) bool { return hashValue(a) == hashValue(b) }

func canonicalFailures(in []ir.Failure, root string) []ir.Failure {
	// Error messages from filesystem APIs can contain the relocated repository
	// root. Strip only that known prefix; source bytes remain bound by their hash.
	out := append([]ir.Failure(nil), in...)
	abs, _ := filepath.Abs(root)
	for i := range out {
		f := &out[i]
		for _, s := range []*string{&f.SanitizedDescription, &f.Remediation.ActionRequired, &f.Remediation.ExpectedState, &f.ASTCoordinates.TargetFile} {
			*s = strings.ReplaceAll(*s, abs+string(filepath.Separator), "")
		}
	}
	return out
}
