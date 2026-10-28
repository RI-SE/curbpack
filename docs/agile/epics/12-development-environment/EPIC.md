# EP-12 — Development environment

**Status:** Draft. Not authorization to implement.
**Type:** Maintainer epic. The user is a person building or running Studio, including CI.
**Starts when:** Scheduled. Does not block EP-01. Does not wait for EP-02 or EP-09.

## Goal

A person can build and start one Studio container with Make, and CI runs that same build. Make only calls scripts. The workflow file does not grow a second copy of the build.

`docs/agile/future_cicd.md` is still the target CI/CD policy and is not in force. This epic is the development container that policy describes. Scanners, SBOM, signing, and promotion of a production image stay in that policy until they are scheduled.

## Why this epic exists

EP-01, EP-02, and EP-03 each leave Docker outside their own scope. Studio already has `make start`, `make test`, `make ci-tests`, and `make package`. None of them builds a container. The application listens on `127.0.0.1` port 8770 (`app/server.py`), so a container is reachable from the host only when it listens on an address the published port can reach.

## Stories

| ID | User goal | Depends on |
| --- | --- | --- |
| [DEV-01](stories/DEV-01-build-and-start-container.md) | Build and start the development container with Make. CI calls that build. | — |

Draft stories are not permission to implement. Further stories (a production image, a registry, an image scan) are not opened here. They wait in `docs/agile/future_cicd.md`.

## Epic acceptance

- From the Studio root, one Make target builds the development image by calling one script.
- One Make target starts that image by calling one script.
- After start, a request from the host to `http://127.0.0.1:8770/` receives an HTTP response from Studio.
- The Linux CI job builds the image by invoking the build target. The workflow does not repeat the script.
- `make` with no arguments lists both targets.
- `make start` and `make package` keep their current behavior.
- Packs v2 files, signatures, and published bytes are unchanged.

## Out of scope

- A production image, a registry push, image scanning, SBOM, or signing.
- Replacing the macOS and Windows packages from `make package`.
- A database, a multi-user service, or an editor dev container.
- Changing the Packs v2 contract or the pilot journeys.
- Rewriting `.github/workflows/ci.yml` beyond one job that calls the build target.

## Open until this epic is accepted

- **Make target names.** Proposed resolution: `make docker-dev` calls `scripts/build/docker-dev.sh`, and `make run-docker-dev` calls `scripts/run/docker-dev.sh`. Those script paths and the run target are the names in `docs/agile/future_cicd.md`. The build target is the extra user-facing entry point that policy allows. DEV-01 uses these names. Status OPEN.
- **Workspace inside the container.** Proposed resolution: the start script mounts a workspace directory and does not bake `data/workspace` into the image. DEV-01 does not require data to survive `docker rm`. Status OPEN.

## Relation to other epics

- **EP-01** finishes the functional pilot. This epic does not gate it.
- **EP-02** modularizes the process. A container is not that split.
- **EP-03** records security evidence. It does not build this image. SEC-04 and SEC-05 stay there.
- **EP-09** makes each tool startable on its own. This epic containers the Studio tree that exists today.
