package validate

import (
	"testing"

	"github.com/afelin/curbpack/internal/packs"
)

func TestCheckRegistryCoversEmbeddedPacks(t *testing.T) {
	known := map[CheckKind]bool{}
	for _, k := range KnownCheckKinds() {
		known[k] = true
	}
	for _, id := range []string{"house-policy", "cra-baseline", "medtech-iec62304"} {
		composed, _, err := packs.Compose([]string{id})
		if err != nil {
			t.Fatalf("compose %s: %v", id, err)
		}
		for _, rule := range composed.Rules {
			k := CheckKind(rule.Check)
			if !known[k] {
				t.Errorf("pack %q rule %q uses unregistered check kind %q", id, rule.ID, rule.Check)
			}
		}
	}
}
