"""Requirements catalog, extract job, and editor go through HTTP."""

from __future__ import annotations

import json
import re
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from app.server import Workspace, make_handler
from common.canonical import version_digest
from common.jsonio import write_json
from common.store import save_pack
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack
from common.errors import ModelError
from requirements.editing import apply_edits, assign_reference_numbers, save_working_requirement
from requirements.extract.adapter import ADAPTERS, load_adapter
from requirements.workspace import extract_section, list_working_copies, load_working_copy, selected_copy


def _proposals() -> list[dict]:
    return [
        {
            "locus": "3",
            "id": "CRA-ANNEX-VII-RISK",
            "locator": "VII.3",
            "discovery_hints": {
                "concepts": ["risk assessment"],
                "path_hints": ["*risk*assessment*", "*THREAT*"],
                "sources": [{"source": "documents", "args": {"path": "docs"}}],
            },
        },
        # Pipeline fixture only. Not a CRA id convention.
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
    ]


def _xml_pack() -> dict:
    return {"id": "cra-xml-baseline", "name": "CRA XML", "version": "0.1.0"}


class RequirementsUiTest(unittest.TestCase):
    def test_catalog_edit_sign_publish_and_extract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = load_adapter(ADAPTERS / "cra-xml" / "adapter.json")
            created = extract_section(
                root,
                ADAPTERS / "cra-xml",
                adapter,
                "VII",
                _proposals()[:1],
                _xml_pack(),
                at="2026-10-13T090000Z",
            )
            _pack, requirements = load_working_copy(created["copy"])
            point3 = next(item for item in requirements if item["id"] == "CRA-ANNEX-VII-RISK")
            edited = apply_edits(
                point3,
                {
                    "references": assign_reference_numbers(
                        [
                            {
                                "locator": point3["references"][0]["locator"],
                                "law_text": point3["references"][0]["law_text"],
                            },
                            {
                                "locator": "VII.1(a)",
                                "law_text": "a statement of the intended purpose",
                            },
                        ]
                    ),
                    "discovery_hints": {
                        "concepts": ["risk assessment"],
                        "sources": [{"source": "documents", "args": {"path": "docs"}}],
                    },
                },
            )
            save_working_requirement(
                created["copy"], edited, expected_digest=version_digest(point3)
            )
            repo = root / "product"
            repo.mkdir()
            write_json(repo / "curbpack.json", created_curbpack(packs=["house-policy"]))
            save_pack(
                repo / "curbpack" / "packs" / "house-policy" / draft_pack()["version"],
                {
                    "id": "house-policy",
                    "name": "House Policy",
                    "version": draft_pack()["version"],
                    "source": {
                        "instrument": "Content of the technical documentation",
                        "url": "https://publications.europa.eu/resource/celex/32024R2847",
                    },
                },
            )
            save_repos(root, add_repo(root, load_repos(root), name="Product", path=str(repo)))
            set_open_repo(root, "product")
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                catalog = _get(base + "/requirements")
                self.assertIn("Pack Sources", catalog)
                self.assertIn("id=\"add-open\"", catalog)
                self.assertIn("Official name", catalog)
                self.assertIn("Content of the technical documentation", catalog)
                self.assertIn("House Policy", catalog)
                sections = _get(base + "/requirements?document=cra-annex-vii")
                self.assertIn("Pack Editor", sections)
                self.assertIn("2026-10-13T090000Z", sections)
                self.assertIn(">Signed</th>", sections)
                self.assertIn(">1</td>", sections)
                self.assertNotIn("Working copy", sections)
                self.assertNotIn('value="publish"', sections)
                self.assertNotIn('data-adapter="nis"', sections)
                self.assertIn('action="/requirements/extract"', sections)
                self.assertIn('name="section_id" value="VII"', sections)
                self.assertNotIn("<h1>Extract</h1>", sections)
                self.assertNotIn("Inventory units", catalog)
                gone = _get(base + "/requirements/extract?adapter=cra-xml")
                self.assertIn("Unknown page", gone)
                with self.assertRaises(AssertionError) as missing_section:
                    _post(base + "/requirements/extract", {"adapter_id": "cra-xml"})
                self.assertIn("section_id", str(missing_section.exception))
                listed = _post(
                    base + "/requirements/select",
                    {
                        "adapter_id": "cra-xml",
                        "timestamp": "2026-10-13T090000Z",
                        "next": "edit",
                    },
                )
                self.assertIn("CRA-ANNEX-VII-RISK", listed)
                self.assertIn('class="sign-bad"', listed)
                self.assertIn("unsigned", listed)
                self.assertIn('data-coverage-status="written"', listed)
                self.assertIn('data-coverage-status="excluded"', listed)
                self.assertIn("not a publication check", listed)
                editor = _get(base + "/requirements/requirement/CRA-ANNEX-VII-RISK")
                self.assertIn("Working copy", editor)
                self.assertIn("2026-10-13T090000Z", editor)
                self.assertIn("cybersecurity risks", editor)
                self.assertIn("a statement of the intended purpose", editor)
                self.assertIn("docs", editor)
                self.assertNotIn("Local Ed25519", editor)
                self.assertNotIn("demo:", editor)
                self.assertIn('class="sign-bad"', editor)
                self.assertIn(">unsigned</button>", editor)
                self.assertIn("editor-actions", editor)
                self.assertNotIn("Technical digest", editor)
                self.assertNotIn("No signed block", editor)
                self.assertIn('id="save-req" disabled', editor)
                self.assertIn('id="cancel-edit"', editor)
                self.assertIn('id="cancel-edit" class="secondary" hidden', editor)
                self.assertIn('id="edit-fields"', editor)
                self.assertNotIn('id="edit-fields" disabled', editor)
                self.assertNotIn("enable-edit", editor)
                self.assertIn('class="ref-law"', editor)
                self.assertLess(
                    editor.index('class="ref-law"'),
                    editor.index('name="note"'),
                )
                self.assertIn('id="sign-open"', editor)
                self.assertNotIn('id="sign-open" disabled', editor)
                self.assertIn('name="strength"', editor)
                self.assertIn('placeholder="MUST"', editor)
                self.assertIn('class="field-info"', editor)
                self.assertIn("ⓘ", editor)
                self.assertIn(
                    'aria-label="MUST, SHOULD, or MAY — only when that word is in law_text. Leave empty otherwise."',
                    editor,
                )
                self.assertIn('name="expected_evidence"', editor)
                self.assertIn('placeholder="process description"', editor)
                self.assertIn(
                    'aria-label="Kind of artifact to look for. One per line. Not proof by itself."',
                    editor,
                )
                _post(
                    base + "/requirements/requirement/CRA-ANNEX-VII-RISK",
                    {
                        "present": "remediation_hint",
                        "remediation_hint": "A different hint.",
                        "expected_digest": version_digest(edited),
                    },
                )
                saved = json.loads(
                    (created["copy"] / "CRA-ANNEX-VII-RISK.json").read_text(encoding="utf-8")
                )
                self.assertEqual(saved["remediation_hint"], "A different hint.")
                self.assertEqual(saved["discovery_hints"]["sources"][0]["args"], {"path": "docs"})
                self.assertEqual(len(saved["references"]), 2)
                publish = _get(base + "/requirements/publish")
                self.assertIn("Publication blockers", publish)
                self.assertIn("unsigned", publish)
                self.assertIn("not a publication blocker", publish)
                self.assertIn("disabled>Publish release", publish)
                refused = _post(base + "/requirements/publish", {"version": "0.1.0"})
                self.assertIn("Field Edition: expected non empty string", refused)
                self.assertIn('class="invalid"', refused)
                self.assertFalse((root / "published").exists())
                _post(
                    base + "/requirements/requirement/CRA-ANNEX-VII-RISK",
                    {
                        "present": "edition",
                        "edition": "2024-11-20",
                        "expected_digest": version_digest(saved),
                    },
                )
                with_edition = json.loads(
                    (created["copy"] / "CRA-ANNEX-VII-RISK.json").read_text(encoding="utf-8")
                )
                self.assertEqual(with_edition["discovery_hints"]["sources"][0]["args"], {"path": "docs"})
                _post(
                    base + "/requirements/requirement/CRA-ANNEX-VII-RISK/sign",
                    {"name": "Ada Jurist", "expected_digest": version_digest(with_edition)},
                )
                signed = json.loads(
                    (created["copy"] / "CRA-ANNEX-VII-RISK.json").read_text(encoding="utf-8")
                )
                self.assertNotIn("demo:", signed["signed"]["signature"])
                self.assertGreater(len(signed["signed"]["signature"]), 20)
                self.assertEqual(signed["signed"]["name"], "Ada Jurist")
                sealed_editor = _get(base + "/requirements/requirement/CRA-ANNEX-VII-RISK")
                self.assertIn('class="sign-ok"', sealed_editor)
                self.assertIn("Ada Jurist", sealed_editor)
                self.assertIn('id="edit-fields"', sealed_editor)
                self.assertNotIn('id="edit-fields" disabled', sealed_editor)
                self.assertNotIn("enable-edit", sealed_editor)
                self.assertIn('id="save-req" disabled', sealed_editor)
                self.assertNotIn('id="sign-open"', sealed_editor)
                sealed_list = _get(base + "/requirements/copy")
                self.assertIn('class="sign-ok"', sealed_list)
                self.assertIn("signed", sealed_list)
                self.assertIn("Ada Jurist", sealed_list)
                _post(base + "/requirements/seal", {"name": "Ada Jurist"})
                ready = _get(base + "/requirements/publish")
                self.assertNotIn("Publication blockers", ready)
                self.assertNotIn("disabled>Publish release", ready)
                _post(base + "/requirements/publish", {"version": "0.1.0"})
                release = root / "published" / "cra-xml-baseline" / "0.1.0"
                self.assertTrue((release / "pack.json").is_file())
                self.assertTrue((release / "CRA-ANNEX-VII-RISK.json").is_file())
                copy_after_publish = _bytes(created["copy"])
                with self.assertRaises(AssertionError):
                    _post(base + "/requirements/publish", {"version": "0.1.0"})
                self.assertEqual(_bytes(created["copy"]), copy_after_publish)
                with patch(
                    "requirements.extract.produce._default_complete",
                    _fake_model_complete,
                ):
                    page = _post(
                        base + "/requirements/extract",
                        {"adapter_id": "cra-xml", "section_id": "VII"},
                    )
                    job_id = _job_id(page)
                    self.assertNotIn('id="job-progress"', page)
                    self.assertNotIn("extract-bar", page)
                    job = _wait_job(base, job_id)
                self.assertEqual(job["status"], "done", job)
                names = list_working_copies(root, "cra-xml-baseline")
                self.assertIn("2026-10-13T090000Z", names)
                self.assertGreater(len(names), 1)
                self.assertEqual(_bytes(created["copy"]), copy_after_publish)
                new_stamp = next(stamp for stamp in names if stamp != "2026-10-13T090000Z")
                self.assertEqual(job.get("base_timestamp"), "2026-10-13T090000Z")
                self.assertEqual(job.get("copy_timestamp"), new_stamp)
                chosen = selected_copy(root, "cra-xml-baseline")
                self.assertIsNotNone(chosen)
                self.assertEqual(chosen.name, "2026-10-13T090000Z")
                refreshed = _get(base + "/requirements?document=cra-annex-vii")
                self.assertIn("2026-10-13T090000Z", refreshed)
                self.assertNotIn(new_stamp, refreshed)
                _post(
                    base + "/requirements/select",
                    {
                        "adapter_id": "cra-xml",
                        "timestamp": new_stamp,
                        "next": "edit",
                    },
                )
                opened = _get(base + "/requirements/copy")
                self.assertIn("FIXTURE-VII-", opened)
                llm_path = root / "cra-xml-baseline" / f"{new_stamp}.work" / "llm.json"
                self.assertTrue(llm_path.is_file())
                llm = json.loads(llm_path.read_text(encoding="utf-8"))
                stages = {note["stage"] for note in llm["llm"]}
                self.assertEqual(stages, {"interpret", "discovery_hints"})
                release_before = _bytes(release)
                with patch(
                    "requirements.extract.produce._default_complete",
                    _failing_complete,
                ):
                    failed_page = _post(
                        base + "/requirements/extract",
                        {"adapter_id": "cra-xml", "section_id": "VII"},
                    )
                    failed = _wait_job(base, _job_id(failed_page))
                self.assertEqual(failed["status"], "failed", failed)
                shown = _get(base + f"/requirements?document=cra-annex-vii&job={failed['job_id']}")
                self.assertIn("Failed", shown)
                self.assertIn(failed["error"], shown)
                self.assertIn(">Close<", shown)
                self.assertEqual(_bytes(created["copy"]), copy_after_publish)
                self.assertEqual(_bytes(release), release_before)
                self.assertEqual(selected_copy(root, "cra-xml-baseline").name, new_stamp)
            finally:
                httpd.shutdown()
                httpd.server_close()


