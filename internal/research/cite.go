package research

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// CiteCheckResult is the deterministic groundedness report.
type CiteCheckResult struct {
	OK       bool     `json:"ok"`
	Errors   []string `json:"errors,omitempty"`
	Warnings []string `json:"warnings,omitempty"`
}

var (
	reFootnoteRef  = regexp.MustCompile(`\[\^([a-zA-Z0-9_-]+)\]`)
	reCiteComment  = regexp.MustCompile(`<!--\s*cite:([a-zA-Z0-9_-]+)\s*-->`)
	reSourceLine   = regexp.MustCompile(`(?i)^\s*Source:\s*([a-zA-Z0-9_-]+)\s*$`)
	reBannedClaims = regexp.MustCompile(`(?i)\b(we are (CE[- ])?certified|product is certified|officially certified|cyberready certifies|notified[- ]body approved|approved by (a )?notified body|conformity assessment (complete|passed|successful)|CE marking (issued|granted|obtained)|is CE[- ]marked|has been CE[- ]marked|certified conformity|we are CRA compliant|CRA compliant|compliant with (the )?CRA|compliant with CE|certified under (the )?[A-Z0-9][-A-Z0-9 ]+|approved under (the )?[A-Z0-9][-A-Z0-9 ]+|is certified (for|against|to) )\b`)
	// Fence-like negation only — bare "informational" / "structural_draft" must NOT
	// greenlight banned claims (e.g. "We are CRA compliant — informational only.").
	reSafeNegation  = regexp.MustCompile(`(?i)not (a |an )?(conformity|certif|CE)|does not certify|never claim|no certification|not CE|not conformity assessment|structural (file/header )?gates|prepares evidence for human review|not a conformity assessment`)
	reClaimsHeading = regexp.MustCompile(`(?im)^#{1,3}\s+Claims\s*$`)
)

// CiteCheck validates draft markdown against a research packet (RAGChecker-lite).
// Rules:
//  1. Every [^id] / Source: id / <!-- cite:id --> must resolve to sources[].id, a pack claim id, or a repo artifact
//  2. Banned claim phrases (claim-safety subset + CRA/CE compliant) fail unless claim-safe negation on same line
//  3. require_headers for packet requirements whose path matches the draft path must appear
//  4. Under a "## Claims" (or #/###) section, every non-empty prose line must be grounded
//  5. Positive regulatory assertions anywhere must be grounded (repo artifact or allowlisted cite)
//     Heal stubs / DefaultScaffoldBody are not grounding artifacts.
func CiteCheck(pkt Packet, draftPath string, draft []byte) CiteCheckResult {
	return citeCheck(pkt, draftPath, draft, NewCatalog("", pkt))
}

func citeCheck(pkt Packet, draftPath string, draft []byte, cat Catalog) CiteCheckResult {
	var res CiteCheckResult
	text := string(draft)
	lines := strings.Split(text, "\n")

	// Collect cite markers — must resolve inward (packet source, claim id, or repo artifact).
	var markers []string
	for _, m := range reFootnoteRef.FindAllStringSubmatch(text, -1) {
		markers = append(markers, m[1])
	}
	for _, m := range reCiteComment.FindAllStringSubmatch(text, -1) {
		markers = append(markers, m[1])
	}
	for _, line := range lines {
		if m := reSourceLine.FindStringSubmatch(line); m != nil {
			markers = append(markers, m[1])
		}
	}
	for _, id := range markers {
		if !cat.knownID(id, pkt) {
			res.Errors = append(res.Errors, fmt.Sprintf("uncited/unknown source id %q (not a packet source, claim id, or repo artifact)", id))
		}
	}

	// Claim-safety subset
	for i, line := range lines {
		if reSafeNegation.FindString(line) != "" {
			continue
		}
		if m := reBannedClaims.FindString(line); m != "" {
			res.Errors = append(res.Errors, fmt.Sprintf("line %d: banned claim phrase %q", i+1, m))
		}
	}

	// require_headers for matching paths
	rel := filepath.ToSlash(draftPath)
	for _, req := range pkt.Requirements {
		if len(req.RequireHeaders) == 0 {
			continue
		}
		if !pathMatchesReq(rel, req.Path) {
			continue
		}
		for _, h := range req.RequireHeaders {
			if !strings.Contains(text, h) {
				res.Errors = append(res.Errors, fmt.Sprintf("missing require_header %q for gate %s", h, req.GateID))
			}
		}
	}

	// Claims section: every non-empty non-heading line needs grounding.
	if idx := findClaimsSection(lines); idx >= 0 {
		for i := idx + 1; i < len(lines); i++ {
			line := lines[i]
			trim := strings.TrimSpace(line)
			if trim == "" {
				continue
			}
			if strings.HasPrefix(trim, "#") {
				break // next section
			}
			if strings.HasPrefix(trim, ">") || strings.HasPrefix(trim, "---") {
				continue
			}
			if !lineGrounded(line, pkt, cat) {
				res.Errors = append(res.Errors, fmt.Sprintf("Claims section line %d: ungrounded assertion (repo artifact, claim id, or allowlisted cite)", i+1))
			}
		}
	}

	// Positive regulatory assertions outside Claims also need grounding.
	for i, line := range lines {
		if reSafeNegation.FindString(line) != "" {
			continue
		}
		if !isPositiveAssertion(line) {
			continue
		}
		if lineGrounded(line, pkt, cat) {
			continue
		}
		res.Errors = append(res.Errors, fmt.Sprintf("line %d: ungrounded factual assertion (repo artifact or allowlisted cite)", i+1))
	}

	res.OK = len(res.Errors) == 0
	return res
}

