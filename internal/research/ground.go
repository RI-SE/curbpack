package research

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/claimid"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/paths"
)

// GroundingArtifact is one independent (non-agent) artifact a confirm screen can show.
type GroundingArtifact struct {
	Kind string // path | config
	Rel  string
}

// Catalog resolves inward cites: repo artifacts plus packet claim ids.
// Heal stubs and agent-cache paths never resolve as path artifacts.
type Catalog struct {
	RepoRoot string
	Token    string
	ClaimIDs map[string]struct{}
}

var (
	reBacktick   = regexp.MustCompile("`([^`]+)`")
	reTestName   = regexp.MustCompile(`\bTest[A-Z][A-Za-z0-9_]+\b`)
	reSHA        = regexp.MustCompile(`\b[0-9a-f]{7,40}\b`)
	reHTTPS      = regexp.MustCompile(`https://[^\s)>\]]+`)
	reConfigFile = regexp.MustCompile(`\.(?:curbpack|cyberready)\.json\b`)
	// Positive regulatory assertions — instructional stub copy must not match.
	rePositiveFact = regexp.MustCompile(`(?i)\b(implements (the )?(CRA|CE |IEC|ISO)|complies with|compliant with|conforms to|certified (under|to|as)|is CRA[- ]compliant|are CRA[- ]compliant|meets (the )?essential requirements|(covers|satisfies|fulfills|fulfils)\s+(the )?(CRA|Annex))\b`)
)

// NewCatalog builds inward resolution from repo + packet requirements.
func NewCatalog(repoRoot string, pkt Packet) Catalog {
	c := Catalog{
		RepoRoot: repoRoot,
		ClaimIDs: map[string]struct{}{},
	}
	if t, ok := packs.RepoToken(repoRoot); ok {
		c.Token = t
	}
	for _, r := range pkt.Requirements {
		id := strings.TrimSpace(r.GateID)
		if id != "" {
			c.ClaimIDs[id] = struct{}{}
		}
	}
	return c
}

// IndependentGrounding lists confirm-displayable artifacts the agent did not author.
// Heal stubs (DefaultScaffoldBody overlap, including token insertion) and cache paths are skipped.
func IndependentGrounding(repoRoot string, rels []string) []GroundingArtifact {
	token, _ := packs.RepoToken(repoRoot)
	var out []GroundingArtifact
	seen := map[string]struct{}{}
	for _, rel := range rels {
		rel = filepath.ToSlash(strings.TrimSpace(rel))
		if rel == "" {
			continue
		}
		if !independentPath(repoRoot, rel, token) {
			continue
		}
		if _, ok := seen[rel]; ok {
			continue
		}
		seen[rel] = struct{}{}
		out = append(out, GroundingArtifact{Kind: "path", Rel: rel})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Rel < out[j].Rel })
	return out
}

// NotIndependent lists existing prose paths that are not independent (heal stub, empty, cache).
func NotIndependent(repoRoot string, rels []string) []string {
	indep := map[string]struct{}{}
	for _, a := range IndependentGrounding(repoRoot, rels) {
		indep[a.Rel] = struct{}{}
	}
	var out []string
	seen := map[string]struct{}{}
	for _, rel := range rels {
		rel = filepath.ToSlash(strings.TrimSpace(rel))
		if rel == "" {
			continue
		}
		if _, ok := indep[rel]; ok {
			continue
		}
		if _, ok := seen[rel]; ok {
			continue
		}
		p := filepath.Join(repoRoot, filepath.FromSlash(rel))
		st, err := os.Stat(p)
		if err != nil || st.IsDir() {
			continue
		}
		seen[rel] = struct{}{}
		out = append(out, rel)
	}
	sort.Strings(out)
	return out
}

func independentPath(repoRoot, rel, token string) bool {
	if paths.IsCacheRel(rel) {
		return false
	}
	if err := packs.ValidateRelPath(rel); err != nil {
		return false
	}
	p := filepath.Join(repoRoot, filepath.FromSlash(rel))
	data, err := os.ReadFile(p)
	if err != nil {
		return false
	}
	if strings.TrimSpace(string(data)) == "" {
		return false
	}
	if packs.ScaffoldOverlap(string(data), rel, token) {
		return false
	}
	return true
}

func (c Catalog) knownID(id string, pkt Packet) bool {
	id = strings.TrimSpace(id)
	if id == "" {
		return false
	}
	for _, s := range pkt.Sources {
		if s.ID == id {
			return true
		}
	}
	if _, ok := c.ClaimIDs[id]; ok {
		return true
	}
	if c.pathOK(id) {
		return true
	}
	if reTestName.MatchString(id) && c.hasTest(id) {
		return true
	}
	if c.hasCommit(id) {
		return true
	}
	if id == ".curbpack.json" || id == ".cyberready.json" || id == "packs" {
		return c.configPresent()
	}
	if c.hasMetric(id) {
		return true
	}
	return false
}

