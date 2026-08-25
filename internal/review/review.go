// Package review triages a received curbpack-native review-pack offline.
// It reports on the document (structure, digest self-consistency, reference
// resolvability) — never a product verdict or conformity assessment.
package review

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/research"
)

const schemaVersion = "curbpack-review-report:1"

// State is one finding outcome. Never conflate these three.
type State string

const (
	StateConfirmed    State = "confirmed"
	StateUnconfirmed  State = "unconfirmed"
	StateContradicted State = "contradicted"
)

// Finding is one triage row about the received document.
type Finding struct {
	ID       string `json:"id"`
	Category string `json:"category"` // structure | digest | reference
	State    State  `json:"state"`
	Detail   string `json:"detail"`
}

// Report is the offline review result (document triage only).
type Report struct {
	Schema           string    `json:"schema"`
	BundleRoot       string    `json:"bundle_root"`
	Findings         []Finding `json:"findings"`
	ConfirmedCount   int       `json:"confirmed_count"`
	UnconfirmedCount int       `json:"unconfirmed_count"`
	ContradictedCount int      `json:"contradicted_count"`
	Disclaimer       string    `json:"disclaimer"`
}

// Options for Run.
type Options struct {
	BundleRoot string
	Writer     io.Writer // triage markdown; default stdout
	JSONOut    bool
}

var (
	reOnePagerFP = regexp.MustCompile(`<!--\s*curbpack-onepager-fp:([0-9a-fA-Za-z]+)`)
	reProvDD     = regexp.MustCompile(`(?s)<dt>([^<]+)</dt>\s*<dd>([^<]*)</dd>`)
	reHTTPS      = regexp.MustCompile(`https://[^\s<>)"'\]]+`)
	reBacktick   = regexp.MustCompile("`([^`]+)`")
	reClaimID    = regexp.MustCompile(`\b(?:HOUSE|CRA|MEDTECH)-[A-Z0-9-]+\b`)
)

// Expected curbpack-native review-pack layers (v1 scope lock).
var requiredFiles = []string{
	"01-gate-failures.json",
	"02-action-report.md",
	"03-executive-summary.md",
	"buyer-onepager.html",
}

var optionalDigestFiles = map[string]string{
	"04-sbom.cdx.json":  "sbom_digest",
	"05-vex-draft.json": "vex_digest",
}

// Run triages a received review-pack directory. Does not call git or network.
func Run(opts Options) (Report, error) {
	root := filepath.Clean(strings.TrimSpace(opts.BundleRoot))
	if root == "" || root == "." {
		return Report{}, fmt.Errorf("review requires a path to a received review-pack directory")
	}
	st, err := os.Stat(root)
	if err != nil {
		return Report{}, fmt.Errorf("review pack path: %w", err)
	}
	if !st.IsDir() {
		return Report{}, fmt.Errorf("review pack path must be a directory (got file %s)", root)
	}

	rep := Report{
		Schema:     schemaVersion,
		BundleRoot: root,
		Disclaimer: "Document triage only — not a product verdict, not conformity assessment, not CE / notified-body approval.",
	}

	checkStructure(&rep, root)
	payload, payloadOK := loadPayload(&rep, root)
	prov := extractProvenance(root)
	checkDigests(&rep, root, payload, payloadOK, prov)
	checkReferences(&rep, root)

	for _, f := range rep.Findings {
		switch f.State {
		case StateConfirmed:
			rep.ConfirmedCount++
		case StateUnconfirmed:
			rep.UnconfirmedCount++
		case StateContradicted:
			rep.ContradictedCount++
		}
	}
	sort.SliceStable(rep.Findings, func(i, j int) bool {
		if rep.Findings[i].Category != rep.Findings[j].Category {
			return rep.Findings[i].Category < rep.Findings[j].Category
		}
		return rep.Findings[i].ID < rep.Findings[j].ID
	})

	w := opts.Writer
	if w == nil {
		w = os.Stdout
	}
	if opts.JSONOut {
		enc := json.NewEncoder(w)
		enc.SetIndent("", "  ")
		if err := enc.Encode(rep); err != nil {
			return rep, err
		}
	} else {
		if _, err := io.WriteString(w, TriageMarkdown(rep)); err != nil {
			return rep, err
		}
	}
	return rep, nil
}

