package research

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/packs"
)

const (
	// SchemaVersion is research-packet.json schema.
	SchemaVersion = "1"
	// ClaimFence matches pathway / exports honesty fence.
	ClaimFence = "Prepares evidence for human review — not a conformity assessment."
	// PacketNote is the fixed informational note (not a gate input).
	PacketNote = "Informational sources for human draft — not conformity assessment; not a gate input."
)

// Source is one allowlisted citation trail entry.
type Source struct {
	ID            string   `json:"id"`
	URL           string   `json:"url"`
	Framework     string   `json:"framework,omitempty"`
	Instrument    string   `json:"instrument,omitempty"`
	RuleIDs       []string `json:"rule_ids,omitempty"`
	RetrievedAt   string   `json:"retrieved_at,omitempty"`
	ContentSHA256 string   `json:"content_sha256,omitempty"`
	Excerpt       string   `json:"excerpt,omitempty"`
	FetchError    string   `json:"fetch_error,omitempty"`
}

// Requirement is a local structural truth from composed pack rules.
type Requirement struct {
	GateID         string   `json:"gate_id"`
	Path           string   `json:"path,omitempty"`
	RequireHeaders []string `json:"require_headers,omitempty"`
	Remediation    string   `json:"remediation,omitempty"`
}

// Packet is the research IR written under .github/curbpack/cache/.
type Packet struct {
	SchemaVersion string        `json:"schema_version"`
	PackIDs       []string      `json:"pack_ids"`
	GraphDigest   string        `json:"graph_digest,omitempty"`
	Sources       []Source      `json:"sources"`
	Requirements  []Requirement `json:"requirements"`
	Claim         string        `json:"claim"`
	Note          string        `json:"note"`
}

// Options controls packet build.
type Options struct {
	RepoRoot string
	PackIDs  []string
	// GateIDs when non-empty filters requirements to those gate ids (bring-docs red path).
	GateIDs []string
	// Fetch when true GETs allowlisted HTTPS URLs (fail-open per URL).
	Fetch bool
	// Now overrides time for tests (RFC3339). Empty → time.Now().UTC().
	Now string
}

// PacketJSONPath returns the default research-packet.json path.
func PacketJSONPath(repoRoot string) string {
	return filepath.Join(repoRoot, ".github", "curbpack", "cache", "research-packet.json")
}

// PacketMDPath returns the human brief path.
func PacketMDPath(repoRoot string) string {
	return filepath.Join(repoRoot, ".github", "curbpack", "cache", "research-brief.md")
}

// PacketPresent reports whether research-packet.json exists.
func PacketPresent(repoRoot string) bool {
	st, err := os.Stat(PacketJSONPath(repoRoot))
	return err == nil && !st.IsDir()
}

// LoadPacket reads research-packet.json. Returns nil, nil if missing.
func LoadPacket(repoRoot string) (*Packet, error) {
	data, err := os.ReadFile(PacketJSONPath(repoRoot))
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var p Packet
	if err := json.Unmarshal(data, &p); err != nil {
		return nil, fmt.Errorf("parse research-packet.json: %w", err)
	}
	return &p, nil
}

// ResolvePackIDs picks packs from opts, then .curbpack.json, then pathway seed, else house-policy.
func ResolvePackIDs(repoRoot string, explicit []string) ([]string, error) {
	if len(explicit) > 0 {
		return explicit, nil
	}
	if cfg, err := config.Load(repoRoot); err == nil && cfg != nil && len(cfg.Packs) > 0 {
		return cfg.Packs, nil
	}
	if ids := readPathwayProposedPacks(repoRoot); len(ids) > 0 {
		return ids, nil
	}
	return []string{"house-policy"}, nil
}

// readPathwayProposedPacks best-effort reads pathway-seed.json without importing pathway
// (avoids import cycle: pathway → research).
func readPathwayProposedPacks(repoRoot string) []string {
	path := filepath.Join(repoRoot, ".github", "curbpack", "cache", "pathway-seed.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var s struct {
		ProposedPacks []string `json:"proposed_packs"`
	}
	if json.Unmarshal(data, &s) != nil {
		return nil
	}
	return s.ProposedPacks
}

