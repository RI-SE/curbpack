# SYS-03 — One repository is the pilot door

**Status:** Decided 2026-10-28 by danielfl. Not implemented. Required for the pilot.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a pilot user**, I want Pack Editor, Discover, Check, and Review to open the one repository I chose, so that Packs, Claims, the run, and the report are the same files and the page shows me that.

This is done on the existing stub: `/requirements`, `/discover`, `/check`, and `/review`. It does not add an application, a registry, or a second catalog.

`curbpack.json` lists Pack ids. It may also contain `requirements`, `exclude_requirements`, and `search_hints`. The last of those is the rename in [SYS-04](SYS-04-search-hints.md). It also points at one directory. Decided 2026-10-28 by danielfl. The key is `curbpack`, and the value is a path relative to the repository. When the key is absent, the directory is `curbpack`. There is no version pin and no separate Claim path. Whether version pins are added stays open on DOC-04.

That directory is where this repository's Packs, Claims, and reports live:

- `<directory>/packs/<pack-id>/pack.json`, with an existing Requirement file beside it
- `<directory>/claims/<claim-id>.json`
- `<directory>/reports/` is the report directory. Check writes one new file per run, `run-<YYYYMMDDTHHMMSSZ>.json`, UTC, so a later run does not replace an earlier one. Review writes `review-<YYYYMMDDTHHMMSSZ>.json` in that same directory. There is no single overwritten `run-result.json` or `review-report.json`.

Claim JSON is unchanged. The directory name is packaging. These files are not written to `<repository>/claims/`, `<repository>/.curbpack/`, or `<repository>/docs/reports/`. Saving the directory writes the `curbpack` value in that repository's `curbpack.json`. It is not Studio workspace state.

Decided 2026-10-28 by danielfl, after the plan review. Discover holds candidates in memory and reads existing Claims from `<directory>/claims/`. The page distinguishes the two. A candidate becomes a Claim, or updates one, only through that process, which writes the project's claim catalog. An extraction is the same shape: memory or temp disk, not the Pack. The Requirement view shows the Requirements already beside that Pack's `pack.json`, and distinguishes them from the extraction. The same kind of process writes a new Requirement file there or updates the existing one.

`docs/reference/packs2.md` §2.3, `docs/arch/ARCHITECTURE.md`, `claims/ARCHITECTURE.md`, and `review/ARCHITECTURE.md` still describe the older layout: no directory in the file, Claims at `claims/`, and the report at `docs/reports/`. Those sentences are stale. This story is the pilot rule. It does not rewrite the whole document set. DOC-04 remains that later pass.

The reference product keeps its Packs and Claims under `external_test/curbpack/`. Its selection file is `curbpack.json`, not `.curbpack.json`, and its `curbpack` value is `external_test/curbpack`. The current `.curbpack.json` only lists Pack ids. `selection.json` stays the working-copy selection PE-11 already uses. This story does not replace it.

Check's edit page is [CHK-01](CHK-01-select-product-and-packs.md). That page and Pack Editor show and save the same `curbpack` value. This story does not add a second editor for the id lists.

Export of a Pack directory is [PE-11](PE-11-publish-pack.md). This story does not define a second export, and it does not change PE-11's overwrite rule.

### SYS-R01 — Pack Editor opens a repository, not the Studio catalog

**Given** the Pack Editor stub  
**When** the person has not chosen a repository  
**Then** the first control is a repository picker  
**And** the page does not list Packs from `registered_sources.json`  
**And** the page does not invent Pack ids from the Studio workspace.

**Given** a chosen repository whose root contains `curbpack.json`  
**When** Pack Editor opens  
**Then** the page reads that file  
**And** it shows the absolute path of the file  
**And** it shows each Pack id in `packs`  
**And** it shows the `curbpack` directory from that file, or `curbpack` when the key is absent, and the person can set it  
**And** a Pack row exists only when `<directory>/packs/<pack-id>/pack.json` is a file  
**And** an id in the file with no such directory is shown as missing and is not replaced with another Pack.

**Given** a Pack row on Pack Sources  
**When** that Pack resolves to `<directory>/packs/<pack-id>/pack.json`  
**Then** the URL cell shows the document URL  
**And** under that URL, in muted text, it shows the pack directory `<directory>/packs/<pack-id>`  
**And** the path is not a new column  
**And** the page does not read or write `.curbpack.json`.

**Given** a chosen repository with no `curbpack.json`  
**When** Pack Editor opens  
**Then** the page says the file is absent  
**And** it shows no Pack rows  
**And** it does not read `.curbpack.json`.

### SYS-R02 — Add writes into the opened repository

**Given** a chosen repository whose `<directory>/claims/` is missing or empty  
**When** Pack Editor opens it  
**Then** the page says there are no Claims.

**Given** that repository  
**When** the person adds a Pack  
**Then** Studio writes `<directory>/packs/<pack-id>/pack.json`  
**And** it adds that id to this repository's `curbpack.json`  
**And** it does not write `registered_sources.json`.

`curbpack.json` is what selects the Packs. A requirements repository can be the packs root of a product repository. Section rows and extraction stay on PE-05 and PE-06. They use the resolved pack directory. This story does not invent a source field.

