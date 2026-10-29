# SYS-03 — Read and write through `curbpack.json` / `curbpack-studio.json`

**Status:** Decided 2026-10-28 by danielfl; scope narrowed 2026-10-29 walkthrough. Not implemented. Required for the pilot.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a pilot user**, I want every Studio view to read and write the product through the paths in this repository’s `curbpack.json`, and Studio operator settings through `curbpack-studio.json`, so the approved app behaviour uses one explicit config.

### What this story is

Wire **where** Packs, Claims, run results, reports, and Studio temp/model settings are read and written.

Authoritative path/config contract: [workspace.md](../../../../reference/workspace.md).

### What this story is not

It does **not** redesign Pack Sources, Pack Editor, Discover (choose existing Claim, diff, candidates), Check, Review, or Extract. Those flows stay as already approved in the running app and their own stories. An implementer must **not** delete or gut that behaviour to “satisfy” this door story.

It does **not** own the created-file shape of `curbpack.json` or the `curbcheck` CLI contract. Those belong to [CHK-07](CHK-07-curbcheck-workspace.md). When the create dialog needs starting values, Studio calls the same defaults function CHK-07 exposes (CLI: `curbcheck --defaults`). Until CHK-07 lands, dialog Save may write the concrete §2.2 values from workspace.md directly, then switch to the shared API without changing the file shape. Rewiring Studio Check/Review pages onto that runner is [CHK-08](CHK-08-studio-check-review-curbcheck.md), after CHK-07.

---

### SYS-R01 — Open repository and `curbpack.json` dialog

One open product repository for Pack Sources, Pack Editor, Discover, Check, and Review. Product I/O uses that repository’s `curbpack.json` ([workspace.md](../../../../reference/workspace.md) §2).

**Given** Pack Sources, Pack Editor, Discover, Check, or Review  
**When** no repository is chosen  
**Then** the view has no product content  
**And** the person is offered a way to choose a repository  

**Given** a chosen repository whose root has no `curbpack.json`  
**When** the person accepts the offer to create one  
**Then** Studio opens a dialog for `curbpack.json` with the fields in workspace.md §2.2  
**And** the dialog has **Save** and **Cancel**  
**And** the dialog matches the style of the Requirements dialog  

**Given** that create dialog with values filled  
**When** the person chooses **Save**  
**Then** Studio writes `<repository>/curbpack.json` with every required §2.2 key set to a concrete value  

**Given** that create dialog  
**When** the person chooses **Cancel**  
**Then** no `curbpack.json` is written  

**Given** a chosen repository that already has `curbpack.json`  
**When** the person opens the same dialog to edit  
**Then** the fields show the file’s current values  
**When** the person chooses **Save**  
**Then** the file is updated  
**When** the person chooses **Cancel**  
**Then** the file is unchanged  

---

### SYS-R02 — Packs and Claims use `packs_dir` and `claims_dir` from `curbpack.json`

Approved Pack Editor / Pack Sources behaviour stays. This requirement only binds paths.

**Given** a chosen repository whose `curbpack.json` `claims_dir` is missing or empty on disk  
**When** Pack Editor opens it  
**Then** the page says there are no Claims  

**Given** that repository  
**When** the person adds a Pack  
**Then** Studio writes `<packs_dir>/<pack-id>/<pack-version>/pack.json` using `packs_dir` from that `curbpack.json`  
**And** it appends the Pack id to that file’s `packs` list  

---

### SYS-R03 — Each field in `curbpack.json` is independent

**Given** repository A and repository B, each with its own `curbpack.json`  
**When** the person sets A’s `packs_dir` to a directory that already contains `<pack-id>/<pack-version>/`  
**Then** A resolves that Pack from A’s `packs_dir`  
**And** B’s `curbpack.json` is unchanged  
**And** A’s Claims continue to come only from A’s `claims_dir`  
**And** saving A’s `packs_dir` does not rewrite Claim files or report files  

---

### SYS-R04 — Discover I/O uses `packs_dir` and `claims_dir` from `curbpack.json`

