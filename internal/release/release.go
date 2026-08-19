package release

import (
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/release/templates"
	"github.com/afelin/curbpack/internal/research"
	"github.com/afelin/curbpack/internal/sbom"
	"github.com/afelin/curbpack/internal/tty"
	"github.com/afelin/curbpack/internal/validate"
	"github.com/afelin/curbpack/internal/vex"
)

// Options for prepare-release.
type Options struct {
	RepoRoot          string
	PackIDs           []string
	OutDir            string
	AllowFailingGates bool // if false, non-zero exit when gates fail (after writing review pack)
}

// Prepare writes the review pack: Annex VII drafts (if missing), three-layer reports, buyer HTML.
func Prepare(opts Options) error {
	root := opts.RepoRoot
	out := opts.OutDir
	if out == "" {
		out = filepath.Join(root, "review-pack")
	}
	if err := os.MkdirAll(out, 0o755); err != nil {
		return err
	}

	// Ensure witness / annex scaffolds exist (edit in any markdown editor).
	if err := ensureWitnessTemplates(root); err != nil {
		return err
	}

	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: opts.PackIDs, Quiet: true})
	if err != nil {
		return err
	}

	var prepErrs []error
	record := func(err error) {
		if err != nil {
			prepErrs = append(prepErrs, err)
		}
	}

	// Layer 1: machine JSON
	layer1, _ := json.MarshalIndent(res.Payload, "", "  ")
	record(os.WriteFile(filepath.Join(out, "01-gate-failures.json"), append(layer1, '\n'), 0o644))

	// Layer 2: semantic markdown for agents
	md := validate.SemanticMarkdown(res.Payload)
	if len(res.Payload.Failures) == 0 {
		md = "# COMPLIANCE STATUS: ALL GATES PASSED\n\nDeterministic pack evaluation found no violations.\n\n" +
			"**Note:** This is evidence preparation for human review — not a certification.\n"
	}
	record(os.WriteFile(filepath.Join(out, "02-action-report.md"), []byte(md), 0o644))

	// Layer 3: executive summary markdown
	execMD := executiveSummary(res)
	record(os.WriteFile(filepath.Join(out, "03-executive-summary.md"), []byte(execMD), 0o644))

	// SBOM summary + CycloneDX 1.5 (best-effort from lockfile)
	evidenceDir := filepath.Join(root, ".github", "curbpack", "evidence")
	record(os.MkdirAll(evidenceDir, 0o755))
	sbomSummary, sbomErr := sbom.FromLockfiles(root)
	sbomPath := filepath.Join(out, "04-sbom-summary.json")
	if sbomErr != nil {
		record(os.WriteFile(sbomPath, []byte(`{"status":"unavailable","detail":`+jsonString(sbomErr.Error())+"}\n"), 0o644))
	} else {
		cdxPath := filepath.Join(evidenceDir, "sbom.cdx.json")
		if _, written, err := sbom.WriteCycloneDX(root, cdxPath); err == nil {
			sbomSummary.CycloneDXPath = written
			sbomSummary.Format = "CycloneDX-1.5"
			record(copyFile(written, filepath.Join(out, "04-sbom.cdx.json")))
		} else {
			record(fmt.Errorf("cyclonedx: %w", err))
		}
		b, _ := json.MarshalIndent(sbomSummary, "", "  ")
		record(os.WriteFile(sbomPath, append(b, '\n'), 0o644))
	}

	// Pending OpenVEX from dependency-shaped findings only (gates stay in IR).
	vexDoc := vex.FromGateFailures(filepath.Base(root), res.Payload)
	vexPath, vexWriteErr := vex.Write(root, vexDoc, filepath.Join(evidenceDir, "vex-pending.json"))
	if vexWriteErr != nil {
		record(fmt.Errorf("vex: %w", vexWriteErr))
	} else {
		record(copyFile(vexPath, filepath.Join(out, "05-vex-draft.json")))
	}

	// SARIF layer (same mapper as CLI export --sarif)
	sarifDoc := exportx.FromGateFailures(res.Payload, root)
	sarifBytes, _ := json.MarshalIndent(sarifDoc, "", "  ")
	record(os.WriteFile(filepath.Join(out, "06-gate-failures.sarif"), append(sarifBytes, '\n'), 0o644))
	record(os.MkdirAll(filepath.Join(root, ".github", "curbpack", "cache"), 0o755))
	record(os.WriteFile(filepath.Join(root, ".github", "curbpack", "cache", "curbpack.sarif"), append(sarifBytes, '\n'), 0o644))

	// Informational watchlist ∩ SBOM join
	if joinPath, err := exportx.WriteWatchlistJoin(root, ""); err != nil {
		record(fmt.Errorf("watchlist join: %w", err))
	} else {
		record(copyFile(joinPath, filepath.Join(out, "07-watchlist-sbom-join.json")))
	}
	// Buyer one-pager HTML — skip rewrite when gate snapshot fingerprint unchanged.
	htmlDoc := buyerOnePager(root, res)
	onepagerPath := filepath.Join(out, "buyer-onepager.html")
	wrote, err := writeOnePagerIfChanged(onepagerPath, htmlDoc)
	if err != nil {
		record(fmt.Errorf("buyer one-pager: %w", err))
	} else if wrote {
		tty.PrintStatus("Buyer one-pager", true, onepagerPath)
	} else {
		tty.PrintStatus("Buyer one-pager", true, onepagerPath+" (unchanged)")
	}

	// Copy / refresh proof page into review-pack and repo proof/
	proof := templates.ProofPageHTML()
	record(os.MkdirAll(filepath.Join(root, "proof"), 0o755))
	record(os.WriteFile(filepath.Join(root, "proof", "index.html"), []byte(proof), 0o644))
	record(os.WriteFile(filepath.Join(out, "proof-index.html"), []byte(proof), 0o644))

	tty.PrintStatus("Review pack", true, out)
	if !res.Passed {
		fmt.Printf("%s\n", tty.C(tty.Yellow, "[!] Gates still failing — pack is for remediation review, not release sign-off."))
	}
	if tty.IsTerminal {
		tty.RenderThermometer(res.Score)
	}
	if !res.Passed && !opts.AllowFailingGates {
		prepErrs = append(prepErrs, fmt.Errorf("gates failing — pass --allow-failing-gates to accept a remediation review pack"))
	}
	return errors.Join(prepErrs...)
}

