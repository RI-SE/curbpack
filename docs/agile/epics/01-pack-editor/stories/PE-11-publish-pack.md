# PE-11 — Export a Pack directory

**Status:** Approved for pilot implementation, 2026-10-28, danielfl.

**Epic:** [EP-01 Pack Editor](../EPIC.md)

**Replaces:** The unaccepted pilot story `PE-11 — Publish a Pack`.

**As a Pack editor**, I want to export the currently selected Pack working copy to a directory so that it can be inspected, transferred, committed, or used as a Packs v2 Pack root without pretending that the pilot has a publication service.

## Pilot decision

The EP-01 pilot implements **Export Pack**, not publisher **Publish release**.

Export writes a directory containing the selected working copy's existing Packs v2 files. The export may contain signed or unsigned Requirements and a signed or unsigned `pack.json`. Export does not assign a version, sign an object, seal a directory, create an immutable release, write under `published/`, fetch anything, or register the Pack anywhere.

Maintainer decision 2026-10-28: if `<destination>/<pack-id>/` already exists, the person overwrites that directory or enters another one. Export does not change it until they choose overwrite. Overwrite replaces the directory. It does not merge it.

A future publication workflow remains separate. Pack exchange as a zip and import of purchased releases remain in EP-11 (`VL-05` and `VL-06`) and are not implemented by this story.

## Packs v2 shape used by this story

The exported Pack is a normal Packs v2 directory:

```text
<chosen-destination>/
  <pack-id>/
    pack.json
    <requirement-file>.json
    ...
```

`pack.json` is metadata. Requirement membership is determined by each Requirement's `pack_id`. Requirement files are directly beside `pack.json`; this story does not introduce a `requirements/` subdirectory or an export manifest.

The chosen destination is therefore a **packs root**. A consumer can resolve the exported Pack as:

```text
<chosen-destination>/<pack-id>/pack.json
```

Only the Pack files belonging to the selected working copy are exported. Extraction diagnostics, temporary files, jobs, comparison previews, workspace catalogues, keys, Claims, product configuration, run results and review reports are not Pack files and are not exported.

## Acceptance summary

Accept when **Export Pack** acts on the selected Pack working copy, lets the person choose a destination directory, creates `<destination>/<pack-id>/`, copies the valid Packs v2 files without changing their bytes, reports signature/seal status without creating approval, refuses malformed or inconsistent input, overwrites an existing export only when the person chooses that, and leaves the source working copy unchanged.

## Requirements (Given / When / Then)

### PE11-R01 — Export is a Pack-level action

**Given** the Pack Sources page shows a Pack row  
**When** the person activates **Export Pack** on that row  
**Then** Studio opens the export flow for that Pack  
**And** the flow identifies the Pack id and the selected working-copy timestamp or path  
**And** the action is not attached to an individual source row or Requirement  
**And** the visible control has a working action rather than being an unhandled `<button type="button">`.

### PE11-R02 — The selected working copy is explicit

**Given** the Pack has one or more dated working copies  
**When** Export Pack opens  
**Then** Studio shows which working copy will be exported  
**And** Export uses exactly that selected working copy  
**And** Studio does not silently substitute the latest copy, a published directory, or another Pack.

**Given** no complete working copy is selected  
**When** the person attempts Export Pack  
**Then** Studio refuses the export with a message identifying the missing selection  
**And** no destination files are written.

### PE11-R03 — The person chooses a destination root

**Given** Export Pack is open for a selected working copy  
**When** the person chooses or enters a writable destination directory and confirms Export  
**Then** Studio creates `<destination>/<pack-id>/`  
**And** Studio reports the final absolute export path  
**And** Studio does not require the destination to be inside the Studio workspace.

**Given** the destination does not exist, is not a directory, or is not writable  
**When** Export is confirmed  
**Then** Studio reports the destination problem  
**And** no partial Pack directory remains.

The implementation may use the platform's directory chooser or the pilot's existing local-path input. Tests must exercise the operation beneath the UI without requiring an interactive operating-system dialog.

### PE11-R04 — Export uses the existing Packs v2 directory shape

**Given** a working copy containing `pack.json` and one or more Requirement JSON files directly beside it  
**When** Export succeeds  
**Then** `<destination>/<pack-id>/pack.json` exists  
**And** every exported Requirement file is directly beside `pack.json`  
**And** every exported Requirement has `pack_id` equal to the exported Pack's `id`  
**And** no `requirements/` subdirectory is invented  
**And** no export-specific manifest or second Pack schema is invented.

### PE11-R05 — Only Pack files are exported

**Given** the selected extraction or workspace also has diagnostics or operational files  
**When** Export succeeds  
**Then** the export contains only `pack.json` and the Requirement JSON files belonging to that Pack  
**And** it excludes at least:

