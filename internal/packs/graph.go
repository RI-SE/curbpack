package packs

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// GraphSchemaVersion is the policy-graph.json schema for agents/importers.
const GraphSchemaVersion = "1"

// PolicyGraph is a deterministic local regulation knowledge graph export.
type PolicyGraph struct {
	SchemaVersion string      `json:"schema_version"`
	Note          string      `json:"note"`
	Nodes         []GraphNode `json:"nodes"`
	Edges         []GraphEdge `json:"edges"`
	Digest        string      `json:"digest,omitempty"`
}

// GraphNode is one RKG node.
type GraphNode struct {
	ID   string            `json:"id"`
	Type string            `json:"type"` // instrument|clause|pack|rule|watchlist
	Attrs map[string]string `json:"attrs,omitempty"`
}

// GraphEdge links nodes.
type GraphEdge struct {
	From string `json:"from"`
	To   string `json:"to"`
	Rel  string `json:"rel"` // implements|cites|bans|attests|extends|overlays
}

// BuildPolicyGraph constructs a deterministic graph for the given pack IDs (composed).
func BuildPolicyGraph(packIDs []string) (PolicyGraph, error) {
	composed, sources, err := Compose(packIDs)
	if err != nil {
		return PolicyGraph{}, err
	}
	wl, err := LoadWatchlist()
	if err != nil {
		return PolicyGraph{}, err
	}

	nodes := map[string]GraphNode{}
	var edges []GraphEdge
	addNode := func(n GraphNode) {
		nodes[n.ID] = n
	}
	addEdge := func(from, to, rel string) {
		edges = append(edges, GraphEdge{From: from, To: to, Rel: rel})
	}

	for _, sid := range sources {
		p, err := LoadPack(sid)
		if err != nil {
			return PolicyGraph{}, err
		}
		pid := "pack:" + p.ID
		addNode(GraphNode{ID: pid, Type: "pack", Attrs: map[string]string{
			"name": p.Name, "version": p.Version, "jurisdiction": p.Jurisdiction,
		}})
		if base := strings.TrimSpace(p.Extends); base != "" {
			addEdge(pid, "pack:"+base, "extends")
		}
		for _, ov := range p.Overlays {
			addEdge(pid, "pack:"+strings.TrimSpace(ov), "overlays")
		}
		for i, c := range p.Citations {
			cid := fmt.Sprintf("instrument:%s:%d", p.ID, i)
			addNode(GraphNode{ID: cid, Type: "instrument", Attrs: citationAttrs(c)})
			addEdge(pid, cid, "cites")
		}
		for _, r := range p.Rules {
			rid := "rule:" + r.ID
			addNode(GraphNode{ID: rid, Type: "rule", Attrs: map[string]string{
				"severity": r.Severity, "check": r.Check, "pack": p.ID,
			}})
			addEdge(pid, rid, "implements")
			for i, c := range r.Citations {
				cid := fmt.Sprintf("clause:%s:%d", r.ID, i)
				addNode(GraphNode{ID: cid, Type: "clause", Attrs: citationAttrs(c)})
				addEdge(rid, cid, "cites")
			}
			if r.Check == "npm_dep_ban" || r.Check == "manifest_dep_ban" {
				bid := "ban:" + r.Package
				addNode(GraphNode{ID: bid, Type: "watchlist", Attrs: map[string]string{"package": r.Package}})
				addEdge(rid, bid, "bans")
			}
		}
	}

	// Composed view node
	addNode(GraphNode{ID: "pack:" + composed.ID, Type: "pack", Attrs: map[string]string{
		"name": "composed", "version": composed.Version,
	}})

	for _, e := range wl.Entries {
		wid := "watchlist:" + e.ID
		attrs := map[string]string{
			"ecosystem": e.Ecosystem,
			"package":   e.Package,
			"purl":      e.PURL,
		}
		addNode(GraphNode{ID: wid, Type: "watchlist", Attrs: attrs})
		for i, c := range e.Citations {
			cid := fmt.Sprintf("instrument:wl:%s:%d", e.ID, i)
			addNode(GraphNode{ID: cid, Type: "instrument", Attrs: citationAttrs(c)})
			addEdge(wid, cid, "cites")
		}
	}

	// Deterministic order
	nodeIDs := make([]string, 0, len(nodes))
	for id := range nodes {
		nodeIDs = append(nodeIDs, id)
	}
	sort.Strings(nodeIDs)
	outNodes := make([]GraphNode, 0, len(nodeIDs))
	for _, id := range nodeIDs {
		outNodes = append(outNodes, nodes[id])
	}
	sort.Slice(edges, func(i, j int) bool {
		a := edges[i].From + "|" + edges[i].Rel + "|" + edges[i].To
		b := edges[j].From + "|" + edges[j].Rel + "|" + edges[j].To
		return a < b
	})

	g := PolicyGraph{
		SchemaVersion: GraphSchemaVersion,
		Note:          "Local regulation knowledge graph for human/agent review — not a conformity assessment.",
		Nodes:         outNodes,
		Edges:         edges,
	}
	body, _ := json.Marshal(struct {
		N []GraphNode `json:"nodes"`
		E []GraphEdge `json:"edges"`
		S string      `json:"schema_version"`
	}{N: outNodes, E: edges, S: GraphSchemaVersion})
	g.Digest = fmt.Sprintf("%x", sha256.Sum256(body))
	return g, nil
}

func citationAttrs(c Citation) map[string]string {
	return map[string]string{
		"framework":      c.Framework,
		"instrument":     c.Instrument,
		"article":        c.Article,
		"annex":          c.Annex,
		"url":            c.URL,
		"effective_from": c.EffectiveFrom,
		"effective_to":   c.EffectiveTo,
	}
}

// ExportPolicyGraph writes .github/cyberready/graph/policy-graph.json (or outPath).
func ExportPolicyGraph(root string, packIDs []string, outPath string) (string, error) {
	if len(packIDs) == 0 {
		packIDs = []string{"house-policy"}
	}
	g, err := BuildPolicyGraph(packIDs)
	if err != nil {
		return "", err
	}
	if outPath == "" {
		outPath = filepath.Join(root, ".github", "cyberready", "graph", "policy-graph.json")
	}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return "", err
	}
	b, err := json.MarshalIndent(g, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(outPath, append(b, '\n'), 0o644); err != nil {
		return "", err
	}
	return outPath, nil
}
