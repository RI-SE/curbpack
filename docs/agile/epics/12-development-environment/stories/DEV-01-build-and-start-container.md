# DEV-01 — Build and start the development container

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-12 Development environment](../EPIC.md)

**As a person building Studio**, I want Make to build and start one container, so that my machine and CI use the same build.

## Pedagogical example

From the Studio root, on a machine with Docker:

```text
make docker-dev
make run-docker-dev
```

The first command calls `scripts/build/docker-dev.sh` and leaves a local image. The second calls `scripts/run/docker-dev.sh` and publishes port 8770. Opening `http://127.0.0.1:8770/` shows the Studio UI. `make` with no arguments lists both commands. CI on Linux runs `make docker-dev` and does not copy the script into the workflow.

## Requirements (Given / When / Then)

### R1 — Build is one Make call

**Given** the Studio tree and a working Docker engine
**When** the person runs `make docker-dev`
**Then** Make invokes `scripts/build/docker-dev.sh` and does not itself contain the image build
**And** the command exits 0 and a local image exists.

### R2 — Start is one Make call

**Given** the image from R1
**When** the person runs `make run-docker-dev`
**Then** Make invokes `scripts/run/docker-dev.sh`
**And** a request to `http://127.0.0.1:8770/` receives an HTTP response from Studio.

### R3 — CI uses the same build

**Given** a pull request or a push to `main`
**When** the Linux CI job builds the container
**Then** that job runs `make docker-dev`
**And** `.github/workflows/ci.yml` does not repeat the build script.

### R4 — Existing entry points stay

**Given** the Make targets that exist before this story
**When** the person runs `make`, `make start`, or `make package`
**Then** `make` lists `docker-dev` and `run-docker-dev`
**And** `make start` still starts the local application
**And** `make package` still builds the host binaries it builds today.

## Out of scope

Pushing the image. A production image. Scanning, SBOM, or signing. Mounting the pilot workspace so data survives container removal (open on the epic). Changing `make test` or `make ci-tests`.
