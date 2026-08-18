package pathway

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/research"
)

// Phase is the pathway parent-path leaf (one shared vocabulary across seed / status / IR / ContextPack).
type Phase string

const (
	PhaseAwaitSuggest      Phase = "AwaitSuggest"
	PhaseAwaitPackConfirm  Phase = "AwaitPackConfirm"
	PhaseAwaitActivate     Phase = "AwaitActivate"
	PhaseAwaitHealOrProse  Phase = "AwaitHealOrProse"
	PhaseAwaitProseConfirm Phase = "AwaitProseConfirm"
	PhaseAwaitCheck        Phase = "AwaitCheck"
	PhaseAwaitShare        Phase = "AwaitShare"
	PhaseAwaitShareConfirm Phase = "AwaitShareConfirm"
	PhaseAwaitAttest       Phase = "AwaitAttest"
	PhaseAwaitHPURLVerify  Phase = "AwaitHPURLVerify"
	PhaseComplete          Phase = "Complete"
)

// Event is a pathway transition that mutates seed (human confirms) or reseeds (suggest).
type Event string

const (
	EventSuggest      Event = "suggest"
	EventConfirmPacks Event = "confirm-packs"
	EventConfirmProse Event = "confirm-prose"
	EventConfirmShare Event = "confirm-share"
)

// ErrUsage marks illegal transition / closed-world usage refuses (CLI → exit 2).
var ErrUsage = errors.New("pathway usage")

// UsageError wraps a usage message; callers check with errors.Is(err, ErrUsage).
type UsageError struct {
	Msg string
}

func (e *UsageError) Error() string { return e.Msg }
func (e *UsageError) Unwrap() error { return ErrUsage }

func usagef(format string, args ...any) error {
	return &UsageError{Msg: fmt.Sprintf(format, args...)}
}

// ParentStatePath is the canonical IR / dual-rep path for a phase.
func ParentStatePath(phase Phase) []string {
	return []string{"Root", "Pathway", string(phase)}
}

// FormatParentPath joins path segments for display.
func FormatParentPath(path []string) string {
	return strings.Join(path, " / ")
}

// Snapshot is machine projection: phase + one next action (+ optional gate_id).
type Snapshot struct {
	Phase  Phase
	Next   NextAction
	GateID string // top failure gate_id when red; never invented
	Path   []string
}

// DerivePhase projects seed + filesystem into one phase (pure; no writes).
func DerivePhase(repoRoot string, s *Seed) (Phase, error) {
	if s == nil {
		return PhaseAwaitSuggest, nil
	}
	if !s.HumanTicks.PacksConfirmed {
		return PhaseAwaitPackConfirm, nil
	}
	cfgPacks, hasCfg := ConfiguredPacks(repoRoot)
	if !hasCfg || !packsMatch(cfgPacks, s.ProposedPacks) {
		return PhaseAwaitActivate, nil
	}
	if !s.HumanTicks.ProseOwned {
		paths, err := ProsePaths(s.ProposedPacks)
		if err != nil {
			return "", err
		}
		if anyMissing(repoRoot, paths) {
			return PhaseAwaitHealOrProse, nil
		}
		return PhaseAwaitProseConfirm, nil
	}
	green, haveCheck := LastCheckGreen(repoRoot)
	if !haveCheck || !green {
		return PhaseAwaitCheck, nil
	}
	if !s.HumanTicks.ShareReviewed {
		if !shareArtifactsPresent(repoRoot) {
			return PhaseAwaitShare, nil
		}
		return PhaseAwaitShareConfirm, nil
	}
	if !hpurlPointerPresent(repoRoot) {
		return PhaseAwaitAttest, nil
	}
	return PhaseAwaitHPURLVerify, nil
}

// Allow reports whether event is legal from phase (suggest always resets).
func Allow(phase Phase, event Event) bool {
	switch event {
	case EventSuggest:
		return true
	case EventConfirmPacks:
		return phase == PhaseAwaitPackConfirm
	case EventConfirmProse:
		return phase == PhaseAwaitProseConfirm
	case EventConfirmShare:
		return phase == PhaseAwaitShareConfirm
	default:
		return false
	}
}

// Guard refuses illegal transitions with ErrUsage.
func Guard(repoRoot string, event Event) (Phase, error) {
	s, err := Load(repoRoot)
	if err != nil {
		return "", err
	}
	phase, err := DerivePhase(repoRoot, s)
	if err != nil {
		return "", err
	}
	if !Allow(phase, event) {
		return phase, usagef("pathway: illegal transition %s from phase %s (run: curbpack pathway status)", event, phase)
	}
	return phase, nil
}