// HasContradictions reports whether any finding is contradicted.
func HasContradictions(rep Report) bool {
	return rep.ContradictedCount > 0
}

func checkStructure(rep *Report, root string) {
	for _, name := range requiredFiles {
		rel := name
		path := filepath.Join(root, name)
		if fileNonEmpty(path) {
			add(rep, Finding{
				ID: "structure:" + rel, Category: "structure", State: StateConfirmed,
				Detail: "Required layer present: " + rel,
			})
		} else if _, err := os.Stat(path); err == nil {
			add(rep, Finding{
				ID: "structure:" + rel, Category: "structure", State: StateContradicted,
				Detail: "Required layer empty: " + rel,
			})
		} else {
			add(rep, Finding{
				ID: "structure:" + rel, Category: "structure", State: StateContradicted,
				Detail: "Required layer missing: " + rel,
			})
		}
	}
	// Optional layers — presence is confirmed; absence is unconfirmed (not contradicted).
	for _, name := range []string{"04-sbom.cdx.json", "04-sbom-summary.json", "05-vex-draft.json", "06-gate-failures.sarif", "07-watchlist-sbom-join.json", "context-pack.json", "buyer-questions.md"} {
		path := filepath.Join(root, name)
		if fileNonEmpty(path) {
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateConfirmed,
				Detail: "Optional layer present: " + name,
			})
		} else {
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateUnconfirmed,
				Detail: "Optional layer absent: " + name,
			})
		}
	}
}

func loadPayload(rep *Report, root string) (ir.GateFailurePayload, bool) {
	path := filepath.Join(root, "01-gate-failures.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return ir.GateFailurePayload{}, false
	}
	var p ir.GateFailurePayload
	if err := json.Unmarshal(data, &p); err != nil {
		add(rep, Finding{
			ID: "digest:gate-json-parse", Category: "digest", State: StateContradicted,
			Detail: "01-gate-failures.json is not valid GateFailurePayload JSON: " + err.Error(),
		})
		return ir.GateFailurePayload{}, false
	}
	add(rep, Finding{
		ID: "digest:gate-json-parse", Category: "digest", State: StateConfirmed,
		Detail: fmt.Sprintf("01-gate-failures.json parses (pack_id=%s score=%d failures=%d)", strings.TrimSpace(p.PackID), p.ReadinessScore, len(p.Failures)),
	})
	return p, true
}

func checkDigests(rep *Report, root string, payload ir.GateFailurePayload, payloadOK bool, prov map[string]string) {
	htmlPath := filepath.Join(root, "buyer-onepager.html")
	htmlDoc, _ := os.ReadFile(htmlPath)
	fp := ""
	if m := reOnePagerFP.FindSubmatch(htmlDoc); m != nil {
		fp = string(m[1])
		add(rep, Finding{
			ID: "digest:onepager-fp-marker", Category: "digest", State: StateConfirmed,
			Detail: "buyer-onepager.html carries curbpack-onepager-fp marker " + fp[:min(12, len(fp))],
		})
	} else if len(htmlDoc) > 0 {
		add(rep, Finding{
			ID: "digest:onepager-fp-marker", Category: "digest", State: StateContradicted,
			Detail: "buyer-onepager.html missing curbpack-onepager-fp marker",
		})
	}

	if payloadOK {
		got := ir.ComputeResultDigest(payload)
		add(rep, Finding{
			ID: "digest:result-digest", Category: "digest", State: StateConfirmed,
			Detail: "Recomputed result_digest from 01-gate-failures.json: " + got[:min(16, len(got))],
		})
		if claimed, ok := prov["result_digest"]; ok && claimed != "" {
			if digestPrefixMatch(got, claimed) {
				add(rep, Finding{
					ID: "digest:result-digest-match", Category: "digest", State: StateConfirmed,
					Detail: "Provenance result_digest agrees with recomputed digest",
				})
			} else {
				add(rep, Finding{
					ID: "digest:result-digest-match", Category: "digest", State: StateContradicted,
					Detail: fmt.Sprintf("Provenance result_digest %q diverges from recomputed %s…", claimed, got[:min(12, len(got))]),
				})
			}
		} else {
			add(rep, Finding{
				ID: "digest:result-digest-match", Category: "digest", State: StateUnconfirmed,
				Detail: "No result_digest in one-pager provenance — recomputed digest recorded only",
			})
		}
	}

	for file, key := range optionalDigestFiles {
		path := filepath.Join(root, file)
		if !fileNonEmpty(path) {
			continue
		}
		got := fileSHA256(path)
		claimed, ok := prov[key]
		if !ok || strings.TrimSpace(claimed) == "" {
			add(rep, Finding{
				ID: "digest:" + key, Category: "digest", State: StateUnconfirmed,
				Detail: fmt.Sprintf("%s present but no %s in one-pager provenance", file, key),
			})
			continue
		}
		if digestPrefixMatch(got, claimed) {
			add(rep, Finding{
				ID: "digest:" + key, Category: "digest", State: StateConfirmed,
				Detail: fmt.Sprintf("%s matches provenance %s (prefix)", file, key),
			})
		} else {
			add(rep, Finding{
				ID: "digest:" + key, Category: "digest", State: StateContradicted,
				Detail: fmt.Sprintf("%s sha256 diverges from provenance %s=%q", file, key, claimed),
			})
		}
	}

	if packClaim := strings.TrimSpace(prov["Rule packs"]); packClaim != "" && payloadOK {
		if packClaim == strings.TrimSpace(payload.PackID) {
			add(rep, Finding{
				ID: "digest:pack-id-agree", Category: "digest", State: StateConfirmed,
				Detail: "One-pager Rule packs agrees with 01-gate-failures.json pack_id",
			})
		} else {
			add(rep, Finding{
				ID: "digest:pack-id-agree", Category: "digest", State: StateContradicted,
				Detail: fmt.Sprintf("pack_id mismatch: json=%q onepager=%q", payload.PackID, packClaim),
			})
		}
	}
}

