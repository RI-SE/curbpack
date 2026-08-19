package exportx

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/instrument"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/pathway"
	"github.com/afelin/curbpack/internal/remediation"
	"github.com/afelin/curbpack/internal/research"
	"github.com/afelin/curbpack/internal/validate"
)

const (
	contextPackSchema   = "1"
	contextPackMaxFails = 12
	contextPackNote     = "ContextPack for assistants — structural evidence for human review. Not a conformity assessment, CE mark, or certification. Re-run curbpack check before claiming fixed. Pathway confirms/attest are human-only."
)

// ContextFailure is a washed top finding for assistants.
type ContextFailure struct {
	GateID      string `json:"gate_id"`
	Severity    string `json:"severity"`
	Description string `json:"description"`
	TargetFile  string `json:"target_file,omitempty"`
	ActionHint  string `json:"action_hint,omitempty"`
}

// ContextInstrument is a washed instrument snapshot (+ optional Δ).
type ContextInstrument struct {
	DepsCount   int    `json:"deps_count"`
	DepsFP      string `json:"deps_fp,omitempty"`
	SecretHits  int    `json:"secret_hits"`
	DepsAdded   int    `json:"deps_added,omitempty"`
	DepsRemoved int    `json:"deps_removed,omitempty"`
	Note        string `json:"note"`
}

// ContextRemediationHint is a remediations.json row washed for assistants.
type ContextRemediationHint struct {
	GateID  string `json:"gate_id"`
	File    string `json:"file,omitempty"`
	Action  string `json:"action,omitempty"`
	Snippet string `json:"snippet,omitempty"`
}

// ContextPathway is additive warm-start status for assistants (not a gate input).
type ContextPathway struct {
	Phase          string `json:"phase,omitempty"`
	ParentPath     string `json:"parent_path,omitempty"`
	NextVerb       string `json:"next_verb,omitempty"`
	NextCmd        string `json:"next_cmd,omitempty"`
	NextNote       string `json:"next_note,omitempty"`
	PacksConfirmed bool   `json:"packs_confirmed"`
	ProseOwned     bool   `json:"prose_owned"`
	ShareReviewed  bool   `json:"share_reviewed"`
	Note           string `json:"note"`
}

// ContextPack is one assistant-facing artifact (JSON + Markdown summary).
type ContextPack struct {
	SchemaVersion        string                   `json:"schema_version"`
	Note                 string                   `json:"note"`
	PackIDs              []string                 `json:"pack_ids"`
	ReadinessScore       int                      `json:"readiness_score"`
	OK                   bool                     `json:"ok"`
	Failures             []ContextFailure         `json:"failures"`
	Instrument           ContextInstrument        `json:"instrument"`
	RemediationHints     []ContextRemediationHint `json:"remediation_hints"`
	Pathway              *ContextPathway          `json:"pathway,omitempty"`
	AgentIdentity        ir.AgentIdentity         `json:"agent_identity,omitempty"`
	Paths                map[string]string        `json:"paths"`
	CertificationClaimed bool                     `json:"certification_claimed"`
}

// WriteContextPack builds context-pack.json (+ .md) from cache IR when present,
// otherwise one quiet validate. Reuses explain-packet wash helpers.
func WriteContextPack(root string, packIDs []string, outPath string) (string, error) {
	payload, score, ok, usedCache, err := loadOrValidatePayload(root, packIDs)
	if err != nil {
		return "", err
	}
	_ = usedCache

	ids := packIDs
	if len(ids) == 0 {
		ids = nonzeroPacks(strings.Split(payload.PackID, ","))
	}

	prior, hadPrior := instrument.Load(root)
	snap := instrument.Compute(root)
	_ = instrument.Write(root, snap)
	added, removed := 0, 0
	if hadPrior {
		added, removed = instrument.DepDelta(prior, snap)
	}

	cache, _ := remediation.Load(root)
	hintIDs := make([]string, 0, len(cache.Entries))
	for id := range cache.Entries {
		hintIDs = append(hintIDs, id)
	}
	sort.Strings(hintIDs)
	hints := make([]ContextRemediationHint, 0, len(hintIDs))
	for _, id := range hintIDs {
		e := cache.Entries[id]
		hints = append(hints, ContextRemediationHint{
			GateID:  e.GateID,
			File:    relativizePath(e.File, root),
			Action:  sanitizeText(e.Action, root),
			Snippet: sanitizeText(truncate(e.Snippet, 240), root),
		})
	}

	failures := sanitizeFailures(payload.Failures, root)
	top := make([]ContextFailure, 0, contextPackMaxFails)
	for i, f := range failures {
		if i >= contextPackMaxFails {
			break
		}
		top = append(top, ContextFailure{
			GateID:      f.GateID,
			Severity:    f.Severity,
			Description: f.SanitizedDescription,
			TargetFile:  f.ASTCoordinates.TargetFile,
			ActionHint:  f.Remediation.ActionRequired,
		})
	}
	if score == 0 && payload.ReadinessScore > 0 {
		score = payload.ReadinessScore
	}

	pack := ContextPack{
		SchemaVersion:  contextPackSchema,
		Note:           contextPackNote,
		PackIDs:        ids,
		ReadinessScore: score,
		OK:             ok,
		Failures:       top,
		Instrument: ContextInstrument{
			DepsCount:   len(snap.Deps),
			DepsFP:      snap.DepsFP,
			SecretHits:  snap.SecretHits,
			DepsAdded:   added,
			DepsRemoved: removed,
			Note:        "Instrument panel map — not a security program · not conformity assessment",
		},
		RemediationHints:     hints,
		Pathway:              buildContextPathway(root),
		AgentIdentity:        payload.AgentIdentity,
		Paths:                contextPackPathsMap(root),
		CertificationClaimed: false,
	}

	mdPath, jsonPath := contextPackPaths(root, outPath)
	if err := os.MkdirAll(filepath.Dir(jsonPath), 0o755); err != nil {
		return "", err
	}
	b, err := json.MarshalIndent(pack, "", "  ")
	if err != nil {
		return "", err
	}
	if err := PacketLooksAirlocked(b); err != nil {
		return "", err
	}
	if err := os.WriteFile(jsonPath, append(b, '\n'), 0o644); err != nil {
		return "", err
	}
	md := formatContextPackMarkdown(pack)
	if err := PacketLooksAirlocked([]byte(md)); err != nil {
		return "", err
	}
	if err := os.WriteFile(mdPath, []byte(md), 0o644); err != nil {
		return "", err
	}
	return jsonPath, nil
}

