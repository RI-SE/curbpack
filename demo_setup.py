"""Create the Annex VII.3 sample workspace. Does not sign anything."""

from __future__ import annotations

import subprocess
from pathlib import Path

from common.errors import ModelError
from common.jsonio import write_json
from common.store import save_pack, save_requirement
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.editing import apply_edits


def prepare_demo(root: Path) -> None:
    pack_dir = root / "packs" / "cra-baseline"
    repo = root / "product"
    if (pack_dir / "CRA-ANNEX-VII-RISK.json").exists() or (repo / "curbpack.json").exists():
        raise ModelError("demo", "workspace", "an empty workspace; this one already has a pack or product")
    requirement = extract_annex_vii_risk()
    source = dict(requirement["source"])
    source["edition"] = "2024-11-20"
    requirement = apply_edits(
        requirement,
        {
            "source": source,
            "remediation_hint": "The file should be the product's own assessment, not a placeholder.",
        },
    )
    pack = draft_pack()
    save_pack(pack_dir, pack)
    save_requirement(pack_dir, requirement)
    repo.mkdir(parents=True)
    hints = created_curbpack()["search_hints"]
    hints["exclude_path_globs"] = ["**/node_modules/**", "*FUTURE_*"]
    hints["prefer_path_globs"] = ["**/README*", "**/docs/**"]
    write_json(repo / "curbpack.json", created_curbpack(packs=["cra-baseline"], search_hints=hints))
    version_dir = repo / "curbpack" / "packs" / "cra-baseline" / pack["version"]
    save_pack(version_dir, pack)
    save_requirement(version_dir, requirement)
    (repo / "README.md").write_text("# sample-product\n\nA demonstration product.\n", encoding="utf-8")
    (repo / "marketing.md").write_text("The brochure mentions cybersecurity risk.\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "threat-model-draft.md").write_text("Draft threat notes.\n", encoding="utf-8")
    (repo / "FUTURE_plan.md").write_text("risk assessment planned later\n", encoding="utf-8")
    (repo / "node_modules" / "pkg").mkdir(parents=True)
    (repo / "node_modules" / "pkg" / "README.md").write_text("cybersecurity risk\n", encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=poc2@example.com", "-c", "user.name=PoC2", "commit", "-m", "sample product")
    save_repos(root, add_repo(root, load_repos(root), name="sample-product", path=str(repo)))
    set_open_repo(root, "sample-product")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
