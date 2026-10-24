# XML source adapters implementation plan (CRA + NIS2)

> **For agentic workers:** Execute one small task at a time under `poc2/AGENTS.md`. This plan is separate from `REQUIREMENTS_IMPLEMENTATION_PLAN.md`. Do not mark Requirements tasks complete here. Do not start Requirements Task 14 from this plan.

**Goal:** Make official EU Formex XML a usable, deterministic source for the existing Requirements workflow for CRA (CELEX 32024R2847) and NIS2 (CELEX 32022L2555), without a new domain model.

**Architecture:** Keep Packs v2 and `poc2/requirements/ARCHITECTURE.md` unchanged. Add adapter directories and Formex traversal under `poc2/requirements/extract/`. Stages 00–01 stay deterministic; 02–03 stay LLM; 04 assembles unsigned Requirements.

**Tech Stack:** Python 3 stdlib (`xml.etree.ElementTree`, `unittest`), existing Requirements extract/workspace/UI.

## Global Constraints

- All `ARCHITECTURE.md` files are read-only.
- No XML-specific fields on Requirements; no `decisions.json`; no second assembly path.
- Keep the existing CRA text adapter (`adapters/cra`) intact.
- Source selection distinguishes CRA text, CRA XML, and NIS2 XML.
- NIS2 means Directive (EU) 2022/2555 only.
- Local commits only. No push/PR/remote/destructive Git.
- Unsupported substantive structures → inspectable diagnostics.

---

### Current checkpoint

| Field | Value |
| --- | --- |
| Plan state | COMPLETE — finish pass (NO.P leak + NIS2 articles + recompare) |
| Current phase/task | Finish tasks A–D done; stop (do not start Requirements Task 14) |
| Last completed task | Finish D — docs + full suite 77 tests + local commit |
| Last verified local commit | `ac812ad01cc4ca60fa6be676e4b0ad99b702ea69` |
| Uncommitted files | none for this plan after commit |
| Last tests and result | `cd poc2 && .venv/bin/python -m unittest discover -s tests -v` — PASS, 77 tests |
| Active blocker/decision | `1(d)` wording discrepancy: fixture unchanged until independent OJ/PDF verification. EUR-Lex notice WAF-blocked; CELLAR Formex used. Annex I–III `<TBL>` not ready. |
| **Exact next action** | Stop. Humans may reconcile Requirements Task 18 later. Do **not** start Task 14 here. |

### Finish-pass tasks

- [x] **A.** Fix `_item_intro` so `NO.P` is not duplicated into `law_text`; regression tests for CRA VII `3`–`8` and NIS2 Art.1 / Art.13 / Art.21.
- [x] **B.** Re-run CRA Annex VII comparison; classify exact / normalization-only / genuine wording; leave fixture unchanged for `1(d)`.
- [x] **C.** Mark NIS2 `Art.1`–`Art.46` ready after per-article extract+assemble validation; annexes I–III remain not ready with `<TBL>` diagnostics.
- [x] **D.** Integration/regression tests, full suite, docs, local commit.

### CRA comparison counts (post-fix)

| Metric | Count |
| --- | --- |
| Shared loci | 13 |
| Exact matches | 6 (`3`–`8`) |
| Normalization-only matches | 6 (`1(a)`–`1(c)`, `2(a)`–`2(c)`) |
| Genuine wording differences | 1 (`1(d)`) |

### NIS2 coverage

| Kind | Status |
| --- | --- |
| Articles 1–46 | ready / in scope (verified) |
| Annex I, II | in scope, **not ready** (`<TBL>` diagnostic) |
| Annex III | out of scope, **not ready** (`<TBL>` diagnostic) |

### Earlier tasks (Phase A–G)

- [x] Task 1 — Pin verification and Formex package load
- [x] Task 2 — Deterministic text + inventory
- [x] Task 3 — Provision extraction for CRA Annex VII (XML)
- [x] Task 4 — CRA XML adapter (`cra-xml`)
- [x] Task 5 — NIS2 XML adapter (`nis`)
- [x] Task 6 — Integrate extract_section + working copies
- [x] Task 7 — Engineer UI source selection and inspection
- [x] Task 8 — CRA text vs XML Annex VII comparison
- [x] Task 9 — Documentation + regression gate
