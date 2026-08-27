package main

import (
	"os"
	"os/exec"
	"strings"
	"testing"
)

func TestMCPNoNetHTTP(t *testing.T) {
	out, err := exec.Command("go", "list", "-deps", "github.com/afelin/curbpack/cmd/curbpack-mcp").CombinedOutput()
	if err != nil {
		t.Fatalf("go list: %v\n%s", err, out)
	}
	for _, line := range strings.Split(string(out), "\n") {
		if strings.TrimSpace(line) == "net/http" {
			t.Fatal("curbpack-mcp must not link net/http (air-gap diligence)")
		}
	}
}

func TestMCPNoListeningSocketInSource(t *testing.T) {
	b, err := os.ReadFile("main.go")
	if err != nil {
		t.Fatal(err)
	}
	text := string(b)
	for _, bad := range []string{"Listen(", "ListenTCP", "ListenUDP", "http.Server", "net.Listen"} {
		if strings.Contains(text, bad) {
			t.Fatalf("MCP must not listen on a socket (%s found)", bad)
		}
	}
}
