# Remediation row Actions menu

## Problem

On an open remediation, each failing check row stacks Find, Add comment, Re-check, and Retire as separate buttons in the Actions column. The column is the right place for those actions. The stack is what makes the row hard to scan.

## Decision

Replace that stack with one dropdown labeled **Actions**, matching the agreed sketch: a wrench, the underlined word Actions, and a caret. The column header stays **Actions**.

The dropdown is a disclosure menu. It is not a `<select>`. The panel opens under the trigger, paints above the table, and does not make the row taller. Clicking outside or pressing Escape closes it. Opening one menu closes any other. Choosing an item closes the menu, then runs that item.

The menu uses the Popover API so the panel sits above the table and light-dismiss works without a second menu implementation.

## Where it appears

The menu is on a check-deviation row in remediation while that remediation is unsigned and the row is still open. Those are the rows that show the stacked buttons today.

These rows have no menu:

- a row that has already passed, including the Remediated section
- a binding row
- a signed remediation
- a review that is not a remediation

The hidden Re-Discover control stays in the cell when evidence is missing. It is not a menu row.

Save, Cancel, and Sign Off at the bottom of the page stay as they are. The page-level Re-check, which runs checks again through `/check`, stays as it is. The row item Re-check is the per-check action and is a different control.

## Menu rows

Visible labels, top to bottom:

| Row | Shown when | What it does |
| --- | --- | --- |
| Find | Evidence for this check is missing, same condition as the Find button today | Opens the existing find dialog |
| Edit check | The check pill on this row is itself a button | Opens the same check editor as a click on that pill |
| Add comment | Always, on a row that has the menu | Opens the existing comment dialog |
| Re-check | Always, on a row that has the menu | Submits the existing per-check form to `/review/recheck` |
| Retire | Always, on a row that has the menu | Submits the existing per-check form to `/review/remediate` with `action=retire` |

Find and Edit check are omitted when their condition is false. They are not disabled rows.

Edit check carries the same `data-check-dialog`, `data-index`, `data-path`, and `data-values` as the check pill. The existing editor opener handles the click. There is no second editor and no navigation to the claim page.

Add comment keeps `data-remedy-comment-open` and the comment dialog. Re-check and Retire keep their hidden fields (`repo_id`, `source`, `claim_id`, `check_digest`) and their form actions. Retire keeps `data-action="retire"`.

The find dialog, the comment dialog, the check editor, and both forms sit outside the menu panel. The Find result slot stays in the cell. Re-check and Retire submit through the `form` attribute, because one menu holds buttons for two forms. A closed menu does not hide a dialog those buttons open.

Retire does not open a confirm dialog. The current row button posts immediately. The retire-confirm dialog belongs to the review compile form when a disposition is retire, and this change does not use it.

Each row is a button. Find, Edit check, and Add comment are `type="button"`. Re-check and Retire remain submit buttons for their existing forms.

## Appearance

The trigger shows a wrench, then the underlined word Actions, then a caret. The wrench is decorative. The trigger's accessible name is Actions.

Each menu row shows a stroke icon, then its label, left aligned, on a light panel with a border and a shadow:

- Find: magnifying glass
- Edit check: pencil
- Add comment: speech bubble
- Re-check: circular arrows
- Retire: archive box

The icons are decorative. The label is the accessible name. They use the same stroke SVG style as the existing check and remedy icons. Retire is the last row, with no extra divider.

## Tests

Render tests assert an Actions trigger on an open remediation check row, the menu labels that apply to that row, and the same hooks as today: find dialog id, comment dialog id, check-dialog data on Edit check, `/review/recheck`, and `data-action="retire"` on the retire submit.

They assert the menu is absent on a passed row, a binding row, a signed remediation, and a review that is not a remediation. The Remediated section still does not contain a Re-check control.

Assertions that require the old stacked button markup are updated to the menu. The server handlers for comment, re-check, and retire stay as they are.
