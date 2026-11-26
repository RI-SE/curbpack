# UP-07 — Update Pack view and low-rework end-to-end scenario

**Epic:** [EP-15 — Update Pack](../EPIC.md)  
**Status:** Draft  
**Starts when:** UP-01 through UP-06 accepted.

**As a product team**, I want one intelligible Update view that walks me from a new upstream version to precisely the decisions I must make, so that I can maintain compliance evidence with minimal avoidable human rework.

## Behavior

Add a **thin TypeScript Update Pack page** owned by `studio/pack/pages/`, linked from Pack selection/list/detail. Use the component's HTTP adapter/router (consistent with current EP-02 stage); no business logic in UI or server. Provide:

1. Current LOCAL Pack, declared source version, chosen BASE and imported NEW, identities and independent source-signature/provenance readings.
2. Read-only overview: exact changed/unchanged/new/removed Requirements; local-only edits and conflicts; counts for potentially affected Claims.
3. Drilldown: three-way old/local/new per Requirement/field, with existing Compare visual controls and explicit Keep local / Take upstream / Resolve conflict, including add/remove decisions.
4. Pre-apply result and **Review affected Claims** list recalculated as choices change; show `match/stale/missing` separately from 'Review suggested' and Check outcome.
5. Explicit Confirm Apply, Cancel; a new local copy and clear return links to Requirement editor, Claims Review/Rebind, Discovery and Check/Review.
6. No update polling, no update status database, no implicit trust/approval or auto-run Checks.
7. Current Git status of the open product repository, as **clean**, **uncommitted changes**, or **unavailable** when that status cannot be read. The reading is information about the repository now. It is a different fact from Git status recorded on an earlier Check run, and the view must not present the two as the same fact. Uncommitted changes, and unavailable status, do not block version selection, preview, Confirm Apply, or the links onward. Update does not commit, stash, branch, or push. The customer keeps their own Git process.

Screen text must never label the 'unaffected Claims count' as legal proof, nor imply that an unreviewed stale Claim is a current binding. Failure/errors must preserve entered selections, originals and context. On small screens the list remains usable; accessibility includes keyboard controls and readable long law-text differences.

## Acceptance — Given / When / Then

### GWT-01 — Realistic fixture and measured impact
**Given** a signed upstream RISE 1.0, a locally owned A copy with local changes and Claims, and upstream RISE 1.1 with a mix of normative edits, hints-only changes, additions, removals and conflict  
**When** the user opens Update and selects changes  
**Then** the preview matches a hand-authored expected delta/impact oracle and the worklist contains only relevant Claim identities.

### GWT-02 — Whole interactive flow
**Given** the above fixture in an open product repository  
**When** the user selects version, resolves a conflict, applies, inspects a Claim, deliberately rebinds and runs Checks  
**Then** the correct working copy and Run Result are shown in existing Review; original source and prior signed reports remain unchanged.

### GWT-03 — Cancel, errors and stale input
**Given** any preview with user selections  
**When** Cancel, missing BASE, malicious path, conflicting namespace or stale-on-disk changes occurs  
**Then** error/exit is clear, no partial copy is selected, and prior files remain intact.

### GWT-04 — No automatic rework
**Given** a Pack update changes only 2 of 20 Requirements with Claims  
**When** the update is accepted  
**Then** Claims for the other 18 Requirements remain byte-identical and absent from the required-action subset; exact `stale`/`match` outcomes are accurate.

### GWT-05 — Trust/abuse scenario
**Given** a purportedly RISE-derived Pack with altered `origin`, missing source or invalid source signature  
**When** Update displays origin checks  
**Then** the UI displays asserted vs authenticated facts without treating a signed derivative as a verified upstream lineage.

### GWT-06 — Platform and regression
**Given** completed implementation  
**When** focused backend, HTTP/browser integration and full `make test` run, followed by pilot package smoke tests where supported  
**Then** verified outcomes are recorded; existing Extract/Import/Compare/Take Ownership/Claims/Discovery/Curbcheck/Review and packaging remain functional.

### GWT-07 — Current product Git status
**Given** an open product repository that is clean, has uncommitted changes, or whose Git status cannot be read  
**And** zero or more earlier Check runs recorded their own Git status for that repository  
**When** the user opens Update  
**Then** the view shows the current status as clean, uncommitted changes, or unavailable  
**And** that reading is identified as the open product repository now, not as the Git status recorded on a Check run.

### GWT-08 — Git status does not gate Update
**Given** the open product repository has uncommitted changes, or its Git status is unavailable  
**When** the user selects versions, previews, and confirms Apply  
**Then** those steps stay available  
**And** Update does not commit, stash, branch, or push.

**Done when:** A real user can complete RISE 1.0→1.1 update with an A-local copy, understand the exact consequences and process only the affected Claims without hidden artifact mutation. Uncommitted product changes are reported and do not block that path.
