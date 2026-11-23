"""review_item for one Check: provenance, reuse, workspace, and history.

The object is defined in docs/reference/studio-internal.md. A review and a
remediation round each keep their own file. Signing writes a third copy next
to the Review Report.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from checks.run import _git_run
from common.canonical import canonical_json, version_digest
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.signing import sign_object
from discovery.studio import load_user_studio

BINDING_CHECK = {"check": "requirement_binding", "args": {}}
_DECISIONS = {"pass", "accepted", "not_assessed", "must_fix"}


def check_digest(check: str, args: dict) -> str:
    payload = canonical_json({"args": args, "check": check}).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def binding_digest() -> str:
    return check_digest(BINDING_CHECK["check"], BINDING_CHECK["args"])


def studio_temp_dir(repo: Path) -> Path:
    """paths.temp_dir from the user studio file, else .curbpack/tmp under the product repo."""
    relative = ".curbpack/tmp"
    loaded = load_user_studio()
    if loaded is not None:
        relative = str(loaded["paths"]["temp_dir"])
    path = Path(relative)
    if path.is_absolute():
        return path
    return Path(repo) / path


def workspace_dir(temp_dir: Path, source_name: str) -> Path:
    stem = Path(source_name).name
    if stem.endswith(".json"):
        stem = stem[: -len(".json")]
    return Path(temp_dir) / stem


def workspace_items_path(temp_dir: Path, source_name: str) -> Path:
    return workspace_dir(temp_dir, source_name) / "review_items.json"


def files_sidecar_path(temp_dir: Path, run_name: str) -> Path:
    stem = Path(run_name).name
    if stem.endswith(".json"):
        stem = stem[: -len(".json")]
    return Path(temp_dir) / f"{stem}.files.json"


def relevant_paths(args: dict) -> list[str]:
    found: list[str] = []
    single = args.get("path")
    if isinstance(single, str) and single and single not in found:
        found.append(single)
    listed = args.get("paths")
    if isinstance(listed, list):
        for item in listed:
            if isinstance(item, str) and item and item not in found:
                found.append(item)
    return found


def _file_record(repo: Path, relative: str) -> dict | None:
    path = Path(repo) / relative
    if not path.is_file():
        return None
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"path": relative, "size": stat.st_size, "mtime": mtime}


def capture_run_files(repo: Path, run: dict) -> list[dict]:
    """Path, size, and mtime for each Check, taken from the worktree now."""
    rows: list[dict] = []
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            files = [record for path in relevant_paths(args) if (record := _file_record(repo, path))]
            rows.append(
                {
                    "claim_id": claim_id,
                    "check_digest": check_digest(str(check.get("check") or ""), args),
                    "files": files,
                }
            )
    return rows


def record_dirty_files(repo: Path, run_path: Path, run: dict) -> Path | None:
    """Write the sidecar once, while the worktree is still the one that ran.

    A later edit of the worktree does not rewrite an existing sidecar.
    curbcheck without Studio does not call this.
    """
    if run.get("worktree") != "dirty":
        return None
    target = files_sidecar_path(studio_temp_dir(repo), run_path.name)
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, {"checks": capture_run_files(repo, run)})
    return target


def load_files_sidecar(temp_dir: Path, run_name: str) -> dict[tuple, list[dict]]:
    path = files_sidecar_path(temp_dir, run_name)
    if not path.is_file():
        return {}
    document = read_json(path)
    found: dict[tuple, list[dict]] = {}
    for row in document.get("checks") or []:
        if not isinstance(row, dict):
            continue
        files = [item for item in row.get("files") or [] if isinstance(item, dict)]
        found[(row.get("claim_id"), row.get("check_digest"))] = files
    return found


def _provenance(run: dict, claim: dict, files: list[dict] | None) -> dict:
    provenance: dict = {}
    digest = claim.get("requirement_digest")
    if isinstance(digest, str) and digest:
        provenance["requirement_digest"] = digest
    commit = run.get("commit")
    if isinstance(commit, str) and commit:
        provenance["git_commit"] = commit
    worktree = run.get("worktree")
    if worktree == "dirty":
        provenance["dirty_git"] = True
    elif worktree == "clean":
        provenance["dirty_git"] = False
    if files:
        provenance["files"] = files
    return provenance


def _item(claim_id: str, digest: str, decision: str, provenance: dict) -> dict:
    item = {
        "key": {"claim_id": claim_id, "check_digest": digest},
        "decision": decision,
    }
    if provenance:
        item["provenance"] = provenance
    return item


def items_from_run(run: dict, files_by_check: dict[tuple, list[dict]] | None = None) -> list[dict]:
    """Decisions from the run. History is empty. pass where the Check passed, otherwise not_assessed."""
    files_by_check = files_by_check or {}
    items: list[dict] = []
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict) or not isinstance(claim.get("id"), str):
            continue
        claim_id = claim["id"]
        binding = claim.get("binding")
        if binding in {"match", "stale", "missing"}:
            digest = binding_digest()
            decision = "pass" if binding == "match" else "not_assessed"
            items.append(
                _item(claim_id, digest, decision, _provenance(run, claim, files_by_check.get((claim_id, digest))))
            )
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            digest = check_digest(str(check.get("check") or ""), args)
            decision = "pass" if check.get("status") == "pass" else "not_assessed"
            items.append(
                _item(claim_id, digest, decision, _provenance(run, claim, files_by_check.get((claim_id, digest))))
            )
    return items


def item_key(item: dict) -> tuple:
    key = item.get("key") if isinstance(item.get("key"), dict) else {}
    return (key.get("claim_id"), key.get("check_digest"))


def merge_items(existing: list[dict], new_items: list[dict]) -> list[dict]:
    """Keep the existing item when the key matches. Add a Check that exists only on the run."""
    kept = {item_key(item): item for item in existing}
    merged: list[dict] = []
    seen: set[tuple] = set()
    for item in new_items:
        key = item_key(item)
        merged.append(kept[key] if key in kept else item)
        seen.add(key)
    for item in existing:
        key = item_key(item)
        if key not in seen:
            merged.append(item)
            seen.add(key)
    return merged


def load_items(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    document = read_json(path)
    rows = document.get("items") if isinstance(document, dict) else None
    if not isinstance(rows, list):
        raise ModelError("review_items", "items", "a list")
    return [row for row in rows if isinstance(row, dict)]


def write_items(path: Path, items: list[dict], *, signed: dict | None = None, marker: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kept: dict = {}
    if path.is_file() and marker is None:
        current = read_json(path)
        if isinstance(current, dict):
            for key in ("history_from", "remedy"):
                if key in current:
                    kept[key] = current[key]
    if marker:
        kept.update(marker)
    document: dict = {"items": items, **kept}
    if signed is not None:
        document["signed"] = signed
    write_json(path, document)


def open_review_items(
    path: Path,
    run: dict,
    *,
    files_by_check: dict[tuple, list[dict]] | None = None,
    choice: str = "",
) -> tuple[list[dict], str]:
    """Return items and the question state: ready, ask, continued, or restarted.

    A missing file is written from the run. An existing file always asks
    continue or start over until the caller passes that choice.
    """
    new_items = items_from_run(run, files_by_check)
    if not path.is_file():
        write_items(path, new_items)
        return new_items, "ready"
    if choice == "continue":
        merged = merge_items(load_items(path), new_items)
        write_items(path, merged)
        return merged, "continued"
    if choice == "start":
        write_items(path, new_items)
        return new_items, "restarted"
    return load_items(path), "ask"


def same_file_metadata(left: list[dict] | None, right: list[dict] | None) -> bool:
    if not left or not right:
        return False
    def rows(items: list[dict]) -> dict[str, tuple]:
        return {
            str(item.get("path")): (item.get("size"), item.get("mtime"))
            for item in items
            if isinstance(item, dict) and item.get("path")
        }
    return rows(left) == rows(right)


def _blob(repo: Path, commit: str, relative: str) -> str | None:
    proc = _git_run(repo, "rev-parse", f"{commit}:{relative}")
    if proc is None or proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _clean_same(repo: Path, previous: dict, current: dict, paths: list[str]) -> bool:
    left = str((previous.get("provenance") or {}).get("git_commit") or "")
    right = str((current.get("provenance") or {}).get("git_commit") or "")
    if not left or not right:
        return False
    if left == right:
        return True
    if not paths:
        return False
    for relative in paths:
        before = _blob(repo, left, relative)
        after = _blob(repo, right, relative)
        if before is None or after is None or before != after:
            return False
    return True


def decision_reusable(previous: dict, current: dict, *, repo: Path, paths: list[str]) -> bool:
    """True when the earlier decision may fill the new item. History is not part of this."""
    if item_key(previous) != item_key(current):
        return False
    left = previous.get("provenance") if isinstance(previous.get("provenance"), dict) else {}
    right = current.get("provenance") if isinstance(current.get("provenance"), dict) else {}
    if not left.get("requirement_digest") or left.get("requirement_digest") != right.get("requirement_digest"):
        return False
    if "dirty_git" not in left or "dirty_git" not in right:
        return False
    if left.get("dirty_git") or right.get("dirty_git"):
        return same_file_metadata(left.get("files"), right.get("files"))
    return _clean_same(repo, previous, current, paths)


def apply_reused_decision(current: dict, previous: dict) -> dict:
    """Copy the decision onto the new item. Leave remediation_history untouched."""
    updated = dict(current)
    updated["decision"] = previous.get("decision")
    for field in ("priority", "comment", "assessed_at"):
        if field in previous and previous.get("decision") in {"accepted", "must_fix"}:
            updated[field] = previous[field]
        else:
            updated.pop(field, None)
    if "remediation_history" in current:
        updated["remediation_history"] = current["remediation_history"]
    else:
        updated.pop("remediation_history", None)
    return updated


def history_to_show(source_items: list[dict], item: dict) -> list[dict]:
    """History written by remediation, matched by key. It does not set decision."""
    wanted = item_key(item)
    for source in source_items:
        if item_key(source) == wanted:
            history = source.get("remediation_history")
            if isinstance(history, list):
                return [entry for entry in history if isinstance(entry, dict)]
    return []


def append_history(
    item: dict,
    *,
    remediation: str,
    action: str | None = None,
    transition: str | None = None,
    old_check_digest: str | None = None,
    date: str | None = None,
) -> dict:
    if not isinstance(remediation, str) or not remediation.strip():
        raise ModelError("review_item", "remediation", "non-empty text")
    entry: dict = {
        "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "remediation": remediation.strip(),
    }
    if action:
        entry["action"] = action
    if transition:
        entry["transition"] = transition
    if old_check_digest:
        entry["old_check_digest"] = old_check_digest
    updated = dict(item)
    history = [row for row in (item.get("remediation_history") or []) if isinstance(row, dict)]
    history.append(entry)
    updated["remediation_history"] = history
    return updated


def record_retire(item: dict, *, remediation: str, date: str | None = None) -> dict:
    """A Retire post names the action. A free-text comment does not."""
    return append_history(item, remediation=remediation, action="retire", date=date)


def retarget_check(
    item: dict,
    check: str,
    args: dict,
    *,
    remediation: str,
    transition: str | None = None,
    date: str | None = None,
) -> dict:
    """Keep the item. Store the old digest and point the key at the new configuration."""
    old = str((item.get("key") or {}).get("check_digest") or "")
    updated = append_history(
        item,
        remediation=remediation,
        transition=transition,
        old_check_digest=old,
        date=date,
    )
    key = dict(updated.get("key") or {})
    key["check_digest"] = check_digest(check, args)
    updated["key"] = key
    return updated


def apply_recheck(item: dict, status: str, *, remediation: str, date: str | None = None) -> dict:
    """A passing re-check sets the recommendation to pass. A failure leaves it."""
    if status != "pass":
        return append_history(item, remediation=remediation, date=date)
    previous = str(item.get("decision") or "")
    updated = append_history(
        item,
        remediation=remediation,
        transition=f"{previous} -> pass" if previous and previous != "pass" else None,
        date=date,
    )
    updated["decision"] = "pass"
    return updated


def is_retired(item: dict) -> bool:
    return any(
        isinstance(entry, dict) and entry.get("action") == "retire"
        for entry in item.get("remediation_history") or []
    )


def retired_absences(remedy_items: list[dict], run: dict) -> list[dict]:
    """A Check or Claim missing from the new run is retired only with action retire."""
    present_claims = {
        claim.get("id")
        for claim in run.get("claims") or []
        if isinstance(claim, dict)
    }
    present_checks: set[tuple] = set()
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        binding = claim.get("binding")
        if binding in {"match", "stale", "missing"}:
            present_checks.add((claim_id, binding_digest()))
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            present_checks.add((claim_id, check_digest(str(check.get("check") or ""), args)))
    missing: list[dict] = []
    claims_with_retire = {item_key(item)[0] for item in remedy_items if is_retired(item)}
    for item in remedy_items:
        claim_id, digest = item_key(item)
        claim_gone = claim_id not in present_claims
        check_gone = (claim_id, digest) not in present_checks
        if claim_gone and claim_id in claims_with_retire:
            missing.append(item)
        elif check_gone and is_retired(item):
            missing.append(item)
    return missing


def assessments_from_decisions(items: list[dict], run: dict) -> list[dict]:
    """Signed decisions are what the report records. pass and not_assessed add no assessment."""
    index_by_key: dict[tuple, dict] = {}
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict) or not isinstance(check.get("index"), int):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            index_by_key[(claim.get("id"), check_digest(str(check.get("check") or ""), args))] = {
                "claim_id": claim.get("id"),
                "claim_digest": claim.get("digest"),
                "index": check.get("index"),
                "status": check.get("status"),
            }
    assessments: list[dict] = []
    for item in items:
        decision = item.get("decision")
        if decision not in {"must_fix", "accepted"}:
            continue
        located = index_by_key.get(item_key(item))
        if located is None:
            continue
        text = item.get("comment")
        text = text.strip() if isinstance(text, str) else ""
        if decision == "accepted" and located.get("status") == "fail" and not text:
            raise ModelError("review_item", "comment", "non-empty text")
        assessments.append(
            {
                "kind": "check",
                "claim_id": located["claim_id"],
                "claim_digest": located["claim_digest"],
                "index": located["index"],
                "disposition": "must_fix" if decision == "must_fix" else "accept",
                "text": text,
            }
        )
    return assessments


def signed_decision(items_document: dict, claim_id: str, digest: str) -> str | None:
    """The signed file's decision is what reporting uses."""
    if not isinstance(items_document.get("signed"), dict):
        return None
    for item in items_document.get("items") or []:
        if isinstance(item, dict) and item_key(item) == (claim_id, digest):
            decision = item.get("decision")
            if decision in _DECISIONS:
                return str(decision)
    return None


