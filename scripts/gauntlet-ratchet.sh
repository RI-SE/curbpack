#!/usr/bin/env bash
# Gauntlet ratchet: run baseline cases + dead-ends; fail on drift.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
if [[ ! -x "$BIN" ]]; then
  go build -o "$BIN" ./cmd/curbpack
fi

BASELINE="${GAUNTLET_BASELINE:-$ROOT/testdata/gauntlet-baseline.json}"
if [[ ! -f "$BASELINE" ]]; then
  echo "missing baseline: $BASELINE" >&2
  exit 1
fi

python3 - "$BIN" "$BASELINE" "$ROOT" <<'PY'
import json, os, subprocess, sys, tempfile, shutil

bin_path, baseline_path, root = sys.argv[1:4]
with open(baseline_path) as f:
    base = json.load(f)

cases = base.get("cases") or []
failed = 0

def run(cmd, cwd=None, env=None, timeout=60):
    e = os.environ.copy()
    if env:
        e.update(env)
    try:
        p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired as ex:
        return 124, (ex.stdout or "") + (ex.stderr or "") + "\nTIMEOUT"

for case in cases:
    cid = case["id"]
    expect = case.get("expect", "pass")  # pass | fail | exit_nonzero
    kind = case.get("kind")
    print(f"== gauntlet: {cid} ({kind}) expect={expect}")

    if kind == "unit_hint":
        # exercised by go test; record only
        continue

    tmp = tempfile.mkdtemp(prefix="gauntlet-")
    try:
        if kind == "heal_missing_stubs":
            subprocess.check_call(["git", "init", "-q"], cwd=tmp)
            subprocess.check_call(["git", "config", "user.email", "ci@curbpack.local"], cwd=tmp)
            subprocess.check_call(["git", "config", "user.name", "CI"], cwd=tmp)
            subprocess.check_call(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=tmp)
            code, out = run([bin_path, "init", "--packs", "house-policy"], cwd=tmp)
            for rel in ("SECURITY.md", ".well-known/security.txt"):
                p = os.path.join(tmp, rel)
                if os.path.exists(p):
                    os.remove(p)
            code, out = run([bin_path, "check", "--heal"], cwd=tmp)
            want_pass = expect == "pass"
            ok = (code == 0) if want_pass else (code != 0)
            for rel in ("SECURITY.md", ".well-known/security.txt"):
                if not os.path.isfile(os.path.join(tmp, rel)):
                    ok = False
                    out += f"\nmissing heal stub {rel}"
            if not want_pass:
                blob = out.lower()
                if "house-anti-placeholder" not in blob and "scaffold body overlap" not in blob:
                    ok = False
                    out += "\nexpected HOUSE-ANTI-PLACEHOLDER / scaffold body overlap on red re-check"
            cache = os.path.join(tmp, ".github/curbpack/cache/remediations.json")
            if want_pass and not os.path.isfile(cache):
                ok = False
                out += "\nmissing remediations.json"
            if not ok:
                print(out)
                print(f"FAIL {cid}: exit={code}", file=sys.stderr)
                failed += 1
            else:
                print(f"OK {cid}")

        elif kind == "dead_end_non_git":
            code, out = run([bin_path, "check"], cwd=tmp)
            ok = code != 0
            if "git" not in out.lower() and "repository" not in out.lower():
                ok = False
            if not ok:
                print(out)
                print(f"FAIL {cid}", file=sys.stderr)
                failed += 1
            else:
                print(f"OK {cid}")

        elif kind == "dead_end_placeholders":
            subprocess.check_call(["git", "init", "-q"], cwd=tmp)
            subprocess.check_call(["git", "config", "user.email", "ci@curbpack.local"], cwd=tmp)
            subprocess.check_call(["git", "config", "user.name", "CI"], cwd=tmp)
            subprocess.check_call(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=tmp)
            run([bin_path, "init", "--packs", "house-policy"], cwd=tmp)
            with open(os.path.join(tmp, "SECURITY.md"), "w") as fh:
                fh.write("# Security\n\nTODO: replace this placeholder with real contacts.\n")
            code, out = run([bin_path, "check"], cwd=tmp)
            ok = code != 0
            if not ok:
                print(out)
                print(f"FAIL {cid}", file=sys.stderr)
                failed += 1
            else:
                print(f"OK {cid}")

        elif kind == "adversarial_pack_load":
            pack_dir = os.path.join(root, case["pack_dir"])
            env = {"CURBPACK_PACKS_DIR": pack_dir}
            # Load via packs list / validate using override — expect fail-closed load or gate fail
            code, out = run([bin_path, "packs", "list"], env=env)
            # unknown check should fail LoadEmbedded when listing if that pack is requested;
            # we validate via a tiny Go-less check: try init with the bad pack id if present
            pack_id = case.get("pack_id", "")
            if pack_id:
                subprocess.check_call(["git", "init", "-q"], cwd=tmp)
                subprocess.check_call(["git", "config", "user.email", "ci@curbpack.local"], cwd=tmp)
                subprocess.check_call(["git", "config", "user.name", "CI"], cwd=tmp)
                subprocess.check_call(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=tmp)
                code, out = run([bin_path, "init", "--packs", pack_id], cwd=tmp, env=env)
                ok = code != 0
            else:
                ok = True
            if expect == "fail_closed":
                if not ok:
                    print(out)
                    print(f"FAIL {cid}", file=sys.stderr)
                    failed += 1
                else:
                    print(f"OK {cid}")
            else:
                print(f"OK {cid}")

        elif kind == "adversarial_runtime":
            pack_dir = os.path.join(root, case["pack_dir"])
            pack_id = case["pack_id"]
            env = {"CURBPACK_PACKS_DIR": pack_dir}
            subprocess.check_call(["git", "init", "-q"], cwd=tmp)
            subprocess.check_call(["git", "config", "user.email", "ci@curbpack.local"], cwd=tmp)
            subprocess.check_call(["git", "config", "user.name", "CI"], cwd=tmp)
            subprocess.check_call(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=tmp)
            # Write config pointing at adversarial pack without init scaffold when load fails
            with open(os.path.join(tmp, ".curbpack.json"), "w") as fh:
                json.dump({"packs": [pack_id]}, fh)
            # Ensure pack is loadable for runtime cases (path traversal / bad regex)
            code, out = run([bin_path, "check", "--packs", pack_id], cwd=tmp, env=env)
            # Must not panic (exit 2 from Go panic rarely); expect non-zero gate fail
            ok = code != 0 and "panic" not in out.lower()
            if expect == "fail_no_panic":
                if not ok:
                    print(out)
                    print(f"FAIL {cid} exit={code}", file=sys.stderr)
                    failed += 1
                else:
                    print(f"OK {cid}")
            else:
                if not ok:
                    failed += 1
                else:
                    print(f"OK {cid}")

        elif kind == "realish_tree":
            src = os.path.join(root, case["fixture"])
            shutil.copytree(src, tmp, dirs_exist_ok=True)
            if not os.path.isdir(os.path.join(tmp, ".git")):
                subprocess.check_call(["git", "init", "-q"], cwd=tmp)
                subprocess.check_call(["git", "config", "user.email", "ci@curbpack.local"], cwd=tmp)
                subprocess.check_call(["git", "config", "user.name", "CI"], cwd=tmp)
                subprocess.check_call(["git", "add", "-A"], cwd=tmp)
                subprocess.check_call(["git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "fixture", "-q"], cwd=tmp)
            code, out = run([bin_path, "check"], cwd=tmp, timeout=int(case.get("timeout_sec", 60)))
            want_pass = expect == "pass"
            ok = (code == 0) if want_pass else (code != 0)
            if not ok:
                print(out)
                print(f"FAIL {cid} exit={code}", file=sys.stderr)
                failed += 1
            else:
                print(f"OK {cid}")

        elif kind == "diff_skip":
            # Pure unit coverage via go test; no-op here
            print(f"OK {cid} (covered by go test)")

        else:
            print(f"UNKNOWN kind {kind} for {cid}", file=sys.stderr)
            failed += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if failed:
    print(f"gauntlet: {failed} case(s) failed", file=sys.stderr)
    sys.exit(1)
print("gauntlet: OK (baseline matched)")
sys.exit(0)
PY
