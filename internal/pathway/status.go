package pathway

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// NextAction is exactly one next verb + command for pathway status.
type NextAction struct {
	Verb string
	Cmd  string
	Note string // optional one-line context (hint / claim); not a second "action"
}

// Status derives the single next action from the guarded machine + filesystem.
func Status(repoRoot string) (NextAction, error) {
	snap, err := Project(repoRoot)
	if err != nil {
		return NextAction{}, err
	}
	return snap.Next, nil
}

// FormatStatus prints exactly one next action + command.
func FormatStatus(a NextAction) string {
	var b strings.Builder
	fmt.Fprintf(&b, "next: %s\n", a.Verb)
	fmt.Fprintf(&b, "run:  %s\n", a.Cmd)
	if strings.TrimSpace(a.Note) != "" {
		fmt.Fprintf(&b, "note: %s\n", a.Note)
	}
	return b.String()
}

// FormatSnapshot prints phase path + one next action (status UI for agents/technicals).
func FormatSnapshot(snap Snapshot) string {
	var b strings.Builder
	fmt.Fprintf(&b, "phase: %s\n", FormatParentPath(snap.Path))
	b.WriteString(FormatStatus(snap.Next))
	return b.String()
}

// FormatHumanStatus prints a plain-English next ask (no statechart path, no HPURL/RKG/OCC).
// Default surface for human / site recipes.
func FormatHumanStatus(snap Snapshot) string {
	ask := humanAsk(snap)
	why := humanWhy(snap)
	var b strings.Builder
	fmt.Fprintf(&b, "next ask: %s\n", ask)
	fmt.Fprintf(&b, "run:      %s\n", humanCmd(snap))
	if why != "" {
		fmt.Fprintf(&b, "why:      %s\n", why)
	}
	fmt.Fprintf(&b, "note:     %s\n", ClaimFence)
	return b.String()
}

func humanCmd(snap Snapshot) string {
	switch snap.Phase {
	case PhaseAwaitHPURLVerify, PhaseComplete:
		return "open proof/index.html"
	default:
		return snap.Next.Cmd
	}
}

func humanWhy(snap Snapshot) string {
	switch snap.Phase {
	case PhaseAwaitSuggest:
		return "Closed questions only — not a regulation pathway."
	case PhaseAwaitPackConfirm:
		return "Human confirms checklists; agents never stamp this."
	case PhaseAwaitActivate:
		return "Match .cyberready.json packs to the confirmed propose."
	case PhaseAwaitHealOrProse:
		if strings.Contains(snap.Next.Cmd, "research") {
			return "Allowlisted links + brief; research never changes check pass/fail."
		}
		return "Heal stubs, then write real product wording."
	case PhaseAwaitProseConfirm:
		if researchPacketNote(snap) {
			return "Cite-check drafts first; then confirm you own the wording."
		}
		return "Confirm you own the wording — then re-check."
	case PhaseAwaitCheck:
		if snap.GateID != "" {
			return "Fix the top finding, then re-check. Chat never greenlights."
		}
		return "Exit code is authoritative. Chat never greenlights."
	case PhaseAwaitShare:
		return "Build buyer questions + context pack for a human reviewer."
	case PhaseAwaitShareConfirm:
		return "Confirm you reviewed the buyer one-pager / questions."
	case PhaseAwaitAttest:
		if gitDirtyNote(snap.Next.Note) {
			return "Working tree has uncommitted changes — commit or attest with --allow-dirty."
		}
		return ClaimFence
	case PhaseAwaitHPURLVerify, PhaseComplete:
		return "Compare the bound hash from the local evidence pointer — still not certification."
	default:
		return sanitizeHumanNote(snap.Next.Note)
	}
}

func researchPacketNote(snap Snapshot) bool {
	return strings.Contains(snap.Next.Note, "cite-check")
}

func gitDirtyNote(note string) bool {
	return strings.Contains(note, "OCC") || strings.Contains(strings.ToLower(note), "dirty")
}

func sanitizeHumanNote(note string) string {
	note = strings.TrimSpace(note)
	if note == "" {
		return ""
	}
	lower := strings.ToLower(note)
	for _, bad := range []string{"hpurl", "rkg", "occ:", "await", "enum "} {
		if strings.Contains(lower, bad) {
			return ""
		}
	}
	return note
}

func humanAsk(snap Snapshot) string {
	switch snap.Phase {
	case PhaseAwaitSuggest:
		return "Answer a few closed questions so we can suggest checklists (not a regulation pathway)."
	case PhaseAwaitPackConfirm:
		return "Confirm the suggested checklists look right for this product (human only)."
	case PhaseAwaitActivate:
		return "Turn on those checklists in this repo (init --packs)."
	case PhaseAwaitHealOrProse:
		if strings.Contains(snap.Next.Cmd, "research") {
			return "Build a short research brief from official allowlisted links (optional fetch)."
		}
		return "Create stub docs, then replace stubs with real product wording."
	case PhaseAwaitProseConfirm:
		return "Confirm you own the wording in the house docs (human only)."
	case PhaseAwaitCheck:
		if snap.GateID != "" {
			return fmt.Sprintf("Fix the top open finding (%s), then re-check.", snap.GateID)
		}
		return "Run the local check on this tree."
	case PhaseAwaitShare:
		return "Share a review pack / buyer questions for a human reviewer."
	case PhaseAwaitShareConfirm:
		return "Confirm you reviewed the buyer one-pager / questions (human only)."
	case PhaseAwaitAttest:
		return "A human signs this tree with attest when ready (agents stop)."
	case PhaseAwaitHPURLVerify, PhaseComplete:
		return "Done — open the local proof page to compare the bound hash"
	default:
		return snap.Next.Verb
	}
}

func packsMatch(configured, proposed []string) bool {
	if len(configured) == 0 || len(proposed) == 0 {
		return false
	}
	// Confirmed propose must be a subset of configured (extends may add bases via Compose).
	set := map[string]struct{}{}
	for _, id := range configured {
		set[id] = struct{}{}
	}
	for _, id := range proposed {
		if _, ok := set[id]; !ok {
			return false
		}
	}
	return true
}

func anyMissing(repoRoot string, rels []string) bool {
	for _, rel := range rels {
		p := filepath.Join(repoRoot, filepath.FromSlash(rel))
		st, err := os.Stat(p)
		if err != nil || st.IsDir() {
			return true
		}
	}
	return false
}
