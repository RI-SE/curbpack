package release

import (
	"encoding/json"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/sbom"
	"github.com/afelin/cyberready/internal/tty"
	"github.com/afelin/cyberready/internal/validate"
)

// Options for prepare-release.
type Options struct {
	RepoRoot string
	PackIDs  []string
	OutDir   string
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

	// SBOM summary (best-effort from lockfile)
	sbomSummary, sbomErr := sbom.FromLockfiles(root)
	sbomPath := filepath.Join(out, "04-sbom-summary.json")
	if sbomErr != nil {
		_ = os.WriteFile(sbomPath, []byte(`{"status":"unavailable","detail":`+jsonString(sbomErr.Error())+"}\n"), 0o644)
	} else {
		b, _ := json.MarshalIndent(sbomSummary, "", "  ")
		_ = os.WriteFile(sbomPath, append(b, '\n'), 0o644)
	}

	// VEX draft (pending attest)
	vex := map[string]any{
		"status":           "draft_pending_attest",
		"schema":           "openvex-stub",
		"generated_at":     time.Now().UTC().Format(time.RFC3339),
		"note":             "VEX statements remain draft until cyberready attest binds them to a commit via Git Notes.",
		"product":          filepath.Base(root),
		"vulnerability_ids": []string{},
	}
	vb, _ := json.MarshalIndent(vex, "", "  ")
	_ = os.WriteFile(filepath.Join(out, "05-vex-draft.json"), append(vb, '\n'), 0o644)

	// Buyer one-pager HTML
	htmlDoc := buyerOnePager(root, res)
	if err := os.WriteFile(filepath.Join(out, "buyer-onepager.html"), []byte(htmlDoc), 0o644); err != nil {
		return err
	}

	// Copy / refresh proof page into review-pack and repo proof/
	proof := ProofPageHTML()
	_ = os.MkdirAll(filepath.Join(root, "proof"), 0o755)
	_ = os.WriteFile(filepath.Join(root, "proof", "index.html"), []byte(proof), 0o644)
	_ = os.WriteFile(filepath.Join(out, "proof-index.html"), []byte(proof), 0o644)

	tty.PrintStatus("Review pack", true, out)
	tty.PrintStatus("Buyer one-pager", true, filepath.Join(out, "buyer-onepager.html"))
	if !res.Passed {
		fmt.Printf("%s\n", tty.C(tty.Yellow, "[!] Gates still failing — pack is for remediation review, not release sign-off."))
	}
	if tty.IsTerminal {
		tty.RenderThermometer(res.Score)
	}
	return nil
}

func jsonString(s string) string {
	b, _ := json.Marshal(s)
	return string(b)
}

func ensureWitnessTemplates(root string) error {
	files := map[string]string{
		"docs/annex-vii/risk_assessment.md": `# Risk Assessment

## Product Overview

Describe the product, intended use, and operating environment.

## Identified Risks

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R-001   |             |          |            |

## Residual Risk Statement

State residual risk after mitigations.
`,
		"docs/annex-vii/support_period.md": `# Support Period

## End of Support

Declare the date or duration of security update support.

## Rationale

Explain how the support period was chosen.
`,
		"docs/annex-vii/user_manual_security.md": `# User Manual — Security

## Secure Configuration

Document default-secure settings and hardening steps.

## Product Disposal

Explain secure decommissioning and data wiping.
`,
		"docs/medtech/software_safety_class.md": `# Software Safety Class

## Classification Rationale

State IEC 62304 Class A/B/C and why.
`,
		"docs/medtech/soup_list.md": `# SOUP List

## Items

| Component | Version | Manufacturer | Residual Risk |
|-----------|---------|--------------|---------------|
|           |         |              |               |
`,
		"docs/medtech/problem_resolution.md": `# Problem Resolution

## Process

Describe intake, triage, fix, verification, and release of corrections.
`,
	}
	for rel, content := range files {
		path := filepath.Join(root, rel)
		if _, err := os.Stat(path); err == nil {
			continue
		}
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
			return err
		}
	}
	return nil
}

