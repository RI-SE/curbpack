package cli_test

import (
	"github.com/afelin/curbpack/internal/cli"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestPrebetaShareAvoidsPrivateFolderAndSecretScaffolds(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "PRIVATE_FOLDER_SENTINEL")
	if err := os.Mkdir(dir, 0755); err != nil {
		t.Fatal(err)
	}
	initScanGit(t, dir)
	old, _ := os.Getwd()
	if err := os.Chdir(dir); err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(old)
	// A declared package name is intentional product metadata, unlike its local folder.
	os.WriteFile("package.json", []byte(`{"name":"example-product","dependencies":{"lodash":"4.17.21"}}`), 0600)
	capture(t, func() {
		err := cli.Run([]string{"share", "--bundle"})
		if err != nil && cli.ExitCode(err) != cli.ExitGates {
			t.Fatal(err)
		}
	})
	for _, name := range []string{".env", ".env.local", "credentials.json", "service-account.json", "id_rsa"} {
		if _, err := os.Stat(name); !os.IsNotExist(err) {
			t.Errorf("share created scan-only target %s", name)
		}
	}
	for _, name := range []string{"buyer-onepager.html", "evidence-bundle.html", "04-sbom.cdx.json"} {
		raw, err := os.ReadFile(filepath.Join("review-pack", name))
		if err != nil {
			t.Fatal(err)
		}
		if strings.Contains(string(raw), "PRIVATE_FOLDER_SENTINEL") {
			t.Errorf("local folder exported in %s", name)
		}
		if strings.HasSuffix(name, "html") {
			for _, bad := range []string{"Open <code>proof/index.html</code>", "Open proof/index.html locally", "(no commit)"} {
				if strings.Contains(string(raw), bad) {
					t.Errorf("dead end %q in %s", bad, name)
				}
			}
			for _, want := range []string{"What to do next", "Not included", "curbpack review"} {
				if !strings.Contains(string(raw), want) {
					t.Errorf("missing recipient guidance %q in %s", want, name)
				}
			}
		}
	}
}
func TestPrebetaAskGreenHasNoFailureAlert(t *testing.T) {
	p := filepath.Join(t.TempDir(), "green.json")
	os.WriteFile(p, []byte(`{"outcome":"pass","evaluated_rules":15,"failures":[]}`), 0600)
	out, _ := capture(t, func() {
		if err := cli.Run([]string{"ask", p, "--propose"}); err != nil {
			t.Fatal(err)
		}
	})
	if strings.Contains(out, "GATE FAILURE") || !strings.Contains(out, "No findings") {
		t.Fatalf("misleading green response: %s", out)
	}
}
