package sock_test

import (
	"encoding/json"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/afelin/cyberready/internal/sock"
)

func TestValidateDeltaIPC(t *testing.T) {
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "README.md"), "# x\n")

	sockPath := filepath.Join(dir, "cr.sock")
	go func() {
		_ = sock.Serve(sockPath, dir)
	}()

	deadline := time.Now().Add(3 * time.Second)
	var conn net.Conn
	var err error
	for time.Now().Before(deadline) {
		conn, err = net.Dial("unix", sockPath)
		if err == nil {
			break
		}
		time.Sleep(20 * time.Millisecond)
	}
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(5 * time.Second))

	enc := json.NewEncoder(conn)
	dec := json.NewDecoder(conn)
	if err := enc.Encode(map[string]any{"op": "validate_delta"}); err != nil {
		t.Fatal(err)
	}
	var resp sock.Response
	if err := dec.Decode(&resp); err != nil {
		t.Fatal(err)
	}
	if resp.Payload == nil && len(resp.Failures) == 0 && resp.OK {
		t.Fatalf("unexpected empty pass: %#v", resp)
	}
	if resp.Reason == "not_installed" {
		t.Fatal("server should not return not_installed")
	}
}

func mustWrite(t *testing.T, path, body string) {
	t.Helper()
	_ = os.MkdirAll(filepath.Dir(path), 0o755)
	_ = os.WriteFile(path, []byte(body), 0o644)
}
