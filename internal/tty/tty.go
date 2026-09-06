package tty

import (
	"fmt"
	"os"
)

var IsTerminal bool

const (
	Reset   = "\033[0m"
	Bold    = "\033[1m"
	Dim     = "\033[2m"
	Red     = "\033[31m"
	Green   = "\033[32m"
	Yellow  = "\033[33m"
	Cyan    = "\033[36m"
	Magenta = "\033[35m"
	BGGreen = "\033[42m"
)

func init() {
	stat, _ := os.Stdout.Stat()
	IsTerminal = (stat.Mode() & os.ModeCharDevice) != 0
}

// C wraps text in ANSI color only when stdout is a TTY (avoids token pollution for agents).
func C(color, text string) string {
	if !IsTerminal {
		return text
	}
	return color + text + Reset
}

func PrintHeader(title string) {
	fmt.Printf("\n%s\n", C(Bold+Cyan, "=== "+title+" ==="))
}

func PrintStatus(step string, passed bool, details string) {
	if passed {
		fmt.Printf("[%s]  %-40s %s\n", C(Green, "✔"), step, C(Dim, "("+details+")"))
	} else {
		fmt.Printf("[%s]  %-40s %s\n", C(Red, "✘"), step, C(Red, details))
	}
}

// PrintNotStarted marks a gate that was not examined (target absent / scaffold / not started).
// Never use PrintStatus ok for unevaluated empty results — emit a not-started finding instead.
func PrintNotStarted(step string, details string) {
	fmt.Printf("[%s]  %-40s %s\n", C(Yellow, "○"), step, C(Dim, "("+details+")"))
}

// RenderCounts prints failed/evaluated/skipped tallies (no percent grade).
func RenderCounts(failed, evaluated, skipped int, gatesOpen bool) {
	color := Green
	if gatesOpen {
		color = Yellow
		if failed > 0 {
			color = Red
		}
	}
	state := "gates green"
	if gatesOpen {
		state = "gates open"
	}
	fmt.Printf("\n%s\n", C(Bold, "LOCAL GATE TALLY"))
	fmt.Printf("%s  failed=%d evaluated=%d skipped=%d\n", C(color, state), failed, evaluated, skipped)
}

// RenderThermometer is retained as a deprecated alias that prints counts derived
// from a legacy score (score ≈ 100 - 20*failed). Prefer RenderCounts.
func RenderThermometer(score int) {
	failed := 0
	if score < 100 {
		failed = (100 - score) / 20
		if failed == 0 && score < 100 {
			failed = 1
		}
	}
	RenderCounts(failed, 0, 0, score < 100)
}

// ScoreFromFailures maps failure count to a 0–100 readiness score.
func ScoreFromFailures(n int) int {
	score := 100 - (n * 20)
	if score < 0 {
		return 0
	}
	return score
}

// WarnCacheWrite prints a dim stderr warning when cache writes fail (gate pass/fail unchanged).
func WarnCacheWrite(msg string) {
	fmt.Fprintf(os.Stderr, "%s\n", C(Dim, "[cache] "+msg))
}

// WarnOCCParent prints a dim stderr note when OCC parent SHA is omitted (best-effort).
func WarnOCCParent(msg string) {
	fmt.Fprintf(os.Stderr, "%s\n", C(Dim, "[occ] "+msg))
}
