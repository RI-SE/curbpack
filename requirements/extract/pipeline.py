"""Annex VII point 3 helper and the old search-plan shape conversion."""

from __future__ import annotations

from pathlib import Path

from common.errors import ModelError
from requirements.extract.assemble import assemble_requirements
from requirements.extract.adapter import ADAPTERS, load_adapter
from requirements.extract.atomize import atomize

DATA = Path(__file__).resolve().parent / "data"
FIXTURE = DATA / "annex_vii.txt"

CRA_SOURCE = {
    "framework": "EU",
    "instrument": "CRA",
    "identifier": "CELEX:32024R2847",
    "language": "en",
    "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847",
}

# The values the existing Annex VII point 3 tests already require.
# This helper does not read the locus map files.
_POINT_3_HINTS = {
    "concepts": [
        "risk assessment",
        "cybersecurity risk",
        "threat model",
        "STRIDE",
        "identified risks",
        "residual risk",
        "Annex I",
    ],
    "path_hints": [
        "*risk*assessment*",
        "*threat*model*",
        "*CRA*ASSESSMENT*",
        "*THREAT*",
    ],
    "sources": [{"source": "documents"}, {"source": "requirements"}],
    "expected_evidence": ["process description", "requirement"],
}


def draft_pack() -> dict:
    return {
        "id": "cra-baseline",
        "name": "CRA baseline",
        "version": "0.1.0",
        "description": "CRA applies to products with digital elements.",
        "source": {
            "framework": "EU",
            "instrument": "CRA",
            "url": CRA_SOURCE["url"],
        },
    }


def _source_entry(item: object) -> dict:
    if isinstance(item, str):
        return {"source": item}
    if isinstance(item, dict) and isinstance(item.get("source"), str):
        entry = {"source": item["source"]}
        if isinstance(item.get("args"), dict):
            entry["args"] = item["args"]
        return entry
    raise ValueError(f"search source is not a source id: {item!r}")


def discovery_hints_from_search(search: dict) -> dict:
    """Step 03 search plan → Requirement.discovery_hints. Drops nothing into `search`."""
    hints: dict = {}
    for field in ("concepts", "path_hints", "expected_evidence"):
        values = search.get(field)
        if values:
            hints[field] = list(values)
    sources = search.get("sources") or []
    if sources:
        hints["sources"] = [_source_entry(item) for item in sources]
    return hints


def extract_annex_vii_risk() -> dict:
    """Unsigned CRA-ANNEX-VII-RISK from the controlled Annex VII fixture."""
    provisions = [
        {"locus": item["locus"], "law_text": item["law_text"]}
        for item in atomize(FIXTURE.read_text(encoding="utf-8"))
    ]
    proposals = [
        {
            "locus": "3",
            "id": "CRA-ANNEX-VII-RISK",
            "locator": "VII.3",
            "discovery_hints": _POINT_3_HINTS,
        }
    ]
    adapter = load_adapter(ADAPTERS / "cra" / "adapter.json")
    requirements, _exclusions = assemble_requirements(provisions, proposals, adapter=adapter)
    match = next((item for item in requirements if item["id"] == "CRA-ANNEX-VII-RISK"), None)
    if match is None:
        raise ModelError("CRA-ANNEX-VII-RISK", "id", "an assembled requirement")
    return match
