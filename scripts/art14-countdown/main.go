// Command art14-countdown bakes server-side Art 14 countdown text into site HTML.
package main

import (
	"fmt"
	"os"
	"regexp"

	"github.com/afelin/curbpack/internal/clock"
)

var countdownRE = regexp.MustCompile(`(<p id="art14-countdown"[^>]*>)([^<]*)(</p>)`)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: art14-countdown <file>...")
		os.Exit(2)
	}
	text := clock.FormatArt14Countdown(clock.DaysUntilUTC(clock.Art14ReportingStart))
	for _, path := range os.Args[1:] {
		b, err := os.ReadFile(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "read %s: %v\n", path, err)
			os.Exit(1)
		}
		s := string(b)
		if !countdownRE.MatchString(s) {
			fmt.Fprintf(os.Stderr, "no art14-countdown element in %s\n", path)
			os.Exit(1)
		}
		out := countdownRE.ReplaceAllString(s, "${1}"+text+"${3}")
		if err := os.WriteFile(path, []byte(out), 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "write %s: %v\n", path, err)
			os.Exit(1)
		}
	}
}
