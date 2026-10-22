# Annex VII quality experiment (2026-10-14)

Task 20 stays open. This is not Task 21. The reference is agent-produced and was not treated as a certified legal gold standard.

Settings for every model call: `qwen3-coder:30b`, `single_call`, temperature `0.2`, `http://127.0.0.1:11434`. No seed. Guidance files were the only product edits. Validators, schemas, and the producer were not changed.

## Reference

Directory: `poc2/data/reference/poc1-annex-vii-unsigned/`

Pack `poc1-annex-vii-reference`, version `0.0.0-reference`, unsigned. Thirteen unsigned Requirements, no `origin`, no `source.edition`. Locators `VII.1(a)` … `VII.8`.

Validation: `poc2/.venv/bin/python poc2/data/reference/build_poc1_annex_vii_reference.py` exited 0. Each file passed `validate_requirement(..., published=False)` on save and again on `load_pack_directory`.

Field mapping and the pointable-words yardstick: `poc2/data/reference/POC1_ANNEX_VII_MAPPING.md`.

### Conversion losses

- PoC1 ids `vii-1a` … `vii-8` and claim slugs were not copied. Reference ids are labels `POC1-REF-VII-*` only.
- Hunt `exclude_path_globs` and `prefer_path_globs`, and the package default `sources: [documents]`, were not written onto Requirements.
- Gold EUR-Lex URL was not copied. `source.url` is the cra-xml adapter URL. Passages are the Formex atomizer text from `L_202402847EN.007501.fmx.xml`.
- Locus `1(d)` wording: gold says "the information and instructions"; the reference uses the Formex sentence "user information and instructions". The other twelve passages match after whitespace normalization.
- Optional fields that are pointable in `law_text` but absent from the PoC1 maps were not invented. In particular the reference has no `applicability` on `1(c)` and no `strength` on `5`. Those words are the evaluation yardstick, not fields the conversion added.

## Quality gap before this experiment

`2026-10-13T134627Z` (baseline) has 13 valid Requirements and thin hints: no `expected_evidence` anywhere, and no `path_hints` on several loci. `VII.8` has `strength: MAY` although that passage has no "may".

`2026-10-13T141531Z` is valid and more searchable than the baseline (globs, evidence kinds, `requirements` on VII.3). It is not the reference. `VII.2(b)` omits the bill of materials. `VII.5` omits common specifications and alternative solutions, and omits `MUST` although the passage says "shall". `VII.1(c)` has no hardware applicability. `VII.8` sets `responsible` to "Manufacturer" and hints "update tracking". Locators are the bare locus (`1(a)`, `8`), not `VII.1(a)`.

## Prompt revisions

Copies live under `poc2/data/reference/prompt-revisions/`. The adapter files now match r2. r0 matches the prompts used for `2026-10-13T141531Z`.

| Revision | interpret sha256 | discovery_hints sha256 | Result |
| --- | --- | --- | --- |
| r0 | `f9111c4c3949121230bf32b1e1c40bfd2f7fd8d9f7b4d92046fdd7924ceeac14` | `54ef07faf955f59a45211e59bd4a325911fc7149dd4687259cd928116dd2bb23` | Prior copy `2026-10-13T141531Z`. Not re-run. |
| r1 | `f4890573467e0aa6659e28fa1568fba67917c7d0025e5ea5f595b573ce805696` | same as r0 | No working copy. Discovery loci `3`–`8` came back as `3)` … `8)`. Interpret locators were `VII.*`, and `strength` was `MUST` on every row, including passages with no shall. `1(c)` still had no applicability. `8` still named manufacturer. |
| r2 | `a31224405a7fa7f7af92e1421e984564aa980e98d8a5a37fad3b8c32434c4f82` | `cf06c24da7c33c755dc935c45163dec842e8989a8a3fad2c45771164579547ab` | Working copy `2026-10-14T043521Z`. 13 Requirements, no exclusions. |
| r3 | `11c1109813a8a525b3243bd0a40a65314b76ae144f7195ca9bd3ff63cd08de27` | `177e0a0cbfbf9f6c29c879035beb747068c5a08bcbc1e028f70a9a79ba7692dc` | Working copy `2026-10-14T043649Z`. Hints stayed specific, but every row gained `strength: MUST`, `responsible: manufacturer`, and `applicability: Where applicable`. Rejected as the best run. |

Raw prompts, responses, and `outcome.json` are under `poc2/data/reference/runs/`. Working copies are under `poc2/data/workspace/cra-xml-baseline/` and were not committed (`data/workspace/` is gitignored). `2026-10-13T134627Z` and `2026-10-13T141531Z` were not modified.

## Best run versus the reference

Best run: r2, `2026-10-14T043521Z`. Repeats with the same bytes: `2026-10-14T043741Z` and `2026-10-14T043810Z`. All three are structurally valid unsigned drafts. `law_text` matches the Formex provisions. Legal fields below are from the pointable-words table, not from extra keys on the reference.

