# NIS2 Article 21 agent reference — traceability and review

**Label.** A Cursor agent produced this reference for later evaluation of the Qwen extraction agent. It is not legally certified and it has not been independently human-reviewed. It is not an extraction-agent result. Do not treat it as a gold standard.

The pack is an unsigned draft. Requirement ids are labels for this directory. They are not a product naming convention. `source.edition` is omitted on purpose: the adapter does not set it, and an unsigned draft should not invent the edition a reviewer has to confirm. The OJ date is recorded in `PROVENANCE.md`.

No model was called. Extraction prompts, prompt revisions, and agent run outputs were not used. The passages come from the deterministic NIS2 Formex adapter, section `Art.21`, and from the same article's official subparagraphs where a provision was split.

## Source read

Directive (EU) 2022/2555, English original OJ Formex, `CELEX:32022L2555`. Article heading: "Article 21" / "Cybersecurity risk-management measures". Those headings state no duty and have no Requirement.

The article has five numbered paragraphs and no footnotes. Paragraph 1 has two subparagraphs. Paragraph 2 is a chapeau plus points (a) to (j). Paragraphs 3 and 4 are single subparagraphs. Paragraph 5 has four subparagraphs. The adapter emits 14 provisions: `21(1)`, `21(2)(a)` through `21(2)(j)`, `21(3)`, `21(4)`, and `21(5)`. For each letter, the adapter repeats the paragraph 2 chapeau in `law_text`.

## How properties were filled

`shall` in the passage is `MUST`. `may` is `MAY`. A passage that contained both was split so one Requirement does not have to drop a modal verb. No passage contains `should`.

`responsible` is set only when the passage names the party that `shall` or `may` acts. That party is Member States or the Commission. Where the subject is "the measures" or "implementing acts", or the sentence is passive, `responsible` is omitted even though an entity's conduct is what Member States must ensure.

`applicability` is used only for a "where" clause that is pointable in that passage: "where applicable, relevant European and international standards", "where appropriate, encryption", and the trailing "where appropriate" in point (j). "When" and "as necessary" stay in `law_text` and in `note`. They are not stored as `applicability`.

`scope` is a verbatim slice of the passage, not a paraphrase. It is omitted when the passage has no enumeration to lift out (point (b), and the examination-procedure sentence).

`exceptions` is omitted on every Requirement. Article 21 does not write an exception. "Where applicable", "where appropriate", "to the extent possible", "at least", and "as necessary" are qualifications, not exceptions.

`note` holds the reading, the cross-reference boundary, and the evidence limit. `remediation_hint` is reviewer advice. Neither one adds a duty the passage does not state.

`discovery_hints` are search aids for realistic artifacts. Path hints may use ordinary filenames the directive does not use, such as `vendor`. `expected_evidence` names the kind of artifact. On entity duties, the note says those artifacts are not proof of appropriateness, proportionality, implementation, or national transposition. On Commission duties, a company security policy is the wrong artifact.

Another article is not copied. Article 22(1), Article 14(4) point (e), and Article 39(2) stay cross-references inside the Article 21 passage that cites them.

## Coverage

