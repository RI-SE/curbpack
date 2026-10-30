# REV-03 — Review run results by Requirement

**Status:** Draft  
**Epic:** EP-01 — Complete Functional Pilot  
**Depends on:** SYS-03 and the existing Packs v2 contracts for run results, review reports, Claims, Requirements, decisions and seals.

## Story

**As a reviewer**,  
I want to open a curbcheck run result, review its Claims grouped by Requirement, record my decision, compile the review and seal the resulting review report,  
so that the automated results, current repository state and human judgement remain distinguishable and traceable.

## Current state

Review presents affected Claims as a flat queue.

The current UI can show a Claim, its evidence paths, Check results and failure details. Inspect can show the related Requirement and open referenced files. The current action named `Re-hunt` starts a new Discovery for the Requirement.

The current UI does not yet provide the intended Requirement-centred workflow for:

- selecting a curbcheck run result;
- reviewing all represented Claims by Requirement;
- distinguishing run-result data from current repository state;
- recording the reviewer's decision;
- compiling and sealing a review report;
- reopening an existing review report.

Exact scored-excerpt highlighting is not derivable from the current run-result fixture and is deferred.

## Desired state

Review follows the same repository-selection pattern as the other Studio pages.

The page shows the selected repository and the effective paths read from its `curbpack.json`:

- current configuration;
- Packs directory;
- Claims directory;
- Results directory;
- Reports directory.

Review supports two entry paths:

1. **Review a run result** from the configured Results directory.
2. **Open an existing review report** from the configured Reports directory.

The normal pilot flow is:

1. select a curbcheck run result;
2. review its Claims grouped by Requirement;
3. inspect failures and current repository state;
4. Compile a review report containing the embedded run result and embedded review-time objects;
5. save the reviewer's `decision` in the compiled review report;
6. seal the review report using the existing Packs v2 `signed` contract.

A sealed report is not necessarily approved. The meaning of the review is carried by `decision`. `signed` seals the report content and identity facts; it does not turn the decision into approval and does not turn failed or skipped Checks into pass.

When Check opens Review for a specific run result, that result is preselected. If no compiled review report exists yet, Review opens the run-result workflow rather than reporting an error.

A compiled review report is reopened from the Reports directory using its embedded `run_result`, Requirements, Claims and reviewer decisions. Historical grouping comes from the embedded review-time objects and does not depend on today's mutable Claim files.

## Data boundaries

### Run result

A curbcheck run result is read from the configured Results directory. It is the historical machine result and can contain:

- `claims[]`;
- each result Claim's `id`, `digest`, `status` and `checks[]`;
- each Check's `check`, `index`, `args`, `status` and optional `detail`;
- `packs[]` with Pack `id`, `version` and `digest`;
- `commit`;
- `worktree`;
- `tool`;
- `tool_version`.

A run result is not a review report and is not selected from the Reports directory.

### Review report

A compiled review report is read from and written to the configured Reports directory. It contains the existing Packs v2 review-report fields, including:

- the embedded `run_result`;
- embedded review-time Requirements and Claims;
- the reviewer's `decision`;
- `signed` when the report has been sealed.

The existing Packs v2 names and shapes are authoritative. This story does not introduce a second report schema.

### Current repository state

While reviewing a raw run result, Review resolves the current Claim by the run-result Claim `id`. The Claim's canonical `requirement_id` is used to resolve and group the current Requirement.

Current objects provide present-day context. They do not replace the objects or results captured by the selected run result or compiled review report.

## Presentation rules

