"""Try discovery from the Requirements editor: pick repo, GO, inspect hits."""

from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.adapter import ADAPTERS, load_adapter
from requirements.workspace import extract_section, mark_selected, mark_source_adapter


def _proposals() -> list[dict]:
    return [
        {
            "locus": "3",
            "id": "CRA-ANNEX-VII-RISK",
            "locator": "VII.3",
            "discovery_hints": {
                "concepts": ["risk assessment"],
                "path_hints": ["*risk*"],
                "sources": [{"source": "documents"}],
            },
        }
    ]


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, data: dict) -> str:
    body = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def _fake_complete(prompt: str, settings: dict) -> str:
    time.sleep(0.15)
    return json.dumps(
        {
            "score": 0.9,
            "rank": "High",
            "why": "Mentions risk assessment for the product.",
            "excerpt": "risk assessment",
        }
    )


class TryDiscoveryUiTest(unittest.TestCase):
    def test_editor_try_discovery_lists_hits_without_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = load_adapter(ADAPTERS / "cra-xml" / "adapter.json")
            created = extract_section(
                root,
                ADAPTERS / "cra-xml",
                adapter,
                "VII",
                _proposals(),
                {"id": "cra-xml-baseline", "name": "CRA XML", "version": "0.1.0"},
                at="2026-10-13T090000Z",
            )
            mark_source_adapter(root, "cra-xml")
            mark_selected(root, "cra-xml-baseline", created["copy"].name)
            product = root / "product"
            product.mkdir()
            (product / "docs").mkdir()
            (product / "docs" / "risk-assessment.md").write_text(
                "# Risk\n\nThis is the risk assessment for the product.\n",
                encoding="utf-8",
            )
            (product / "curbpack.json").write_text(
                json.dumps({"packs": ["cra-xml-baseline"], "hunt": {}}),
                encoding="utf-8",
            )
            data = load_repos(root)
            add_repo(root, data, name="Sample", path=str(product))
            save_repos(root, data)

            ws = Workspace(root)
            ws.discover_complete = _fake_complete
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ws))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                editor = _get(base + "/requirements/requirement/CRA-ANNEX-VII-RISK")
                self.assertIn("Discovery test run for CRA-ANNEX-VII-RISK", editor)
                self.assertIn("an assessment of the cybersecurity risks", editor)
                self.assertIn('id="try-discovery-open">Test discovery</button>', editor)
                self.assertIn("testDiscovery.disabled = true", editor)
                self.assertNotIn("save-before-test", editor)
                self.assertIn("try-discovery-dialog", editor)
                self.assertIn("GO", editor)
                self.assertIn("Sample", editor)
                self.assertIn('id="try-add-repo-open"', editor)
                self.assertIn(">Add repo</button>", editor)
                self.assertIn('id="try-add-repo"', editor)
                self.assertIn('name="next"', editor)
                self.assertIn('id="try-browse-path"', editor)
                self.assertIn('id="repo-browse"', editor)

                started = _post(
                    base + "/requirements/requirement/CRA-ANNEX-VII-RISK/try-discovery",
                    {"repo_id": "sample", "assess_limit": "5"},
                )
                self.assertIn('id="try-job"', started)
                self.assertIn('class="log"', started)
                self.assertIn("class=\"progress\"", started)
                job_id = None
                for part in started.split('data-poll="')[1:]:
                    poll = part.split('"', 1)[0]
                    if "/try-discovery/jobs/" in poll:
                        job_id = poll.rsplit("/", 1)[-1]
                        break
                self.assertTrue(job_id)
                deadline = time.time() + 5
                while time.time() < deadline:
                    job = json.loads(_get(base + f"/requirements/try-discovery/jobs/{job_id}"))
                    if job.get("status") != "running":
                        break
                    time.sleep(0.05)
                self.assertEqual(job.get("status"), "done")
                after = _get(
                    base
                    + "/requirements/requirement/CRA-ANNEX-VII-RISK"
                    + f"?try_repo=sample&try_open=1"
                )
                self.assertIn("docs/risk-assessment.md", after)
                self.assertIn("Mentions risk assessment", after)
                self.assertIn("0.90", after)
                self.assertIn(">Found on</th>", after)
                self.assertIn("<code>*risk*</code>", after)
                self.assertNotIn("Matched by", after)
                dialog = after.split('id="try-discovery-dialog"', 1)[1].split("</dialog>", 1)[0]
                self.assertNotIn("check-pick", dialog)
                self.assertNotIn("vote-", dialog)
                self.assertNotIn("Add a finding", dialog)
                self.assertIn('data-open="1"', after)

                file_page = _get(
                    base
                    + "/requirements/requirement/CRA-ANNEX-VII-RISK/try-discovery/file"
                    + "?repo=sample&path=docs%2Frisk-assessment.md"
                )
                self.assertIn(
                    "Back to the discovery test run for CRA-ANNEX-VII-RISK",
                    file_page,
                )
                self.assertIn("<mark>", file_page)
                self.assertIn("risk assessment", file_page)
            finally:
                httpd.shutdown()
                httpd.server_close()


    def test_try_discovery_add_repo_returns_to_dialog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = load_adapter(ADAPTERS / "cra-xml" / "adapter.json")
            created = extract_section(
                root,
                ADAPTERS / "cra-xml",
                adapter,
                "VII",
                _proposals(),
                {"id": "cra-xml-baseline", "name": "CRA XML", "version": "0.1.0"},
                at="2026-10-13T090000Z",
            )
            mark_source_adapter(root, "cra-xml")
            mark_selected(root, "cra-xml-baseline", created["copy"].name)
            product = root / "product"
            product.mkdir()
            (product / "docs").mkdir()
            (product / "curbpack.json").write_text(
                json.dumps({"packs": ["cra-xml-baseline"], "hunt": {}}),
                encoding="utf-8",
            )

            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                editor = _get(base + "/requirements/requirement/CRA-ANNEX-VII-RISK")
                self.assertIn("No product repos yet.", editor)
                self.assertIn('id="try-add-repo-open"', editor)
                self.assertIn(">Add repo</button>", editor)
                self.assertNotIn("Add one under Discovery", editor)

                after = _post(
                    base + "/discover/repos",
                    {
                        "name": "From try",
                        "path": str(product),
                        "next": "/requirements/requirement/CRA-ANNEX-VII-RISK?try_open=1",
                    },
                )
                self.assertIn('data-open="1"', after)
                self.assertIn("From try", after)
                self.assertIn('name="repo_id"', after)
                self.assertIn('value="from-try"', after)
                self.assertNotIn("No product repos yet.", after)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