def sign_items_document(
    items: list[dict],
    *,
    name: str,
    private_key: bytes,
    at: str,
) -> tuple[dict, str]:
    """Sign the items object. Return the sealed document and the version digest the report stores."""
    document = {"items": items}
    digest = version_digest(document)
    sealed = sign_object(document, name=name, private_key=private_key, at=at)
    return sealed, digest


def paths_for_item(run: dict, item: dict) -> list[str]:
    """Relevant paths: provenance.files when present, otherwise the Check arguments."""
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    files = provenance.get("files")
    if isinstance(files, list) and files:
        return [str(row.get("path")) for row in files if isinstance(row, dict) and row.get("path")]
    claim_id, digest = item_key(item)
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict) or claim.get("id") != claim_id:
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            if check_digest(str(check.get("check") or ""), args) == digest:
                return relevant_paths(args)
    return []


def with_history(items: list[dict], source_items: list[dict]) -> list[dict]:
    """Attach remediation history for display. The attached history does not set decision."""
    shown = []
    for item in items:
        history = history_to_show(source_items, item)
        if not history:
            shown.append(item)
            continue
        copy = dict(item)
        copy["remediation_history"] = history
        shown.append(copy)
    return shown


def reuse_decisions(repo: Path, run: dict, items: list[dict], source_items: list[dict]) -> list[dict]:
    """Fill decision from a matching source item. History stays on the source."""
    by_key = {item_key(item): item for item in source_items}
    reused = []
    for item in items:
        previous = by_key.get(item_key(item))
        if previous and decision_reusable(previous, item, repo=repo, paths=paths_for_item(run, item)):
            reused.append(apply_reused_decision(item, previous))
        else:
            reused.append(item)
    return reused


