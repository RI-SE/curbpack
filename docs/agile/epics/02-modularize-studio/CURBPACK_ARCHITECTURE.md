# Curbpack — Target Architecture

## Architecture

Curbpack is organised around two independently usable systems: **Curbcheck** and **Curbpack Studio**. Studio is a modular monolith with a thin application shell, REST endpoints owned by their respective functional areas, and thin TypeScript pages. **KISS** is the governing principle.

## Repository structure

```text
curbpack/
├── models/                         # Shared data contracts
│   ├── internal/                   # Internal Python types, where needed
│   └── pydantic/                   # Pydantic contracts; generate JSON Schema as needed
│       ├── requirement.py
│       ├── claim.py
│       ├── pack.py
│       └── report.py
│
├── curbcheck/                      # Standalone check execution system
│   ├── api.py                      # Public Python API
│   ├── cli.py                      # Command-line interface
│   ├── impl/                       # Implementation, divided by responsibility
│   │   ├── execute.py
│   │   ├── registry.py
│   │   └── report.py
│   ├── checks/                     # Check implementations
│   └── tests/
│
├── studio/                         # Studio application
│   ├── app.py                      # Startup, shared infrastructure, router registration
│   ├── authentication/             # Identity and OIDC
│   │   ├── router.py
│   │   └── impl/
│   │       └── oidc.py
│   ├── authorization/              # Permissions and access control
│   │   ├── impl/
│   │   │   └── permissions.py
│   │   └── tests/
│   ├── pack/                       # Packs and Requirements
│   │   ├── cli.py
│   │   ├── router.py
│   │   ├── impl/
│   │   │   ├── extract.py
│   │   │   ├── import_pack.py
│   │   │   ├── working_copy.py
│   │   │   ├── edit.py
│   │   │   └── publish.py
│   │   ├── pages/
│   │   │   ├── extract/
│   │   │   └── editor/
│   │   └── tests/
│   ├── claim/                      # Claims and Discovery
│   │   ├── cli.py
│   │   ├── router.py
│   │   ├── impl/
│   │   │   ├── create.py
│   │   │   ├── edit.py
│   │   │   └── discovery.py
│   │   ├── pages/
│   │   │   ├── discovery/
│   │   │   └── editor/
│   │   └── tests/
│   ├── compile/                    # Report assembly and export
│   │   ├── router.py
│   │   ├── impl/                    # Report compilation and output formats
│   │   ├── pages/                  # Only if needed
│   │   └── tests/
│   ├── review/                     # Review of results and evidence
│   │   ├── router.py
│   │   ├── impl/
│   │   │   ├── results.py
│   │   │   └── evidence.py
│   │   ├── pages/
│   │   └── tests/
│   └── check/                      # Studio UI and REST adapter to Curbcheck
│       ├── router.py
│       ├── pages/
│       └── tests/
│
├── scripts/                        # Development, CI, packaging utilities
├── tests/                          # Cross-system and integration tests
├── docs/                           # Requirements, references, user/developer guides
├── policies/                       # Shared development rules
├── AGENTS.md                       # Short entry point for coding agents
├── Makefile
└── pyproject.toml
```

**The filenames inside `impl/` are examples of functional responsibilities, not a requirement to create empty files.** Optional `cli.py`, `pages/`, and other files exist only where needed.

## Responsibility and ownership

| Directory or file | Responsibility |
|---|---|
| `models/` | Shared data contracts. Use Pydantic as the source for validation and generate JSON Schema when required. |
| `models/internal/` | Internal Python types that are not public API contracts. |
| `models/pydantic/` | Shared public data models, validation and serialization. |
| `curbcheck/` | Independently usable Check execution system. No HTTP router of its own. |
| `curbcheck/api.py` | Public Python interface to Curbcheck functionality. |
| `curbcheck/cli.py` | Command-line interface to the same functionality. |
| `curbcheck/checks/` | Individual Check implementations. |
| `studio/app.py` | Starts Studio, provides shared application infrastructure and registers routers; no subsystem business logic. |
| `studio/authentication/` | User authentication, including OIDC. |
| `studio/authorization/` | Permissions and access control. Runtime data and certificates are stored outside the source tree. |
| `studio/pack/` | Pack and Requirement operations, including extraction, importing, editing working copies and publishing. |
| `studio/claim/` | Claim operations, discovery and editing. |
| `studio/compile/` | Assemble and export verification reports (e.g. JSON/PDF); does not run Checks or make human review decisions. |
| `studio/review/` | Human review of verification results and evidence; does not own report compilation. |
| `studio/check/` | Studio's thin REST adapter and UI for Curbcheck; does not reimplement Checks. |
| `router.py` | Owns REST paths, HTTP request/response handling and Pydantic validation; maps requests to explicit, typed Python arguments for implementation calls. |
| `api.py` | Public Python interface when one is needed. |
| `cli.py` | CLI interface when one is needed. |
| `impl/` | Business logic grouped into small Python modules by functional responsibility, independent of HTTP and UI. |
| `pages/` | Thin TypeScript UI; presentation and user interaction only; business operations use REST endpoints. |
| `scripts/` | Development, testing, CI and packaging scripts. |
| `tests/` | Cross-system/integration tests; subsystem tests live with their owners. |
| `docs/` | Requirements, reference contracts and guides. |
| `policies/` and `AGENTS.md` | Concise development rules and agent entry point. |

## Architectural rules

1. **KISS:** Choose the smallest clear implementation that satisfies the requirements. Do not add unnecessary layers or abstractions.
2. **Ownership:** Each Studio functional area owns its REST endpoints, implementation and UI where applicable.
3. **Thin REST layer:** `router.py` defines paths and public Pydantic request/response contracts, then calls `impl/` with explicitly mapped, typed Python arguments. Avoid passing framework request objects into domain logic.
4. **Independent implementation:** `impl/` does not depend on FastAPI, HTTP or TypeScript. CLI and REST interfaces reuse the same functionality without duplicating it.
5. **Thin application shell:** `studio/app.py` starts the application and registers routers; it does not implement functional-area operations.
6. **Thin UI:** TypeScript pages handle presentation and interaction; domain operations happen through REST APIs.
7. **Curbcheck integration:** `studio/check/router.py` exposes Curbcheck through Studio by calling `curbcheck/api.py`; Curbcheck needs no independent HTTP router.

## Runtime configuration

`curbpack-studio.json` holds configuration, not runtime database contents or private keys. Database files and certificates belong in the user's platform-appropriate application-data location, outside the repository. Paths may be configurable.

## Compile boundary

Compile is a separate Studio subsystem in `studio/compile/`. Move existing report assembly/export behavior there, including functionality previously dispersed across root `compile/` and `review/compile.py`. Check runs checks; Compile assembles reports; Review makes human review decisions.
