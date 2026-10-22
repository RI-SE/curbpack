"""Build an unsigned NIS2 Article 21 reference pack.

This is an analyst reference for later comparison. It does not call a model,
does not read extraction prompts or agent run outputs, and does not write a
working copy or a published Pack.

Requirement ids are directory labels. They are not a product naming convention.
Passages for lettered paragraph 2 points are the deterministic adapter's
``law_text``. Split paragraphs use the same ``wrap_law`` function on the
official subparagraph or sentence, and the script checks that those pieces
reconstruct the adapter passage.
"""

from __future__ import annotations

import hashlib
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
POC2 = ROOT / "poc2"
sys.path.insert(0, str(POC2))

from common.store import load_pack_directory, save_pack, save_requirement  # noqa: E402
from requirements.extract.adapter import ADAPTERS, load_adapter, section_provisions  # noqa: E402
from requirements.extract.formex.package import OFFICIAL_XML, load_doc_package  # noqa: E402
from requirements.extract.formex.provisions import _find_article, wrap_law  # noqa: E402
from requirements.extract.formex.text import collapse_ws, element_text, local_tag  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "unsigned"
REVIEW = HERE / "REVIEW.md"
PROVENANCE = HERE / "PROVENANCE.md"
PACK_ID = "nis2-article-21-agent-reference"

SOURCE = {
    "framework": "EU",
    "instrument": "NIS2",
    "identifier": "CELEX:32022L2555",
    "language": "en",
    "url": "https://publications.europa.eu/resource/celex/32022L2555",
}

DOCUMENTS_AND_GIT = [{"source": "documents"}, {"source": "git"}]
DOCUMENTS_ONLY = [{"source": "documents"}]

EVIDENCE_NOT_PROOF = (
    "Discovery hints name plausible artifacts. They are not proof that a "
    "measure is appropriate, proportionate, or in place, and they are not "
    "proof that a Member State has transposed this duty."
)

CHAPEAU_NOTE = (
    "The paragraph 2 chapeau is kept in this passage so that 'shall' stays "
    "pointable. The all-hazards approach, and the aim of protecting network "
    "and information systems and their physical environment, are that shared "
    "parent qualification. They are not ten separate duties. 'At least' means "
    "the list is a minimum. This passage does not itself name essential and "
    "important entities; the chapeau refers to the measures in paragraph 1."
)

_MODAL = re.compile(r"\b(shall|may|should)\b", re.IGNORECASE)


def split_once(text: str, boundary: str) -> tuple[str, str]:
    """Split ``text`` on a boundary that starts with '. '."""
    if not boundary.startswith(". "):
        raise SystemExit(f"boundary must start with a period and space: {boundary!r}")
    index = text.index(boundary)
    left = text[: index + 1]
    right = text[index + 2 :]
    if left + " " + right != text:
        raise SystemExit("split did not reconstruct the source passage")
    return left, right


def article_parts() -> tuple[str, str, list[str]]:
    package = load_doc_package(OFFICIAL_XML / "nis2")
    body = next(part for part in package["parts"] if part["kind"] == "body")
    article = _find_article(ET.parse(body["file"]).getroot(), "21")
    if article is None:
        raise SystemExit("Article 21 not found")
    title = ""
    subtitle = ""
    alineas: list[str] = []
    for child in list(article):
        tag = local_tag(child.tag)
        if tag == "TI.ART":
            title = element_text(child)
        elif tag == "STI.ART":
            subtitle = element_text(child)
        elif tag == "PARAG":
            for grandchild in list(child):
                if local_tag(grandchild.tag) == "ALINEA":
                    alineas.append(element_text(grandchild))
    if len(alineas) != 9:
        raise SystemExit(f"expected 9 alineas, found {len(alineas)}")
    return title, subtitle, alineas


def hints(
    concepts: list[str],
    path_hints: list[str],
    expected: list[str],
    sources: list[dict] | None = None,
) -> dict:
    return {
        "concepts": concepts,
        "path_hints": path_hints,
        "sources": sources if sources is not None else DOCUMENTS_AND_GIT,
        "expected_evidence": expected,
    }