func checkReferences(rep *Report, root string) {
	bundleFiles := map[string]struct{}{}
	_ = filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return nil
		}
		bundleFiles[filepath.ToSlash(rel)] = struct{}{}
		bundleFiles[filepath.Base(path)] = struct{}{}
		return nil
	})

	texts := map[string][]byte{}
	for _, name := range []string{"02-action-report.md", "03-executive-summary.md", "buyer-questions.md", "context-pack.md", "buyer-onepager.html"} {
		if data, err := os.ReadFile(filepath.Join(root, name)); err == nil {
			texts[name] = data
		}
	}

	seenURL := map[string]struct{}{}
	seenPath := map[string]struct{}{}
	seenClaim := map[string]struct{}{}

	for src, data := range texts {
		text := string(data)
		for _, u := range reHTTPS.FindAllString(text, -1) {
			u = strings.TrimRight(u, ".,);\"'/")
			u = strings.TrimSuffix(u, "</p")
			u = strings.TrimSuffix(u, "</a")
			if _, ok := seenURL[u]; ok {
				continue
			}
			seenURL[u] = struct{}{}
			// External links are recorded but never fetched — cannot reach confirmed.
			// Allowlisted vs unknown is informational only; never elevates to confirmed.
			detail := fmt.Sprintf("External link recorded (never fetched) from %s: %s", src, u)
			if err := research.ValidateSourceURL(u); err == nil {
				detail = fmt.Sprintf("Allowlisted external link recorded (never fetched) from %s: %s", src, u)
			}
			add(rep, Finding{
				ID: "reference:url:" + shortID(u), Category: "reference", State: StateUnconfirmed,
				Detail: detail,
			})
		}
		for _, m := range reBacktick.FindAllStringSubmatch(text, -1) {
			cand := filepath.ToSlash(strings.TrimSpace(m[1]))
			if cand == "" || strings.Contains(cand, " ") || len(cand) > 200 {
				continue
			}
			if strings.HasPrefix(cand, "http") {
				continue
			}
			if _, ok := seenPath[cand]; ok {
				continue
			}
			seenPath[cand] = struct{}{}
			st, detail := resolveBundleAnchor(root, cand, bundleFiles)
			add(rep, Finding{
				ID: "reference:path:" + shortID(cand), Category: "reference", State: st,
				Detail: referenceKindDetail("in-bundle-or-repo", detail+" (from "+src+")"),
			})
		}
		for _, m := range reClaimID.FindAllString(text, -1) {
			if _, ok := seenClaim[m]; ok {
				continue
			}
			seenClaim[m] = struct{}{}
			// Claim ids in the pack are catalog citations — present in document = confirmed as cited;
			// we do not treat them as product proof.
			add(rep, Finding{
				ID: "reference:claim:" + m, Category: "reference", State: StateConfirmed,
				Detail: fmt.Sprintf("Pack claim id present in document: %s", m),
			})
		}
	}

	if len(seenURL) == 0 && len(seenPath) == 0 && len(seenClaim) == 0 {
		add(rep, Finding{
			ID: "reference:none", Category: "reference", State: StateUnconfirmed,
			Detail: "No path/claim/URL references extracted from triage surfaces",
		})
	}
}

