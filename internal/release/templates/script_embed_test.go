package templates_test

import (
	"encoding/json"
	"regexp"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/release/templates"
)

// FG-02: repository-derived JSON embedded raw in a <script> element can close
// the element early and alter offline bundle presentation (INV-05, INV-06 / MUST-43).
func TestEvidenceBundleScriptEmbedEscapesBreakout(t *testing.T) {
	malicious := `{"hpurl":"</script><p id=\"fg02-injected\">altered</p><script>"}`
	htmlDoc := templates.EvidenceBundleHTML(templates.BundleDTO{
		RepoName:       "sample",
		Score:          80,
		Passed:         true,
		Timestamp:      "2026-08-13T00:00:00Z",
		HPURLEmbedJSON: malicious,
	})

	if strings.Contains(htmlDoc, `id="fg02-injected"`) {
		t.Fatal("script breakout altered offline bundle presentation")
	}
	if strings.Contains(htmlDoc, `</script><p id=`) {
		t.Fatal("raw </script> from embed closed the script element early")
	}

	re := regexp.MustCompile(`(?s)<script type="application/json" id="curbpack-hpurl-pointer">(.*?)</script>`)
	m := re.FindStringSubmatch(htmlDoc)
	if m == nil {
		t.Fatal("missing curbpack-hpurl-pointer script element")
	}
	body := m[1]
	if strings.Contains(strings.ToLower(body), "</script") {
		t.Fatalf("script body still contains a script closer: %q", body)
	}
	if !strings.Contains(body, `\u003c`) {
		t.Fatalf("expected Unicode escapes for angle brackets in script body; got %q", body)
	}

	var got map[string]any
	if err := json.Unmarshal([]byte(body), &got); err != nil {
		t.Fatalf("escaped embed must remain valid JSON: %v\nbody=%q", err, body)
	}
	hpurl, _ := got["hpurl"].(string)
	if !strings.Contains(hpurl, "</script>") {
		t.Fatalf("JSON round-trip must restore original hpurl value; got %q", hpurl)
	}
}

func TestEvidenceBundleScriptEmbedBenignJSON(t *testing.T) {
	benign := `{"hpurl":"curbpack://stamp/abc","v":1}`
	htmlDoc := templates.EvidenceBundleHTML(templates.BundleDTO{
		RepoName: "sample", Score: 80, Passed: true, Timestamp: "2026-08-13T00:00:00Z",
		HPURLEmbedJSON: benign,
	})
	re := regexp.MustCompile(`(?s)<script type="application/json" id="curbpack-hpurl-pointer">(.*?)</script>`)
	m := re.FindStringSubmatch(htmlDoc)
	if m == nil {
		t.Fatal("missing curbpack-hpurl-pointer script element")
	}
	var got map[string]any
	if err := json.Unmarshal([]byte(m[1]), &got); err != nil {
		t.Fatalf("benign embed must remain valid JSON: %v", err)
	}
	if got["hpurl"] != "curbpack://stamp/abc" {
		t.Fatalf("hpurl=%v", got["hpurl"])
	}
}
