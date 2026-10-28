"""Handlers for the Check programs this build runs."""

from __future__ import annotations

from pathlib import Path

from checks.filecheck import run_contents, run_exist
from checks.gitcheck import run_git_author, run_git_fresh
from checks.nodecheck import run_dep_ban

_NODE_DEP_BAN_IDS = frozenset({"dep_ban", "npm_dep_ban", "manifest_dep_ban"})


def exist_handle(repo: Path, check: str, args: dict) -> dict:
    if check != "exist":
        return {"status": "fail", "detail": f"check {check!r} is not a subcommand of curbcheck-exist"}
    return run_exist(repo, args)


def contents_handle(repo: Path, check: str, args: dict) -> dict:
    if check != "contents":
        return {"status": "fail", "detail": f"check {check!r} is not a subcommand of curbcheck-contents"}
    return run_contents(repo, args)


def git_handle(repo: Path, check: str, args: dict) -> dict:
    if check == "git_fresh":
        return run_git_fresh(repo, args)
    if check == "git_author":
        return run_git_author(repo, args)
    return {"status": "fail", "detail": f"check {check!r} is not implemented"}


def node_handle(repo: Path, check: str, args: dict) -> dict:
    if check in _NODE_DEP_BAN_IDS:
        return run_dep_ban(repo, args)
    return {"status": "fail", "detail": f"check {check!r} is not a subcommand of curbcheck-node"}
