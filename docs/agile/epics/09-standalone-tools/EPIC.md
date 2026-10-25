# EP-09 — Start each Packs v2 tool on its own

**Status:** Draft. Not authorization to move code, rename packages, or open repositories.
**Type:** User epic. The stories are the people who start one tool.
**Starts when:** EP-01 is accepted. Does not wait for every EP-02 story. Does not block the pilot.

## Goal

The names in `docs/reference/packs2.md` ("Names — curbpack is the ecosystem; products stand alone") are the programs a person starts. `docs/arch/ARCHITECTURE.md` currently names the same work as directories inside one application. This epic makes each product startable by itself. The integrated pilot is `pilot_app`. It is the cover that links the tools. It is not a seventh product and it does not own their behavior.

`curbpack` stays the format and trust name (`curbpack.json`, Packs, Requirements, Claims). It is not a process. `common/` stays the shared library those processes call for Packs v2 IO, validation, and signing. Discover stays a mode inside curbpack-claims. Extract stays inside Requirements.

## Why the split is small, and why it is not done

The operations already live in `requirements/`, `claims/`, `checks/`, `review/`, `scaffold/`, and `common/`. `python3 -m checks` already evaluates Claims without the UI, and the run result's `tool` is already `curbcheck` (`common/version.py`). `scaffold/stub.py` only imports `common.errors`. A later repository per tool is then `common/` plus that tool.

These seams are why that copy is not available today:

- The only startable processes are `python3 -m app` and `python3 -m checks`.
- Requirements and Claims pages import `app.pages` (`requirements/ui/pages.py`, `claims/ui/pages.py`, `claims/ui/researcher.py`). The tools depend on the shell.
- `app/server.py` imports every tool and is the only UI process.
- `discovery/` is a top-level package and `discovery/assess.py` imports `requirements.extract.call`.
- Compile is `review/compile.py`. There is no compile process.
- `workflow.py` at the repository root builds the cover from checks, requirements, and review.

EP-02 keeps functions callable without the GUI and still places HTTP in `app/`. This epic uses that callable seam. When this epic is accepted it narrows EP-02's shell: `pilot_app` owns the cover and the pilot's HTTP; each UI tool owns the HTTP that serves only itself. Subsystem functions still do not import the web framework. `docs/agile/future_architecture.md` says EP-02 is the only planned reshape and that the shell is not renamed. That sentence stays until this epic is accepted.

## Stories

| ID | User | Starts |
| --- | --- | --- |
| [TL-01](stories/TL-01-start-requirements.md) | Legal expert | Requirements, alone |
| [TL-02](stories/TL-02-start-claims.md) | QA engineer | curbpack-claims, alone |
| [TL-03](stories/TL-03-start-scaffold.md) | Developer | curbpack-scaffold, alone |
| [TL-04](stories/TL-04-start-curbcheck.md) | CI | curbcheck, alone |
| [TL-05](stories/TL-05-start-compile.md) | Person preparing a handoff | curbpack-compile, alone |
| [TL-06](stories/TL-06-start-review.md) | Reviewer | curbpack-review, alone |
| [TL-07](stories/TL-07-start-pilot-app.md) | Pilot operator | pilot_app, the integrated cover |

Each tool story can land on its own after the epic is accepted. TL-07 stays true the whole time: the pilot journeys in EP-01 still start from one cover.

## Epic acceptance

1. A person can start each packs2 product in the table above and do that product's job without starting another product.
2. Requirements and curbpack-claims answer on the command line and in their own UI. curbcheck and curbpack-compile are command line. curbpack-scaffold and curbpack-review are UI. pilot_app is the cover.
3. No tool imports `pilot_app` or another tool's UI. A tool reads another tool's Packs v2 files through `common/`.
4. `python3 -m checks` still starts curbcheck. EP-07's name for that command stays.
5. Signed Requirement, Claim, pack, and report bytes are unchanged by a start that does not edit that object.
6. `docs/arch/ARCHITECTURE.md` names these programs and calls the shell `pilot_app`. It stops describing the tools only as directories of one application. Packs v2 fields do not change.
7. The EP-01 cover journeys still run from pilot_app.

## Out of scope

- Creating a Git repository per tool. The import rule above is what makes that copy small later.
- Renaming the `checks` package. The product name is curbcheck; the start command is `python3 -m checks`.
- The deferred scaffold role in `docs/arch/ARCHITECTURE.md` (propose remediation from check results, `remediation_hint`, and templates). TL-03 is the stub writer in packs2.
- New Packs v2 fields, a plugin framework, a second check engine, or a new domain type.
- Rewriting EP-02's thin pages, shared models, or headless tests. Those stories remain EP-02.

## Open until this epic is accepted

- **Shell HTTP.** Proposed resolution: `pilot_app` serves the cover; each UI tool serves its own pages; domain functions stay free of the web framework. This narrows ARCH-01. It is not decided by this draft.
- **Entry-point spelling** for the tools that have no `__main__` yet. Proposed resolution: `python3 -m requirements`, `python3 -m claims`, `python3 -m scaffold`, `python3 -m compile`, `python3 -m review`, and `python3 -m pilot_app`, matching `python3 -m checks`. Product names are what the person sees. Packaging commands beyond that stay an implementation choice, as packs2 already says.