func jsonString(s string) string {
	b, _ := json.Marshal(s)
	return string(b)
}

// writeIfChanged writes data only when missing or content hash differs. Returns true if written.
func writeIfChanged(path string, data []byte) (bool, error) {
	want := sha256.Sum256(data)
	if prev, err := os.ReadFile(path); err == nil {
		got := sha256.Sum256(prev)
		if want == got {
			return false, nil
		}
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return false, err
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return false, err
	}
	return true, nil
}

// writeOnePagerIfChanged skips rewrite when the stable gate fingerprint matches
// (ignores wall-clock "Generated" timestamps so prepare-release is quiet).
func writeOnePagerIfChanged(path, htmlDoc string) (bool, error) {
	fp := onePagerFingerprint(htmlDoc)
	if prev, err := os.ReadFile(path); err == nil {
		if onePagerFingerprint(string(prev)) == fp && fp != "" {
			return false, nil
		}
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return false, err
	}
	if err := os.WriteFile(path, []byte(htmlDoc), 0o644); err != nil {
		return false, err
	}
	return true, nil
}

func onePagerFingerprint(htmlDoc string) string {
	// Prefer explicit marker; fall back to hashing body without Generated line.
	const marker = "<!-- curbpack-onepager-fp:"
	if i := strings.Index(htmlDoc, marker); i >= 0 {
		rest := htmlDoc[i+len(marker):]
		if j := strings.Index(rest, " -->"); j >= 0 {
			return rest[:j]
		}
	}
	var b strings.Builder
	for _, line := range strings.Split(htmlDoc, "\n") {
		if strings.Contains(line, "Generated ") {
			continue
		}
		b.WriteString(line)
		b.WriteByte('\n')
	}
	sum := sha256.Sum256([]byte(b.String()))
	return fmt.Sprintf("%x", sum[:16])
}

