"""One guidance file, one model call, one validated proposal list."""

from __future__ import annotations

from requirements.extract.call import CompleteFn, _one_call


def run_single_call(
    *,
    guidance_files: list,
    provisions_text: str,
    stage: str,
    strategy: str,
    model: str,
    temperature: float,
    endpoint: str,
    complete_fn: CompleteFn,
    validate_one,
    loci: set[str],
) -> tuple[list[dict], list[dict]]:
    path = guidance_files[0]
    proposals, note = _one_call(
        path,
        provisions_text,
        stage=stage,
        strategy=strategy,
        model=model,
        temperature=temperature,
        endpoint=endpoint,
        max_rounds=None,
        complete_fn=complete_fn,
        validate_one=validate_one,
        loci=loci,
        role="propose",
        prior=None,
    )
    return proposals, [note]