func extractProvenance(root string) map[string]string {
	out := map[string]string{}
	data, err := os.ReadFile(filepath.Join(root, "buyer-onepager.html"))
	if err != nil {
		return out
	}
	// Unescape HTML entities in dd text for comparison.
	for _, m := range reProvDD.FindAllStringSubmatch(string(data), -1) {
		k := strings.TrimSpace(html.UnescapeString(m[1]))
		v := strings.TrimSpace(html.UnescapeString(m[2]))
		if k == "" {
			continue
		}
		out[k] = v
		// Also map digest keys lowercase.
		lk := strings.ToLower(k)
		out[lk] = v
	}
	return out
}

func digestPrefixMatch(full, claimed string) bool {
	claimed = strings.TrimSpace(claimed)
	claimed = strings.TrimSuffix(claimed, "…")
	claimed = strings.TrimSuffix(claimed, "...")
	claimed = strings.TrimSpace(claimed)
	if claimed == "" || full == "" {
		return false
	}
	// Display truncates to 12 + ellipsis.
	n := len(claimed)
	if n > len(full) {
		n = len(full)
	}
	if n > 12 {
		n = 12
	}
	return strings.HasPrefix(full, claimed[:n])
}

func fileNonEmpty(path string) bool {
	st, err := os.Stat(path)
	return err == nil && st.Size() > 0
}

func fileSHA256(path string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	sum := sha256.Sum256(data)
	return fmt.Sprintf("%x", sum)
}

func looksLikeRepoPath(s string) bool {
	if strings.Contains(s, "/") || strings.HasSuffix(s, ".md") || strings.HasSuffix(s, ".json") || strings.HasSuffix(s, ".yml") || strings.HasSuffix(s, ".yaml") {
		return true
	}
	return strings.EqualFold(s, "SECURITY.md") || strings.EqualFold(s, "README.md")
}

func shortID(s string) string {
	sum := sha256.Sum256([]byte(s))
	return fmt.Sprintf("%x", sum[:6])
}

func add(rep *Report, f Finding) {
	rep.Findings = append(rep.Findings, f)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// TriageMarkdown returns a pasteable case-ticket note.
func TriageMarkdown(rep Report) string {
	var b strings.Builder
	b.WriteString("# Curbpack review — triage note\n\n")
	b.WriteString("> ")
	b.WriteString(rep.Disclaimer)
	b.WriteString("\n\n")
	fmt.Fprintf(&b, "- **Bundle:** `%s`\n", rep.BundleRoot)
	fmt.Fprintf(&b, "- **Confirmed:** %d · **Unconfirmed:** %d · **Contradicted:** %d\n\n",
		rep.ConfirmedCount, rep.UnconfirmedCount, rep.ContradictedCount)

	writeSection := func(title string, state State) {
		var rows []Finding
		for _, f := range rep.Findings {
			if f.State == state {
				rows = append(rows, f)
			}
		}
		if len(rows) == 0 {
			return
		}
		fmt.Fprintf(&b, "## %s\n\n", title)
		for _, f := range rows {
			fmt.Fprintf(&b, "- **[%s]** `%s` — %s\n", f.State, f.ID, f.Detail)
		}
		b.WriteByte('\n')
	}
	writeSection("Contradicted", StateContradicted)
	writeSection("Unconfirmed", StateUnconfirmed)
	writeSection("Confirmed", StateConfirmed)

	b.WriteString("---\n")
	b.WriteString("Generated by `curbpack review` (offline). Exit 1 if any finding is contradicted.\n")
	return b.String()
}