Approved Discover behaviour stays (candidates in memory, distinguish existing Claim, choose when a Claim already exists, diff before update, create-or-update). This requirement only rebinds directories.

**Given** the open repository’s `curbpack.json`  
**When** the person uses Discover  
**Then** Requirements are offered from Packs selected in that file under its `packs_dir`  
**And** existing Claims are the files in that file’s `claims_dir`  
**And** saving a Claim writes or updates `<claims_dir>/<claim-id>.json`  

---

### SYS-R05 — Check I/O uses `curbpack.json` paths

Approved Check behaviour stays. This requirement only rebinds directories and filenames.

**Given** the open repository’s `curbpack.json`  
**When** the person runs Check  
**Then** the run loads Packs from `packs_dir` and Claims from `claims_dir`  
**And** it writes a new `run-result_<YYYYMMDDTHHMMSSZ>.json` under `results_dir`  
**And** a later run leaves earlier run-result files in place  

---

### SYS-R06 — Review I/O uses `curbpack.json` paths

Approved Review behaviour stays. This requirement only rebinds directories and filenames.

**Given** a run-result file under `results_dir`  
**When** the person compiles a report  
**Then** Compile reads that run and Claims from `claims_dir`  
**And** it writes a new `review-report_<YYYYMMDDTHHMMSSZ>.json` under `reports_dir`  
**And** a later compile leaves earlier report files in place  

---

### SYS-R07 — One open repository on every product view

**Given** a repository chosen on Pack Sources, Pack Editor, Discover, Check, Review, or Studio config  
**When** the person opens any of those views  
**Then** each names that same repository  
**And** choosing a different repository on one view changes all of them  
**And** each view shows the concrete paths in use from that repository’s `curbpack.json` (at least `packs_dir`, `claims_dir`, and, where the view uses them, `results_dir` / `reports_dir`)  
**And** the Studio config page shows the paths from `curbpack-studio.json` when that file is present  

Directory compare / pack-diff as a general tool is **out of this story** (later; see EP-09 / EP-11). Existing Discover claim-diff stays as approved Discover behaviour.

---

### SYS-R08 — Extract still lands in the Pack only on accept

Approved extract / compare / accept behaviour stays. Paths come from `curbpack.json` / `curbpack-studio.json`.

**Given** a Pack under that repository’s `packs_dir`  
**When** extraction finishes  
**Then** new Requirements are in memory or under Studio temp (`curbpack-studio.json` `paths` when present, else current pilot temp)  
**And** they are not yet files in the Pack version directory  
**When** the person accepts  
**Then** the Requirement file is written or updated in that Pack version directory  

---

### SYS-R09 — `curbpack-studio.json` page

Studio operator config for the chosen repository ([workspace.md](../../../../reference/workspace.md) §4).

**Given** a chosen repository  
**When** the person opens the Studio config page  
**And** `curbpack-studio.json` is absent  
**Then** the page offers to create one  
**And** the editor shows workspace.md §4.2 fields  
**And** the editor has **Save** and **Cancel**  

**Given** that editor with values filled  
**When** the person chooses **Save**  
**Then** Studio writes `<repository>/curbpack-studio.json`  

**Given** that editor  
**When** the person chooses **Cancel**  
**Then** no file is written (create) or the existing file is unchanged (edit)  

**Given** a chosen repository that already has `curbpack-studio.json`  
**When** the person opens the Studio config page  
**Then** the editor shows the file’s current values  
**And** **Save** updates that file  

While the file is absent, today’s pilot bind/model/temp wiring stays until Save creates it.

---

### Does not pass

- Product views show product content when no repository is chosen.
- Packs, Claims, runs, or reports are read/written from paths other than this repository’s `curbpack.json` fields.
- `curbpack.json` or `curbpack-studio.json` is created/edited without Save/Cancel.
- Implementing this story removes approved Discover / Check / Review / Extract behaviour (choose existing Claim, diff, candidates, etc.).

### Stop if

Stop when a step would redesign an approved product flow instead of rebinding its paths, invent config keys outside workspace.md §2.2 / §4.2, or store path fields only in Studio workspace state. Record the step.
