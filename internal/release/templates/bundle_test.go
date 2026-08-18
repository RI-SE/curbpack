package templates_test

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/release/templates"
)

func TestEvidenceBundleRetentionLine(t *testing.T) {
	htmlDoc := templates.EvidenceBundleHTML(templates.BundleDTO{
		RepoName: "sample", Score: 80, Passed: true, Timestamp: "2026-08-13T00:00:00Z",
	})
	if !strings.Contains(htmlDoc, "Keep this folder with the release tag for 10 years or the support period, whichever is longer") {
		t.Fatal("missing retention reminder")
	}
	if !strings.Contains(htmlDoc, "Curbpack does not archive it") {
		t.Fatal("must say Curbpack does not archive it")
	}
	if !strings.Contains(htmlDoc, "not a legal fulfillment claim") {
		t.Fatal("must deny legal fulfillment")
	}
	if strings.Contains(htmlDoc, "<h2>HPURL") {
		t.Fatal("user-facing heading must not use HPURL jargon")
	}
}
