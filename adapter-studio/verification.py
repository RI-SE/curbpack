"""Verification suggestions for adapter-studio.

The local model is called the same way as discovery hints. The result stays
in the studio run. It is not written into a Curbpack requirement.
"""

from __future__ import annotations

import threading
from pathlib import Path

from common.errors import ModelError
from requirements.extract.call import CompleteFn, _default_complete, _parse_json_object
from requirements.extract.produce import _DEFAULT_ENDPOINT, _DEFAULT_MODEL, _DEFAULT_TEMPERATURE

_PROMPT = Path(__file__).resolve().parent / "prompts" / "verification_hints.txt"
_TOP_FIELDS = (
    "verification_objective",
    "verification_methods",
    "evidence_hints",
    "verification_assumptions",
)
_METHOD_FIELDS = ("method", "verifies", "additional_assumption")
_MODEL_CALL = threading.Lock()


def verification_inputs(provisions: list[dict], interpret_rows: list[dict]) -> list[dict]:
    """Rows that already have an atomic requirement id and locator."""
    by_locus = {}
    for item in provisions:
        if isinstance(item, dict) and isinstance(item.get("locus"), str):
            by_locus[item["locus"]] = item
    inputs = []
    for row in interpret_rows:
        if not isinstance(row, dict):
            continue
        locus = row.get("locus")
        provision = by_locus.get(locus) if isinstance(locus, str) else None
        if not isinstance(provision, dict):
            continue
        requirement_id = row.get("id")
        locator = row.get("locator")
        law_text = provision.get("law_text")
        if not isinstance(requirement_id, str) or not requirement_id.strip():
            continue
        if not isinstance(locator, str) or not locator.strip():
            continue
        if not isinstance(law_text, str) or not law_text.strip():
            continue
        inputs.append(
            {
                "locus": locus,
                "source_text": law_text,
                "atom": law_text,
                "locator": locator,
            }
        )
    return inputs


def render_prompt(source_text: str, atom: str, locator: str) -> str:
    template = _PROMPT.read_text(encoding="utf-8")
    return (
        template.replace("{source_text}", source_text)
        .replace("{atom}", atom)
        .replace("{locator}", locator)
    )


def validate_suggestion(data: dict) -> dict:
    """Reject a reply that is not the prompt's object."""
    if not isinstance(data, dict):
        raise ModelError("verification hints", "response", "a JSON object")
    unknown = sorted(set(data) - set(_TOP_FIELDS))
    if unknown:
        raise ModelError("verification hints", unknown[0], "absent")
    missing = [key for key in _TOP_FIELDS if key not in data]
    if missing:
        raise ModelError("verification hints", missing[0], "present")
    objective = data["verification_objective"]
    if not isinstance(objective, str):
        raise ModelError("verification hints", "verification_objective", "a string")
    methods = data["verification_methods"]
    if not isinstance(methods, list):
        raise ModelError("verification hints", "verification_methods", "an array")
    checked_methods = []
    for index, method in enumerate(methods):
        if not isinstance(method, dict):
            raise ModelError("verification hints", f"verification_methods[{index}]", "an object")
        extra = sorted(set(method) - set(_METHOD_FIELDS))
        if extra:
            raise ModelError("verification hints", extra[0], "absent")
        for key in ("method", "verifies"):
            if not isinstance(method.get(key), str):
                raise ModelError("verification hints", key, "a string")
        assumption = method.get("additional_assumption")
        if assumption is not None and not isinstance(assumption, str):
            raise ModelError("verification hints", "additional_assumption", "a string or null")
        checked_methods.append(
            {
                "method": method["method"],
                "verifies": method["verifies"],
                "additional_assumption": assumption,
            }
        )
    evidence = _string_list(data["evidence_hints"], "evidence_hints")
    assumptions = _string_list(data["verification_assumptions"], "verification_assumptions")
    return {
        "verification_objective": objective,
        "verification_methods": checked_methods,
        "evidence_hints": evidence,
        "verification_assumptions": assumptions,
    }


def propose_verification(
    items: list[dict],
    *,
    complete: CompleteFn | None = None,
    model: str = _DEFAULT_MODEL,
    temperature: float = _DEFAULT_TEMPERATURE,
    endpoint: str = _DEFAULT_ENDPOINT,
    on_row=None,
) -> list[dict]:
    """One model call per requirement. Each accepted reply is reported before the next call."""
    complete_fn = complete or _default_complete
    suggestions = []
    for item in items:
        with _MODEL_CALL:
            raw = complete_fn(
                render_prompt(item["source_text"], item["atom"], item["locator"]),
                {
                    "model": model,
                    "temperature": temperature,
                    "endpoint": endpoint,
                    "stage": "verification_hints",
                },
            )
        suggestion = {"locus": item["locus"], **validate_suggestion(_parse_json_object(raw))}
        suggestions.append(suggestion)
        if on_row is not None:
            on_row(suggestion)
    return suggestions


def suggestion_text(suggestion: dict) -> str:
    """One readable cell. Empty when this row was not sent."""
    if not suggestion:
        return ""
    lines = [str(suggestion.get("verification_objective") or "")]
    for method in suggestion.get("verification_methods") or []:
        if not isinstance(method, dict):
            continue
        line = f"{method.get('method') or ''} — {method.get('verifies') or ''}"
        assumption = method.get("additional_assumption")
        if isinstance(assumption, str) and assumption.strip():
            line += f" ({assumption})"
        lines.append(line)
    evidence = [item for item in suggestion.get("evidence_hints") or [] if isinstance(item, str)]
    if evidence:
        lines.append("Evidence: " + "; ".join(evidence))
    assumptions = [
        item for item in suggestion.get("verification_assumptions") or [] if isinstance(item, str)
    ]
    if assumptions:
        lines.append("Assumptions: " + "; ".join(assumptions))
    return "\n".join(line for line in lines if line).strip()


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ModelError("verification hints", field, "an array of strings")
    return list(value)
