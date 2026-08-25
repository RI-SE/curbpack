// Package review triages a received curbpack-native review-pack offline.
// It reports on the document (structure, digest self-consistency, reference
// resolvability) — never a product verdict or conformity assessment.
//
// A reference is a claim the triage surfaces make about the system under review:
// a pack claim id, a path-shaped artifact pointer, or an external URL.
// Markup, booleans, JSON keys, versions, and truncated hashes are not references.
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

	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/pathjail"
	"github.com/afelin/curbpack/internal/research"
)

const (
	schemaVersion     = "curbpack-review-report:2"
	ClassifierVersion = "refclass:1"

	maxFileBytes  = 8 << 20  // 8 MiB per file
	maxTotalBytes = 64 << 20 // 64 MiB total across reads
)

// State is one finding outcome. Never conflate these three.
type State string

const (
	StateConfirmed    State = "confirmed"
	StateUnconfirmed  State = "unconfirmed"
	StateContradicted State = "contradicted"
)

// Cause explains unconfirmed or contradicted findings (schema v2).
type Cause string

const (
	CauseProducer     Cause = "producer"
	CauseExtractor    Cause = "extractor"
	CauseGenuine      Cause = "genuine"
	CauseExternal     Cause = "external"
	CauseSelfDisagree Cause = "self_disagree"
)

// Finding is one triage row about the received document.
type Finding struct {
	ID       string `json:"id"`
	Category string `json:"category"` // structure | digest | reference
	State    State  `json:"state"`
	Cause    Cause  `json:"cause,omitempty"`
	Detail   string `json:"detail"`
}

// Report is the offline review result (document triage only).
type Report struct {
	Schema                     string    `json:"schema"`
	ClassifierVersion          string    `json:"classifier_version"`
	BundleRoot                 string    `json:"bundle_root"`
	Findings                   []Finding `json:"findings"`
	ConfirmedCount             int       `json:"confirmed_count"`
	UnconfirmedCount           int       `json:"unconfirmed_count"`
	ContradictedCount          int       `json:"contradicted_count"`
	UnconfirmedProducer        int       `json:"unconfirmed_producer"`
	UnconfirmedExtractor       int       `json:"unconfirmed_extractor"`
	UnconfirmedGenuine         int       `json:"unconfirmed_genuine"`
	UnconfirmedExternal        int       `json:"unconfirmed_external"`
	ContradictedSelfDisagree   int       `json:"contradicted_self_disagree"`
	DroppedCount               int       `json:"dropped_count"`
	Dropped                    []string  `json:"dropped,omitempty"`
	Disclaimer                 string    `json:"disclaimer"`
}

