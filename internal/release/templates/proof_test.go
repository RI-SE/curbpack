package templates_test

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/release/templates"
)

func TestProofPageStampCopy(t *testing.T) {
	htmlDoc := templates.ProofPageHTML()
	if !strings.Contains(htmlDoc, "<title>Does this folder match the human stamp?</title>") {
		t.Fatal("title must ask whether the folder matches the human stamp")
	}
	if !strings.Contains(htmlDoc, "<h1>Does this folder match the human stamp?</h1>") {
		t.Fatal("heading must match the stamp question")
	}
	titleEnd := strings.Index(htmlDoc, "</title>")
	if titleEnd < 0 {
		t.Fatal("missing title")
	}
	if strings.Contains(strings.ToLower(htmlDoc[:titleEnd]), "hpurl") {
		t.Fatal("title must not use HPURL jargon")
	}
	if !strings.Contains(htmlDoc, "hpurl-pointer.json") {
		t.Fatal("repo-copy auto-fill must still fetch the local pointer file")
	}
	if !strings.Contains(htmlDoc, "Yes — this folder matches the human stamp") {
		t.Fatal("yes copy missing")
	}
	if !strings.Contains(htmlDoc, "No — this folder does not match the human stamp") {
		t.Fatal("no copy missing")
	}
}
