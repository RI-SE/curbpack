"""HTML/JS for navigating directories when adding a product repo."""

from __future__ import annotations

import html
import json


def browse_dialog_and_script(*, start_path: str) -> str:
    """One browse dialog plus wire helpers for Add-repo path fields on the page."""
    start = html.escape(start_path)
    start_js = json.dumps(start_path)
    return f"""
<dialog id="repo-browse">
<div class="head">
  <h2>Choose folder</h2>
  <button type="button" class="secondary" id="repo-browse-cancel">Cancel</button>
</div>
<div class="body">
<p class="muted">Server-side folders (this machine). Pick the product repository root.</p>
<p><code id="repo-browse-cwd">{start}</code></p>
<p class="actions">
<button type="button" class="secondary" id="repo-browse-up" disabled>Up</button>
<button type="button" id="repo-browse-use">Use this folder</button>
</p>
<ul id="repo-browse-list" class="repo-browse-list"></ul>
<p id="repo-browse-err" class="err" hidden></p>
</div>
</dialog>
<style>
.repo-browse-list{{list-style:none;margin:.5rem 0 0;padding:0;max-height:16rem;overflow:auto;border:1px solid var(--line);border-radius:8px}}
.repo-browse-list li{{margin:0;border-bottom:1px solid var(--line)}}
.repo-browse-list li:last-child{{border-bottom:0}}
.repo-browse-list button{{display:block;width:100%;text-align:left;background:#fff;color:var(--ink);border:0;border-radius:0;padding:.45rem .65rem}}
.repo-browse-list button:hover{{background:#f8fafc}}
label.repo-path-row{{display:block}}
.repo-path-row .path-with-browse{{display:flex;gap:.35rem;align-items:center}}
.repo-path-row .path-with-browse input{{flex:1;min-width:0}}
</style>
<script>
(function () {{
  const browseDialog = document.getElementById("repo-browse");
  if (!browseDialog || browseDialog.dataset.wired === "1") return;
  browseDialog.dataset.wired = "1";
  const cwdEl = document.getElementById("repo-browse-cwd");
  const listEl = document.getElementById("repo-browse-list");
  const errEl = document.getElementById("repo-browse-err");
  const upBtn = document.getElementById("repo-browse-up");
  const useBtn = document.getElementById("repo-browse-use");
  const cancelBtn = document.getElementById("repo-browse-cancel");
  let currentPath = {start_js};
  let targetPath = null;
  let targetName = null;
  const startPath = {start_js};

  function showErr(message) {{
    if (!errEl) return;
    if (!message) {{ errEl.hidden = true; errEl.textContent = ""; return; }}
    errEl.hidden = false;
    errEl.textContent = message;
  }}

  async function loadDir(path) {{
    showErr("");
    const url = "/discover/browse?dir=" + encodeURIComponent(path || "");
    const response = await fetch(url, {{ headers: {{ "Accept": "application/json" }} }});
    const data = await response.json().catch(() => ({{}}));
    if (!response.ok) {{
      showErr(data.error || data.detail || ("Could not list " + path));
      return;
    }}
    currentPath = data.path || path;
    if (cwdEl) cwdEl.textContent = currentPath;
    if (upBtn) {{
      upBtn.disabled = !data.parent;
      upBtn.dataset.parent = data.parent || "";
    }}
    if (!listEl) return;
    listEl.innerHTML = "";
    const dirs = data.dirs || [];
    if (!dirs.length) {{
      const empty = document.createElement("li");
      empty.innerHTML = '<span class="muted" style="display:block;padding:.45rem .65rem">No subfolders</span>';
      listEl.appendChild(empty);
      return;
    }}
    for (const row of dirs) {{
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = row.name + "/";
      button.addEventListener("click", () => loadDir(row.path));
      li.appendChild(button);
      listEl.appendChild(li);
    }}
  }}

  if (upBtn) {{
    upBtn.addEventListener("click", () => {{
      if (upBtn.dataset.parent) loadDir(upBtn.dataset.parent);
    }});
  }}
  if (useBtn) {{
    useBtn.addEventListener("click", () => {{
      if (targetPath) targetPath.value = currentPath;
      if (targetName && !targetName.value.trim()) {{
        const parts = currentPath.replace(/\\\\/g, "/").split("/").filter(Boolean);
        targetName.value = parts[parts.length - 1] || "";
      }}
      browseDialog.close();
    }});
  }}
  if (cancelBtn) cancelBtn.addEventListener("click", () => browseDialog.close());
  browseDialog.addEventListener("cancel", (event) => {{
    event.preventDefault();
    browseDialog.close();
  }});

  window.openRepoBrowse = function (pathInput, nameInput) {{
    targetPath = pathInput;
    targetName = nameInput || null;
    const initial = (pathInput && pathInput.value.trim()) || startPath;
    browseDialog.showModal();
    loadDir(initial);
  }};
}})();
</script>
"""


def path_field_with_browse(*, path_id: str, browse_id: str, value: str = "") -> str:
    """Path label + text input + Browse button that calls openRepoBrowse."""
    val = html.escape(value)
    pid = html.escape(path_id)
    bid = html.escape(browse_id)
    return f"""
<label class="repo-path-row">Path
<span class="path-with-browse">
<input type="text" id="{pid}" name="path" required autocomplete="off" placeholder="/absolute/path/to/repo" value="{val}">
<button type="button" class="secondary" id="{bid}">Browse…</button>
</span>
</label>
<p class="muted">Absolute path, or a path relative to the workspace. Browse lists folders on this machine.</p>
"""