- Requirements are the top-level items in the review list.
- A Requirement is collapsed initially only when all contained Claim and Check results are `pass` and none of the explicitly defined attention conditions below applies.
- A Requirement is expanded initially when any contained Claim or Check is `fail` or `skipped`.
- A Requirement is also expanded initially when: the current Claim digest differs from the run result; the current Claim cannot be resolved; the Claim exists but its `requirement_id` cannot be resolved; a compiled report shows that the current Claim has changed Requirement; a recognised path-bearing Check refers to evidence that is currently missing; or a Requirement, Claim or review report has an invalid seal.
- `Verification unavailable` and `Untrusted signer` are shown clearly but do not by themselves force expansion. `Unsigned` does not by itself force expansion in the pilot.
- The reviewer can expand or collapse every Requirement manually.
- `pass`, `fail` and `skipped` are distinct. `skipped` is never presented as pass.
- Requirement seal state, Claim seal state, machine result, reviewer decision and review-report seal state are separate UI concepts.
- Summary labels may be used, but the five verification facts required by the existing Packs v2 seal contract remain available to the reviewer.
- A Git-signed commit can provide the applicable seal according to the existing Packs v2 rules. Missing trusted certificate material is distinguished from a cryptographically invalid seal.
- Unknown or unresolvable run-result Claims are shown in an always-visible expanded `Unresolved Claims` group.
- File links are created only for path arguments recognised by the current Check registry contract described below.
- Edit opens the existing Claims Editor for the affected Claim and Check. Review does not implement a second inline Check editor.
- Exact scored-excerpt highlighting is outside this story.

## Path-argument contract for the pilot

The current Check registry has argument schemas but no explicit `path-bearing` annotation. The pilot therefore uses an explicit Review adapter for the currently supported built-in Checks:

- `exist`: `args.paths[]` are repo-relative file paths;
- `contents`: `args.path` or `args.paths[]` are repo-relative file paths;
- `dep_ban`: has no file path.

An unknown Check type is rendered with its recorded `args`, `status` and optional `detail`, but Review does not guess file links from arbitrary strings. Adding path metadata to the Check registry is deferred.

## Scenarios

### Scenario 1 — Open Review with a selected repository

**Given** a repository has been selected through shared repository selection  
**And** the repository contains a readable `curbpack.json`  
**When** the reviewer opens Review  
**Then** Review shall use the selected repository  
**And** Review shall show the effective configuration, Packs, Claims, Results and Reports paths  
**And** Review shall not use hard-coded result or report locations.

### Scenario 2 — Change repository

**Given** Review is showing a repository and selected document  
**When** the reviewer selects another repository  
**Then** Review shall read the new repository's `curbpack.json`  
**And** update all effective paths  
**And** list run results from its Results directory  
**And** list review reports from its Reports directory  
**And** clear a selection that does not belong to the new repository.

### Scenario 3 — List run results and review reports separately

**Given** the selected repository has usable Results and Reports directories  
**When** Review loads the repository  
**Then** Review shall present curbcheck run results as review inputs  
**And** present compiled review reports as existing reviews  
**And** shall not describe a run result as a review report  
**And** shall not search the Reports directory for raw run results.

### Scenario 4 — Open a run result supplied by Check

**Given** Check has written a run result to the configured Results directory  
**When** the reviewer navigates from Check to Review for that run result  
**Then** that exact run result shall be preselected and opened  
**And** the reviewer shall still be able to select another run result from the same repository.

### Scenario 5 — Check has run but no review report exists

**Given** a selected run result exists in the Results directory  
**And** no compiled review report exists for that run result  
**When** Review opens the run result  
**Then** Review shall start a new review from the run result  
**And** shall not report the missing review report as an error  
**And** shall not create a review report until the reviewer invokes Compile.

### Scenario 6 — Open an existing review report

**Given** the Reports directory contains a readable compiled review report  
**When** the reviewer selects that review report  
**Then** Review shall open its embedded review-time Requirements, Claims, run result and decisions  
**And** shall preserve their historical grouping  
**And** shall not regroup the report using today's mutable Claim files.

### Scenario 7 — Show run context

**Given** a run result is open directly or through a review report  
**When** Review renders the header  
**Then** Review shall show `tool`, `tool_version`, `commit`, `worktree` and recorded Pack `id` and `version` values  
**And** a dirty worktree shall be visible but shall not be presented as a failed Check.