- extraction diagnostics and model-call data;
- coverage and comparison previews;
- job state and temporary files;
- workspace catalogues and UI state;
- signing keys;
- `curbpack.json` and `claims/` from a product repository;
- Check run results and review reports.

### PE11-R06 — Input is validated before writing the destination

**Given** a selected working copy  
**When** Export is confirmed  
**Then** Studio validates `pack.json` and each Requirement with the existing Packs v2 validator before making the final export visible  
**And** it rejects a missing or malformed `pack.json`  
**And** it rejects a missing Pack id  
**And** it rejects an invalid Requirement object  
**And** it rejects a Requirement whose `pack_id` does not equal the selected Pack id  
**And** it rejects an empty or incomplete extraction directory that is not a complete working copy  
**And** validation failure leaves no final or partial export directory.

This story does not add new validation fields or reinterpret Packs v2. If the existing validator and `docs/reference/packs2.md` conflict, stop and record the conflict instead of inventing an export-only rule.

### PE11-R07 — Signed and unsigned Packs can both be exported

**Given** the selected working copy contains unsigned Requirements, signed Requirements, or both  
**When** Export Pack opens  
**Then** Studio shows counts for signed and unsigned Requirements  
**And** Studio shows the existing signature reading for `pack.json` or reports that the Pack is unsigned  
**And** lack of a Requirement signature or Pack seal does not by itself block export  
**And** the UI does not describe an unsigned export as approved, published, or verified.

**Given** a `signed` block is present  
**When** Studio can verify it using the existing local trust input  
**Then** the existing Packs v2 signature reading is shown  
**And** Export does not replace that reading with a new status vocabulary.

**Given** a signature is present but does not verify  
**When** Export is attempted  
**Then** Studio reports that exact verification result before confirmation  
**And** it does not repair, remove, or recreate the signature  
**And** it does not claim that Export verified the Pack.

### PE11-R08 — Export preserves Pack bytes

**Given** a valid selected working copy  
**When** Export succeeds  
**Then** every exported Pack file is byte-for-byte equal to its source file  
**And** existing `signed` blocks remain byte-for-byte unchanged  
**And** `pack.version`, Requirement `origin`, source editions and legal passages remain unchanged  
**And** Export does not add timestamps, paths, status fields, digests, signatures, seals, or export metadata to Pack files.

### PE11-R09 — Overwrite an existing export, or choose another directory

**Given** `<destination>/<pack-id>/` already exists  
**When** the person confirms Export without choosing overwrite  
**Then** Studio leaves that directory unchanged  
**And** it identifies the conflicting target path  
**And** the person can choose **Overwrite** or enter another destination  
**And** the person can cancel.

**Given** `<destination>/<pack-id>/` already exists  
**When** the person confirms **Overwrite**  
**Then** Studio replaces that directory with the exported Pack  
**And** the result is the exported Pack files, not a merge with files that were already there  
**And** other directories directly under the destination stay in place  
**And** the source working copy is unchanged.

### PE11-R10 — Export is atomic from the user's perspective

**Given** validation succeeds and the target Pack directory does not exist  
**When** Studio exports the Pack  
**Then** it first writes to a unique temporary directory beneath the chosen destination  
**And** it verifies the temporary copy has the expected files and source-equivalent bytes  
**And** it places the completed temporary directory at `<destination>/<pack-id>/`  
**And** a failure before that placement removes the temporary directory  
**And** when the person chose overwrite, the previous `<destination>/<pack-id>/` stays in place until the temporary copy has been verified.

### PE11-R11 — Export does not mutate the source

**Given** a selected working copy and a snapshot of its file bytes  
**When** Export succeeds or fails  
**Then** every source Pack file remains byte-identical to the snapshot  
**And** the working-copy timestamp or identity is unchanged  
**And** `pack.version`, `origin`, signatures and the Pack seal are unchanged  
**And** no new working copy or published release is created.

### PE11-R12 — A previous export does not track later edits

**Given** a successful export  
**When** the source working copy is later edited, re-extracted, signed or sealed  
**Then** the earlier exported directory remains byte-identical to the completed export  
**And** Studio does not update it in place.

### PE11-R13 — Export is not publication

**Given** a successful export  
**When** Studio reports the result  
**Then** the operation and result are called **Export** and **exported Pack**  
**And** Studio does not say that the Pack was published, released, approved or registered  
**And** Studio does not create `published/<pack-id>/<version>/`  
**And** Studio does not assign or request a new `pack.version`  
**And** Studio does not sign a Requirement or seal the Pack directory  
**And** Studio does not make an immutability claim about the external destination.

### PE11-R14 — Exported Pack can be loaded as a Pack root

