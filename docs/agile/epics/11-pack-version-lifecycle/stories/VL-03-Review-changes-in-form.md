# VL-03 — Review Requirement changes in form view

**Epic:** EP-11 — Pack Version Lifecycle

**Starts when:** VL-02 is accepted.

**As a user**, I want to review proposed Requirement changes in a familiar form instead of a JSON diff, so that I can easily select which values to keep before continuing to edit or sign the Requirement.

## Behavior

### Requirements list

After Extract or Import produces comparison results, display an additional **New** column in the existing Requirements list.

- Requirements with proposed changes show a **Changes** link.
- Clicking Changes opens the new Compare page for that Requirement.
- Requirements without proposed changes show no Changes link.

The comparison belongs to the current Extract or Import operation. No persistent update queue is needed.

### Compare page

Replace the existing JSON-diff presentation with a form-based Compare page.

Implement the page in its own Python module, e.g. `requirements/ui/compare_form.py`.

The page receives the current Requirement, the proposed Requirement and the context needed to return to the correct Requirements list.

Use the same fields, ordering and grouping as the existing Requirement editor.

For each changed field:

- Display a dropdown containing both complete values.
- **Old:** red, struck-through text.
- **New:** green text.
- Support multiline text values within the dropdown.
- The selected option determines which value will be retained.

Unchanged fields are displayed normally.

At the top, provide two controls:

- **Select all old**
- **Select all new**

Each control updates all changed-field selections. Individual selections can subsequently be changed.

### Apply and continue

Provide **Cancel** and **Apply**.

- Cancel returns to the Requirements list without changing anything.
- Apply submits the selected values through the existing Compare/Apply functionality.
- Only selected new values replace their corresponding existing values.
- After Apply, open the normal Requirement editor with the resulting Requirement loaded.

The user can then edit further, test discovery or sign using the existing editor.

## Acceptance — Given / When / Then

### GWT-01 — Requirements list

**Given** an Extract or Import comparison containing changed and unchanged Requirements  
**When** the Requirements list is displayed  
**Then** the New column identifies Requirements with proposed changes and provides a Changes link for each.

### GWT-02 — Open Compare

**Given** a Requirement with proposed changes  
**When** the user selects Changes  
**Then** its Compare page opens with the correct current and proposed values.

### GWT-03 — Form presentation

**Given** a Requirement comparison  
**When** the Compare page is displayed  
**Then** the fields follow the existing Requirement editor's structure, changed fields offer Old/New dropdown choices, and unchanged fields retain their normal presentation.

### GWT-04 — Dropdown values

**Given** a changed text field containing multiline values  
**When** its dropdown is opened  
**Then** both complete values are readable, with Old displayed in red and struck through and New displayed in green.

### GWT-05 — Select all

**Given** several changed fields  
**When** the user selects All old or All new  
**Then** every changed field selects the corresponding version, while remaining individually selectable.

### GWT-06 — Selective Apply

**Given** a comparison with a mixture of Old and New selections  
**When** the user selects Apply  
**Then** only fields selected as New are updated, using the existing Apply implementation.

### GWT-07 — Cancel

**Given** a comparison with selections made  
**When** the user selects Cancel  
**Then** no Requirement is modified and the user returns to the correct Requirements list.

### GWT-08 — Continue editing

**Given** the user has applied selected changes  
**When** Apply completes  
**Then** the normal Requirement editor opens with the resulting values and its existing editing, discovery-testing and signing controls available.

### GWT-09 — Regression

**Given** the new Compare presentation has been implemented  
**When** the full existing test suite runs  
**Then** all tests pass, including focused tests for GWT-01 through GWT-08.

**Done when:** The JSON-diff page has been replaced by a form-based Compare page, users can select Old/New values directly in dropdowns, and Apply leads into the existing Requirement editor without changing the underlying comparison behavior.