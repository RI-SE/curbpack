"""Readings from the sample workspace. No HTML."""

from __future__ import annotations

from pathlib import Path

from common.errors import ModelError
from common.keystore import trust_store
from common.signing import read_signature
from checks.run import process_exit_code
from common.store import load_claims, load_requirement, load_run_result
from requirements.editing import read_pack_seal
from review.compile import durable_report_path, load_report, read_report_signature, same_run


def snapshot(root: Path) -> dict:
    pack_dir = root / "packs" / "cra-baseline"
    repo = root / "product"
    requirement_path = pack_dir / "CRA-ANNEX-VII-RISK.json"
    info = {
        "requirement": None,
        "requirement_reading": None,
        "claims": [],
        "run_result": None,
        "run_exit": None,
        "report": None,
        "report_reading": None,
        "report_error": None,
        "same_run": None,
        "pack_reading": None,
    }
    trust = trust_store(root / "keys")
    if (pack_dir / "pack.json").is_file():
        info["pack_reading"] = read_pack_seal(pack_dir, trust)
    if requirement_path.is_file():
        requirement = load_requirement(requirement_path)
        info["requirement"] = requirement
        info["requirement_reading"] = read_signature(requirement, trust, what="requirement")
    if (repo / "claims").is_dir():
        info["claims"] = load_claims(repo / "claims")
    run_path = repo / ".curbpack" / "run-result.json"
    if run_path.is_file():
        result = load_run_result(run_path)
        info["run_result"] = result
        info["run_exit"] = process_exit_code(result)
    report_path = durable_report_path(repo)
    if report_path.is_file():
        try:
            report = load_report(report_path)
        except (ModelError, ValueError, OSError) as exc:
            info["report_error"] = str(exc)
        else:
            info["report"] = report
            info["report_reading"] = read_report_signature(
                report,
                trust,
                repo=repo,
                relative="docs/reports/review-report.json",
            )
            if isinstance(info["run_result"], dict):
                info["same_run"] = same_run(report, info["run_result"])
    return info