func executiveSummary(res validate.Result) string {
	var b strings.Builder
	b.WriteString("# Executive Summary — Supplier Readiness\n\n")
	b.WriteString("> CyberReady prepares evidence for **human review**. It does not certify conformity.\n\n")
	fmt.Fprintf(&b, "- **Generated:** %s\n", res.Payload.Timestamp)
	fmt.Fprintf(&b, "- **Packs:** %s\n", res.Payload.PackID)
	fmt.Fprintf(&b, "- **Readiness score:** %d%%\n", res.Score)
	fmt.Fprintf(&b, "- **Open findings:** %d\n\n", len(res.Payload.Failures))
	if res.Passed {
		b.WriteString("All deterministic gates passed. Proceed to human review of Annex VII / medtech drafts, then `cyberready attest`.\n")
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
	var rows strings.Builder
	for _, f := range res.Payload.Failures {
		fmt.Fprintf(&rows, "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n",
			html.EscapeString(f.GateID), html.EscapeString(f.Severity), html.EscapeString(f.SanitizedDescription))
	}
	if len(res.Payload.Failures) == 0 {
		rows.WriteString(`<tr><td colspan="3">No open gate findings.</td></tr>`)
	}
	return fmt.Sprintf(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CyberReady — Buyer One-Pager</title>
  <style>
    :root { --ink:#1a1f2e; --muted:#5c6578; --line:#d8dde8; --ok:#1f6f43; --warn:#92400e; }
    body { margin:0; font-family: "Source Serif 4", "Iowan Old Style", Georgia, serif; color:var(--ink);
      background: linear-gradient(165deg, #eef2f7 0%%, #f7f3ec 45%%, #e8eef5 100%%); min-height:100vh; }
    main { max-width: 720px; margin: 0 auto; padding: 2.5rem 1.25rem 3rem; }
    .brand { font-family: "IBM Plex Sans", "Segoe UI", sans-serif; letter-spacing:0.04em;
      font-weight:700; font-size:0.85rem; text-transform:uppercase; color:#2a5080; }
    h1 { font-size:2rem; line-height:1.2; margin:0.4rem 0 0.5rem; font-weight:600; }
    .lede { color:var(--muted); font-size:1.05rem; margin-bottom:1.5rem; }
    .status { display:inline-block; padding:0.4rem 0.75rem; border-radius:4px; font-family:"IBM Plex Sans",sans-serif; font-size:0.9rem; font-weight:600; }
    .status.ok { background:#e6f6ec; color:var(--ok); border:1px solid #b7e0c5; }
    .status.warn { background:#fff4e5; color:var(--warn); border:1px solid #f0d2a8; }
    .meter { margin:1.25rem 0; font-family:"IBM Plex Sans",sans-serif; }
    .bar { height:12px; background:#dde3ee; border-radius:2px; overflow:hidden; margin-top:0.35rem; }
    .bar > span { display:block; height:100%%; background:#2a5080; width:%d%%; }
    table { width:100%%; border-collapse:collapse; margin-top:1.25rem; font-family:"IBM Plex Sans",sans-serif; font-size:0.9rem; }
    th, td { text-align:left; padding:0.55rem 0.4rem; border-bottom:1px solid var(--line); vertical-align:top; }
    th { color:var(--muted); font-weight:600; }
    footer { margin-top:2rem; font-size:0.85rem; color:var(--muted); font-family:"IBM Plex Sans",sans-serif; }
  </style>
</head>
<body>
  <main>
    <div class="brand">CyberReady+</div>
    <h1>%s</h1>
    <p class="lede">Supplier readiness snapshot for procurement review. Evidence is prepared locally — this page is not a certificate of conformity.</p>
    <div class="status %s">%s</div>
    <div class="meter">Readiness score: <strong>%d%%</strong>
      <div class="bar"><span></span></div>
    </div>
    <table>
      <thead><tr><th>Gate</th><th>Severity</th><th>Finding</th></tr></thead>
      <tbody>
%s
      </tbody>
    </table>
    <footer>
      Generated %s · Packs: %s · Open <code>proof/index.html</code> for HPURL fragment inspection.
    </footer>
  </main>
</body>
</html>
`, res.Score, html.EscapeString(name), statusClass, html.EscapeString(status), res.Score, rows.String(),
		html.EscapeString(res.Payload.Timestamp), html.EscapeString(res.Payload.PackID))
}

// ProofPageHTML returns static HPURL viewer (h/p/s fragment contract + Coreward aliases).
func ProofPageHTML() string {
	return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CyberReady — Proof</title>
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
    dl { display:grid; grid-template-columns:7rem 1fr; gap:0.5rem 1rem; margin:0; }
    dt { color:#9aa3b2; }
    dd { margin:0; word-break:break-all; font-family:ui-monospace,Menlo,monospace; font-size:0.85rem; }
    footer { margin-top:1.5rem; color:#9aa3b2; font-size:0.85rem; }
    code { font-size:0.8rem; }
  </style>
</head>
<body>
  <main>
    <h1>Evidence proof</h1>
    <p class="subtitle">HPURL fragment params stay in the browser hash — they are not sent as a page request path.</p>
    <div id="status" class="status warn">Waiting for fragment parameters…</div>
    <dl id="fields"></dl>
    <footer>
      CyberReady contract: <code>#?h=&lt;hash&gt;&amp;p=&lt;pointer&gt;&amp;s=&lt;signature&gt;</code><br/>
      Coreward-compatible aliases also accepted: <code>run</code>, <code>capsule</code>, <code>vows</code> (and optional <code>space</code>).
      Not a certification.
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
      return {
        h, p, s,
        space: params.get("space") || undefined,
        repo: params.get("repo") || undefined,
        pub: params.get("@") || undefined,
      };
    }
    function setStatus(kind, message) {
      const el = document.getElementById("status");
      el.className = "status " + kind;
      el.textContent = message;
    }
    function renderFields(data) {
      const dl = document.getElementById("fields");
      dl.innerHTML = "";
      const rows = [
        ["Hash (h)", data.h],
        ["Pointer (p)", data.p],
        ["Signature (s)", data.s],
        ["Space", data.space],
        ["Repo", data.repo],
        ["Public key", data.pub ? "(present)" : undefined],
      ];
      for (const [label, value] of rows) {
        if (!value) continue;
        const dt = document.createElement("dt"); dt.textContent = label;
        const dd = document.createElement("dd"); dd.textContent = value;
        dl.appendChild(dt); dl.appendChild(dd);
      }
    }
    const data = parseHashParams();
    if (!data) {
      setStatus("warn", "No receipt in link — append #?h=…&p=…&s=…");
    } else {
      renderFields(data);
      setStatus("ok", "Params loaded (client-side only)");
    }
  </script>
</body>
</html>
`
}

// Unused import guard for ir in case of refactors
var _ = ir.Failure{}