### Scenario 8 — Resolve a run-result Claim

**Given** the selected raw run result contains a Claim entry with `id`  
**When** Review loads the entry  
**Then** Review shall resolve the current Claim with the same `id` from the configured Claims directory  
**And** retain the run-result entry as historical machine data  
**And** not replace recorded results with current Claim data.

### Scenario 9 — Group a resolved Claim by its canonical Requirement

**Given** a current Claim has been resolved for a raw run-result entry  
**And** the Claim contains canonical `requirement_id`  
**When** Review builds the Requirement list  
**Then** Review shall resolve that Requirement using Packs v2  
**And** group the Claim under that Requirement  
**And** shall not infer Requirement identity from the Claim id string.

### Scenario 10 — Current Claim has changed Requirement since a compiled review

**Given** a compiled review report is open  
**And** the embedded review-time Claim is grouped under its embedded review-time Requirement  
**And** a current Claim with the same `id` can be resolved  
**And** the current Claim's `requirement_id` differs from the embedded review-time relationship  
**When** Review renders the report  
**Then** historical grouping shall remain under the embedded review-time Requirement  
**And** the current relationship shall be shown as changed  
**And** Review shall not silently move historical results to the current Requirement  
**And** a new curbcheck run shall be required for a new result.

### Scenario 10a — Raw run result cannot establish the previous Requirement relationship

**Given** a raw run result is open  
**And** the current Claim digest differs from the run-result digest  
**When** Review resolves the current Claim and its current `requirement_id`  
**Then** Review may show the current Requirement as present-day context  
**And** Review shall state that the previous Requirement relationship cannot be established from the raw run result  
**And** Review shall not claim that the Claim changed Requirement without a historical Claim object.

### Scenario 11 — Run-result Claim cannot be resolved

**Given** a raw run result contains a Claim `id`  
**And** no current Claim with that `id` can be resolved  
**When** Review renders the run result  
**Then** Review shall retain the Claim entry and recorded Checks  
**And** place the entry in an always-visible expanded `Unresolved Claims` group  
**And** shall not invent a Requirement from the Claim id  
**And** shall not present the current repository as passing that Claim.

### Scenario 11a — Claim exists but Requirement cannot be resolved

**Given** a current Claim has been resolved for a raw run-result entry  
**And** its canonical `requirement_id` cannot be resolved using Packs v2  
**When** Review renders the run result  
**Then** Review shall retain the Claim and its recorded Checks  
**And** place the Claim in an always-visible expanded `Unresolved Claims` group  
**And** identify the unresolved `requirement_id`  
**And** shall not invent Requirement text or grouping  
**And** shall show the condition as requiring attention.

### Scenario 12 — Collapse a fully passing Requirement

**Given** all contained Claim and Check results are `pass`  
**And** no current red condition exists  
**When** Review initially renders the Requirement  
**Then** the Requirement shall be collapsed  
**And** its identity, Requirement seal summary and result summary shall remain visible.

### Scenario 13 — Expand a Requirement containing fail

**Given** a contained Claim or Check has `status: fail`  
**When** Review initially renders the Requirement  
**Then** the Requirement shall be expanded  
**And** each failed result shall be red  
**And** its recorded `detail` shall be shown when present.

### Scenario 14 — Expand a Requirement containing skipped

**Given** no contained result is `fail`  
**And** at least one contained Claim or Check has `status: skipped`  
**When** Review initially renders the Requirement  
**Then** the Requirement shall be expanded  
**And** `skipped` shall be visibly distinct from `pass` and `fail`  
**And** its recorded `detail` shall be shown when present  
**And** Review shall not count or describe the skipped result as pass.

### Scenario 15 — Manually expand or collapse a Requirement

**Given** a Requirement is visible  
**When** the reviewer clicks its header  
**Then** Review shall toggle its expanded state  
**And** shall not change any machine result, decision or seal.