def _wait_job(base: str, job_id: str) -> dict:
    deadline = time.time() + 8
    job = None
    while time.time() < deadline:
        job = json.loads(_get(base + f"/requirements/jobs/{job_id}"))
        if job["status"] in {"done", "failed", "aborted"}:
            return job
        time.sleep(0.05)
    raise AssertionError(job)


def _failing_complete(prompt: str, settings: dict) -> str:
    raise ModelError("model", "output", "a JSON object with provisions")


def _fake_model_complete(prompt: str, settings: dict) -> str:
    """Test double: one validated proposal per input locus. Not a CRA id convention."""
    match = re.search(r"---\n(\[.*\])\n---", prompt, re.S)
    if match is None:
        raise AssertionError("prompt missing provisions JSON")
    provisions = json.loads(match.group(1))
    if settings["stage"] == "interpret":
        rows = []
        for item in provisions:
            locus = item["locus"]
            if locus == "3":
                rows.append({"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3"})
            else:
                safe = locus.replace("(", "").replace(")", "")
                rows.append(
                    {"locus": locus, "id": f"FIXTURE-VII-{safe}", "locator": f"VII.{locus}"}
                )
        return json.dumps({"provisions": rows})
    return json.dumps(
        {
            "provisions": [
                {"locus": item["locus"], "discovery_hints": {"concepts": [item["locus"]]}}
                for item in provisions
            ]
        }
    )