| Provision | Requirement | What the Requirement keeps |
| --- | --- | --- |
| Heading | none | No duty |
| `21(1)` first subparagraph | `NIS2-ART21-REF-1-TAKE-MEASURES` | Member States ensure appropriate and proportionate technical, operational, and organisational measures, to manage risks and to prevent or minimise incident impact, for the systems entities use in operations or service provision |
| `21(1)` second subparagraph, first sentence | `NIS2-ART21-REF-1-SECURITY-LEVEL` | Those measures shall ensure a level of security appropriate to the risks, taking into account state-of-the-art, standards where applicable, and cost |
| `21(1)` second subparagraph, second sentence | `NIS2-ART21-REF-1-PROPORTIONALITY` | Proportionality assessment shall take account of exposure, size, likelihood, and severity, including societal and economic impact |
| `21(2)` chapeau | each point `(a)`–`(j)` | All-hazards approach and protection of systems and their physical environment. Not a separate Requirement |
| `21(2)(a)` | `NIS2-ART21-REF-2A-RISK-POLICIES` | Policies on risk analysis and information system security |
| `21(2)(b)` | `NIS2-ART21-REF-2B-INCIDENT-HANDLING` | Incident handling. Reporting duties outside this point are not added |
| `21(2)(c)` | `NIS2-ART21-REF-2C-CONTINUITY` | Business continuity, with backup management and disaster recovery as examples, and crisis management |
| `21(2)(d)` | `NIS2-ART21-REF-2D-SUPPLY-CHAIN` | Supply chain security, including security aspects of relationships with direct suppliers or service providers |
| `21(2)(e)` | `NIS2-ART21-REF-2E-LIFECYCLE-VULNERABILITY` | Security in acquisition, development, and maintenance, including vulnerability handling and disclosure |
| `21(2)(f)` | `NIS2-ART21-REF-2F-EFFECTIVENESS` | Policies and procedures to assess effectiveness of the risk-management measures |
| `21(2)(g)` | `NIS2-ART21-REF-2G-HYGIENE-TRAINING` | Basic cyber hygiene practices and cybersecurity training |
| `21(2)(h)` | `NIS2-ART21-REF-2H-CRYPTOGRAPHY` | Policies and procedures on cryptography; encryption where appropriate |
| `21(2)(i)` | `NIS2-ART21-REF-2I-HR-ACCESS-ASSETS` | Human resources security, access control policies, and asset management |
| `21(2)(j)` | `NIS2-ART21-REF-2J-AUTHENTICATION-COMMS` | Multi-factor or continuous authentication, secured voice, video and text communications, and secured emergency communication systems within the entity, where appropriate |
| `21(3)` first sentence | `NIS2-ART21-REF-3-SUPPLIER-ACCOUNT` | When judging point (d) measures, take into account direct-supplier and service-provider vulnerabilities, and the quality of products and cybersecurity practices, including secure development procedures |
| `21(3)` second sentence | `NIS2-ART21-REF-3-ARTICLE22-RESULTS` | Also take into account results of Article 22(1) coordinated assessments of critical supply chains |
| `21(4)` | `NIS2-ART21-REF-4-CORRECTIVE-MEASURES` | An entity that finds it does not comply with paragraph 2 takes, without undue delay, all necessary, appropriate, and proportionate corrective measures |
| `21(5)` first subparagraph | `NIS2-ART21-REF-5-ACTS-LISTED-ENTITIES` | By 17 October 2024 the Commission shall adopt implementing acts for the listed entity types |
| `21(5)` second subparagraph | `NIS2-ART21-REF-5-ACTS-OTHER-ENTITIES` | The Commission may adopt technical, methodological, and sectoral requirements for other essential and important entities, as necessary |
| `21(5)` third subparagraph, first sentence | `NIS2-ART21-REF-5-PREPARE-STANDARDS` | When preparing those acts, the Commission shall follow European and international standards and relevant technical specifications, to the extent possible |
| `21(5)` third subparagraph, second sentence | `NIS2-ART21-REF-5-COOPERATION-GROUP-ENISA` | The Commission shall exchange advice and cooperate with the Cooperation Group and ENISA on the drafts, in accordance with Article 14(4), point (e) |
| `21(5)` fourth subparagraph | `NIS2-ART21-REF-5-EXAMINATION-PROCEDURE` | Those acts shall be adopted under the examination procedure in Article 39(2) |

Twenty-one Requirements. Every adapter locus has at least one. The builder checks that the split passages reconstruct the adapter paragraph, that each letter's `law_text` is the adapter passage, and that every `shall` or `may` sentence outside the paragraph 2 list is contained in a Requirement.

## Split and consolidation

Paragraph 1 is three Requirements. The security-level sentence and the proportionality sentence are separate duties with different conditions. Keeping them inside the take-measures Requirement would hide both behind one policy document.

Paragraph 2 has no extra chapeau Requirement. The chapeau has the only `shall` for the list, so each letter keeps it. Counting ten all-hazards duties would be wrong; the note on each letter says the chapeau is one parent qualification. Points (a) to (j) stay separate because they call for different evidence. Point (i) is not collapsed into access control. Point (g) is not collapsed into training.

Paragraph 3 is two Requirements. The supplier-vulnerability account and the Article 22(1) results account are different acts, and only the second depends on a Union-level assessment the entity does not perform.

