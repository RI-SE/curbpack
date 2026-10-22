"""Revise-loop extract of CRA Annex VII loci 2(b), 5, and 8.

Writes a new dated working copy and a trace directory. Does not overwrite an
existing copy, a published Pack, or the frozen reference. The comparison in
outcome.json is mechanical. It is not a legal verdict.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POC2 = ROOT / "poc2"
sys.path.insert(0, str(POC2))

from common.jsonio import write_json  # noqa: E402
from common.store import save_requirement  # noqa: E402
from requirements.extract.adapter import ADAPTERS, load_adapter, section_provisions  # noqa: E402
from requirements.extract.assemble import assemble_requirements  # noqa: E402
from requirements.extract.produce import proposals_from_producers  # noqa: E402
from requirements.workspace import create_extraction_copy, work_directory  # noqa: E402

WORKSPACE = POC2 / "data" / "workspace"
REFERENCE = POC2 / "data" / "reference" / "poc1-annex-vii-unsigned"
LOCI = ("2(b)", "5", "8")
REFERENCE_FILES = {"2(b)": "POC1-REF-VII-2B.json", "5": "POC1-REF-VII-5.json", "8": "POC1-REF-VII-8.json"}
MODEL = "qwen3-coder:30b"
MODEL_DIGEST = "06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca"
ENDPOINT = "http://127.0.0.1:11434"


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    trace_dir = WORKSPACE / "traces" / stamp
    adapter_dir = ADAPTERS / "cra-xml"
    adapter = load_adapter(adapter_dir / "adapter.json")
    extracted = section_provisions(adapter_dir, adapter, "VII")
    provisions = [
        {"locus": item["locus"], "law_text": item["law_text"]}
        for item in extracted["provisions"]
        if item["locus"] in LOCI
    ]
    if [item["locus"] for item in provisions] != list(LOCI):
        raise SystemExit(f"expected loci {list(LOCI)}, got {[item['locus'] for item in provisions]}")
    reference_before = _hashes(REFERENCE)
    started = time.perf_counter()
    outcome: dict = {
        "started_at": stamp,
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "strategy": "propose_critique_revise",
        "max_rounds": 10,
        "temperature": 0.2,
        "endpoint": ENDPOINT,
        "loci": list(LOCI),
        "trace_dir": str(trace_dir),
        "legal_verdict": "not claimed",
    }
    try:
        proposals, notes = proposals_from_producers(
            provisions,
            adapter_dir=adapter_dir,
            strategy="propose_critique_revise",
            max_rounds=10,
            model=MODEL,
            temperature=0.2,
            endpoint=ENDPOINT,
            trace_dir=trace_dir,
        )
        requirements, exclusions = assemble_requirements(provisions, proposals, adapter=adapter)
        if exclusions:
            raise RuntimeError(f"subset assembly exclusions: {exclusions}")
        pack = {
            "id": adapter["pack_id"],
            "name": "cra-xml revise loop VII.2(b) VII.5 VII.8",
            "version": "0.1.0",
        }
        copy = create_extraction_copy(WORKSPACE, pack["id"], pack)
        for requirement in requirements:
            save_requirement(copy, requirement, published=False)
        work = work_directory(copy)
        work.mkdir(parents=True, exist_ok=False)
        write_json(work / "llm.json", {"llm": notes})
        write_json(
            work / "subset.json",
            {
                "loci": list(LOCI),
                "trace_dir": str(trace_dir),
                "note": "Three-locus revise-loop experiment. Not a full Annex VII extract.",
            },
        )
        outcome["status"] = "written"
        outcome["copy"] = str(copy)
        outcome["requirement_count"] = len(requirements)
        outcome["comparison"] = _comparison(provisions, requirements)
        outcome["trace"] = _trace_summary(trace_dir)
    except Exception as exc:
        outcome["status"] = "failed"
        outcome["error"] = str(exc)
        if trace_dir.exists():
            (trace_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
            outcome["trace"] = _trace_summary(trace_dir)
    outcome["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    outcome["reference_unchanged"] = _hashes(REFERENCE) == reference_before
    if trace_dir.exists():
        (trace_dir / "outcome.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))
    if outcome["status"] != "written" or not outcome["reference_unchanged"]:
        raise SystemExit(1)


def _comparison(provisions: list[dict], requirements: list[dict]) -> list[dict]:
    rows = []
    for provision, requirement in zip(provisions, requirements):
        reference = json.loads((REFERENCE / REFERENCE_FILES[provision["locus"]]).read_text(encoding="utf-8"))
        law = provision["law_text"].lower()
        locator = requirement["references"][0]["locator"]
        rows.append(
            {
                "locus": provision["locus"],
                "locator": locator,
                "id": requirement["id"],
                "strength": requirement.get("strength"),
                "law_has_shall": "shall" in law,
                "law_has_should": "should" in law,
                "law_has_may": "may" in law,
                "responsible": requirement.get("responsible"),
                "responsible_in_law_text": _named_in_law(requirement.get("responsible"), provision["law_text"]),
                "applicability": requirement.get("applicability"),
                "output_concepts": (requirement.get("discovery_hints") or {}).get("concepts", []),
                "reference_concepts": reference.get("discovery_hints", {}).get("concepts", []),
                "output_path_hints": (requirement.get("discovery_hints") or {}).get("path_hints", []),
                "reference_path_hints": reference.get("discovery_hints", {}).get("path_hints", []),
                "output_expected_evidence": (requirement.get("discovery_hints") or {}).get("expected_evidence", []),
                "reference_expected_evidence": reference.get("discovery_hints", {}).get("expected_evidence", []),
            }
        )
    return rows


def _named_in_law(responsible: str | None, law_text: str) -> bool | None:
    if responsible is None:
        return None
    return responsible.lower() in law_text.lower()


def _trace_summary(trace_dir: Path) -> dict:
    events_path = trace_dir / "events.jsonl"
    if not events_path.is_file():
        return {"events": 0}
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    calls = [event for event in events if event.get("event") == "model_call"]
    prompt_tokens = sum(event.get("prompt_tokens") or 0 for event in calls)
    completion_tokens = sum(event.get("completion_tokens") or 0 for event in calls)
    return {
        "calls": len(calls),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "stops": [
            {"stage": event.get("stage"), "locus": event.get("locus"), "reason": event.get("reason")}
            for event in events
            if event.get("event") == "stop"
        ],
        "run_end": next((event.get("status") for event in reversed(events) if event.get("event") == "run_end"), None),
    }


def _hashes(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.glob("*.json"))
    }


if __name__ == "__main__":
    main()
