"""View models for the researcher overview and a Requirement's findings."""

from __future__ import annotations

from pathlib import Path

from claims.bind import read_claim_seal, suggest_claim_id
from discovery.assess import shows_support


def overview_rows(
    requirements: list[dict],
    job: dict | None,
    feedback: dict,
    claims: list[dict],
    *,
    repo: Path | None,
    trust: dict[str, bytes],
) -> list[dict]:
    by_requirement = {}
    if isinstance(job, dict):
        for row in job.get("results") or []:
            if isinstance(row, dict) and isinstance(row.get("requirement_id"), str):
                by_requirement[row["requirement_id"]] = row
    marks = feedback.get("requirements") if isinstance(feedback, dict) else {}
    if not isinstance(marks, dict):
        marks = {}
    rows = []
    for requirement in requirements:
        if not isinstance(requirement, dict) or not isinstance(requirement.get("id"), str):
            continue
        requirement_id = requirement["id"]
        block = by_requirement.get(requirement_id)
        paths = marks.get(requirement_id) if isinstance(marks.get(requirement_id), dict) else {}
        findings = merge_findings((block or {}).get("candidates") or [] if block else [], paths)
        ran = block is not None
        assessed = any(item.get("assessment_state") in {"assessed", "reused", "failed"} for item in findings)
        high = sum(1 for item in findings if item.get("rank") == "High")
        owned = [
            claim
            for claim in claims
            if isinstance(claim, dict) and claim.get("requirement_id") == requirement_id
        ]
        rows.append(
            {
                "id": requirement_id,
                "locator": _locator(requirement),
                "findings": len(findings) if ran or findings else None,
                "high": high if assessed else None,
                "useful": sum(1 for item in findings if item.get("vote") == "useful"),
                "poor": sum(1 for item in findings if item.get("vote") == "poor"),
                "claims": len(owned),
                "signing": _signing(owned, repo, trust),
            }
        )
    return rows


def merge_findings(candidates: list, marks: dict) -> list[dict]:
    rows = []
    seen = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or not candidate.get("path"):
            continue
        if not shows_support(candidate):
            continue
        path = str(candidate["path"])
        extra = marks.get(path) if isinstance(marks.get(path), dict) else {}
        row = dict(candidate)
        row["vote"] = extra.get("vote") or ""
        row["checks"] = [item for item in extra.get("checks") or [] if isinstance(item, dict)]
        row["human_why"] = extra.get("human_why") or ""
        row["dismissed_why"] = extra.get("dismissed_why") or ""
        row["added"] = bool(extra.get("added"))
        rows.append(row)
        seen.add(path)
    for path, extra in marks.items():
        if path in seen or not isinstance(extra, dict) or not extra.get("added"):
            continue
        rows.append(
            {
                "path": path,
                "matched_by": "added",
                "excerpt": "",
                "assessment_state": "not_assessed",
                "vote": extra.get("vote") or "",
                "checks": [item for item in extra.get("checks") or [] if isinstance(item, dict)],
                "human_why": extra.get("human_why") or "",
                "dismissed_why": extra.get("dismissed_why") or "",
                "added": True,
            }
        )
    return rows


def claim_links(requirement_id: str, finding: dict, claims: list[dict]) -> list[dict]:
    """One link when this finding's evidence locator already has a Claim."""
    known = {claim.get("id"): claim for claim in claims if isinstance(claim, dict)}
    path = str(finding.get("path") or "")
    if not path:
        return []
    claim_id = suggest_claim_id(requirement_id, path)
    if claim_id in known:
        return [{"id": claim_id}]
    return []


def _locator(requirement: dict) -> str:
    references = requirement.get("references") or []
    if references and isinstance(references[0], dict):
        return str(references[0].get("locator") or "")
    return ""


def signing_label(
    claims: list[dict],
    requirement_id: str,
    repo: Path | None,
    trust: dict[str, bytes],
) -> str:
    """Seal reading for the Claims of one Requirement. Empty when there are none."""
    owned = [claim for claim in claims if isinstance(claim, dict) and claim.get("requirement_id") == requirement_id]
    return _signing(owned, repo, trust)


def _signing(claims: list[dict], repo: Path | None, trust: dict[str, bytes]) -> str:
    if not claims:
        return ""
    labels = []
    for claim in claims:
        relative = f"claims/{claim.get('id')}.json"
        reading = read_claim_seal(claim, trust, repo=repo, relative=relative)
        if reading.get("verifiable"):
            labels.append("verifiable")
        elif isinstance(claim.get("signed"), dict):
            labels.append("signed, not verifiable")
        else:
            labels.append("unsigned draft")
    if any(label == "signed, not verifiable" for label in labels):
        return "signed, not verifiable"
    if any(label == "unsigned draft" for label in labels):
        return "unsigned draft"
    return "verifiable"