// Project builds Status snapshot (one next verb) from machine + filesystem.
func Project(repoRoot string) (Snapshot, error) {
	s, err := Load(repoRoot)
	if err != nil {
		return Snapshot{}, err
	}
	phase, err := DerivePhase(repoRoot, s)
	if err != nil {
		return Snapshot{}, err
	}
	snap := Snapshot{Phase: phase, Path: ParentStatePath(phase)}
	switch phase {
	case PhaseAwaitSuggest:
		snap.Next = NextAction{
			Verb: "suggest packs",
			Cmd:  "curbpack pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes",
			Note: "enum seed only — see docs/getting-started/pathway.md",
		}
	case PhaseAwaitPackConfirm:
		packsCSV := strings.Join(s.ProposedPacks, ",")
		note := "proposed: " + packsCSV
		if s.NextHint != "" {
			note += "; next_hint=" + s.NextHint
		}
		snap.Next = NextAction{
			Verb: "confirm packs (human)",
			Cmd:  "curbpack pathway confirm-packs",
			Note: note,
		}
	case PhaseAwaitActivate:
		note := "or edit .curbpack.json packs to match confirmed propose"
		if !policyGraphPresent(repoRoot) {
			note += "; optional: curbpack packs export-graph"
		}
		snap.Next = NextAction{
			Verb: "activate packs",
			Cmd:  "curbpack init --packs " + strings.Join(s.ProposedPacks, ","),
			Note: note,
		}
	case PhaseAwaitHealOrProse:
		if !research.PacketPresent(repoRoot) {
			snap.Next = NextAction{
				Verb: "build research packet",
				Cmd:  "curbpack research",
				Note: "allowlisted sources + human brief; optional --fetch; then check --heal — research never gates check",
			}
		} else {
			snap.Next = NextAction{
				Verb: "heal stubs",
				Cmd:  "curbpack check --heal",
				Note: "then edit real prose from research-brief.md; cite-or-refuse; RKG / form-hints",
			}
		}
	case PhaseAwaitProseConfirm:
		snap.Next = NextAction{
			Verb: "confirm prose (human)",
			Cmd:  "curbpack pathway confirm-prose",
			Note: "cite-check + every prose path independent; stub-only / ungrounded claims refuse",
		}
	case PhaseAwaitCheck:
		gateID := TopGateID(repoRoot)
		snap.GateID = gateID
		if gateID != "" {
			snap.Next = NextAction{
				Verb: "heal then propose",
				Cmd:  "curbpack check --heal",
				Note: fmt.Sprintf("top gate_id=%s; then curbpack research --gate-id=%s (optional) + ask … --propose", gateID, gateID),
			}
		} else {
			snap.Next = NextAction{
				Verb: "run check",
				Cmd:  "curbpack check",
				Note: "red → check --heal + ask --propose; chat never greenlights",
			}
		}
	case PhaseAwaitShare:
		snap.Next = NextAction{
			Verb: "share review pack",
			Cmd:  "curbpack share",
			Note: "then human confirm-share",
		}
	case PhaseAwaitShareConfirm:
		snap.Next = NextAction{
			Verb: "confirm share (human)",
			Cmd:  "curbpack pathway confirm-share",
			Note: "review buyer-questions / one-pager",
		}
	case PhaseAwaitAttest:
		note := ClaimFence
		if gitutil.IsDirty(repoRoot) {
			note = "OCC: working tree dirty — commit or curbpack attest --allow-dirty; " + ClaimFence
		}
		snap.Next = NextAction{
			Verb: "human attest (agents stop)",
			Cmd:  "curbpack attest",
			Note: note,
		}
	case PhaseAwaitHPURLVerify, PhaseComplete:
		snap.Next = NextAction{
			Verb: "verify HPURL (human)",
			Cmd:  "open proof/index.html",
			Note: "paste state_hash from evidence pointer; client-side h= compare — not certification",
		}
	default:
		snap.Next = NextAction{
			Verb: "suggest packs",
			Cmd:  "curbpack pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes",
		}
	}
	return snap, nil
}

// TopGateID reads the first failure gate_id from latest_failure.json (never invents).
func TopGateID(repoRoot string) string {
	path := filepath.Join(repoRoot, ".github", "curbpack", "cache", "latest_failure.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	var payload struct {
		Failures []struct {
			GateID string `json:"gate_id"`
		} `json:"failures"`
	}
	if err := json.Unmarshal(data, &payload); err != nil {
		return ""
	}
	for _, f := range payload.Failures {
		id := strings.TrimSpace(f.GateID)
		if id != "" {
			return id
		}
	}
	return ""
}

func hpurlPointerPresent(repoRoot string) bool {
	p := filepath.Join(repoRoot, ".github", "curbpack", "evidence", "hpurl-pointer.json")
	st, err := os.Stat(p)
	return err == nil && !st.IsDir()
}

func policyGraphPresent(repoRoot string) bool {
	p := filepath.Join(repoRoot, ".github", "curbpack", "graph", "policy-graph.json")
	st, err := os.Stat(p)
	return err == nil && !st.IsDir()
}