def apply_assessment_decisions(items: list[dict], assessments: list[dict], run: dict) -> list[dict]:
    """Copy a saved review verdict onto the matching item. Retire is not a verdict."""
    located: dict[tuple, tuple] = {}
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict) or not isinstance(check.get("index"), int):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            located[(claim.get("id"), check.get("index"))] = (
                claim.get("id"),
                check_digest(str(check.get("check") or ""), args),
                check.get("status"),
            )
    updated = [dict(item) for item in items]
    by_key = {item_key(item): item for item in updated}
    for assessment in assessments:
        if not isinstance(assessment, dict) or assessment.get("kind") != "check":
            continue
        found = located.get((assessment.get("claim_id"), assessment.get("index")))
        if found is None:
            continue
        item = by_key.get((found[0], found[1]))
        if item is None:
            continue
        disposition = assessment.get("disposition")
        if disposition == "must_fix":
            item["decision"] = "must_fix"
        elif disposition == "accept":
            item["decision"] = "accepted"
        elif disposition in {"", "pass"}:
            item["decision"] = "pass" if found[2] == "pass" else "not_assessed"
        else:
            continue
        text = assessment.get("text")
        if item["decision"] in {"must_fix", "accepted"} and isinstance(text, str) and text.strip():
            item["comment"] = text.strip()
    return updated