### Scenario 16 — Preserve expansion state

**Given** the reviewer has manually expanded or collapsed a Requirement  
**When** the reviewer opens and closes a file, Inspect or the Claims Editor  
**Then** Review shall preserve the selected repository, document and expansion state.

### Scenario 17 — Show Requirement and Claim seal summaries

**Given** a Requirement and Claim can be resolved  
**When** Review renders them  
**Then** Review shall show separate Requirement and Claim seal summaries  
**And** each summary shall use the existing Packs v2 verification result  
**And** neither summary shall be presented as a Check result or review decision.

### Scenario 18 — Verify an explicit `signed` seal

**Given** a Requirement, Claim or review report contains `signed`  
**When** Review verifies the seal  
**Then** Review shall use the existing Packs v2 verification contract  
**And** make the five prescribed verification facts available  
**And** distinguish a valid seal from invalid content, invalid signature and untrusted or unavailable certificate material.

### Scenario 19 — Recognise a Git-signed commit seal

**Given** an object has no explicit `signed` value  
**And** Packs v2 permits the applicable Git-signed commit to provide the seal  
**When** Review determines seal state  
**Then** Review shall verify the Git seal using the existing implementation  
**And** shall not label the object `Unsigned` solely because `signed` is absent  
**And** shall expose the applicable verification facts.

### Scenario 20 — No usable seal exists

**Given** neither a valid explicit `signed` seal nor an applicable valid Git seal can be established  
**When** Review renders the object  
**Then** Review shall show a precise summary such as `Unsigned`, `Verification unavailable`, `Untrusted signer` or `Invalid seal` according to the existing verification result  
**And** shall not reject the object in this pilot  
**And** shall not change any recorded Check result.

### Scenario 21 — Current Claim matches the run result

**Given** a run-result Claim contains `digest`  
**And** the current Claim can be resolved  
**When** its digest, using curbcheck's canonicalisation, equals the recorded `digest`  
**Then** Review shall show the Claim as unchanged since the Check run.

### Scenario 22 — Current Claim changed after the run

**Given** a run-result Claim contains `digest`  
**And** the current Claim can be resolved  
**When** its current digest differs from the recorded `digest`  
**Then** Review shall show `Claim changed since Check`  
**And** expand the affected Requirement  
**And** retain the recorded results  
**And** not imply that those results apply to the changed Claim  
**And** require a new curbcheck run for new results.

### Scenario 23 — Show recorded Checks

**Given** a run-result Claim contains `checks[]`  
**When** Review renders the expanded Claim  
**Then** Review shall show every recorded Check's `check`, `index`, `args`, `status` and optional `detail`  
**And** preserve multiple Checks and multiple paths  
**And** not invent a Requirement-level Check.

### Scenario 24 — Render known path-bearing Checks

**Given** a recorded Check is `exist` or `contents`  
**When** Review renders its recorded arguments  
**Then** Review shall use the pilot adapter to identify `args.path` or `args.paths[]` as applicable  
**And** show every repo-relative file path  
**And** make currently available paths selectable  
**And** mark currently missing paths without changing the historical result.

### Scenario 25 — Render a `dep_ban` Check

**Given** a recorded Check is `dep_ban`  
**When** Review renders it  
**Then** Review shall show its package and banned-version arguments  
**And** shall not invent a file path or file link.

### Scenario 26 — Render an unknown Check type

**Given** a recorded Check type is not covered by the pilot adapter  
**When** Review renders it  
**Then** Review shall show its recorded `args`, `status` and optional `detail`  
**And** shall not guess which strings are file paths  
**And** shall not create file links from unrecognised arguments.

### Scenario 27 — Open an available file

**Given** a recognised path-bearing Check refers to a file inside the selected repository  
**And** the file currently exists  
**When** the reviewer selects the path  
**Then** Review shall open the file in a dialog  
**And** identify its repo-relative path  
**And** show readable file content  
**And** return to the same review state when closed  
**And** shall not require exact excerpt highlighting in this story.

