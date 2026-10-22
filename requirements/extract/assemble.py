"""Validate interpret and discovery-hint proposals, then assemble unsigned Requirements."""

from __future__ import annotations

from common.errors import ModelError
from common.validate import validate_requirement

_INTERPRET_FIELDS = {
    "locus",
    "id",
    "locator",
    "note",
    "strength",
    "responsible",
    "applicability",
    "exceptions",
    "scope",
}
_HINTS_FIELDS = {"locus", "discovery_hints"}
_ALLOWED_FIELDS = _INTERPRET_FIELDS | _HINTS_FIELDS
_COPY_FIELDS = (
    "note",
    "strength",
    "responsible",
    "applicability",
    "exceptions",
    "scope",
    "discovery_hints",
)


def validate_interpret_proposal(proposal: dict, loci: set[str]) -> dict:
    """Check one stage-02 proposal. An unknown locus is an error here."""
    _reject_unexpected(proposal, _INTERPRET_FIELDS, "interpret proposal")
    locus = _required_locus(proposal, "interpret proposal")
    if locus not in loci:
        raise ModelError("interpret proposal", "locus", f"one of the provisions, not {locus}")
    return proposal


def validate_hints_proposal(proposal: dict, loci: set[str]) -> dict:
    """Check one stage-03 proposal. An unknown locus is an error here."""
    _reject_unexpected(proposal, _HINTS_FIELDS, "hints proposal")
    locus = _required_locus(proposal, "hints proposal")
    if locus not in loci:
        raise ModelError("hints proposal", "locus", f"one of the provisions, not {locus}")
    if "discovery_hints" in proposal:
        _check_hints_shape(proposal["discovery_hints"])
    return proposal


def assemble_requirements(
    provisions: list[dict],
    proposals: list[dict],
    *,
    adapter: dict,
) -> tuple[list[dict], list[dict]]:
    """Build unsigned Requirements. Incomplete loci are exclusions, not dropped."""
    provision_loci = _provision_loci(provisions)
    by_locus = {item["locus"]: item for item in provisions}
    _reject_duplicate_kind(proposals)
    merged = _merge_proposals(proposals)
    known = set(provision_loci)

    requirements: list[dict] = []
    exclusions: list[dict] = []
    for locus in provision_loci:
        proposal = merged.get(locus)
        if proposal is None:
            exclusions.append({"locus": locus, "reason": "no proposal"})
            continue
        built = _build_requirement(by_locus[locus], proposal, adapter)
        if "reason" in built:
            exclusions.append(built)
        else:
            requirements.append(built)
    for locus in merged:
        if locus not in known:
            exclusions.append({"locus": locus, "reason": "unknown locus"})
    return requirements, exclusions


def _provision_loci(provisions: list[dict]) -> list[str]:
    seen: set[str] = set()
    loci: list[str] = []
    for index, item in enumerate(provisions):
        if not isinstance(item, dict):
            raise ModelError("provisions", f"[{index}]", "an object")
        locus = item.get("locus")
        if not isinstance(locus, str) or not locus:
            raise ModelError("provisions", "locus", "a non-empty string")
        if locus in seen:
            raise ModelError("provisions", "locus", f"a unique locus, not a duplicate {locus}")
        if not isinstance(item.get("law_text"), str) or not item["law_text"]:
            raise ModelError("provisions", "law_text", "a non-empty string")
        seen.add(locus)
        loci.append(locus)
    return loci


def _reject_duplicate_kind(proposals: list[dict]) -> None:
    interpret: set[str] = set()
    hints: set[str] = set()
    for proposal in proposals:
        _reject_unexpected(proposal, _ALLOWED_FIELDS, "proposal")
        locus = _required_locus(proposal, "proposal")
        if _is_interpret(proposal):
            if locus in interpret:
                raise ModelError("interpret proposal", "locus", f"a unique locus, not a duplicate {locus}")
            interpret.add(locus)
        if _is_hints(proposal):
            if locus in hints:
                raise ModelError("hints proposal", "locus", f"a unique locus, not a duplicate {locus}")
            hints.add(locus)


def _is_interpret(proposal: dict) -> bool:
    extra = _INTERPRET_FIELDS.intersection(proposal) - {"locus"}
    return bool(extra) or "discovery_hints" not in proposal


def _is_hints(proposal: dict) -> bool:
    return "discovery_hints" in proposal


def _merge_proposals(proposals: list[dict]) -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for proposal in proposals:
        locus = proposal["locus"]
        current = merged.setdefault(locus, {})
        for key, value in proposal.items():
            if key == "locus":
                continue
            if key in current and current[key] != value:
                raise ModelError("proposal", key, f"one value for locus {locus}")
            current[key] = value
    return merged


def _build_requirement(provision: dict, proposal: dict, adapter: dict) -> dict:
    locus = provision["locus"]
    requirement_id = proposal.get("id")
    locator = proposal.get("locator")
    if not isinstance(requirement_id, str) or not requirement_id.strip():
        return {"locus": locus, "reason": "missing id"}
    if not isinstance(locator, str) or not locator.strip():
        return {"locus": locus, "reason": "missing locator"}
    source = adapter.get("source")
    pack_id = adapter.get("pack_id")
    if not isinstance(source, dict) or not isinstance(pack_id, str) or not pack_id:
        raise ModelError(str(adapter.get("id") or "adapter"), "pack_id", "pack_id and source")
    requirement = {
        "id": requirement_id,
        "pack_id": pack_id,
        "source": dict(source),
        "references": [
            {"nr": 1, "locator": locator, "law_text": provision["law_text"]},
        ],
    }
    for field in _COPY_FIELDS:
        if field in proposal:
            requirement[field] = proposal[field]
    try:
        return validate_requirement(requirement, published=False)
    except ModelError as exc:
        return {"locus": locus, "reason": str(exc)}


def _check_hints_shape(hints: object) -> None:
    probe = {
        "id": "probe",
        "pack_id": "probe",
        "source": {
            "framework": "EU",
            "instrument": "CRA",
            "identifier": "probe",
            "language": "en",
            "url": "https://example.test",
        },
        "references": [{"nr": 1, "locator": "X", "law_text": "text"}],
        "discovery_hints": hints,
    }
    validate_requirement(probe, published=False)


def _reject_unexpected(proposal: object, allowed: set[str], object_name: str) -> None:
    if not isinstance(proposal, dict):
        raise ModelError(object_name, "proposal", "an object")
    unknown = sorted(set(proposal) - allowed)
    if unknown:
        raise ModelError(object_name, unknown[0], "absent")


def _required_locus(proposal: dict, object_name: str) -> str:
    locus = proposal.get("locus")
    if not isinstance(locus, str) or not locus:
        raise ModelError(object_name, "locus", "a non-empty string")
    return locus
