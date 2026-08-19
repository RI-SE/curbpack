package cli

import "testing"

func TestCommandRegistryCoversCompletionList(t *testing.T) {
	reg := map[string]bool{}
	for _, n := range RegisteredCommandNames() {
		reg[n] = true
	}
	for _, c := range completionCommands {
		if c == "help" || c == "version" {
			continue
		}
		if !reg[c] {
			t.Errorf("registry missing %q from completionCommands", c)
		}
	}
}

func TestCommandRegistryDispatch(t *testing.T) {
	for _, name := range RegisteredCommandNames() {
		if _, ok := lookupCommand(name); !ok {
			t.Errorf("lookupCommand(%q) = false", name)
		}
	}
	if _, ok := lookupCommand("reality-check"); !ok {
		t.Fatal("reality-check alias must resolve to scan")
	}
	if _, ok := lookupCommand("not-a-command"); ok {
		t.Fatal("unknown command should not resolve")
	}
}
