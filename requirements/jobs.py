"""Extract job files. They are operational state, not Pack contents."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from common.errors import ModelError
from common.jsonio import read_json, write_json
from requirements.extract.adapter import load_adapter, section_provisions
from requirements.extract.produce import proposals_from_producers
from requirements.workspace import extract_section, mark_selected, mark_source_adapter, selected_copy

_LOCK = threading.Lock()

_ACTIVITY = {
    "start": "Starting extraction",
    "interpret": "Running stage 02 interpret and stage 03 discovery hints",
    "assemble": "Assembling the working copy",
    "done": "Finished",
    "failed": "Failed",
    "aborted": "Aborted",
}

CompleteFn = Callable[[str, dict], str]


def start_extract_job(
    jobs_dir: Path,
    *,
    job_id: str,
    root: Path,
    adapter_dir: Path,
    section_id: str,
    pack: dict,
    proposals: list[dict] | None = None,
    complete: CompleteFn | None = None,
) -> str:
    """Run extract on a daemon thread and return the job id.

    When ``proposals`` is omitted, stages 02 and 03 run first (inject ``complete``
    in tests). An explicit ``proposals`` list is the fixture path and skips the
    model producers.
    """
    jobs_dir.mkdir(parents=True, exist_ok=True)
    _save(
        jobs_dir,
        job_id,
        {
            "job_id": job_id,
            "status": "running",
            "stage": "start",
            "activity": _ACTIVITY["start"],
            "progress": 0.2,
            "log_tail": [f"start {section_id}"],
        },
    )
    threading.Thread(
        target=_run_extract,
        args=(jobs_dir, job_id, root, adapter_dir, section_id, pack, proposals, complete),
        name=f"extract-{job_id}",
        daemon=True,
    ).start()
    return job_id


def read_job(jobs_dir: Path, job_id: str) -> dict:
    path = _job_path(jobs_dir, job_id)
    if not path.is_file():
        raise ModelError("job", "id", "an existing job file")
    document = read_json(path)
    if not isinstance(document, dict):
        raise ModelError("job", "id", "a job object")
    return document


def request_abort(jobs_dir: Path, job_id: str) -> None:
    """Mark a running job aborted. A finished job is left as it is."""
    path = _job_path(jobs_dir, job_id)
    with _LOCK:
        if not path.is_file():
            raise ModelError("job", "id", "an existing job file")
        job = read_json(path)
        if not isinstance(job, dict) or job.get("status") != "running":
            return
        tail = [line for line in list(job.get("log_tail") or []) if isinstance(line, str)]
        tail.append("aborted by user")
        job["log_tail"] = tail[-200:]
        job["status"] = "aborted"
        job["stage"] = "aborted"
        job["activity"] = _ACTIVITY["aborted"]
        job["error"] = "aborted by user"
        write_json(path, job)


def _run_extract(
    jobs_dir: Path,
    job_id: str,
    root: Path,
    adapter_dir: Path,
    section_id: str,
    pack: dict,
    proposals: list[dict] | None,
    complete: CompleteFn | None,
) -> None:
    if not _advance(jobs_dir, job_id, stage="start", progress=0.2, line=f"extract {section_id}"):
        return
    try:
        adapter = load_adapter(adapter_dir / "adapter.json")
        llm_notes = None
        if proposals is None:
            if not _advance(jobs_dir, job_id, stage="interpret", progress=0.4, line="stages 02 and 03"):
                return
            extracted = section_provisions(adapter_dir, adapter, section_id)
            provisions = [
                {"locus": item["locus"], "law_text": item["law_text"]}
                for item in extracted["provisions"]
            ]
            proposals, llm_notes = proposals_from_producers(
                provisions,
                adapter_dir=adapter_dir,
                complete=complete,
            )
        if not _advance(jobs_dir, job_id, stage="assemble", progress=0.8, line="stage 04 assemble"):
            return
        result = extract_section(
            root,
            adapter_dir,
            adapter,
            section_id,
            proposals,
            pack,
            llm_notes=llm_notes,
        )
    except Exception as exc:
        failed = read_job(jobs_dir, job_id)
        if failed.get("status") == "aborted":
            return
        failed["status"] = "failed"
        failed["stage"] = "failed"
        failed["activity"] = _ACTIVITY["failed"]
        failed["progress"] = 1.0
        failed["error"] = str(exc)
        failed["log_tail"] = list(failed.get("log_tail") or []) + [str(exc)]
        _save(jobs_dir, job_id, failed)
        return
    if read_job(jobs_dir, job_id).get("status") == "aborted":
        return
    mark_source_adapter(root, str(adapter["id"]))
    base = selected_copy(root, pack["id"])
    done = read_job(jobs_dir, job_id)
    if done.get("status") == "aborted":
        return
    done["status"] = "done"
    done["stage"] = "done"
    done["activity"] = _ACTIVITY["done"]
    done["progress"] = 1.0
    done.pop("error", None)
    done["copy_timestamp"] = result["copy"].name
    done["adapter_id"] = adapter["id"]
    if base is None:
        mark_selected(root, pack["id"], result["copy"].name)
    else:
        done["base_timestamp"] = base.name
    done["log_tail"] = list(done.get("log_tail") or []) + [f"wrote {result['copy'].name}"]
    _save(jobs_dir, job_id, done)


def _advance(jobs_dir: Path, job_id: str, *, stage: str, progress: float, line: str) -> bool:
    """Record stage activity. Return False when the job is no longer running."""
    current = read_job(jobs_dir, job_id)
    if current.get("status") != "running":
        return False
    current["stage"] = stage
    current["activity"] = _ACTIVITY[stage]
    current["progress"] = progress
    current["log_tail"] = list(current.get("log_tail") or []) + [line]
    _save(jobs_dir, job_id, current)
    return read_job(jobs_dir, job_id).get("status") == "running"


def _save(jobs_dir: Path, job_id: str, job: dict) -> None:
    path = _job_path(jobs_dir, job_id)
    with _LOCK:
        if path.is_file():
            existing = read_json(path)
            if (
                isinstance(existing, dict)
                and existing.get("status") == "aborted"
                and job.get("status") != "aborted"
            ):
                return
        tail = [line for line in list(job.get("log_tail") or []) if isinstance(line, str)]
        job["log_tail"] = tail[-200:]
        write_json(path, job)


def _job_path(jobs_dir: Path, job_id: str) -> Path:
    if not job_id or Path(job_id).name != job_id or job_id in {".", ".."}:
        raise ModelError("job", "id", "a single file name")
    return jobs_dir / f"{job_id}.json"
