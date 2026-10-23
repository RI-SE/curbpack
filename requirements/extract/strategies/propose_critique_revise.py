"""Propose, critique, and revise one provision at a time.

The stage still returns one validated proposal per input locus, in input
order. Critique text is sent with the source passage when asking for a
revision. A schema-valid revision is kept unless it drops a non-empty field
the critique did not name. Nothing in this module treats a model score, or
the phrase legally correct, as acceptance.

Stop reasons recorded in the trace: no_issues_reported, no_actionable_change,
invalid_response, aborted, max_rounds.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Callable

from common.errors import ModelError
from common.paths import install_root
from requirements.extract.call import _llm_note, _parse_and_validate, _parse_json_object
from requirements.extract.trace import Trace, now_utc, sha256_text

_GUIDANCE = install_root() / "requirements" / "extract" / "guidance"
_CRITIQUE_PATH = _GUIDANCE / "critique.txt"
_REVISE_PATH = _GUIDANCE / "revise.txt"
_MAX_ATTEMPTS = 3
TIMEOUT_SECONDS = 600
_SCALAR_FIELDS = ("note", "strength", "responsible", "applicability", "exceptions", "scope")
_HINT_FIELDS = ("concepts", "path_hints", "sources", "expected_evidence")
_PROPOSE_SUFFIX = (
    '\nReturn one JSON object and no other text: {"provisions":[ one object for this provision ]}.\n'
)
_SECRET = re.compile(r"(?i)(authorization:\s*)\S+|(bearer\s+)\S+")


class _Abort(Exception):
    """The caller asked to stop before another model call."""


class _Call:
    def __init__(self, parsed, note: dict, raw: str, error: ModelError | None):
        self.parsed = parsed
        self.note = note
        self.raw = raw
        self.error = error


def run_propose_critique_revise(
    provisions: list[dict],
    *,
    stage: str,
    validate_one,
    strategy: str,
    model: str,
    temperature: float,
    endpoint: str,
    guidance: Path,
    max_rounds: int,
    complete_fn,
    trace: Trace,
    should_abort: Callable[[], bool] | None,
) -> tuple[list[dict], list[dict]]:
    propose_template = _load_template(guidance, ("provisions",))
    critique_template = _load_template(_CRITIQUE_PATH, ("provisions", "candidate"))
    revise_template = _load_template(_REVISE_PATH, ("provisions", "candidate", "critique"))
    trace.start(
        {
            "endpoint": endpoint,
            "max_rounds": max_rounds,
            "model": model,
            "strategy": strategy,
            "temperature": temperature,
            "timeout_seconds": TIMEOUT_SECONDS,
        }
    )
    trace.event(
        {
            "event": "stage_start",
            "guidance": str(guidance),
            "guidance_sha256": sha256_text(guidance.read_text(encoding="utf-8")),
            "stage": stage,
        }
    )
    proposals: list[dict] = []
    notes: list[dict] = []
    try:
        for provision in provisions:
            proposal, provision_notes = _one_provision(
                provision,
                stage=stage,
                validate_one=validate_one,
                strategy=strategy,
                model=model,
                temperature=temperature,
                endpoint=endpoint,
                guidance=guidance,
                max_rounds=max_rounds,
                complete_fn=complete_fn,
                trace=trace,
                should_abort=should_abort,
                propose_template=propose_template,
                critique_template=critique_template,
                revise_template=revise_template,
            )
            proposals.append(proposal)
            notes.extend(provision_notes)
    except _Abort:
        raise ModelError("produce", "aborted", "stop requested before the next model call") from None
    return proposals, notes


def _one_provision(
    provision: dict,
    *,
    stage: str,
    validate_one,
    strategy: str,
    model: str,
    temperature: float,
    endpoint: str,
    guidance: Path,
    max_rounds: int,
    complete_fn,
    trace: Trace,
    should_abort,
    propose_template: str,
    critique_template: str,
    revise_template: str,
) -> tuple[dict, list[dict]]:
    locus = provision["locus"]
    passage = _dump([provision])
    cap = _MAX_ATTEMPTS * (1 + 2 * max_rounds)
    made = 0
    trace.event({"event": "provision", "locus": locus, "provision": provision, "stage": stage})

    def budget() -> None:
        nonlocal made
        if made >= cap:
            raise ModelError("produce", "calls", f"at most {cap} model calls for locus {locus}")
        made += 1

    shared = dict(
        stage=stage,
        strategy=strategy,
        model=model,
        temperature=temperature,
        endpoint=endpoint,
        max_rounds=max_rounds,
        complete_fn=complete_fn,
        trace=trace,
        should_abort=should_abort,
        locus=locus,
        budget=budget,
    )
    proposed, _propose_raw, propose_notes = _until_valid(
        **shared,
        role="propose",
        round_number=0,
        guidance_path=guidance,
        prompt=_fill(propose_template, {"provisions": passage}) + _PROPOSE_SUFFIX,
        parser=lambda raw: _one_row(raw, locus, validate_one),
    )
    if proposed is None:
        raise ModelError("produce", "response", f"a schema-valid proposal for {locus}")
    notes = list(propose_notes)
    candidate = proposed
    candidate_file = _store_candidate(trace, stage, locus, 0, candidate)
    stop_reason = "max_rounds"
    remaining: list[str] = []

    for round_number in range(1, max_rounds + 1):
        findings, critique_raw, critique_notes = _until_valid(
            **shared,
            role="critique",
            round_number=round_number,
            guidance_path=_CRITIQUE_PATH,
            prompt=_fill(critique_template, {"provisions": passage, "candidate": _dump(candidate)}),
            parser=_findings,
        )
        notes.extend(critique_notes)
        if findings is None:
            stop_reason = "invalid_response"
            remaining.append("critique was not usable")
            break
        actionable = bool(findings)
        trace.event(
            {
                "actionable": actionable,
                "event": "critique",
                "findings": findings,
                "locus": locus,
                "round": round_number,
            }
        )
        if not actionable:
            stop_reason = "no_issues_reported"
            break
        revised, _raw, revise_notes = _until_valid(
            **shared,
            role="revise",
            round_number=round_number,
            guidance_path=_REVISE_PATH,
            prompt=_fill(
                revise_template,
                {"provisions": passage, "candidate": _dump(candidate), "critique": critique_raw},
            ),
            parser=lambda raw: _one_row(raw, locus, validate_one),
        )
        notes.extend(revise_notes)
        if revised is None:
            stop_reason = "invalid_response"
            remaining.append("revision was not schema-valid")
            break
        if revised == candidate:
            stop_reason = "no_actionable_change"
            trace.event(
                {
                    "decision": "reject",
                    "event": "revision",
                    "locus": locus,
                    "reason": "no_actionable_change",
                    "round": round_number,
                }
            )
            break
        reason = regression_reason(candidate, revised, findings)
        if reason is not None:
            remaining.append(reason)
            trace.event(
                {
                    "decision": "reject",
                    "event": "revision",
                    "locus": locus,
                    "reason": reason,
                    "round": round_number,
                }
            )
            continue
        candidate = revised
        candidate_file = _store_candidate(trace, stage, locus, round_number, candidate)
        trace.event(
            {
                "decision": "accept",
                "event": "revision",
                "locus": locus,
                "reason": "schema_valid",
                "round": round_number,
            }
        )

    digest = sha256_text(_dump(candidate))
    trace.add_output(
        {
            "candidate": candidate_file,
            "candidate_sha256": digest,
            "locus": locus,
            "remaining": list(remaining),
            "stage": stage,
            "stop": stop_reason,
        }
    )
    trace.event(
        {
            "candidate": candidate_file,
            "candidate_sha256": digest,
            "event": "stop",
            "locus": locus,
            "reason": stop_reason,
            "remaining": remaining,
            "stage": stage,
        }
    )
    return candidate, notes


def regression_reason(previous: dict, revised: dict, findings: list[dict]) -> str | None:
    """A schema-valid revision regresses when it clears a field nobody challenged."""
    named = {finding.get("field") for finding in findings if isinstance(finding.get("field"), str)}
    named = {field for field in named if field}
    for key in _SCALAR_FIELDS:
        if _present(previous.get(key)) and not _present(revised.get(key)) and key not in named:
            return f"dropped {key} without a finding"
    previous_hints = previous.get("discovery_hints")
    revised_hints = revised.get("discovery_hints")
    hint_named = "discovery_hints" in named or bool(named.intersection(_HINT_FIELDS))
    if _present(previous_hints) and not _present(revised_hints) and not hint_named:
        return "dropped discovery_hints without a finding"
    if isinstance(previous_hints, dict) and isinstance(revised_hints, dict):
        for key, value in previous_hints.items():
            challenged = key in named or "discovery_hints" in named
            if _present(value) and not _present(revised_hints.get(key)) and not challenged:
                return f"dropped discovery_hints.{key} without a finding"
    return None


def _until_valid(*, parser, **kwargs):
    notes: list[dict] = []
    last_raw = ""
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        result = _attempt(attempt=attempt, parser=parser, **kwargs)
        notes.append(result.note)
        if result.error is None:
            return result.parsed, result.raw, notes
        last_raw = result.raw
    return None, last_raw, notes


def _attempt(
    *,
    attempt: int,
    parser,
    role: str,
    round_number: int,
    guidance_path: Path,
    prompt: str,
    stage: str,
    strategy: str,
    model: str,
    temperature: float,
    endpoint: str,
    max_rounds: int,
    complete_fn,
    trace: Trace,
    should_abort,
    locus: str,
    budget,
) -> _Call:
    _abort_if_requested(should_abort, trace)
    budget()
    number = trace.next_call()
    started = time.perf_counter()
    started_at = now_utc()
    settings = {
        "attempt": attempt,
        "endpoint": endpoint,
        "max_rounds": max_rounds,
        "model": model,
        "role": role,
        "round": round_number,
        "stage": stage,
        "strategy": strategy,
        "temperature": temperature,
        "timeout": TIMEOUT_SECONDS,
    }
    safe_prompt = _sanitize(prompt)
    error: ModelError | None = None
    raw = ""
    try:
        raw = complete_fn(safe_prompt, settings)
        if not isinstance(raw, str):
            raise ModelError("produce", "response", "text")
    except ModelError as exc:
        error = exc
    except Exception as exc:
        error = ModelError("produce", "endpoint", f"a completed model call ({exc})")
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    parsed = None
    validation = None if error is None else str(error)
    parse = "error" if error is not None else "ok"
    if error is None:
        try:
            parsed = parser(raw)
        except ModelError as exc:
            error = exc
            parse = "invalid"
            validation = str(exc)
    prompt_file = trace.artifact(f"calls/{number:04d}.prompt.txt", safe_prompt)
    response_file = trace.artifact(f"calls/{number:04d}.response.txt", raw)
    record = {
        "attempt": attempt,
        "completion_tokens": settings.get("completion_tokens"),
        "duration_ms": duration_ms,
        "ended_at": now_utc(),
        "endpoint": endpoint,
        "event": "model_call",
        "locus": locus,
        "model": model,
        "model_digest": settings.get("model_digest"),
        "n": number,
        "parse": parse,
        "prompt_file": prompt_file,
        "prompt_sha256": sha256_text(safe_prompt),
        "prompt_tokens": settings.get("prompt_tokens"),
        "response_file": response_file,
        "response_sha256": sha256_text(raw),
        "role": role,
        "round": round_number,
        "stage": stage,
        "started_at": started_at,
        "timeout_seconds": TIMEOUT_SECONDS,
        "validation": validation,
    }
    trace.add_call({key: value for key, value in record.items() if key != "event"})
    trace.event(record)
    note = _llm_note(
        stage=stage,
        strategy=strategy,
        model=model,
        temperature=temperature,
        endpoint=endpoint,
        guidance_path=guidance_path,
        max_rounds=max_rounds,
    )
    _abort_if_requested(should_abort, trace)
    return _Call(parsed, note, raw, error)


def _abort_if_requested(should_abort, trace: Trace) -> None:
    if should_abort is not None and should_abort():
        trace.status = "aborted"
        trace.event(
            {
                "event": "abort",
                "reason": "stop requested; a model call already in flight is not cancelled",
            }
        )
        raise _Abort()


def _one_row(raw: str, locus: str, validate_one) -> dict:
    rows = _parse_and_validate(raw, loci={locus}, validate_one=validate_one)
    return rows[0]


def _findings(raw: str) -> list[dict]:
    data = _parse_json_object(raw)
    found = data.get("findings")
    if not isinstance(found, list):
        raise ModelError("produce", "findings", "a list")
    cleaned: list[dict] = []
    for index, item in enumerate(found):
        if not isinstance(item, dict):
            raise ModelError("produce", f"findings[{index}]", "an object")
        field = item.get("field", "")
        aspect = item.get("aspect", "")
        quote = item.get("quote", "")
        locator = item.get("locator", "")
        if not all(isinstance(part, str) for part in (field, aspect, quote, locator)):
            raise ModelError("produce", f"findings[{index}]", "string field, aspect, quote, and locator")
        if not field.strip() and not aspect.strip():
            continue
        cleaned.append({"aspect": aspect, "field": field, "locator": locator, "quote": quote})
    return cleaned


def _load_template(path: Path, required: tuple[str, ...]) -> str:
    if not path.is_file():
        raise ModelError("produce", "guidance", f"a guidance file at {path}")
    text = path.read_text(encoding="utf-8")
    missing = [name for name in required if "{" + name + "}" not in text]
    if missing:
        raise ModelError("produce", "guidance", f"{path.name} to contain {missing}")
    return text


def _fill(template: str, parts: dict[str, str]) -> str:
    text = template
    for key, value in parts.items():
        text = text.replace("{" + key + "}", value)
    return text


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _present(value) -> bool:
    return value not in (None, "", [], {})


def _store_candidate(trace: Trace, stage: str, locus: str, index: int, candidate: dict) -> str:
    safe = locus.replace("/", "_").replace("\\", "_")
    return trace.artifact(f"candidates/{stage}/{safe}/{index:03d}.json", _dump(candidate) + "\n")


def _sanitize(text: str) -> str:
    return _SECRET.sub(lambda match: f"{match.group(1) or match.group(2)}[redacted]", text)
