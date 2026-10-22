"""Score retrieved candidates. Model output is not evidence and not a Claim field."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

from common.errors import ModelError
from discovery.search import read_source_text, verify_excerpt
from requirements.extract.call import _default_complete, _parse_json_object

MAX_CHARS = 12000
DEFAULT_MODEL = "qwen3-coder:30b"
DEFAULT_ENDPOINT = "http://127.0.0.1:11434"
DEFAULT_ASSESS_LIMIT = 5
RANKS = {"High", "Medium", "Low", "None"}

SCORE_PROMPT = """You score whether a repository file is evidence for a regulatory documentation requirement.

Requirement (verbatim):
---
{law_text}
---

Requirement id: {requirement_id}
File path: {path}

File content:
---
{body}
---

Rules:
- Score current product evidence higher than FUTURE_/planned/roadmap material.
- Prefer files that assess risks (tables, STRIDE, residual risk), not files that only mention "security".
- Pick a short excerpt (1-6 lines) from the file that best supports the score; empty if none.
- Reply with ONLY one JSON object, no markdown:
  {{"score": <float 0.0-1.0>, "rank": "<High|Medium|Low|None>", "why": "<one short sentence>", "excerpt": "<verbatim quote or empty>"}}
"""

CompleteFn = Callable[[str, dict], str]


def assess_candidates(
    repo: Path,
    requirement: dict,
    candidates: list[dict],
    *,
    complete: CompleteFn | None = None,
    assess_limit: int = DEFAULT_ASSESS_LIMIT,
    prior: list[dict] | None = None,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
) -> list[dict]:
    """Assess up to assess_limit candidates. Retrieval rows are never dropped."""
    if not isinstance(assess_limit, int) or isinstance(assess_limit, bool) or not 0 <= assess_limit <= 20:
        raise ModelError("discover", "assess_limit", "an integer from 0 to 20")
    law = _law_text(requirement)
    law_sha = _sha(law)
    previous = {
        str(row.get("path") or ""): row
        for row in (prior or [])
        if isinstance(row, dict) and row.get("assessment_state") in {"assessed", "reused"}
    }
    caller = complete or _default_complete
    out: list[dict] = []
    calls = 0
    endpoint_error = ""
    for item in candidates:
        if not isinstance(item, dict) or not item.get("path"):
            continue
        row = {
            "path": str(item["path"]),
            "matched_by": str(item.get("matched_by") or ""),
            "matched_hints": [
                str(hint)
                for hint in (item.get("matched_hints") or [])
                if isinstance(hint, str) and hint.strip()
            ],
            "excerpt": str(item.get("excerpt") or ""),
        }
        try:
            body = read_source_text(repo, row["path"])
        except ModelError as exc:
            row["assessment_state"] = "failed"
            row["assessment_error"] = str(exc)
            out.append(row)
            continue
        truncated = _truncate(body)
        prompt = SCORE_PROMPT.format(
            law_text=law.strip(),
            requirement_id=str(requirement.get("id") or ""),
            path=row["path"],
            body=truncated,
        )
        prompt_sha = _sha(prompt)
        body_sha = _sha(truncated)
        reusable = previous.get(row["path"])
        if (
            reusable
            and reusable.get("law_sha256") == law_sha
            and reusable.get("body_sha256") == body_sha
            and reusable.get("model") == model
            and reusable.get("prompt_sha256") == prompt_sha
        ):
            _copy_assessment(row, reusable)
            row["assessment_state"] = "reused"
            out.append(row)
            continue
        if endpoint_error:
            row["assessment_state"] = "failed"
            row["assessment_error"] = endpoint_error
            out.append(row)
            continue
        if calls >= assess_limit:
            row["assessment_state"] = "not_assessed"
            row["assessment_skip"] = "cap"
            out.append(row)
            continue
        settings = {
            "model": model,
            "temperature": 0,
            "endpoint": endpoint,
            "timeout": 600,
        }
        try:
            raw = caller(prompt, settings)
        except Exception as exc:
            endpoint_error = str(exc)
            row["assessment_state"] = "failed"
            row["assessment_error"] = endpoint_error
            out.append(row)
            continue
        calls += 1
        judged = _judgment(raw, body)
        row.update(judged)
        if row["assessment_state"] == "assessed":
            row["law_sha256"] = law_sha
            row["body_sha256"] = body_sha
            row["model"] = model
            row["prompt_sha256"] = prompt_sha
        out.append(row)
    return out


def _law_text(requirement: dict) -> str:
    parts = []
    for ref in requirement.get("references") or []:
        if isinstance(ref, dict) and isinstance(ref.get("law_text"), str) and ref["law_text"].strip():
            parts.append(ref["law_text"].strip())
    return "\n\n".join(parts)


def _truncate(body: str) -> str:
    if len(body) > MAX_CHARS:
        return body[:MAX_CHARS] + "\n…[truncated]…"
    return body


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _copy_assessment(row: dict, prior: dict) -> None:
    for key in (
        "score",
        "rank",
        "why",
        "model_excerpt",
        "model_excerpt_verified",
        "law_sha256",
        "body_sha256",
        "model",
        "prompt_sha256",
    ):
        if key in prior:
            row[key] = prior[key]


def shows_support(row: dict) -> bool:
    """False when a finished assessment found no support.

    Score 0 and rank None are omitted from the list a person reads. A row that
    was not assessed, or whose call failed, stays.
    """
    if row.get("assessment_state") not in {"assessed", "reused"}:
        return True
    try:
        score = float(row.get("score"))
    except (TypeError, ValueError):
        return True
    rank = str(row.get("rank") or "").lower()
    return score > 0 and rank != "none"


def _judgment(raw: str, body: str) -> dict:
    try:
        data = _parse_json_object(raw)
    except (ModelError, json.JSONDecodeError, ValueError) as exc:
        return {"assessment_state": "failed", "assessment_error": f"unparseable: {exc}"}
    score = data.get("score")
    rank = data.get("rank")
    why = data.get("why")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
        return {"assessment_state": "failed", "assessment_error": "score outside 0-1"}
    if rank not in RANKS:
        return {"assessment_state": "failed", "assessment_error": "rank not High, Medium, Low, or None"}
    if not isinstance(why, str) or not why.strip():
        return {"assessment_state": "failed", "assessment_error": "missing rationale"}
    excerpt = data.get("excerpt") if isinstance(data.get("excerpt"), str) else ""
    return {
        "assessment_state": "assessed",
        "score": float(score),
        "rank": rank,
        "why": why.strip(),
        "model_excerpt": excerpt,
        "model_excerpt_verified": verify_excerpt(body, excerpt) is not None,
    }