// Build constructs a deterministic research packet (sans fetch timestamps/excerpts).
func Build(opts Options) (Packet, error) {
	ids, err := ResolvePackIDs(opts.RepoRoot, opts.PackIDs)
	if err != nil {
		return Packet{}, err
	}
	composed, _, err := packs.Compose(ids)
	if err != nil {
		return Packet{}, err
	}

	graphDigest := ""
	if g, gerr := packs.BuildPolicyGraph(ids); gerr == nil {
		graphDigest = g.Digest
	}

	sources := collectSources(composed)
	reqs := collectRequirements(composed, opts.GateIDs)

	pkt := Packet{
		SchemaVersion: SchemaVersion,
		PackIDs:       append([]string(nil), ids...),
		GraphDigest:   graphDigest,
		Sources:       sources,
		Requirements:  reqs,
		Claim:         ClaimFence,
		Note:          PacketNote,
	}

	if opts.Fetch {
		now := opts.Now
		if now == "" {
			now = time.Now().UTC().Format(time.RFC3339)
		}
		FetchSources(pkt.Sources, now)
	}
	return pkt, nil
}

func collectSources(composed packs.Pack) []Source {
	type agg struct {
		url, framework, instrument string
		rules                      map[string]struct{}
	}
	byURL := map[string]*agg{}

	add := func(c packs.Citation, ruleID string) {
		u := strings.TrimSpace(c.URL)
		if u == "" {
			return
		}
		if err := ValidateSourceURL(u); err != nil {
			return // drop non-allowlisted / non-https silently from trail
		}
		a := byURL[u]
		if a == nil {
			a = &agg{
				url:        u,
				framework:  c.Framework,
				instrument: c.Instrument,
				rules:      map[string]struct{}{},
			}
			byURL[u] = a
		}
		if a.framework == "" {
			a.framework = c.Framework
		}
		if a.instrument == "" {
			a.instrument = c.Instrument
		}
		if ruleID != "" {
			a.rules[ruleID] = struct{}{}
		}
	}

	for _, c := range composed.Citations {
		add(c, "")
	}
	for _, r := range composed.Rules {
		for _, c := range r.Citations {
			add(c, r.ID)
		}
	}

	urls := make([]string, 0, len(byURL))
	for u := range byURL {
		urls = append(urls, u)
	}
	sort.Strings(urls)

	out := make([]Source, 0, len(urls))
	for i, u := range urls {
		a := byURL[u]
		ruleIDs := make([]string, 0, len(a.rules))
		for id := range a.rules {
			ruleIDs = append(ruleIDs, id)
		}
		sort.Strings(ruleIDs)
		out = append(out, Source{
			ID:         fmt.Sprintf("src-%d", i+1),
			URL:        a.url,
			Framework:  a.framework,
			Instrument: a.instrument,
			RuleIDs:    ruleIDs,
		})
	}
	return out
}

func collectRequirements(composed packs.Pack, gateFilter []string) []Requirement {
	want := map[string]struct{}{}
	for _, g := range gateFilter {
		g = strings.TrimSpace(g)
		if g != "" {
			want[g] = struct{}{}
		}
	}
	var out []Requirement
	for _, r := range composed.Rules {
		if len(want) > 0 {
			if _, ok := want[r.ID]; !ok {
				continue
			}
		}
		path := strings.TrimSpace(r.Path)
		if path == "" && len(r.Paths) > 0 {
			path = strings.Join(r.Paths, ",")
		}
		out = append(out, Requirement{
			GateID:         r.ID,
			Path:           path,
			RequireHeaders: append([]string(nil), r.RequireHeaders...),
			Remediation:    r.Remediation,
		})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].GateID < out[j].GateID })
	return out
}

// Write persists packet JSON + human markdown brief. Does not affect check.
func Write(repoRoot string, pkt Packet) (jsonPath, mdPath string, err error) {
	jsonPath = PacketJSONPath(repoRoot)
	mdPath = PacketMDPath(repoRoot)
	if err := os.MkdirAll(filepath.Dir(jsonPath), 0o755); err != nil {
		return "", "", err
	}
	b, err := json.MarshalIndent(pkt, "", "  ")
	if err != nil {
		return "", "", err
	}
	if err := os.WriteFile(jsonPath, append(b, '\n'), 0o644); err != nil {
		return "", "", err
	}
	md := FormatBrief(pkt)
	if err := os.WriteFile(mdPath, []byte(md), 0o644); err != nil {
		return "", "", err
	}
	return jsonPath, mdPath, nil
}

// StableSourcesDigest hashes source URLs+ids (ignores fetch fields) for golden tests.
func StableSourcesDigest(pkt Packet) string {
	var b strings.Builder
	for _, s := range pkt.Sources {
		fmt.Fprintf(&b, "%s|%s|%s|%s|%s\n", s.ID, s.URL, s.Framework, s.Instrument, strings.Join(s.RuleIDs, ","))
	}
	sum := sha256.Sum256([]byte(b.String()))
	return fmt.Sprintf("%x", sum[:16])
}