Paragraph 4 stays one Requirement. The finding of non-compliance is the trigger, not a separate detection duty.

Paragraph 5 is five Requirements. The second subparagraph is `MAY`. The standards sentence and the ENISA sentence are split so that "to the extent possible" is not read onto the cooperation duty. The examination procedure is its own sentence and does not name the Commission.

Overlaps that were kept, not merged:

- Point (a) is minimum content of the paragraph 1 measures, not a copy of paragraph 1.
- Paragraph 3 qualifies point (d). It does not replace point (d).
- Point (f) assesses effectiveness. Paragraph 4 is corrective action after a finding of non-compliance with paragraph 2.
- The paragraph 5 acts lay down requirements for the paragraph 2 measures. They are Commission duties, not entity measures.

## Evidence is not compliance

For the entity-facing Requirements, a policy, procedure, training record, supplier file, or corrective-action note can show that the topic was addressed. It does not show that the measure is appropriate or proportionate, that it is implemented, or that national law requires it. The legal addressee of `shall` in paragraphs 1, 3, and 4 is Member States.

For paragraph 5, the artifact is a Commission act or a record of the Commission's preparation, consultation, or adoption procedure. Material in a product repository does not establish those facts. The `MAY` Requirement is satisfied, as a matter of this sentence, if no further act exists.

## Unresolved questions

These are left open. They are not resolved by a note.

1. **Point (j), "where appropriate".** The phrase is at the end of the point. It may qualify the whole point or only the secured emergency communication systems. `applicability` stores the phrase. The note records the ambiguity.
2. **Point (j), "within the entity".** It may modify only the emergency systems, or also the secured voice, video, and text communications.
3. **Point (c), crisis management.** The reading used here is that backup management and disaster recovery are examples of business continuity, and crisis management is a further limb. It can also be read as a further example. Either reading keeps the words in the Requirement.
4. **"Where applicable" in paragraph 1.** The reading used here is that it qualifies "relevant European and international standards", because of where the commas sit, and not the state-of-the-art or the cost. A broader reading is possible.
5. **"Direct" in paragraph 3.** It clearly qualifies "each direct supplier and service provider". The next clause says "their suppliers and service providers" and does not repeat "direct". The Requirement does not narrow that second clause.
6. **`responsible`.** The field is the party the modal verb names. A later human review could still decide that, where both Member States and the entities are named, the entity is the more useful value. That would be a different reading of the Packs v2 field, not a second duty.
7. **Names.** No confirmed product id or locator convention is used. Locators follow the adapter locus (`21(1)`, `21(2)(a)`), in the same shape as the Packs v2 examples `13(4)` and `VII.3`.
8. **Outside this article.** Definitions of essential and important entities, network and information systems, incident, and the listed service types live in other provisions and annexes. They are not restated. National transposition is a different instrument. Whether the Commission adopted the paragraph 5 acts, and what they contain, is not decided from this text.

## What this directory is not

The Requirements implementation plan checkpoint was not updated. Another task is using that file for the CRA reference and later agent runs. Writing the same checkpoint would collide, so this review is the resume record for this reference only.

The regulation adapter, application code, prompts, Packs v2, architecture, policies, and PoC1 were not modified.

## Validation

From `poc2/`, the builder calls `save_pack(..., sealed=False)` and `save_requirement(..., published=False)`, reloads the directory with `load_pack_directory`, and checks the coverage and pointability rules above.

```text
.venv/bin/python data/reference/nis2-article-21-agent-produced/build_reference.py
```

Result: exit 0. 21 Requirements reloaded. No `signed`, no `origin`, and no `source.edition`.

```text
.venv/bin/python -m unittest tests.test_formex_package tests.test_formex_no_number_leak tests.test_formex_provisions_cra tests.test_formex_inventory tests.test_xml_adapters tests.test_m1_requirement
```

Result: 29 tests, OK. Those tests cover the pinned NIS2 Formex bytes, Article 21 loci, and unsigned Requirement validation. The full PoC2 suite was not re-run; this step does not change application code.

Hashes of the Formex inputs and of these outputs are in `PROVENANCE.md`. That file's own hash is not stored inside it.