def requirement(
    requirement_id: str,
    locator: str,
    law_text: str,
    *,
    strength: str,
    note: str,
    remediation_hint: str,
    discovery: dict,
    responsible: str | None = None,
    applicability: str | None = None,
    scope: str | None = None,
) -> dict:
    body = {
        "id": requirement_id,
        "pack_id": PACK_ID,
        "strength": strength,
        "remediation_hint": remediation_hint,
        "source": dict(SOURCE),
        "references": [{"nr": 1, "locator": locator, "law_text": law_text}],
        "note": note,
        "discovery_hints": discovery,
    }
    if responsible is not None:
        body["responsible"] = responsible
    if applicability is not None:
        body["applicability"] = applicability
    if scope is not None:
        body["scope"] = scope
    return body


def _slice_from(text: str, start: str, *, drop_final_period: bool = False) -> str:
    index = text.index(start)
    chunk = text[index:]
    if drop_final_period and chunk.endswith("."):
        chunk = chunk[:-1]
    return chunk


def build_requirements(by_locus: dict[str, str], alineas: list[str]) -> list[dict]:
    measures = alineas[0]
    level, proportionality = split_once(alineas[1], ". When assessing")
    supplier, article_22 = split_once(alineas[3], ". Member States shall also")
    standards, consultation = split_once(alineas[7], ". The Commission shall exchange")
    listed = alineas[5]
    other = alineas[6]
    examination = alineas[8]

    level_scope = (
        "the state-of-the-art and, where applicable, relevant European and "
        "international standards, as well as the cost of implementation"
    )
    prop_scope = _slice_from(
        proportionality,
        "the degree of the entity",
        drop_final_period=True,
    )
    supplier_scope = _slice_from(
        supplier,
        "the vulnerabilities specific to each direct supplier",
        drop_final_period=True,
    )
    article_22_scope = _slice_from(
        article_22,
        "the results of the coordinated security risk assessments",
        drop_final_period=True,
    )
    listed_scope = _slice_from(
        listed,
        "DNS service providers",
        drop_final_period=True,
    )

    letters = {
        "21(2)(a)": (
            "NIS2-ART21-REF-2A-RISK-POLICIES",
            "risk analysis and information system security",
            "One listed item: policies on risk analysis and information system security. "
            "This is minimum content of the paragraph 1 measures, not a second statement of paragraph 1.",
            "Look for policies that address both risk analysis and information system security.",
            hints(
                ["risk analysis policy", "information system security policy"],
                ["*risk*polic*", "*information*security*"],
                ["risk analysis policy", "information system security policy"],
            ),
        ),
        "21(2)(b)": (
            "NIS2-ART21-REF-2B-INCIDENT-HANDLING",
            None,
            "One listed item: incident handling. Articles on incident reporting are outside this point and are not added.",
            "Look for an incident-handling procedure. A report to an authority is a different duty and is not stated here.",
            hints(
                ["incident handling", "incident response procedure"],
                ["*incident*"],
                ["incident handling procedure"],
            ),
        ),
        "21(2)(c)": (
            "NIS2-ART21-REF-2C-CONTINUITY",
            "business continuity, such as backup management and disaster recovery, and crisis management",
            "Reading: backup management and disaster recovery are examples of business continuity; "
            "crisis management is a further limb of the same point. The examples are not a closed list. "
            "Whether crisis management could instead be read as another example is recorded in the review and does not remove it from the passage.",
            "Look for continuity, backup or recovery, and crisis-management material. An example in the text is not a closed checklist.",
            hints(
                ["business continuity", "backup management", "disaster recovery", "crisis management"],
                ["*continuity*", "*backup*", "*disaster*recovery*", "*crisis*"],
                ["business continuity description", "backup or disaster-recovery procedure", "crisis management procedure"],
            ),
        ),
        "21(2)(d)": (
            "NIS2-ART21-REF-2D-SUPPLY-CHAIN",
            "supply chain security, including security-related aspects concerning the relationships between each entity and its direct suppliers or service providers",
            "'Including' does not close the list. 'Direct' qualifies the relationships named in this point. "
            "Paragraph 3 adds further considerations and is separate.",
            "Look for supply-chain security measures covering relationships with direct suppliers or service providers.",
            hints(
                ["supply chain security", "direct supplier", "service provider"],
                ["*supplier*", "*supply*chain*", "*vendor*"],
                ["supply-chain security measures", "direct supplier or service-provider security arrangements"],
            ),
        ),
        "21(2)(e)": (
            "NIS2-ART21-REF-2E-LIFECYCLE-VULNERABILITY",
            "security in network and information systems acquisition, development and maintenance, including vulnerability handling and disclosure",
            "Acquisition, development, and maintenance are all named. Vulnerability handling and disclosure are included. "
            "This point states no timeline and no recipient.",
            "Look for security practices across acquisition, development, and maintenance, including vulnerability handling and disclosure.",
            hints(
                ["secure acquisition", "secure development", "vulnerability handling", "vulnerability disclosure"],
                ["*vulnerabilit*", "*secure*development*", "*disclosure*"],
                ["lifecycle security practices", "vulnerability handling and disclosure procedure"],
            ),
        ),
        "21(2)(f)": (
            "NIS2-ART21-REF-2F-EFFECTIVENESS",
            "policies and procedures to assess the effectiveness of cybersecurity risk-management measures",
            "This point is about assessing effectiveness. It is not the measures themselves and not the corrective action in paragraph 4. "
            "It names policies and procedures, not a particular metric.",
            "Look for policies or procedures whose purpose is to assess whether risk-management measures work.",
            hints(
                ["effectiveness of cybersecurity measures", "risk-management review"],
                ["*effectiveness*", "*risk*management*"],
                ["policy or procedure for assessing effectiveness of risk-management measures"],
            ),
        ),
        "21(2)(g)": (
            "NIS2-ART21-REF-2G-HYGIENE-TRAINING",
            "basic cyber hygiene practices and cybersecurity training",
            "Both basic cyber hygiene practices and cybersecurity training are named. A training record does not stand in for hygiene practices.",
            "Look for hygiene practices and for cybersecurity training. Either one alone is short of this point.",
            hints(
                ["cyber hygiene", "cybersecurity training", "security awareness"],
                ["*training*", "*hygiene*", "*awareness*"],
                ["basic cyber hygiene practices", "cybersecurity training records"],
            ),
        ),
        "21(2)(h)": (
            "NIS2-ART21-REF-2H-CRYPTOGRAPHY",
            "the use of cryptography and, where appropriate, encryption",
            "'where appropriate' is placed immediately before 'encryption'. It is read as qualifying encryption, "
            "not the duty to have policies and procedures on the use of cryptography.",
            "Look for cryptography policies and procedures. Treat encryption as conditional on 'where appropriate', which this point does not define.",
            hints(
                ["cryptography policy", "encryption"],
                ["*cryptograph*", "*encrypt*"],
                ["cryptography policy or procedure", "encryption practice where encryption is appropriate"],
            ),
        ),
        "21(2)(i)": (
            "NIS2-ART21-REF-2I-HR-ACCESS-ASSETS",
            "human resources security, access control policies and asset management",
            "Three subjects are named. Access control does not stand in for human resources security or asset management.",
            "Look for human resources security, access control policies, and asset management. All three are in the point.",
            hints(
                ["human resources security", "access control policy", "asset management"],
                ["*access*control*", "*asset*", "*personnel*"],
                ["human resources security practice", "access control policy", "asset management record"],
            ),
        ),
        "21(2)(j)": (
            "NIS2-ART21-REF-2J-AUTHENTICATION-COMMS",
            "multi-factor authentication or continuous authentication solutions, secured voice, video and text communications and secured emergency communication systems within the entity",
            "Unresolved attachment: the trailing 'where appropriate' may qualify the whole point or only the last system. "
            "'Or' between multi-factor authentication and continuous authentication solutions is an alternative. "
            "'Within the entity' may modify only the emergency systems or also the secured communications. "
            "Voice, video, and text are joined by 'and'.",
            "Look for multi-factor or continuous authentication, and for secured voice, video, and text communications and secured emergency systems. Do not treat both authentication forms as always required.",
            hints(
                ["multi-factor authentication", "continuous authentication", "secured communications", "emergency communication"],
                ["*multi*factor*", "*authentication*", "*mfa*"],
                [
                    "multi-factor or continuous authentication practice",
                    "secured voice, video, and text communications",
                    "secured emergency communication systems",
                ],
            ),
        ),
    }

    built: list[dict] = [
        requirement(
            "NIS2-ART21-REF-1-TAKE-MEASURES",
            "21(1)",
            wrap_law(measures),
            strength="MUST",
            responsible="Member States",
            scope=_slice_from(
                measures,
                "technical, operational and organisational measures",
                drop_final_period=True,
            ),
            remediation_hint=(
                "Look for the technical, operational, and organisational measures applied to the "
                "network and information systems used for operations or services, covering both risk "
                "management and incident impact. 'Appropriate and proportionate' is not defined numerically here."
            ),
            note=(
                "The duty named by 'shall' is on Member States. The conduct they must ensure is that of "
                "essential and important entities. Both aims are in the passage: manage the risks, and "
                "prevent or minimise the impact of incidents. The systems are those the entities use for "
                "their operations or for the provision of their services. "
                + EVIDENCE_NOT_PROOF
            ),
            discovery=hints(
                [
                    "cybersecurity risk management",
                    "technical measures",
                    "operational measures",
                    "organisational measures",
                    "incident impact",
                ],
                ["*risk*management*", "*security*measures*", "*nis2*"],
                [
                    "risk-management policy",
                    "description of technical, operational, and organisational measures",
                ],
            ),
        ),
        requirement(
            "NIS2-ART21-REF-1-SECURITY-LEVEL",
            "21(1)",
            wrap_law(level),
            strength="MUST",
            applicability="where applicable, relevant European and international standards",
            scope=level_scope,
            remediation_hint=(
                "Look for how the security level of the paragraph 1 measures was judged against the risks, "
                "including state-of-the-art, cost, and standards where applicable."
            ),
            note=(
                "No party is the subject of 'shall'; the measures shall ensure the level of security. "
                "'where applicable' is read as qualifying the standards, not the state-of-the-art or the cost. "
                "'The first subparagraph' means the take-measures passage in this same paragraph. "
                + EVIDENCE_NOT_PROOF
            ),
            discovery=hints(
                [
                    "state-of-the-art",
                    "security level",
                    "cost of implementation",
                    "European standard",
                    "international standard",
                ],
                ["*risk*assessment*", "*standard*"],
                [
                    "record of the security level judged against the risks",
                    "standards considered where applicable",
                ],
            ),
        ),
        requirement(
            "NIS2-ART21-REF-1-PROPORTIONALITY",
            "21(1)",
            wrap_law(proportionality),
            strength="MUST",
            scope=prop_scope,
            remediation_hint=(
                "Look for a proportionality assessment that takes account of exposure, size, likelihood, "
                "and severity, including societal and economic impact."
            ),
            note=(
                "'When assessing' is a condition of this sentence. It is not a 'where' clause, so "
                "applicability is omitted. The sentence names no duty-holder. The factors are cumulative. "
                "'Those measures' refers to the measures in this paragraph. "
                + EVIDENCE_NOT_PROOF
            ),
            discovery=hints(
                [
                    "proportionality",
                    "risk exposure",
                    "entity size",
                    "incident likelihood",
                    "incident severity",
                    "societal impact",
                ],
                ["*proportional*", "*risk*assessment*"],
                ["proportionality assessment covering exposure, size, likelihood, and severity"],
            ),
        ),
    ]

    for locus, (requirement_id, scope, specific_note, remediation, discovery) in letters.items():
        note = CHAPEAU_NOTE + " " + specific_note + " " + EVIDENCE_NOT_PROOF
        if locus == "21(2)(h)":
            applicability = "where appropriate, encryption"
        elif locus == "21(2)(j)":
            applicability = "where appropriate"
        else:
            applicability = None
        built.append(
            requirement(
                requirement_id,
                locus,
                by_locus[locus],
                strength="MUST",
                applicability=applicability,
                scope=scope,
                remediation_hint=remediation,
                note=note,
                discovery=discovery,
            )
        )

    built.extend(
        [
            requirement(
                "NIS2-ART21-REF-3-SUPPLIER-ACCOUNT",
                "21(3)",
                wrap_law(supplier),
                strength="MUST",
                responsible="Member States",
                scope=supplier_scope,
                remediation_hint=(
                    "Look for how direct-supplier and service-provider vulnerabilities, and the quality "
                    "of products and cybersecurity practices of suppliers and service providers, were taken "
                    "into account when judging supply-chain measures."
                ),
                note=(
                    "This applies when considering which paragraph 2, point (d), measures are appropriate. "
                    "That is a 'when' condition, so applicability is omitted. The vulnerability clause says "
                    "'each direct supplier and service provider'. The quality and practices clause says "
                    "'their suppliers and service providers' and does not repeat 'direct'. Secure development "
                    "procedures are an inclusion, not a complete catalogue. "
                    + EVIDENCE_NOT_PROOF
                ),
                discovery=hints(
                    [
                        "supplier vulnerability",
                        "service provider vulnerability",
                        "supplier cybersecurity practices",
                        "secure development procedure",
                    ],
                    ["*supplier*", "*third*party*", "*vendor*"],
                    [
                        "account of vulnerabilities specific to each direct supplier and service provider",
                        "account of supplier product quality and cybersecurity practices",
                    ],
                ),
            ),
            requirement(
                "NIS2-ART21-REF-3-ARTICLE22-RESULTS",
                "21(3)",
                wrap_law(article_22),
                strength="MUST",
                responsible="Member States",
                scope=article_22_scope,
                remediation_hint=(
                    "Look for a record that results of Article 22(1) coordinated supply-chain assessments "
                    "were taken into account when judging point (d) measures. This passage does not require "
                    "the entity to carry out that Union-level assessment."
                ),
                note=(
                    "Cross-reference only. Article 22 is not copied into this requirement. The passage does "
                    "not say that such a result exists for every entity. "
                    + EVIDENCE_NOT_PROOF
                ),
                discovery=hints(
                    ["Article 22", "coordinated security risk assessment", "critical supply chain"],
                    ["*article*22*", "*supply*chain*assessment*"],
                    ["record that coordinated critical-supply-chain assessment results were taken into account"],
                ),
            ),
            requirement(
                "NIS2-ART21-REF-4-CORRECTIVE-MEASURES",
                "21(4)",
                wrap_law(alineas[4]),
                strength="MUST",
                responsible="Member States",
                scope="all necessary, appropriate and proportionate corrective measures",
                remediation_hint=(
                    "Look for corrective measures taken without undue delay after the entity finds it does "
                    "not comply with the paragraph 2 measures. This passage does not define the delay or "
                    "require the finding itself."
                ),
                note=(
                    "The trigger is an entity that finds non-compliance with the paragraph 2 measures. "
                    "Detection is not a separate duty in this paragraph. 'Without undue delay' has no duration here. "
                    "The passage is not extended to paragraph 1 or paragraph 3. Necessary, appropriate, and "
                    "proportionate all qualify the corrective measures. "
                    + EVIDENCE_NOT_PROOF
                ),
                discovery=hints(
                    ["corrective measures", "non-compliance", "undue delay"],
                    ["*corrective*", "*non-compliance*", "*noncompliance*", "*remediat*"],
                    ["corrective-action record for a found gap against the paragraph 2 measures"],
                ),
            ),
            requirement(
                "NIS2-ART21-REF-5-ACTS-LISTED-ENTITIES",
                "21(5)",
                wrap_law(listed),
                strength="MUST",
                responsible="the Commission",
                scope=listed_scope,
                remediation_hint=(
                    "Look for the Commission implementing acts required by 17 October 2024 for the listed "
                    "entity types. A company security policy is not that act."
                ),
                note=(
                    "The deadline is in the passage. This reference does not decide whether the acts were "
                    "adopted or what they contain. The entity list is closed for this subparagraph and keeps "
                    "the wording 'online market places'. "
                    "A product security document is not evidence of the Commission's act."
                ),
                discovery=hints(
                    ["Commission implementing act", "Article 21", "32022L2555", "online market places"],
                    ["*implementing*act*", "*32022L2555*"],
                    ["Commission implementing act for the entity types listed in this subparagraph"],
                    DOCUMENTS_ONLY,
                ),
            ),
            requirement(
                "NIS2-ART21-REF-5-ACTS-OTHER-ENTITIES",
                "21(5)",
                wrap_law(other),
                strength="MAY",
                responsible="The Commission",
                scope="the technical and the methodological requirements, as well as sectoral requirements",
                remediation_hint=(
                    "Look for a Commission implementing act for other essential or important entities only "
                    "if one was adopted. 'May' is not a duty to adopt an act for every such entity."
                ),
                note=(
                    "'May' is the modal verb. 'As necessary' and 'other than those referred to in the first "
                    "subparagraph' limit this power. Sectoral requirements are named as well as technical and "
                    "methodological requirements. Absence of an act is consistent with this sentence."
                ),
                discovery=hints(
                    ["Commission implementing act", "sectoral requirements", "essential and important entities"],
                    ["*implementing*act*", "*sectoral*"],
                    ["Commission implementing act for other essential or important entities, if adopted"],
                    DOCUMENTS_ONLY,
                ),
            ),
            requirement(
                "NIS2-ART21-REF-5-PREPARE-STANDARDS",
                "21(5)",
                wrap_law(standards),
                strength="MUST",
                responsible="the Commission",
                scope="European and international standards, as well as relevant technical specifications",
                remediation_hint=(
                    "Look for how the Commission, when preparing the implementing acts of the first and second "
                    "subparagraphs, followed European and international standards and relevant technical "
                    "specifications to the extent possible."
                ),
                note=(
                    "'When preparing' limits this sentence to those implementing acts. 'To the extent possible' "
                    "qualifies the duty. It is not written as an exception, so exceptions is omitted. "
                    "Technical specifications are named separately from standards. A company's choice of a "
                    "standard is not evidence of this Commission duty."
                ),
                discovery=hints(
                    ["European standard", "international standard", "technical specification", "implementing act"],
                    ["*implementing*act*"],
                    ["preparatory record on standards and technical specifications for the Article 21(5) acts"],
                    DOCUMENTS_ONLY,
                ),
            ),
            requirement(
                "NIS2-ART21-REF-5-COOPERATION-GROUP-ENISA",
                "21(5)",
                wrap_law(consultation),
                strength="MUST",
                responsible="The Commission",
                scope="exchange advice and cooperate with the Cooperation Group and ENISA",
                remediation_hint=(
                    "Look for exchange of advice and cooperation with the Cooperation Group and ENISA on the "
                    "draft implementing acts, as referred to in Article 14(4), point (e)."
                ),
                note=(
                    "Article 14(4), point (e), is a cross-reference and is not copied. The duty in this sentence "
                    "is on the Commission. It is not a duty written onto ENISA or the Cooperation Group. "
                    "A company consultation record is not evidence of this duty."
                ),
                discovery=hints(
                    ["Cooperation Group", "ENISA", "draft implementing act", "Article 14(4)"],
                    ["*enisa*", "*cooperation*group*"],
                    ["record of Commission advice and cooperation with the Cooperation Group and ENISA"],
                    DOCUMENTS_ONLY,
                ),
            ),
            requirement(
                "NIS2-ART21-REF-5-EXAMINATION-PROCEDURE",
                "21(5)",
                wrap_law(examination),
                strength="MUST",
                remediation_hint=(
                    "Look for adoption of those implementing acts through the examination procedure referred "
                    "to in Article 39(2). The sentence does not name the Commission."
                ),
                note=(
                    "This is the adoption procedure for those implementing acts. Article 39(2) is not copied. "
                    "No party is named, so responsible is omitted. A product repository does not establish "
                    "which committee procedure was used."
                ),
                discovery=hints(
                    ["examination procedure", "Article 39(2)", "implementing act"],
                    ["*implementing*act*"],
                    ["adoption record citing the examination procedure in Article 39(2)"],
                    DOCUMENTS_ONLY,
                ),
            ),
        ]
    )
    return built