func pathMatchesReq(draftRel, reqPath string) bool {
	reqPath = strings.TrimSpace(reqPath)
	if reqPath == "" {
		return false
	}
	draftRel = filepath.ToSlash(draftRel)
	for _, p := range strings.Split(reqPath, ",") {
		p = filepath.ToSlash(strings.TrimSpace(p))
		if p == "" {
			continue
		}
		// Exact path, or draft ends with "/"+p (path-segment boundary).
		// Never basename-only HasSuffix (e.g. "evil_risk_assessment.md" vs "risk_assessment.md").
		if draftRel == p || strings.HasSuffix(draftRel, "/"+p) {
			return true
		}
	}
	return false
}

func findClaimsSection(lines []string) int {
	for i, line := range lines {
		if reClaimsHeading.MatchString(line) {
			return i
		}
	}
	return -1
}

func lineHasCite(line string) bool {
	return reFootnoteRef.MatchString(line) || reCiteComment.MatchString(line) || reSourceLine.MatchString(line)
}

// CiteCheckFile loads draft from disk relative to repo root (or absolute).
func CiteCheckFile(pkt Packet, repoRoot, draftRel string) (CiteCheckResult, error) {
	path := draftRel
	if !filepath.IsAbs(path) {
		path = filepath.Join(repoRoot, filepath.FromSlash(draftRel))
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return CiteCheckResult{}, err
	}
	rel := draftRel
	if filepath.IsAbs(draftRel) && repoRoot != "" {
		if r, err := filepath.Rel(repoRoot, draftRel); err == nil {
			rel = filepath.ToSlash(r)
		}
	}
	return citeCheck(pkt, rel, data, NewCatalog(repoRoot, pkt)), nil
}

// CiteCheckProsePaths runs cite-check on each existing prose path; aggregates errors.
func CiteCheckProsePaths(repoRoot string, pkt Packet, paths []string) CiteCheckResult {
	var all CiteCheckResult
	all.OK = true
	cat := NewCatalog(repoRoot, pkt)
	for _, rel := range paths {
		p := filepath.Join(repoRoot, filepath.FromSlash(rel))
		st, err := os.Stat(p)
		if err != nil || st.IsDir() {
			continue
		}
		data, err := os.ReadFile(p)
		if err != nil {
			all.OK = false
			all.Errors = append(all.Errors, fmt.Sprintf("%s: %v", rel, err))
			continue
		}
		res := citeCheck(pkt, rel, data, cat)
		for _, e := range res.Errors {
			all.Errors = append(all.Errors, fmt.Sprintf("%s: %s", rel, e))
		}
		all.Warnings = append(all.Warnings, res.Warnings...)
	}
	all.OK = len(all.Errors) == 0
	return all
}
