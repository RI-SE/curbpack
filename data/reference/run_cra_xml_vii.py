"""One real cra-xml Annex VII extract into the gitignored workspace.

Does not change selection.json. Does not overwrite an existing timestamp.
Writes a small outcome file under poc2/data/reference/runs/.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POC2 = ROOT / "poc2"
sys.path.insert(0, str(POC2))

from requirements.extract.adapter import ADAPTERS, load_adapter, section_provisions  # noqa: E402
from requirements.extract.produce import _default_complete, proposals_from_producers  # noqa: E402
from requirements.workspace import extract_section  # noqa: E402

WORKSPACE = POC2 / "data" / "workspace"
RUNS = POC2 / "data" / "reference" / "runs"


def main() -> None:
    label = sys.argv[1]
    adapter_dir = ADAPTERS / "cra-xml"
    adapter = load_adapter(adapter_dir / "adapter.json")
    extracted = section_provisions(adapter_dir, adapter, "VII")
    provisions = [
        {"locus": item["locus"], "law_text": item["law_text"]}
        for item in extracted["provisions"]
    ]
    raw_dir = RUNS / label
    raw_dir.mkdir(parents=True, exist_ok=False)
    call_index = {"n": 0}

    def complete(prompt: str, settings: dict) -> str:
        call_index["n"] += 1
        (raw_dir / f"prompt-{call_index['n']}-{settings['stage']}.txt").write_text(prompt, encoding="utf-8")
        try:
            text = _default_complete(prompt, settings)
        except Exception:
            (raw_dir / f"error-{call_index['n']}.txt").write_text(traceback.format_exc(), encoding="utf-8")
            raise
        (raw_dir / f"response-{call_index['n']}-{settings['stage']}.txt").write_text(text, encoding="utf-8")
        return text

    outcome: dict = {
        "label": label,
        "model": "qwen3-coder:30b",
        "strategy": "single_call",
        "temperature": 0.2,
        "endpoint": "http://127.0.0.1:11434",
        "section": "VII",
    }
    try:
        proposals, notes = proposals_from_producers(
            provisions,
            adapter_dir=adapter_dir,
            strategy="single_call",
            model="qwen3-coder:30b",
            temperature=0.2,
            endpoint="http://127.0.0.1:11434",
            complete=complete,
        )
        pack = {"id": adapter["pack_id"], "name": "cra-xml extract", "version": "0.1.0"}
        result = extract_section(
            WORKSPACE,
            adapter_dir,
            adapter,
            "VII",
            proposals,
            pack,
            llm_notes=notes,
        )
        outcome["status"] = "written"
        outcome["copy"] = result["copy"].name
        outcome["requirement_count"] = len(result["requirements"])
        outcome["exclusions"] = result["exclusions"]
        outcome["llm"] = notes
    except Exception as exc:
        outcome["status"] = "failed"
        outcome["error"] = str(exc)
        (raw_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
    (raw_dir / "outcome.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))
    if outcome["status"] != "written":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