// Options for Run.
type Options struct {
	BundleRoot string
	Writer     io.Writer // triage markdown or JSON; default stdout
	JSONOut    bool
	Full       bool // full dump + dropped list; default is terse
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

var optionalDigestFiles = []struct {
	File string
	Key  string
}{
	{"04-sbom.cdx.json", "sbom_digest"},
	{"05-vex-draft.json", "vex_digest"},
}

var optionalStructureFiles = []string{
	"04-sbom.cdx.json", "04-sbom-summary.json", "05-vex-draft.json",
	"06-gate-failures.sarif", "07-watchlist-sbom-join.json",
	"context-pack.json", "buyer-questions.md",
}

var triageSurfaces = []string{
	"02-action-report.md", "03-executive-summary.md",
	"buyer-questions.md", "buyer-onepager.html",
}

// Run triages a received review-pack directory. Does not call git or network.
func Run(opts Options) (Report, error) {
	root := filepath.Clean(strings.TrimSpace(opts.BundleRoot))
	if root == "" || root == "." {
		return Report{}, fmt.Errorf("review requires a path to a received review-pack directory")
	}
	st, err := os.Lstat(root)
	if err != nil {
		return Report{}, fmt.Errorf("review pack path: %w", err)
	}
	if st.Mode()&os.ModeSymlink != 0 {
		return Report{}, fmt.Errorf("review pack path refuses symlink: %s", root)
	}
	if !st.IsDir() {
		return Report{}, fmt.Errorf("review pack path must be a directory (got file %s)", root)
	}

	rep := Report{
		Schema:            schemaVersion,
		ClassifierVersion: ClassifierVersion,
		BundleRoot:        filepath.Base(root), // basename only — airlock refuses absolute homes
		Disclaimer:        "Document triage only — not a product verdict, not conformity assessment, not CE / notified-body approval.",
	}

	tallyRoot := root // absolute path for IO only
	budget := &readBudget{remaining: maxTotalBytes}
	checkStructure(&rep, tallyRoot, budget)
	payload, payloadOK := loadPayload(&rep, tallyRoot, budget)
	prov := extractProvenance(tallyRoot, budget)
	checkDigests(&rep, tallyRoot, payload, payloadOK, prov, budget)
	checkReferences(&rep, tallyRoot, budget)

	if redactReportAirlock(&rep) {
		add(&rep, Finding{
			ID: "structure:airlock-redacted", Category: "structure",
			State: StateContradicted, Cause: CauseSelfDisagree,
			Detail: "Bundle triage echoed home-path or PEM-shaped material; redacted before emit",
		})
	}

	tally(&rep)
	sortFindings(rep.Findings)

	w := opts.Writer
	if w == nil {
		w = os.Stdout
	}

	var out []byte
	if opts.JSONOut {
		var buf strings.Builder
		enc := json.NewEncoder(&buf)
		enc.SetIndent("", "  ")
		if err := enc.Encode(rep); err != nil {
			return rep, err
		}
		out = []byte(buf.String())
	} else {
		out = []byte(TriageMarkdown(rep, opts.Full))
	}
	if err := exportx.PacketLooksAirlocked(out); err != nil {
		return rep, fmt.Errorf("review output failed airlock: %w", err)
	}
	if _, err := w.Write(out); err != nil {
		return rep, err
	}
	return rep, nil
}

// HasContradictions reports whether any finding is contradicted.
func HasContradictions(rep Report) bool {
	return rep.ContradictedCount > 0
}

func tally(rep *Report) {
	for _, f := range rep.Findings {
		switch f.State {
		case StateConfirmed:
			rep.ConfirmedCount++
		case StateUnconfirmed:
			rep.UnconfirmedCount++
			switch f.Cause {
			case CauseProducer:
				rep.UnconfirmedProducer++
			case CauseExtractor:
				rep.UnconfirmedExtractor++
			case CauseGenuine:
				rep.UnconfirmedGenuine++
			case CauseExternal:
				rep.UnconfirmedExternal++
			}
		case StateContradicted:
			rep.ContradictedCount++
			if f.Cause == CauseSelfDisagree {
				rep.ContradictedSelfDisagree++
			}
		}
	}
	rep.DroppedCount = len(rep.Dropped)
	sort.Strings(rep.Dropped)
}

func sortFindings(fs []Finding) {
	stateOrd := map[State]int{
		StateContradicted: 0,
		StateUnconfirmed:  1,
		StateConfirmed:    2,
	}
	sort.SliceStable(fs, func(i, j int) bool {
		si, sj := stateOrd[fs[i].State], stateOrd[fs[j].State]
		if si != sj {
			return si < sj
		}
		if fs[i].Category != fs[j].Category {
			return fs[i].Category < fs[j].Category
		}
		return fs[i].ID < fs[j].ID
	})
}

func checkStructure(rep *Report, root string, budget *readBudget) {
	for _, name := range requiredFiles {
		path, err := jailJoin(root, name)
		if err != nil {
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: "Required layer path refused: " + name,
			})
			continue
		}
		st, err := os.Lstat(path)
		switch {
		case err != nil:
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: "Required layer missing: " + name,
			})
		case st.Mode()&os.ModeSymlink != 0:
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: "Required layer is a symlink (refused): " + name,
			})
		case st.Size() == 0:
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: "Required layer empty: " + name,
			})
		default:
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateConfirmed,
				Detail: "Required layer present: " + name,
			})
		}
	}
	for _, name := range optionalStructureFiles {
		path, err := jailJoin(root, name)
		if err != nil {
			continue
		}
		st, err := os.Lstat(path)
		if err == nil && st.Mode()&os.ModeSymlink == 0 && st.Size() > 0 {
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateConfirmed,
				Detail: "Optional layer present: " + name,
			})
		} else {
			add(rep, Finding{
				ID: "structure:" + name, Category: "structure", State: StateUnconfirmed, Cause: CauseProducer,
				Detail: "Optional layer absent: " + name,
			})
		}
	}
	_ = budget
}

