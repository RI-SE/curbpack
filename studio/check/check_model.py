"""Check view-model and POST. The URL stays on the old server."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from curbcheck.api import _pack_version_dir, packs_dir
from common.errors import ModelError
from common.jsonio import read_json
from common.store import load_run_result

if TYPE_CHECKING:
    from app.server import Workspace


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
        if path.is_file() and path.name.startswith("run-result_") and path.name.endswith(".json"):
            return str(path)
        return ""
    dated = sorted(folder.glob("run-result_*.json"))
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
    values = {key: "" for key in ("packs_dir", "claims_dir", "results_dir", "reports_dir")}
    if repo_id:
        repo = _registered_repo_path(ws, repo_id)
        config_path = repo / "curbpack.json"
        if config_path.is_file():
            from common.validate import validate_curbpack_config

            config = validate_curbpack_config(read_json(config_path))
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
        "runs": _performed_checks(results_folder),
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


def _performed_checks(results_folder: str) -> list[dict]:
    if not results_folder:
        return []
    folder = Path(results_folder)
    if not folder.is_dir():
        return []
    rows = []
    for path in sorted(folder.glob("run-result_*.json")):
        if not path.is_file():
            continue
        row = {
            "name": path.name,
            "path": str(path.resolve()),
            "when": _run_when(path.name),
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
    rows.reverse()
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


def _run_check(ws: Workspace, form: dict) -> str:
    from urllib.parse import quote

    from app.server import _registered_repo_path
    from common.validate import validate_curbpack_config
    from curbcheck.api import new_run_result_path, results_dir, run_and_write
    from discovery.door import set_open_repo

    repo_id = (form.get("repo_id") or form.get("repo") or [""])[0].strip()
    if repo_id:
        set_open_repo(ws.root, repo_id)
    action = (form.get("action") or [""])[0].strip()
    if repo_id and action == "check":
        repo = _registered_repo_path(ws, repo_id)
        config = validate_curbpack_config(read_json(repo / "curbpack.json"))
        out = new_run_result_path(results_dir(repo, config))
        result, code = run_and_write(repo, None, out)
        return (
            f"/check?repo={quote(repo_id, safe='')}&exit={code}"
            f"&result={quote(str(out.resolve()), safe='')}"
        )
    return f"/check?repo={quote(repo_id, safe='')}" if repo_id else "/check"