func loadOrValidatePayload(root string, packIDs []string) (payload ir.GateFailurePayload, score int, ok bool, usedCache bool, err error) {
	cachePath := filepath.Join(root, ".github", "curbpack", "cache", "latest_failure.json")
	if b, rerr := os.ReadFile(cachePath); rerr == nil {
		var p ir.GateFailurePayload
		if json.Unmarshal(b, &p) == nil && (p.SchemaVersion != "" || len(p.Failures) > 0 || p.PackID != "") {
			if cacheValidForRequest(root, p, packIDs) {
				ok = len(p.Failures) == 0
				score = p.ReadinessScore
				return p, score, ok, true, nil
			}
		}
	}
	res, verr := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, Quiet: true})
	if verr != nil {
		return ir.GateFailurePayload{}, 0, false, false, verr
	}
	p := res.Payload
	p.ReadinessScore = res.Score
	return p, res.Score, res.Passed, false, nil
}

// cacheValidForRequest rejects stale cache when pack set or HEAD commit drifted.
func cacheValidForRequest(root string, p ir.GateFailurePayload, requested []string) bool {
	head, err := gitutil.HeadSHA(root)
	if err != nil || head == "" {
		return false
	}
	if parent := strings.TrimSpace(p.ConcurrencyControl.ExpectedParentCommitSHA); parent != head {
		return false
	}
	want := normalizePackList(requested)
	if len(want) == 0 {
		cfgIDs, err := config.ResolvePackIDs(root, nil)
		if err != nil {
			return false
		}
		want = normalizePackList(cfgIDs)
	}
	if len(want) == 0 {
		return true
	}
	got := normalizePackList(strings.Split(p.PackID, ","))
	if len(got) != len(want) {
		return false
	}
	for i := range want {
		if want[i] != got[i] {
			return false
		}
	}
	return true
}

func normalizePackList(ids []string) []string {
	out := make([]string, 0, len(ids))
	for _, id := range ids {
		id = strings.TrimSpace(id)
		if id != "" {
			out = append(out, id)
		}
	}
	sort.Strings(out)
	return out
}

func contextPackPaths(root, outPath string) (mdPath, jsonPath string) {
	if outPath == "" {
		base := filepath.Join(root, ".github", "curbpack", "cache", "context-pack")
		return base + ".md", base + ".json"
	}
	ext := strings.ToLower(filepath.Ext(outPath))
	stem := strings.TrimSuffix(outPath, ext)
	switch ext {
	case ".md", ".markdown":
		return outPath, stem + ".json"
	case ".json":
		return stem + ".md", outPath
	default:
		return outPath + ".md", outPath + ".json"
	}
}

func contextPackPathsMap(root string) map[string]string {
	base := filepath.ToSlash(filepath.Join(".github", "curbpack", "cache"))
	m := map[string]string{
		"latest_failure":  base + "/latest_failure.json",
		"instrument":      base + "/instrument.json",
		"remediations":    base + "/remediations.json",
		"context_pack":    base + "/context-pack.json",
		"context_pack_md": base + "/context-pack.md",
		"buyer_questions": base + "/buyer-questions.md",
		"explain_packet":  base + "/explain-packet.json",
		"policy_graph":    filepath.ToSlash(filepath.Join(".github", "curbpack", "graph", "policy-graph.json")),
		"pathway_seed":    base + "/pathway-seed.json",
		"research_packet": base + "/research-packet.json",
		"research_brief":  base + "/research-brief.md",
	}
	if snap, err := pathway.Project(root); err == nil {
		m["pathway_status_hint"] = snap.Next.Cmd
	}
	if research.PacketPresent(root) {
		m["research_packet_present"] = "true"
		if pkt, err := research.LoadPacket(root); err == nil && pkt != nil {
			m["research_sources"] = fmt.Sprintf("%d", len(pkt.Sources))
		}
	} else {
		m["research_packet_present"] = "false"
	}
	return m
}

