"""Stage 02 interpret and stage 03 discovery-hint producers.

Model output is expected as {"provisions": [...]} with the fields allowed by
requirements/ARCHITECTURE.md §4.2. Guidance rendering substitutes {provisions}
with JSON of the input list. multi_prompt keeps the last validated list.
propose_critique_revise critiques each provision and sends that critique,
with the source passage, into the revision. The default strategy is single_call.

strategy selects one of strategies/single_call.py, strategies/multi_prompt.py,
or strategies/propose_critique_revise.py. model, temperature, endpoint, and
guidance are the other caller settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from common.errors import ModelError
from requirements.extract.assemble import validate_hints_proposal, validate_interpret_proposal
from requirements.extract.call import CompleteFn, _default_complete
from requirements.extract.strategies.multi_prompt import run_multi_prompt
from requirements.extract.strategies.propose_critique_revise import run_propose_critique_revise
from requirements.extract.strategies.single_call import run_single_call
from requirements.extract.trace import Trace

_DEFAULT_STRATEGY = "single_call"
_DEFAULT_MODEL = "qwen3-coder:30b"
_DEFAULT_TEMPERATURE = 0.2
_DEFAULT_ENDPOINT = "http://127.0.0.1:11434"
_STRATEGIES = frozenset({"single_call", "multi_prompt", "propose_critique_revise"})


def interpret(
    provisions: list[dict],
    *,
    strategy: str = _DEFAULT_STRATEGY,
    model: str = _DEFAULT_MODEL,
    temperature: float = _DEFAULT_TEMPERATURE,
    endpoint: str = _DEFAULT_ENDPOINT,
    guidance: Path,
    max_rounds: int | None = None,
    complete: CompleteFn | None = None,
    trace_dir: Path | None = None,
    should_abort: Callable[[], bool] | None = None,
    trace=None,
) -> tuple[list[dict], list[dict]]:
    """Propose interpret fields for each provision. Returns (proposals, llm notes)."""
    return _produce(
        provisions,
        stage="interpret",
        validate_one=validate_interpret_proposal,
        strategy=strategy,
        model=model,
        temperature=temperature,
        endpoint=endpoint,
        guidance=guidance,
        max_rounds=max_rounds,
        complete=complete,
        trace_dir=trace_dir,
        should_abort=should_abort,
        trace=trace,
    )


def discovery_hints(
    provisions: list[dict],
    *,
    strategy: str = _DEFAULT_STRATEGY,
    model: str = _DEFAULT_MODEL,
    temperature: float = _DEFAULT_TEMPERATURE,
    endpoint: str = _DEFAULT_ENDPOINT,
    guidance: Path,
    max_rounds: int | None = None,
    complete: CompleteFn | None = None,
    trace_dir: Path | None = None,
    should_abort: Callable[[], bool] | None = None,
    trace=None,
) -> tuple[list[dict], list[dict]]:
    """Propose discovery_hints for each provision. Returns (proposals, llm notes)."""
    return _produce(
        provisions,
        stage="discovery_hints",
        validate_one=validate_hints_proposal,
        strategy=strategy,
        model=model,
        temperature=temperature,
        endpoint=endpoint,
        guidance=guidance,
        max_rounds=max_rounds,
        complete=complete,
        trace_dir=trace_dir,
        should_abort=should_abort,
        trace=trace,
    )


def proposals_from_producers(
    provisions: list[dict],
    *,
    adapter_dir: Path,
    complete: CompleteFn | None = None,
    strategy: str = _DEFAULT_STRATEGY,
    model: str = _DEFAULT_MODEL,
    temperature: float = _DEFAULT_TEMPERATURE,
    endpoint: str = _DEFAULT_ENDPOINT,
    max_rounds: int | None = None,
    trace_dir: Path | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Run stages 02 and 03 and merge proposals. Notes are concatenated in call order."""
    interpret_guidance = adapter_dir / "prompts" / "interpret.txt"
    hints_guidance = adapter_dir / "prompts" / "discovery_hints.txt"
    if not interpret_guidance.is_file():
        raise ModelError("produce", "guidance", f"an interpret prompt at {interpret_guidance}")
    if not hints_guidance.is_file():
        raise ModelError("produce", "guidance", f"a discovery_hints prompt at {hints_guidance}")
    trace = None
    if trace_dir is not None or should_abort is not None or max_rounds is not None:
        if strategy != "propose_critique_revise":
            raise ModelError(
                "produce",
                "strategy",
                "propose_critique_revise when max_rounds, trace_dir, or should_abort is set",
            )
    if trace_dir is not None:
        trace = Trace.open(trace_dir)
    try:
        if trace is not None:
            trace.add_meta({"adapter_dir": str(adapter_dir)})
        interpret_rows, interpret_notes = interpret(
            provisions,
            strategy=strategy,
            model=model,
            temperature=temperature,
            endpoint=endpoint,
            guidance=interpret_guidance,
            max_rounds=max_rounds,
            complete=complete,
            should_abort=should_abort,
            trace=trace,
        )
        hints_rows, hints_notes = discovery_hints(
            provisions,
            strategy=strategy,
            model=model,
            temperature=temperature,
            endpoint=endpoint,
            guidance=hints_guidance,
            max_rounds=max_rounds,
            complete=complete,
            should_abort=should_abort,
            trace=trace,
        )
        return interpret_rows + hints_rows, interpret_notes + hints_notes
    finally:
        if trace is not None:
            trace.finish()


