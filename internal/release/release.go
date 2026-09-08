package release

import (
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/clock"
	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/outwrite"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/redact"
	"github.com/afelin/curbpack/internal/release/templates"
	"github.com/afelin/curbpack/internal/research"
	"github.com/afelin/curbpack/internal/sbom"
	"github.com/afelin/curbpack/internal/tty"
	"github.com/afelin/curbpack/internal/validate"
	"github.com/afelin/curbpack/internal/vex"
)

// Options for prepare-release.
type Options struct {
	AsOf              string
	RepoRoot          string
	PackIDs           []string
	OutDir            string
	AllowFailingGates bool              // if false, non-zero exit when gates fail (after writing review pack)
	Result            *validate.Result  // when set, skip validate.Run (share threads one evaluation)
	ExtraArtifacts    map[string][]byte // share companions, published in the same completed set
}

// Prepare writes the review pack: Annex VII drafts (if missing), three-layer reports, buyer HTML.
func Prepare(opts Options) error {
	if _, _, err := clock.EvaluationAsOf(opts.AsOf); err != nil {
		return err
	}
	root := opts.RepoRoot
	repoAbs, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	outPermitted, out, err := outwrite.DirDest(root, opts.OutDir, "review-pack")
	if err != nil {
		return err
	}

	// Repository artifacts and an explicit outside pack are both written by this
	// operation. Acquire repository first consistently; nested mappers are pure.
	lock, err := outwrite.Acquire(repoAbs)
	if err != nil {
		return err
	}
	defer lock.Release()
	if outPermitted != repoAbs {
		outLock, err := outwrite.Acquire(outPermitted)
		if err != nil {
			return err
		}
		defer outLock.Release()
	}

	if err := outwrite.EnsureDir(outPermitted, out); err != nil {
		return err
	}

	// Ensure witness / annex scaffolds exist (edit in any markdown editor).
	if opts.Result == nil {
		if err := ensureWitnessTemplates(repoAbs, opts.PackIDs); err != nil {
			return err
		}
	}

	var res validate.Result
	if opts.Result != nil {
		res = *opts.Result
		if res.Evaluation.SchemaVersion == ir.EvaluationSchemaVersion {
			if err := validate.VerifyResultInputs(root, res); err != nil {
				return err
			}
		}
	} else {
		res, err = validate.Run(validate.Options{RepoRoot: root, PackIDs: opts.PackIDs, Quiet: true, Writer: lock, AsOf: opts.AsOf})
		if err != nil {
			return err
		}
	}

	return prepareWithResult(repoAbs, outPermitted, out, opts, res)
}