def status_for_item(claim_result: dict, item: dict) -> str | None:
    """The re-check status for this item. None when the claim result has no such Check."""
    _claim_id, digest = item_key(item)
    for check in claim_result.get("checks") or []:
        if not isinstance(check, dict):
            continue
        args = check.get("args") if isinstance(check.get("args"), dict) else {}
        if check_digest(str(check.get("check") or ""), args) == digest:
            status = check.get("status")
            return str(status) if isinstance(status, str) else None
    return None


def recheck_item(repo: Path, claims_dir: Path, items: list[dict], claim_id: str, digest: str, text: str) -> list[dict]:
    """Run the Claim and merge that Check's status onto the same item."""
    from checks.run import run_claim
    from common.store import load_claim

    claim = load_claim(Path(claims_dir) / f"{claim_id}.json")
    result = run_claim(repo, claim)
    updated = []
    found = False
    for item in items:
        key = item.get("key") if isinstance(item.get("key"), dict) else {}
        if key.get("claim_id") == claim_id and key.get("check_digest") == digest:
            found = True
            status = status_for_item(result, item)
            if status is not None:
                item = apply_recheck(item, status, remediation=text)
        updated.append(item)
    if not found:
        raise ModelError("review_item", "check_digest", "an item in this workspace")
    return updated


