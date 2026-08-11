package sock_test

import (
	"encoding/json"
	"net"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/sock"
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

	info, err := os.Stat(sockPath)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm()&0o077 != 0 {
		t.Fatalf("sock should be private (0600), got %04o", info.Mode().Perm())
	}
}

func TestDefaultPathNotSharedTmp(t *testing.T) {
	t.Setenv("CURBPACK_SOCK", "")
	t.Setenv("XDG_RUNTIME_DIR", t.TempDir())
	p, err := sock.DefaultPath()
	if err != nil {
		t.Fatal(err)
	}
	if p == "/tmp/curbpack.sock" {
		t.Fatal("must not default to shared /tmp/curbpack.sock")
	}
	if !strings.Contains(p, "curbpack") {
		t.Fatalf("unexpected path %q", p)
	}
}

func TestExplainPacketIPC(t *testing.T) {
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "README.md"), "# x\n")
	mustWrite(t, filepath.Join(dir, ".curbpack.json"), "{\n  \"packs\": [\"house-policy\"],\n  \"version\": \"0.4.1\"\n}\n")

	sockPath := filepath.Join(dir, "cr-explain.sock")
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
	_ = conn.SetDeadline(time.Now().Add(10 * time.Second))

	enc := json.NewEncoder(conn)
	dec := json.NewDecoder(conn)
	if err := enc.Encode(map[string]any{"op": "explain_packet"}); err != nil {
		t.Fatal(err)
	}
	var resp sock.Response
	if err := dec.Decode(&resp); err != nil {
		t.Fatal(err)
	}
	if !resp.OK {
		t.Fatalf("explain_packet want ok: %#v", resp)
	}
	if len(resp.Packet) == 0 {
		t.Fatal("explain_packet missing explain_packet payload")
	}
	var pkt struct {
		Untrusted string `json:"untrusted_metadata"`
		Note      string `json:"note"`
	}
	if err := json.Unmarshal(resp.Packet, &pkt); err != nil {
		t.Fatalf("explain_packet not JSON object: %v\n%s", err, resp.Packet)
	}
	if !strings.Contains(pkt.Untrusted, "<untrusted_metadata>") || !strings.Contains(pkt.Untrusted, "</untrusted_metadata>") {
		t.Fatalf("packet must wrap agent body in untrusted_metadata tags, got %q", pkt.Untrusted)
	}
	if strings.Contains(pkt.Untrusted, "/Users/") || strings.Contains(pkt.Untrusted, "/home/") {
		t.Fatal("packet must refuse absolute home paths")
	}
	if strings.Contains(pkt.Untrusted, "BEGIN ") && strings.Contains(pkt.Untrusted, "PRIVATE KEY") {
		t.Fatal("packet must refuse PEM leakage")
	}
	if !strings.Contains(resp.Detail, "explain-packet.json") {
		t.Fatalf("detail should point at cache path, got %q", resp.Detail)
	}
}

func TestRefuseWorldWritableParent(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("unix sock")
	}
	dir := t.TempDir()
	bad := filepath.Join(dir, "world")
	if err := os.MkdirAll(bad, 0o777); err != nil {
		t.Fatal(err)
	}
	// Some filesystems ignore sticky/umask — force world-writable.
	_ = os.Chmod(bad, 0o777)
	sockPath := filepath.Join(bad, "curbpack.sock")
	err := sock.Serve(sockPath, dir)
	if err == nil {
		t.Fatal("expected refuse world-writable parent")
	}
	if !strings.Contains(err.Error(), "world-writable") {
		t.Fatalf("want world-writable error, got %v", err)
	}
}

func mustWrite(t *testing.T, path, body string) {
	t.Helper()
	_ = os.MkdirAll(filepath.Dir(path), 0o755)
	_ = os.WriteFile(path, []byte(body), 0o644)
}