func loadPayload(rep *Report, root string, budget *readBudget) (ir.GateFailurePayload, bool) {
	data, truncated, err := readCapped(root, "01-gate-failures.json", budget)
	if err != nil {
		return ir.GateFailurePayload{}, false
	}
	if truncated {
		add(rep, Finding{
			ID: "digest:gate-json-size", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
			Detail: "01-gate-failures.json exceeded size cap (truncated — not silently accepted)",
		})
		return ir.GateFailurePayload{}, false
	}
	var p ir.GateFailurePayload
	if err := json.Unmarshal(data, &p); err != nil {
		add(rep, Finding{
			ID: "digest:gate-json-parse", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
			Detail: "01-gate-failures.json is not valid GateFailurePayload JSON: " + fence(err.Error()),
		})
		return ir.GateFailurePayload{}, false
	}
	add(rep, Finding{
		ID: "digest:gate-json-parse", Category: "digest", State: StateConfirmed,
		Detail: fmt.Sprintf("01-gate-failures.json parses (pack_id=%s score=%d failures=%d)",
			fence(strings.TrimSpace(p.PackID)), p.ReadinessScore, len(p.Failures)),
	})
	return p, true
}

func checkDigests(rep *Report, root string, payload ir.GateFailurePayload, payloadOK bool, prov map[string]string, budget *readBudget) {
	htmlDoc, truncated, err := readCapped(root, "buyer-onepager.html", budget)
	if err == nil && truncated {
		add(rep, Finding{
			ID: "digest:onepager-size", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
			Detail: "buyer-onepager.html exceeded size cap (truncated — not silently accepted)",
		})
	}
	fp := ""
	if m := reOnePagerFP.FindSubmatch(htmlDoc); m != nil {
		fp = string(m[1])
		add(rep, Finding{
			ID: "digest:onepager-fp-marker", Category: "digest", State: StateConfirmed,
			Detail: "buyer-onepager.html carries curbpack-onepager-fp marker " + fp[:min(12, len(fp))],
		})
	} else if len(htmlDoc) > 0 && err == nil && !truncated {
		add(rep, Finding{
			ID: "digest:onepager-fp-marker", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
			Detail: "buyer-onepager.html missing curbpack-onepager-fp marker",
		})
	}

	if payloadOK {
		got := ir.ComputeResultDigest(payload)
		add(rep, Finding{
			ID: "digest:result-digest", Category: "digest", State: StateConfirmed,
			Detail: "Recomputed result_digest from 01-gate-failures.json: " + got[:min(16, len(got))],
		})
		claimed := strings.TrimSpace(prov["result_digest"])
		bindClaim := strings.TrimSpace(prov["result_digest_bind"])
		switch {
		case claimed != "" && digestPrefixMatch(got, claimed):
			add(rep, Finding{
				ID: "digest:result-digest-match", Category: "digest", State: StateConfirmed,
				Detail: "Provenance result_digest agrees with recomputed digest",
			})
		case claimed != "":
			add(rep, Finding{
				ID: "digest:result-digest-match", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: fmt.Sprintf("Provenance result_digest %q diverges from recomputed %s…", fence(claimed), got[:min(12, len(got))]),
			})
		default:
			add(rep, Finding{
				ID: "digest:result-digest-match", Category: "digest", State: StateUnconfirmed, Cause: CauseProducer,
				Detail: "No result_digest in one-pager provenance — recomputed digest recorded only",
			})
		}
		if bindClaim != "" && !digestPrefixMatch(got, bindClaim) {
			add(rep, Finding{
				ID: "digest:result-digest-bind", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: fmt.Sprintf("Bind result_digest_bind %q disagrees with recomputed %s…", fence(bindClaim), got[:min(12, len(got))]),
			})
		}
	}

	for _, pair := range optionalDigestFiles {
		path, jerr := jailJoin(root, pair.File)
		if jerr != nil {
			continue
		}
		st, err := os.Lstat(path)
		if err != nil || st.Mode()&os.ModeSymlink != 0 || st.Size() == 0 {
			continue
		}
		data, truncated, rerr := readCapped(root, pair.File, budget)
		if rerr != nil {
			continue
		}
		if truncated {
			add(rep, Finding{
				ID: "digest:" + pair.Key, Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: pair.File + " exceeded size cap (truncated — not silently accepted)",
			})
			continue
		}
		sum := sha256.Sum256(data)
		got := fmt.Sprintf("%x", sum)
		claimed := strings.TrimSpace(prov[pair.Key])
		bindClaim := strings.TrimSpace(prov[pair.Key+"_bind"])
		switch {
		case claimed == "":
			add(rep, Finding{
				ID: "digest:" + pair.Key, Category: "digest", State: StateUnconfirmed, Cause: CauseProducer,
				Detail: fmt.Sprintf("%s present but no %s in one-pager provenance", pair.File, pair.Key),
			})
		case digestPrefixMatch(got, claimed):
			add(rep, Finding{
				ID: "digest:" + pair.Key, Category: "digest", State: StateConfirmed,
				Detail: fmt.Sprintf("%s matches provenance %s (prefix)", pair.File, pair.Key),
			})
		default:
			add(rep, Finding{
				ID: "digest:" + pair.Key, Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: fmt.Sprintf("%s sha256 diverges from provenance %s=%q", pair.File, pair.Key, fence(claimed)),
			})
		}
		if bindClaim != "" && !digestPrefixMatch(got, bindClaim) {
			add(rep, Finding{
				ID: "digest:" + pair.Key + "-bind", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: fmt.Sprintf("Bind %s_bind %q disagrees with file hash", pair.Key, fence(bindClaim)),
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
				ID: "digest:pack-id-agree", Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: fmt.Sprintf("pack_id mismatch: json=%q onepager=%q", fence(payload.PackID), fence(packClaim)),
			})
		}
	}
}