### SYS-R03 — A shared packs root still leaves each project its own file and its own Claims

**Given** a directory whose `packs/<pack-id>/pack.json` exists  
**When** the person sets this repository's `curbpack` value to that directory  
**Then** the Pack id resolves there  
**And** another repository that keeps its own `curbpack` value does not change  
**And** Claims are read from that directory's `claims/`  
**And** a Claim whose Requirement is not in the Packs now resolved is shown as not in those Packs  
**And** that retarget does not delete or rewrite the Claim file, and it does not rewrite the report.

The destination may be a folder the person keeps for many projects. The story does not hard-code that folder's name. For the cyberready test product the `curbpack` value is `external_test/curbpack`.

### SYS-R04 — Discover reads the claim catalog and keeps candidates in memory

**Given** the repository and packs root from SYS-R01  
**When** the person opens Discover  
**Then** Discover shows the same repository path and the same packs root  
**And** the Requirements it offers are those in the Packs `curbpack.json` selects from that packs root  
**And** the Claims it shows as existing are the files in `<directory>/claims/`  
**And** a candidate is held in memory and is not a file in that catalog  
**And** the page distinguishes an existing Claim from a candidate  
**And** the process that turns a candidate into a Claim writes `<directory>/claims/<claim-id>.json`, or updates that existing Claim file  
**And** no other Discover action writes a Claim file  
**And** that process does not write `<workspace>/product/claims/` or `<repository>/claims/`  
**And** Discover does not load Requirements from `registered_sources.json` or from a working copy the page did not name.

### SYS-R05 — Check runs that repository against that packs root

**Given** the same repository, packs root, and Requirement selection  
**When** the person runs Check  
**Then** the run reads `<repository>/curbpack.json` and `<directory>/claims/`  
**And** it loads Pack directories only from that packs root  
**And** it evaluates the Requirements the page shows as selected, including `requirements` and `exclude_requirements` when those lists are in the file  
**And** a Claim whose Requirement is not selected is not run, and it does not abort the run of the selected ones  
**And** the run is a new file `<directory>/reports/run-<YYYYMMDDTHHMMSSZ>.json`  
**And** a second run writes a second file and leaves the first in place  
**And** the page shows the path of the file this run wrote.

### SYS-R06 — Review compiles that run and those Claims

**Given** SYS-R05 has written the run result  
**When** the person compiles a report  
**Then** the report is compiled from the dated run file this Check wrote  
**And** the Claims it reads are `<directory>/claims/`  
**And** the report file is `<directory>/reports/review-<YYYYMMDDTHHMMSSZ>.json`  
**And** compiling again writes another file and leaves the earlier report in place  
**And** the page names that repository and that packs root  
**And** it does not compile the workspace `product/` run or write the report under workspace `product/`.

### SYS-R07 — One selection follows all four pages

**Given** a repository and a packs root chosen on any of these pages  
**When** the person opens Pack Editor, Discover, Check, or Review  
**Then** each page names that same repository and that same packs root  
**And** choosing a different repository on one page changes all four  
**And** Discover, Check, and Review, opened before a repository is chosen, say that none is chosen and do not read the workspace `product/` repository.

### SYS-R08 — An extraction stays temporary; the Requirement view shows the Pack

**Given** a Pack whose `<directory>/packs/<pack-id>/` already contains Requirement files beside `pack.json`  
**When** the person opens the Requirement view for that Pack  
**Then** those existing Requirements are shown  
**And** the page distinguishes them from an extraction  

**Given** the person extracts a section of that Pack  
**When** extraction finishes  
**Then** the extracted Requirements are in memory or on temp disk  
**And** they are not files under `<directory>/packs/<pack-id>/`  
**And** the process that accepts an extraction writes a new Requirement file beside that `pack.json`, or updates the existing Requirement file  
**And** no other extraction action writes that file.

### Does not pass

The story is not done while any of these remain:

- Pack Editor lists Packs from `registered_sources.json` after a repository is chosen.
- Check still offers **Read it** and **Start empty**, or fills the table from the workspace Pack list.
- Discover writes a Claim file for a candidate that has not gone through the create-or-update process, or writes a Claim outside `<directory>/claims/`.
- The page does not distinguish an existing Claim from a candidate.
- Check ignores `requirements` or `exclude_requirements`, or aborts the selected Requirements because some other Claim is in `<directory>/claims/`.
- Check overwrites one run file, or writes the run outside `<directory>/reports/`.
- Review compiles the workspace `product/` run, or writes the report outside `<directory>/reports/`, or replaces an earlier report file.
- A changed `curbpack` value hides a Claim whose Requirement no longer resolves, or rewrites that Claim.
- The directory is remembered only in Studio state and not in `curbpack.json`.
- An extraction is written into `<directory>/packs/<pack-id>/` before the person commits it.
- The Requirement view hides a Requirement that already sits beside that Pack's `pack.json`, or does not distinguish it from an extraction.

### Stop if

Stop when a step would add a version pin, read `.curbpack.json`, keep `registered_sources.json` as the list of Packs after a repository is chosen, or store the directory anywhere except the `curbpack` value in `curbpack.json`. Record the step. Do not follow the stale layout in the older documents because it is already on the page.
