# PE-08 — Extract again and compare

**Status:** Open deviation, 2026-10-28, danielfl. Not accepted.

**Epic:** [EP-01 Pack Editor](../EPIC.md)

**As a Pack author**, I want to run extraction again and compare it with my existing Requirements, for example after changing the model, prompt, adapter or legal text.

**Accept when:** A new extraction never silently replaces existing work; the Review extraction view shows the old and new values; I can keep the old value or use the new one for each supported difference; unchanged or unselected data remain unchanged; I explicitly apply the result or discard it; cancelling changes nothing; modified signed content needs a new signature. The comparison must also make newly added or missing Requirements visible rather than silently deleting them.

The apply and cancel controls below are the 2026-10-28 review by danielfl. They replace the button **Use the new definitions you chose** and the link **Leave the working copy unchanged**.

### PE8-R01 — Save with nothing chosen asks, then returns to the Pack

**Given** Review extraction for a Pack, and no new definition was chosen  
**When** the person presses **Save**  
**Then** a popup says that nothing was changed  
**And** the popup offers **OK** and **Cancel**  
**And** the working copy is unchanged  
**And** the page does not only show the banner `Nothing was brought in. The working copy is unchanged.`

**Given** that popup  
**When** the person presses **OK**  
**Then** the Sections page of the Pack just edited is shown  
**And** the Pack list is not shown.

**Given** that popup  
**When** the person presses **Cancel**  
**Then** Review extraction stays open  
**And** the working copy is unchanged.

### PE8-R02 — Cancel returns to the same Pack

**Given** Review extraction for a Pack  
**When** the person presses **Cancel**  
**Then** that control is a button  
**And** the Sections page of the Pack just edited is shown  
**And** the Pack list is not shown  
**And** there is no link **Leave the working copy unchanged** to `/requirements`.