func buildContextPathway(root string) *ContextPathway {
	seed, err := pathway.Load(root)
	if err != nil {
		return nil
	}
	snap, err := pathway.Project(root)
	if err != nil {
		return nil
	}
	cp := &ContextPathway{
		Phase:      string(snap.Phase),
		ParentPath: pathway.FormatParentPath(snap.Path),
		NextVerb:   snap.Next.Verb,
		NextCmd:    snap.Next.Cmd,
		NextNote:   snap.Next.Note,
		Note:       "Re-check locally. Not certification. confirm-* / attest are human-only. Seed is not a gate input.",
	}
	if seed != nil {
		cp.PacksConfirmed = seed.HumanTicks.PacksConfirmed
		cp.ProseOwned = seed.HumanTicks.ProseOwned
		cp.ShareReviewed = seed.HumanTicks.ShareReviewed
	}
	return cp
}

func formatContextPackMarkdown(p ContextPack) string {
	var b strings.Builder
	b.WriteString("# Curbpack ContextPack\n\n")
	b.WriteString("> Structural evidence for human review. Not a conformity assessment, CE mark, or certification.\n\n")
	fmt.Fprintf(&b, "- **Packs:** %s\n", strings.Join(p.PackIDs, ", "))
	fmt.Fprintf(&b, "- **Readiness:** %d%%\n", p.ReadinessScore)
	fmt.Fprintf(&b, "- **OK:** %v\n", p.OK)
	fmt.Fprintf(&b, "- **Certification claimed:** no\n")
	if p.AgentIdentity.Source != "" || p.AgentIdentity.AgentID != "" {
		fmt.Fprintf(&b, "- **Agent identity:** `%s`", mdCell(p.AgentIdentity.Source))
		if p.AgentIdentity.Reason != "" {
			fmt.Fprintf(&b, " (%s)", mdCell(p.AgentIdentity.Reason))
		}
		if p.AgentIdentity.AgentID != "" {
			fmt.Fprintf(&b, " agent_id=`%s`", mdCell(p.AgentIdentity.AgentID))
		}
		b.WriteString(" — lineage label, not attestation\n")
	}
	b.WriteString("\n")
	if p.Pathway != nil {
		b.WriteString("## Pathway\n\n")
		fmt.Fprintf(&b, "- **Phase:** `%s`\n", p.Pathway.ParentPath)
		fmt.Fprintf(&b, "- **Next:** %s\n", p.Pathway.NextVerb)
		fmt.Fprintf(&b, "- **Run:** `%s`\n", p.Pathway.NextCmd)
		if strings.TrimSpace(p.Pathway.NextNote) != "" {
			fmt.Fprintf(&b, "- **Note:** %s\n", p.Pathway.NextNote)
		}
		b.WriteString("\n_Agents: prefer this section over spelunking pathway-seed.json. Stop at human confirms/attest._\n\n")
	}
	fmt.Fprintf(&b, "## Instrument\n\n- deps: %d (fp `%s`)\n- secret-hits: %d\n", p.Instrument.DepsCount, p.Instrument.DepsFP, p.Instrument.SecretHits)
	if p.Instrument.DepsAdded != 0 || p.Instrument.DepsRemoved != 0 {
		fmt.Fprintf(&b, "- Δ deps: +%d / −%d\n", p.Instrument.DepsAdded, p.Instrument.DepsRemoved)
	}
	b.WriteString("\n## Top failures\n\n")
	if len(p.Failures) == 0 {
		b.WriteString("_None in this pack snapshot._\n\n")
	} else {
		b.WriteString("| gate_id | severity | description | target_file |\n|---|---|---|---|\n")
		for _, f := range p.Failures {
			fmt.Fprintf(&b, "| %s | %s | %s | %s |\n",
				mdCell(f.GateID), mdCell(f.Severity), mdCell(f.Description), mdCell(f.TargetFile))
		}
		b.WriteString("\n")
	}
	if len(p.RemediationHints) > 0 {
		b.WriteString("## Remediation hints (by gate_id)\n\n")
		for _, h := range p.RemediationHints {
			fmt.Fprintf(&b, "- `%s`: %s\n", h.GateID, mdCell(h.Action))
		}
		b.WriteString("\n")
	}
	b.WriteString("## Paths\n\n")
	pathKeys := make([]string, 0, len(p.Paths))
	for k := range p.Paths {
		pathKeys = append(pathKeys, k)
	}
	sort.Strings(pathKeys)
	for _, k := range pathKeys {
		fmt.Fprintf(&b, "- `%s`: `%s`\n", k, p.Paths[k])
	}
	b.WriteString("\n_Assistants: run `curbpack check` (exit code authoritative). Never invent gate results or certification claims._\n")
	return b.String()
}

func truncate(s string, n int) string {
	s = strings.TrimSpace(s)
	if n <= 0 || len(s) <= n {
		return s
	}
	return s[:n] + "…"
}
