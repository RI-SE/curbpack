package research

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/paths"
)

func TestBuild_DeterministicSources_CRA(t *testing.T) {
	t.Parallel()
	pkt, err := Build(Options{PackIDs: []string{"cra-baseline"}})
	if err != nil {
		t.Fatal(err)
	}
	if pkt.SchemaVersion != SchemaVersion {
		t.Fatalf("schema %s", pkt.SchemaVersion)
	}
	if pkt.Claim != ClaimFence {
		t.Fatalf("claim fence")
	}
	if len(pkt.Sources) == 0 {
		t.Fatal("expected CRA citation source")
	}
	for _, s := range pkt.Sources {
		if err := ValidateSourceURL(s.URL); err != nil {
			t.Fatalf("source %s: %v", s.ID, err)
		}
		if !strings.HasPrefix(s.ID, "src-") {
			t.Fatalf("id %q", s.ID)
		}
	}
	d1 := StableSourcesDigest(pkt)
	pkt2, err := Build(Options{PackIDs: []string{"cra-baseline"}})
	if err != nil {
		t.Fatal(err)
	}
	if d1 != StableSourcesDigest(pkt2) {
		t.Fatal("sources digest not stable")
	}
	// Requirements include annex headers
	found := false
	for _, r := range pkt.Requirements {
		if r.GateID == "CRA-ANNEX-VII-RISK" && len(r.RequireHeaders) > 0 {
			found = true
			break
		}
	}
	if !found {
		t.Fatal("missing CRA-ANNEX-VII-RISK requirement")
	}
}

func TestBuild_HousePolicy_NoSourcesOK(t *testing.T) {
	t.Parallel()
	pkt, err := Build(Options{PackIDs: []string{"house-policy"}})
	if err != nil {
		t.Fatal(err)
	}
	if len(pkt.Sources) != 0 {
		t.Fatalf("house-policy should have no citation URLs, got %d", len(pkt.Sources))
	}
	if len(pkt.Requirements) == 0 {
		t.Fatal("expected house-policy requirements")
	}
}

func TestValidateSourceURL_Refuse(t *testing.T) {
	t.Parallel()
	cases := []string{
		"http://eur-lex.europa.eu/",
		"https://evil.example/",
		"ftp://www.iso.org/x",
		"",
	}
	for _, u := range cases {
		if err := ValidateSourceURL(u); err == nil {
			t.Fatalf("want refuse for %q", u)
		}
	}
	if err := ValidateSourceURL("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847"); err != nil {
		t.Fatal(err)
	}
}

func TestFetch_AllowlistAndFailOpen(t *testing.T) {
	t.Parallel()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
		_, _ = w.Write([]byte("<html><body><h1>Hello CRA</h1><p>Informational text.</p></body></html>"))
	}))
	defer srv.Close()

	// Direct server URL is not allowlisted — ValidateSourceURL fails before GET.
	sources := []Source{{ID: "src-1", URL: srv.URL}}
	FetchSourcesWith(sources, "2026-01-01T00:00:00Z", srv.Client())
	if sources[0].FetchError == "" {
		t.Fatal("expected fetch_error for non-allowlisted host")
	}

	// Allowlisted host via rewrite: inject custom transport that only serves when URL host matches allowlist check after we swap URL host in Validate — use a Doer that validates then hits test server.
	doer := &rewriteDoer{target: srv.URL, inner: srv.Client()}
	sources = []Source{{ID: "src-1", URL: "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847"}}
	FetchSourcesWith(sources, "2026-01-01T00:00:00Z", doer)
	if sources[0].FetchError != "" {
		t.Fatalf("fetch error: %s", sources[0].FetchError)
	}
	if sources[0].ContentSHA256 == "" || sources[0].Excerpt == "" {
		t.Fatalf("want excerpt+sha, got %#v", sources[0])
	}
	if !strings.Contains(sources[0].Excerpt, "Hello CRA") {
		t.Fatalf("excerpt %q", sources[0].Excerpt)
	}
}

type rewriteDoer struct {
	target string
	inner  *http.Client
}

func (r *rewriteDoer) Do(req *http.Request) (*http.Response, error) {
	if err := ValidateSourceURL(req.URL.String()); err != nil {
		return nil, err
	}
	u2, err := http.NewRequest(req.Method, r.target, nil)
	if err != nil {
		return nil, err
	}
	u2.Header = req.Header
	return r.inner.Do(u2)
}

func TestCiteCheck_ResolveAndClaims(t *testing.T) {
	t.Parallel()
	pkt := Packet{
		Sources: []Source{{ID: "src-1", URL: "https://eur-lex.europa.eu/"}},
		Requirements: []Requirement{{
			GateID:         "CRA-ANNEX-VII-RISK",
			Path:           "docs/annex-vii/risk_assessment.md",
			RequireHeaders: []string{"# Risk Assessment", "## Product Overview"},
		}},
	}
	good := []byte(`# Risk Assessment

## Product Overview

See official text. [^src-1]

## Claims

Product documentation is shaped like CRA Annex VII drafts. <!-- cite:src-1 -->
`)
	res := CiteCheck(pkt, "docs/annex-vii/risk_assessment.md", good)
	if !res.OK {
		t.Fatalf("want ok, errors=%v", res.Errors)
	}

	bad := []byte(`# Risk Assessment

## Claims

We are CRA compliant.
`)
	res = CiteCheck(pkt, "docs/annex-vii/risk_assessment.md", bad)
	if res.OK {
		t.Fatal("want fail")
	}
	joined := strings.Join(res.Errors, "\n")
	if !strings.Contains(joined, "banned claim") && !strings.Contains(joined, "uncited") {
		t.Fatalf("errors: %v", res.Errors)
	}

	unknown := []byte("Hello [^src-99]\n")
	res = CiteCheck(pkt, "x.md", unknown)
	if res.OK {
		t.Fatal("unknown cite should fail")
	}
}

