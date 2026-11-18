"""One-Requirement discovery for tuning hints from the Requirements editor.

Calls the same retrieval and assessment as a Discover job. Progress lives in a
job file for the black log popup. Final candidates are temporary, not Claims.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json
from discovery.assess import assess_candidates, shows_support
from discovery.search import discover_candidates, read_source_text

_LOCK = threading.Lock()
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def result_path(jobs_dir: Path, requirement_id: str, repo_id: str) -> Path:
    return jobs_dir / f"try-discovery-{_slug(requirement_id)}__{_slug(repo_id)}.json"


def load_try_result(jobs_dir: Path, requirement_id: str, repo_id: str) -> dict | None:
    path = result_path(jobs_dir, requirement_id, repo_id)
    if not path.is_file():
        return None
    document = read_json(path)
    return document if isinstance(document, dict) else None


def start_try_job(
    jobs_dir: Path,
    *,
    job_id: str,
    repo: Path,
    repo_id: str,
    requirement: dict,
    hunt: dict,
    assess_limit: int = 5,
    pack_id: str = "",
    complete=None,
) -> str:
    """Run retrieval+assessment on a daemon thread. Return the job id."""
    requirement_id = str(requirement.get("id") or "").strip()
    if not requirement_id:
        raise ModelError("try discovery", "requirement", "an id")
    if not isinstance(repo_id, str) or not repo_id.strip():
        raise ModelError("try discovery", "repo_id", "a repository id")
    if not isinstance(assess_limit, int) or isinstance(assess_limit, bool) or not 0 <= assess_limit <= 20:
        raise ModelError("try discovery", "assess_limit", "an integer from 0 to 20")
    if not repo.is_dir():
        raise ModelError("try discovery", "repo", f"an existing directory, not {repo}")
    jobs_dir.mkdir(parents=True, exist_ok=True)
    title = f"Discovery test run — {requirement_id}"
    _save(
        jobs_dir,
        job_id,
        {
            "job_id": job_id,
            "kind": "try-discovery",
            "status": "running",
            "activity": "Starting…",
            "progress": 0.0,
            "title": title,
            "log_tail": [title, "Reading discovery hints…"],
            "error": "",
            "repo_id": repo_id,
            "requirement_id": requirement_id,
            "pack_id": pack_id,
            "assess_limit": assess_limit,
        },
    )
    threading.Thread(
        target=_run,
        kwargs={
            "jobs_dir": jobs_dir,
            "job_id": job_id,
            "repo": repo,
            "repo_id": repo_id,
            "requirement": requirement,
            "hunt": hunt,
            "assess_limit": assess_limit,
            "complete": complete,
        },
        name=f"try-discovery-{job_id}",
        daemon=True,
    ).start()
    return job_id


def read_try_job(jobs_dir: Path, job_id: str) -> dict:
    path = jobs_dir / f"{job_id}.json"
    if not path.is_file():
        raise ModelError("try discovery", "job_id", f"a known job, not {job_id}")
    document = read_json(path)
    if not isinstance(document, dict):
        raise ModelError("try discovery", "job", "a job object")
    return document


def candidate_for_path(document: dict | None, path: str) -> dict | None:
    if not isinstance(document, dict):
        return None
    for key in ("candidates", "dismissed"):
        for row in document.get(key) or []:
            if isinstance(row, dict) and row.get("path") == path:
                return row
    return None


def read_try_file(repo: Path, path: str) -> str:
    return read_source_text(repo, path)


def _run(
    *,
    jobs_dir: Path,
    job_id: str,
    repo: Path,
    repo_id: str,
    requirement: dict,
    hunt: dict,
    assess_limit: int,
    complete,
) -> None:
    requirement_id = str(requirement.get("id") or "")
    try:
        _advance(jobs_dir, job_id, progress=0.05, activity="Walking the repository…", line="Retrieve candidates")
        found = discover_candidates(repo, requirement, hunt)
        _advance(
            jobs_dir,
            job_id,
            progress=0.25,
            activity=f"Found {len(found)} candidate(s)",
            line=f"candidates: {len(found)}",
        )
        for item in found:
            if isinstance(item, dict) and item.get("path"):
                _advance(
                    jobs_dir,
                    job_id,
                    progress=0.25,
                    activity=f"Found {len(found)} candidate(s)",
                    line=f"{item['path']}  {item.get('matched_by') or ''}",
                )
        kept = []
        dismissed = []
        if not found:
            _finish(jobs_dir, job_id, requirement_id, repo_id, kept, dismissed)
            return
        total = len(found)
        for index, candidate in enumerate(found):
            path = str((candidate or {}).get("path") or "")
            _advance(
                jobs_dir,
                job_id,
                progress=0.25 + 0.7 * (index / max(total, 1)),
                activity=f"Assessing {index + 1}/{total}",
                line=f"assess: {path}",
            )
            scored_rows = assess_candidates(
                repo,
                requirement,
                [candidate],
                complete=complete,
                assess_limit=1 if index < assess_limit else 0,
            )
            row = scored_rows[0] if scored_rows else dict(candidate)
            state = row.get("assessment_state")
            if state in {"assessed", "reused"}:
                _advance(
                    jobs_dir,
                    job_id,
                    progress=0.25 + 0.7 * ((index + 1) / max(total, 1)),
                    activity=f"Assessing {index + 1}/{total}",
                    line=f"{state}: {path}  score={row.get('score')}  {row.get('rank')}",
                )
            elif state == "failed":
                _advance(
                    jobs_dir,
                    job_id,
                    progress=0.25 + 0.7 * ((index + 1) / max(total, 1)),
                    activity=f"Assessing {index + 1}/{total}",
                    line=f"failed: {path}  {row.get('assessment_error') or ''}",
                )
            else:
                _advance(
                    jobs_dir,
                    job_id,
                    progress=0.25 + 0.7 * ((index + 1) / max(total, 1)),
                    activity=f"Assessing {index + 1}/{total}",
                    line=f"skipped: {path}",
                )
            if shows_support(row):
                kept.append(row)
            else:
                dismissed.append(row)
                _advance(
                    jobs_dir,
                    job_id,
                    progress=0.25 + 0.7 * ((index + 1) / max(total, 1)),
                    activity=f"Assessing {index + 1}/{total}",
                    line=f"dropped: {path}",
                )
        _finish(jobs_dir, job_id, requirement_id, repo_id, kept, dismissed)
    except Exception as exc:
        _fail(jobs_dir, job_id, str(exc))


def _finish(
    jobs_dir: Path,
    job_id: str,
    requirement_id: str,
    repo_id: str,
    kept: list,
    dismissed: list,
) -> None:
    document = {
        "requirement_id": requirement_id,
        "repo_id": repo_id,
        "candidates": kept,
        "dismissed": dismissed,
    }
    write_json(result_path(jobs_dir, requirement_id, repo_id), document)
    current = read_try_job(jobs_dir, job_id)
    current["status"] = "done"
    current["activity"] = f"Done — {len(kept)} kept"
    current["progress"] = 1.0
    current["log_tail"] = list(current.get("log_tail") or []) + [
        f"kept: {len(kept)}",
        f"dismissed: {len(dismissed)}",
    ]
    current["repo_id"] = repo_id
    current["requirement_id"] = requirement_id
    _save(jobs_dir, job_id, current)


def _fail(jobs_dir: Path, job_id: str, message: str) -> None:
    current = read_try_job(jobs_dir, job_id)
    current["status"] = "failed"
    current["error"] = message
    current["activity"] = "Failed"
    current["progress"] = 1.0
    current["log_tail"] = list(current.get("log_tail") or []) + [f"error: {message}"]
    _save(jobs_dir, job_id, current)


def _advance(
    jobs_dir: Path,
    job_id: str,
    *,
    progress: float,
    activity: str,
    line: str,
) -> None:
    current = read_try_job(jobs_dir, job_id)
    if current.get("status") != "running":
        return
    current["progress"] = progress
    current["activity"] = activity
    tail = list(current.get("log_tail") or [])
    tail.append(line)
    current["log_tail"] = tail[-80:]
    _save(jobs_dir, job_id, current)


def _save(jobs_dir: Path, job_id: str, document: dict) -> None:
    with _LOCK:
        write_json(jobs_dir / f"{job_id}.json", document)


def _slug(value: str) -> str:
    cleaned = _SAFE.sub("-", value.strip()).strip("-")
    return cleaned or "x"