def _law(requirement_obj: dict) -> str:
    return requirement_obj["references"][0]["law_text"]


def assert_pointable(requirement_obj: dict) -> None:
    flat = collapse_ws(_law(requirement_obj))
    requirement_id = requirement_obj["id"]
    modals = {match.group(1).lower() for match in _MODAL.finditer(flat)}
    strength = requirement_obj["strength"]
    if strength == "MUST":
        if "shall" not in modals or "may" in modals or "should" in modals:
            raise SystemExit(f"{requirement_id} strength MUST but modals are {sorted(modals)}")
    elif strength == "MAY":
        if modals != {"may"}:
            raise SystemExit(f"{requirement_id} strength MAY but modals are {sorted(modals)}")
    else:
        raise SystemExit(f"{requirement_id} unexpected strength {strength}")
    for field in ("responsible", "applicability", "scope"):
        if field in requirement_obj and requirement_obj[field] not in flat:
            raise SystemExit(f"{requirement_id} {field} is not a substring of law_text: {requirement_obj[field]!r}")
    if "exceptions" in requirement_obj:
        raise SystemExit(f"{requirement_id} exceptions was set, but Article 21 writes no exception clause")
    for forbidden in ("signed", "origin", "edition"):
        if forbidden in requirement_obj or forbidden in requirement_obj.get("source", {}):
            raise SystemExit(f"{requirement_id} must not carry {forbidden}")


