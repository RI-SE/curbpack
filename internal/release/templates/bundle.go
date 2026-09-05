package templates

import (
	"fmt"
	"html"
	"strings"
)

// BundleDTO is the input for offline evidence-bundle.html.
type BundleDTO struct {
	RepoName       string
	Score          int
	Passed         bool
	Timestamp      string
	OnePagerBody   string // inner HTML from buyer one-pager main (optional embed)
	HPURLFragment  string
	HPURLEmbedJSON string // raw JSON for offline verify
	Remediation    bool   // show REMEDIATION banner when gates red
}

// EvidenceBundleHTML renders review-pack/evidence-bundle.html for offline handoff.
func EvidenceBundleHTML(d BundleDTO) string {
	banner := ""
	if d.Remediation {
		banner = `<div class="remediation" role="note">REMEDIATION — gates failing on this tree. Fix findings and re-run curbpack check before buyer handoff. Not a conformity assessment.</div>`
	}
	status := "Gates passed — pending human review"
	if !d.Passed {
		status = "Needs remediation — human review required"
	}
	hpurlBlock := ""
	if d.HPURLFragment != "" {
		hpurlBlock = fmt.Sprintf(`<section><h2>Evidence stamp (offline)</h2><code>%s</code></section>`, html.EscapeString(d.HPURLFragment))
	}
	if d.HPURLEmbedJSON != "" {
		// FG-02 / MUST-43: never embed repository-derived JSON raw inside <script>.
		// Unicode escapes keep JSON valid while preventing </script> breakout.
		hpurlBlock += fmt.Sprintf(`<script type="application/json" id="curbpack-hpurl-pointer">%s</script>`, escapeJSONForHTMLScript(d.HPURLEmbedJSON))
	}
	onePager := d.OnePagerBody
	if onePager == "" {
		onePager = `<p>No buyer one-pager embedded — run curbpack share first.</p>`
	}
	return fmt.Sprintf(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Curbpack — Evidence Bundle</title>
  <!-- curbpack-bundle-schema:1 -->
  <style>
    :root { --ink:#0a0a0b; --muted:#4a4a52; --warn:#92400e; --rem:#b91c1c; --paper:#fcfcfc; }
    body { margin:0; font-family: "IBM Plex Sans", sans-serif; color:var(--ink); background:var(--paper); }
    main { max-width: 820px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }
    .remediation { background:#fef2f2; color:var(--rem); border:2px solid var(--rem); padding:1rem; margin-bottom:1.5rem; font-weight:600; }
    .meta { color:var(--muted); font-size:0.9rem; margin-bottom:1.5rem; }
    h1 { font-size:1.75rem; margin:0 0 0.5rem; }
    h2 { font-size:1.1rem; margin:1.5rem 0 0.5rem; border-top:1px solid var(--ink); padding-top:1rem; }
    .embed { border:1px solid #ccc; padding:1rem; margin-top:1rem; }
    footer { margin-top:2rem; font-size:0.85rem; color:var(--muted); }
  </style>
</head>
<body>
  <main>
    %s
    <h1>Evidence bundle — %s</h1>
    <p class="meta">%s · score %d%% · Generated %s · Structural evidence for human review — not conformity assessment.</p>
    <p class="meta">Keep this folder with the release tag for 10 years or the support period, whichever is longer. Curbpack does not archive it. This is a reminder, not a legal fulfillment claim.</p>
    <section class="embed">
      <h2>Buyer one-pager</h2>
      %s
    </section>
    %s
    <footer>Open proof/index.html locally to compare the stamp to the embedded pointer. Unsigned ≠ verified.</footer>
  </main>
</body>
</html>
`, banner, html.EscapeString(d.RepoName), html.EscapeString(status), d.Score, html.EscapeString(d.Timestamp), onePager, hpurlBlock)
}

// escapeJSONForHTMLScript makes JSON safe as text inside an HTML <script> element.
// HTML5 script data ends at a literal "</script>" (case-insensitive); escaping
// "<", ">", and "&" to JSON Unicode escapes prevents breakout while remaining
// valid JSON for offline consumers (INV-05, INV-06).
func escapeJSONForHTMLScript(s string) string {
	s = strings.ReplaceAll(s, `&`, `\u0026`)
	s = strings.ReplaceAll(s, `<`, `\u003c`)
	s = strings.ReplaceAll(s, `>`, `\u003e`)
	return s
}

// ExtractOnePagerMain returns inner main content from full one-pager HTML for bundle embed.
func ExtractOnePagerMain(htmlDoc string) string {
	const open = "<main>"
	const close = "</main>"
	i := strings.Index(htmlDoc, open)
	j := strings.Index(htmlDoc, close)
	if i < 0 || j < 0 || j <= i {
		return htmlDoc
	}
	return htmlDoc[i+len(open) : j]
}