func checkReferences(rep *Report, root string, budget *readBudget) {
	bundleFiles, walkFindings := walkBundleIndex(root)
	for _, f := range walkFindings {
		add(rep, f)
	}

	seen := map[string]struct{}{} // one finding per identity key
	var dropped []string

	for _, name := range triageSurfaces {
		data, truncated, err := readCapped(root, name, budget)
		if err != nil {
			continue
		}
		if truncated {
			add(rep, Finding{
				ID: "reference:size:" + name, Category: "reference", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: name + " exceeded size cap while extracting references",
			})
			continue
		}
		text := string(data)

		for _, u := range reHTTPS.FindAllString(text, -1) {
			u = strings.TrimRight(u, ".,);\"'/")
			u = strings.TrimSuffix(u, "</p")
			u = strings.TrimSuffix(u, "</a")
			kind := ClassifyReference(u)
			if kind != RefURL {
				dropped = appendUnique(dropped, u)
				continue
			}
			key := "reference:url:" + shortID(u)
			if _, ok := seen[key]; ok {
				continue
			}
			seen[key] = struct{}{}
			detail := fmt.Sprintf("External link recorded (never fetched) from %s: %s", name, fence(u))
			if err := research.ValidateSourceURL(u); err == nil {
				detail = fmt.Sprintf("Allowlisted external link recorded (never fetched) from %s: %s", name, fence(u))
			}
			add(rep, Finding{
				ID: key, Category: "reference", State: StateUnconfirmed, Cause: CauseExternal,
				Detail: detail,
			})
		}

		for _, m := range reClaimID.FindAllString(text, -1) {
			if ClassifyReference(m) != RefClaim {
				dropped = appendUnique(dropped, m)
				continue
			}
			key := "reference:claim:" + m
			if _, ok := seen[key]; ok {
				continue
			}
			seen[key] = struct{}{}
			add(rep, Finding{
				ID: key, Category: "reference", State: StateConfirmed,
				Detail: fmt.Sprintf("Pack claim id present in document: %s", m),
			})
		}

		for _, m := range reBacktick.FindAllStringSubmatch(text, -1) {
			cand := filepath.ToSlash(strings.TrimSpace(m[1]))
			if cand == "" || strings.Contains(cand, " ") || len(cand) > 200 {
				dropped = appendUnique(dropped, cand)
				continue
			}
			kind := ClassifyReference(cand)
			switch kind {
			case RefClaim:
				// Claims never enter the path resolver (identity = claim id already handled).
				continue
			case RefURL:
				continue
			case RefDrop:
				dropped = appendUnique(dropped, cand)
				continue
			case RefPath:
				// identity = cleaned relative path as cited (basename is resolution-only)
				identity := filepath.ToSlash(filepath.Clean(cand))
				if identity == "." {
					dropped = appendUnique(dropped, cand)
					continue
				}
				key := "reference:path:" + identity
				if _, ok := seen[key]; ok {
					continue
				}
				seen[key] = struct{}{}
				st, detail, cause := resolveBundleAnchor(root, identity, bundleFiles)
				add(rep, Finding{
					ID: key, Category: "reference", State: st, Cause: cause,
					Detail: referenceKindDetail("in-bundle-or-repo", detail+" (from "+name+")"),
				})
			}
		}
	}

	rep.Dropped = dropped
	if len(seen) == 0 {
		add(rep, Finding{
			ID: "reference:none", Category: "reference", State: StateUnconfirmed, Cause: CauseExtractor,
			Detail: "No path/claim/URL references extracted from triage surfaces",
		})
	}
}

