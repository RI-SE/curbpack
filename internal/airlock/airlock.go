// Package airlock checks emitted bytes for absolute homes / PEM blobs without heavier deps.
package airlock

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var (
	homePathRE = regexp.MustCompile(`(?i)(/Users/[^/\s]+|/home/[^/\s]+|/mnt/[a-z]/Users/[^/\s]+|C:\\Users\\[^\\\s]+)`)
	pemBlobRE  = regexp.MustCompile(`-----BEGIN [A-Z0-9 ]+-----[\s\S]{20,}?-----END [A-Z0-9 ]+-----`)
)

// PacketLooksAirlocked reports whether packet bytes avoid absolute homes / PEM blobs.
func PacketLooksAirlocked(data []byte) error {
	if pemBlobRE.Match(data) {
		return fmt.Errorf("explain-packet contains PEM-looking blob")
	}
	if homePathRE.Match(data) {
		return fmt.Errorf("explain-packet contains absolute home path")
	}
	if home, err := os.UserHomeDir(); err == nil {
		home = strings.TrimSpace(home)
		if usableHome(home) {
			if bytes.Contains(data, []byte(home)) {
				return fmt.Errorf("explain-packet contains user home directory path")
			}
			if slash := filepath.ToSlash(home); slash != home && bytes.Contains(data, []byte(slash)) {
				return fmt.Errorf("explain-packet contains user home directory path")
			}
		}
	}
	return nil
}

func usableHome(home string) bool {
	home = strings.TrimSpace(home)
	if home == "" || home == "/" || home == `C:\` || home == `C:/` {
		return false
	}
	return true
}