def assert_coverage(by_locus: dict[str, str], alineas: list[str], requirements: list[dict]) -> None:
    expected = ["21(1)", *[f"21(2)({letter})" for letter in "abcdefghij"], "21(3)", "21(4)", "21(5)"]
    if list(by_locus) != expected:
        raise SystemExit(f"adapter loci changed: {list(by_locus)}")
    by_id = {item["id"]: item for item in requirements}
    if len(by_id) != len(requirements):
        raise SystemExit("duplicate requirement id")

    paragraph_text = {
        "21(1)": collapse_ws(alineas[0] + " " + alineas[1]),
        "21(3)": collapse_ws(alineas[3]),
        "21(4)": collapse_ws(alineas[4]),
        "21(5)": collapse_ws(" ".join(alineas[5:])),
    }
    grouped: dict[str, list[str]] = {locus: [] for locus in expected}
    for item in requirements:
        locator = item["references"][0]["locator"]
        if locator not in grouped:
            raise SystemExit(f"locator {locator} is not an Article 21 adapter locus")
        grouped[locator].append(collapse_ws(_law(item)))
        assert_pointable(item)

    for locus, pieces in grouped.items():
        if locus.startswith("21(2)("):
            if pieces != [collapse_ws(by_locus[locus])]:
                raise SystemExit(f"{locus} law_text is not the adapter passage")
            continue
        joined = " ".join(pieces)
        if joined != paragraph_text[locus]:
            raise SystemExit(f"{locus} pieces do not reconstruct the paragraph")
        if locus in by_locus and collapse_ws(by_locus[locus]) != paragraph_text[locus]:
            raise SystemExit(f"adapter passage for {locus} differs from the alinea text")

    chapeau = (
        "The measures referred to in paragraph 1 shall be based on an all-hazards "
        "approach that aims to protect network and information systems and the physical "
        "environment of those systems from incidents, and shall include at least the following:"
    )
    for letter in "abcdefghij":
        if chapeau not in collapse_ws(by_locus[f"21(2)({letter})"]):
            raise SystemExit(f"chapeau missing from 21(2)({letter})")

    shall_or_may = []
    for index, alinea in enumerate(alineas):
        if not alinea.endswith("."):
            raise SystemExit(f"alinea does not end with a period: {alinea[-40:]!r}")
        # Paragraph 2 is one list. Its 'shall' is the shared chapeau on each letter.
        if index == 2:
            continue
        for sentence in alinea.split(". "):
            if not sentence.endswith("."):
                sentence = sentence + "."
            if _MODAL.search(sentence):
                shall_or_may.append(collapse_ws(sentence))
    flats = [collapse_ws(_law(item)) for item in requirements]
    for sentence in shall_or_may:
        if not any(sentence in flat for flat in flats):
            raise SystemExit(f"no requirement contains sentence: {sentence}")
    if len(by_id) != 21:
        raise SystemExit(f"expected 21 requirements, found {len(by_id)}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_provenance(title: str, subtitle: str, source_file: str) -> None:
    input_paths = [
        POC2 / "requirements/extract/data/official_xml/MANIFEST.json",
        POC2 / "requirements/extract/data/official_xml/nis2/L_2022333EN.fmx4.zip",
        POC2 / "requirements/extract/data/official_xml/nis2/L_2022333EN.01008001.doc.xml",
        Path(source_file),
        ADAPTERS / "nis" / "adapter.json",
        Path(__file__),
        REVIEW,
    ]
    lines = [
        "# NIS2 Article 21 agent reference — provenance",
        "",
        "**Label.** A Cursor agent produced this reference from the official English Formex text of Directive (EU) 2022/2555, Article 21. It is not legally certified and it has not been independently human-reviewed. It is not an extraction-agent result.",
        "",
        "The pack directory contains only `pack.json` and Requirement JSON. This file and `REVIEW.md` sit beside that directory so they are not Requirement files and are not part of a pack directory seal.",
        "",
        "SHA-256 is of the file bytes. This file's own hash is not stored here.",
        "",
        "## Source identity",
        "",
        "| Fact | Value |",
        "| --- | --- |",
        "| Instrument | Directive (EU) 2022/2555 (NIS 2 Directive) |",
        "| Identifier | `CELEX:32022L2555` |",
        "| Language | en |",
        "| Edition used | Original OJ Formex, OJ L 333, 27 December 2022. Act date 14 December 2022. Not a consolidation and not national implementing law. |",
        "| `source.edition` on Requirements | Omitted. An unsigned draft does not invent the edition a reviewer has to confirm. The OJ date above is the manifest fact. |",
        "| Retrieval URL | `https://publications.europa.eu/resource/celex/32022L2555` |",
        "| Article heading read | " + f"`{title}` / `{subtitle}` |",
        "| Adapter | `nis`, section `Art.21`, deterministic provisions only |",
        "",
        "## Inputs and records",
        "",
        "| Path | SHA-256 |",
        "| --- | --- |",
    ]
    for path in input_paths:
        if not path.is_file():
            raise SystemExit(f"missing provenance input: {path}")
        lines.append(f"| `{path.relative_to(ROOT)}` | `{sha256(path)}` |")
    lines.extend(["", "## Reference pack files", "", "| Path | SHA-256 |", "| --- | --- |"])
    for path in [OUT / "pack.json", *sorted(OUT.glob("NIS2-ART21-REF-*.json"))]:
        lines.append(f"| `{path.relative_to(ROOT)}` | `{sha256(path)}` |")
    lines.append("")
    PROVENANCE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    adapter = load_adapter(ADAPTERS / "nis" / "adapter.json")
    extracted = section_provisions(ADAPTERS / "nis", adapter, "Art.21")
    by_locus = {item["locus"]: item["law_text"] for item in extracted["provisions"]}
    title, subtitle, alineas = article_parts()
    requirements = build_requirements(by_locus, alineas)
    assert_coverage(by_locus, alineas, requirements)

    if OUT.exists():
        for path in OUT.glob("*.json"):
            path.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    save_pack(
        OUT,
        {
            "id": PACK_ID,
            "name": "NIS2 Article 21 agent reference",
            "version": "0.0.0-reference",
            "assurance_class": "structural_draft",
            "description": (
                "Agent-produced unsigned reference for Directive (EU) 2022/2555 Article 21 only. "
                "Not legally certified and not independently human-reviewed. Not a published Pack "
                "and not an extraction-agent result. Requirement ids are reference labels, not a "
                "product naming convention."
            ),
            "jurisdiction": "EU",
            "source": {
                "framework": "EU",
                "instrument": "NIS2",
                "url": SOURCE["url"],
            },
        },
        sealed=False,
    )
    for item in requirements:
        save_requirement(OUT, item, published=False)

    pack, loaded = load_pack_directory(OUT)
    if pack["id"] != PACK_ID or len(loaded) != 21:
        raise SystemExit("reload failed")
    if "signed" in pack:
        raise SystemExit("pack must be unsigned")
    print(f"title: {title}")
    print(f"subtitle: {subtitle}")
    print(f"source file: {extracted['file']}")
    print(f"requirements: {len(loaded)}")
    for item in loaded:
        ref = item["references"][0]
        print(f"{item['id']}\t{ref['locator']}\t{item['strength']}")
    if not REVIEW.is_file():
        raise SystemExit(f"write {REVIEW.name} before provenance")
    write_provenance(title, subtitle, extracted["file"])
    print(f"provenance: {PROVENANCE}")
    print(f"provenance sha256: {sha256(PROVENANCE)}")


if __name__ == "__main__":
    main()
