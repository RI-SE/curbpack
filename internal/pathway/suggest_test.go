package pathway

import (
	"reflect"
	"testing"
)

func TestSuggest_ClosedWorldMap(t *testing.T) {
	t.Parallel()
	cases := []struct {
		name  string
		in    Answers
		packs []string
		hint  string
	}{
		{
			name:  "default hygiene house-first",
			in:    Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"},
			packs: []string{"house-policy"},
		},
		{
			name:  "hygiene ignores eu-docs",
			in:    Answers{Product: "hygiene", EuDocs: "yes", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"},
			packs: []string{"house-policy"},
		},
		{
			name:  "shipping without eu-docs",
			in:    Answers{Product: "shipping", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"},
			packs: []string{"house-policy"},
		},
		{
			name:  "shipping plus eu-docs",
			in:    Answers{Product: "shipping", EuDocs: "yes", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"},
			packs: []string{"house-policy", "cra-baseline"},
		},
		{
			name:  "medtech wins",
			in:    Answers{Product: "shipping", EuDocs: "yes", Medtech: "yes", Sector: "none", HouseFirst: "yes", CeContext: "none"},
			packs: []string{"medtech-iec62304"},
		},
		{
			name:  "sector other forces house + hint",
			in:    Answers{Product: "shipping", EuDocs: "yes", Medtech: "yes", Sector: "other", HouseFirst: "yes", CeContext: "none"},
			packs: []string{"house-policy"},
			hint:  "write-your-own-pack",
		},
		{
			name:  "ce_context never changes packs",
			in:    Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "in_procedure"},
			packs: []string{"house-policy"},
		},
		{
			name:  "house-first no still hygiene → house",
			in:    Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "no", CeContext: "none"},
			packs: []string{"house-policy"},
		},
	}
	for _, tc := range cases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			got, err := Suggest(tc.in)
			if err != nil {
				t.Fatalf("Suggest: %v", err)
			}
			if !reflect.DeepEqual(got.ProposedPacks, tc.packs) {
				t.Fatalf("packs=%v want %v", got.ProposedPacks, tc.packs)
			}
			if got.NextHint != tc.hint {
				t.Fatalf("hint=%q want %q", got.NextHint, tc.hint)
			}
		})
	}
}

func TestSuggest_RejectsUnknownEnum(t *testing.T) {
	t.Parallel()
	_, err := Suggest(Answers{Product: "dora", EuDocs: "no", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"})
	if err == nil {
		t.Fatal("expected enum error")
	}
	_, err = Suggest(Answers{Product: "hygiene", EuDocs: "maybe", Medtech: "no", Sector: "none", HouseFirst: "yes", CeContext: "none"})
	if err == nil {
		t.Fatal("expected eu-docs enum error")
	}
	_, err = Suggest(Answers{Product: "hygiene", EuDocs: "no", Medtech: "no", Sector: "finance", HouseFirst: "yes", CeContext: "none"})
	if err == nil {
		t.Fatal("expected sector enum error")
	}
}

func TestIntersectKnown_DropsUnknown(t *testing.T) {
	t.Parallel()
	known := map[string]struct{}{"house-policy": {}, "cra-baseline": {}}
	got := IntersectKnown([]string{"house-policy", "dora-pack", "cra-baseline"}, known)
	want := []string{"house-policy", "cra-baseline"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}
