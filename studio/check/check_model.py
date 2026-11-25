"""Check view-model and POST. The URL stays on the old server."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from curbcheck.api import _pack_version_dir, packs_dir, reports_dir
from common.errors import ModelError
from common.jsonio import read_json
from common.store import load_run_result

if TYPE_CHECKING:
    from app.server import Workspace


def new_check_run_path(folder: Path) -> Path:
    """A new Check is a directory. The run, its Review, and its Remedy live there."""
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        directory = folder / f"run-result_{stamp}"
        if not directory.exists():
            directory.mkdir()
            return directory / "run-result.json"
        time.sleep(1)


def _run_stamp(path: Path) -> str:
    if path.name == "run-result.json" and path.parent.name.startswith("run-result_"):
        return path.parent.name
    return path.name


def _run_result_files(folder: Path) -> list[Path]:
    files = [path for path in folder.glob("run-result_*.json") if path.is_file()]
    files.extend(path for path in folder.glob("run-result_*/run-result.json") if path.is_file())
    return sorted(files, key=_run_stamp)


def _is_run_result(path: Path) -> bool:
    return path.is_file() and (
        (path.name.startswith("run-result_") and path.name.endswith(".json"))
        or (path.name == "run-result.json" and path.parent.name.startswith("run-result_"))
    )


def _confined_run_result_path(results_folder: str, requested: str) -> str:
    if not results_folder:
        return ""
    folder = Path(results_folder).resolve()
    wanted = (requested or "").strip()
    if wanted:
        path = Path(wanted).resolve()
        try:
            path.relative_to(folder)
        except ValueError:
            return ""
        if _is_run_result(path):
            return str(path)
        return ""
    dated = _run_result_files(folder)
    if dated:
        return str(dated[-1].resolve())
    return ""


def _check_editor_model(ws: Workspace, query: dict) -> dict:
    from app.server import (
        _door_path_fields,
        _listed_repos,
        _registered_repo_path,
        _sync_open_repo,
    )

    repos = _listed_repos(ws)
    repo_id = _sync_open_repo(ws, query)
    if repo_id and not any(row.get("id") == repo_id for row in repos):
        raise ModelError("check", "repo", f"a registered repository, not {repo_id}")
    fields = _door_path_fields(ws, repo_id) if repo_id else {}
    packs: list[dict] = []
    selection = ""
    opened: Path | None = None
    reports_folder: Path | None = None
    values = {key: "" for key in ("packs_dir", "claims_dir", "results_dir", "reports_dir")}
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        opened = repo
        config_path = repo / "curbpack.json"
        if config_path.is_file():
            from common.validate import validate_curbpack_config

            config = validate_curbpack_config(read_json(config_path))
            reports_folder = reports_dir(repo, config)
            for key in values:
                values[key] = str(config.get(key) or "")
            packs_root = packs_dir(repo, config)
            claim_counts = _claims_by_pack(repo)
            for pack_id in config["packs"]:
                try:
                    pack_dir = _pack_version_dir(packs_root, pack_id)
                    present = True
                except ModelError:
                    pack_dir = packs_root / pack_id
                    present = False
                packs.append(
                    {
                        "id": pack_id,
                        "name": _pack_name(repo, pack_id),
                        "present": present,
                        "pack_dir": str(pack_dir.resolve()),
                        "claims": claim_counts.get(pack_id, 0),
                    }
                )
            if "exclude_requirements" in config:
                selection = "exclude_requirements " + ", ".join(config["exclude_requirements"])
            elif "requirements" in config:
                selection = "requirements " + ", ".join(config["requirements"])
    results_folder = fields.get("results_dir") or ""
    result_path = _confined_run_result_path(results_folder, (query.get("result") or [""])[0])
    return {
        "repos": repos,
        "repo_id": repo_id,
        "ask_read": False,
        "packs": packs,
        "selection": selection,
        "curbpack_file": fields.get("curbpack_file") or "",
        "directory": fields.get("directory") or "",
        "claims_dir": fields.get("claims_dir") or "",
        "results_dir": fields.get("results_dir") or "",
        "reports_dir": fields.get("reports_dir") or "",
        "packs_dir_value": values["packs_dir"],
        "claims_dir_value": values["claims_dir"],
        "results_dir_value": values["results_dir"],
        "reports_dir_value": values["reports_dir"],
        "run_result_path": result_path,
        "runs": _annotate_rounds(
            opened,
            reports_folder,
            _performed_checks(results_folder),
            repo_id,
        ),
    }


def _pack_name(repo: Path, pack_id: str) -> str:
    from discovery.door import pack_display_name

    try:
        return pack_display_name(repo, pack_id)
    except (ModelError, OSError, ValueError):
        return pack_id


def _claims_by_pack(repo: Path) -> dict[str, int]:
    from discovery.door import repo_claims_dir
    from studio.claim.impl.bind import read_claims

    try:
        folder = repo_claims_dir(repo)
    except ModelError:
        return {}
    if not folder.is_dir():
        return {}
    try:
        claims = read_claims(folder)
    except (ModelError, OSError, ValueError):
        return {}
    counts: dict[str, int] = {}
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        pack_id = claim.get("pack_id")
        if isinstance(pack_id, str) and pack_id:
            counts[pack_id] = counts.get(pack_id, 0) + 1
    return counts


def _remedy_pdf_href(repo_id: str, path: Path, directory: Path | None, document: object) -> str:
    """The Markdown report beside the active seal. An open round has no report link."""
    from urllib.parse import quote

    from studio.review.impl.remedy_report import published_remedy_file

    if not repo_id or directory is None or published_remedy_file(directory, document) is None:
        return ""
    return (
        f"/review/remedy-report?repo={quote(repo_id, safe='')}"
        f"&result={quote(str(path), safe='')}"
    )


def _remedy_full_check_counts(repo: Path | None, directory: Path | None, document: object) -> dict | None:
    """Pass, fail, skipped, and stale from the full Check recorded on the signed remediation."""
    from studio.review.impl.items import active_remedy_report

    names: list[str] = []
    active = active_remedy_report(directory, document) if directory is not None else None
    if active is not None and active.is_file():
        try:
            sealed = read_json(active)
        except (OSError, ValueError):
            sealed = None
        if isinstance(sealed, dict):
            names = [item for item in (sealed.get("full_checks") or []) if isinstance(item, str) and item]
    if not names and isinstance(document, dict):
        names = [item for item in (document.get("projected_runs") or []) if isinstance(item, str) and item]
    if repo is None or not names:
        return None
    stamp = names[-1]
    folder = remediation_results_dir(repo)
    path = folder / stamp / "run-result.json"
    if not path.is_file():
        flat = folder / stamp
        path = flat if flat.is_file() else None
    if path is None:
        return None
    try:
        loaded = read_json(path)
    except (OSError, ValueError):
        return None
    if isinstance(loaded, dict) and isinstance(loaded.get("run_result"), dict):
        loaded = loaded["run_result"]
    if not isinstance(loaded, dict):
        return None
    return _outcome_counts(loaded)


def _quote_link(repo_id: str, **query: str) -> str:
    from urllib.parse import quote

    parts = [f"repo={quote(repo_id, safe='')}"]
    for key, value in query.items():
        if value:
            parts.append(f"{key}={quote(value, safe='')}")
    return "/review?" + "&".join(parts)


def _document_is_signed(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        document = read_json(path)
    except (OSError, ValueError):
        return False
    return isinstance(document, dict) and isinstance(document.get("signed"), dict)


def _items_document(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        document = read_json(path)
    except (OSError, ValueError):
        return {}
    return document if isinstance(document, dict) else {}


def _remediation_started(path: Path) -> bool:
    document = _items_document(path)
    if document.get("remedy") is True:
        return True
    rows = document.get("items")
    return any(
        isinstance(row, dict) and any(isinstance(entry, dict) for entry in row.get("remediation_history") or [])
        for row in rows or []
    )


def _newest_signed(directory: Path, *patterns: str) -> Path | None:
    found: list[Path] = []
    for pattern in patterns:
        for path in directory.glob(pattern):
            if path.name.endswith(".items.json"):
                continue
            if _document_is_signed(path):
                found.append(path)
    if not found:
        return None
    return sorted(found, key=lambda path: path.name)[-1]


def _round_state(repo_id: str, path: Path, items: Path | None, *, locked: bool, remedy_signed: bool) -> dict:
    """Create, Continue, and View for the review. Start, Continue, and Completed for the remedy."""
    result = str(path)
    review_href = _quote_link(repo_id, result=result)
    if not locked:
        if items is not None and items.is_file():
            return {
                "review_label": "Continue",
                "review_href": _quote_link(repo_id, result=result, resume="1"),
                "remedy_label": "—",
                "remedy_href": "",
            }
        return {"review_label": "Create", "review_href": review_href, "remedy_label": "—", "remedy_href": ""}
    review_href = _quote_link(repo_id, result=result, view="review")
    if remedy_signed:
        remedy_label = "Completed"
        remedy_href = _quote_link(repo_id, result=result, mode="remediation", view="report")
    elif items is not None and _remediation_started(items):
        remedy_label = "Continue"
        remedy_href = _quote_link(repo_id, result=result, mode="remediation")
    else:
        remedy_label = "Start"
        remedy_href = _quote_link(repo_id, result=result, mode="remediation")
    return {
        "review_label": "View",
        "review_href": review_href,
        "remedy_label": remedy_label,
        "remedy_href": remedy_href,
    }


def check_result_removal(results_folder: str, requested: str) -> list[Path]:
    """Files that belong to one Checks performed row, and nothing outside that row."""
    confined = _confined_run_result_path(results_folder, requested)
    if not confined:
        return []
    path = Path(confined)
    folder = Path(results_folder).resolve()
    if path.name == "run-result.json" and path.parent.name.startswith("run-result_"):
        directory = path.parent
        if directory.is_symlink() or directory.parent.resolve() != folder:
            return []
        return _contained_files(directory, folder)
    if path.is_symlink() or path.parent.resolve() != folder:
        return []
    return [path]


def remove_check_result(results_folder: str, requested: str) -> list[str]:
    """Delete one check result. Returns the paths that were removed, relative to the results folder."""
    folder = Path(results_folder).resolve()
    files = check_result_removal(str(folder), requested)
    if not files:
        return []
    labels = [_relative_result_path(folder, path) for path in files]
    directories = {
        path.parent
        for path in files
        if path.name == "run-result.json" and path.parent.name.startswith("run-result_")
    }
    for path in files:
        if path.is_symlink() or path.is_file():
            path.unlink()
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        _remove_emptied(directory, folder)
    return labels


def _contained_files(directory: Path, root: Path) -> list[Path]:
    """Files inside directory. A symlink is the link itself, never the target."""
    found: list[Path] = []
    root = root.resolve()
    try:
        directory.resolve().relative_to(root)
    except ValueError:
        return found
    for child in sorted(directory.iterdir(), key=lambda item: item.name):
        if child.is_symlink():
            found.append(child)
            continue
        if child.is_file():
            try:
                child.resolve().relative_to(root)
            except ValueError:
                continue
            found.append(child)
        elif child.is_dir():
            found.extend(_contained_files(child, root))
    return found


def _remove_emptied(directory: Path, stop: Path) -> None:
    if directory.is_symlink() or not directory.is_dir():
        return
    if directory.resolve() == stop.resolve():
        return
    for child in list(directory.iterdir()):
        if child.is_dir() and not child.is_symlink():
            _remove_emptied(child, stop)
    try:
        directory.rmdir()
    except OSError:
        return


def _relative_result_path(folder: Path, path: Path) -> str:
    try:
        return path.relative_to(folder).as_posix()
    except ValueError:
        return path.name


def _removal_labels(path: Path) -> list[str]:
    if not path.name:
        return []
    home = path.parent.parent if path.name == "run-result.json" else path.parent
    return [_relative_result_path(home, item) for item in check_result_removal(str(home), str(path))]


def _annotate_rounds(repo: Path | None, reports_folder: Path | None, runs: list[dict], repo_id: str) -> list[dict]:
    """One row per Check directory. A Review belongs to that directory, not to identical content."""
    from studio.review.impl.items import (
        projected_run_names,
        remediation_is_sealed,
        studio_temp_dir,
        workspace_items_path,
    )

    del reports_folder
    hidden = projected_run_names(repo) if repo is not None else set()
    rows = []
    for run in runs:
        if run.get("name") in hidden:
            continue
        row = dict(run)
        path = Path(str(run.get("path") or ""))
        directory = path.parent if path.name == "run-result.json" else None
        if directory is not None and directory.name.startswith("run-result_"):
            items = directory / "review_items.json"
            document = _items_document(items)
            locked = (
                _newest_signed(directory, "review-report.json", "review-report_*.json") is not None
                or _document_is_signed(items)
                or document.get("review_locked") is True
            )
            remedy_signed = remediation_is_sealed(items)
        else:
            items = workspace_items_path(studio_temp_dir(repo), path.name) if repo is not None and path.name else None
            document = _items_document(items) if items is not None else {}
            locked = _document_is_signed(items) if items is not None else False
            locked = locked or document.get("review_locked") is True
            remedy_signed = document.get("remedy_locked") is True
        row.update(_round_state(repo_id, path, items, locked=locked, remedy_signed=remedy_signed))
        working = document if directory is not None else {}
        row["remedy_pdf_href"] = _remedy_pdf_href(repo_id, path, directory, working)
        if remedy_signed:
            counts = _remedy_full_check_counts(repo, directory, working)
            if counts:
                row["remedy_counts"] = counts
        row["files"] = _removal_labels(path)
        rows.append(row)
    return rows


def _performed_checks(results_folder: str) -> list[dict]:
    if not results_folder:
        return []
    folder = Path(results_folder)
    if not folder.is_dir():
        return []
    rows = []
    for path in reversed(_run_result_files(folder)):
        row = {
            "name": _run_stamp(path),
            "path": str(path.resolve()),
            "when": _run_when(_run_stamp(path)),
            "fail": 0,
            "pass": 0,
            "skipped": 0,
            "stale": 0,
            "missing": 0,
            "match": 0,
        }
        try:
            row.update(_outcome_counts(load_run_result(path)))
        except (ModelError, OSError, ValueError):
            row["unreadable"] = True
        rows.append(row)
    return rows


def _run_when(name: str) -> str:
    stamp = name.removeprefix("run-result_").removesuffix(".json")
    if (
        len(stamp) == 16
        and stamp.endswith("Z")
        and stamp[8] == "T"
        and stamp[:8].isdigit()
        and stamp[9:15].isdigit()
    ):
        return (
            f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]} "
            f"{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]} UTC"
        )
    return name


def _outcome_counts(result: dict) -> dict:
    counts = {"pass": 0, "fail": 0, "skipped": 0, "stale": 0, "missing": 0, "match": 0}
    for row in result.get("claims") or []:
        if not isinstance(row, dict):
            continue
        binding = row.get("binding")
        if binding in ("match", "stale", "missing"):
            counts[binding] += 1
        nested = [item for item in (row.get("checks") or []) if isinstance(item, dict)]
        statuses = [str(item.get("status") or "") for item in nested] or [str(row.get("status") or "")]
        for status in statuses:
            if status in ("pass", "fail", "skipped"):
                counts[status] += 1
    return counts


def _check_report(ws: Workspace, query: dict, editor: dict) -> tuple[dict | None, int | None]:
    path_text = str(editor.get("run_result_path") or "").strip()
    if not path_text:
        return None, None
    path = Path(path_text)
    if not path.is_file():
        return None, None
    try:
        result = load_run_result(path)
    except (ModelError, OSError, ValueError):
        return None, None
    if (query.get("exit") or [""])[0] != "":
        return result, int((query.get("exit") or ["1"])[0] or "1")
    from curbcheck.api import process_exit_code

    return result, process_exit_code(result)


def _load_compared_run(path: Path) -> dict:
    document = read_json(path)
    if isinstance(document, dict) and isinstance(document.get("run_result"), dict):
        return document["run_result"]
    return load_run_result(path)


def remediation_results_dir(repo: Path) -> Path:
    """Re-checks made while a Remedy is open. They are not Checks performed."""
    from studio.review.impl.items import studio_temp_dir

    return studio_temp_dir(repo) / "remediation-runs"


def _execute_check(repo: Path) -> tuple[dict, Path]:
    from curbcheck.api import run_and_write
    from studio.review.impl.items import record_dirty_files

    out = new_check_run_path(remediation_results_dir(repo))
    result, _code = run_and_write(repo, None, out)
    record_dirty_files(repo, out, result)
    return result, out


def regress_remediation(repo: Path, source: str, *, result: dict | None = None, out: Path | None = None) -> str:
    """Run every Check, then project the original deviations or store an outside warning."""
    from studio.review.impl.items import items_home, settle_regression

    if not source:
        return "skipped"
    path = items_home(repo, Path(source))
    if not path.is_file():
        return "skipped"
    if result is None or out is None:
        result, out = _execute_check(repo)
    stamp = out.parent.name if out.name == "run-result.json" else out.name
    document = read_json(path)
    names = [name for name in (document.get("projected_runs") or []) if isinstance(name, str)]
    if stamp not in names:
        names.append(stamp)
    from studio.review.impl.items import write_items, load_items

    write_items(path, load_items(path), marker={"projected_runs": names})
    return settle_regression(
        path,
        _load_compared_run(Path(source)),
        result,
        run_name=stamp,
        run_path=str(out.resolve()),
    )


def _project_open_remedy(repo: Path, out: Path, result: dict, return_to: str) -> None:
    """A Check while Remedy is open updates that copy and is not its own row."""
    from urllib.parse import parse_qs, urlparse

    query = parse_qs(urlparse(return_to).query)
    source = (query.get("report") or query.get("result") or [""])[0]
    if not source:
        return
    regress_remediation(repo, source, result=result, out=out)


def _run_check(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path
    from common.validate import validate_curbpack_config
    from curbcheck.api import results_dir, run_and_write
    from discovery.door import set_open_repo

    repo_id = (form.get("repo_id") or form.get("repo") or [""])[0].strip()
    if repo_id:
        set_open_repo(ws.root, repo_id)
    action = (form.get("action") or [""])[0].strip()
    if repo_id and action == "check":
        repo = _registered_repo_path(ws, repo_id)
        config = validate_curbpack_config(read_json(repo / "curbpack.json"))
        return_to = (form.get("return_to") or [""])[0].strip()
        remediation = (
            return_to.startswith("/review")
            and not return_to.startswith("//")
            and "\\" not in return_to
            and "mode=remediation" in return_to
        )
        folder = remediation_results_dir(repo) if remediation else results_dir(repo, config)
        out = new_check_run_path(folder)
        result, code = run_and_write(repo, None, out)
        from studio.review.impl.items import record_dirty_files

        record_dirty_files(repo, out, result)
        if (
            return_to.startswith("/review")
            and not return_to.startswith("//")
            and "\\" not in return_to
            and "mode=remediation" in return_to
        ):
            _project_open_remedy(repo, out, result, return_to)
            return return_to
        if return_to.startswith("/review") and not return_to.startswith("//") and "\\" not in return_to:
            return (
                f"/review?repo={quote(repo_id, safe='')}"
                f"&result={quote(str(out.resolve()), safe='')}"
            )
        return (
            f"/check?repo={quote(repo_id, safe='')}&exit={code}"
            f"&result={quote(str(out.resolve()), safe='')}"
        )
    return f"/check?repo={quote(repo_id, safe='')}" if repo_id else "/check"


def _remove_check(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path
    from common.validate import validate_curbpack_config
    from curbcheck.api import results_dir
    from discovery.door import set_open_repo

    repo_id = (form.get("repo_id") or form.get("repo") or [""])[0].strip()
    if repo_id:
        set_open_repo(ws.root, repo_id)
    if not repo_id:
        return "/check"
    repo = _registered_repo_path(ws, repo_id)
    config = validate_curbpack_config(read_json(repo / "curbpack.json"))
    requested = (form.get("result") or [""])[0]
    if remove_check_result(str(results_dir(repo, config)), requested):
        return f"/check?repo={quote(repo_id, safe='')}&removed=1"
    return f"/check?repo={quote(repo_id, safe='')}&remove=no"
