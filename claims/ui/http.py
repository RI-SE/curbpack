"""Researcher routes. The server dispatches here and does not search or write Claims."""

from __future__ import annotations

from pathlib import Path

from claims.bind import create_configured_claims, read_claim, read_claims, rebind, suggest_claim_id, write_claim
from claims.ui.coverage import covered_paths, load_run
from claims.ui import researcher
from common.errors import CheckError, ModelError
from discovery.feedback import add_finding, load_feedback, save_check, save_vote
from discovery.jobs import latest_job
from discovery.present import overview_rows, signing_label
from discovery.repos import find_repo, load_repos, resolve_repo_path
from discovery.search import read_source_text
from requirements.workspace import load_working_copy, select_working_copy


def handle_get(root: Path, path: str, query: dict, *, sources: list, trust: dict) -> bytes | None:
    if path == "/discover/claims":
        context = _context(root, query, sources)
        rows = overview_rows(
            context["requirements"],
            context["job"],
            context["feedback"],
            context["claims"],
            repo=context["repo"],
            trust=trust,
        )
        return researcher.overview_page({**_ids(context), "rows": rows})
    if not path.startswith("/discover/claims/"):
        return None
    requirement_id, kind = _split(path)
    context = _context(root, query, sources)
    requirement = _requirement(context, requirement_id)
    if kind == "file":
        file_path = _one(query, "path")
        model = {**_ids(context), "requirement_id": requirement_id, "path": file_path}
        try:
            model["body"] = read_source_text(context["repo"], file_path)
        except ModelError as exc:
            model["error"] = str(exc)
            return researcher.file_page(model)
        candidate = _candidate(context, requirement_id, file_path)
        model["excerpt"] = str((candidate or {}).get("excerpt") or "")
        model["model_excerpt"] = str((candidate or {}).get("model_excerpt") or "")
        return researcher.file_page(model)
    model = _with_signing(context, requirement, query, trust)
    if _one(query, "from") == "review":
        model["covered_paths"] = sorted(
            covered_paths(context["claims"], load_run(context["repo"]), requirement_id)
        )
    return researcher.requirement_page(model)


def handle_post(root: Path, path: str, form: dict, *, sources: list, trust: dict):
    """Return a redirect URL, or HTML bytes for Create. None if this route is not ours."""
    if path not in {
        "/discover/feedback/vote",
        "/discover/feedback/checks",
        "/discover/feedback/add",
        "/discover/claims/create",
    }:
        return None
    context = _context(root, form, sources)
    requirement_id = _one(form, "requirement_id")
    requirement = _requirement(context, requirement_id)
    known = [item["id"] for item in context["requirements"]]
    file_path = _one(form, "path")
    common = dict(
        workspace=root,
        repo_id=context["repo_id"],
        source_id=context["source_id"],
        timestamp=context["timestamp"],
        requirement_id=requirement_id,
        path=file_path,
        known_ids=known,
    )
    if path == "/discover/feedback/vote":
        save_vote(**common, vote=_one(form, "vote"))
        return _back(context, requirement_id)
    if path == "/discover/feedback/checks":
        try:
            check, args, label = _check_from_form(file_path, form)
            document = save_check(**common, check=check, args=args, label=label)
            _sync_claim(context, requirement, file_path, document, form)
        except (ModelError, CheckError) as exc:
            model = _with_signing(context, requirement, form, trust)
            model["check_error"] = {
                "path": file_path,
                "check": _one(form, "check"),
                "invalid": _invalid_fields(exc),
                "values": {key: _one(form, key) for key in _CHECK_FIELDS},
            }
            return researcher.requirement_page(model)
        return _back(context, requirement_id)
    if path == "/discover/feedback/add":
        add_finding(**common, repo=context["repo"], rationale=_one(form, "rationale"))
        return _back(context, requirement_id, open_checks=file_path)
    marks = _marks(context, requirement_id)
    entry = marks.get(file_path) if isinstance(marks.get(file_path), dict) else {}
    checks = [item for item in (entry.get("checks") or []) if isinstance(item, dict)]
    if not checks:
        model = _with_signing(context, requirement, form, trust)
        model["notice"] = "This finding has no checks, so no Claim was created."
        return researcher.requirement_page(model)
    description = _one(form, "description").strip() or str(entry.get("human_why") or "").strip()
    if not description:
        model = _with_signing(context, requirement, form, trust)
        model["notice"] = "A Claim needs a description of why this evidence supports the Requirement."
        return researcher.requirement_page(model)
    try:
        source = _claim_source(requirement, form)
    except ModelError as exc:
        model = _with_signing(context, requirement, form, trust)
        model["notice"] = str(exc)
        return researcher.requirement_page(model)
    outcomes = create_configured_claims(
        context["repo"] / "claims",
        requirement_id=requirement_id,
        known_ids=known,
        source=source,
        args={"path": file_path},
        checks=checks,
        description=description,
    )
    context["claims"] = read_claims(context["repo"] / "claims")
    model = _with_signing(context, requirement, form, trust)
    model["outcomes"] = outcomes
    return researcher.requirement_page(model)


