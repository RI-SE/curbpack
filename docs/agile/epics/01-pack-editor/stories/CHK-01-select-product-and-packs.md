# CHK-01 — See what a Check run will use

**Status:** Specified 2026-10-28 by danielfl. Not implemented. Choosing a repo already works.

The repository, the packs root, and the `claims/` directory are the ones [SYS-03](SYS-03-one-repo-door.md) selected. This story does not open a second door.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a product engineer**, I want one edit page for the chosen product repository's `curbpack.json`, so that before a run I can see what was loaded, what I have changed, which Packs and Requirements apply, and where that repository's Claims are.

This is the pilot's product-selection page. A person must understand it without reading the source.

**Implementation note:** Preserve the normative product configuration (`curbpack.json`) and Packs v2 semantics. No new Pack inheritance or `requires` schema is authorized. Whether `curbpack.json` stores only Pack ids or exact version pins stays the open question on DOC-04. This story does not decide it, and it does not add a version-pin field.

### CHK1-R01 — The page shows that the file was read, and where each Pack came from

**Given** a chosen product repository  
**When** Check opens this page  
**Then** the page names that repository  
**And** it names the path of `curbpack.json` in that repository  
**And** it says that the file was read, or that the file is absent  
**And** each Pack row says whether its id was in the file or is only offered by the page  
**And** each row names the Pack version that would be used, or says that the version cannot be resolved  
**And** a missing or unresolvable version is not silently replaced with another version.

Choosing the repository already works. The current page does not do the rest. It offers **Read it** and **Start empty** as two links, and the table is the workspace Pack list with no origin on the row.

### CHK1-R02 — The packs directory is on the page and can be set

**Given** this page for a chosen repository  
**When** the person looks for the Pack files behind the ids  
**Then** the page names the directory those ids are loaded from  
**And** the person can set that directory as directly as a Pack source is chosen  
**And** for the cyberready test product the directory to point at is `external_test/curbpack/packs`.

The directory on disk is `external_test`, not `external_tests`.

### CHK1-R03 — Loaded and changed stay distinct, and Studio Requirements can be chosen

**Given** a `curbpack.json` that was read  
**When** the person changes Packs or Requirements and has not saved  
**Then** the page shows what was loaded and what Save would write  
**And** the person can choose Requirements authored in Studio from the Packs this page has loaded  
**And** that choice uses the file's existing `requirements` and `exclude_requirements` lists  
**And** those lists are visible on the page, not only inside Export  
**And** the page does not say that a selected Pack means the product complies with it.

### CHK1-R04 — Claims for this repository are the files in its claims directory

**Given** the chosen product repository  
**When** the person looks for Claims created for that repository  
**Then** the page shows the path `<directory>/claims`, where `directory` is the `curbpack` value in that repository's `curbpack.json`  
**And** each Claim file there is listed  
**And** a Claim saved for that repository is written in that directory.

A Discovery save with no product repository selected currently falls back to the workspace `product/claims` directory. That directory is not the chosen repository, and this page does not show it. This story does not leave a Claim for the chosen repository there.

### CHK1-R05 — The run uses the copy, the Requirements, and the Claims this page shows

**Given** this page shows one Pack copy, the Requirements that would be checked, and `<that repository>/claims`  
**When** the person runs Check  
**Then** the run reads that Pack copy  
**And** it evaluates the Requirements the page shows as selected  
**And** it reads Claims only from that repository's `curbpack/claims` directory  
**And** a Claim saved by Discover for that same repository and that same Pack copy is one of those files.

Discover already writes there when a product repository is selected. The Check button does not follow the page. It loads every Claim in the repository and ignores the file's `requirements` and `exclude_requirements` lists. A Claim for some other Requirement aborts the run. A Claim saved with no repository selected is written under the workspace `product/claims` directory, which this run does not read.

### CHK1-R06 — A dirty product tree is not a clean commit

**Given** a Check run for the chosen repository  
**When** the product working tree is dirty  
**Then** the result is not reported as verification of a clean commit  
**And** the checked revision is visible when a commit was evaluated.
