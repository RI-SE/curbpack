package pathway

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestConfirmPacks_RefuseNoSuggest(t *testing.T) {
	dir := t.TempDir()
	_, err := ConfirmPacks(dir)
	if err == nil || !errors.Is(err, ErrUsage) {
		t.Fatalf("want usage refuse, got %v", err)
	}
}

func TestConfirmPacks_RefuseUnknownID(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		Answers:       Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"},
		ProposedPacks: []string{"dora-nis2-theater"},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	_, err := ConfirmPacks(dir)
	if err == nil || !strings.Contains(err.Error(), "unknown pack") {
		t.Fatalf("want unknown pack refuse, got %v", err)
	}
	loaded, err := Load(dir)
	if err != nil || loaded == nil {
		t.Fatal(err)
	}
	if loaded.HumanTicks.PacksConfirmed {
		t.Fatal("tick must not stamp on refuse")
	}
}

func TestConfirmPacks_OK(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		Answers:       Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"},
		ProposedPacks: []string{"house-policy"},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	out, err := ConfirmPacks(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !out.HumanTicks.PacksConfirmed {
		t.Fatal("expected packs_confirmed")
	}
	if out.Claim != ClaimFence {
		t.Fatalf("claim fence=%q", out.Claim)
	}
	graph := filepath.Join(dir, ".github", "curbpack", "graph", "policy-graph.json")
	if _, err := os.Stat(graph); err != nil {
		t.Fatalf("confirm-packs should export RKG: %v", err)
	}
}

func TestConfirmProse_RefuseWithoutPacksTick(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		ProposedPacks: []string{"house-policy"},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	_, err := ConfirmProse(dir)
	if err == nil || !errors.Is(err, ErrUsage) {
		t.Fatalf("want usage refuse, got %v", err)
	}
}

func TestConfirmProse_RefuseMissingFiles(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		ProposedPacks: []string{"house-policy"},
		HumanTicks:    HumanTicks{PacksConfirmed: true},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	// Phase AwaitHealOrProse — confirm-prose is illegal until heal + files exist.
	_, err := ConfirmProse(dir)
	if err == nil || !errors.Is(err, ErrUsage) {
		t.Fatalf("want usage refuse from AwaitHealOrProse, got %v", err)
	}
}

func TestConfirmProse_OKWithDocs(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		ProposedPacks: []string{"house-policy"},
		HumanTicks:    HumanTicks{PacksConfirmed: true},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), []byte(`{"packs":["house-policy"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("# Security\n\nHouse policy prose.\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, ".well-known"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".well-known", "security.txt"), []byte("Contact: security@example.com\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	out, err := ConfirmProse(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !out.HumanTicks.ProseOwned {
		t.Fatal("expected prose_owned")
	}
}

func TestConfirmShare_RefuseWithoutArtifacts(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		ProposedPacks: []string{"house-policy"},
		HumanTicks:    HumanTicks{PacksConfirmed: true, ProseOwned: true},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), []byte(`{"packs":["house-policy"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	// Green check so phase is AwaitShare (not AwaitCheck) — still no share artifacts.
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	_ = os.WriteFile(filepath.Join(cache, "latest_result.json"), []byte(`{"failures":[]}`+"\n"), 0o644)
	_, err := ConfirmShare(dir)
	if err == nil || !errors.Is(err, ErrUsage) {
		t.Fatalf("want usage refuse, got %v", err)
	}
}

func TestConfirmShare_OK(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		ProposedPacks: []string{"house-policy"},
		HumanTicks:    HumanTicks{PacksConfirmed: true, ProseOwned: true},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), []byte(`{"packs":["house-policy"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(cache, "latest_result.json"), []byte(`{"failures":[]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(cache, "buyer-questions.md"), []byte("# q\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(cache, "context-pack.json"), []byte(`{"schema_version":"1"}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	out, err := ConfirmShare(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !out.HumanTicks.ShareReviewed {
		t.Fatal("expected share_reviewed")
	}
}

func TestStatus_OneNextAction(t *testing.T) {
	dir := t.TempDir()
	a, err := Status(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(a.Cmd, "pathway suggest") {
		t.Fatalf("want suggest next, got %+v", a)
	}
	formatted := FormatStatus(a)
	if !strings.Contains(formatted, "next:") || !strings.Contains(formatted, "run:") {
		t.Fatalf("format=%q", formatted)
	}
	// exactly one next/run pair
	if strings.Count(formatted, "next:") != 1 || strings.Count(formatted, "run:") != 1 {
		t.Fatalf("want one next+run, got %q", formatted)
	}
}

func TestApplySuggest_ResetsTicks(t *testing.T) {
	dir := t.TempDir()
	r, err := Suggest(Answers{Product: "shipping", EuDocs: "yes", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"})
	if err != nil {
		t.Fatal(err)
	}
	s, err := ApplySuggest(dir, r)
	if err != nil {
		t.Fatal(err)
	}
	if s.HumanTicks.PacksConfirmed || s.HumanTicks.ProseOwned || s.HumanTicks.ShareReviewed {
		t.Fatalf("ticks must reset: %+v", s.HumanTicks)
	}
	if len(s.ProposedPacks) != 2 {
		t.Fatalf("packs=%v", s.ProposedPacks)
	}
}

func TestConfirmProse_InvalidatesLatestResult(t *testing.T) {
	dir := t.TempDir()
	s := Seed{
		SchemaVersion: SchemaVersion,
		ProposedPacks: []string{"house-policy"},
		HumanTicks:    HumanTicks{PacksConfirmed: true},
		Claim:         ClaimFence,
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), []byte(`{"packs":["house-policy"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("# Security\n\nHouse policy prose.\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, ".well-known"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".well-known", "security.txt"), []byte("Contact: security@example.com\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	latest := filepath.Join(cache, "latest_result.json")
	if err := os.WriteFile(latest, []byte(`{"failures":[]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := ConfirmProse(dir); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(latest); !os.IsNotExist(err) {
		t.Fatalf("latest_result.json must be invalidated after confirm-prose, err=%v", err)
	}
	phase, err := DerivePhase(dir, mustLoadSeed(t, dir))
	if err != nil {
		t.Fatal(err)
	}
	if phase != PhaseAwaitCheck {
		t.Fatalf("want AwaitCheck after prose, got %s", phase)
	}
}

func mustLoadSeed(t *testing.T, dir string) *Seed {
	t.Helper()
	s, err := Load(dir)
	if err != nil || s == nil {
		t.Fatalf("load: %v nil=%v", err, s == nil)
	}
	return s
}

func TestWrite_AtomicAndCorruptSeedHardError(t *testing.T) {
	dir := t.TempDir()
	if err := Write(dir, Seed{ProposedPacks: []string{"house-policy"}, Claim: ClaimFence}); err != nil {
		t.Fatal(err)
	}
	if _, err := Load(dir); err != nil {
		t.Fatal(err)
	}
	// Corrupt seed must hard-error on note/suggest — never silent overwrite.
	if err := os.WriteFile(SeedPath(dir), []byte("{not-json\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := NoteSet(dir, "hello"); err == nil {
		t.Fatal("corrupt seed: note must hard-error")
	}
	r, err := Suggest(Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := ApplySuggest(dir, r); err == nil {
		t.Fatal("corrupt seed: suggest must hard-error")
	}
}