**Given** Export succeeds to `<destination>/<pack-id>/`  
**When** the existing Pack loader is given `<destination>` as its packs root and selects `<pack-id>`  
**Then** it resolves `<destination>/<pack-id>/pack.json`  
**And** it loads the Requirement files beside `pack.json`  
**And** it obtains the same Pack id, `pack.version`, Requirement ids and Pack-directory digest as a direct load of the exported bytes  
**And** Export itself does not alter a product repository's `curbpack.json`.

### PE11-R15 — The obsolete baseline help does not imply publication

**Given** the Pack Sources page currently describes Git baselines and shows both timestamped working copies and `published/<pack-id>/<version>/`  
**When** this story is implemented  
**Then** that page no longer presents the unimplemented Publish action as part of the pilot's working flow  
**And** Git workspace history is described separately from Export  
**And** the page does not display a developer-specific absolute workspace path as if it were the portable data contract  
**And** any retained Git example labels its path as an installation-specific example  
**And** the page links to the governing Packs v2 or workspace documentation rather than defining a competing layout.

## Test evidence required

The implementation must add tests that prove at least the following:

1. The Pack-row action opens Export for the correct Pack and selected working copy.
2. A valid Pack with two Requirement files exports to `<destination>/<pack-id>/`.
3. Exported files are byte-for-byte equal to their source files.
4. The exported directory can be loaded by the existing Pack loader using `<destination>` as the packs root.
5. An unsigned Pack and mixed signed/unsigned Requirements can be exported without being called published.
6. A malformed `pack.json` is rejected without destination residue.
7. A Requirement with the wrong `pack_id` is rejected without destination residue.
8. Workspace diagnostics and non-Pack JSON files are not exported.
9. Confirming Export when the target exists, without Overwrite, leaves that directory unchanged and offers Overwrite or another destination.
10. A simulated copy or validation failure leaves no final or temporary directory. An existing target stays unchanged.
11. Overwrite replaces `<destination>/<pack-id>/` with the exported files. A file that existed only in the old directory is gone. A sibling directory under the destination is unchanged.
12. Source working-copy bytes are unchanged after success and failure.
13. A later source edit does not change an earlier export.
14. The Pack Sources UI no longer has an unhandled Publish button.
15. Existing Pack Editor, signature, Check-loader and navigation regression tests still pass.

Record the actual test command and observed result in the implementation evidence. Do not replace an existing regression test merely because it required the old dead `Publish` markup; update the test to assert the accepted Export behaviour.

## Definition of done

- The Pack Sources row offers a working **Export Pack** action.
- The person can select a destination packs root.
- Studio writes `<destination>/<pack-id>/pack.json` and Requirement files beside it.
- Export uses the selected working copy and copies only Packs v2 Pack files.
- Valid signed, unsigned and mixed working copies are represented honestly.
- Existing signatures and all Pack-file bytes are preserved.
- Invalid or inconsistent input is rejected before a final export appears.
- An existing target is overwritten only when the person chooses Overwrite. Otherwise it stays unchanged, and the person can enter another destination.
- Success and failure leave the source working copy unchanged.
- The exported directory can be loaded by the existing Pack loader.
- The pilot UI and documentation call the operation Export, not Publish.
- No `published/` release, zip exchange, import workflow or product configuration change is introduced.
- The complete affected test suite passes with recorded evidence.

## Out of scope

- Publisher publication and immutable release creation.
- Creating `published/<pack-id>/<version>/`.
- Choosing, incrementing or changing `pack.version`.
- Signing Requirements or sealing a Pack as a side effect of Export.
- Requiring all Requirements to be signed.
- Creating a zip, `.curbpack` archive, checksum manifest or exchange-specific schema.
- Importing an exported Pack into Studio.
- Uploading to a server, registry, Git remote or SharePoint.
- Updating a product repository's `curbpack.json`.
- Choosing which Pack release a product uses.
- Multi-version management, update detection or Claim impact analysis.
- Redesigning working-copy or extraction semantics.
- Adding a `requirements/` subdirectory.
- Changing Packs v2 fields, signing semantics or directory digest rules.

## Stop if

Stop implementation and record the exact conflict if:

- the selected UI row cannot be resolved to one explicit working-copy directory;
- the working copy contains JSON files and the implementation cannot determine from the existing contract which are Pack Requirements and which are diagnostics;
- the existing validator rejects an accepted Packs v2 fixture;
- export would require changing Pack-file bytes;
- the only available implementation would change an existing destination without Overwrite, or would merge it with the new export;
- tests require a new persistent field or export manifest;
- implementing Export would require deciding the EP-11 publish, zip, import or active-version contracts.

Do not solve those conflicts by silently restoring Publish semantics or inventing another Pack representation.