def _produce(
    provisions: list[dict],
    *,
    stage: str,
    validate_one,
    strategy: str,
    model: str,
    temperature: float,
    endpoint: str,
    guidance: Path,
    max_rounds: int | None,
    complete: CompleteFn | None,
    trace_dir: Path | None = None,
    should_abort: Callable[[], bool] | None = None,
    trace=None,
) -> tuple[list[dict], list[dict]]:
    loci = _input_loci(provisions)
    if strategy not in _STRATEGIES:
        raise ModelError("produce", "strategy", f"one of {sorted(_STRATEGIES)}")
    if strategy == "propose_critique_revise":
        if not isinstance(max_rounds, int) or max_rounds < 1:
            raise ModelError("produce", "max_rounds", "an integer >= 1")
        if trace is not None and trace_dir is not None:
            raise ModelError("produce", "trace_dir", "absent when a trace is already open")
    elif max_rounds is not None:
        raise ModelError("produce", "max_rounds", "absent unless propose_critique_revise")
    elif trace_dir is not None or trace is not None:
        raise ModelError("produce", "trace_dir", "absent unless propose_critique_revise")
    elif should_abort is not None:
        raise ModelError("produce", "should_abort", "absent unless propose_critique_revise")

    complete_fn = complete or _default_complete
    guidance_files = _guidance_files(guidance, strategy)
    provisions_text = json.dumps(provisions, ensure_ascii=False, sort_keys=True)
    if strategy == "single_call":
        return run_single_call(
            guidance_files=guidance_files,
            provisions_text=provisions_text,
            stage=stage,
            strategy=strategy,
            model=model,
            temperature=temperature,
            endpoint=endpoint,
            complete_fn=complete_fn,
            validate_one=validate_one,
            loci=loci,
        )
    if strategy == "multi_prompt":
        return run_multi_prompt(
            guidance_files=guidance_files,
            provisions_text=provisions_text,
            stage=stage,
            strategy=strategy,
            model=model,
            temperature=temperature,
            endpoint=endpoint,
            complete_fn=complete_fn,
            validate_one=validate_one,
            loci=loci,
        )
    if strategy == "propose_critique_revise":
        if not guidance.is_file():
            raise ModelError("produce", "guidance", "one guidance file for propose_critique_revise")
        own_trace = False
        if trace is None and trace_dir is not None:
            trace = Trace.open(trace_dir)
            own_trace = True
        active = trace if trace is not None else Trace.disabled()
        try:
            return run_propose_critique_revise(
                provisions,
                stage=stage,
                validate_one=validate_one,
                strategy=strategy,
                model=model,
                temperature=temperature,
                endpoint=endpoint,
                guidance=guidance,
                max_rounds=max_rounds,
                complete_fn=complete_fn,
                trace=active,
                should_abort=should_abort,
            )
        finally:
            if own_trace:
                trace.finish()
    raise ModelError("produce", "strategy", f"one of {sorted(_STRATEGIES)}")


def _guidance_files(guidance: Path, strategy: str) -> list[Path]:
    if not guidance.exists():
        raise ModelError("produce", "guidance", f"an existing path, not {guidance}")
    if guidance.is_dir():
        files = sorted(path for path in guidance.iterdir() if path.is_file() and path.suffix == ".txt")
        if not files:
            raise ModelError("produce", "guidance", "a directory with at least one .txt file")
        if strategy == "single_call" and len(files) != 1:
            raise ModelError("produce", "guidance", "one guidance file for single_call")
        return files
    if not guidance.is_file():
        raise ModelError("produce", "guidance", "a file or directory")
    if strategy == "multi_prompt":
        # One file still makes one complete call; callers that need several
        # prompts pass a directory of .txt files.
        return [guidance]
    return [guidance]


def _input_loci(provisions: list[dict]) -> set[str]:
    loci: set[str] = set()
    for index, item in enumerate(provisions):
        if not isinstance(item, dict):
            raise ModelError("provisions", f"[{index}]", "an object")
        locus = item.get("locus")
        if not isinstance(locus, str) or not locus:
            raise ModelError("provisions", "locus", "a non-empty string")
        if locus in loci:
            raise ModelError("provisions", "locus", f"a unique locus, not a duplicate {locus}")
        loci.add(locus)
    if not loci:
        raise ModelError("provisions", "provisions", "a non-empty list")
    return loci
