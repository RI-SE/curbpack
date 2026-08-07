package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// File is the on-disk .cyberready.json shape.
type File struct {
	Packs   []string `json:"packs"`
	Hooks   bool     `json:"hooks,omitempty"`
	Version string   `json:"version,omitempty"`
	Claim   string   `json:"claim,omitempty"`
}

// Load reads .cyberready.json from repo root. Returns nil, nil if missing.
func Load(root string) (*File, error) {
	path := filepath.Join(root, ".cyberready.json")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var c File
	if err := json.Unmarshal(data, &c); err != nil {
		return nil, fmt.Errorf("parse .cyberready.json: %w", err)
	}
	return &c, nil
}

// Write creates or overwrites .cyberready.json.
func Write(root string, c File) error {
	if c.Claim == "" {
		c.Claim = "Prepares evidence for human review — not a conformity assessment."
	}
	b, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(root, ".cyberready.json"), append(b, '\n'), 0o644)
}

// ParsePacksFlag splits a comma-separated --packs value.
func ParsePacksFlag(s string) []string {
	parts := strings.Split(s, ",")
	var out []string
	seen := map[string]struct{}{}
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		if _, ok := seen[p]; ok {
			continue
		}
		seen[p] = struct{}{}
		out = append(out, p)
	}
	return out
}

// ResolvePackIDs returns CLI override, else config packs, else default house-policy (cold start).
func ResolvePackIDs(root string, cli []string) ([]string, error) {
	if len(cli) > 0 {
		return cli, nil
	}
	cfg, err := Load(root)
	if err != nil {
		return nil, err
	}
	if cfg != nil && len(cfg.Packs) > 0 {
		return cfg.Packs, nil
	}
	return []string{"house-policy"}, nil
}
