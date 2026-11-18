"""Discover job files. Operational progress for the popup, not Pack contents.

The log is the printout. Candidate lists on the job are the return value the
page shows for this run. They are not Claims.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from common.errors import ModelError
from common.jsonio import read_json, write_json
from discovery.assess import (
    DEFAULT_ASSESS_LIMIT,
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    assess_candidates,
    shows_support,
)
from discovery.repos import set_repo_status
from discovery.search import discover_candidates

_LOCK = threading.Lock()

# Discover for a product pack reads that repo's curbpack.json, not a Pack-editor copy.
CURBPACK_COPY = "curbpack"

SearchFn = Callable[[Path, dict, dict], list]
AssessFn = Callable[..., list]


def start_discover_job(
    jobs_dir: Path,
    *,
    job_id: str,
    workspace: Path,
    repo_id: str,
    repo: Path,
    requirements: list[dict],
    hunt: dict,
    title: str,
    search: SearchFn | None = None,
    source_id: str = "",
    timestamp: str = "",
    pack_id: str = "",
    assess_limit: int = DEFAULT_ASSESS_LIMIT,
    assess: AssessFn | None = None,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
    complete=None,
) -> str:
    """Search every requirement on a daemon thread and return the job id."""
    if not isinstance(assess_limit, int) or isinstance(assess_limit, bool) or not 0 <= assess_limit <= 20:
        raise ModelError("discover", "assess_limit", "an integer from 0 to 20")
    jobs_dir.mkdir(parents=True, exist_ok=True)
    _save(
        jobs_dir,
        job_id,
        {
            "job_id": job_id,
            "status": "running",
            "stage": "start",
            "activity": "Discovering evidence in repo",
            "progress": 0.0,
            "title": title,
            "log_tail": [title],
            "results": [],
            "error": "",
            "repo_id": repo_id,
            "source_id": source_id,
            "timestamp": timestamp,
            "pack_id": pack_id,
            "assess_limit": assess_limit,
            "model": model,
        },
    )
    set_repo_status(workspace, repo_id, "running")
    threading.Thread(
        target=_run,
        kwargs={
            "jobs_dir": jobs_dir,
            "job_id": job_id,
            "workspace": workspace,
            "repo_id": repo_id,
            "repo": repo,
            "requirements": requirements,
            "hunt": hunt,
            "search": search or discover_candidates,
            "source_id": source_id,
            "timestamp": timestamp,
            "assess_limit": assess_limit,
            "assess": assess or assess_candidates,
            "model": model,
            "endpoint": endpoint,
            "complete": complete,
        },
        name=f"discover-{job_id}",
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
        tail.append("aborted")
        job["log_tail"] = tail[-200:]
        job["status"] = "aborted"
        job["stage"] = "aborted"
        job["activity"] = "Aborted"
        job["error"] = "aborted by user"
        write_json(path, job)


def reviewable_targets(workspace: Path) -> list[dict]:
    """Repository, source, and working copy pairs that have findings to review."""
    found: dict[tuple[str, str, str], dict] = {}

    def remember(repo_id: str, source_id: str, timestamp: str) -> None:
        if repo_id and source_id and timestamp:
            found[(repo_id, source_id, timestamp)] = {
                "repo_id": repo_id,
                "source_id": source_id,
                "timestamp": timestamp,
            }

    jobs_dir = workspace / "jobs"
    if jobs_dir.is_dir():
        for path in jobs_dir.glob("*.json"):
            try:
                document = read_json(path)
            except (OSError, ValueError):
                continue
            if isinstance(document, dict) and document.get("results"):
                remember(
                    str(document.get("repo_id") or ""),
                    str(document.get("source_id") or ""),
                    str(document.get("timestamp") or ""),
                )
    feedback_dir = workspace / "discover-feedback"
    if feedback_dir.is_dir():
        for path in feedback_dir.glob("*.json"):
            try:
                document = read_json(path)
            except (OSError, ValueError):
                continue
            requirements = document.get("requirements") if isinstance(document, dict) else None
            if isinstance(requirements, dict) and requirements:
                remember(
                    str(document.get("repo_id") or ""),
                    str(document.get("source_id") or ""),
                    str(document.get("timestamp") or ""),
                )
    return list(found.values())


def latest_job(
    jobs_dir: Path,
    *,
    repo_id: str,
    source_id: str,
    timestamp: str,
) -> dict | None:
    """Newest job that stored results for this repository, source, and copy."""
    if not jobs_dir.is_dir() or not repo_id or not source_id or not timestamp:
        return None
    chosen: dict | None = None
    chosen_mtime = -1.0
    for path in jobs_dir.glob("*.json"):
        try:
            document = read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict) or not document.get("results"):
            continue
        if document.get("repo_id") != repo_id or document.get("source_id") != source_id:
            continue
        if document.get("timestamp") != timestamp:
            continue
        mtime = path.stat().st_mtime
        if mtime >= chosen_mtime:
            chosen = document
            chosen_mtime = mtime
    return chosen


def _run(
    jobs_dir: Path,
    job_id: str,
    workspace: Path,
    repo_id: str,
    repo: Path,
    requirements: list[dict],
    hunt: dict,
    search: SearchFn,
    source_id: str = "",
    timestamp: str = "",
    assess_limit: int = DEFAULT_ASSESS_LIMIT,
    assess: AssessFn | None = None,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
    complete=None,
) -> None:
    try:
        if not repo.is_dir():
            _fail(jobs_dir, job_id, workspace, repo_id, f"repository is not a directory: {repo}")
            return
        rows = [item for item in requirements if isinstance(item, dict) and isinstance(item.get("id"), str)]
        if not rows:
            _fail(jobs_dir, job_id, workspace, repo_id, "this working copy has no requirements")
            return
        assess_fn = assess or assess_candidates
        prior_job = latest_job(jobs_dir, repo_id=repo_id, source_id=source_id, timestamp=timestamp)
        if prior_job and prior_job.get("job_id") == job_id:
            prior_job = None
        results: list[dict] = []
        for index, requirement in enumerate(rows):
            if read_job(jobs_dir, job_id).get("status") != "running":
                set_repo_status(workspace, repo_id, "aborted")
                return
            requirement_id = requirement["id"]
            locator = _locator(requirement)
            label = f"=== {requirement_id} {locator} ===" if locator else f"=== {requirement_id} ==="
            if not _advance(jobs_dir, job_id, progress=index / len(rows), line=label):
                set_repo_status(workspace, repo_id, "aborted")
                return
            found = search(repo, requirement, hunt)
            if not isinstance(found, list):
                found = []
            candidates = [_candidate(item) for item in found if isinstance(item, dict) and item.get("path")]
            lines = [f"candidates: {len(candidates)}"]
            lines.extend(f"{item['path']}  {item['matched_by']}" for item in candidates)
            block = {"requirement_id": requirement_id, "locator": locator, "candidates": []}
            results.append(block)
            if not _advance(jobs_dir, job_id, progress=index / len(rows), line="\n".join(lines), results=results):
                set_repo_status(workspace, repo_id, "aborted")
                return
            prior_rows = _prior_candidates(prior_job, requirement_id)
            calls = 0
            endpoint_down = ""
            for candidate in candidates:
                if read_job(jobs_dir, job_id).get("status") != "running":
                    set_repo_status(workspace, repo_id, "aborted")
                    return
                if endpoint_down:
                    scored = dict(candidate)
                    scored["assessment_state"] = "failed"
                    scored["assessment_error"] = endpoint_down
                    lines = [f"failed: {scored.get('path')}"]
                else:
                    limit = 1 if calls < assess_limit else 0
                    scored_rows = assess_fn(
                        repo,
                        requirement,
                        [candidate],
                        complete=complete,
                        assess_limit=limit,
                        prior=prior_rows,
                        model=model,
                        endpoint=endpoint,
                    )
                    scored = scored_rows[0] if scored_rows else dict(candidate)
                    state = scored.get("assessment_state")
                    if state == "assessed":
                        calls += 1
                        lines = [f"scoring {calls}/{assess_limit}: {scored.get('path')}"]
                    elif state == "reused":
                        lines = [f"reused: {scored.get('path')}"]
                    elif state == "failed":
                        error = str(scored.get("assessment_error") or "")
                        if _endpoint_failure(error):
                            endpoint_down = error
                        lines = [f"failed: {scored.get('path')}"]
                    else:
                        lines = [f"skipped cap: {scored.get('path')}"]
                if shows_support(scored):
                    block["candidates"].append(scored)
                else:
                    block.setdefault("dismissed", []).append(scored)
                    lines = [f"dropped: {scored.get('path')}"]
                processed = len(block["candidates"]) + len(block.get("dismissed") or [])
                if not _advance(
                    jobs_dir,
                    job_id,
                    progress=(index + processed / max(len(candidates), 1)) / len(rows),
                    line="\n".join(lines),
                    results=results,
                ):
                    set_repo_status(workspace, repo_id, "aborted")
                    return
        done = read_job(jobs_dir, job_id)
        if done.get("status") != "running":
            set_repo_status(workspace, repo_id, "aborted")
            return
        done["status"] = "done"
        done["stage"] = "done"
        done["activity"] = "Finished"
        done["progress"] = 1.0
        done["results"] = results
        _save(jobs_dir, job_id, done)
        set_repo_status(workspace, repo_id, "done")
    except Exception as exc:
        _fail(jobs_dir, job_id, workspace, repo_id, str(exc))


def _prior_candidates(job: dict | None, requirement_id: str) -> list[dict]:
    if not isinstance(job, dict):
        return []
    for row in job.get("results") or []:
        if isinstance(row, dict) and row.get("requirement_id") == requirement_id:
            kept = [item for item in row.get("candidates") or [] if isinstance(item, dict)]
            dropped = [item for item in row.get("dismissed") or [] if isinstance(item, dict)]
            return kept + dropped
    return []


def _endpoint_failure(error: str) -> bool:
    if not error:
        return False
    if error.startswith("unparseable") or "score outside" in error or "rank not" in error:
        return False
    if "missing rationale" in error or "existing file" in error or "readable file" in error:
        return False
    return True


def _candidate(item: dict) -> dict:
    return {
        "path": str(item.get("path") or ""),
        "matched_by": str(item.get("matched_by") or ""),
        "matched_hints": [
            str(hint)
            for hint in (item.get("matched_hints") or [])
            if isinstance(hint, str) and hint.strip()
        ],
        "excerpt": str(item.get("excerpt") or ""),
    }


def _locator(requirement: dict) -> str:
    references = requirement.get("references") or []
    if references and isinstance(references[0], dict):
        return str(references[0].get("locator") or "")
    return ""


def _fail(jobs_dir: Path, job_id: str, workspace: Path, repo_id: str, message: str) -> None:
    failed = read_job(jobs_dir, job_id)
    failed["status"] = "failed"
    failed["stage"] = "failed"
    failed["activity"] = "Failed"
    failed["progress"] = 1.0
    failed["error"] = message
    failed["log_tail"] = list(failed.get("log_tail") or []) + [message]
    _save(jobs_dir, job_id, failed)
    set_repo_status(workspace, repo_id, "failed")


def _advance(
    jobs_dir: Path,
    job_id: str,
    *,
    progress: float,
    line: str,
    results: list[dict] | None = None,
) -> bool:
    current = read_job(jobs_dir, job_id)
    running = current.get("status") == "running"
    if running:
        current["stage"] = "search"
        current["activity"] = "Discovering evidence in repo"
        current["progress"] = progress
    current["log_tail"] = list(current.get("log_tail") or []) + [line]
    if results is not None:
        current["results"] = results
    _save(jobs_dir, job_id, current)
    if not running:
        return False
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