### Scenario 28 — Refuse a path outside the repository

**Given** a recorded path resolves outside the selected repository  
**When** the reviewer attempts to open it  
**Then** Review shall refuse the path  
**And** identify it as invalid  
**And** not display content outside the repository.

### Scenario 29 — Open the existing Claims Editor

**Given** a recorded Check can be matched unambiguously to the current Claim Check by digest, `index` and `check`  
**When** the reviewer selects Edit  
**Then** Review shall open the existing Claims Editor for that Claim and Check  
**And** the editor shall show the current `check` and `args`  
**And** Review shall not implement a separate inline Check editor.

### Scenario 30 — Recorded Check cannot be matched safely

**Given** the Claim digest differs  
**Or** the recorded `index` does not identify a current Check  
**Or** the current `check` value differs from the recorded value  
**When** Review renders the historical Check  
**Then** Review shall retain the recorded result  
**And** identify that the current Check cannot be matched safely  
**And** not offer an ambiguous Edit action.

### Scenario 31 — Save through Claims Editor

**Given** the reviewer has opened a safely matched Check in Claims Editor  
**When** the reviewer saves a change  
**Then** Claims Editor shall update the current Claim using its existing workflow  
**And** the old seal shall no longer verify for changed signed content  
**And** the selected run result or review report shall remain unchanged  
**And** a new curbcheck run shall be required.

### Scenario 32 — Re-Discover evidence

**Given** a Claim remains available  
**And** referenced evidence is missing, moved or unsuitable  
**When** the reviewer selects Re-Discover  
**Then** Discovery shall open for the Claim's Requirement in the selected repository  
**And** the existing Claim, run result and review report shall remain unchanged  
**And** accepting evidence shall use the ordinary Claim workflow  
**And** a new curbcheck run shall be required.

### Scenario 33 — Compile a review report

**Given** a run result is selected  
**And** Compile can resolve the exact Claim versions checked by curbcheck with matching digests  
**When** the reviewer invokes Compile  
**Then** Review shall create a new review report in the configured Reports directory  
**And** embed the run result and the required review-time Requirements and exact checked Claims  
**And** create the report without a reviewer `decision`  
**And** not overwrite the run result  
**And** not overwrite an earlier review report.

### Scenario 34 — Compile cannot recover the exact checked Claim

**Given** a run-result Claim cannot be resolved  
**Or** the available current Claim does not match the run-result `digest`  
**And** no exact checked Claim version is otherwise available to Compile through the existing provenance mechanism  
**When** the reviewer invokes Compile  
**Then** Compile shall stop without writing a review report  
**And** explain which Claim has a provenance gap  
**And** shall not embed today's changed Claim as though it were the checked Claim  
**And** shall not write a partial or incomplete review report  
**And** shall preserve the run result unchanged.

### Scenario 35 — Save the reviewer's decision in a compiled report

**Given** a compiled review report exists  
**And** the report has not yet been sealed  
**When** the reviewer records and saves a decision  
**Then** Review shall store the decision using the existing review-report `decision` contract  
**And** shall not encode the decision by changing Check statuses  
**And** shall allow the decision to approve, request changes or otherwise state the review outcome supported by the existing contract.

### Scenario 35a — Seal a compiled review report

**Given** a compiled review report contains the intended `decision`  
**When** the reviewer invokes the existing signing action  
**Then** the report shall be sealed using the existing Packs v2 `signed` contract  
**And** the seal shall cover the report content including `decision`  
**And** Review shall distinguish `Report sealed` from the meaning of the decision  
**And** sealing shall not convert `fail` or `skipped` to `pass`.

### Scenario 36 — Detect a changed sealed report

**Given** a review report has a valid seal  
**When** content covered by the seal is changed afterward  
**Then** subsequent verification shall not show the report as validly sealed  
**And** Review shall identify the verification failure according to the existing Packs v2 contract  
**And** shall retain the report's recorded machine results and decision text for inspection.