def _context(root: Path, bag: dict, sources: list) -> dict:
    repo_id = _one(bag, "repo") or _one(bag, "repo_id")
    source_id = _one(bag, "source") or _one(bag, "source_id")
    timestamp = _one(bag, "timestamp")
    row = find_repo(load_repos(root), repo_id)
    if row is None:
        raise ModelError("discover", "repo_id", f"a registered repository, not {repo_id}")
    source = next((item for item in sources if item.get("source_id") == source_id), None)
    if source is None:
        raise ModelError("discover", "source_id", f"a registered source, not {source_id}")
    pack_id = source.get("pack_id")
    if not isinstance(pack_id, str) or not pack_id:
        raise ModelError("discover", "pack_id", "a pack id on the source")
    directory = select_working_copy(root, pack_id, timestamp)
    _pack, requirements = load_working_copy(directory)
    requirements = [item for item in requirements if isinstance(item, dict) and isinstance(item.get("id"), str)]
    repo = resolve_repo_path(root, str(row.get("path") or ""))
    job = latest_job(root / "jobs", repo_id=repo_id, source_id=source_id, timestamp=timestamp)
    feedback = load_feedback(root, repo_id, source_id, timestamp)
    claims_dir = repo / "claims"
    claims = read_claims(claims_dir) if claims_dir.is_dir() else []
    return {
        "repo_id": repo_id,
        "source_id": source_id,
        "timestamp": timestamp,
        "repo": repo,
        "requirements": requirements,
        "job": job,
        "feedback": feedback,
        "claims": claims,
    }


def _requirement(context: dict, requirement_id: str) -> dict:
    for item in context["requirements"]:
        if item.get("id") == requirement_id:
            return item
    raise ModelError("discover", "requirement_id", f"an id in this working copy, not {requirement_id}")


def _with_signing(context: dict, requirement: dict, bag: dict, trust: dict) -> dict:
    model = _requirement_model(context, requirement, bag)
    model["signing"] = signing_label(context["claims"], requirement["id"], context["repo"], trust)
    return model


def _requirement_model(context: dict, requirement: dict, bag: dict) -> dict:
    requirement_id = requirement["id"]
    block = None
    if isinstance(context.get("job"), dict):
        for row in context["job"].get("results") or []:
            if isinstance(row, dict) and row.get("requirement_id") == requirement_id:
                block = row
                break
    return {
        **_ids(context),
        "requirement": requirement,
        "candidates": (block or {}).get("candidates") or [],
        "marks": _marks(context, requirement_id),
        "claims": context["claims"],
        "model": (context.get("job") or {}).get("model") or "",
        "notice": _one(bag, "notice"),
        "open_checks": _one(bag, "open_checks"),
        "repo_files": _repo_files(context["repo"]),
    }


def _marks(context: dict, requirement_id: str) -> dict:
    requirements = context["feedback"].get("requirements") or {}
    marks = requirements.get(requirement_id)
    return marks if isinstance(marks, dict) else {}


def _candidate(context: dict, requirement_id: str, path: str) -> dict | None:
    model = _requirement_model(context, _requirement(context, requirement_id), {})
    for item in model["candidates"]:
        if isinstance(item, dict) and item.get("path") == path:
            return item
    return None


def _ids(context: dict) -> dict:
    return {
        "repo_id": context["repo_id"],
        "source_id": context["source_id"],
        "timestamp": context["timestamp"],
    }


def _split(path: str) -> tuple[str, str]:
    rest = path[len("/discover/claims/") :]
    if rest.endswith("/file"):
        return rest[: -len("/file")], "file"
    return rest, "page"


