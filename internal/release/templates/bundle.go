package templates

import (
	"fmt"
	"html"
	"strings"
)

// BundleDTO is the input for offline evidence-bundle.html.
type BundleDTO struct {
	RepoName       string
	Score          int // historical
	FailedRules    int
	EvaluatedRules int
	SkippedRules   int
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
	return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Curbpack — Evidence bundle</title><!-- curbpack-bundle-schema:1 --><style>` + reportCSS + `</style></head><body><main>` + banner + onePager + hpurlBlock + `<details><summary>Keeping the evidence</summary><p>Keep this folder with the release tag for 10 years or the support period, whichever is longer where that retention policy applies. Confirm your own retention requirements. Curbpack does not archive it. This is a reminder, not a legal fulfillment claim.</p></details></main></body></html>`
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
