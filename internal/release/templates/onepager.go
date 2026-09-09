package templates

import (
	"crypto/sha256"
	"fmt"
	"html"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
)

// OnePagerDTO is the stable input for buyer one-pager HTML generation.
type OnePagerDTO struct {
	RepoName          string
	Score             int // historical fingerprint input; public HTML uses counts
	FailedRules       int
	EvaluatedRules    int
	SkippedRules      int
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
	Result   string
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

// reportCSS is shared by standalone and embedded reports. No network resources.
const reportCSS = `
:root{color-scheme:light;--ink:#182b38;--muted:#48606d;--line:#cbd8df;--accent:#075c70;--paper:#fff;--wash:#f3f7f9}
*{box-sizing:border-box}body{margin:0;background:var(--wash);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1040px;margin:auto;padding:32px 24px 64px}h1{font-size:2rem;line-height:1.2;margin:12px 0}h2{font-size:1.25rem;margin:30px 0 12px}h3{font-size:1rem}
p{margin:10px 0}a{color:var(--accent);text-underline-offset:3px}a:hover{color:#003945}a:focus-visible,summary:focus-visible{outline:3px solid #b45309;outline-offset:4px}
.brand{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;font-weight:750;color:var(--accent)}.lede,.meta,footer{color:var(--muted)}
.status{padding:18px 20px;border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:8px;background:var(--paper);margin:20px 0}.status strong{display:block;font-size:1.15rem}.status.warn{border-left-color:#b45309}.counts{display:block;margin-top:6px;font-variant-numeric:tabular-nums}
nav{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}nav a{padding:7px 12px;border:1px solid var(--line);border-radius:5px;background:white}
.card,details{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:16px 20px;margin:12px 0}summary{cursor:pointer;font-weight:650}.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px}.cards .card{margin:0}
ul,ol{padding-left:24px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;background:white;font-size:.9rem}th,td{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}th{background:#eaf1f5}#evidence th:nth-child(1){width:45%}#evidence th:nth-child(2){width:20%}#evidence th:nth-child(3){width:35%}#evidence td:nth-child(2){overflow-wrap:normal}caption{text-align:left;color:var(--muted);padding:10px 0}td small{display:block;color:var(--muted);margin-top:6px}
code{font-family:ui-monospace,Menlo,monospace;font-size:.85em;overflow-wrap:anywhere}.command{display:block;padding:12px;background:#eaf1f5;border-radius:5px}dl.prov{display:grid;grid-template-columns:170px 1fr;gap:10px}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}footer{margin-top:32px;border-top:1px solid var(--line);padding-top:16px;font-size:.85rem}.remediation{border-left:5px solid #b45309;padding:14px;background:#fff4e5}
@media(max-width:640px){#evidence thead{position:absolute;width:1px;height:1px;clip-path:inset(50%);overflow:hidden}#evidence tbody,#evidence tr,#evidence td{display:block;width:100%}#evidence tr{border:1px solid var(--line);margin-bottom:12px;border-radius:6px}#evidence td{border:0}#evidence td::before{content:attr(data-label);display:block;font-weight:650;color:var(--muted);margin-bottom:4px}main{padding:20px 16px 40px}h1{font-size:1.6rem}.cards{grid-template-columns:1fr}dl.prov{grid-template-columns:1fr;gap:4px}dd{margin-bottom:12px}th,td{padding:8px}.card,details{padding:14px}}
@media print{body{background:white;font-size:11pt}main{max-width:none;padding:0}nav{display:none}details{break-inside:avoid}details>*{display:block!important}details::details-content{display:block!important;content-visibility:visible!important}.card{break-inside:avoid}a{color:inherit}.table-wrap{overflow:visible}}
`

// BuyerOnePagerHTML renders an actionable recipient overview. The historical
// fingerprint computation above is unchanged for existing readers.
func BuyerOnePagerHTML(d OnePagerDTO) string {
	status, class := "Selected checks passed — review still needed", "ok"
	if !d.Passed {
		status, class = "Findings need attention", "warn"
	}
	if d.SkippedRules > 0 {
		status, class = "Incomplete check — run a full evaluation", "warn"
	}
	labels := strings.TrimSpace(d.PackLabels)
	if labels == "" {
		labels = d.PackID
	}
	var cover, findings strings.Builder
	for _, r := range d.CoverRows {
		result := r.Result
		if result == "" {
			result = "Not evaluated"
		}
		path := r.Path
		if path == "" {
			path = "No document path supplied"
		}
		fmt.Fprintf(&cover, `<tr><td data-label="Review task">%s</td><td data-label="Check result">%s</td><td data-label="Referenced evidence"><code>%s</code><small>Not included — request supporting evidence. For sensitive checks, request a redacted summary.</small></td></tr>`, html.EscapeString(r.Question), html.EscapeString(result), html.EscapeString(path))
	}
	if len(d.CoverRows) == 0 {
		cover.WriteString(`<tr><td colspan="3">No review tasks supplied. Ask the producer which checks apply.</td></tr>`)
	}
	for _, f := range d.Failures {
		fmt.Fprintf(&findings, `<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>`, html.EscapeString(f.GateID), html.EscapeString(f.Severity), html.EscapeString(f.Description))
	}
	if len(d.Failures) == 0 {
		findings.WriteString(`<tr><td colspan="3">No open findings in the selected checks.</td></tr>`)
	}
	signature := "No verified signer. This unsigned report does not establish who produced it."
	if !d.UnsignedLoud {
		signature = d.AttestLine + ". Key use does not establish human approval."
	}
	body := fmt.Sprintf(`<div class="brand">Curbpack · Review overview</div>
<h1>%s</h1><p class="lede">A record of selected repository checks. Use it to identify evidence to inspect and questions to resolve; it is not a certificate of conformity.</p>
<div class="status %s"><strong>%s</strong><span class="counts">%d failed · %d evaluated · %d skipped</span></div>
<p><strong>Checks selected:</strong> %s</p>
<nav aria-label="Report sections"><a href="#next">Next steps</a><a href="#evidence">Evidence checklist</a><a href="#findings">Findings</a><a href="#provenance">Verification details</a></nav>
<section id="next"><h2>What to do next</h2>
<div class="cards"><div class="card"><h3>Internal team or producer</h3><p>Address findings, run <code>curbpack check</code>, then review the source changes before sharing. Use <code>curbpack review --repo .</code> to check document references.</p></div>
<div class="card"><h3>Buyer or insurer</h3><p>Confirm the intended product, version and use. Request the referenced evidence, support commitments and unresolved risks. Decide whether more evidence is needed before a purchase or coverage decision.</p></div>
<div class="card"><h3>Reviewer or auditor</h3><p>Check the received folder, inspect the supporting evidence, and record your findings. Matching hashes do not establish producer identity, complete product evidence or applicability.</p></div>
<div class="card"><h3>Agent or automation</h3><p>Use <code>curbpack check --json</code> for gates and <code>curbpack review review-pack --json</code> for separate trust results. Preserve exit codes. Leave approval and signing to a person.</p></div></div>
<p>Keep the whole received folder together. From its parent directory, run:</p><code class="command">curbpack review review-pack</code><p>If the folder has another name, substitute that name. A single HTML file is a reading copy, not a complete verifiable pack. If Curbpack is not installed, ask your technical reviewer to run this check.</p>
<details><summary>How to interpret verification</summary><ul><li><strong>Integrity:</strong> run review to check whether included files match their manifest.</li><li><strong>Authenticity:</strong> %s</li><li><strong>Completeness:</strong> review checks declared files only, not all product evidence.</li><li><strong>Applicability:</strong> you must establish whether this product, policy and date match your intended use.</li></ul><p>This page cannot verify its own contents. Use the CLI on the received folder.</p></details></section>
<section id="evidence"><h2>Evidence checklist</h2><p>These are review tasks, not answers from a person. Product source files are not included automatically. Request only the evidence needed through an approved channel; do not request raw credentials or private keys.</p><div class="table-wrap"><table><caption>All %d review tasks · a passed structure check does not settle the content</caption><thead><tr><th scope="col">Review task</th><th scope="col">Check result</th><th scope="col">Referenced evidence</th></tr></thead><tbody>%s</tbody></table></div></section>
<section id="findings"><h2>Findings</h2><div class="table-wrap"><table><thead><tr><th scope="col">Check</th><th scope="col">Priority</th><th scope="col">Finding</th></tr></thead><tbody>%s</tbody></table></div></section>
<section id="provenance"><h2>Verification details</h2><p>Local gate tally: <strong>failed=%d evaluated=%d skipped=%d</strong> — not certification. Signing is optional and separate from this review.</p><details><summary>Recorded inputs and digests</summary>%s</details><details><summary>Sources and method scope</summary><p>Method scope: %s. The selected checks prepare evidence for human review; they do not assess conformity.</p>%s</details></section>
<footer>Generated %s. Record your decision and any missing evidence in your own review process. No feedback is sent by this page.</footer>`, html.EscapeString(d.RepoName), class, html.EscapeString(status), d.FailedRules, d.EvaluatedRules, d.SkippedRules, html.EscapeString(labels), html.EscapeString(signature), len(d.CoverRows), cover.String(), findings.String(), d.FailedRules, d.EvaluatedRules, d.SkippedRules, d.ProvenanceHTML, html.EscapeString(d.AssuranceClass), d.SourcesHTML, html.EscapeString(d.Timestamp))
	return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Curbpack — Review overview</title><!-- curbpack-onepager-fp:` + OnePagerFingerprint(d) + ` --><style>` + reportCSS + `</style></head><body><main>` + body + `</main></body></html>`
}