def _back(context: dict, requirement_id: str, **extra: str) -> str:
    from urllib.parse import quote

    query = (
        f"repo={quote(context['repo_id'])}&source={quote(context['source_id'])}"
        f"&timestamp={quote(context['timestamp'])}"
    )
    for key, value in extra.items():
        if value:
            query += f"&{quote(key)}={quote(value)}"
    return f"/discover/claims/{quote(requirement_id)}?{query}"


def _check_from_form(path: str, form: dict) -> tuple[str, dict, str]:
    """Map a PoC picker choice onto a Packs v2 check the runner can execute."""
    choice = _one(form, "check")
    if choice == "exist":
        return "exist", {"paths": [path]}, ""
    if choice == "contents":
        check, args = _file_present(path, form)
        if check == "exist":
            raise ModelError("contents", "probes", "at least one probe; use exist when only presence matters")
        return check, args, ""
    if choice == "file_present":
        check, args = _file_present(path, form)
        return check, args, "file_present"
    if choice == "text_forbid":
        return "contents", {"path": path, "probes": [{"kind": "pattern", "pattern": _one(form, "pattern")}]}, "text_forbid"
    if choice == "anti_placeholder":
        return "contents", {"path": path, "probes": [{"kind": "placeholder"}]}, "anti_placeholder"
    if choice == "contents":
        return _contents_probe(path, form)
    if choice == "dep_ban":
        versions = [part.strip() for part in _one(form, "banned_versions").split(",") if part.strip()]
        return "dep_ban", {"package": _one(form, "package"), "banned_versions": versions}, ""
    if choice == "fresh":
        args: dict = {"path": path}
        if _one(form, "max_age_days"):
            args["max_age_days"] = _integer(form, "max_age_days")
        if _one(form, "since_ref"):
            args["since_ref"] = _one(form, "since_ref")
        return "fresh", args, ""
    if choice == "owned":
        args = {"path": path, "bind_repo_token": _one(form, "owned_bind_repo_token") in {"1", "true", "on"}}
        if _one(form, "require_git_author_name"):
            args["name"] = _one(form, "require_git_author_name")
        if _one(form, "require_git_author_email"):
            args["email"] = _one(form, "require_git_author_email")
        return "owned", args, ""
    raise ModelError(
        "discover",
        "check",
        "file_present, text_forbid, anti_placeholder, dep_ban, fresh, or owned",
    )


def _file_present(path: str, form: dict) -> tuple[str, dict]:
    probes = []
    if _one(form, "min_bytes"):
        probes.append({"kind": "size", "bytes": _integer(form, "min_bytes"), "op": ">="})
    if _one(form, "min_words"):
        probes.append({"kind": "words", "n": _integer(form, "min_words"), "op": ">="})
    headers = [part.strip() for part in _one(form, "require_headers").split(",") if part.strip()]
    if headers:
        probes.append({"kind": "headers", "headers": headers})
    if _one(form, "fp_bind_repo_token") in {"1", "true", "on"}:
        probes.append({"kind": "token"})
    extra = [part.strip() for part in _one(form, "require_tree_paths").split(",") if part.strip()]
    paths = [path, *extra]
    if not probes:
        return "exist", {"paths": paths}
    if len(paths) == 1:
        return "contents", {"path": path, "probes": probes}
    return "contents", {"paths": paths, "probes": probes}


def _contents_probe(path: str, form: dict) -> tuple[str, dict, str]:
    kind = _one(form, "probe_kind") or "pattern"
    probe: dict = {"kind": kind}
    if kind == "pattern":
        probe["pattern"] = _one(form, "pattern")
    elif kind == "size":
        probe["bytes"] = _integer(form, "bytes")
        probe["op"] = _one(form, "op") or ">="
    elif kind == "words":
        probe["n"] = _integer(form, "n")
        probe["op"] = _one(form, "op") or ">="
    elif kind == "headers":
        headers = [part.strip() for part in _one(form, "headers").split(",") if part.strip()]
        probe["headers"] = headers
    elif kind not in {"token", "placeholder"}:
        raise ModelError("contents", "kind", "size, words, headers, token, pattern, or placeholder")
    return "contents", {"path": path, "probes": [probe]}, ""


def _integer(form: dict, key: str) -> int:
    raw = _one(form, key)
    if not raw.lstrip("-").isdigit():
        raise ModelError("contents", key, "integer")
    return int(raw)


