# PoC1 Annex VII reference — field and semantic mapping

**Label.** This comparison set was produced by a Cursor agent from PoC1 files that a Cursor agent also produced. The user has inspected it. It is not an independently legally certified gold standard, and it is not fully human-reviewed. Do not treat a field as an approved Requirement on the strength of this directory.

The PoC1 YAML `description` lines say "Human-reviewed". This conversion does not adopt that header as certification.

Produced by `poc2/data/reference/build_poc1_annex_vii_reference.py` with no model call. Inputs, read only:

- `poc/components/transform/adapters/cra/maps/claims.yml`
- `poc/components/transform/adapters/cra/maps/search.yml`
- `poc/data/in/ctam_cra_requirements_search.yml`
- cra-xml Formex provisions from `section_provisions` on section `VII` (`L_202402847EN.007501.fmx.xml`)

Output directory: `poc2/data/reference/poc1-annex-vii-unsigned/`

Pack `poc1-annex-vii-reference`, version `0.0.0-reference`, unsigned. Thirteen Requirements, unsigned, no `origin`, no `source.edition`. `claims.yml` and the gold package agree on id, claim, note, concepts, path hints, sources, and expected evidence for every locus.

## Validation

The builder calls `save_pack(..., sealed=False)` and `save_requirement(..., published=False)`, which run `validate_pack` / `validate_requirement`. It then reloads the directory with `load_pack_directory`. Re-running the builder now exits because the output directory already exists. That refusal is the freeze.

Independent check on 2026-10-14, from `poc2/`, with no model call:

` .venv/bin/python` loaded `data/reference/poc1-annex-vii-unsigned` through `load_pack_directory`, then `validate_pack(..., sealed=False)` and `validate_requirement(..., published=False)` on all 13 files. Exit 0. Each file is unsigned, has no `origin`, and has no `source.edition`. Locators are `VII.` plus the loci below, in this order. Concepts, path hints, expected evidence, per-locus sources, and the `1(c)` note match `search.yml` and `claims.yml`. `law_text` matches the cra-xml Formex provision for that locus, byte for byte. The same check compared `claims.yml` with the gold package.

SHA-256 values for the inputs and the frozen JSON are in `poc2/data/reference/POC1_ANNEX_VII_PROVENANCE.md`. The Requirement JSON files were not rewritten for this record.

## Locus mapping

Reference ids are directory labels. They are not the product naming convention. PoC1 ids and claim slugs are not stored on the Requirements. `requirements/ARCHITECTURE.md` states that those PoC1 ids are not Requirement ids, and the product id convention for these loci is still unconfirmed. Copying either value would have been a naming decision, so the labels stay local to this directory.

| Locus | PoC1 id | PoC1 claim slug | Reference id | Locator | `sources` copied |
| --- | --- | --- | --- | --- | --- |
| `1(a)` | `vii-1a` | `vii-1a-intended-purpose` | `POC1-REF-VII-1A` | `VII.1(a)` | no |
| `1(b)` | `vii-1b` | `vii-1b-software-versions-affecting-compliance` | `POC1-REF-VII-1B` | `VII.1(b)` | `documents`, `git` |
| `1(c)` | `vii-1c` | `vii-1c-hardware-illustrations` | `POC1-REF-VII-1C` | `VII.1(c)` | no; `note` copied |
| `1(d)` | `vii-1d` | `vii-1d-annex-ii-instructions` | `POC1-REF-VII-1D` | `VII.1(d)` | no |
| `2(a)` | `vii-2a` | `vii-2a-design-development-architecture` | `POC1-REF-VII-2A` | `VII.2(a)` | `documents`, `git` |
| `2(b)` | `vii-2b` | `vii-2b-vulnerability-handling-process` | `POC1-REF-VII-2B` | `VII.2(b)` | `documents`, `git` |
| `2(c)` | `vii-2c` | `vii-2c-production-monitoring` | `POC1-REF-VII-2C` | `VII.2(c)` | `documents`, `test_management` |
| `3` | `vii-3` | `vii-3-cybersecurity-risk-assessment` | `POC1-REF-VII-3` | `VII.3` | `documents`, `requirements` |
| `4` | `vii-4` | `vii-4-support-period-rationale` | `POC1-REF-VII-4` | `VII.4` | no |
| `5` | `vii-5` | `vii-5-standards-or-alternative-solutions` | `POC1-REF-VII-5` | `VII.5` | no |
| `6` | `vii-6` | `vii-6-conformity-test-reports` | `POC1-REF-VII-6` | `VII.6` | `test_management`, `documents` |
| `7` | `vii-7` | `vii-7-eu-declaration-of-conformity` | `POC1-REF-VII-7` | `VII.7` | no |
| `8` | `vii-8` | `vii-8-sbom-on-reasoned-request` | `POC1-REF-VII-8` | `VII.8` | `documents`, `git` |

