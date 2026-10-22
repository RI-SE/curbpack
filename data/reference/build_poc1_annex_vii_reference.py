"""Convert the PoC1 Annex VII maps into unsigned Packs v2 Requirements.

Reads the human-reviewed PoC1 YAML and the cra-xml Formex provisions.
Does not call a model. Requirement ids are reference labels, not a product
naming convention. PoC1 claim slugs are not copied.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POC2 = ROOT / "poc2"
sys.path.insert(0, str(POC2))

from common.store import load_pack_directory, save_pack, save_requirement  # noqa: E402
from common.validate import validate_requirement  # noqa: E402
from requirements.extract.adapter import ADAPTERS, load_adapter, section_provisions  # noqa: E402

OUT = POC2 / "data" / "reference" / "poc1-annex-vii-unsigned"
CLAIMS = ROOT / "poc/components/transform/adapters/cra/maps/claims.yml"
SEARCH = ROOT / "poc/components/transform/adapters/cra/maps/search.yml"
GOLD = ROOT / "poc/data/in/ctam_cra_requirements_search.yml"
EXPECTED_LOCI = [
    "1(a)",
    "1(b)",
    "1(c)",
    "1(d)",
    "2(a)",
    "2(b)",
    "2(c)",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
]


def _yaml_json(path: Path) -> dict:
    raw = subprocess.check_output(
        ["ruby", "-ryaml", "-rjson", "-e", "puts JSON.generate(YAML.load_file(ARGV[0]))", str(path)],
        text=True,
    )
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise SystemExit(f"{path} did not load as a mapping")
    return loaded


def _reference_id(locus: str) -> str:
    token = locus.upper().replace("(", "").replace(")", "")
    return f"POC1-REF-VII-{token}"


def _norm(text: str) -> str:
    return " ".join(text.split())


def _hints(search: dict) -> dict:
    hints: dict = {}
    for field in ("concepts", "path_hints", "expected_evidence"):
        values = search.get(field)
        if not isinstance(values, list) or not values:
            raise SystemExit(f"search for a locus is missing {field}")
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise SystemExit(f"search {field} is not a list of strings")
        hints[field] = list(values)
    sources = search.get("sources")
    if sources is not None:
        if not isinstance(sources, list) or not sources:
            raise SystemExit("search sources is not a non-empty list")
        hints["sources"] = [{"source": item} for item in sources]
    return hints


def main() -> None:
    claims = _yaml_json(CLAIMS)["by_locus"]
    search = _yaml_json(SEARCH)["by_locus"]
    gold = _yaml_json(GOLD)
    adapter_dir = ADAPTERS / "cra-xml"
    adapter = load_adapter(adapter_dir / "adapter.json")
    extracted = section_provisions(adapter_dir, adapter, "VII")
    provisions = extracted["provisions"]
    loci = [item["locus"] for item in provisions]
    if loci != EXPECTED_LOCI:
        raise SystemExit(f"adapter loci {loci} != {EXPECTED_LOCI}")
    if set(claims) != set(EXPECTED_LOCI) or set(search) != set(EXPECTED_LOCI):
        raise SystemExit("claims.yml or search.yml locus set does not match the adapter")

    gold_by_locus = {}
    for row in gold["requirements"]:
        locus = row["locus"]
        if locus in gold_by_locus:
            raise SystemExit(f"duplicate gold locus {locus}")
        gold_by_locus[locus] = row
    if list(gold_by_locus) != EXPECTED_LOCI:
        raise SystemExit(f"gold loci {list(gold_by_locus)} != {EXPECTED_LOCI}")

    losses = []
    for locus in EXPECTED_LOCI:
        claim = claims[locus]
        gold_row = gold_by_locus[locus]
        if claim.get("id") != gold_row.get("id") or claim.get("claim") != gold_row.get("claim"):
            raise SystemExit(f"{locus}: claims.yml and gold id/claim differ")
        if claim.get("note") != gold_row.get("note"):
            raise SystemExit(f"{locus}: claims.yml and gold note differ")
        gold_search = gold_row["search"]
        mapped = search[locus]
        for key in ("concepts", "path_hints", "expected_evidence", "sources"):
            if mapped.get(key) != gold_search.get(key):
                raise SystemExit(f"{locus}: search.yml {key} differs from the gold package")
        official = next(item["law_text"] for item in provisions if item["locus"] == locus)
        if _norm(official) != _norm(gold_row["law_text"]):
            losses.append(
                {
                    "locus": locus,
                    "kind": "law_text wording",
                    "gold": _norm(gold_row["law_text"]),
                    "official": _norm(official),
                }
            )

    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    pack = {
        "id": "poc1-annex-vii-reference",
        "name": "PoC1 Annex VII reference",
        "version": "0.0.0-reference",
        "description": (
            "Agent-converted comparison reference from the PoC1 Annex VII maps "
            "and cra-xml Formex provisions. Not an independently certified legal "
            "gold standard. Unsigned. Ids are reference labels, not the product naming convention."
        ),
    }
    save_pack(OUT, pack)

    written = []
    for item in provisions:
        locus = item["locus"]
        claim = claims[locus]
        requirement = {
            "id": _reference_id(locus),
            "pack_id": pack["id"],
            "source": dict(adapter["source"]),
            "references": [
                {
                    "nr": 1,
                    "locator": f"VII.{locus}",
                    "law_text": item["law_text"],
                }
            ],
            "discovery_hints": _hints(search[locus]),
        }
        if "note" in claim:
            requirement["note"] = claim["note"]
        checked = validate_requirement(requirement, published=False)
        if "signed" in checked or "origin" in checked or "edition" in checked["source"]:
            raise SystemExit("reference requirement must stay unsigned and without edition")
        save_requirement(OUT, checked)
        written.append(checked["id"])

    loaded_pack, loaded = load_pack_directory(OUT)
    if loaded_pack["id"] != pack["id"] or len(loaded) != 13:
        raise SystemExit("reload failed")
    loaded_loci = []
    for requirement in loaded:
        validate_requirement(requirement, published=False)
        locator = requirement["references"][0]["locator"]
        if not locator.startswith("VII."):
            raise SystemExit(f"bad locator {locator}")
        loaded_loci.append(locator.removeprefix("VII."))
    if loaded_loci != EXPECTED_LOCI:
        raise SystemExit(f"reloaded loci {loaded_loci}")

    summary = {
        "directory": str(OUT.relative_to(ROOT)),
        "loci": EXPECTED_LOCI,
        "ids": written,
        "source_file": extracted["file"],
        "wording_differences": losses,
        "claim_slugs_not_copied": {locus: claims[locus]["claim"] for locus in EXPECTED_LOCI},
        "poc1_ids_not_used": {locus: claims[locus]["id"] for locus in EXPECTED_LOCI},
        "requirements_without_sources": [
            locus for locus in EXPECTED_LOCI if "sources" not in search[locus]
        ],
        "gold_default_sources_not_copied": gold["defaults"]["sources"],
        "gold_hunt_globs_not_copied": {
            "exclude_path_globs": gold["defaults"]["exclude_path_globs"],
            "prefer_path_globs": gold["defaults"]["prefer_path_globs"],
        },
        "gold_source_url_not_copied": gold["source_url"],
        "adapter_source_url": adapter["source"]["url"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