func prepareWithResult(repoAbs, outPermitted, out string, opts Options, res validate.Result) error {
	var prepErrs []error
	output := map[string][]byte{}
	var repoFiles []outwrite.Artifact
	record := func(err error) {
		if err != nil {
			prepErrs = append(prepErrs, err)
		}
	}
	writeOut := func(name string, data []byte) {
		output[name] = data
	}
	writeRepo := func(rel string, data []byte) {
		dest, _, err := validate.SafeJoin(repoAbs, rel)
		if err != nil {
			record(err)
			return
		}
		repoFiles = append(repoFiles, outwrite.Artifact{PermittedRoot: repoAbs, Path: dest, Data: data})
	}

	// Layer 1: machine JSON
	layer1, _ := json.MarshalIndent(res.Payload, "", "  ")
	writeOut("01-gate-failures.json", append(layer1, '\n'))

	// Layer 2: semantic markdown for agents
	md := validate.ActionReportMarkdown(res.Payload, res.SkippedRules)
	if len(res.Payload.Failures) > 0 {
		md += "\n" + validate.SemanticMarkdown(res.Payload)
	}
	writeOut("02-action-report.md", []byte(md))

	// Layer 3: executive summary markdown
	execMD := executiveSummary(res)
	writeOut("03-executive-summary.md", []byte(execMD))

	// SBOM summary + CycloneDX 1.5 (best-effort from lockfile)
	sbomSummary, sbomErr := sbom.FromLockfiles(repoAbs)
	if sbomErr != nil {
		writeOut("04-sbom-summary.json", []byte(`{"status":"unavailable","detail":`+jsonString(sbomErr.Error())+"}\n"))
	} else {
		pkgs, source, err := sbom.CollectPackages(repoAbs)
		if err != nil {
			record(err)
		} else if doc, err := sbom.BuildCycloneDX(repoAbs, pkgs, source); err != nil {
			record(err)
		} else if data, err := json.MarshalIndent(doc, "", "  "); err != nil {
			record(err)
		} else {
			data = append(data, '\n')
			writeRepo(".github/curbpack/evidence/sbom.cdx.json", data)
			writeOut("04-sbom.cdx.json", data)
			sbomSummary.CycloneDXPath = ".github/curbpack/evidence/sbom.cdx.json"
			sbomSummary.Format = "CycloneDX-1.5"
		}
		b, _ := json.MarshalIndent(sbomSummary, "", "  ")
		writeOut("04-sbom-summary.json", append(b, '\n'))
	}

	// Pending OpenVEX from dependency-shaped findings only (gates stay in IR).
	vexDoc, vexErr := vex.FromGateFailures(filepath.Base(repoAbs), res.Payload)
	if vexErr != nil {
		record(fmt.Errorf("vex: %w", vexErr))
	} else {
		data, err := json.MarshalIndent(vexDoc, "", "  ")
		if err != nil {
			record(err)
		} else {
			data = append(data, '\n')
			writeRepo(".github/curbpack/evidence/vex-pending.json", data)
			writeOut("05-vex-draft.json", data)
		}
	}

	// SARIF layer (same mapper as CLI export --sarif)
	sarifDoc := exportx.FromGateFailures(res.Payload, repoAbs)
	sarifBytes, _ := json.MarshalIndent(sarifDoc, "", "  ")
	writeOut("06-gate-failures.sarif", append(sarifBytes, '\n'))
	writeRepo(".github/curbpack/cache/curbpack.sarif", append(sarifBytes, '\n'))

	// Informational watchlist ∩ SBOM join
	if report, err := exportx.BuildWatchlistJoin(repoAbs); err != nil {
		record(fmt.Errorf("watchlist join: %w", err))
	} else if data, err := json.MarshalIndent(report, "", "  "); err != nil {
		record(err)
	} else {
		data = append(data, '\n')
		writeRepo(".github/curbpack/cache/watchlist-sbom-join.json", data)
		writeOut("07-watchlist-sbom-join.json", data)
	}
	// Hash the staged artifacts, never a previous emission's files.
	htmlDoc := buyerOnePagerWithDigests(repoAbs, res, digestIfPresent(output["04-sbom.cdx.json"]), digestIfPresent(output["05-vex-draft.json"]))
	writeOut("buyer-onepager.html", []byte(htmlDoc))

	// Copy / refresh proof page into review-pack and repo proof/
	proof := templates.ProofPageHTML()
	writeRepo("proof/index.html", []byte(proof))
	writeOut("proof-index.html", []byte(proof))

	if len(prepErrs) > 0 {
		return errors.Join(prepErrs...)
	}
	for name, data := range opts.ExtraArtifacts {
		if _, _, err := validate.SafeJoin(out, name); err != nil {
			return err
		}
		if _, exists := output[name]; exists || name == ir.PackManifestFile || name == "evaluation.json" || name == "run-receipt.json" {
			return fmt.Errorf("duplicate pack artifact %q", name)
		}
		output[name] = data
	}
	var manifest []byte
	if res.Evaluation.SchemaVersion == ir.EvaluationSchemaVersion {
		raw, err := ir.MarshalCanonical(res.Evaluation)
		if err != nil {
			return err
		}
		if err := ir.ValidateEvaluation(res.Evaluation); err != nil {
			return err
		}
		if err := ir.ValidateReceipt(res.Receipt, res.Evaluation, ir.BytesDigest(raw)); err != nil {
			return err
		}
		output["evaluation.json"] = raw
		receipt, err := ir.MarshalReceipt(res.Receipt)
		if err != nil {
			return err
		}
		output["run-receipt.json"] = receipt
		m, err := ir.NewPackManifest(output)
		if err != nil {
			return err
		}
		manifest, err = ir.MarshalPackManifest(m)
		if err != nil {
			return err
		}
	}
	names := make([]string, 0, len(output))
	for name := range output {
		names = append(names, name)
	}
	sort.Strings(names)
	files := repoFiles
	for _, name := range names {
		files = append(files, outwrite.Artifact{PermittedRoot: outPermitted, Path: filepath.Join(out, name), Data: output[name]})
	}
	if manifest != nil {
		files = append(files, outwrite.Artifact{PermittedRoot: outPermitted, Path: filepath.Join(out, ir.PackManifestFile), Data: manifest})
	}
	// Never rewrite canonical evaluation, signed pointers or evidence to hide a
	// leak. Refuse the complete publication before any file is replaced.
	ctx := redact.Verify(redact.Embedded)
	for _, file := range files {
		var err error
		switch strings.ToLower(filepath.Ext(file.Path)) {
		case ".json", ".sarif":
			err = redact.JSONLooksClean(file.Data, ctx)
		default:
			err = redact.LooksClean(file.Data, ctx)
		}
		if err != nil {
			return fmt.Errorf("pack artifact %s failed redaction verification: %w", filepath.Base(file.Path), err)
		}
	}
	if err := outwrite.Publish(files); err != nil {
		return err
	}
	tty.PrintStatus("Buyer one-pager", true, filepath.Join(out, "buyer-onepager.html"))

	tty.PrintStatus("Review pack", true, out)
	if !res.Passed {
		fmt.Printf("%s\n", tty.C(tty.Yellow, "[!] Gates still failing — pack is for remediation review, not release sign-off."))
	}
	if tty.IsTerminal {
		tty.RenderCounts(res.FailedRules, res.EvaluatedRules, res.SkippedRules, !res.Passed)
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

// writeOnePagerIfChanged skips rewrite when the on-disk body matches the new
// document aside from wall-clock "Generated" lines. Never trust the HTML
// fingerprint marker alone — a forged page can copy the current marker (FG-01).
func writeOnePagerIfChanged(permitted, path, htmlDoc string) (bool, error) {
	fp := onePagerContentFingerprint(htmlDoc)
	if prev, err := os.ReadFile(path); err == nil {
		if onePagerContentFingerprint(string(prev)) == fp && fp != "" {
			return false, nil
		}
	}
	if err := outwrite.WriteFile(permitted, path, []byte(htmlDoc), 0o644); err != nil {
		return false, err
	}
	return true, nil
}

// onePagerContentFingerprint hashes the HTML body ignoring Generated timestamps.
// It does not trust <!-- curbpack-onepager-fp:… --> (INV-02 / FG-01).
func onePagerContentFingerprint(htmlDoc string) string {
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

// onePagerFingerprint extracts the claimed marker when present; otherwise hashes content.
// Used for ShareStale claimed-marker extraction — not for rewrite skip decisions.
func onePagerFingerprint(htmlDoc string) string {
	const marker = "<!-- curbpack-onepager-fp:"
	if i := strings.Index(htmlDoc, marker); i >= 0 {
		rest := htmlDoc[i+len(marker):]
		if j := strings.Index(rest, " -->"); j >= 0 {
			return rest[:j]
		}
	}
	return onePagerContentFingerprint(htmlDoc)
}

func ensureWitnessTemplates(root string, requested []string) error {
	ids, err := config.ResolvePackIDs(root, requested)
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
	var pending []outwrite.Artifact
	for _, rel := range paths {
		path, clean, err := validate.SafeJoin(root, rel)
		if err != nil {
			return fmt.Errorf("scaffold path refused: %s: %w", rel, err)
		}
		if _, err := os.Stat(path); err == nil {
			continue
		} else if !os.IsNotExist(err) {
			return err
		}
		pending = append(pending, outwrite.Artifact{PermittedRoot: root, Path: path, Data: []byte(packs.DefaultScaffoldBody(clean))})
	}
	return outwrite.Publish(pending)
}

func executiveSummary(res validate.Result) string {
	var b strings.Builder
	b.WriteString("# Executive Summary — Supplier Readiness\n\n")
	b.WriteString("> Curbpack prepares evidence for **human review**. It does not certify conformity.\n\n")
	if res.Payload.EvaluationDigest != "" {
		fmt.Fprintf(&b, "- **Evaluation:** `%s`\n- **As of:** %s\n", res.Payload.EvaluationDigest, res.Payload.AsOf)
	} else {
		fmt.Fprintf(&b, "- **Generated:** %s\n", res.Payload.Timestamp)
	}
	fmt.Fprintf(&b, "- **Packs:** %s\n", res.Payload.PackID)
	fmt.Fprintf(&b, "- **Failed / evaluated / skipped:** %d / %d / %d\n", res.FailedRules, res.EvaluatedRules, res.SkippedRules)
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

func buyerOnePager(root, outDir string, res validate.Result) string {
	return buyerOnePagerWithDigests(root, res, fileSHA256Hex(filepath.Join(outDir, "04-sbom.cdx.json")), fileSHA256Hex(filepath.Join(outDir, "05-vex-draft.json")))
}

func digestIfPresent(raw []byte) string {
	if len(raw) == 0 {
		return ""
	}
	return ir.BytesDigest(raw)
}

func buyerOnePagerWithDigests(root string, res validate.Result, sbomDigest, vexDigest string) string {
	name := filepath.Base(root)
	bind, _ := attest.LatestBind(root)
	line, class, unsignedLoud := attest.AttestDisplay(bind)
	var failures []templates.OnePagerFailure
	failedGates := map[string]struct{}{}
	for _, f := range res.Payload.Failures {
		failures = append(failures, templates.OnePagerFailure{
			GateID:      f.GateID,
			Severity:    f.Severity,
			Description: f.SanitizedDescription,
		})
		failedGates[f.GateID] = struct{}{}
	}
	assuranceClass := buyerQuestionsAssuranceClass
	mechanicalSummary := ""
	if ids := nonzeroPackCSV(res.Payload.PackID); len(ids) > 0 {
		if composed, _, err := packs.Compose(ids); err == nil {
			if ac := strings.TrimSpace(composed.AssuranceClass); ac != "" {
				assuranceClass = ac
			}
			total := res.EvaluatedRules
			evidenced := total - len(failedGates)
			if evidenced < 0 {
				evidenced = 0
			}
			if total > 0 {
				mechanicalSummary = fmt.Sprintf("%d of %d evaluated gates mechanically evidenced; %d skipped", evidenced, total, res.SkippedRules)
			}
		}
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
	resultDigest := ir.ComputeResultDigest(res.Payload)
	dto := templates.OnePagerDTO{
		RepoName:          name,
		Score:             res.Score,
		FailedRules:       res.FailedRules,
		EvaluatedRules:    res.EvaluatedRules,
		SkippedRules:      res.SkippedRules,
		Passed:            res.Passed,
		PackID:            res.Payload.PackID,
		PackLabels:        exportx.PackPlainNames(res.Payload.PackID),
		Timestamp:         res.Payload.Timestamp,
		Failures:          failures,
		CoverRows:         cover,
		Bind:              bind,
		AttestLine:        line,
		AttestClass:       class,
		UnsignedLoud:      unsignedLoud,
		AssuranceClass:    assuranceClass,
		MechanicalSummary: mechanicalSummary,
		ProvenanceHTML:    provenanceDL(res.Payload, bind, line, unsignedLoud, resultDigest, sbomDigest, vexDigest),
		SourcesHTML:       sourcesStrip(root, res.Payload.PackID),
		FooterPrefix:      footerHTML(line, unsignedLoud),
		ResultDigest:      resultDigest,
		SBOMDigest:        sbomDigest,
		VEXDigest:         vexDigest,
	}
	return templates.BuyerOnePagerHTML(dto)
}

const buyerQuestionsAssuranceClass = "structural_draft"

func nonzeroPackCSV(csv string) []string {
	var out []string
	for _, id := range strings.Split(csv, ",") {
		id = strings.TrimSpace(id)
		if id != "" {
			out = append(out, id)
		}
	}
	return out
}

func footerHTML(line string, unsignedLoud bool) string {
	if unsignedLoud {
		return `<span class="unsigned-foot">` + html.EscapeString(line) + `</span>`
	}
	return html.EscapeString(line) + " · "
}

func provenanceDL(payload ir.GateFailurePayload, bind attest.BindInfo, line string, unsignedLoud bool, payloadDigest, sbomDigest, vexDigest string) string {
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
	signOff := "Pending human review. A signature does not establish human review or approval."
	if !unsignedLoud {
		signOff = "Signature verified against the selected policy. Human review and approval are separate."
	}

	// Payload / file digests are source of truth for the share; bind values that
	// disagree are emitted alongside so the offline reader can contradict.
	// Digests never upgrade UNSIGNED / not-cryptographically-verified rendering.

	var b strings.Builder
	b.WriteString(`<dl class="prov">`)
	fmt.Fprintf(&b, "<dt>Rule packs</dt><dd>%s</dd>\n", html.EscapeString(payload.PackID))
	fmt.Fprintf(&b, "<dt>Commit</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(commit)))
	fmt.Fprintf(&b, "<dt>Attest</dt><dd>%s</dd>\n", html.EscapeString(line))
	fmt.Fprintf(&b, "<dt>Signer</dt><dd>%s</dd>\n", html.EscapeString(signer))
	fmt.Fprintf(&b, "<dt>User touch</dt><dd>%s</dd>\n", html.EscapeString(touch))
	fmt.Fprintf(&b, "<dt>state_hash</dt><dd>%s</dd>\n", html.EscapeString(state))
	fmt.Fprintf(&b, "<dt>result_digest</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(payloadDigest)))
	if bind.ResultDigest != "" && !digestPrefixAgree(payloadDigest, bind.ResultDigest) {
		fmt.Fprintf(&b, "<dt>result_digest_bind</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(bind.ResultDigest)))
	}
	if sbomDigest != "" {
		fmt.Fprintf(&b, "<dt>sbom_digest</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(sbomDigest)))
		if bind.SBOMDigest != "" && !digestPrefixAgree(sbomDigest, bind.SBOMDigest) {
			fmt.Fprintf(&b, "<dt>sbom_digest_bind</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(bind.SBOMDigest)))
		}
	} else if bind.SBOMDigest != "" {
		// No file on disk — still surface bind claim so reader can leave it unconfirmed.
		fmt.Fprintf(&b, "<dt>sbom_digest_bind</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(bind.SBOMDigest)))
	}
	if vexDigest != "" {
		fmt.Fprintf(&b, "<dt>vex_digest</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(vexDigest)))
		if bind.VEXDigest != "" && !digestPrefixAgree(vexDigest, bind.VEXDigest) {
			fmt.Fprintf(&b, "<dt>vex_digest_bind</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(bind.VEXDigest)))
		}
	} else if bind.VEXDigest != "" {
		fmt.Fprintf(&b, "<dt>vex_digest_bind</dt><dd>%s</dd>\n", html.EscapeString(truncateSHA(bind.VEXDigest)))
	}
	if name := strings.TrimSpace(bind.ReviewedBy); name != "" {
		fmt.Fprintf(&b, "<dt>Reviewed by</dt><dd>%s — recorded review, not assessment.</dd>\n", html.EscapeString(name))
	}
	fmt.Fprintf(&b, "<dt>Human sign-off</dt><dd>%s</dd>\n", html.EscapeString(signOff))
	b.WriteString(`<dt>Verify</dt><dd>proof/index.html + local evidence pointer (client-side hash compare)</dd>`)
	b.WriteString(`</dl>`)
	return b.String()
}

func fileSHA256Hex(path string) string {
	data, err := os.ReadFile(path)
	if err != nil || len(data) == 0 {
		return ""
	}
	sum := sha256.Sum256(data)
	return fmt.Sprintf("%x", sum)
}

// digestComparePrefixLen is the fixed truncation length for digest agreement (MUST-12).
// Claimed values shorter than this cannot confirm. Keep in sync with review.DigestComparePrefixLen.
const digestComparePrefixLen = 12

// digestPrefixAgree mirrors the offline reviewer's fixed-prefix contract (MUST-12).
func digestPrefixAgree(full, claimed string) bool {
	claimed = strings.TrimSpace(claimed)
	claimed = strings.TrimSuffix(claimed, "…")
	claimed = strings.TrimSuffix(claimed, "...")
	claimed = strings.TrimSpace(claimed)
	if claimed == "" || full == "" {
		return false
	}
	n := digestComparePrefixLen
	if len(claimed) < n || len(full) < n {
		return false
	}
	if len(claimed) == n {
		return full[:n] == claimed
	}
	return strings.HasPrefix(full, claimed)
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

// ProofPageHTML delegates to templates package.
func ProofPageHTML() string {
	return templates.ProofPageHTML()
}

// WriteEvidenceBundle writes review-pack/evidence-bundle.html for offline handoff.
func WriteEvidenceBundle(root string, res validate.Result) (string, error) {
	repoAbs, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	permitted, out, err := outwrite.FileDest(repoAbs, "", "review-pack/evidence-bundle.html")
	if err != nil {
		return "", err
	}
	lock, err := outwrite.Acquire(permitted)
	if err != nil {
		return "", err
	}
	defer lock.Release()

	onepagerPath := filepath.Join(filepath.Dir(out), "buyer-onepager.html")
	var onePagerMain string
	if b, err := os.ReadFile(onepagerPath); err == nil {
		onePagerMain = templates.ExtractOnePagerMain(string(b))
	}
	hpurlFrag := ""
	hpurlJSON := ""
	ptrPath := filepath.Join(repoAbs, ".github", "curbpack", "evidence", "hpurl-pointer.json")
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
		RepoName:       filepath.Base(repoAbs),
		Score:          res.Score,
		FailedRules:    res.FailedRules,
		EvaluatedRules: res.EvaluatedRules,
		SkippedRules:   res.SkippedRules,
		Passed:         res.Passed,
		Timestamp:      res.Payload.Timestamp,
		OnePagerBody:   onePagerMain,
		HPURLFragment:  hpurlFrag,
		HPURLEmbedJSON: hpurlJSON,
		Remediation:    !res.Passed,
	})
	if err := outwrite.WriteFile(permitted, out, []byte(doc), 0o644); err != nil {
		return "", err
	}
	return out, nil
}

// PrepareScaffolds creates draft inputs before share's single evaluation. A
// supplied Result is never silently changed by scaffolding during publication.
func PrepareScaffolds(root string, packIDs []string) error {
	abs, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	lock, err := outwrite.Acquire(abs)
	if err != nil {
		return err
	}
	defer lock.Release()
	return ensureWitnessTemplates(abs, packIDs)
}