func extractProvenance(root string, budget *readBudget) map[string]string {
	out := map[string]string{}
	data, truncated, err := readCapped(root, "buyer-onepager.html", budget)
	if err != nil || truncated {
		return out
	}
	for _, m := range reProvDD.FindAllStringSubmatch(string(data), -1) {
		k := strings.TrimSpace(html.UnescapeString(m[1]))
		v := strings.TrimSpace(html.UnescapeString(m[2]))
		if k == "" {
			continue
		}
		out[k] = v
		out[strings.ToLower(k)] = v
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
	n := len(claimed)
	if n > len(full) {
		n = len(full)
	}
	if n > 12 {
		n = 12
	}
	return strings.HasPrefix(full, claimed[:n])
}

func shortID(s string) string {
	sum := sha256.Sum256([]byte(s))
	return fmt.Sprintf("%x", sum[:6])
}

func add(rep *Report, f Finding) {
	rep.Findings = append(rep.Findings, f)
}

func appendUnique(xs []string, s string) []string {
	s = strings.TrimSpace(s)
	if s == "" {
		return xs
	}
	for _, x := range xs {
		if x == s {
			return xs
		}
	}
	return append(xs, s)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func fence(s string) string {
	s = strings.TrimSpace(s)
	if s == "" {
		return s
	}
	return "<untrusted_metadata>" + s + "</untrusted_metadata>"
}

// Airlock placeholders — fixed tokens so PacketLooksAirlocked accepts triage output
// while preserving a contradicted finding that the bundle echoed unsafe material.
const (
	redactedHome = "<redacted:home-path>"
	redactedPEM  = "<redacted:pem>"
)

// Match exportx airlock shapes (homePathRE / pemBlobRE) for redact-then-emit.
var (
	reHomePath = regexp.MustCompile(`(?i)(/Users/[^/\s"'<>]+|/home/[^/\s"'<>]+|/mnt/[a-z]/Users/[^/\s"'<>]+|C:\\Users\\[^\\\s"'<>]+)`)
	rePEMBlob  = regexp.MustCompile(`-----BEGIN [A-Z0-9 ]+-----[\s\S]{20,}?-----END [A-Z0-9 ]+-----`)
)

// redactReportAirlock mutates finding details/ids and dropped tokens. Returns true if any redaction occurred.
func redactReportAirlock(rep *Report) bool {
	changed := false
	for i := range rep.Findings {
		if s, ok := redactAirlockString(rep.Findings[i].Detail); ok {
			rep.Findings[i].Detail = s
			changed = true
		}
		if s, ok := redactAirlockString(rep.Findings[i].ID); ok {
			rep.Findings[i].ID = s
			changed = true
		}
	}
	for i := range rep.Dropped {
		if s, ok := redactAirlockString(rep.Dropped[i]); ok {
			rep.Dropped[i] = s
			changed = true
		}
	}
	return changed
}

func redactAirlockString(s string) (string, bool) {
	orig := s
	s = rePEMBlob.ReplaceAllString(s, redactedPEM)
	if home, err := os.UserHomeDir(); err == nil {
		home = strings.TrimSpace(home)
		if home != "" && home != "/" && home != `\` {
			s = strings.ReplaceAll(s, home, redactedHome)
			if slash := filepath.ToSlash(home); slash != home {
				s = strings.ReplaceAll(s, slash, redactedHome)
			}
		}
	}
	s = reHomePath.ReplaceAllString(s, redactedHome)
	return s, s != orig
}

func jailJoin(root, rel string) (string, error) {
	full, _, err := pathjail.Join(root, rel)
	return full, err
}

type readBudget struct {
	remaining int64
}

func readCapped(root, rel string, budget *readBudget) (data []byte, truncated bool, err error) {
	full, _, err := pathjail.Join(root, rel)
	if err != nil {
		return nil, false, err
	}
	st, err := os.Lstat(full)
	if err != nil {
		return nil, false, err
	}
	if st.Mode()&os.ModeSymlink != 0 {
		return nil, false, fmt.Errorf("refusing symlink: %s", rel)
	}
	if !st.Mode().IsRegular() {
		return nil, false, fmt.Errorf("not a regular file: %s", rel)
	}
	if budget.remaining <= 0 {
		return nil, true, nil
	}
	perFile := int64(maxFileBytes)
	if perFile > budget.remaining {
		perFile = budget.remaining
	}
	f, err := os.Open(full)
	if err != nil {
		return nil, false, err
	}
	defer f.Close()
	limited := io.LimitReader(f, perFile+1)
	data, err = io.ReadAll(limited)
	if err != nil {
		return nil, false, err
	}
	if int64(len(data)) > perFile {
		data = data[:perFile]
		budget.remaining = 0
		return data, true, nil
	}
	budget.remaining -= int64(len(data))
	return data, false, nil
}

func walkBundleIndex(root string) (map[string]struct{}, []Finding) {
	files := map[string]struct{}{}
	var findings []Finding
	_ = filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		// Re-Lstat so we never follow symlinks (Walk may still visit link nodes).
		st, lerr := os.Lstat(path)
		if lerr != nil {
			return nil
		}
		if st.Mode()&os.ModeSymlink != 0 {
			rel, _ := filepath.Rel(root, path)
			findings = append(findings, Finding{
				ID: "structure:symlink:" + shortID(filepath.ToSlash(rel)),
				Category: "structure", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: "Symlink skipped under bundle: " + fence(filepath.ToSlash(rel)),
			})
			if st.IsDir() || (info != nil && info.IsDir()) {
				return filepath.SkipDir
			}
			return nil
		}
		if st.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return nil
		}
		slash := filepath.ToSlash(rel)
		if _, _, jerr := pathjail.Join(root, slash); jerr != nil {
			findings = append(findings, Finding{
				ID: "structure:jail:" + shortID(slash),
				Category: "structure", State: StateContradicted, Cause: CauseSelfDisagree,
				Detail: "Path outside jail skipped: " + fence(slash),
			})
			return nil
		}
		files[slash] = struct{}{}
		files[filepath.Base(path)] = struct{}{}
		return nil
	})
	return files, findings
}

// TriageMarkdown returns a pasteable case-ticket note.
// Terse (default): summary line + top items. Full: complete dump + dropped list.
func TriageMarkdown(rep Report, full bool) string {
	var b strings.Builder
	base := filepath.Base(rep.BundleRoot)
	b.WriteString("# Curbpack review — triage note\n\n")
	b.WriteString("> ")
	b.WriteString(rep.Disclaimer)
	b.WriteString("\n\n")

	if !full {
		fmt.Fprintf(&b, "%s — %d genuine unresolved · %d contradicted",
			base, rep.UnconfirmedGenuine, rep.ContradictedCount)
		if rep.UnconfirmedExtractor > 0 {
			fmt.Fprintf(&b, " · %d extractor", rep.UnconfirmedExtractor)
		}
		b.WriteByte('\n')
		fmt.Fprintf(&b, "Confirmed %d · producer %d · external %d. (--full for all)\n\n",
			rep.ConfirmedCount, rep.UnconfirmedProducer, rep.UnconfirmedExternal)

		top := 0
		for _, f := range rep.Findings {
			if f.State != StateContradicted && !(f.State == StateUnconfirmed && f.Cause == CauseGenuine) {
				continue
			}
			if top >= 5 {
				break
			}
			fmt.Fprintf(&b, "  · **[%s]** `%s` — %s\n", f.State, f.ID, f.Detail)
			top++
		}
		if top > 0 {
			b.WriteByte('\n')
		}
		b.WriteString("---\n")
		b.WriteString("Generated by `curbpack review` (offline). Exit 1 if any finding is contradicted.\n")
		return b.String()
	}

	fmt.Fprintf(&b, "- **Bundle:** `%s`\n", rep.BundleRoot)
	fmt.Fprintf(&b, "- **Classifier:** `%s`\n", rep.ClassifierVersion)
	fmt.Fprintf(&b, "- **Confirmed:** %d · **Unconfirmed:** %d (producer %d · extractor %d · genuine %d · external %d) · **Contradicted:** %d (self_disagree %d)\n",
		rep.ConfirmedCount, rep.UnconfirmedCount,
		rep.UnconfirmedProducer, rep.UnconfirmedExtractor, rep.UnconfirmedGenuine, rep.UnconfirmedExternal,
		rep.ContradictedCount, rep.ContradictedSelfDisagree)
	fmt.Fprintf(&b, "- **Dropped tokens:** %d\n\n", rep.DroppedCount)

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
			cause := ""
			if f.Cause != "" {
				cause = " (" + string(f.Cause) + ")"
			}
			fmt.Fprintf(&b, "- **[%s]** `%s`%s — %s\n", f.State, f.ID, cause, f.Detail)
		}
		b.WriteByte('\n')
	}
	writeSection("Contradicted", StateContradicted)
	writeSection("Unconfirmed", StateUnconfirmed)
	writeSection("Confirmed", StateConfirmed)

	if len(rep.Dropped) > 0 {
		b.WriteString("## Dropped (not references)\n\n")
		for _, d := range rep.Dropped {
			fmt.Fprintf(&b, "- `%s`\n", d)
		}
		b.WriteByte('\n')
	}

	b.WriteString("---\n")
	b.WriteString("Generated by `curbpack review --full` (offline). Exit 1 if any finding is contradicted.\n")
	return b.String()
}
