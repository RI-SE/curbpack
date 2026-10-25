# Install and start Curbpack Studio

Install is how you get the local application running before the getting-started walkthrough.

The procedure below is a source checkout. It was run against this repository. A published installer for macOS and for Windows is not described here, because this tree does not by itself prove that both release binaries exist.

## 1. macOS or Linux, from a source checkout

Studio's Python dependency is `cryptography`, listed in `requirements.txt`.

```sh
python3 -m pip install -r requirements.txt
make start
```

`make start` runs `python3 -m app`. The process listens on `127.0.0.1:8770` unless you pass `--host` or `--port`. A source checkout uses `data/workspace` inside the repository as its workspace. A frozen build uses `~/curbpack-studio/workspace` so it does not write into the extracted bundle.

For a disposable workspace:

```sh
python3 -m app --workspace /absolute/path/to/disposable-workspace
```

Open the URL printed at startup. The usual one is `http://127.0.0.1:8770`.

`make package` builds two executables only for macOS ARM64 or Windows x64, and only when it is run on that host. `curbpack-studio-<host>` is the application. `curbcheck-<host>` is the checker. On macOS ARM64 those names are `curbpack-studio-macos-arm64` and `curbcheck-macos-arm64`. Run the checker with `curbcheck-macos-arm64 --repo --packs --out`. A source checkout, including Linux, still uses `python3 -m checks` with the same arguments. Follow that release's own notes if a later download is published. Gatekeeper and SmartScreen behavior for an unsigned download is in [Troubleshooting](troubleshooting.md).

## 2. Windows

From a source checkout, after `requirements.txt` is installed:

```powershell
python -m app
```

`make package` on Windows builds and smoke-tests `curbpack-studio-windows-x64.exe` and `curbcheck-windows-x64.exe`. The checker takes `--repo`, `--packs`, and `--out`. A source checkout still uses `python -m checks` with the same arguments. `.github/workflows/ci.yml` and `.github/workflows/release.yml` describe the jobs. A workflow file does not mean a downloadable `.exe` exists for the commit you have. Use the address printed at startup.

## 3. Verify

```sh
make test
make ci-tests
```

`make test` runs the functional tests. `make ci-tests` runs the mandatory CI checks. `ONLY=tests` selects that one check. Today the only registered check name is `tests`.

These commands do not certify a product repository. In the browser, confirm the cover loads and that **Packs** (`/requirements`), **Discovery & Claims** (`/discover`), **Check** (`/check`) and **Review** (`/review`) open.

The cover also has a Developer section: Claim editor (`/claims`), Scaffold (`/scaffold`), a sample requirement editor (`/requirement`), and **Prepare sample workspace**. Prepare builds a small demo workspace. It is not installation of the Glucose Log reference product, and it does not become the Pack Check uses unless you select it.

## 4. If it does not start

Record the interpreter, the platform, the command, and the error. Do not delete a workspace or regenerate Packs as a generic fix. If the port is taken, start with `--port` set to a free port.

## 5. Next

Continue with [Getting started](getting-started.md).
