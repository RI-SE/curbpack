// Command curbpack-mcp is a library-backed stdio MCP server for reference resolution.
// Read-only tools only. No confirm/attest/doc generation. CGO_ENABLED=0.
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"

	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/pathjail"
	"github.com/afelin/curbpack/internal/review"
)

const serverName = "curbpack-mcp"
const serverVersion = "0.6.0"

type rpcReq struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id,omitempty"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params,omitempty"`
}

type rpcResp struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id,omitempty"`
	Result  any             `json:"result,omitempty"`
	Error   *rpcErr         `json:"error,omitempty"`
}

type rpcErr struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

type toolCallParams struct {
	Name      string         `json:"name"`
	Arguments map[string]any `json:"arguments"`
}

// Process-scoped cache keyed (path,mtime,size) — memory only; persistence forbidden.
type cacheEntry struct {
	mtime int64
	size  int64
	rep   review.Report
}

var (
	cacheMu sync.Mutex
	cache   = map[string]cacheEntry{}
)

func main() {
	if err := serve(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintf(os.Stderr, "%s: %v\n", serverName, err)
		os.Exit(1)
	}
}

func serve(in io.Reader, out io.Writer) error {
	br := bufio.NewReader(in)
	enc := json.NewEncoder(out)
	for {
		line, err := br.ReadBytes('\n')
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		line = bytes.TrimSpace(line)
		if len(line) == 0 {
			continue
		}
		var req rpcReq
		if err := json.Unmarshal(line, &req); err != nil {
			_ = enc.Encode(rpcResp{JSONRPC: "2.0", Error: &rpcErr{Code: -32700, Message: "parse error"}})
			continue
		}
		resp := handle(req)
		if resp == nil {
			continue
		}
		if err := enc.Encode(resp); err != nil {
			return err
		}
	}
}

func handle(req rpcReq) *rpcResp {
	switch req.Method {
	case "initialize":
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"protocolVersion": "2024-11-05",
			"capabilities":    map[string]any{"tools": map[string]any{}},
			"serverInfo":      map[string]any{"name": serverName, "version": serverVersion},
			"instructions":    "Curbpack MCP resolves references offline. Never claim certification. Trust boundary = local repo; never expose to third parties.",
		}}
	case "notifications/initialized", "initialized":
		return nil
	case "tools/list":
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"tools": toolDefs()}}
	case "tools/call":
		var p toolCallParams
		if err := json.Unmarshal(req.Params, &p); err != nil {
			return &rpcResp{JSONRPC: "2.0", ID: req.ID, Error: &rpcErr{Code: -32602, Message: "invalid params"}}
		}
		text, err := callTool(p.Name, p.Arguments)
		if err != nil {
			return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
				"content": []map[string]any{{"type": "text", "text": err.Error()}},
				"isError": true,
			}}
		}
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"content": []map[string]any{{"type": "text", "text": text}},
		}}
	default:
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Error: &rpcErr{Code: -32601, Message: "method not found"}}
	}
}

func toolDefs() []map[string]any {
	return []map[string]any{
		{
			"name":        "resolve_references",
			"description": "Offline review of a review-pack or repo path (references resolve). Read-only.",
			"inputSchema": map[string]any{
				"type": "object",
				"properties": map[string]any{
					"path": map[string]any{"type": "string", "description": "Absolute or relative path to review-pack or repo"},
					"repo": map[string]any{"type": "boolean", "description": "When true, ReferencesOnly repo triage"},
				},
				"required": []string{"path"},
			},
		},
		{
			"name":        "check_citation_currency",
			"description": "Packs doctor citation currency (unverified/stale). Advisory; never gates check.",
			"inputSchema": map[string]any{"type": "object", "properties": map[string]any{}},
		},
		{
			"name":        "record_digest",
			"description": "Return record_digest for a review-pack path.",
			"inputSchema": map[string]any{
				"type":       "object",
				"properties": map[string]any{"path": map[string]any{"type": "string"}},
				"required":   []string{"path"},
			},
		},
	}
}

func callTool(name string, args map[string]any) (string, error) {
	switch name {
	case "resolve_references":
		path, _ := args["path"].(string)
		repo, _ := args["repo"].(bool)
		rep, err := runReviewCached(path, repo)
		if err != nil {
			return "", err
		}
		b, err := json.MarshalIndent(rep, "", "  ")
		return string(b), err
	case "check_citation_currency":
		f, err := packs.DoctorPacks()
		if err != nil {
			return "", err
		}
		b, err := json.MarshalIndent(f, "", "  ")
		return string(b), err
	case "record_digest":
		path, _ := args["path"].(string)
		rep, err := runReviewCached(path, false)
		if err != nil {
			return "", err
		}
		return rep.RecordDigest, nil
	default:
		return "", fmt.Errorf("unknown tool %q", name)
	}
}

func runReviewCached(path string, repoMode bool) (review.Report, error) {
	path = filepath.Clean(path)
	if path == "" || path == "." {
		return review.Report{}, fmt.Errorf("path required")
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		return review.Report{}, err
	}
	st, err := os.Lstat(abs)
	if err != nil {
		return review.Report{}, err
	}
	if st.Mode()&os.ModeSymlink != 0 {
		return review.Report{}, fmt.Errorf("refusing symlink path")
	}
	key := abs
	mtime := st.ModTime().UnixNano()
	size := st.Size()
	cacheMu.Lock()
	if e, ok := cache[key]; ok && e.mtime == mtime && e.size == size {
		rep := e.rep
		cacheMu.Unlock()
		return rep, nil
	}
	cacheMu.Unlock()

	opts := review.Options{
		BundleRoot: abs,
		Writer:     io.Discard,
		JSONOut:    true,
	}
	if repoMode {
		opts.ReferencesOnly = true
		if err := pathjail.ValidateRel("."); err != nil {
			return review.Report{}, err
		}
	}
	rep, err := review.Run(opts)
	if err != nil {
		return review.Report{}, err
	}
	cacheMu.Lock()
	cache[key] = cacheEntry{mtime: mtime, size: size, rep: rep}
	cacheMu.Unlock()
	return rep, nil
}