func copyFile(src, dst string) error {
	if src == "" {
		return nil
	}
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, data, 0o644)
}

func ensureWitnessTemplates(root string) error {
	ids, err := config.ResolvePackIDs(root, nil)
	if err != nil {
		ids = []string{"cra-baseline"}
	}
	paths, err := packs.ScaffoldPaths(ids)
	if err != nil || len(paths) == 0 {
		paths = []string{
			"docs/annex-vii/risk_assessment.md",
			"docs/annex-vii/support_period.md",
			"docs/annex-vii/user_manual_security.md",
			"docs/incident/art14-path.md",
		}
	}
	for _, rel := range paths {
		path, clean, err := validate.SafeJoin(root, rel)
		if err != nil {
			return fmt.Errorf("scaffold path refused: %s: %w", rel, err)
		}
		if _, err := os.Stat(path); err == nil {
			continue
		}
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(path, []byte(packs.DefaultScaffoldBody(clean)), 0o644); err != nil {
			return err
		}
	}
	return nil
}

func executiveSummary(res validate.Result) string {
	var b strings.Builder
	b.WriteString("# Executive Summary — Supplier Readiness\n\n")
	b.WriteString("> Curbpack prepares evidence for **human review**. It does not certify conformity.\n\n")
	fmt.Fprintf(&b, "- **Generated:** %s\n", res.Payload.Timestamp)
	fmt.Fprintf(&b, "- **Packs:** %s\n", res.Payload.PackID)
	fmt.Fprintf(&b, "- **Readiness score:** %d%%\n", res.Score)
	fmt.Fprintf(&b, "- **Open findings:** %d\n\n", len(res.Payload.Failures))
	if res.Passed {
		b.WriteString("All deterministic gates passed. Proceed to human review of Annex VII / medtech drafts, then `curbpack attest`.\n")
		return b.String()
	}
	b.WriteString("## Top actions\n\n")
	for i, f := range res.Payload.Failures {
		if i >= 8 {
			fmt.Fprintf(&b, "\n_…and %d more — see 02-action-report.md_\n", len(res.Payload.Failures)-8)
			break
		}
		fmt.Fprintf(&b, "%d. **[%s]** %s — %s\n", i+1, f.GateID, f.Severity, f.Remediation.ActionRequired)
	}
	return b.String()
}

func buyerOnePager(root string, res validate.Result) string {
	name := filepath.Base(root)
	bind, _ := attest.LatestBind(root)
	line, class, unsignedLoud := attest.AttestDisplay(bind)
	var failures []templates.OnePagerFailure
	for _, f := range res.Payload.Failures {
		failures = append(failures, templates.OnePagerFailure{
			GateID:      f.GateID,
			Severity:    f.Severity,
			Description: f.SanitizedDescription,
		})
	}
	var cover []templates.OnePagerCoverRow
	if qs, err := exportx.CollectBuyerQuestions(root, nil, res); err == nil {
		for i, q := range qs {
			if i >= 12 {
				break
			}
			cover = append(cover, templates.OnePagerCoverRow{
				Path:     q.ArtifactPath,
				Question: q.HumanQuestion,
			})
		}
	}
	dto := templates.OnePagerDTO{
		RepoName:       name,
		Score:          res.Score,
		Passed:         res.Passed,
		PackID:         res.Payload.PackID,
		PackLabels:     exportx.PackPlainNames(res.Payload.PackID),
		Timestamp:      res.Payload.Timestamp,
		Failures:       failures,
		CoverRows:      cover,
		Bind:           bind,
		AttestLine:     line,
		AttestClass:    class,
		UnsignedLoud:   unsignedLoud,
		ProvenanceHTML: provenanceDL(res.Payload.PackID, bind, line, unsignedLoud),
		SourcesHTML:    sourcesStrip(root, res.Payload.PackID),
		FooterPrefix:   footerHTML(line, unsignedLoud),
	}
	return templates.BuyerOnePagerHTML(dto)
}

