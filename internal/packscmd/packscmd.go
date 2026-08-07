package packscmd

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/afelin/cyberready/internal/packs"
	"github.com/afelin/cyberready/internal/tty"
)

// List prints embedded packs and watchlist summary.
func List() error {
	all, err := packs.LoadEmbedded()
	if err != nil {
		return err
	}
	fmt.Println(tty.C(tty.Bold+tty.Cyan, "Embedded regulation packs"))
	for _, p := range all {
		fmt.Printf("  %-22s %s  (%d rules) — %s\n", p.ID, p.Version, len(p.Rules), p.Name)
	}
	wl, err := packs.LoadWatchlist()
	if err != nil {
		return err
	}
	fmt.Printf("\nWatchlist v%d updated %s — %d informational entries\n", wl.Version, wl.Updated, len(wl.Entries))
	fmt.Println(tty.C(tty.Dim, wl.Note))
	return nil
}

// UpdateStub documents / optionally fetches a pack update channel.
// Without CYBERREADY_PACKS_URL it only prints instructions (offline-safe).
func UpdateStub() error {
	url := strings.TrimSpace(os.Getenv("CYBERREADY_PACKS_URL"))
	dest := strings.TrimSpace(os.Getenv("CYBERREADY_PACKS_DIR"))
	if dest == "" {
		dest = filepath.Join(".github", "cyberready", "packs")
	}
	if url == "" {
		fmt.Println(`packs update (P2 stub)

CyberReady embeds packs in the binary. To refresh without a new binary:

  1. Air-gap import:
       cyberready packs import ./path/to/packs-bundle

  2. Or set CYBERREADY_PACKS_DIR to a directory containing:
       cra-baseline/pack.json
       medtech-iec62304/pack.json
       _watchlist.json

  3. Optional online channel (when available):
       CYBERREADY_PACKS_URL=https://… cyberready packs update

Watchlist refreshes are informational only and never fail validate.
No signed CDN is required for P0/P1 demos.`)
		return nil
	}

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return fmt.Errorf("packs update fetch failed (offline?): %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("packs update HTTP %d", resp.StatusCode)
	}
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(dest, 0o755); err != nil {
		return err
	}
	out := filepath.Join(dest, "bundle.json")
	if err := os.WriteFile(out, data, 0o644); err != nil {
		return err
	}
	tty.PrintStatus("Packs update", true, "wrote "+out+" — extract pack.json files manually or use packs import")
	return nil
}

// ImportAirGap copies pack.json files from a local directory into CYBERREADY_PACKS_DIR / dest.
func ImportAirGap(src string) error {
	if src == "" {
		return fmt.Errorf("usage: cyberready packs import <directory>")
	}
	dest := strings.TrimSpace(os.Getenv("CYBERREADY_PACKS_DIR"))
	if dest == "" {
		dest = filepath.Join(".github", "cyberready", "packs")
	}
	if err := os.MkdirAll(dest, 0o755); err != nil {
		return err
	}
	entries, err := os.ReadDir(src)
	if err != nil {
		return err
	}
	copied := 0
	for _, e := range entries {
		name := e.Name()
		if name == "_watchlist.json" {
			in, err := os.ReadFile(filepath.Join(src, name))
			if err != nil {
				return err
			}
			if err := os.WriteFile(filepath.Join(dest, name), in, 0o644); err != nil {
				return err
			}
			copied++
			continue
		}
		if !e.IsDir() {
			continue
		}
		inPath := filepath.Join(src, name, "pack.json")
		data, err := os.ReadFile(inPath)
		if err != nil {
			continue
		}
		var probe map[string]any
		if json.Unmarshal(data, &probe) != nil {
			continue
		}
		outDir := filepath.Join(dest, name)
		if err := os.MkdirAll(outDir, 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(filepath.Join(outDir, "pack.json"), data, 0o644); err != nil {
			return err
		}
		copied++
	}
	tty.PrintStatus("Air-gap import", true, fmt.Sprintf("%d items → %s", copied, dest))
	fmt.Println("Set CYBERREADY_PACKS_DIR=" + dest + " to use imported packs.")
	return nil
}
