package doctor

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/githook"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/paths"
	"github.com/afelin/curbpack/internal/platform"
	"github.com/afelin/curbpack/internal/tty"
)

const Claim = "Prepares evidence for human review — not a conformity assessment."

// InstrumentPanelCovenant is the always-on honesty line for doctor / instrument surfaces.
const InstrumentPanelCovenant = "instrument panel · not a security program · not conformity assessment"

// Options controls doctor checks.
type Options struct {
	RepoRoot string // optional; empty = discover from cwd
	Version  string
	Repair   bool // local PATH/alias re-assert only — never downloads
}

// ExitMissingBinary is returned when --repair cannot find the binary (print install hint).
const ExitMissingBinary = 2

// ErrMissingBinary signals CLI should exit 2 with install hint.
type ErrMissingBinary struct {
	Hint string
}

func (e *ErrMissingBinary) Error() string {
	return "curbpack binary missing — reinstall: " + e.Hint
}

// Run prints environment confidence checks. Always exits 0 from CLI unless fatal I/O or --repair missing binary.
func Run(opts Options) error {
	tty.PrintHeader("CURBPACK DOCTOR")
	fmt.Printf("%s\n", tty.C(tty.Dim, Claim))
	fmt.Printf("%s\n\n", tty.C(tty.Dim, InstrumentPanelCovenant))

	if opts.Repair {
		return runRepair(opts)
	}

	ok := true
	printCheck := func(name string, passed bool, detail string) {
		tty.PrintStatus(name, passed, detail)
		if !passed {
			ok = false
		}
	}

	printCheck("binary", true, fmt.Sprintf("curbpack %s (%s/%s)", opts.Version, runtime.GOOS, runtime.GOARCH))
	printCheck("Go toolchain", true, "not required for released binaries (stdlib build only)")

	runInstallHealth(printCheck, opts.Version)

	if _, err := exec.LookPath("git"); err != nil {
		printCheck("git on PATH", false, "git not found — required for check/demo/attest — see docs/getting-started/troubleshooting.md")
	} else {
		out, _ := exec.Command("git", "version").Output()
		printCheck("git on PATH", true, strings.TrimSpace(string(out)))
	}

	root := opts.RepoRoot
	inRepo := false
	if root == "" {
		if r, err := gitutil.RepoRoot(""); err == nil {
			root = r
			inRepo = true
		}
	} else {
		if _, err := os.Stat(filepath.Join(root, ".git")); err == nil {
			inRepo = true
		}
	}

	if inRepo {
		printCheck("git repository", true, root)
		if cfg, err := config.Load(root); err != nil {
			printCheck(".curbpack.json", false, err.Error())
		} else if cfg == nil {
			printCheck(".curbpack.json", false, "missing — run: curbpack init")
		} else {
			printCheck(".curbpack.json", true, "packs="+strings.Join(cfg.Packs, ","))
			if cfg.Hooks {
				hook := githook.Path(root)
				b, err := os.ReadFile(hook)
				if err != nil {
					printCheck("pre-commit hook", false, "hooks=true but hook missing")
				} else if strings.Contains(string(b), "\r") {
					printCheck("pre-commit hook", false, "CRLF detected — convert to LF; init --hooks only replaces exact known Curbpack bodies")
				} else {
					switch githook.Classify(b) {
					case githook.KindCurrent:
						printCheck("pre-commit hook", true, "curbpack check")
					case githook.KindLegacyHeal:
						printCheck("pre-commit hook", false, "legacy curbpack check --heal (v0.5.2–v0.5.4) — run: curbpack init --hooks (exact-match migrate; backs up to .curbpack-legacy.bak)")
					default:
						if !strings.Contains(string(b), "curbpack") {
							printCheck("pre-commit hook", false, "present but does not call curbpack")
						} else if githook.ContainsHeal(b) {
							printCheck("pre-commit hook", false, "custom hook still runs check --heal — edit manually; do not blind-overwrite with init --hooks")
						} else {
							printCheck("pre-commit hook", true, "custom hook calls curbpack (not an exact Curbpack body)")
						}
					}
				}
			} else {
				printCheck("pre-commit hook", true, "not enabled (optional: curbpack init)")
			}
		}
		skill := filepath.Join(root, ".cursor", "skills", "curbpack", "SKILL.md")
		if _, err := os.Stat(skill); err == nil {
			printCheck("Cursor skill", true, skill)
		} else {
			printCheck("Cursor skill", true, "absent (optional: curbpack init)")
		}
		tasks := filepath.Join(root, ".vscode", "tasks.json")
		if _, err := os.Stat(tasks); err == nil {
			printCheck("VS Code/Cursor tasks", true, tasks)
		} else {
			printCheck("VS Code/Cursor tasks", true, "absent (optional: curbpack init)")
		}
	} else {
		printCheck("git repository", true, "cwd is not a product repo (ok — use curbpack demo)")
	}

	ids, err := packs.ListIDs()
	if err != nil {
		printCheck("embedded packs", false, err.Error())
	} else {
		printCheck("embedded packs", true, strings.Join(ids, ", "))
	}

	fmt.Println()
	if ok {
		if inRepo {
			cfg, _ := config.Load(root)
			if cfg == nil {
				fmt.Printf("%s\n", tty.C(tty.Bold+tty.Green, "[+] Doctor OK — next: curbpack init"))
			} else {
				fmt.Printf("%s\n", tty.C(tty.Bold+tty.Green, "[+] Doctor OK — next: curbpack check  (or bare: curbpack)"))
			}
		} else {
			fmt.Printf("%s\n", tty.C(tty.Bold+tty.Green, "[+] Doctor OK — try: curbpack demo"))
		}
		fmt.Printf("%s\n", tty.C(tty.Dim, "PATH lost after OS update? curbpack doctor --repair (local only; never downloads)"))
	} else {
		fmt.Printf("%s\n", tty.C(tty.Bold+tty.Yellow, "[!] Doctor found issues — fix above, then re-run"))
		fmt.Printf("%s\n", tty.C(tty.Dim, "stuck? docs/getting-started/troubleshooting.md · repair: curbpack doctor --repair"))
	}
	fmt.Printf("%s\n", tty.C(tty.Dim, Claim))
	if paths.EnvIs1("ALLOW_CONFIRM") {
		fmt.Printf("%s\n", tty.C(tty.Yellow, "CURBPACK_ALLOW_CONFIRM=1 is set — agents can stamp confirms. Never set this env on the Action."))
	}
	return nil
}

