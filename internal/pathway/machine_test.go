package pathway

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestGuard_IllegalConfirmOrder(t *testing.T) {
	dir := t.TempDir()
	// No seed → confirm-packs illegal
	if _, err := Guard(dir, EventConfirmPacks); !errors.Is(err, ErrUsage) {
		t.Fatalf("want usage refuse, got %v", err)
	}
	r, err := Suggest(Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := ApplySuggest(dir, r); err != nil {
		t.Fatal(err)
	}
	// Packs not confirmed → confirm-prose / confirm-share illegal
	if _, err := Guard(dir, EventConfirmProse); !errors.Is(err, ErrUsage) {
		t.Fatalf("confirm-prose before packs: %v", err)
	}
	if _, err := Guard(dir, EventConfirmShare); !errors.Is(err, ErrUsage) {
		t.Fatalf("confirm-share before packs: %v", err)
	}
	if _, err := Guard(dir, EventConfirmPacks); err != nil {
		t.Fatalf("confirm-packs should allow: %v", err)
	}
	if _, err := ConfirmPacks(dir); err != nil {
		t.Fatal(err)
	}
	// After packs, confirm-packs again illegal (phase advanced)
	if _, err := Guard(dir, EventConfirmPacks); !errors.Is(err, ErrUsage) {
		t.Fatalf("re-confirm-packs: %v", err)
	}
}

func TestStatus_GoldenPhases(t *testing.T) {
	dir := t.TempDir()
	mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})

	cases := []struct {
		name      string
		setup     func(t *testing.T)
		wantVerb  string
		wantPhase Phase
	}{
		{
			name:      "no-seed",
			setup:     func(t *testing.T) {},
			wantVerb:  "suggest packs",
			wantPhase: PhaseAwaitSuggest,
		},
		{
			name: "await-pack-confirm",
			setup: func(t *testing.T) {
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					Claim:         ClaimFence,
				})
			},
			wantVerb:  "confirm packs (human)",
			wantPhase: PhaseAwaitPackConfirm,
		},
		{
			name: "await-activate",
			setup: func(t *testing.T) {
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true},
					Claim:         ClaimFence,
				})
				// mismatch packs → activate
				mustWriteCyberreadyJSON(t, dir, []string{"cra-baseline"})
			},
			wantVerb:  "activate packs",
			wantPhase: PhaseAwaitActivate,
		},
		{
			name: "await-heal",
			setup: func(t *testing.T) {
				mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true},
					Claim:         ClaimFence,
				})
			},
			wantVerb:  "build research packet",
			wantPhase: PhaseAwaitHealOrProse,
		},
		{
			name: "await-prose-confirm",
			setup: func(t *testing.T) {
				mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})
				writeHouseDocs(t, dir)
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true},
					Claim:         ClaimFence,
				})
			},
			wantVerb:  "confirm prose (human)",
			wantPhase: PhaseAwaitProseConfirm,
		},
		{
			name: "await-check-no-result",
			setup: func(t *testing.T) {
				mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})
				writeHouseDocs(t, dir)
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true, ProseOwned: true},
					Claim:         ClaimFence,
				})
			},
			wantVerb:  "run check",
			wantPhase: PhaseAwaitCheck,
		},
		{
			name: "await-check-red-gate",
			setup: func(t *testing.T) {
				mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})
				writeHouseDocs(t, dir)
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true, ProseOwned: true},
					Claim:         ClaimFence,
				})
				writeLatestFailure(t, dir, "HOUSE-SECURITY-MD", false)
			},
			wantVerb:  "heal then propose",
			wantPhase: PhaseAwaitCheck,
		},
		{
			name: "await-share",
			setup: func(t *testing.T) {
				mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})
				writeHouseDocs(t, dir)
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true, ProseOwned: true},
					Claim:         ClaimFence,
				})
				writeLatestFailure(t, dir, "", true)
			},
			wantVerb:  "share review pack",
			wantPhase: PhaseAwaitShare,
		},
		{
			name: "await-attest",
			setup: func(t *testing.T) {
				mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})
				writeHouseDocs(t, dir)
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true, ProseOwned: true, ShareReviewed: true},
					Claim:         ClaimFence,
				})
				writeLatestFailure(t, dir, "", true)
				cache := filepath.Join(dir, ".github", "curbpack", "cache")
				_ = os.MkdirAll(cache, 0o755)
				_ = os.WriteFile(filepath.Join(cache, "buyer-questions.md"), []byte("# q\n"), 0o644)
			},
			wantVerb:  "human attest (agents stop)",
			wantPhase: PhaseAwaitAttest,
		},
		{
			name: "await-hpurl",
			setup: func(t *testing.T) {
				mustWriteCyberreadyJSON(t, dir, []string{"house-policy"})
				writeHouseDocs(t, dir)
				writeSeed(t, dir, Seed{
					ProposedPacks: []string{"house-policy"},
					HumanTicks:    HumanTicks{PacksConfirmed: true, ProseOwned: true, ShareReviewed: true},
					Claim:         ClaimFence,
				})
				writeLatestFailure(t, dir, "", true)
				ev := filepath.Join(dir, ".github", "curbpack", "evidence")
				_ = os.MkdirAll(ev, 0o755)
				_ = os.WriteFile(filepath.Join(ev, "hpurl-pointer.json"), []byte(`{"state_hash":"abc"}\n`), 0o644)
			},
			wantVerb:  "verify HPURL (human)",
			wantPhase: PhaseAwaitHPURLVerify,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			// Reset dir contents lightly by removing seed/cache between cases.
			_ = os.RemoveAll(filepath.Join(dir, ".github", "curbpack", "cache"))
			_ = os.RemoveAll(filepath.Join(dir, ".github", "curbpack", "evidence"))
			tc.setup(t)
			snap, err := Project(dir)
			if err != nil {
				t.Fatal(err)
			}
			if snap.Phase != tc.wantPhase {
				t.Fatalf("phase=%s want %s", snap.Phase, tc.wantPhase)
			}
			if snap.Next.Verb != tc.wantVerb {
				t.Fatalf("verb=%q want %q; snap=%+v", snap.Next.Verb, tc.wantVerb, snap)
			}
			formatted := FormatSnapshot(snap)
			if strings.Count(formatted, "next:") != 1 || strings.Count(formatted, "run:") != 1 {
				t.Fatalf("want one next+run, got %q", formatted)
			}
			if !strings.Contains(formatted, "Root / Pathway /") {
				t.Fatalf("missing parent path: %q", formatted)
			}
			if tc.wantPhase == PhaseAwaitCheck && tc.wantVerb == "heal then propose" {
				if snap.GateID != "HOUSE-SECURITY-MD" {
					t.Fatalf("gate_id=%q", snap.GateID)
				}
			}
		})
	}
}

