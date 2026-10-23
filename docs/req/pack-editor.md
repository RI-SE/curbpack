# Pack Editor — derived system requirements

**Status:** Draft for review, **not** an approved implementation contract.  
**Source:** [EP-01 Pack Editor](../agile/epics/01-pack-editor/EPIC.md) and its [PE-01–PE-11 stories](../agile/epics/01-pack-editor/stories/).  
**External contract:** `docs/reference/packs2.md` in this repository. That specification, not this document, defines persistent Pack and Requirement schemas.

These are testable behavior contracts derived from the agreed stories. Where behavior has not been decided, it stays open rather than being filled in by an agent.

| Requirement | Required observable behavior | Derived from |
| --- | --- | --- |
| **REQ-PE-001** | The start page offers Pack Editor and still links to Discovery, Check, and Review. Opening the pack list shows the current editable Packs. That open does not change an existing catalog file or any Pack file. A missing catalog may still be created with the pilot's default rows. The link label and the source-page heading stay as they are. Status DRAFT. | PE-01 |
| **REQ-PE-002** | Each Pack row identifies the Pack, its official document and selected adapter; **Edit** opens the selected Pack. | PE-02 |
| **REQ-PE-003** | **Add Pack** accepts a Pack name, official document name, document URL and a configured adapter. Saving creates an editable Pack entry; it must not start extraction or publication. | PE-03 |
| **REQ-PE-004** | Opening a Pack shows only its registered sources, as in the current pilot; the heading displays document and adapter. Each source row retains the existing **Extract** and **Edit** operations. Opening makes no Requirement changes. Do not silently change how source rows relate to adapter-enumerated sections. | PE-04 |
| **REQ-PE-005** | **Add Source** records the source and its applicable section/reference and URL under the selected Pack using the existing configuration flow; it does not start extraction. The Pack-level document and adapter are reused, not independently chosen for every source. | PE-05 |
| **REQ-PE-006** | **Extract** for a selected source invokes its configured adapter with the source URL and applicable section, retains the existing display of supported/remaining sections where available, reports progress, output and errors, and produces unsigned Requirement candidates referencing the regulatory text. Existing accepted Requirements remain unchanged on failure. | PE-06 |
| **REQ-PE-007** | A first extraction makes each candidate and supporting original text/location available for review and correction; no candidate is automatically treated as signed or published. | PE-07 |
| **REQ-PE-008** | Re-extraction presents existing versus proposed content, including additions and possible removals, **before** modifying accepted Requirements. Cancel/discard is non-destructive. | PE-08 |
| **REQ-PE-009** | The comparison supports explicit choices for supported differences. Apply changes only selected values; preserve unselected fields and unrelated Requirements. A changed signed payload must no longer verify as previously signed. | PE-08 |
| **REQ-PE-010** | Editing a Requirement updates only explicitly edited supported fields; unchanged legal references and other Requirements remain intact. Editing a signed payload invalidates the previous signature. | PE-09 |
| **REQ-PE-011** | Requirement signing and verification operate on the actual saved payload according to Packs v2; a modified payload cannot retain a valid previous signature. | PE-10 |
| **REQ-PE-012** | **Publish** acts on the selected Pack. Its published Requirements belong to that Pack by `requirement.pack_id`, meet the applicable signing/sealing rules, retain regulatory provenance, and are released at an explicitly chosen version without overwriting a prior release. | PE-11 |
| **REQ-PE-013** | Each persisted Requirement preserves its regulatory source identity and edition and the supporting passages in `references[].locator` and `references[].law_text`, including multiple references where necessary. Neither comparison nor editing may silently discard them. | PE-06–PE-11 |
| **REQ-PE-014** | The editor's adapter configuration and extraction run diagnostics do not become invented normative Packs v2 fields. Use `origin` only for a working copy derived from a published Pack, as defined by Packs v2. | PE-03–PE-11 |

## Not yet specified — do not implement by assumption

- How the editable Requirements workspace relates to Git, branches and the current Working copy UI. Git is intended as the versioned working environment; the UI and workflow have not been decided.
- Whether the source rows correspond one-to-one to sections, or select a section/range when starting extraction. Keep the existing behavior until verified against the fresh pilot.
- Whether multiple sections can be extracted in one operation; one-at-a-time is the agreed baseline.
- Exact controls for accepting or refusing a Requirement *removed* by a new extraction (the absence itself must be visible; it must not cause silent deletion).
- Whether publication includes all reviewed Requirements in a Pack or a user-selected subset; no new Pack Publisher component has been approved.

## Test mapping

When implementing, map each REQ-PE ID to an executable test or recorded manual acceptance test in `docs/test/`, including success, cancellation and failure paths. Tests and current implementation status are **not** asserted by this draft. Import the fresh PoC2 tests and establish their baseline first.

## SYS-02 — one suite for the pipeline

**Status:** Draft. Not a pilot release blocker.
**Source:** [SYS-02](../agile/epics/01-pack-editor/stories/SYS-02-one-test-suite.md).

| ID | Status | Required observable behavior | Derived from |
| --- | --- | --- | --- |
| **SYS-R01** | DRAFT | `make test` and `make ci-tests` execute `scripts/ci/checks/tests.py`. That script loads `tests/test_*.py` and no other suite. After this story, `tests/cs/` and `tests/ci/` are absent. | SYS-02 |
| **SYS-R02** | DRAFT | With no `ONLY`, `make ci-tests` prints one dotted line for `tests` and `Summary: N PASS, M FAIL`. `ONLY=tests` prints one line per case and one summary. An unknown `ONLY` exits nonzero and lists the valid names. There is no extra Make target and no `run_cs_checks` script. | SYS-02; `docs/agile/future_cicd.md` presentation section |
| **SYS-R03** | DRAFT | `select_working_copy` and `select_published_pack` raise `ModelError` when `pack_id` is not a single directory name, and a normal id still selects. The assertion lives in a `tests/test_*.py` module. The product check already in `requirements/workspace.py` `_pack_id_name` stays; this requirement does not redefine Packs v2. | SYS-02; SEC-02 evidence, folded here |