def latest_ready_remedy(temp_dir: Path, reports_dir: Path, run: dict) -> tuple[str, list[dict]] | None:
    """The newest Remedy Report whose Review Report is not this Run Result."""
    from review.compile import load_report, same_run

    if not Path(temp_dir).is_dir():
        return None
    found: list[tuple[str, list[dict]]] = []
    for path in sorted(Path(temp_dir).glob("review-report_*/review_items.json")):
        try:
            document = read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict) or document.get("remedy") is not True:
            continue
        stem = path.parent.name
        report_path = Path(reports_dir) / f"{stem}.json"
        if report_path.is_file():
            try:
                report = load_report(report_path)
            except (ModelError, ValueError):
                continue
            if same_run(report, run):
                continue
        found.append((stem, load_items(path)))
    if not found:
        return None
    return found[-1]


def _workspace_from_return(repo: Path, return_to: str) -> Path | None:
    from urllib.parse import parse_qs, urlparse

    if "mode=remediation" not in str(return_to or ""):
        return None
    query = parse_qs(urlparse(return_to).query)
    source = (query.get("report") or query.get("result") or [""])[0]
    if not source:
        return None
    path = workspace_items_path(studio_temp_dir(repo), Path(source).name)
    if not path.is_file():
        return None
    return path


