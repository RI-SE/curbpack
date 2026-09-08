package redact_test

import (
	"github.com/afelin/curbpack/internal/redact"
	"strings"
	"testing"
)

func TestJSONRedactionUsesExplicitContextAndPreservesLargeNumbers(t *testing.T) {
	t.Setenv("HOME", "/ignored/ambient-home")
	raw := []byte(`{"home":"/opt/custom-home/private","nested":["/opt/custom-home/doc"],"number":9007199254740993}`)
	for _, mode := range []redact.Mode{redact.Plain, redact.Embedded} {
		ctx := redact.Context{Mode: mode, Home: "/opt/custom-home"}
		clean, err := redact.JSON(raw, ctx)
		if err != nil {
			t.Fatal(err)
		}
		if strings.Contains(string(clean), "/opt/custom-home") || !strings.Contains(string(clean), "9007199254740993") {
			t.Fatalf("JSON contract lost: %s", clean)
		}
		if err := redact.LooksClean(clean, ctx); err != nil {
			t.Fatal(err)
		}
	}
}
func TestJSONRedactionRefusesCollidingKeys(t *testing.T) {
	if _, err := redact.JSON([]byte(`{"/opt/home/x":1,"~/x":2}`), redact.Context{Mode: redact.Plain, Home: "/opt/home"}); err == nil {
		t.Fatal("redaction lost a map field")
	}
}

func TestJSONVerifyFindsEscapedHomeWithoutRewritingEvidence(t *testing.T) {
	raw := []byte(`{"claim":"C:\\Users\\sample\\secret","large":9007199254740993}`)
	if err := redact.JSONLooksClean(raw, redact.Context{Mode: redact.Embedded, Home: `C:\Users\sample`}); err == nil {
		t.Fatal("escaped Windows home accepted")
	}
}
