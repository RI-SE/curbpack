package cli

import "testing"

func TestAskDocumentedArgumentOrder(t *testing.T) {
	for _, args := range [][]string{{"failure.json", "--propose"}, {"--propose", "failure.json"}, {"failure.json", "--propose=true"}} {
		f, err := parseAskFlags(args)
		if err != nil || f.path != "failure.json" || !f.propose {
			t.Errorf("%v: flags=%+v error=%v", args, f, err)
		}
	}
}

func TestAskRejectsUnknownAndExtraArguments(t *testing.T) {
	for _, args := range [][]string{{"failure.json", "--bogus"}, {"a.json", "b.json"}, {"--propose=invalid"}} {
		if _, err := parseAskFlags(args); err == nil {
			t.Errorf("accepted %v", args)
		}
	}
	f, err := parseAskFlags([]string{"--", "--propose"})
	if err != nil || f.path != "--propose" || f.propose {
		t.Fatalf("literal path: %+v %v", f, err)
	}
}
