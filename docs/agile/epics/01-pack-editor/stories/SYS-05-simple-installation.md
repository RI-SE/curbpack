# SYS-05 — Install Studio and curbcheck with one simple choice

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**Status:** Implemented and locally verified; native Windows and published-installer release acceptance remain pending. Retrospective story recording the installation work authorized by the maintainer on 2026-10-29.

**As a user**, I want a simple installer for my computer, so that I can start Curbpack Studio and run curbcheck without cloning the repository, installing Python, or manually choosing and renaming binaries.

## User choices

- **Install Studio:** install both `curbpack-studio` and `curbcheck`.
- **Install curbcheck only:** install only `curbcheck`, preserving any existing Studio program.
- **Manual installation:** retain the explicit download and checksum instructions below the normal installation path for users who manage their own installation.

## Acceptance behavior

### R1 — Studio includes the checker

**Given** a release with binaries and SHA-256 entries for the detected host
**When** the user runs the Studio installer
**Then** both programs are downloaded and verified before either installed program is replaced
**And** they are installed under stable command names, without Python, a source checkout or administrator privileges.

Hosts addressed by the installers are macOS ARM64, Linux x64 with glibc (Ubuntu 22.04 or newer), and Windows x64. Unsupported hosts stop with a clear error. Build or fixture-test coverage alone is not a claim of native platform support; release acceptance is recorded separately.

### R2 — Checker-only installation stays independent

**Given** an existing Studio installation
**When** the user runs the curbcheck-only installer
**Then** only `curbcheck` is installed or updated
**And** the existing Studio executable is unchanged.

### R3 — A bad download cannot replace an installed program

**Given** existing installed programs
**When** any required download is missing, its checksum entry is missing or invalid, or its bytes do not match SHA-256
**Then** installation fails before replacing either executable
**And** an error identifies the failure.

A permission error or a locked executable during the subsequent installation phase may still interrupt replacement. This story does not promise a transaction across two programs. Workspaces, Packs, Claims, signatures, product evidence and product configuration are never installation targets.

### R4 — The normal path needs no configuration

**Given** the default installer command from the installation guide
**When** a published installer release is available
**Then** one release tag is resolved and used for all binary and checksum downloads
**And** Unix installs under `~/.local/bin`, with a PATH instruction when needed
**And** Windows installs under `%LOCALAPPDATA%\Programs\Curbpack` and adds that directory to the user's PATH.

An explicit release and destination are optional overrides via `CURBPACK_VERSION` and `CURBPACK_INSTALL_DIR`. A pinned installer command downloads the installer and programs from the same tag. Repeating the command updates only its selected programs.

### R5 — The release carries standalone installers

**Given** a successful CI run
**When** installer artifacts are packaged
**Then** `install-studio.sh`, `install-curbcheck.sh`, `install-studio.ps1`, `install-curbcheck.ps1` and their `SHA256SUMS` are produced
**And** each installer is standalone; it needs no downloaded helper source or product source checkout
**And** authorized release publishing reuses those verified CI bytes and includes their checksums.

The installer CI job is independent of the Studio and checker build jobs. This story does not authorize publishing a release.

### R6 — Documentation makes the simple path obvious

**Given** a new user opening the installation guide
**Then** the first instructions install Studio with its checker
**And** checker-only installation is a distinct choice
**And** start commands, PATH help, supported installer targets and release availability are stated
**And** Manual installation remains below the installer instructions
**And** developers can locate installer source, packaging and tests.

## Verification

| Evidence | Observed result |
| --- | --- |
| Unix installer and release integration tests | 28 passed; includes preservation, version selection, repeat installation, libc rejection and generated artifact checksums |
| PowerShell installer scenarios | 9 passed in PowerShell 7.6.9 on macOS with fixture downloads, simulated Windows environment values and a PATH callback |
| Actual macOS ARM64 release files | Installed both programs from `2026-10-28a-test-release`; checker help and Studio HTTP cover passed in temporary directories |
| Actual Linux x64 binaries | Built from source in Ubuntu 22.04 under x64 emulation, installed under stable names, both packaged smoke tests passed |
| Actual Alpine/musl x64 | Installer rejected the host before downloading; existing programs preserved |
| Isolated full local CI suite | 378 passed, 0 failed, on the committed baseline plus SYS-05 changes |
| Native Windows user PATH persistence | Automated CI check prepared; not executed on native Windows locally |
| Public installer download commands | Not executed against a newly published installer release; no release was published by this work |

The old macOS release has the older checker CLI. Its observed `--help` and startup prove installation/startup only; the current CLI is exercised by the new Linux build and existing checker tests. No fixture result is presented as native Windows acceptance.

The live implementation and verification record is [plan/SYS-05.md](../../../../../plan/SYS-05.md). It will move to `impl/SYS-05.md` only after all in-scope acceptance evidence and independent review are complete. Native Windows behavior and a newly published release must not be reported as observed if they have not been run.

## Boundaries

No package manager integration, GUI wizard, automatic background updates, shell-profile rewriting, new persistent schemas, product release policy, signing operation, `doctor`, legacy aliases or repair framework. The user's own product policies continue to govern release decisions and publication. Native release checks remain subject to SYSTEM_REQUIREMENTS MUST-84.
