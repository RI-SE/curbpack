// Package sockclient is a thin Unix socket client for optional Coreward IPC.
package sockclient

import (
	"bufio"
	"bytes"
	"encoding/json"
	"io"
	"net"
	"time"
)

// Op sends a JSON request to a Unix domain socket and returns the response line.
func Op(sockPath, op string, payload any) (string, error) {
	conn, err := net.DialTimeout("unix", sockPath, 2*time.Second)
	if err != nil {
		return "", err
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(60 * time.Second))
	req := map[string]any{"op": op}
	if payload != nil {
		req["payload"] = payload
	}
	b, _ := json.Marshal(req)
	if _, err := conn.Write(append(b, '\n')); err != nil {
		return "", err
	}
	resp, err := bufio.NewReader(conn).ReadBytes('\n')
	if err != nil && err != io.EOF {
		return "", err
	}
	return string(bytes.TrimSpace(resp)), nil
}
