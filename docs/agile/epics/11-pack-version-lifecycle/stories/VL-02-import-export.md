# VL-02 — Import and export Pack ZIP

**Epic:** [EP-11 — Pack identity, exchange and traceability](../EPIC.md)

**Starts when:** VR-00, VL-00 and VL-01 are accepted.

**As a user**, I want to export a Pack as a ZIP file and import it into the existing Requirements workflow, so that Packs can be exchanged between organizations without changing their contents, identities or signatures.

## Behavior

### Export

Export a Pack as a ZIP containing its existing Pack directory, including `pack.json` and all Requirement files.

Preserve file paths and bytes. Do not transform the Pack into another data format.

Display the signature verification results from VR-00. Missing or invalid signatures must be reported but must not prevent export.

### Import

Allow the user to select a Pack ZIP in the Requirements UI.

1. Safely extract the ZIP into a temporary location.
2. Validate its directory structure and Packs v2 data contracts.
3. Verify and report Pack and Requirement signature status using VR-00.
4. Preserve the imported files, namespace, origin, version and signatures unchanged.
5. Install the Pack without overwriting an existing Pack identity and version.
6. Open the imported Pack in the same Requirements workspace used after Extract.

Import must not change ownership. Editing an imported Pack from another namespace uses the ownership confirmation and copy operation implemented in VL-01.

The resulting workspace must support the same existing Review, Compare, Edit and Sign functionality as a Pack produced by Extract.

## Acceptance — Given / When / Then

### GWT-01 — Export ZIP

**Given** an existing Pack containing multiple Requirements  
**When** the user exports it as ZIP  
**Then** the ZIP contains the complete Pack directory with unchanged relative paths and file bytes.

### GWT-02 — Export regardless of signatures

**Given** a Pack containing signed, unsigned or invalidly signed Requirements  
**When** the user exports it  
**Then** export succeeds and the signature report identifies the verification status of the Pack and each Requirement.

### GWT-03 — Import ZIP

**Given** a ZIP containing one valid Packs v2 Pack directory  
**When** the user imports it  
**Then** the Pack is validated, installed and available in the Requirements workspace.

### GWT-04 — Preserve identity and contents

**Given** a Pack with namespace, ID, version, origin and signatures  
**When** it is exported and imported  
**Then** all Pack and Requirement files retain their original bytes, identities and metadata.

### GWT-05 — Same workflow as Extract

**Given** a successfully imported Pack  
**When** the user opens it in Requirements  
**Then** the existing Review, Compare, Edit and Sign functionality is available through the same components and workflow used for extracted Requirements.

### GWT-06 — Ownership on edit

**Given** an imported Pack whose namespace differs from the current target namespace  
**When** the user requests to edit a Requirement  
**Then** the ownership confirmation and atomic copying behavior from VL-01 applies.

### GWT-07 — Existing Pack collision

**Given** a Pack with the same namespace, ID and version already exists  
**When** the user imports a ZIP containing that identity  
**Then** the import is rejected without overwriting or modifying the existing Pack.

### GWT-08 — Unsafe ZIP

**Given** a ZIP containing unsafe paths, symlinks escaping the destination, or an invalid Pack directory structure  
**When** the user imports it  
**Then** the import fails without writing outside the intended destination or leaving a partially installed Pack.

### GWT-09 — Invalid or missing signatures

**Given** an otherwise structurally valid Pack with missing or invalid signatures  
**When** the user imports it  
**Then** import succeeds, the original files remain unchanged, and the signature issues are reported using VR-00.

### GWT-10 — ZIP round-trip

**Given** an existing Pack  
**When** it is exported to ZIP and imported into an empty compatible workspace  
**Then** the resulting Pack files are byte-for-byte identical to the source, and their embedded signatures retain the same verification results under the same trust configuration.

### GWT-11 — Regression

**Given** ZIP import and export have been implemented  
**When** the full existing test suite runs  
**Then** all tests pass, including focused tests for GWT-01 through GWT-10.

**Done when:** A user can exchange a complete Pack as ZIP, import it into the existing Requirements workspace, and continue using the same workflow as Extract, without modifying the original data or bypassing the established ownership rules.