## Field mapping

| Existing information | Packs v2 | What was done |
| --- | --- | --- |
| Adapter `source` | `source` | Copied. No `edition`. |
| Gold `source_url` (EUR-Lex HTML) | — | Not copied. The passages come from the Formex file the adapter names. Adapter URL is `https://publications.europa.eu/resource/celex/32024R2847`. |
| Gold `instrument: CRA`, `annex: VII` | `source.instrument`, locator prefix | `source.instrument` is the adapter value `CRA`. The annex is the `VII.` prefix on `references[0].locator`. Packs v2 has no annex field. |
| Section `VII` + provision `locus` | `references[0].locator` | Mechanical join `VII.{locus}` (`VII.3`, `VII.1(a)`). The adapter stores `locus`; it does not emit a separate locator string. `nr` is 1. |
| Adapter `law_text` | `references[0].law_text` | Copied verbatim, including the atomizer's 78-column wrap. |
| Gold / text-fixture `law_text` | — | Not copied. See the one wording loss below. |
| PoC1 `id` (`vii-1a` … `vii-8`) | — | Not used. Those values are map keys, not Requirement ids. Reference ids are `POC1-REF-VII-1A` … `POC1-REF-VII-8`, labels for this directory only. They are not a product naming convention. |
| PoC1 `claim` slug | — | Not copied. |
| `search.concepts`, `path_hints`, `expected_evidence` | `discovery_hints` | Copied in order. |
| `search.sources` strings | `discovery_hints.sources[]` as `{"source": "<id>"}` | Copied only where that locus lists `sources`. |
| Package `defaults.sources: [documents]` | — | Not written onto Requirements that omit `sources`. In the gold package that default is shared hunt configuration. |
| `defaults.exclude_path_globs`, `prefer_path_globs` | — | Not copied. Those are repo `curbpack.json` `hunt` fields. No `curbpack.json` was written. |
| `claims.yml` note on `1(c)` | `note` | Copied: `often N/A for pure software`. |
| strength, responsible, applicability, exceptions, scope, remediation_hint | — | Absent from the PoC1 maps. Not invented on the Requirements. Pointable words that remain only in `law_text` are listed below. |

## Wording not copied into `law_text`

Normalized whitespace, locus `1(d)` only. The other twelve gold passages match the Formex provisions after whitespace normalization. This difference is the one already recorded as genuine wording in `poc2/requirements/extract/data/official_xml/compare/cra_annex_vii_text_vs_xml.md`. The text fixture was left unchanged there; this reference follows the Formex passage.

- Gold / text fixture: `the information and instructions as set out in Annex II`
- Formex provision used here: `user information and instructions as set out in Annex II`

## Pointable words left in `law_text`

These are readings of the official passage under Packs v2. They were not added to the reference Requirements, because the PoC1 maps do not contain them. A later extract that sets the field from these words is legally supported. A later extract that sets a field from words that are not in the passage is not.

