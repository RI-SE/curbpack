package contract_test

import (
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"testing"
)

// Stable sock ops — must match docs/stable-contracts.md and internal/sock/sock.go.
var requiredSockOps = []string{
	"validate_delta",
	"get_latest_failure",
	"graph_summary",
	"explain_packet",
}

func stableContractsRoot(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "../.."))
}

func TestStableSockOpsDocumented(t *testing.T) {
	root := stableContractsRoot(t)
	sockSrc, err := os.ReadFile(filepath.Join(root, "internal/sock/sock.go"))
	if err != nil {
		t.Fatal(err)
	}
	docs, err := os.ReadFile(filepath.Join(root, "docs/stable-contracts.md"))
	if err != nil {
		t.Fatal(err)
	}
	docStr := string(docs)
	src := string(sockSrc)
	if !strings.Contains(src, "ops=validate_delta,get_latest_failure,graph_summary,explain_packet") {
		t.Fatal("sock listen banner missing four ops")
	}
	caseRE := regexp.MustCompile(`(?m)^\s*case "([^"]+)":`)
	for _, m := range caseRE.FindAllStringSubmatch(src, -1) {
		op := m[1]
		if !strings.Contains(docStr, op) {
			t.Fatalf("sock op %q missing from docs/stable-contracts.md", op)
		}
	}
	for _, op := range requiredSockOps {
		if !strings.Contains(src, `case "`+op+`"`) {
			t.Fatalf("missing sock case %q", op)
		}
		if !strings.Contains(docStr, op) {
			t.Fatalf("required op %q missing from docs/stable-contracts.md", op)
		}
	}
}

func TestExplainConsumerContractFilePresent(t *testing.T) {
	root := stableContractsRoot(t)
	path := filepath.Join(root, "internal/contract/explain_coreward_consumer_test.go")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("explain consumer contract test missing: %v", err)
	}
}