def _sync_claim(context: dict, requirement: dict, file_path: str, feedback: dict, form: dict) -> None:
    """A row with one or more checks is the Claim. Saving a check writes that file."""
    requirement_id = requirement["id"]
    marks = (feedback.get("requirements") or {}).get(requirement_id) or {}
    entry = marks.get(file_path) if isinstance(marks.get(file_path), dict) else {}
    checks = [
        {"check": item["check"], "args": item["args"]}
        for item in (entry.get("checks") or [])
        if isinstance(item, dict) and item.get("check") and isinstance(item.get("args"), dict)
    ]
    if not checks:
        return
    description = str(entry.get("human_why") or "").strip() or _candidate_why(context, requirement_id, file_path)
    if not description:
        raise ModelError(
            "claim",
            "description",
            "a rationale for why this evidence source supports the Requirement",
        )
    source = _claim_source(requirement, form)
    known = [item["id"] for item in context["requirements"]]
    claim_id = suggest_claim_id(requirement_id, file_path)
    directory = context["repo"] / "claims"
    destination = directory / f"{claim_id}.json"
    if destination.is_file():
        existing = read_claim(destination)
        same = (
            existing.get("source") == source
            and existing.get("args") == {"path": file_path}
            and existing.get("checks") == checks
            and existing.get("description") == description
        )
        if same:
            return
        write_claim(
            directory,
            rebind(
                existing,
                source=source,
                args={"path": file_path},
                checks=checks,
                description=description,
            ),
        )
        return
    create_configured_claims(
        directory,
        requirement_id=requirement_id,
        known_ids=known,
        source=source,
        args={"path": file_path},
        checks=checks,
        description=description,
        claim_id=claim_id,
    )


def _candidate_why(context: dict, requirement_id: str, file_path: str) -> str:
    job = context.get("job")
    if not isinstance(job, dict):
        return ""
    for block in job.get("results") or []:
        if not isinstance(block, dict) or block.get("requirement_id") != requirement_id:
            continue
        rows = list(block.get("candidates") or []) + list(block.get("dismissed") or [])
        for row in rows:
            if isinstance(row, dict) and row.get("path") == file_path:
                return str(row.get("why") or "").strip()
    return ""


def _claim_source(requirement: dict, form: dict) -> str:
    posted = _one(form, "claim_source").strip()
    if posted:
        return posted
    ids = _source_ids(requirement)
    if len(ids) == 1:
        return ids[0]
    raise ModelError("claim", "source", "one source id from discovery_hints.sources")


def _source_ids(requirement: dict) -> list[str]:
    hints = requirement.get("discovery_hints") if isinstance(requirement.get("discovery_hints"), dict) else {}
    sources = hints.get("sources") if isinstance(hints, dict) else None
    ids = []
    for item in sources or []:
        if isinstance(item, dict) and isinstance(item.get("source"), str) and item["source"] not in ids:
            ids.append(item["source"])
    return ids


_CHECK_FIELDS = (
    "min_bytes",
    "min_words",
    "require_headers",
    "fp_bind_repo_token",
    "require_tree_paths",
    "pattern",
    "package",
    "banned_versions",
    "max_age_days",
    "since_ref",
    "owned_bind_repo_token",
    "require_git_author_email",
    "require_git_author_name",
)


def _invalid_fields(exc: BaseException) -> list[str]:
    field = getattr(exc, "field", "")
    if field in {"min_bytes", "bytes"}:
        return ["min_bytes"]
    if field in {"min_words", "n"}:
        return ["min_words"]
    if field == "max_age_days":
        return ["max_age_days"]
    if field == "pattern":
        return ["pattern"]
    if field == "package":
        return ["package"]
    if field == "probes":
        return ["min_bytes", "min_words", "require_headers"]
    return []


def _repo_files(repo: Path, *, limit: int = 500) -> list[str]:
    """Repo-relative files a person can pick when adding a candidate by hand."""
    root = repo.resolve()
    if not root.is_dir():
        return []
    paths = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if relative.startswith("."):
            continue
        paths.append(relative)
        if len(paths) >= limit:
            break
    return paths


def _one(bag: dict, key: str) -> str:
    value = bag.get(key) or [""]
    if isinstance(value, list):
        return str(value[0] if value else "").strip()
    return str(value).strip()
