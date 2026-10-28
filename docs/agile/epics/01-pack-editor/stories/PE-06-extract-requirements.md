# PE-06 — Extract Requirements

**Status:** Reviewed 2026-10-28 by danielfl for the extraction window and abort. The apply and cancel controls are PE-08 and are not accepted.

**Epic:** [EP-01 Pack Editor](../EPIC.md)

**As a Pack author**, I want to extract Requirements from a chosen section so that I do not have to transcribe and interpret the entire legal text manually.

**Accept when:** Extract uses the selected Pack's adapter and the source's URL/section; the existing extraction view shows available/remaining sections where the adapter provides them and the run progress, output and errors; the result is a set of proposed Requirements with references to the actual regulatory text; extraction does not sign or publish; failure does not destroy existing accepted Requirements. The adapter describes how the regulatory document is divided into sections; the UI must not assume every regulation has the same structure.

**Human review:** 2026-10-28, danielfl. **Extract** opens the extraction window. Abort is available. The run then offers a choice between a new definition and the existing one. The buttons after that choice are the open deviation on PE-08.