func footerHTML(line string, unsignedLoud bool) string {
	if unsignedLoud {
		return `<span class="unsigned-foot">` + html.EscapeString(line) + `</span>`
	}
	return html.EscapeString(line) + " · "
}

func provenanceDL(packID string, bind attest.BindInfo, line string, unsignedLoud bool) string {
	commit := bind.CommitSHA
	if commit == "" || commit == "unknown" {
		commit = "(no commit)"
	}
	state := bind.StateHash
	if state == "" {
		state = "(none — run curbpack attest after human review)"
	}
	signer := bind.Signer
	if signer == "" {
		signer = "local-unsigned"
	}
	touch := bind.UserTouch
	if touch == "" {
		touch = "not-verified"
	}
	signOff := "Pending human review. A reviewer runs curbpack attest; ssh-agent-signed = human-bound on this commit."
	if !unsignedLoud {
		signOff = "Human-bound on this commit (ssh-agent-signed). Still not conformity assessment."
	}
	var b strings.Builder
	b.WriteString(`<dl class="prov">`)
	fmt.Fprintf(&b, "<dt>Rule packs</dt><dd>%s</dd>\n", html.EscapeString(packID))
	fmt.Fprintf(&b, "<dt>Commit</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(commit)))
	fmt.Fprintf(&b, "<dt>Attest</dt><dd>%s</dd>\n", html.EscapeString(line))
	fmt.Fprintf(&b, "<dt>Signer</dt><dd>%s</dd>\n", html.EscapeString(signer))
	fmt.Fprintf(&b, "<dt>User touch</dt><dd>%s</dd>\n", html.EscapeString(touch))
	fmt.Fprintf(&b, "<dt>state_hash</dt><dd>%s</dd>\n", html.EscapeString(state))
	if bind.SBOMDigest != "" {
		fmt.Fprintf(&b, "<dt>sbom_digest</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(bind.SBOMDigest)))
	}
	if bind.VEXDigest != "" {
		fmt.Fprintf(&b, "<dt>vex_digest</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(bind.VEXDigest)))
	}
	if name := strings.TrimSpace(bind.ReviewedBy); name != "" {
		fmt.Fprintf(&b, "<dt>Reviewed by</dt><dd>%s — recorded review, not assessment.</dd>\n", html.EscapeString(name))
	}
	fmt.Fprintf(&b, "<dt>Human sign-off</dt><dd>%s</dd>\n", html.EscapeString(signOff))
	b.WriteString(`<dt>Verify</dt><dd>proof/index.html + local evidence pointer (client-side hash compare)</dd>`)
	b.WriteString(`</dl>`)
	return b.String()
}

// sourcesStrip adds claim-safe allowlisted citation links when a research packet exists
// with PackIDs matching the release packs (or falls back to composed pack citation URLs).
// Informational only — not conformity.
func sourcesStrip(root, packIDCSV string) string {
	var urls []string
	seen := map[string]struct{}{}
	add := func(u string) {
		u = strings.TrimSpace(u)
		if u == "" {
			return
		}
		if err := research.ValidateSourceURL(u); err != nil {
			return
		}
		if _, ok := seen[u]; ok {
			return
		}
		seen[u] = struct{}{}
		urls = append(urls, u)
	}
	ids := strings.Split(packIDCSV, ",")
	var clean []string
	for _, id := range ids {
		id = strings.TrimSpace(id)
		if id != "" {
			clean = append(clean, id)
		}
	}
	if pkt, err := research.LoadPacket(root); err == nil && pkt != nil {
		if packIDSetsEqual(pkt.PackIDs, clean) {
			for _, s := range pkt.Sources {
				add(s.URL)
			}
		}
	}
	if len(urls) == 0 && len(clean) > 0 {
		if composed, _, err := packs.Compose(clean); err == nil {
			for _, c := range composed.Citations {
				add(c.URL)
			}
			for _, r := range composed.Rules {
				for _, c := range r.Citations {
					add(c.URL)
				}
			}
		}
	}
	if len(urls) == 0 {
		return ""
	}
	var b strings.Builder
	b.WriteString(`<p style="margin:1rem 0 0.35rem;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.04em;color:var(--muted);font-family:ui-monospace,Menlo,monospace">Sources (informational)</p>`)
	b.WriteString(`<ul style="margin:0;padding-left:1.1rem;font-size:0.85rem">`)
	for _, u := range urls {
		fmt.Fprintf(&b, `<li><a href="%s">%s</a></li>`, html.EscapeString(u), html.EscapeString(u))
	}
	b.WriteString(`</ul>`)
	b.WriteString(`<p style="margin:0.5rem 0 0;font-size:0.8rem;color:var(--muted)">Allowlisted official links for human reading — not a conformity assessment.</p>`)
	return b.String()
}

func packIDSetsEqual(a, b []string) bool {
	setA := map[string]struct{}{}
	for _, id := range a {
		id = strings.TrimSpace(id)
		if id != "" {
			setA[id] = struct{}{}
		}
	}
	setB := map[string]struct{}{}
	for _, id := range b {
		id = strings.TrimSpace(id)
		if id != "" {
			setB[id] = struct{}{}
		}
	}
	if len(setA) != len(setB) {
		return false
	}
	for id := range setA {
		if _, ok := setB[id]; !ok {
			return false
		}
	}
	return true
}

func truncateSHA(s string) string {
	if len(s) > 16 {
		return s[:12] + "…"
	}
	return s
}

type attestInfo struct {
	Line         string
	Class        string
	UnsignedLoud bool
	Commit       string
	StateHash    string
	Signer       string
	UserTouch    string
	SBOMDigest   string
	VEXDigest    string
}

// loadAttestInfo reads LatestBind for buyer-facing provenance.
func loadAttestInfo(root string) attestInfo {
	bind, _ := attest.LatestBind(root)
	line, class, unsignedLoud := attest.AttestDisplay(bind)
	return attestInfo{
		Line:         line,
		Class:        class,
		UnsignedLoud: unsignedLoud,
		Commit:       bind.CommitSHA,
		StateHash:    bind.StateHash,
		Signer:       bind.Signer,
		UserTouch:    bind.UserTouch,
		SBOMDigest:   bind.SBOMDigest,
		VEXDigest:    bind.VEXDigest,
	}
}

// ProofPageHTML delegates to templates package.
func ProofPageHTML() string {
	return templates.ProofPageHTML()
}

// WriteEvidenceBundle writes review-pack/evidence-bundle.html for offline handoff.
func WriteEvidenceBundle(root string, res validate.Result) (string, error) {
	out := filepath.Join(root, "review-pack", "evidence-bundle.html")
	onepagerPath := filepath.Join(root, "review-pack", "buyer-onepager.html")
	var onePagerMain string
	if b, err := os.ReadFile(onepagerPath); err == nil {
		onePagerMain = templates.ExtractOnePagerMain(string(b))
	}
	hpurlFrag := ""
	hpurlJSON := ""
	ptrPath := filepath.Join(root, ".github", "curbpack", "evidence", "hpurl-pointer.json")
	if b, err := os.ReadFile(ptrPath); err == nil {
		hpurlJSON = string(b)
		var ptr struct {
			HPURL string `json:"hpurl"`
		}
		if json.Unmarshal(b, &ptr) == nil {
			hpurlFrag = ptr.HPURL
		}
	}
	doc := templates.EvidenceBundleHTML(templates.BundleDTO{
		RepoName:       filepath.Base(root),
		Score:          res.Score,
		Passed:         res.Passed,
		Timestamp:      res.Payload.Timestamp,
		OnePagerBody:   onePagerMain,
		HPURLFragment:  hpurlFrag,
		HPURLEmbedJSON: hpurlJSON,
		Remediation:    !res.Passed,
	})
	if err := os.MkdirAll(filepath.Dir(out), 0o755); err != nil {
		return "", err
	}
	if err := os.WriteFile(out, []byte(doc), 0o644); err != nil {
		return "", err
	}
	return out, nil
}

// Unused import guard for ir in case of refactors
var _ = ir.Failure{}
