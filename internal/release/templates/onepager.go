package templates

import (
	"crypto/sha256"
	"fmt"
	"html"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
)

// onePagerCoverMax is the front-of-page file checklist cap (cognitive load).
const onePagerCoverMax = 12

// OnePagerDTO is the stable input for buyer one-pager HTML generation.
type OnePagerDTO struct {
	RepoName          string
	Score             int
	Passed            bool
	PackID            string
	PackLabels        string // plain-words pack names for the cover; not in fingerprint
	Timestamp         string
	Failures          []OnePagerFailure
	CoverRows         []OnePagerCoverRow // path + human question; not in fingerprint
	Bind              attest.BindInfo
	AttestLine        string
	AttestClass       string
	UnsignedLoud      bool
	AssuranceClass    string
	MechanicalSummary string // e.g. "5 of 7 gates mechanically evidenced"
	ProvenanceHTML    string
	SourcesHTML       string
	FooterPrefix      string
	// Provenance digests (hex); empty when absent. Digests flip the fingerprint so
	// prepare rewrites when digests appear, but never upgrade UNSIGNED trust class.
	ResultDigest string
	SBOMDigest   string
	VEXDigest    string
}

// OnePagerFailure is one gate row for the one-pager table.
type OnePagerFailure struct {
	GateID      string
	Severity    string
	Description string
}

// OnePagerCoverRow is one front-of-page file-to-open row (path + human question).
type OnePagerCoverRow struct {
	Path     string
	Question string
}

// OnePagerFingerprint computes the stable fingerprint marker for a DTO.
func OnePagerFingerprint(d OnePagerDTO) string {
	status := "Needs remediation"
	if d.Passed {
		status = "Gates passed — pending human review & attest"
	}
	if d.UnsignedLoud {
		status = "UNSIGNED — not cryptographically verified · " + status
	}
	var fpSeed strings.Builder
	fmt.Fprintf(&fpSeed, "%d|%s|%s|%s|%s|%s", d.Score, d.PackID, status, d.AttestLine, d.Bind.CommitSHA, d.Bind.StateHash)
	for _, f := range d.Failures {
		fmt.Fprintf(&fpSeed, "|%s:%s", f.GateID, f.Severity)
	}
	fmt.Fprintf(&fpSeed, "|%s|%s|%s", d.ResultDigest, d.SBOMDigest, d.VEXDigest)
	sum := sha256.Sum256([]byte(fpSeed.String()))
	return fmt.Sprintf("%x", sum[:16])
}

// BuyerOnePagerHTML renders the buyer one-pager from a DTO.
func BuyerOnePagerHTML(d OnePagerDTO) string {
	fp := OnePagerFingerprint(d)
	status := "Needs remediation"
	statusClass := "warn"
	if d.Passed {
		status = "Gates passed — pending human review & attest"
		statusClass = "ok"
	}
	if d.UnsignedLoud {
		status = "UNSIGNED — not cryptographically verified · " + status
		statusClass = "unsigned"
	}
	var rows strings.Builder
	for _, f := range d.Failures {
		fmt.Fprintf(&rows, "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n",
			html.EscapeString(f.GateID), html.EscapeString(f.Severity), html.EscapeString(f.Description))
	}
	if len(d.Failures) == 0 {
		rows.WriteString(`<tr><td colspan="3">No open gate findings.</td></tr>`)
	}
	var cover strings.Builder
	n := len(d.CoverRows)
	if n > onePagerCoverMax {
		n = onePagerCoverMax
	}
	for _, r := range d.CoverRows[:n] {
		fmt.Fprintf(&cover, "<tr><td>%s</td><td>%s</td></tr>\n",
			html.EscapeString(r.Path), html.EscapeString(r.Question))
	}
	if n == 0 {
		cover.WriteString(`<tr><td colspan="2">No file checklist rows.</td></tr>`)
	}
	labels := strings.TrimSpace(d.PackLabels)
	if labels == "" {
		labels = d.PackID
	}
	assuranceLine := ""
	if ac := strings.TrimSpace(d.AssuranceClass); ac != "" {
		assuranceLine = fmt.Sprintf(`<p class="assurance"><strong>Assurance class:</strong> %s`, html.EscapeString(ac))
		if ms := strings.TrimSpace(d.MechanicalSummary); ms != "" {
			assuranceLine += fmt.Sprintf(` · <strong>%s</strong>`, html.EscapeString(ms))
		}
		assuranceLine += "</p>\n    "
	}
	lede := "Structural evidence for human review — not conformity assessment. Hand this one-pager (and the review pack) to a buyer or auditor. Evidence is prepared locally — this page is not a certificate of conformity."
	if d.UnsignedLoud {
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
    .packs { font-size:1rem; margin:0 0 0.85rem; }
    .assurance { font-size:0.95rem; margin:0 0 0.85rem; color:var(--muted); }
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
    <p class="packs"><strong>Packs:</strong> %s</p>
    %s<div class="status %s">%s</div>
    <div class="status %s" style="margin-left:0.5rem">%s</div>
    <h2>Files to open</h2>
    <table>
      <thead><tr><th>Path</th><th>Question</th></tr></thead>
      <tbody>
%s
      </tbody>
    </table>
    <table>
      <thead><tr><th>Gate</th><th>Severity</th><th>Finding</th></tr></thead>
      <tbody>
%s
      </tbody>
    </table>

    <h2 id="provenance">Back — provenance &amp; human sign-off</h2>
    <div class="back">
      <div class="meter">Local gate score on this tree: <strong>%d%%</strong> — not certification
        <div class="bar"><span></span></div>
      </div>
      <p>Chosen rule packs are structural checklists (house policy or regulation-shaped drafts). Gate green is not legal conformity. Human sign-off is <code>curbpack attest</code> — ssh-agent signed means a human bound this tree; unsigned ≠ verified.</p>
      %s
      %s
    </div>

    <footer>
      %s
      Structural evidence for human review — not conformity assessment. Generated %s · Open <code>proof/index.html</code> to compare the stamp to the local evidence pointer.
    </footer>
  </main>
</body>
</html>
`, fp, d.Score, html.EscapeString(d.RepoName), html.EscapeString(lede),
		html.EscapeString(labels),
		assuranceLine,
		statusClass, html.EscapeString(status),
		d.AttestClass, html.EscapeString(d.AttestLine),
		cover.String(), rows.String(),
		d.Score,
		d.ProvenanceHTML, d.SourcesHTML,
		d.FooterPrefix, html.EscapeString(d.Timestamp))
}