func runInstallHealth(printCheck func(string, bool, string), version string) {
	binPath, err := exec.LookPath(platform.BinaryName())
	if err != nil {
		// Running via go run / absolute path is still OK for doctor.
		exe, e2 := os.Executable()
		if e2 == nil {
			binPath = exe
			printCheck("install LookPath", true, "via executable: "+binPath)
		} else {
			printCheck("install LookPath", false, "curbpack not on PATH — "+platform.InstallCommandHint())
		}
	} else {
		printCheck("install LookPath", true, binPath)
	}

	marker, merr := platform.ReadMarker()
	if merr != nil {
		printCheck("install marker", true, "absent (ok if go install / workspace build) — schema curbpack-install-marker:1")
	} else if marker.Schema != platform.MarkerSchema {
		printCheck("install marker", false, "unexpected schema "+marker.Schema)
	} else {
		printCheck("install marker", true, platform.FormatMarkerDetail(marker))
	}

	if dir, err := platform.DefaultInstallDir(); err == nil {
		printCheck("install dir", true, dir)
	}
	_ = version
}

func runRepair(opts Options) error {
	fmt.Printf("%s\n", tty.C(tty.Dim, "repair: local PATH + alias only — no network / no auto-update"))
	hint := platform.InstallCommandHint()

	exe, err := os.Executable()
	if err != nil {
		fmt.Printf("%s\n", tty.C(tty.Red, "binary missing — reinstall:"))
		fmt.Printf("  %s\n", hint)
		return &ErrMissingBinary{Hint: hint}
	}
	exe, err = filepath.EvalSymlinks(exe)
	if err != nil {
		exe, _ = os.Executable()
	}
	if st, err := os.Stat(exe); err != nil || st.IsDir() {
		fmt.Printf("%s\n", tty.C(tty.Red, "binary missing — reinstall:"))
		fmt.Printf("  %s\n", hint)
		return &ErrMissingBinary{Hint: hint}
	}

	installDir := filepath.Dir(exe)
	binName := platform.BinaryName()
	aliasName := platform.AliasName()

	// Prefer conventional install dir for PATH/alias/marker (avoid writing into workspace ./bin).
	if def, err := platform.DefaultInstallDir(); err == nil {
		if _, err := os.Stat(filepath.Join(def, binName)); err == nil {
			installDir = def
			exe = filepath.Join(def, binName)
		} else if filepath.Base(filepath.Dir(exe)) == "bin" && strings.Contains(filepath.ToSlash(exe), "/curbpack/") {
			// Workspace build: still repair toward the conventional install dir if it exists or is creatable.
			installDir = def
		}
	}
	binDest := filepath.Join(installDir, binName)
	aliasDest := filepath.Join(installDir, aliasName)

	if _, err := os.Stat(binDest); err != nil {
		// Copy/link current executable into install dir if missing there but we have a usable exe.
		if err := os.MkdirAll(installDir, 0o755); err != nil {
			return err
		}
		if filepath.Clean(exe) != filepath.Clean(binDest) {
			in, err := os.ReadFile(exe)
			if err != nil {
				fmt.Printf("%s\n", tty.C(tty.Red, "binary missing — reinstall:"))
				fmt.Printf("  %s\n", hint)
				return &ErrMissingBinary{Hint: hint}
			}
			tmp := binDest + ".new"
			if err := os.WriteFile(tmp, in, 0o755); err != nil {
				return err
			}
			if err := os.Rename(tmp, binDest); err != nil {
				_ = os.Remove(tmp)
				return err
			}
		}
	}

	// Refresh alias (Unix symlink; Windows file copy).
	_ = os.Remove(aliasDest)
	if runtime.GOOS == "windows" {
		in, err := os.ReadFile(binDest)
		if err != nil {
			return err
		}
		if err := os.WriteFile(aliasDest, in, 0o755); err != nil {
			return err
		}
		tty.PrintStatus("alias", true, aliasDest+" (copy)")
	} else {
		if err := os.Symlink(binName, aliasDest); err != nil {
			// Fall back to copy
			in, rerr := os.ReadFile(binDest)
			if rerr != nil {
				return rerr
			}
			if err := os.WriteFile(aliasDest, in, 0o755); err != nil {
				return err
			}
			tty.PrintStatus("alias", true, aliasDest+" (copy fallback)")
		} else {
			tty.PrintStatus("alias", true, aliasDest+" → "+binName)
		}
	}

	pathDetail, pathErr := ensureDirOnPATH(installDir)
	if pathErr != nil {
		tty.PrintStatus("PATH", false, pathErr.Error())
	} else {
		tty.PrintStatus("PATH", true, pathDetail)
	}

	ver := opts.Version
	if ver == "" {
		ver = "unknown"
	}
	if !strings.HasPrefix(ver, "v") && ver != "unknown" && ver != "dev" {
		ver = "v" + ver
	}
	if err := platform.WriteMarker(ver, installDir, binDest); err != nil {
		tty.PrintStatus("install marker", false, err.Error())
	} else {
		mp := filepath.Join(installDir, "install-marker.json")
		tty.PrintStatus("install marker", true, mp)
	}

	// Fail-closed: only claim success after LookPath can resolve curbpack.
	if _, err := exec.LookPath(platform.BinaryName()); err != nil {
		fmt.Println()
		fmt.Printf("%s\n", tty.C(tty.Red, "repair incomplete — curbpack still not on PATH after local repair"))
		fmt.Printf("%s\n", tty.C(tty.Dim, "Open a new shell, or reinstall: "+hint))
		fmt.Printf("%s\n", tty.C(tty.Dim, Claim))
		return &ErrMissingBinary{Hint: hint}
	}

	fmt.Println()
	fmt.Printf("%s\n", tty.C(tty.Bold+tty.Green, "[+] Repair done (local only)"))
	fmt.Printf("%s\n", tty.C(tty.Dim, "Open a new shell if PATH was just updated. Missing binary forever? "+hint))
	fmt.Printf("%s\n", tty.C(tty.Dim, Claim))
	return nil
}