def _bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _job_id(page: str) -> str:
    marker = 'data-job-id="'
    start = page.index(marker) + len(marker)
    end = page.index('"', start)
    return page[start:end]


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise AssertionError(f"{exc.code} {body}") from exc


_NIS_URL = "https://publications.europa.eu/resource/celex/32022L2555"


class RepoPackSectionsTest(unittest.TestCase):
    def test_pack_without_requirements_enables_extract_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            version = draft_pack()["version"]
            fresh = repo / "curbpack" / "packs" / "fresh-nis" / version
            kept = repo / "curbpack" / "packs" / "kept-nis" / version
            house = repo / "curbpack" / "packs" / "house-policy" / version
            fresh.mkdir(parents=True)
            kept.mkdir(parents=True)
            house.mkdir(parents=True)
            write_json(
                repo / "curbpack.json",
                created_curbpack(packs=["fresh-nis", "kept-nis", "house-policy"]),
            )
            write_json(
                fresh / "pack.json",
                {
                    "id": "fresh-nis",
                    "name": "Fresh NIS",
                    "version": "0.1.0",
                    "source": {"framework": "EU", "instrument": "NIS2", "url": _NIS_URL},
                },
            )
            write_json(
                kept / "pack.json",
                {
                    "id": "kept-nis",
                    "name": "Kept NIS",
                    "version": "0.1.0",
                    "source": {"framework": "EU", "instrument": "NIS2", "url": _NIS_URL},
                },
            )
            requirement = {
                "id": "NIS-ART1",
                "pack_id": "kept-nis",
                "source": {
                    "framework": "EU",
                    "instrument": "NIS2",
                    "identifier": "CELEX:32022L2555",
                    "language": "en",
                    "url": _NIS_URL,
                },
                "references": [
                    {"nr": 1, "locator": "Art.1", "law_text": "This Directive lays down measures."}
                ],
            }
            write_json(kept / "NIS-ART1.json", requirement)
            write_json(
                house / "pack.json",
                {
                    "id": "house-policy",
                    "name": "House Policy Example",
                    "version": "0.1.0",
                },
            )
            write_json(
                house / "HOUSE-SECURITY-MD.json",
                {
                    "id": "HOUSE-SECURITY-MD",
                    "pack_id": "house-policy",
                    "source": {
                        "framework": "internal",
                        "instrument": "House Policy Example",
                        "identifier": "HOUSE-SECURITY-MD",
                        "language": "en",
                        "url": "packs/house-policy/pack.json",
                    },
                    "references": [
                        {
                            "nr": 1,
                            "locator": "Security docs",
                            "law_text": "SECURITY.md present with a Security header.",
                        }
                    ],
                },
            )
            save_repos(
                root,
                add_repo(root, load_repos(root), name="Fixture product", path=str(repo)),
            )
            set_open_repo(root, "fixture-product")
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                fresh_page = _get(
                    base + "/requirements?document=fresh-nis&repo=fixture-product"
                )
                self.assertIn('id="add-open"', fresh_page)
                self.assertIn("No sections yet. Click Add.", fresh_page)
                self.assertNotIn(">Extract</button>", fresh_page)
                added = _post(
                    base + "/requirements/catalog",
                    {
                        "document_id": "fresh-nis",
                        "repo": "fixture-product",
                        "adapter_id": "nis",
                        "section_id": "Art.1",
                    },
                )
                self.assertIn(">Extract</button>", added)
                self.assertIn('disabled>Edit</button>', added)
                self.assertEqual(list(fresh.glob("*.json")), [fresh / "pack.json"])
                kept_page = _get(
                    base + "/requirements?document=kept-nis&repo=fixture-product"
                )
                self.assertIn("Art.1", kept_page)
                self.assertIn('action="/requirements/requirement/NIS-ART1"', kept_page)
                self.assertIn('name="pack" value="kept-nis"', kept_page)
                self.assertIn(">Extract</button>", kept_page)
                house_page = _get(
                    base + "/requirements?document=house-policy&repo=fixture-product"
                )
                self.assertIn("<code>manual</code>", house_page)
                self.assertIn("Security docs", house_page)
                self.assertNotIn("No sections yet. Click Add.", house_page)
                self.assertNotIn("HOUSE-SECURITY-MD", house_page)
                self.assertIn('disabled>Extract</button>', house_page)
                self.assertIn('name="section" value="Security docs"', house_page)
                self.assertIn('id="add-open"', house_page)
                listed = _get(
                    base + "/requirements/copy?repo=fixture-product&pack=kept-nis"
                )
                self.assertIn("NIS-ART1", listed)
                self.assertIn("This Directive lays down measures.", _get(
                    base + "/requirements/requirement/NIS-ART1?repo=fixture-product&pack=kept-nis"
                ))
                _post(
                    base + "/requirements/requirement/NIS-ART1",
                    {
                        "repo": "fixture-product",
                        "pack": "kept-nis",
                        "present": "note",
                        "note": "Reviewed in the pack.",
                        "expected_digest": version_digest(requirement),
                    },
                )
                saved = json.loads((kept / "NIS-ART1.json").read_text(encoding="utf-8"))
                self.assertEqual(saved["note"], "Reviewed in the pack.")
            finally:
                httpd.shutdown()