| Locus | In the passage | Not put on the reference |
| --- | --- | --- |
| `1(a)` | No shall, should, may, where-clause, or named duty-holder. | No optional fields. |
| `1(b)` | No modal and no where-clause. "affecting compliance with essential cybersecurity requirements" qualifies which versions, and stays inside `law_text`. | No optional fields. |
| `1(c)` | `where the product with digital elements is a hardware product` | Applicability was not promoted. The copied `note` is the PoC1 comment "often N/A for pure software". That comment is not the where-clause. |
| `1(d)` | No modal, where-clause, or named party. Annex II is a cross-reference, not a second passage on this Requirement. | No optional fields. |
| `2(a)` | `where applicable` qualifies drawings and schemes, not the whole design description. | Applicability was not promoted. |
| `2(b)` | `manufacturer` is who put the vulnerability-handling processes in place. The passage has no shall or may. | Responsible was not promoted. The documentation duty's holder is not a separate sentence here. |
| `2(c)` | No modal, where-clause, or named party. | No optional fields. |
| `3` | No shall. Packs v2 states that this risk passage has no `strength`. No where-clause and no named party. | No optional fields. |
| `4` | No modal, where-clause, or named party in this passage. | No optional fields. |
| `5` | `shall` occurs in "the technical documentation shall specify the parts which have been applied". `where those harmonised standards, common specifications or European cybersecurity certification schemes have not been applied` introduces the alternative-solutions branch. | `strength: MUST` and that where-condition were not promoted. |
| `6` | No modal, where-clause, or named party. | No optional fields. |
| `7` | No modal, where-clause, or named party. | No optional fields. |
| `8` | Opens with `where applicable`. No shall or may. The market surveillance authority requests the bill of materials; it does not hold the duty. | Applicability was not promoted. Responsible must not be filled with a party the passage does not name. |

## Discovery aspects carried from the PoC1 search plans

Hints are search suggestions. Format names and method names below are not legal duties. A useful extract covers the distinct artefacts in the passage. It does not have to repeat every PoC1 token, and a longer hint list is not a better one.

| Locus | Distinct aspects in the passage | PoC1 hint detail that goes beyond the passage |
| --- | --- | --- |
| `1(a)` | Intended purpose. | "intended use", "what the product does" are search paraphrases. |
| `1(b)` | Versions of software that affect compliance. | SBOM and `*soup*` are extra hunt targets. Changelog is a reasonable place versions are written. |
| `1(c)` | Photographs or illustrations of external features, marking, and internal layout, only for hardware. | — |
| `1(d)` | User information and instructions set out in Annex II. | Security instructions, secure configuration, and product disposal are Annex II subject matter, not words in this passage. |
| `2(a)` | Design and development, system architecture, how components integrate. Drawings and schemes where applicable. | — |
| `2(b)` | Vulnerability-handling process, software bill of materials, coordinated vulnerability disclosure policy, contact address, technical solutions for secure distribution of updates. | — |
| `2(c)` | Production and monitoring processes, and validation of those processes. | `test_management` and "test result" treat validation as test evidence. |
| `3` | Cybersecurity risk assessment across design, development, production, delivery, and maintenance, including how Annex I Part I essential requirements apply. | STRIDE, residual risk, and `*CRA*ASSESSMENT*` are hunt preferences. Threat model is a common artefact for this passage, not a named legal method. |
| `4` | Information used to determine the support period. | "Expires" and `*security.txt*` are hunt preferences. |
| `5` | Harmonised standards, common specifications, European cybersecurity certification schemes, solutions adopted where those are not applied, other technical specifications, and the parts applied when application is partial. | — |
| `6` | Test reports for product conformity and for vulnerability-handling processes, against Annex I Parts I and II. | — |
| `7` | A copy of the EU declaration of conformity. | "DoC" is an abbreviation. |
| `8` | Software bill of materials, where applicable, after a reasoned request from a market surveillance authority when needed to check Annex I. | CycloneDX, SPDX, and SOUP are format hints. The conditional request is not a standing duty to track updates. |

## How later extracts are judged

Structural validity is separate from semantic quality. A file that validates can still miss an artefact or invent a party.

Do not score an extract higher because it has more fields, a longer hint list, or more shared words with this reference. Score whether a person can see each distinct artefact and condition, whether optional fields follow the pointable-words table, and whether the hints are specific enough to look for those artefacts. `documents` on a Requirement that omits `sources` here matches the gold package default. It is not an extra duty.