// ensureDirOnPATH prepends dir for this process and persists where supported.
// Returns a human status detail distinguishing session vs persisted PATH.
func ensureDirOnPATH(dir string) (detail string, err error) {
	// Always prepend for this process.
	pathEnv := os.Getenv("PATH")
	parts := splitPATH(pathEnv)
	found := false
	for _, p := range parts {
		if filepath.Clean(p) == filepath.Clean(dir) {
			found = true
			break
		}
	}
	if !found {
		_ = os.Setenv("PATH", dir+string(os.PathListSeparator)+pathEnv)
	}

	switch runtime.GOOS {
	case "windows":
		if err := persistWindowsUserPATH(dir); err != nil {
			return "", err
		}
		return dir + " on PATH (this session + User PATH persisted)", nil
	default:
		// Soft hint for Unix profiles — do not rewrite shell rc automatically.
		if !found {
			fmt.Printf("%s\n", tty.C(tty.Dim, "Add permanently (if needed): export PATH=\""+dir+":$PATH\""))
			return dir + " on PATH (this session only — not persisted to shell rc)", nil
		}
		return dir + " already on PATH (this session; Unix does not auto-edit shell rc)", nil
	}
}

func splitPATH(p string) []string {
	if p == "" {
		return nil
	}
	return strings.Split(p, string(os.PathListSeparator))
}

func persistWindowsUserPATH(dir string) error {
	// Best-effort via PowerShell so we do not need golang.org/x/sys.
	ps := fmt.Sprintf(
		`$d = '%s'; $p = [Environment]::GetEnvironmentVariable('Path','User'); if (-not $p) { $p = '' }; $parts = $p -split ';' | Where-Object { $_ -ne '' }; if ($parts -notcontains $d) { [Environment]::SetEnvironmentVariable('Path', ($d + ';' + $p).TrimEnd(';'), 'User'); Write-Output 'updated' } else { Write-Output 'present' }`,
		strings.ReplaceAll(dir, "'", "''"),
	)
	cmd := exec.Command("powershell", "-NoProfile", "-NonInteractive", "-Command", ps)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("persist User PATH: %w (%s)", err, strings.TrimSpace(string(out)))
	}
	return nil
}