func TestParentStatePath(t *testing.T) {
	p := ParentStatePath(PhaseAwaitCheck)
	if FormatParentPath(p) != "Root / Pathway / AwaitCheck" {
		t.Fatalf("%v", p)
	}
}

func writeSeed(t *testing.T, dir string, s Seed) {
	t.Helper()
	s.SchemaVersion = SchemaVersion
	if s.Claim == "" {
		s.Claim = ClaimFence
	}
	if err := Write(dir, s); err != nil {
		t.Fatal(err)
	}
}

func mustWriteCyberreadyJSON(t *testing.T, dir string, packs []string) {
	t.Helper()
	b, _ := json.Marshal(map[string]any{"packs": packs})
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), append(b, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

func writeHouseDocs(t *testing.T, dir string) {
	t.Helper()
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("# Security\n\nHouse policy prose.\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, ".well-known"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".well-known", "security.txt"), []byte("Contact: security@example.com\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

func writeLatestFailure(t *testing.T, dir, gateID string, green bool) {
	t.Helper()
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	var failures []map[string]string
	if !green && gateID != "" {
		failures = []map[string]string{{"gate_id": gateID}}
	}
	payload := map[string]any{"schema_version": "1", "failures": failures}
	b, _ := json.Marshal(payload)
	if err := os.WriteFile(filepath.Join(cache, "latest_failure.json"), append(b, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(cache, "latest_result.json"), append(b, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
