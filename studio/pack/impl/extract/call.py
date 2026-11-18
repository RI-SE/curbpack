"""One model call, JSON parse, and the diagnostic note shared by proposal strategies."""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from common.errors import ModelError

CompleteFn = Callable[[str, dict], str]


def _one_call(
    guidance_path: Path,
    provisions_text: str,
    *,
    stage: str,
    strategy: str,
    model: str,
    temperature: float,
    endpoint: str,
    max_rounds: int | None,
    complete_fn: CompleteFn,
    validate_one,
    loci: set[str],
    role: str,
    prior: str | None,
) -> tuple[list[dict] | str, dict]:
    template = guidance_path.read_text(encoding="utf-8")
    prompt = template.replace("{provisions}", provisions_text)
    if role == "critique" and prior is not None:
        prompt = f"{prompt}\n\nCritique this proposal JSON:\n{prior}\n"
    elif role == "revise" and prior is not None:
        prompt = f"{prompt}\n\nRevise this proposal JSON:\n{prior}\n"
    settings = {
        "stage": stage,
        "strategy": strategy,
        "model": model,
        "temperature": temperature,
        "endpoint": endpoint,
        "role": role,
    }
    if max_rounds is not None:
        settings["max_rounds"] = max_rounds
    raw = complete_fn(prompt, settings)
    note = _llm_note(
        stage=stage,
        strategy=strategy,
        model=model,
        temperature=temperature,
        endpoint=endpoint,
        guidance_path=guidance_path,
        max_rounds=max_rounds,
    )
    if role == "critique":
        return raw, note
    proposals = _parse_and_validate(raw, loci=loci, validate_one=validate_one)
    return proposals, note


def _parse_and_validate(raw: str, *, loci: set[str], validate_one) -> list[dict]:
    data = _parse_json_object(raw)
    rows = data.get("provisions")
    if not isinstance(rows, list):
        raise ModelError("produce", "provisions", "a list")
    if len(rows) != len(loci):
        raise ModelError("produce", "provisions", f"{len(loci)} results, not {len(rows)}")
    seen: set[str] = set()
    out: list[dict] = []
    for row in rows:
        validated = validate_one(row, loci)
        locus = validated["locus"]
        if locus in seen:
            raise ModelError("produce", "locus", f"a unique locus, not a duplicate {locus}")
        seen.add(locus)
        out.append(validated)
    missing = loci - seen
    if missing:
        raise ModelError("produce", "locus", f"results for {sorted(missing)}")
    return out


def _llm_note(
    *,
    stage: str,
    strategy: str,
    model: str,
    temperature: float,
    endpoint: str,
    guidance_path: Path,
    max_rounds: int | None,
) -> dict:
    body = guidance_path.read_bytes()
    note = {
        "stage": stage,
        "strategy": strategy,
        "model": model,
        "temperature": temperature,
        "endpoint": endpoint,
        "prompt": str(guidance_path),
        "prompt_sha256": hashlib.sha256(body).hexdigest(),
    }
    if strategy == "propose_critique_revise":
        note["max_rounds"] = max_rounds
    return note


def _default_complete(prompt_text: str, settings: dict) -> str:
    payload = {
        "model": settings["model"],
        "stream": False,
        "options": {"temperature": settings["temperature"]},
        "messages": [{"role": "user", "content": prompt_text}],
    }
    request = urllib.request.Request(
        f'{str(settings["endpoint"]).rstrip("/")}/api/chat',
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.get("timeout", 600)) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise ModelError("produce", "endpoint", f"a reachable model server ({exc})") from exc
    if isinstance(data.get("prompt_eval_count"), int):
        settings["prompt_tokens"] = data["prompt_eval_count"]
    if isinstance(data.get("eval_count"), int):
        settings["completion_tokens"] = data["eval_count"]
    content = ((data.get("message") or {}).get("content") or "").strip()
    if not content:
        raise ModelError("produce", "response", "non-empty model content")
    return content


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ModelError("produce", "response", "a JSON object") from None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ModelError("produce", "response", "a JSON object") from exc
    if not isinstance(data, dict):
        raise ModelError("produce", "response", "a JSON object")
    return data
