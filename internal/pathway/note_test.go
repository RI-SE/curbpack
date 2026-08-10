package pathway

import (
	"errors"
	"path/filepath"
	"reflect"
	"testing"
)

func TestNoteSetAndForget(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	// Bootstrap minimal seed via Write
	if err := Write(dir, Seed{ProposedPacks: []string{"house-policy"}}); err != nil {
		t.Fatal(err)
	}

	s, err := NoteSet(dir, "prefer house-first wording")
	if err != nil {
		t.Fatal(err)
	}
	if len(s.SessionNotes) != 1 || s.SessionNotes[0] != "prefer house-first wording" {
		t.Fatalf("session_notes=%v", s.SessionNotes)
	}

	s, err = NoteSet(dir, "product_name=Acme Widget")
	if err != nil {
		t.Fatal(err)
	}
	if s.Corrections["product_name"] != "Acme Widget" {
		t.Fatalf("corrections=%v", s.Corrections)
	}

	s, err = NoteSet(dir, "last_draft_pick=A")
	if err != nil {
		t.Fatal(err)
	}
	if s.LastDraftPick != "A" {
		t.Fatalf("last_draft_pick=%q", s.LastDraftPick)
	}

	if _, err := NoteSet(dir, "last_draft_pick=Z"); err == nil || !errors.Is(err, ErrUsage) {
		t.Fatalf("expected usage refuse for bad pick, got %v", err)
	}

	s, err = NoteForget(dir, "product_name")
	if err != nil {
		t.Fatal(err)
	}
	if len(s.Corrections) != 0 {
		t.Fatalf("expected corrections cleared, got %v", s.Corrections)
	}

	s, err = NoteForget(dir, "prefer house-first wording")
	if err != nil {
		t.Fatal(err)
	}
	if len(s.SessionNotes) != 0 {
		t.Fatalf("session_notes=%v", s.SessionNotes)
	}

	s, err = NoteForget(dir, "last_draft_pick")
	if err != nil {
		t.Fatal(err)
	}
	if s.LastDraftPick != "" {
		t.Fatalf("last_draft_pick=%q", s.LastDraftPick)
	}

	loaded, err := Load(dir)
	if err != nil || loaded == nil {
		t.Fatalf("Load: %v %v", loaded, err)
	}
	if loaded.Claim != ClaimFence {
		t.Fatalf("claim=%q", loaded.Claim)
	}
	if filepath.Base(SeedPath(dir)) != "pathway-seed.json" {
		t.Fatal("unexpected seed path")
	}
}

func TestApplySuggestPreservesSessionMemory(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	prev := Seed{
		ProposedPacks: []string{"house-policy"},
		SessionNotes:  []string{"keep me"},
		Corrections:   map[string]string{"contact": "ops@example.com"},
		LastDraftPick: "B",
	}
	if err := Write(dir, prev); err != nil {
		t.Fatal(err)
	}
	res, err := Suggest(Answers{
		Product: "hygiene", EuDocs: "no", Medtech: "no",
		Sector: "none", HouseFirst: "yes", CeContext: "none",
	})
	if err != nil {
		t.Fatal(err)
	}
	got, err := ApplySuggest(dir, res)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(got.SessionNotes, prev.SessionNotes) {
		t.Fatalf("notes=%v", got.SessionNotes)
	}
	if got.Corrections["contact"] != "ops@example.com" {
		t.Fatalf("corrections=%v", got.Corrections)
	}
	if got.LastDraftPick != "B" {
		t.Fatalf("pick=%q", got.LastDraftPick)
	}
	if got.HumanTicks.PacksConfirmed {
		t.Fatal("ticks should reset on suggest")
	}
}
