package release

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
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

	// Layer 1: machine JSON
	layer1, _ := json.MarshalIndent(res.Payload, "", "  ")
	if err := os.WriteFile(filepath.Join(out, "01-gate-failures.json"), append(layer1, '\n'), 0o644); err != nil {
		return err
	}

	// Layer 2: semantic markdown for agents
	md := validate.SemanticMarkdown(res.Payload)
	if len(res.Payload.Failures) == 0 {
		md = "# COMPLIANCE STATUS: ALL GATES PASSED\n\nDeterministic pack evaluation found no violations.\n\n" +
			"**Note:** This is evidence preparation for human review — not a certification.\n"
	}
	if err := os.WriteFile(filepath.Join(out, "02-action-report.md"), []byte(md), 0o644); err != nil {
		return err
	}

	// Layer 3: executive summary markdown
	execMD := executiveSummary(res)
	if err := os.WriteFile(filepath.Join(out, "03-executive-summary.md"), []byte(execMD), 0o644); err != nil {
		return err
	}

	// SBOM summary + CycloneDX 1.5 (best-effort from lockfile)
	evidenceDir := filepath.Join(root, ".github", "curbpack", "evidence")
	_ = os.MkdirAll(evidenceDir, 0o755)
	sbomSummary, sbomErr := sbom.FromLockfiles(root)
	sbomPath := filepath.Join(out, "04-sbom-summary.json")
	if sbomErr != nil {
		_ = os.WriteFile(sbomPath, []byte(`{"status":"unavailable","detail":`+jsonString(sbomErr.Error())+"}\n"), 0o644)
	} else {
		cdxPath := filepath.Join(evidenceDir, "sbom.cdx.json")
		if _, written, err := sbom.WriteCycloneDX(root, cdxPath); err == nil {
			sbomSummary.CycloneDXPath = written
			sbomSummary.Format = "CycloneDX-1.5"
			_ = copyFile(written, filepath.Join(out, "04-sbom.cdx.json"))
		}
		b, _ := json.MarshalIndent(sbomSummary, "", "  ")
		_ = os.WriteFile(sbomPath, append(b, '\n'), 0o644)
	}

	// Pending OpenVEX from dependency-shaped findings only (gates stay in IR).
	vexDoc := vex.FromGateFailures(filepath.Base(root), res.Payload)
	vexPath, _ := vex.Write(root, vexDoc, filepath.Join(evidenceDir, "vex-pending.json"))
	_ = copyFile(vexPath, filepath.Join(out, "05-vex-draft.json"))

	// SARIF layer (same mapper as CLI export --sarif)
	sarifDoc := exportx.FromGateFailures(res.Payload, root)
	sarifBytes, _ := json.MarshalIndent(sarifDoc, "", "  ")
	_ = os.WriteFile(filepath.Join(out, "06-gate-failures.sarif"), append(sarifBytes, '\n'), 0o644)
	_ = os.MkdirAll(filepath.Join(root, ".github", "curbpack", "cache"), 0o755)
	_ = os.WriteFile(filepath.Join(root, ".github", "curbpack", "cache", "curbpack.sarif"), append(sarifBytes, '\n'), 0o644)

	// Informational watchlist ∩ SBOM join
	if joinPath, err := exportx.WriteWatchlistJoin(root, ""); err == nil {
		_ = copyFile(joinPath, filepath.Join(out, "07-watchlist-sbom-join.json"))
	}
	// Buyer one-pager HTML — skip rewrite when gate snapshot fingerprint unchanged.
	htmlDoc := buyerOnePager(root, res)
	onepagerPath := filepath.Join(out, "buyer-onepager.html")
	wrote, err := writeOnePagerIfChanged(onepagerPath, htmlDoc)
	if err != nil {
		return err
	}
	if wrote {
		tty.PrintStatus("Buyer one-pager", true, onepagerPath)
	} else {
		tty.PrintStatus("Buyer one-pager", true, onepagerPath+" (unchanged)")
	}

	// Copy / refresh proof page into review-pack and repo proof/
	proof := ProofPageHTML()
	_ = os.MkdirAll(filepath.Join(root, "proof"), 0o755)
	_ = os.WriteFile(filepath.Join(root, "proof", "index.html"), []byte(proof), 0o644)
	_ = os.WriteFile(filepath.Join(out, "proof-index.html"), []byte(proof), 0o644)

	tty.PrintStatus("Review pack", true, out)
	if !res.Passed {
		fmt.Printf("%s\n", tty.C(tty.Yellow, "[!] Gates still failing — pack is for remediation review, not release sign-off."))
	}
	if tty.IsTerminal {
		tty.RenderThermometer(res.Score)
	}
	if !res.Passed && !opts.AllowFailingGates {
		return fmt.Errorf("gates failing — pass --allow-failing-gates to accept a remediation review pack")
	}
	return nil
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
	status := "Needs remediation"
	statusClass := "warn"
	if res.Passed {
		status = "Gates passed — pending human review & attest"
		statusClass = "ok"
	}
	info := loadAttestInfo(root)
	if info.UnsignedLoud {
		status = "UNSIGNED — not cryptographically verified · " + status
		statusClass = "unsigned"
	}
	var rows strings.Builder
	var fpSeed strings.Builder
	fmt.Fprintf(&fpSeed, "%d|%s|%s|%s|%s|%s", res.Score, res.Payload.PackID, status, info.Line, info.Commit, info.StateHash)
	for _, f := range res.Payload.Failures {
		fmt.Fprintf(&rows, "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n",
			html.EscapeString(f.GateID), html.EscapeString(f.Severity), html.EscapeString(f.SanitizedDescription))
		fmt.Fprintf(&fpSeed, "|%s:%s", f.GateID, f.Severity)
	}
	if len(res.Payload.Failures) == 0 {
		rows.WriteString(`<tr><td colspan="3">No open gate findings.</td></tr>`)
	}
	fpSum := sha256.Sum256([]byte(fpSeed.String()))
	fp := fmt.Sprintf("%x", fpSum[:16])
	lede := "Structural evidence for human review — not conformity assessment. Hand this one-pager (and the review pack) to a buyer or auditor. Evidence is prepared locally — this page is not a certificate of conformity."
	if info.UnsignedLoud {
		lede = "UNSIGNED — not cryptographically verified. " + lede
	}
	return fmt.Sprintf(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Curbpack — Buyer One-Pager</title>
  <!-- curbpack-onepager-fp:%s -->
  <style>
    :root { --ink:#0a0a0b; --muted:#4a4a52; --line:#e4e6eb; --ok:#15803d; --warn:#92400e; --paper:#fcfcfc; --unsigned:#b91c1c; }
    body { margin:0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; color:var(--ink); background:var(--paper); min-height:100vh; }
    main { max-width: 720px; margin: 0 auto; padding: 2.5rem 1.25rem 3rem; }
    .brand { letter-spacing:0.06em; font-weight:700; font-size:0.8rem; text-transform:uppercase; font-family:ui-monospace,Menlo,monospace; color:#005073; }
    h1 { font-family: Fraunces, Georgia, serif; font-size:2rem; line-height:1.2; margin:0.4rem 0 0.5rem; font-weight:600; }
    h2 { font-family: Fraunces, Georgia, serif; font-size:1.2rem; margin:2rem 0 0.75rem; font-weight:600; border-top:1px solid var(--ink); padding-top:1.25rem; }
    .lede { color:var(--muted); font-size:1.05rem; margin-bottom:1.5rem; }
    .status { display:inline-block; padding:0.4rem 0.75rem; font-size:0.85rem; font-weight:600; font-family:ui-monospace,Menlo,monospace; }
    .status.ok { background:#f0fdf4; color:var(--ok); border:1px solid var(--ok); }
    .status.warn { background:#fff4e5; color:var(--warn); border:1px solid #f0d2a8; }
    .status.unsigned { background:#fef2f2; color:var(--unsigned); border:1px solid var(--unsigned); letter-spacing:0.02em; text-transform:uppercase; }
    .meter { margin:1.25rem 0; font-family:ui-monospace,Menlo,monospace; font-size:0.9rem; }
    .bar { height:10px; background:var(--line); overflow:hidden; margin-top:0.35rem; border:1px solid var(--ink); }
    .bar > span { display:block; height:100%%; background:var(--ink); width:%d%%; }
    table { width:100%%; border-collapse:collapse; margin-top:1.25rem; font-size:0.9rem; }
    th, td { text-align:left; padding:0.55rem 0.4rem; border-bottom:1px solid var(--line); vertical-align:top; }
    th { color:var(--muted); font-weight:600; }
    .back { margin-top:0.5rem; padding:1.1rem 1.15rem; border:1px solid var(--ink); background:#f2f3f5; }
    .back p { margin:0 0 0.75rem; font-size:0.9rem; color:var(--muted); }
    dl.prov { display:grid; grid-template-columns:9.5rem 1fr; gap:0.45rem 1rem; margin:0; font-size:0.88rem; }
    dl.prov dt { color:var(--muted); font-family:ui-monospace,Menlo,monospace; font-size:0.78rem; }
    dl.prov dd { margin:0; word-break:break-all; font-family:ui-monospace,Menlo,monospace; font-size:0.82rem; }
    footer { margin-top:2rem; font-size:0.85rem; color:var(--muted); }
    footer .unsigned-foot { color:var(--unsigned); font-weight:700; font-size:1rem; display:block; margin-bottom:0.5rem; }
  </style>
</head>
<body>
  <main>
    <div class="brand">Curbpack · Front</div>
    <h1>%s</h1>
    <p class="lede">%s</p>
    <div class="status %s">%s</div>
    <div class="status %s" style="margin-left:0.5rem">%s</div>
    <div class="meter">Local gate score on this tree: <strong>%d%%</strong> — not certification
      <div class="bar"><span></span></div>
    </div>
    <table>
      <thead><tr><th>Gate</th><th>Severity</th><th>Finding</th></tr></thead>
      <tbody>
%s
      </tbody>
    </table>

    <h2 id="provenance">Back — provenance &amp; human sign-off</h2>
    <div class="back">
      <p>Chosen rule packs are structural checklists (house policy or regulation-shaped drafts). Gate green is not legal conformity. Human sign-off is <code>curbpack attest</code> — ssh-agent signed means a human bound this tree; unsigned ≠ verified.</p>
      %s
      %s
    </div>

    <footer>
      %s
      Structural evidence for human review — not conformity assessment. Generated %s · Open <code>proof/index.html</code> to verify the HPURL fragment against <code>.github/curbpack/evidence/hpurl-pointer.json</code>.
    </footer>
  </main>
</body>
</html>
`, fp, res.Score, html.EscapeString(name), html.EscapeString(lede),
		statusClass, html.EscapeString(status),
		info.Class, html.EscapeString(info.Line),
		res.Score, rows.String(),
		provenanceDL(res.Payload.PackID, info),
		sourcesStrip(root, res.Payload.PackID),
		footerHTML(info.Line, info.UnsignedLoud),
		html.EscapeString(res.Payload.Timestamp))
}

func footerHTML(line string, unsignedLoud bool) string {
	if unsignedLoud {
		return `<span class="unsigned-foot">` + html.EscapeString(line) + `</span>`
	}
	return html.EscapeString(line) + " · "
}

func provenanceDL(packID string, info attestInfo) string {
	commit := info.Commit
	if commit == "" || commit == "unknown" {
		commit = "(no commit)"
	}
	state := info.StateHash
	if state == "" {
		state = "(none — run curbpack attest after human review)"
	}
	signer := info.Signer
	if signer == "" {
		signer = "local-unsigned"
	}
	touch := info.UserTouch
	if touch == "" {
		touch = "not-verified"
	}
	signOff := "Pending human review. A reviewer runs curbpack attest; ssh-agent-signed = human-bound on this commit."
	if !info.UnsignedLoud {
		signOff = "Human-bound on this commit (ssh-agent-signed). Still not conformity assessment."
	}
	var b strings.Builder
	b.WriteString(`<dl class="prov">`)
	fmt.Fprintf(&b, "<dt>Rule packs</dt><dd>%s</dd>\n", html.EscapeString(packID))
	fmt.Fprintf(&b, "<dt>Commit</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(commit)))
	fmt.Fprintf(&b, "<dt>Attest</dt><dd>%s</dd>\n", html.EscapeString(info.Line))
	fmt.Fprintf(&b, "<dt>Signer</dt><dd>%s</dd>\n", html.EscapeString(signer))
	fmt.Fprintf(&b, "<dt>User touch</dt><dd>%s</dd>\n", html.EscapeString(touch))
	fmt.Fprintf(&b, "<dt>state_hash</dt><dd>%s</dd>\n", html.EscapeString(state))
	if info.SBOMDigest != "" {
		fmt.Fprintf(&b, "<dt>sbom_digest</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(info.SBOMDigest)))
	}
	if info.VEXDigest != "" {
		fmt.Fprintf(&b, "<dt>vex_digest</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(info.VEXDigest)))
	}
	fmt.Fprintf(&b, "<dt>Human sign-off</dt><dd>%s</dd>\n", html.EscapeString(signOff))
	b.WriteString(`<dt>Verify</dt><dd>proof/index.html + hpurl-pointer.json (client-side hash compare)</dd>`)
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

// loadAttestInfo best-effort reads HEAD notes; default UNSIGNED loudness.
func loadAttestInfo(root string) attestInfo {
	info := attestInfo{
		Line:         "UNSIGNED — not cryptographically verified",
		Class:        "unsigned",
		UnsignedLoud: true,
		Signer:       "local-unsigned",
		UserTouch:    "not-verified",
	}
	commit, err := gitutil.HeadSHA(root)
	if err == nil && commit != "" && commit != "unknown" {
		info.Commit = commit
	}
	if info.Commit == "" {
		return info
	}
	body, err := gitutil.NotesShow(root, info.Commit)
	if err != nil || strings.TrimSpace(body) == "" {
		return info
	}
	var cap attest.Capsule
	if json.Unmarshal([]byte(body), &cap) != nil {
		return info
	}
	info.StateHash = cap.StateHash
	info.Signer = cap.Signer
	info.UserTouch = cap.UserTouch
	if cap.Evidence != nil {
		info.SBOMDigest = cap.Evidence["sbom_digest"]
		info.VEXDigest = cap.Evidence["vex_digest"]
	}
	if cap.UserTouch == "ssh-agent-signed" && cap.SSHSignature != "" && !strings.HasPrefix(cap.SSHSignature, "agent-bind:") {
		info.Line = "ssh-agent-signed"
		info.Class = "ok"
		info.UnsignedLoud = false
	}
	return info
}

// ProofPageHTML returns static HPURL viewer with client-side hash verification.
func ProofPageHTML() string {
	return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Curbpack — Proof</title>
  <style>
    :root { color-scheme: light dark; font-family: "IBM Plex Sans", system-ui, sans-serif; line-height: 1.5; }
    body { margin:0; min-height:100vh; display:grid; place-items:center;
      background: linear-gradient(160deg,#0f1117,#1a2233); color:#e8eaed; }
    main { width:min(640px,92vw); padding:2rem; border:1px solid #2a3142; border-radius:12px; background:#161a24; }
    h1 { margin:0 0 0.25rem; font-size:1.35rem; }
    .subtitle { color:#9aa3b2; margin-bottom:1.5rem; }
    .status { padding:0.75rem 1rem; border-radius:8px; margin-bottom:1.25rem; font-weight:600; }
    .status.ok { background:#12351f; color:#6ee7a0; border:1px solid #1f6f43; }
    .status.warn { background:#3a2a12; color:#fbbf24; border:1px solid #92400e; }
    .status.err { background:#3b1212; color:#fca5a5; border:1px solid #991b1b; }
    dl { display:grid; grid-template-columns:8.5rem 1fr; gap:0.5rem 1rem; margin:0; }
    dt { color:#9aa3b2; }
    dd { margin:0; word-break:break-all; font-family:ui-monospace,Menlo,monospace; font-size:0.85rem; }
    footer { margin-top:1.5rem; color:#9aa3b2; font-size:0.85rem; }
    code { font-size:0.8rem; }
    input { width:100%; box-sizing:border-box; margin:0.35rem 0 0.75rem; padding:0.5rem 0.65rem;
      border-radius:6px; border:1px solid #2a3142; background:#0f1117; color:#e8eaed; font-family:ui-monospace,Menlo,monospace; }
    button { padding:0.45rem 0.85rem; border-radius:6px; border:1px solid #3a4660; background:#243049; color:#e8eaed; cursor:pointer; }
  </style>
</head>
<body>
  <main>
    <h1>Evidence proof</h1>
    <p class="subtitle">HPURL fragment stays in the browser hash. Verify <code>h=</code> against the local evidence pointer digest (client-side only).</p>
    <div id="status" class="status warn">Waiting for fragment parameters…</div>
    <dl id="fields"></dl>
    <label for="expected">Expected state_hash (from <code>.github/curbpack/evidence/hpurl-pointer.json</code>)</label>
    <input id="expected" placeholder="Paste state_hash to verify…" autocomplete="off" />
    <button type="button" id="verifyBtn">Verify hash</button>
    <footer>
      Contract: <code>#?h=&lt;hash&gt;&amp;p=&lt;pointer&gt;&amp;s=&lt;signature&gt;</code><br/>
      Aliases: <code>run</code>, <code>capsule</code>, <code>vows</code>. Local pointer: <code>.github/curbpack/evidence/</code>. Not a certification.
    </footer>
  </main>
  <script>
    function parseHashParams() {
      const hash = location.hash || "";
      let q = "";
      if (hash.startsWith("#?")) q = hash.slice(2);
      else if (hash.startsWith("#")) q = hash.slice(1);
      if (!q) return null;
      if (q.startsWith("?")) q = q.slice(1);
      const params = new URLSearchParams(q);
      const h = params.get("h") || params.get("capsule") || params.get("bundle");
      const p = params.get("p") || params.get("run") || params.get("ref") || params.get("pointer");
      const s = params.get("s") || params.get("vows") || params.get("$");
      if (!h && !p && !s) return null;
      return { h, p, s, space: params.get("space") || undefined, repo: params.get("repo") || undefined };
    }
    function setStatus(kind, message) {
      const el = document.getElementById("status");
      el.className = "status " + kind;
      el.textContent = message;
    }
    function renderFields(data) {
      const dl = document.getElementById("fields");
      dl.innerHTML = "";
      for (const [label, value] of [["Hash (h)", data.h], ["Pointer (p)", data.p], ["Signature (s)", data.s], ["Space", data.space], ["Repo", data.repo]]) {
        if (!value) continue;
        const dt = document.createElement("dt"); dt.textContent = label;
        const dd = document.createElement("dd"); dd.textContent = value;
        dl.appendChild(dt); dl.appendChild(dd);
      }
    }
    function normalizeHex(v) { return (v || "").trim().toLowerCase(); }
    function verify() {
      const data = parseHashParams();
      const expected = normalizeHex(document.getElementById("expected").value);
      if (!data || !data.h) { setStatus("warn", "No h= hash in fragment"); return; }
      if (!expected) { setStatus("warn", "Paste expected state_hash from hpurl-pointer.json"); return; }
      if (normalizeHex(data.h) === expected) {
        setStatus("ok", "Hash match — fragment h= equals local evidence pointer (client-side verify)");
      } else {
        setStatus("err", "Hash mismatch — fragment does not match pasted state_hash");
      }
    }
    const data = parseHashParams();
    if (!data) {
      setStatus("warn", "No receipt in link — append #?h=…&p=…&s=…");
    } else {
      renderFields(data);
      setStatus("ok", "Params loaded — paste state_hash and Verify");
      if (data.h) document.getElementById("expected").placeholder = "Expected: " + data.h.slice(0, 16) + "…";
    }
    document.getElementById("verifyBtn").addEventListener("click", verify);
    // Best-effort: fetch local pointer when served from same origin (file:// may block)
    fetch("../.github/curbpack/evidence/hpurl-pointer.json").then(r => r.ok ? r.json() : null).then(j => {
      if (j && j.state_hash) {
        document.getElementById("expected").value = j.state_hash;
        verify();
      }
    }).catch(() => {});
  </script>
</body>
</html>
`
}

// Unused import guard for ir in case of refactors
var _ = ir.Failure{}