func TestCiteCheck_InformationalOnlyDoesNotNegateBannedClaim(t *testing.T) {
	t.Parallel()
	pkt := Packet{Sources: []Source{{ID: "src-1", URL: "https://eur-lex.europa.eu/"}}}
	draft := []byte("We are CRA compliant — informational only.\n")
	res := CiteCheck(pkt, "x.md", draft)
	if res.OK {
		t.Fatal("bare 'informational' must not negate banned CRA claim")
	}
	joined := strings.Join(res.Errors, "\n")
	if !strings.Contains(joined, "banned claim") {
		t.Fatalf("want banned claim error, got %v", res.Errors)
	}
}

func TestPathMatchesReq_NoBasenameTrap(t *testing.T) {
	t.Parallel()
	req := "docs/annex-vii/risk_assessment.md"
	if !pathMatchesReq("docs/annex-vii/risk_assessment.md", req) {
		t.Fatal("exact path must match")
	}
	if !pathMatchesReq("repo/docs/annex-vii/risk_assessment.md", req) {
		t.Fatal("suffix with /+p must match")
	}
	// Basename-only HasSuffix trap: evil_risk_assessment.md ends with risk_assessment.md
	if pathMatchesReq("docs/annex-vii/evil_risk_assessment.md", "risk_assessment.md") {
		t.Fatal("basename-only suffix must not match")
	}
	if pathMatchesReq("other/risk_assessment.md", "docs/annex-vii/risk_assessment.md") {
		t.Fatal("different parent path must not match via basename")
	}
}

func TestCiteCheck_AllowlistedURLGroundsClaims(t *testing.T) {
	t.Parallel()
	pkt := Packet{}
	good := []byte(`## Claims

Annex structure follows the CRA text. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847
`)
	res := CiteCheck(pkt, "docs/annex-vii/risk_assessment.md", good)
	if !res.OK {
		t.Fatalf("allowlisted URL should ground Claims, errors=%v", res.Errors)
	}
	bad := []byte(`## Claims

Annex structure follows the CRA text. https://evil.example/law
`)
	res = CiteCheck(pkt, "docs/annex-vii/risk_assessment.md", bad)
	if res.OK {
		t.Fatal("non-allowlisted URL must not ground")
	}
}

func TestCiteCheck_ClaimIDGrounds(t *testing.T) {
	t.Parallel()
	pkt := Packet{Requirements: []Requirement{{GateID: "CRA-ANNEX-VII-RISK"}}}
	draft := []byte(`## Claims

Draft maps to CRA-ANNEX-VII-RISK.
`)
	res := CiteCheck(pkt, "docs/annex-vii/risk_assessment.md", draft)
	if !res.OK {
		t.Fatalf("claim id should ground, errors=%v", res.Errors)
	}
}

func TestCiteCheck_HealStubPathDoesNotGround(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte(packs.DefaultScaffoldBody("SECURITY.md")), 0o644); err != nil {
		t.Fatal(err)
	}
	pkt := Packet{}
	draft := []byte(`## Claims

This product implements CRA Annex VII — see SECURITY.md.
`)
	res := citeCheck(pkt, "docs/annex-vii/risk_assessment.md", draft, NewCatalog(dir, pkt))
	if res.OK {
		t.Fatal("heal-stub path must not ground a Claims line")
	}
}

func TestCiteCheck_RepoPathGrounds(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	body := "# Security\n\nHouse reporting contact and response process for this repo.\n"
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	pkt := Packet{}
	draft := []byte(`## Claims

House reporting lives in SECURITY.md.
`)
	res := citeCheck(pkt, "SECURITY.md", draft, NewCatalog(dir, pkt))
	if !res.OK {
		t.Fatalf("independent repo path should ground, errors=%v", res.Errors)
	}
}

func TestIndependentGrounding_SkipsCacheAndStubs(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	cache := filepath.Join(dir, filepath.FromSlash(paths.CacheRel))
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(cache, "notes.md"), []byte("agent cache prose\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte(packs.DefaultScaffoldBody("SECURITY.md")), 0o644); err != nil {
		t.Fatal(err)
	}
	arts := IndependentGrounding(dir, []string{"SECURITY.md", paths.CacheRel + "/notes.md"})
	if len(arts) != 0 {
		t.Fatalf("stub + cache must not count, got %#v", arts)
	}
}

func TestIndependentGrounding_AcceptsHumanProse(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("# Security\n\nHouse policy prose.\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	arts := IndependentGrounding(dir, []string{"SECURITY.md"})
	if len(arts) != 1 || arts[0].Rel != "SECURITY.md" {
		t.Fatalf("want SECURITY.md, got %#v", arts)
	}
}

func TestCiteCheck_UngroundedPositiveAssertion(t *testing.T) {
	t.Parallel()
	pkt := Packet{}
	draft := []byte("# Security\n\nThis product implements CRA Annex VII.\n")
	res := CiteCheck(pkt, "SECURITY.md", draft)
	if res.OK {
		t.Fatal("positive CRA assertion without grounding must refuse")
	}
}