def record_check_change(
    repo: Path,
    return_to: str,
    claim_id: str,
    old_check: str,
    old_args: dict,
    new_check: str,
    new_args: dict,
) -> None:
    """A changed Check configuration keeps the item and records old_check_digest."""
    path = _workspace_from_return(repo, return_to)
    if path is None:
        return
    old_digest = check_digest(old_check, old_args if isinstance(old_args, dict) else {})
    new_digest = check_digest(new_check, new_args if isinstance(new_args, dict) else {})
    if old_digest == new_digest:
        return
    updated = []
    for item in load_items(path):
        if item_key(item) == (claim_id, old_digest):
            item = retarget_check(
                item,
                new_check,
                new_args if isinstance(new_args, dict) else {},
                remediation="Check configuration updated.",
            )
        updated.append(item)
    write_items(path, updated)


def record_rebind(repo: Path, return_to: str, claim_id: str) -> None:
    """Rebind records one history entry on this Claim."""
    path = _workspace_from_return(repo, return_to)
    if path is None:
        return
    items = load_items(path)
    target = None
    for item in items:
        if item_key(item) == (claim_id, binding_digest()):
            target = item_key(item)
            break
    if target is None:
        for item in items:
            if item_key(item)[0] == claim_id:
                target = item_key(item)
                break
    if target is None:
        return
    updated = []
    for item in items:
        if item_key(item) == target:
            item = append_history(item, remediation="Rebound the Claim.")
        updated.append(item)
    write_items(path, updated)


def retire_live_check(claims_dir: Path, claim_id: str, digest: str) -> None:
    """Remove the Check, or the Claim when none remain. Uses the existing Claim writers."""
    from common.store import load_claim, save_claim
    from studio.claim.impl.bind import rebind, retire_claim

    if digest == binding_digest():
        retire_claim(claims_dir, claim_id)
        return
    path = Path(claims_dir) / f"{claim_id}.json"
    if not path.is_file():
        raise ModelError(f"claim {claim_id}", "id", "an existing claim file")
    claim = load_claim(path)
    kept = []
    removed = False
    for check in claim.get("checks") or []:
        if not isinstance(check, dict):
            continue
        args = check.get("args") if isinstance(check.get("args"), dict) else {}
        if not removed and check_digest(str(check.get("check") or ""), args) == digest:
            removed = True
            continue
        kept.append(check)
    if not removed:
        raise ModelError("review_item", "check_digest", "a Check on this Claim")
    if not kept:
        retire_claim(claims_dir, claim_id)
        return
    save_claim(claims_dir, rebind(claim, checks=kept))


def report_items_path(report_path: Path) -> Path:
    name = report_path.name
    if name.endswith(".json"):
        name = name[: -len(".json")] + ".items.json"
    else:
        name = name + ".items.json"
    return report_path.with_name(name)