| Locus | Baseline `134627Z` | Prior `141531Z` | Best r2, stable across 3 calls |
| --- | --- | --- | --- |
| `1(a)` | Thin concepts, no paths, no evidence kinds. | Intended purpose, usable globs. | Same useful level. No false strength. |
| `1(b)` | No paths or evidence kinds. | Versions and changelog globs. No SBOM, which the reference uses only as an extra hunt target. | Versions, changelog, git. No false strength. |
| `1(c)` | Concepts name photographs and marking; no paths. | No applicability. No marking. | Still no applicability. Marking appears in one of three calls, photographs in the other two. Hardware condition is not a field. |
| `1(d)` | No paths. | Generic user-guide hints. | User information and instructions. Does not invent Annex II disposal duties. |
| `2(a)` | Some architecture paths, no evidence kinds. | Architecture and git. | Architecture, integration, documents and git. Drawings "where applicable" never become `applicability`. |
| `2(b)` | Concepts include the bill of materials; paths are only `*vulnerability*` and `*update*`; no evidence kinds. | Drops the bill of materials. | All three calls name the bill of materials, the coordinated disclosure policy, the contact address, and secure update distribution, with documents and git. Evidence kinds vary (`test result` on the first call, `requirement` on the repeats). |
| `2(c)` | No test source. | No `test_management`, evidence kind `requirement`. | All three calls use `test_management` and `test result` for process validation. |
| `3` | Lifecycle verbs, no evidence kinds, source documents only. | Threat modeling and `requirements`. Misses Annex I applicability. | All three calls name the risk assessment, essential-requirements applicability, a threat-model glob, and source `requirements`. They also add "risk mitigation", which the passage does not name. No `strength`, which is correct. |
| `4` | No paths. | Support period and end of life. | Same useful level on all three calls. |
| `5` | Names standards and common specifications; misses alternative solutions; no evidence kinds. | Misses common specifications and alternative solutions. No `MUST`. | All three calls hint harmonised standards, common specifications, certification schemes, and alternative solutions. None set `strength: MUST`, though the passage says "shall". The "where … have not been applied" branch is not `applicability`. |
| `6` | No test source. | Test reports and `test_management`. | Same, stable. |
| `7` | One concept, no paths. | Declaration globs, plus a broader "certification document". | EU declaration is stable. "Certification document" remains an extra label. |
| `8` | `strength: MAY`. Concepts are the bill of materials and the authority. | `responsible: Manufacturer`. Concepts include update tracking. | No `responsible` and no `MAY` on any call. `applicability` is the same long paste of the sentence on all three calls, so the reasoned-request limit is present and the whole passage is also repeated. Hint concepts are not stable: the first call stays near the bill of materials; both repeats add vulnerability-reporting contact and secure update distribution, which are `2(b)` artefacts. |

## Repeatability

The r2 prompt bytes were not changed between the three calls. Locators, the absence of blanket `MUST` / `manufacturer`, the four `2(b)` artefacts, the `5` alternative-solution hints, the `3` requirements source, and the `8` applicability string were stable. `1(c)` marking, `8` neighbouring-duty hints, and some evidence-kind choices were not. Temperature 0.2 with no seed is enough to move those hints.

r3 showed the other failure mode: a self-check that says "a row with shall must have MUST" was applied to every row.

## Tests

- `cd poc2 && .venv/bin/python -m unittest tests.test_requirements_produce tests.test_requirements_extract tests.test_xml_adapters` — PASS, 26 tests.
- `cd poc2 && .venv/bin/python -m unittest discover -s tests` — PASS, 96 tests. A sandboxed run failed 3 git-init tests; the same command outside the sandbox passed. Logged `ModelError` tracebacks in that run are the tests' expected refusal paths.

## Conclusion

**Improved.** Not recovered.

Discovery for `VII.2(b)`, `VII.5`, and `VII.3` is more useful than `2026-10-13T141531Z` and, on those artefacts, meets the reference's distinct aspects. `VII.8` no longer invents a manufacturer. The legal fields a person must inspect are still wrong or missing: hardware applicability on `VII.1(c)` never appears, `VII.5` never gets `MUST` from "shall", and `VII.8` hints still pick up update and contact duties on two of three calls. Further prompt edits were stopped at three revisions.

Remaining failure modes:

- The model treats "check every row for where / shall" as permission to stamp one applicability and one strength onto all rows, or as optional when the clause is mid-sentence.
- `VII.8` applicability copies the passage instead of keeping only the condition.
- Neighbour provisions leak into `VII.8` hints often enough that one favorable call is not the behavior.
- `1(c)` marking is not reliable.
- No producer change was made. A stray `)` on loci `3`–`8` still fails the run, which is the existing exact-locus check.
