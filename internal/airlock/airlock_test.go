package airlock

import (
	"strings"
	"testing"
)

func TestPacketLooksAirlockedClean(t *testing.T) {
	if err := PacketLooksAirlocked([]byte(`{"detail":"relative/path.md","ok":true}`)); err != nil {
		t.Fatalf("clean packet: %v", err)
	}
}

func TestPacketLooksAirlockedHomePath(t *testing.T) {
	err := PacketLooksAirlocked([]byte(`leak /Users/alice/secret`))
	if err == nil || !strings.Contains(err.Error(), "home") {
		t.Fatalf("want home-path error, got %v", err)
	}
}

func TestPacketLooksAirlockedPEM(t *testing.T) {
	pem := "-----BEGIN CERTIFICATE-----\n" + strings.Repeat("A", 40) + "\n-----END CERTIFICATE-----"
	err := PacketLooksAirlocked([]byte(pem))
	if err == nil || !strings.Contains(err.Error(), "PEM") {
		t.Fatalf("want PEM error, got %v", err)
	}
}