### Scenario 37 — Reopen a sealed review report

**Given** a sealed review report exists in the Reports directory  
**When** the reviewer opens it  
**Then** Review shall show its historical grouping, embedded objects, run result, decision and seal verification  
**And** shall not reinterpret `signed` as approval  
**And** shall not silently replace embedded objects with current repository objects.

### Scenario 37a — Invalid preselected document is not silently replaced

**Given** Review is opened with a preselected run-result or review-report path  
**And** the requested document is absent, unreadable or outside the configured directory for that document type  
**When** Review attempts to open it  
**Then** Review shall identify the requested document and its expected type  
**And** shall not silently select another run result or review report  
**And** shall keep the selected repository unchanged.

## Error scenarios

### Scenario 38 — `curbpack.json` cannot be read

**Given** a repository is selected  
**And** `curbpack.json` is missing or invalid  
**When** Review opens  
**Then** Review shall name `curbpack.json` in the error  
**And** shall not guess directory locations.

### Scenario 39 — Results directory is unavailable

**Given** the configured Results directory cannot be used  
**When** Review lists run results  
**Then** Review shall identify the unavailable Results directory  
**And** shall not search the Reports directory as a fallback.

### Scenario 40 — Reports directory is unavailable

**Given** the configured Reports directory cannot be used  
**When** Review lists or writes review reports  
**Then** Review shall identify the unavailable Reports directory  
**And** shall not search or write to the Results directory as a fallback.

### Scenario 41 — No run results exist

**Given** the Results directory contains no run results  
**When** Review opens the new-review path  
**Then** Review shall show an empty state  
**And** shall not interpret the absence as a passing review.

### Scenario 42 — Selected document cannot be read

**Given** a listed run result or review report cannot be parsed or read  
**When** the reviewer selects it  
**Then** Review shall identify the exact document and type that failed  
**And** shall not present partial data as complete  
**And** shall not silently select another document.

## Acceptance fixture

Use the supplied curbcheck run result as the base fixture:

- 13 Claim results;
- 19 recorded Checks;
- one failing Claim;
- Checks with multiple paths;
- a `dep_ban` Check without a file path.

Extend the fixture set with:

- one `skipped` Check with `detail`;
- one run-result Claim whose current Claim file is absent;
- one current Claim whose digest differs from the run result;
- one current Claim whose `requirement_id` changed after the run;
- one compiled review report containing embedded review-time objects and `decision`;
- one valid sealed review report;
- one sealed review report changed after sealing;
- Git-sealed, untrusted-certificate and invalid-seal verification cases.

## Deferred beyond the pilot

- Exact scored-excerpt highlighting.
- Full completeness comparison between a run result and every current Requirement and Claim.
- A separate completeness or coverage Tool.
- Registry-level metadata declaring path-bearing arguments.
- Automatic rerunning of curbcheck from Review.
- Inline Check editing inside Review.
- Automatically replacing, rebinding or deleting Claims.
- Rejecting unsigned Requirements or Claims.
- Changing historical run results or compiled review reports when current objects change.
- Changes to Packs v2 object shapes or the existing seal contract.

## Implementation guardrails

- Use the existing Packs v2 names and fields, including canonical Claim `requirement_id`, review-report `decision` and `signed`.
- Keep Results directory run results separate from Reports directory review reports.
- Do not equate `signed` with approved.
- Do not equate missing `signed` with unsigned until the applicable Git seal has also been considered.
- Do not collapse `Verification unavailable`, `Untrusted signer` and `Invalid seal` into one false status.
- Do not infer Requirement identity from a Claim id string.
- Do not treat `skipped` as `pass`.
- Do not guess file paths from arbitrary Check arguments.
- Open the existing Claims Editor for edits.
- Do not mutate historical documents while browsing, editing current Claims or using Re-Discover.