func (c Catalog) pathOK(rel string) bool {
	rel = filepath.ToSlash(strings.TrimSpace(rel))
	rel = strings.Trim(rel, "\"'")
	if rel == "" || c.RepoRoot == "" {
		return false
	}
	return independentPath(c.RepoRoot, rel, c.Token)
}

func (c Catalog) configPresent() bool {
	if c.RepoRoot == "" {
		return false
	}
	for _, name := range []string{paths.ConfigFile, paths.LegacyConfigFile} {
		st, err := os.Stat(filepath.Join(c.RepoRoot, name))
		if err == nil && !st.IsDir() {
			return true
		}
	}
	return false
}

func (c Catalog) hasCommit(id string) bool {
	if c.RepoRoot == "" {
		return false
	}
	id = strings.ToLower(strings.TrimSpace(id))
	if len(id) < 7 {
		return false
	}
	sha, err := gitutil.HeadSHA(c.RepoRoot)
	if err != nil {
		return false
	}
	sha = strings.ToLower(strings.TrimSpace(sha))
	return sha == id || strings.HasPrefix(sha, id)
}

func (c Catalog) hasTest(name string) bool {
	if c.RepoRoot == "" || !strings.HasPrefix(name, "Test") {
		return false
	}
	needle := []byte("func " + name + "(")
	found := false
	n := 0
	_ = filepath.WalkDir(c.RepoRoot, func(p string, d os.DirEntry, err error) error {
		if err != nil || found {
			return nil
		}
		if d.IsDir() {
			switch d.Name() {
			case ".git", "node_modules", "vendor":
				return filepath.SkipDir
			}
			return nil
		}
		if !strings.HasSuffix(d.Name(), "_test.go") {
			return nil
		}
		n++
		if n > 400 {
			return filepath.SkipAll
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return nil
		}
		if strings.Contains(string(b), string(needle)) {
			found = true
			return filepath.SkipAll
		}
		return nil
	})
	return found
}

func (c Catalog) hasMetric(id string) bool {
	if c.RepoRoot == "" || id == "" {
		return false
	}
	data, err := os.ReadFile(paths.ResolveUnderCache(c.RepoRoot, "instrument.json"))
	if err != nil {
		return false
	}
	var m map[string]json.RawMessage
	if json.Unmarshal(data, &m) != nil {
		return false
	}
	_, ok := m[id]
	return ok
}

func lineHasAllowlistedURL(line string) bool {
	for _, raw := range reHTTPS.FindAllString(line, -1) {
		raw = strings.TrimRight(raw, ".,;:!?*")
		if ValidateSourceURL(raw) == nil {
			return true
		}
	}
	return false
}

func (c Catalog) lineHitsArtifact(line string, pkt Packet) bool {
	for _, m := range reBacktick.FindAllStringSubmatch(line, -1) {
		tok := strings.TrimSpace(m[1])
		if c.knownID(tok, pkt) || c.pathOK(tok) {
			return true
		}
	}
	if reConfigFile.FindString(line) != "" && c.configPresent() {
		return true
	}
	for _, id := range claimid.FindAll(line) {
		if !claimid.IsClaim(id) {
			continue
		}
		if c.knownID(id, pkt) {
			return true
		}
	}
	for _, name := range reTestName.FindAllString(line, -1) {
		if c.hasTest(name) {
			return true
		}
	}
	for _, sha := range reSHA.FindAllString(line, -1) {
		if c.hasCommit(sha) {
			return true
		}
	}
	// Relative path tokens ending in a source-ish suffix.
	for _, f := range strings.Fields(line) {
		f = strings.Trim(f, ".,;:()[]{}")
		if strings.Contains(f, "/") || strings.HasSuffix(f, ".md") || strings.HasSuffix(f, ".txt") || strings.HasSuffix(f, ".json") {
			if c.pathOK(f) {
				return true
			}
		}
	}
	return false
}

func lineGrounded(line string, pkt Packet, cat Catalog) bool {
	if lineHasAllowlistedURL(line) {
		return true
	}
	if cat.lineHitsArtifact(line, pkt) {
		return true
	}
	if lineHasCite(line) {
		// Markers resolved globally; a line with only known markers is grounded.
		ids := citeIDsOnLine(line)
		if len(ids) == 0 {
			return false
		}
		for _, id := range ids {
			if !cat.knownID(id, pkt) {
				return false
			}
		}
		return true
	}
	return false
}

func citeIDsOnLine(line string) []string {
	var ids []string
	for _, m := range reFootnoteRef.FindAllStringSubmatch(line, -1) {
		ids = append(ids, m[1])
	}
	for _, m := range reCiteComment.FindAllStringSubmatch(line, -1) {
		ids = append(ids, m[1])
	}
	if m := reSourceLine.FindStringSubmatch(line); m != nil {
		ids = append(ids, m[1])
	}
	return ids
}

func isPositiveAssertion(line string) bool {
	return rePositiveFact.FindString(line) != ""
}
