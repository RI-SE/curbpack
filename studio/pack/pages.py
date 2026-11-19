"""Requirements catalog, editor, and extract-job panel."""

from __future__ import annotations

import html
import json

from app.pages import page, repo_config_panel


def documents_page(model: dict) -> bytes:
    rows = [_document_row(document) for document in model.get("documents") or []]
    repo_id = str(model.get("repo_id") or "")
    file_absent = bool(model.get("file_absent"))
    if not repo_id:
        table = '<p class="muted">Choose a repo to work with.</p>'
    elif file_absent:
        table = '<p class="muted">This repository has no curbpack.json.</p>'
    elif rows:
        table = (
            "<table><thead><tr>"
            "<th>Pack Name</th><th>Official name</th><th>Adapter</th><th>URL</th><th>Actions</th>"
            "</tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    else:
        table = '<p class="muted">No packs yet. Click Add.</p>'
    err = str(model.get("error") or "")
    flash = f'<p class="err">{html.escape(err)}</p>' if err else _flash(str(model.get("message") or ""))
    claims_line = (
        '<p class="muted">No Claims.</p>' if model.get("no_claims") else ""
    )
    create = ""
    if repo_id and file_absent:
        create = (
            '<p class="actions">'
            '<button type="button" id="curbpack-open">Create curbpack.json</button>'
            "</p>"
        )
    # Edit configuration lives on Project, not in this panel.
    show = ("config",) if repo_id and not file_absent and model.get("curbpack_file") else ()
    config_panel = repo_config_panel(model, action="/requirements", show=show, beside=create)
    add = _add_toolbar() if repo_id and not file_absent else ""
    import_zip = ""
    if repo_id and not file_absent:
        import_zip = """
<form method="post" action="/requirements" enctype="multipart/form-data" class="import-zip">
<input type="file" name="archive" accept=".zip,application/zip" aria-label="ZIP file">
<button type="button">Import From zipped Pack</button>
</form>
<script>
(function () {
  const form = document.querySelector("form.import-zip");
  const input = form.querySelector('input[name="archive"]');
  form.querySelector("button").addEventListener("click", function () { input.click(); });
  input.addEventListener("change", function () {
    if (input.files && input.files.length) form.submit();
  });
})();
</script>
"""
    source_actions = ""
    if add or import_zip:
        source_actions = f'<div class="actions source-actions">{add}{import_zip}</div>'
    taken = [
        {"id": str(item.get("id") or ""), "namespace": str(item.get("namespace") or "")}
        for item in (model.get("documents") or [])
        if isinstance(item, dict)
    ]
    dialog = (
        _document_add_dialog(
            model.get("adapters") or [],
            repo_id,
            namespace_base=str((model.get("curbpack_fields") or {}).get("namespace_base") or ""),
            taken=taken,
        )
        if add
        else ""
    )
    edit_dialog = (
        _document_edit_dialog(
            model.get("edit_adapters") or model.get("adapters") or [],
            repo_id,
            namespace_base=str((model.get("curbpack_fields") or {}).get("namespace_base") or ""),
        )
        if add
        else ""
    )
    config_dialog = _curbpack_dialog(model) if repo_id else ""
    body = f"""
<h1>Pack Sources</h1>
<p class="muted">Pack Sources reads the Packs named in this repository's curbpack.json.
Change project from the top bar.</p>
{_start_empty_form(show=not repo_id)}
{claims_line}
{source_actions}
{flash}
<div class="card">{table}</div>
{dialog}
{edit_dialog}
{config_dialog}
"""
    if model.get("job"):
        body += job_fragment(model["job"]).decode("utf-8")
    return page("Pack Sources", body, banner=config_panel)


def export_page(model: dict) -> bytes:
    pack_id = html.escape(str(model.get("pack_id") or ""))
    document_id = html.escape(str(model.get("document_id") or ""))
    destination = html.escape(str(model.get("destination") or ""))
    conflict = str(model.get("conflict") or "")
    message = _flash(str(model.get("message") or ""))
    cancel = '<p><a href="/requirements">Cancel</a></p>'
    if not model.get("timestamp"):
        body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a></p>
<h1>Export Pack</h1>
<p>No working copy is selected for <code>{pack_id}</code>.</p>
{cancel}
"""
        return page("Export Pack", body)
    readings = _signature_report(model.get("rows") or [])
    conflict_html = ""
    if conflict:
        shown = html.escape(conflict)
        conflict_html = f"""
<p class="err">{shown}</p>
<form method="post" action="/requirements/export">
<input type="hidden" name="document" value="{document_id}">
<input type="hidden" name="destination" value="{destination}">
<input type="hidden" name="overwrite" value="1">
<button type="submit">Overwrite</button>
</form>
<p>Or choose another directory.</p>
"""
    body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a></p>
<h1>Export Pack</h1>
<p>Pack <code>{pack_id}</code> · <code>{html.escape(str(model.get("timestamp") or ""))}</code></p>
<p>Signed: {int(model.get("signed") or 0)}</p>
<p>Unsigned: {int(model.get("unsigned") or 0)}</p>
{readings}
{message}
{conflict_html}
<form method="post" action="/requirements/export">
<input type="hidden" name="document" value="{document_id}">
<label>Destination <input name="destination" value="{destination}"></label>
<button type="submit">Export</button>
</form>
<form method="post" action="/requirements/export">
<input type="hidden" name="document" value="{document_id}">
<input type="hidden" name="exchange" value="zip">
<button type="submit">Export ZIP</button>
</form>
{cancel}
"""
    return page("Export Pack", body)


def _signature_report(rows: list) -> str:
    """Print status rows. This does not decide whether a signature is valid."""
    parts: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = html.escape(str(row.get("title") or ""))
        status = html.escape(str(row.get("status") or ""))
        method = html.escape(str(row.get("method") or ""))
        reason = str(row.get("reason") or "").strip()
        reason_html = f" — {html.escape(reason)}" if reason else ""
        parts.append(
            f'<p class="signature"><strong>{title}</strong> status {status} method {method}{reason_html}</p>'
        )
    return "\n".join(parts)


def catalog_page(model: dict) -> bytes:
    if not str(model.get("repo_id") or ""):
        body = f"""
<p class="muted">Go back: <a href="/requirements">Pack Sources</a></p>
<h1>Pack Editor</h1>
<p class="muted">Choose a repo to work with.</p>
"""
        return page("Pack Editor", body, banner=repo_config_panel(model, action="/requirements"))
    document = model.get("document") or {}
    name = str(document.get("name") or "")
    rows = [_source_row(source) for source in model.get("sources") or []]
    if rows:
        table = (
            "<table><thead><tr>"
            "<th>Adapter</th><th>Section</th><th>URL</th>"
            "<th>Signed</th><th>Unsigned</th><th>Actions</th>"
            "</tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    else:
        table = '<p class="muted">No sections yet. Click Add Section.</p>'
    err = str(model.get("error") or "")
    flash = f'<p class="err">{html.escape(err)}</p>' if err else _flash(str(model.get("message") or ""))
    repo = str(model.get("repo_id") or "")
    back = "/requirements" + (f"?repo={html.escape(repo)}" if repo else "")
    add = '<p class="actions"><button type="button" id="add-open">Add Section</button></p>'
    dialog = _section_add_dialog(model.get("adapters") or [], document)
    body = f"""
<p class="muted">Go back: <a href="{back}">Pack Sources</a></p>
<h1>Pack Editor</h1>
<p class="muted">Sections of <strong>{html.escape(name)}</strong>.
<strong>Extract</strong>, when available, does not overwrite your current Requirement automatically. You choose which updates to keep. Fields you leave out stay as they are.
Humans must review, <strong>Edit</strong>, and <strong>Sign</strong> each Requirement.</p>
{flash}
{add}
<div class="card">{table}</div>
{dialog}
"""
    if model.get("job"):
        body += job_fragment(model["job"], document_id=str(document.get("id") or "")).decode("utf-8")
    return page(
        "Pack Editor",
        body,
        banner=repo_config_panel(model, action="/requirements"),
    )


def _start_empty_form(*, show: bool) -> str:
    if not show:
        return ""
    return """
<form method="post" action="/requirements/start-empty">
<label>Working folder <input name="folder" required autocomplete="off"></label>
<button type="submit">Start empty</button>
</form>
<p class="muted">Start empty registers that folder and opens it. Save writes curbpack.json.</p>
"""


def _add_toolbar() -> str:
    return '<button type="button" id="add-open">Add Pack Source</button>'


def _document_row(document: dict) -> str:
    doc_id = str(document.get("id") or "")
    name = str(document.get("name") or "")
    namespace = str(document.get("namespace") or "")
    official = str(document.get("official_name") or "")
    adapter_id = str(document.get("adapter_id") or "")
    url = str(document.get("url") or "")
    pack_dir = str(document.get("pack_dir") or "")
    if url:
        link = (
            f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(url)}</a>'
        )
    else:
        link = '<span class="muted">Manual Content</span>'
    where = f'<div class="muted">{html.escape(pack_dir)}</div>' if pack_dir else ""
    url_cell = link + where
    repo = str(document.get("repo_id") or "")
    repo_field = (
        f'<input type="hidden" name="repo" value="{html.escape(repo)}">' if repo else ""
    )
    actions = (
        '<button type="button" class="pack-edit"'
        f' data-id="{html.escape(doc_id)}"'
        f' data-name="{html.escape(name)}"'
        f' data-official="{html.escape(official)}"'
        f' data-url="{html.escape(url)}"'
        f' data-adapter="{html.escape(adapter_id or "manual")}"'
        f' data-extract="{"1" if document.get("extract_enabled") else "0"}"'
        ">Edit Pack Source</button>"
        '<form method="get" action="/requirements">'
        f'<input type="hidden" name="document" value="{html.escape(doc_id)}">'
        f"{repo_field}"
        '<button type="submit">Edit Sections</button></form>'
    )
    if not document.get("missing"):
        actions += (
            '<form method="get" action="/requirements/export">'
            f'<input type="hidden" name="document" value="{html.escape(doc_id)}">'
            '<button type="submit">Export Pack</button></form>'
            f"{_signature_badge(document) if 'all_signed' in document else ''}"
        )
    return (
        f'<tr data-document="{html.escape(doc_id)}" data-adapter="{html.escape(adapter_id)}">'
        f"<td><code>{html.escape(namespace)}</code></td>"
        f'<td class="muted">{html.escape(official)}</td>'
        f"<td><code>{html.escape(adapter_id)}</code></td>"
        f"<td>{url_cell}</td>"
        f'<td class="actions">{actions}</td></tr>'
    )


def _signature_badge(document: dict) -> str:
    title = html.escape(str(document.get("signature_title") or ""))
    if document.get("all_signed"):
        label, kind = "signed", "sign-ok"
    else:
        label, kind = "unsigned", "sign-bad"
    return (
        f'<button type="button" class="{kind}" disabled title="{title}">{label}</button>'
    )


def _curbpack_dialog(model: dict) -> str:
    fields = model.get("curbpack_fields") or {}
    repo_id = html.escape(str(model.get("repo_id") or ""))
    packs = ",".join(str(item) for item in fields.get("packs") or [] if isinstance(item, str))
    exclude = ",".join(
        str(item) for item in fields.get("exclude_requirements") or [] if isinstance(item, str)
    )
    hints = json.dumps(fields.get("search_hints") or {}, indent=2, ensure_ascii=False)
    show = "1" if model.get("show_curbpack_dialog") else ""
    return f"""
<dialog id="curbpack-dialog" data-show="{show}">
<div class="head"><h2>curbpack.json</h2>
<button type="button" id="curbpack-cancel" class="secondary">Cancel</button></div>
<div class="body">
<form method="post" action="/requirements/curbpack" id="curbpack-form">
<input type="hidden" name="repo" value="{repo_id}">
<input type="hidden" name="action" value="save">
<label>Packs <input type="text" name="packs" value="{html.escape(packs)}" autocomplete="off"></label>
<label>Exclude requirements <input type="text" name="exclude_requirements" value="{html.escape(exclude)}" autocomplete="off"></label>
<label>packs_dir <input type="text" name="packs_dir" value="{html.escape(str(fields.get("packs_dir") or ""))}" required autocomplete="off"></label>
<label>claims_dir <input type="text" name="claims_dir" value="{html.escape(str(fields.get("claims_dir") or ""))}" required autocomplete="off"></label>
<label>results_dir <input type="text" name="results_dir" value="{html.escape(str(fields.get("results_dir") or ""))}" required autocomplete="off"></label>
<label>reports_dir <input type="text" name="reports_dir" value="{html.escape(str(fields.get("reports_dir") or ""))}" required autocomplete="off"></label>
<label>namespace_base <input type="text" name="namespace_base" value="{html.escape(str(fields.get("namespace_base") or ""))}" required autocomplete="off"></label>
<label>search_hints <textarea name="search_hints" required>{html.escape(hints)}</textarea></label>
<p class="actions">
<button type="button" id="curbpack-cancel-footer" class="secondary">Cancel</button>
<button type="submit">Save</button>
</p>
</form>
</div>
</dialog>
<script>
(function () {{
  const dialog = document.getElementById("curbpack-dialog");
  function closeDialog() {{ dialog.close(); }}
  const openBtn = document.getElementById("curbpack-open");
  if (openBtn) openBtn.addEventListener("click", () => dialog.showModal());
  if (dialog.dataset.show === "1") dialog.showModal();
  document.getElementById("curbpack-cancel").addEventListener("click", closeDialog);
  document.getElementById("curbpack-cancel-footer").addEventListener("click", closeDialog);
}})();
</script>
"""


def _document_add_dialog(
    adapters: list,
    repo_id: str = "",
    *,
    namespace_base: str = "",
    taken: list | None = None,
) -> str:
    options = []
    for item in adapters:
        adapter_id = str(item.get("id") or "")
        instrument = str(item.get("instrument") or adapter_id)
        options.append(
            f'<option value="{html.escape(adapter_id)}">'
            f"{html.escape(instrument)} ({html.escape(adapter_id)})</option>"
        )
    return f"""
<dialog id="add-dialog">
<div class="head"><h2>Add Pack Source</h2></div>
<div class="body">
<form method="post" action="/requirements/documents" id="add-form">
<input type="hidden" name="repo" value="{html.escape(repo_id)}">
<label>Adapter<select name="adapter_id" id="add-adapter" required>{"".join(options)}</select></label>
<label>Pack name<span class="name-with-namespace"><span class="namespace-prefix" id="add-namespace">{html.escape(namespace_base)}/</span><input type="text" name="name" id="add-name" required autocomplete="off"></span></label>
<p class="name-conflict" id="add-name-conflict" hidden>This Pack name is already in curbpack.json.</p>
<label>Official Document Name<input type="text" name="official_name" id="add-official" autocomplete="off"></label>
<label>URL<span class="url-with-open"><input type="text" name="url" id="add-url" required autocomplete="off"><button type="button" class="secondary" id="add-url-open">Open</button></span></label>
<p class="actions">
<button type="submit" id="add-save">Save</button>
<button type="button" id="add-cancel" class="secondary">Cancel</button>
</p>
</form>
</div>
</dialog>
<script type="application/json" id="add-adapters">{json.dumps(adapters)}</script>
<script type="application/json" id="add-taken">{json.dumps(taken or [])}</script>
<script>
(function () {{
  const adapters = JSON.parse(document.getElementById("add-adapters").textContent || "[]");
  const taken = JSON.parse(document.getElementById("add-taken").textContent || "[]");
  const dialog = document.getElementById("add-dialog");
  const adapterEl = document.getElementById("add-adapter");
  const nameEl = document.getElementById("add-name");
  const urlEl = document.getElementById("add-url");
  const saveEl = document.getElementById("add-save");
  const conflictEl = document.getElementById("add-name-conflict");
  const namespaceBase = (document.getElementById("add-namespace").textContent || "").replace(/\\/$/, "");
  function packId(name) {{
    const slug = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return slug || "document";
  }}
  function refreshName() {{
    const name = nameEl.value.trim();
    const namespace = namespaceBase ? namespaceBase + "/" + name : name;
    const id = packId(name);
    const conflict = name !== "" && taken.some((item) => item.namespace === namespace || item.id === id);
    nameEl.classList.toggle("conflict", conflict);
    nameEl.setAttribute("aria-invalid", conflict ? "true" : "false");
    saveEl.disabled = conflict;
    conflictEl.hidden = !conflict;
  }}
  function currentAdapter() {{
    return adapters.find((item) => item.id === adapterEl.value) || null;
  }}
  function fillFromAdapter() {{
    const adapter = currentAdapter();
    if (!adapter) return;
    urlEl.value = adapter.url || "";
    if (nameEl.dataset.touched !== "1") nameEl.value = adapter.instrument || "";
    refreshName();
  }}
  document.getElementById("add-open").addEventListener("click", () => {{
    nameEl.dataset.touched = "";
    fillFromAdapter();
    dialog.showModal();
  }});
  function closeAdd() {{ dialog.close(); }}
  document.getElementById("add-cancel").addEventListener("click", closeAdd);
  adapterEl.addEventListener("change", fillFromAdapter);
  nameEl.addEventListener("input", () => {{
    nameEl.dataset.touched = "1";
    refreshName();
  }});
  document.getElementById("add-url-open").addEventListener("click", () => {{
    const url = urlEl.value.trim();
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  }});
  fillFromAdapter();
}})();
</script>
"""


def _document_edit_dialog(adapters: list, repo_id: str, *, namespace_base: str = "") -> str:
    """Edit one pack row. Saving a URL that turns Extract on asks before writing pack.json."""
    options = ['<option value="manual">Manual Content</option>']
    choices = [{"id": "manual", "instrument": "Manual Content", "url": ""}]
    for item in adapters:
        adapter_id = str(item.get("id") or "")
        instrument = str(item.get("instrument") or adapter_id)
        url = str(item.get("url") or "")
        options.append(
            f'<option value="{html.escape(adapter_id)}">'
            f"{html.escape(instrument)} ({html.escape(adapter_id)})</option>"
        )
        choices.append(
            {"id": adapter_id, "instrument": instrument, "url": url}
        )
    return f"""
<dialog id="edit-pack-dialog">
<div class="head"><h2>Edit Pack Source</h2></div>
<div class="body">
<form method="post" action="/requirements/documents" id="edit-pack-form">
<input type="hidden" name="repo" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="update">
<input type="hidden" name="pack" id="edit-pack-id" value="">
<label>Adapter<select name="adapter_id" id="edit-adapter" required>{"".join(options)}</select></label>
<label>Pack name<span class="name-with-namespace"><span class="namespace-prefix" id="edit-namespace">{html.escape(namespace_base)}/</span><input type="text" name="name" id="edit-name" required autocomplete="off"></span></label>
<label>Official Document Name<input type="text" name="official_name" id="edit-official" autocomplete="off"></label>
<label>URL<span class="url-with-open"><input type="text" name="url" id="edit-url" autocomplete="off"><button type="button" class="secondary" id="edit-url-open">Open</button></span></label>
<p class="actions">
<button type="submit" id="edit-pack-save">Save</button>
<button type="button" id="edit-pack-cancel" class="secondary">Cancel</button>
</p>
</form>
</div>
</dialog>
<dialog id="edit-pack-confirm">
<div class="head"><h2>Update the pack info?</h2>
<button type="button" id="edit-pack-confirm-cancel" class="secondary">Cancel</button></div>
<div class="body">
<p>This URL turns Extract on. Save the pack info?</p>
<p class="actions">
<button type="button" id="edit-pack-confirm-cancel-footer" class="secondary">Cancel</button>
<button type="button" id="edit-pack-confirm-ok">OK</button>
</p>
</div>
</dialog>
<script type="application/json" id="edit-adapters">{json.dumps(choices)}</script>
<script>
(function () {{
  const adapters = JSON.parse(document.getElementById("edit-adapters").textContent || "[]");
  const dialog = document.getElementById("edit-pack-dialog");
  const confirmDialog = document.getElementById("edit-pack-confirm");
  const form = document.getElementById("edit-pack-form");
  const adapterEl = document.getElementById("edit-adapter");
  const nameEl = document.getElementById("edit-name");
  const officialEl = document.getElementById("edit-official");
  const urlEl = document.getElementById("edit-url");
  const idEl = document.getElementById("edit-pack-id");
  let initial = {{adapter: "", url: "", name: "", official: ""}};
  function currentAdapter() {{
    return adapters.find((item) => item.id === adapterEl.value) || null;
  }}
  function extractOn() {{
    const url = urlEl.value.trim();
    if (!url || adapterEl.value === "manual") return false;
    return adapters.some((item) => item.id !== "manual" && item.url && item.url === url);
  }}
  function rowChanged() {{
    return adapterEl.value !== initial.adapter
      || urlEl.value.trim() !== initial.url
      || nameEl.value.trim() !== initial.name
      || officialEl.value.trim() !== initial.official;
  }}
  function closeEdit() {{ dialog.close(); }}
  function closeConfirm() {{ confirmDialog.close(); }}
  document.querySelectorAll(".pack-edit").forEach((button) => {{
    button.addEventListener("click", () => {{
      idEl.value = button.dataset.id || "";
      nameEl.value = button.dataset.name || "";
      officialEl.value = button.dataset.official || "";
      urlEl.value = button.dataset.url || "";
      const adapterId = button.dataset.adapter || "manual";
      adapterEl.value = adapters.some((item) => item.id === adapterId) ? adapterId : "manual";
      initial = {{
        adapter: adapterEl.value,
        url: urlEl.value.trim(),
        name: nameEl.value.trim(),
        official: officialEl.value.trim(),
      }};
      form.dataset.confirmed = "";
      dialog.showModal();
    }});
  }});
  adapterEl.addEventListener("change", () => {{
    const adapter = currentAdapter();
    if (!adapter) return;
    urlEl.value = adapter.url || "";
    if (!officialEl.value.trim() && adapter.instrument && adapter.id !== "manual") {{
      officialEl.value = adapter.instrument;
    }}
  }});
  document.getElementById("edit-pack-cancel").addEventListener("click", closeEdit);
  document.getElementById("edit-url-open").addEventListener("click", () => {{
    const url = urlEl.value.trim();
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  }});
  form.addEventListener("submit", (event) => {{
    if (form.dataset.confirmed === "1") return;
    if (rowChanged() && extractOn()) {{
      event.preventDefault();
      confirmDialog.showModal();
    }}
  }});
  document.getElementById("edit-pack-confirm-cancel").addEventListener("click", closeConfirm);
  document.getElementById("edit-pack-confirm-cancel-footer").addEventListener("click", closeConfirm);
  document.getElementById("edit-pack-confirm-ok").addEventListener("click", () => {{
    form.dataset.confirmed = "1";
    confirmDialog.close();
    form.requestSubmit();
  }});
}})();
</script>
"""


def _section_add_dialog(adapters: list, document: dict) -> str:
    doc_id = str(document.get("id") or "")
    doc_name = str(document.get("name") or "")
    options = []
    for item in adapters:
        adapter_id = str(item.get("id") or "")
        instrument = str(item.get("instrument") or adapter_id)
        options.append(
            f'<option value="{html.escape(adapter_id)}">'
            f"{html.escape(instrument)} ({html.escape(adapter_id)})</option>"
        )
    return f"""
<dialog id="add-dialog">
<div class="head"><h2>Add section</h2>
<button type="button" id="add-cancel" class="secondary">Cancel</button></div>
<div class="body">
<form method="post" action="/requirements/catalog" id="add-form">
<input type="hidden" name="document_id" value="{html.escape(doc_id)}">
<input type="hidden" name="repo" value="{html.escape(str(document.get("repo_id") or ""))}">
<p>Document <strong>{html.escape(doc_name)}</strong></p>
<label>Adapter<select name="adapter_id" id="add-adapter" required>{"".join(options)}</select></label>
<label>Section<select name="section_id" id="add-section" required></select></label>
<p class="muted" id="section-hint"></p>
<p class="actions">
<button type="button" id="add-cancel-footer" class="secondary">Cancel</button>
<button type="submit" id="add-save">Save</button>
</p>
</form>
</div>
</dialog>
<script type="application/json" id="add-adapters">{json.dumps(adapters)}</script>
<script>
(function () {{
  const adapters = JSON.parse(document.getElementById("add-adapters").textContent || "[]");
  const dialog = document.getElementById("add-dialog");
  const adapterEl = document.getElementById("add-adapter");
  const sectionEl = document.getElementById("add-section");
  const hint = document.getElementById("section-hint");
  const save = document.getElementById("add-save");
  function currentAdapter() {{
    return adapters.find((item) => item.id === adapterEl.value) || null;
  }}
  function fillSections() {{
    const adapter = currentAdapter();
    const sections = ((adapter && adapter.sections) || []).filter(
      (section) => section.ready && section.in_scope
    );
    sectionEl.innerHTML = "";
    if (!sections.length) {{
      hint.textContent = "No section can be extracted.";
      save.disabled = true;
      return;
    }}
    hint.textContent = "";
    save.disabled = false;
    for (const section of sections) {{
      const option = document.createElement("option");
      option.value = section.id;
      option.textContent = section.id + (section.title ? (" — " + section.title) : "");
      sectionEl.appendChild(option);
    }}
  }}
  document.getElementById("add-open").addEventListener("click", () => {{
    fillSections();
    dialog.showModal();
  }});
  function closeAdd() {{ dialog.close(); }}
  document.getElementById("add-cancel").addEventListener("click", closeAdd);
  document.getElementById("add-cancel-footer").addEventListener("click", closeAdd);
  adapterEl.addEventListener("change", fillSections);
  fillSections();
}})();
</script>
"""



def _bound_pack_fields(model: dict) -> str:
    repo = str(model.get("repo_id") or "")
    pack = str(model.get("bound_pack") or "")
    fields = []
    if repo and pack:
        fields.append(f'<input type="hidden" name="repo" value="{html.escape(repo)}">')
        fields.append(f'<input type="hidden" name="pack" value="{html.escape(pack)}">')
    for key in ("proposal", "destination", "section"):
        value = str(model.get(key) or "").strip()
        if value:
            fields.append(
                f'<input type="hidden" name="{key}" value="{html.escape(value)}">'
            )
    return "".join(fields)


def _working_copy_identity(model: dict) -> str:
    """The open working copy, so the save POST checks that copy's digest."""
    if str(model.get("bound_pack") or "").strip():
        return ""
    stamp = str(model.get("copy_timestamp") or "").strip()
    if not stamp:
        return ""
    return f'<input type="hidden" name="timestamp" value="{html.escape(stamp)}">'


def _pack_edit_form(model: dict) -> str:
    repo = str(model.get("edit_repo") or "")
    pack = str(model.get("edit_pack") or "")
    if not repo or not pack:
        return ""
    return (
        '<form method="get" action="/requirements/copy">'
        f'<input type="hidden" name="repo" value="{html.escape(repo)}">'
        f'<input type="hidden" name="pack" value="{html.escape(pack)}">'
        '<button type="submit">Edit</button></form>'
    )


def _source_row(source: dict) -> str:
    adapter_id = str(source.get("adapter_id") or source.get("id") or "")
    source_id = str(source.get("source_id") or source.get("id") or adapter_id)
    section_id = str(source.get("section_id") or "")
    url = str(source.get("url") or "")
    pack_dir = str(source.get("pack_dir") or "")
    link = (
        f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(url)}</a>'
        if url
        else '<span class="muted">—</span>'
    )
    where = f'<div class="muted">{html.escape(pack_dir)}</div>' if pack_dir else ""
    url_cell = link + where
    section_ready = source.get("section_ready")
    if section_ready is True:
        section_status = ""
    elif section_ready is False:
        section_status = "Cannot be extracted"
    else:
        section_status = str(source.get("status") or "")
    copies = list(source.get("copies") or [])
    form_id = f"source-{html.escape(source_id)}"
    chosen = next((copy for copy in copies if copy.get("chosen")), None)
    edit_repo = str(source.get("edit_repo") or "")
    edit_pack = str(source.get("edit_pack") or "")
    edit_requirement = str(source.get("edit_requirement") or "")
    edit_section = str(source.get("edit_section") or "")
    if edit_section and edit_repo and edit_pack:
        hidden_copy = ""
        actions = (
            '<form method="get" action="/requirements/copy">'
            f'<input type="hidden" name="repo" value="{html.escape(edit_repo)}">'
            f'<input type="hidden" name="pack" value="{html.escape(edit_pack)}">'
            f'<input type="hidden" name="section" value="{html.escape(edit_section)}">'
            '<button type="submit">Edit</button></form>'
        )
    elif edit_requirement and edit_repo and edit_pack:
        hidden_copy = ""
        actions = (
            f'<form method="get" action="/requirements/requirement/{html.escape(edit_requirement)}">'
            f'<input type="hidden" name="repo" value="{html.escape(edit_repo)}">'
            f'<input type="hidden" name="pack" value="{html.escape(edit_pack)}">'
            '<button type="submit">Edit</button></form>'
        )
    elif edit_repo and edit_pack:
        hidden_copy = ""
        actions = (
            '<form method="get" action="/requirements/copy">'
            f'<input type="hidden" name="repo" value="{html.escape(edit_repo)}">'
            f'<input type="hidden" name="pack" value="{html.escape(edit_pack)}">'
            '<button type="submit">Edit</button></form>'
        )
    elif chosen is not None:
        stamp = html.escape(str(chosen.get("timestamp") or ""))
        hidden_copy = (
            f'<input type="hidden" name="timestamp" form="{form_id}" value="{stamp}">'
        )
        actions = (
            f'<button type="submit" form="{form_id}" name="next" value="edit">Edit</button>'
        )
    else:
        hidden_copy = ""
        actions = '<button type="button" disabled>Edit</button>'
    signed_count = source.get("signed_count")
    unsigned_count = source.get("unsigned_count")
    if signed_count is None:
        signed_cell = "<td></td>"
        unsigned_cell = "<td></td>"
    else:
        signed_cell = f"<td>{int(signed_count)}</td>"
        unsigned_cell = f"<td>{int(unsigned_count or 0)}</td>"
    document_id = str(source.get("document_id") or "")
    if source.get("extract_enabled") is False or section_ready is False:
        extract = '<button type="button" disabled>Extract</button>'
    else:
        hidden_document = (
            f'<input type="hidden" name="document_id" value="{html.escape(document_id)}">'
            if document_id
            else ""
        )
        repo_id = str(source.get("repo_id") or "")
        hidden_repo = (
            f'<input type="hidden" name="repo" value="{html.escape(repo_id)}">'
            if repo_id
            else ""
        )
        extract = (
            '<form method="post" action="/requirements/extract">'
            f'<input type="hidden" name="adapter_id" value="{html.escape(adapter_id)}">'
            f'<input type="hidden" name="section_id" value="{html.escape(section_id)}">'
            f"{hidden_document}"
            f"{hidden_repo}"
            '<button type="submit">Extract</button></form>'
        )
    return (
        f'<tr data-adapter="{html.escape(adapter_id)}" data-source="{html.escape(source_id)}">'
        f"<td><code>{html.escape(adapter_id)}</code><br>"
        f"{html.escape(str(source.get('source_format') or ''))}</td>"
        f"<td><code>{html.escape(section_id)}</code>"
        + (f" · <span class=\"muted\">{html.escape(section_status)}</span>" if section_status else "")
        + "</td>"
        f"<td>{url_cell}</td>"
        f"{signed_cell}{unsigned_cell}"
        '<td class="actions">'
        f"{hidden_copy}"
        f'<form id="{form_id}" method="post" action="/requirements/select">'
        f'<input type="hidden" name="adapter_id" value="{html.escape(adapter_id)}"></form>'
        f"{extract}"
        f"{actions}"
        "</td></tr>"
    )


def source_page(model: dict) -> bytes:
    adapter_id = str(model.get("adapter_id") or "")
    legal = model.get("source") or {}
    url = str(legal.get("url") or "")
    url_html = (
        f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(url)}</a>'
        if url
        else ""
    )
    section_rows = []
    ready_options = []
    for section in model.get("sections") or []:
        flags = []
        flags.append("in scope" if section.get("in_scope") else "out of scope")
        flags.append("ready" if section.get("ready") else "not ready")
        section_rows.append(
            f"<li><code>{html.escape(str(section.get('id')))}</code> — "
            f"{html.escape(', '.join(flags))}"
            + (
                f" · {html.escape(str(section.get('title')))}"
                if section.get("title")
                else ""
            )
            + "</li>"
        )
        if section.get("ready") is True and section.get("in_scope") is True:
            selected = " selected" if section.get("id") == model.get("inspect_section") else ""
            ready_options.append(
                f'<option value="{html.escape(str(section.get("id")))}"{selected}>'
                f'{html.escape(str(section.get("id")))}</option>'
            )
    inventory = model.get("inventory") or {}
    diagnostics = list(inventory.get("diagnostics") or []) + list(model.get("provision_diagnostics") or [])
    diag_html = (
        "<ul>"
        + "".join(f"<li>{html.escape(str(item.get('reason') or item))}</li>" for item in diagnostics)
        + "</ul>"
        if diagnostics
        else "<p class=\"muted\">No parsing diagnostics.</p>"
    )
    provision_rows = []
    for item in model.get("provisions_preview") or []:
        provision_rows.append(
            "<li><code>"
            f"{html.escape(str(item.get('locus')))}</code> "
            f"{html.escape(str(item.get('law_text') or '')[:160])}</li>"
        )
    provisions_html = (
        "<ul>" + "".join(provision_rows) + "</ul>" if provision_rows else ""
    )
    inspect = ""
    if ready_options:
        inspect = (
            '<form method="get" action="/requirements/inspect">'
            f'<input type="hidden" name="adapter" value="{html.escape(adapter_id)}">'
            f'<label>Section<select name="section">{"".join(ready_options)}</select></label>'
            '<p><button type="submit">Show provisions</button></p></form>'
            + provisions_html
        )
    unit_count = (inventory or {}).get("unit_count")
    inventory_html = ""
    if unit_count is not None:
        inventory_html = f"<p>Inventory units: {html.escape(str(unit_count))}</p>"
    body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a></p>
<h1>Source details</h1>
<p>{html.escape(str(legal.get("instrument") or ""))}
 <code>{html.escape(str(legal.get("identifier") or ""))}</code></p>
<p>Adapter <code>{html.escape(adapter_id)}</code>
 ({html.escape(str(model.get("source_format") or ""))}, {html.escape(str(model.get("status") or ""))})</p>
<p>{url_html}</p>
<div class="card">
<h2>Sections</h2>
<ul>{"".join(section_rows) or "<li>No sections.</li>"}</ul>
{inventory_html}
{diag_html}
{inspect}
</div>
"""
    return page("Source details", body)


def _sections_crumb(model: dict) -> str:
    """Link back to the sections of the pack source this working copy belongs to."""
    document_id = str(model.get("document_id") or "").strip()
    name = str(model.get("document_name") or "").strip()
    if not document_id or not name:
        return ""
    href = "/requirements?document=" + document_id
    repo = str(model.get("repo_id") or "").strip()
    if repo:
        href += "&repo=" + repo
    return f' · <a href="{html.escape(href)}">{html.escape(name)}</a>'


def copy_page(model: dict) -> bytes:
    if not model.get("timestamp"):
        body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a>{_sections_crumb(model)}</p>
<h1>Requirements</h1>
<p>No working copy is selected. Choose a dated copy on the catalog, or start a new extraction.</p>
"""
        return page("Requirements", body)
    read_only = bool(model.get("read_only"))
    rows = []
    for item in model.get("requirements") or []:
        requirement_id = str(item.get("id") or "")
        locators = ", ".join(str(value) for value in (item.get("locators") or []))
        who = str(item.get("who") or "").strip()
        if item.get("verifiable"):
            badge = (
                '<button type="button" class="sign-ok" disabled>signed</button>'
                + (f' <span class="muted">{html.escape(who)}</span>' if who else "")
            )
        elif item.get("signed"):
            badge = (
                '<button type="button" class="sign-bad" disabled>not verified</button>'
                + (f' <span class="muted">{html.escape(who)}</span>' if who else "")
            )
        else:
            badge = '<button type="button" class="sign-bad" disabled>unsigned</button>'
        if read_only:
            id_cell = f"<code>{html.escape(requirement_id)}</code>"
        elif item.get("changes_only") and item.get("changes_href"):
            id_cell = (
                f'<a href="{html.escape(str(item.get("changes_href") or ""))}">'
                f"<code>{html.escape(requirement_id)}</code></a>"
            )
        else:
            query = html.escape(str(model.get("requirement_query") or ""))
            id_cell = (
                f'<a href="/requirements/requirement/{html.escape(requirement_id)}{query}">'
                f"<code>{html.escape(requirement_id)}</code></a>"
            )
        new_cell = ""
        if model.get("comparison"):
            href = str(item.get("changes_href") or "")
            if href:
                label = "New" if item.get("changes_only") else "Updates"
                link = f'<a href="{html.escape(href)}">{label}</a>'
            else:
                link = ""
            new_cell = f"<td>{link}</td>"
        rows.append(
            "<tr>"
            f"<td>{id_cell}</td>"
            f"<td>{html.escape(locators)}</td>"
            f"<td>{badge}</td>"
            f"{new_cell}"
            "</tr>"
        )
    listed = (
        "<table><thead><tr><th>Requirement</th><th>Source references</th><th>Signature</th>"
        + ("<th>Changes</th>" if model.get("comparison") else "")
        + "</tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table>"
        if rows
        else "<p>This Pack has no requirements.</p>"
    )
    coverage = model.get("coverage_detail")
    coverage_html = ""
    if coverage:
        coverage_html = (
            "<details><summary>Extract coverage</summary>"
            '<p class="muted">Per legal locus: extracted into this working copy, skipped, or failed. '
            "It is not a publication check.</p>"
            f"{_coverage_detail_html(coverage)}</details>"
        )
    path = str(model.get("pack_dir") or "")
    path_line = f'<p class="muted"><code>{html.escape(path)}</code></p>' if path else ""
    report = _signature_report(model.get("rows") or []) if model.get("rows") else ""
    body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a>{_sections_crumb(model)}
 · <code>{html.escape(str(model.get("adapter_id") or ""))}</code></p>
<h1>Requirements</h1>
{_drop_extracted(model)}
{path_line}
{report}
{_flash(str(model.get("message") or ""))}
<div class="card">{listed}</div>
{coverage_html}
"""
    return page("Requirements", body)



def _drop_extracted(model: dict) -> str:
    """Drop clears the latest section extract. Requirements already saved in the pack stay."""
    when = str(model.get("extracted_at") or "").strip()
    section = str(model.get("section") or "").strip()
    pack = str(model.get("pack_id") or "").strip()
    if not when or not section or not pack:
        return ""
    repo = html.escape(str(model.get("repo_id") or ""))
    return (
        '<form method="post" action="/requirements/extract/drop">'
        f'<input type="hidden" name="repo" value="{repo}">'
        f'<input type="hidden" name="pack" value="{html.escape(pack)}">'
        f'<input type="hidden" name="section" value="{html.escape(section)}">'
        f'<p class="muted">Latest extraction {html.escape(when)}</p>'
        '<p><button type="submit">Drop Extracted Data</button></p>'
        "</form>"
    )


def _flash(message: str) -> str:
    if not message:
        return ""
    return f'<p class="ok">{html.escape(message)}</p>'


def _coverage_label(status: str) -> str:
    """Human label for extract coverage status codes stored as written/excluded/failed."""
    return {
        "written": "extracted",
        "excluded": "skipped",
        "failed": "failed",
        "none": "none",
    }.get(status, status)


def _coverage_detail_html(detail: dict | None) -> str:
    if not detail:
        return "<p class=\"muted\">Select a working copy to inspect extract coverage.</p>"
    raw_status = str(detail.get("status") or "none")
    status = html.escape(_coverage_label(raw_status))
    rows = []
    for item in detail.get("loci") or []:
        if not isinstance(item, dict):
            continue
        locus = html.escape(str(item.get("locus") or ""))
        row_status = str(item.get("status") or "")
        css = {
            "written": "coverage-written",
            "excluded": "coverage-excluded",
            "failed": "coverage-failed",
        }.get(row_status, "muted")
        reason = item.get("reason")
        reason_html = f" — {html.escape(str(reason))}" if reason else ""
        rows.append(
            f'<li class="{css}" data-coverage-status="{html.escape(row_status)}">'
            f"<code>{locus}</code> {html.escape(_coverage_label(row_status))}{reason_html}</li>"
        )
    loci_html = "<ul>" + "".join(rows) + "</ul>" if rows else "<p class=\"muted\">No locus rows.</p>"
    error = detail.get("error")
    error_html = f'<p class="err">{html.escape(str(error))}</p>' if error else ""
    diagnostics = detail.get("source_diagnostics") or []
    diag_html = ""
    if diagnostics:
        diag_html = (
            "<p>Source diagnostics</p><ul>"
            + "".join(
                f"<li>{html.escape(str(item.get('reason') or item))}</li>" for item in diagnostics
            )
            + "</ul>"
        )
    return (
        f"<h3>Extract coverage</h3>"
        f"<p>Status <strong>{status}</strong></p>"
        f"{error_html}{loci_html}{diag_html}"
    )


def consolidate_page(model: dict) -> bytes:
    requirements = {item["id"]: item for item in (model.get("requirements") or [])}
    digests = model.get("digests") or {}
    blocks = []
    for suggestion in model.get("suggestions") or []:
        ids = suggestion.get("ids") or []
        hidden = []
        references = []
        for requirement_id in ids:
            hidden.append(f'<input type="hidden" name="ids" value="{html.escape(str(requirement_id))}">')
            hidden.append(
                f'<input type="hidden" name="digest_id" value="{html.escape(str(requirement_id))}">'
            )
            hidden.append(
                '<input type="hidden" name="digest_value" value="'
                f'{html.escape(str(digests.get(requirement_id) or ""))}">'
            )
            for ref in (requirements.get(requirement_id) or {}).get("references") or []:
                references.append(
                    f'<input type="hidden" name="ref_locator" value="{html.escape(str(ref.get("locator") or ""))}">'
                    f'<input type="hidden" name="ref_law_text" value="{html.escape(str(ref.get("law_text") or ""))}">'
                )
        options = "".join(
            f'<option value="{html.escape(str(requirement_id))}">{html.escape(str(requirement_id))}</option>'
            for requirement_id in ids
        )
        blocks.append(
            "<li>"
            f"<p>{html.escape(', '.join(str(item) for item in ids))}: {html.escape(str(suggestion.get('reason') or ''))}</p>"
            '<form method="post" action="/requirements/consolidate/apply">'
            + "".join(hidden)
            + "".join(references)
            + f'<label>Retained id<select name="retained_id">{options}</select></label>'
            + '<label>note<input type="text" name="note"></label>'
            + "<p><button type=\"submit\">Merge</button></p></form></li>"
        )
    listed = "<ul>" + "".join(blocks) + "</ul>" if blocks else "<p>No overlap suggestions.</p>"
    body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a>
 · <a href="/requirements/copy">Requirements list</a></p>
<h1>Consolidate</h1>
<p class="muted">Leaving this page does not save a merge.</p>
{listed}
"""
    return page("Consolidate", body)


def compare_form_document(query: dict) -> bytes:
    """Shell for the compiled form. The script draws the fields."""
    from urllib.parse import urlencode

    pairs = []
    for key in ("proposal", "destination", "pack", "repo", "section"):
        value = (query.get(key) or [""])[0]
        if value:
            pairs.append((key, value))
    cancel = "/requirements/copy"
    if pairs:
        cancel += "?" + urlencode(pairs)
    requirement = html.escape((query.get("requirement") or [""])[0])
    body = (
        f'<div id="compare-form" data-requirement="{requirement}" '
        f'data-cancel="{html.escape(cancel)}"></div>'
        '<script type="module" src="/requirements/compare/form.js"></script>'
    )
    return page("Compare", body)


def compare_page(model: dict) -> bytes:
    left = str(model.get("left") or "")
    right = str(model.get("right") or "")
    option_rows = list(model.get("options") or [])
    if not option_rows:
        # Backward-compatible fallback if only bare timestamps are supplied.
        option_rows = [
            {"value": stamp, "label": str(stamp), "kind": "working"}
            for stamp in (model.get("copies") or [])
        ]

    def _options_html(selected: str) -> str:
        bits = []
        for item in option_rows:
            value = str(item.get("value") or "")
            label = str(item.get("label") or value)
            mark = " selected" if value and value == selected else ""
            bits.append(
                f'<option value="{html.escape(value)}"{mark}>{html.escape(label)}</option>'
            )
        return "".join(bits)

    diff = model.get("diff") or {}
    sections = ""
    if diff:
        transfer = ""
        if model.get("can_transfer"):
            transfer = (
                "<form method=\"post\" action=\"/requirements/compare/apply\">"
                f"<input type=\"hidden\" name=\"source\" value=\"{html.escape(left)}\">"
                f"<input type=\"hidden\" name=\"destination\" value=\"{html.escape(right)}\">"
                "<label>Requirement<input type=\"text\" name=\"requirement_id\"></label>"
                "<label>Field<input type=\"text\" name=\"field\"></label>"
                "<label>Value<input type=\"text\" name=\"value\"></label>"
                "<label>Source digest<input type=\"text\" name=\"source_digest\"></label>"
                "<label>Destination digest<input type=\"text\" name=\"destination_digest\"></label>"
                "<p><button type=\"submit\">Apply transfer</button></p></form>"
            )
        sections = (
            f"<p>Unchanged: {html.escape(', '.join(diff.get('unchanged') or []) or 'none')}</p>"
            f"<p>Changed: {html.escape(_changed_text(diff.get('changed') or []))}</p>"
            f"<p>Only left: {html.escape(', '.join(diff.get('only_left') or []) or 'none')}</p>"
            f"<p>Only right: {html.escape(', '.join(diff.get('only_right') or []) or 'none')}</p>"
            f"<p>Possible split: {html.escape(str(diff.get('possible_split') or []))}</p>"
            f"<p>Ambiguous: {html.escape(str(diff.get('ambiguous') or []))}</p>"
            f"{transfer}"
        )
    body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a></p>
<h1>Compare</h1>
<p class="muted">Opening this page does not change either copy.
The selected working copy is labeled <strong>Working copy</strong>.
Published releases appear as <strong>Published · version</strong>.</p>
<form method="get" action="/requirements/compare">
<label>Left<select name="left">{_options_html(left)}</select></label>
<label>Right<select name="right">{_options_html(right)}</select></label>
<p><button type="submit">Show differences</button></p>
</form>
{sections}
"""
    return page("Compare", body)


def _changed_text(changed: list) -> str:
    if not changed:
        return "none"
    return "; ".join(f"{item.get('id')}: {', '.join(item.get('fields') or [])}" for item in changed)


def _copy_line(model: dict, requirement: dict) -> str:
    stamp = str(model.get("copy_timestamp") or "")
    pack_id = str(model.get("pack_id") or "")
    version = str(model.get("pack_version") or "")
    parts = ["Working copy"]
    if pack_id:
        parts.append(f"<code>{html.escape(pack_id)}</code>")
    if stamp:
        parts.append(f"<code>{html.escape(stamp)}</code>")
    if version:
        parts.append(f"version <code>{html.escape(version)}</code>")
    origin = requirement.get("origin") if isinstance(requirement.get("origin"), dict) else {}
    origin_pack = str(origin.get("pack") or "")
    origin_version = str(origin.get("version") or "")
    taken = ""
    if origin_pack or origin_version:
        taken = (
            " Taken from published "
            f"<code>{html.escape(origin_pack)}</code> "
            f"<code>{html.escape(origin_version)}</code>."
        )
    return f'<p class="muted">{" · ".join(parts)}.{taken}</p>'


def _signature_word(reading: dict | None) -> str:
    """valid, invalid, or unsigned. Object status is a different fact."""
    if not isinstance(reading, dict):
        return "unsigned"
    if reading.get("verifiable"):
        return "valid"
    reason = str(reading.get("reason") or "")
    if reason.startswith("No signed block"):
        return "unsigned"
    return "invalid"


def _identity_lines(model: dict, requirement: dict) -> str:
    identity = (
        '<p id="requirement-identity">Namespace '
        f'<code>{html.escape(str(requirement.get("namespace") or ""))}</code>'
        f' · Pack <code>{html.escape(str(model.get("pack_id") or ""))}</code>'
        f' · Requirement <code>{html.escape(str(requirement.get("id") or ""))}</code></p>'
    )
    origin = requirement.get("origin")
    origin_line = ""
    if isinstance(origin, dict) and origin:
        bits = []
        for key in ("namespace", "pack", "version", "requirement"):
            if key in origin:
                bits.append(f'{key} <code>{html.escape(str(origin.get(key) or ""))}</code>')
        origin_line = f'<p id="requirement-origin">Origin {" ".join(bits)}</p>'
    word = _signature_word(model.get("reading") if isinstance(model.get("reading"), dict) else None)
    signature = (
        f'<p id="signature-status" data-signature="{html.escape(word)}">'
        f"Signature status {html.escape(word)}</p>"
    )
    return identity + origin_line + signature


def ownership_confirmation_page(
    requirement_id: str,
    form: dict,
    cancel_href: str,
    action: str | None = None,
) -> bytes:
    """The story's confirmation. Nothing has been written yet."""
    hidden = []
    for key, values in form.items():
        if key == "take_ownership":
            continue
        for value in values:
            hidden.append(
                f'<input type="hidden" name="{html.escape(str(key))}" '
                f'value="{html.escape(str(value))}">'
            )
    hidden.append('<input type="hidden" name="take_ownership" value="1">')
    post_action = action or f"/requirements/requirement/{html.escape(requirement_id)}"
    body = f"""
<h1>Take ownership of this Pack?</h1>
<p>You are about to modify a Pack published under another namespace.</p>
<p>By continuing, you take responsibility for maintaining your own copy of the entire Pack, including all its Requirements.</p>
<p>The original Pack remains unchanged. Your copy is unsigned and requires your own review; signing is a separate action, not a condition for export.</p>
<p class="actions">
<a href="{html.escape(cancel_href)}">Cancel</a>
<form method="post" action="{post_action}">
{"".join(hidden)}
<button type="submit">Take ownership</button>
</form>
</p>
"""
    return page("Take ownership of this Pack?", body)


def _review_target(model: dict) -> dict:
    """The Requirement open on this page, including its working-copy timestamp."""
    requirement = model.get("requirement") if isinstance(model.get("requirement"), dict) else {}
    target = {
        "repo": str(model.get("claims_repo_id") or model.get("repo_id") or ""),
        "namespace": str(requirement.get("namespace") or ""),
        "pack_id": str(requirement.get("pack_id") or model.get("pack_id") or ""),
        "requirement_id": str(requirement.get("id") or ""),
    }
    if not str(model.get("bound_pack") or "").strip():
        timestamp = str(model.get("copy_timestamp") or "")
        if timestamp:
            target["timestamp"] = timestamp
    return target


def _affected_claims_html(model: dict) -> str:
    from urllib.parse import quote, urlencode

    blocks = []
    target = _review_target(model)
    pack = target["pack_id"]
    requirement_id = target["requirement_id"]
    review_query = {
        "repo": target["repo"],
        "namespace": target["namespace"],
        "pack_id": pack,
        "requirement_id": requirement_id,
    }
    discovery_query = {"repo": target["repo"], "pack": pack}
    if target.get("timestamp"):
        review_query["timestamp"] = target["timestamp"]
        discovery_query["timestamp"] = target["timestamp"]
    for item in model.get("affected_claims") or []:
        if not isinstance(item, dict):
            continue
        claim_id = str(item.get("id") or "")
        recorded = item.get("recorded") if isinstance(item.get("recorded"), dict) else {}
        current = item.get("current") if isinstance(item.get("current"), dict) else {}
        review = "/claims?" + urlencode(review_query) + "#" + quote(f"claim-{claim_id}", safe="")
        discovery = (
            "/discover/claims/"
            + quote(requirement_id, safe="")
            + "?"
            + urlencode(discovery_query)
        )
        later = "/requirements/requirement/" + quote(requirement_id, safe="")
        later_pack = str(model.get("bound_pack") or "")
        if target["repo"] or later_pack:
            later += "?" + urlencode({"repo": target["repo"], "pack": later_pack})
        recorded_digest = html.escape(str(recorded.get("requirement_digest") or ""))
        current_digest = html.escape(str(current.get("digest") or ""))
        blocks.append(
            f'<p data-affected-claim="{html.escape(claim_id)}">'
            f"<span>{html.escape(claim_id)}</span>"
            f'<span data-claim-recorded-digest="{recorded_digest}">{recorded_digest}</span>'
            f'<span data-claim-current-digest="{current_digest}">{current_digest}</span>'
            f'<a href="{html.escape(review)}">Review Claim</a>'
            f'<a href="{html.escape(discovery)}">Discovery</a>'
            f'<a data-later="1" href="{html.escape(later)}">Later</a>'
            f"</p>"
        )
    if not blocks:
        return ""
    return "<section>" + "".join(blocks) + "</section>"


def _ownership_claims_html(model: dict) -> str:
    from urllib.parse import quote, urlencode

    groups = model.get("ownership_claims") if isinstance(model.get("ownership_claims"), dict) else {}
    target = _review_target(model)
    blocks = []
    review = "/claims?" + urlencode(
        {
            "repo": target["repo"],
            "namespace": target["namespace"],
            "pack_id": target["pack_id"],
            "requirement_id": target["requirement_id"],
            **({"timestamp": target["timestamp"]} if target.get("timestamp") else {}),
        }
    )
    for item in groups.get("source") or []:
        if not isinstance(item, dict):
            continue
        claim_id = str(item.get("id") or "")
        blocks.append(
            f'<p data-source-claim="{html.escape(claim_id)}"'
            f' data-source-namespace="{html.escape(str(item.get("namespace") or ""))}">'
            f"<span>{html.escape(claim_id)}</span>"
            f'<a href="{html.escape(review + "#" + quote("claim-" + claim_id, safe=""))}">Review Claim</a>'
            f"</p>"
        )
    for item in groups.get("owned") or []:
        if not isinstance(item, dict):
            continue
        blocks.append(f'<p data-owned-claim="{html.escape(str(item.get("id") or ""))}"></p>')
    if not blocks:
        return ""
    return "<section>" + "".join(blocks) + "</section>"


def editor_page(model: dict) -> bytes:
    requirement = model.get("requirement")
    if not isinstance(requirement, dict):
        return page("Not found", "<h1>Not found</h1><p>Unknown requirement.</p>")
    signed = isinstance(requirement.get("signed"), dict)
    source = requirement.get("source") or {}
    hints = requirement.get("discovery_hints") or {}
    # Locator / law_text are display-only inside the same fieldset (no inputs).
    references = _references(requirement.get("references") or [])
    invalid = {str(name) for name in (model.get("invalid_fields") or []) if str(name)}
    fields = _scalars(requirement, invalid)
    err = str(model.get("error") or "")
    flash = (
        f'<p class="err">{html.escape(err)}</p>'
        if err
        else _flash(str(model.get("message") or ""))
    )
    affected = _affected_claims_html(model)
    ownership = _ownership_claims_html(model)
    banner = '<p id="unsaved" hidden>Unsaved edits. The saved version is unchanged.</p>'
    # Clean: nothing to save. Dirty: Save+Cancel on, Sign off; signed badge flips.
    script = """
<script>
const fields = document.getElementById("edit-fields");
const banner = document.getElementById("unsaved");
const save = document.getElementById("save-req");
const cancel = document.getElementById("cancel-edit");
const sign = document.getElementById("sign-open");
const testDiscovery = document.getElementById("try-discovery-open");
const seal = document.getElementById("seal-status");
function markDirty() {
  if (banner) banner.hidden = false;
  if (save) save.disabled = false;
  if (cancel) cancel.hidden = false;
  if (sign) sign.disabled = true;
  if (testDiscovery) testDiscovery.disabled = true;
  if (seal && seal.dataset.wasSigned === "1") {
    seal.innerHTML =
      '<button type="button" class="sign-bad" disabled>unsigned</button>';
    seal.dataset.wasSigned = "0";
  }
}
if (cancel) {
  cancel.addEventListener("click", () => { location.reload(); });
}
if (fields) {
  fields.addEventListener("input", (event) => {
    markDirty();
    if (event.target && event.target.classList) event.target.classList.remove("invalid");
  });
  fields.addEventListener("change", markDirty);
  const firstBad = fields.querySelector("input.invalid, textarea.invalid");
  if (firstBad) firstBad.focus();
}
</script>
"""
    sign_btn = "" if signed else '<button type="button" id="sign-open">Sign</button>'
    sign_ui = "" if signed else _sign_dialog(requirement, model)
    status = _seal_status_badge(model.get("reading"))
    from studio.claim.try_discovery import dialog_html

    try_model = {
        "requirement_id": requirement.get("id"),
        "repos": model.get("repos") or [],
        "try_repo_id": model.get("try_repo_id") or "",
        "try_assess_limit": model.get("try_assess_limit") or 5,
        "try_candidates": model.get("try_candidates") or [],
        "discovery_hints": requirement.get("discovery_hints") or {},
        "try_open": bool(model.get("try_open")),
        "try_ran": bool(model.get("try_ran")),
        "try_error": model.get("try_error") or "",
        "try_job": model.get("try_job"),
        "workspace_root": model.get("workspace_root") or "",
        "repo_id": model.get("repo_id") or "",
        "bound_pack": model.get("bound_pack") or "",
        "law_passages": [
            {"locator": ref.get("locator"), "law_text": ref.get("law_text")}
            for ref in (requirement.get("references") or [])
            if isinstance(ref, dict)
        ],
    }
    body = f"""
<p class="muted"><a href="/requirements">Pack Sources</a>
 · <a href="{html.escape(str(model.get("list_href") or "/requirements/copy"))}">Requirements list</a></p>
<div class="req-head">
<h1>{html.escape(str(requirement.get("id")))}</h1>
{status}
</div>
{_copy_line(model, requirement)}
{_identity_lines(model, requirement)}
{flash}
{affected}
{ownership}
{banner}
<form method="post" action="/requirements/requirement/{html.escape(str(requirement.get("id")))}">
<fieldset id="edit-fields">
{references}
{fields}
{_source_fields(source, invalid)}
{_hint_fields(hints)}
<input type="hidden" name="expected_digest" value="{html.escape(str(model.get("expected_digest") or ""))}">
{_working_copy_identity(model)}
{_bound_pack_fields(model)}
</fieldset>
<p class="actions editor-actions">
<button type="submit" id="save-req" disabled>Save</button>
<button type="button" id="cancel-edit" class="secondary" hidden>Cancel</button>
<button type="button" id="try-discovery-open">Test discovery</button>
{sign_btn}
</p>
</form>
{sign_ui}
{dialog_html(try_model)}
{script}
"""
    return page(str(requirement.get("id")), body)


def job_fragment(job: dict, *, document_id: str = "") -> bytes:
    job_id = str(job.get("job_id") or "")
    status = str(job.get("status") or "")
    lines = "\n".join(html.escape(str(line)) for line in (job.get("log_tail") or []))
    activity = str(job.get("activity") or job.get("stage") or "")
    error = str(job.get("error") or "")
    error_html = f'<p id="job-error" class="err">{html.escape(error)}</p>' if error else '<p id="job-error"></p>'
    back = f"/requirements?document={document_id}" if document_id else "/requirements"
    document_field = (
        f'<input type="hidden" name="document" value="{html.escape(document_id)}">'
        if document_id
        else ""
    )
    abort = ""
    if status == "running":
        abort = (
            f'<form id="job-abort" method="post" action="/requirements/jobs/{html.escape(job_id)}/abort">'
            f"{document_field}"
            '<button type="submit">Abort</button></form>'
        )
    close_hidden = "" if status == "failed" else " hidden"
    html_text = f"""
<dialog id="job" open data-status="{html.escape(status)}" data-job-id="{html.escape(job_id)}" data-poll="/requirements/jobs/{html.escape(job_id)}">
<div class="head"><h2>Extraction</h2></div>
<div class="body">
<p>Status <strong id="job-status">{html.escape(status)}</strong></p>
<p id="job-activity">{html.escape(activity)}</p>
<pre id="job-log" class="log">{lines}</pre>
{error_html}
{abort}
<p><a id="job-close" href="{html.escape(back)}"{close_hidden}>Close</a></p>
</div>
</dialog>
<script>
const back = {json.dumps(back)};
const dialog = document.getElementById("job");
dialog.addEventListener("cancel", (event) => {{
  if (dialog.dataset.status === "running") event.preventDefault();
}});
dialog.addEventListener("click", (event) => {{
  if (event.target === dialog) event.preventDefault();
}});
function showJob(job) {{
  dialog.dataset.status = job.status || "";
  document.getElementById("job-status").textContent = job.status || "";
  document.getElementById("job-activity").textContent = job.activity || job.stage || "";
  document.getElementById("job-log").textContent = (job.log_tail || []).join("\\n");
  const error = document.getElementById("job-error");
  error.textContent = job.error || "";
  error.className = job.error ? "err" : "";
  const closeButton = document.getElementById("job-close");
  const abortForm = document.getElementById("job-abort");
    if (job.status === "done") {{
    if (job.section_extract && job.dest_pack && job.section_id) {{
      let review = "/requirements/copy?pack=" + encodeURIComponent(job.dest_pack)
        + "&section=" + encodeURIComponent(job.section_id);
      if (job.dest_repo) review += "&repo=" + encodeURIComponent(job.dest_repo);
      location.assign(review);
    }} else if (job.dest_pack && job.copy_timestamp) {{
      let review = "/requirements/copy?proposal=" + encodeURIComponent(job.copy_timestamp)
        + "&pack=" + encodeURIComponent(job.dest_pack);
      if (job.dest_repo) review += "&repo=" + encodeURIComponent(job.dest_repo);
      location.assign(review);
    }} else if (job.base_timestamp && job.copy_timestamp) {{
      location.assign(
        "/requirements/copy?proposal=" + encodeURIComponent(job.copy_timestamp)
        + "&destination=" + encodeURIComponent(job.base_timestamp)
      );
    }} else {{
      location.assign(back + (back.indexOf("?") >= 0 ? "&" : "?") + "extracted=1");
    }}
    return;
  }}
  if (job.status === "aborted") {{
    location.assign(back + (back.indexOf("?") >= 0 ? "&" : "?") + "aborted=1");
    return;
  }}
  if (job.status === "failed") {{
    closeButton.hidden = false;
    if (abortForm) abortForm.hidden = true;
    return;
  }}
  setTimeout(pollJob, 500);
}}
async function pollJob() {{
  const response = await fetch(dialog.dataset.poll);
  showJob(await response.json());
}}
if (dialog.dataset.status === "running" || dialog.dataset.status === "done") pollJob();
else showJob({{status: dialog.dataset.status, activity: document.getElementById("job-activity").textContent, log_tail: document.getElementById("job-log").textContent.split("\\n"), error: document.getElementById("job-error").textContent}});
</script>
"""
    return html_text.encode("utf-8")


# UI label text (human). JSON field names stay on name=/present=.
_FIELD_LABELS: dict[str, str] = {
    "note": "Note",
    "remediation_hint": "Remediation hint",
    "strength": "Strength",
    "responsible": "Responsible",
    "applicability": "Applicability",
    "exceptions": "Exceptions",
    "scope": "Scope",
    "framework": "Framework",
    "instrument": "Instrument",
    "identifier": "Identifier",
    "edition": "Edition",
    "language": "Language",
    "url": "URL",
    "concepts": "Concepts",
    "path_hints": "Path hints",
    "expected_evidence": "Expected evidence",
    "sources": "Sources",
    "locator": "Locator",
    "law_text": "Law text",
}

# Short packs2-faithful hints + grey placeholder examples for the editor.
_FIELD_HELP: dict[str, tuple[str, str]] = {
    "note": (
        "Optional reading note. Not a second law text, and not applicability.",
        "Hardware photos only apply when the product is hardware.",
    ),
    "remediation_hint": (
        "Publisher advice to the product team. Part of the sealed requirement.",
        "Add a product-specific risk assessment (no placeholders).",
    ),
    "strength": (
        "MUST, SHOULD, or MAY — only when that word is in law_text. Leave empty otherwise.",
        "MUST",
    ),
    "responsible": (
        "Who the duty names in law_text. Leave empty when the party is not pointable there.",
        "manufacturer",
    ),
    "applicability": (
        "The “where …” clause in law_text. Leave empty when there is none.",
        "where the product with digital elements is a hardware product",
    ),
    "exceptions": (
        "Exception written in law_text. Leave empty when the passage has none.",
        "except where …",
    ),
    "scope": (
        "Enumeration sliced from law_text. Leave empty when there is no list to lift out.",
        "risk analysis and information system security",
    ),
    "framework": ("Legal or policy framework for this cut.", "EU"),
    "instrument": ("Instrument short name, repeated so the seal still names the act.", "CRA"),
    "identifier": ("Act id the human looked up (not pack.version).", "CELEX:32024R2847"),
    "edition": ("OJ or consolidation date used for this cut. Part of the seal.", "2024-11-20"),
    "language": ("Language of law_text on this requirement.", "en"),
    "url": ("The one address these passages were cut from.", "https://eur-lex.europa.eu/…"),
    "concepts": ("Search terms for discovery. One per line.", "risk assessment"),
    "path_hints": ("Filename globs for discovery. One per line.", "*risk*assessment*"),
    "expected_evidence": (
        "Kind of artifact to look for. One per line. Not proof by itself.",
        "process description",
    ),
    "sources": (
        "Packs v2 discovery source objects (JSON). check does not read these.",
        '[{"source":"documents"}]',
    ),
    "locator": (
        "Where in the source the law text below is found.",
        "VII.3",
    ),
    "law_text": (
        "Direct quote clipped from the source. Everything below must be derived from this text.",
        "an assessment of the cybersecurity risks…",
    ),
}


def _field_label(key: str) -> str:
    return _FIELD_LABELS.get(key, key.replace("_", " ").capitalize())


def _info_tip(text: str) -> str:
    """Visible hover tip — native title tooltips often fail in the preview browser."""
    if not text:
        return ""
    return (
        f'<span class="field-info" tabindex="0" aria-label="{html.escape(text)}">'
        f'ⓘ<span class="tip">{html.escape(text)}</span></span>'
    )


def _labeled_input(
    *,
    name: str,
    value: str,
    help_key: str,
    kind: str = "text",
    css_class: str = "",
    title: str | None = None,
    invalid: bool = False,
) -> str:
    label = title if title is not None else _field_label(help_key)
    hint, placeholder = _FIELD_HELP.get(help_key, ("", ""))
    tip = f" {_info_tip(hint)}" if hint else ""
    ph = f' placeholder="{html.escape(placeholder)}"' if placeholder else ""
    class_attr = f' class="{html.escape(css_class)}"' if css_class else ""
    control_class = ' class="invalid"' if invalid else ""
    if kind == "textarea":
        control = (
            f'<textarea name="{html.escape(name)}"{control_class}{ph}>'
            f"{html.escape(value)}</textarea>"
        )
    else:
        control = (
            f'<input type="text" name="{html.escape(name)}" '
            f'value="{html.escape(value)}"{control_class}{ph}>'
        )
    return f"<label{class_attr}>{html.escape(label)}{tip}{control}</label>"


def _scalars(requirement: dict, invalid_fields: set[str] | None = None) -> str:
    bad = invalid_fields or set()
    wide = []
    for field in ("note", "remediation_hint"):
        value = requirement.get(field) or ""
        wide.append(
            f'<input type="hidden" name="present" value="{field}">'
            + _labeled_input(
                name=field,
                value=str(value),
                help_key=field,
                invalid=field in bad,
            )
        )
    compact = []
    for field in ("strength", "responsible", "applicability", "exceptions", "scope"):
        value = requirement.get(field) or ""
        compact.append(
            f'<input type="hidden" name="present" value="{field}">'
            + _labeled_input(
                name=field,
                value=str(value),
                help_key=field,
                invalid=field in bad,
            )
        )
    return "".join(wide) + f'<div class="field-grid">{"".join(compact)}</div>'


def _source_fields(source: dict, invalid_fields: set[str] | None = None) -> str:
    bad = invalid_fields or set()
    compact = []
    for field in ("framework", "instrument", "identifier", "edition", "language"):
        value = source.get(field) or ""
        compact.append(
            f'<input type="hidden" name="present" value="{field}">'
            + _labeled_input(
                name=field,
                value=str(value),
                help_key=field,
                invalid=field in bad,
            )
        )
    url = str(source.get("url") or "")
    url_field = (
        f'<input type="hidden" name="present" value="url">'
        + _labeled_input(
            name="url",
            value=url,
            help_key="url",
            css_class="span-2",
            invalid="url" in bad,
        )
    )
    link = ""
    if url:
        link = (
            f'<p class="muted">Source link '
            f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(url)}</a></p>'
        )
    return f'<div class="field-grid">{"".join(compact)}{url_field}</div>{link}'


def _hint_fields(hints: dict) -> str:
    row = []
    for field in ("concepts", "expected_evidence", "path_hints"):
        text = "\n".join(str(item) for item in (hints.get(field) or []))
        row.append(
            f'<input type="hidden" name="present" value="{field}">'
            + _labeled_input(
                name=field,
                value=text,
                help_key=field,
                kind="textarea",
            )
        )
    # Keep sources in the form so round-trips do not drop it; hide until the UI uses it.
    sources = json.dumps(hints.get("sources") or [], indent=2)
    sources_field = (
        f'<input type="hidden" name="present" value="sources">'
        f'<textarea name="sources" hidden>{html.escape(sources)}</textarea>'
    )
    return f'<div class="field-grid hint-grid">{"".join(row)}</div>{sources_field}'


def _references(references: list) -> str:
    # Passages are extract output: read-only in the editor. Not posted, so Save
    # cannot rewrite them. nr is hidden until multi-reference editing returns.
    if not references:
        return '<p class="muted">No source references.</p>'
    rows = ['<div class="ref-list">']
    for ref in references:
        locator = html.escape(str(ref.get("locator") or ""))
        law_text = html.escape(str(ref.get("law_text") or ""))
        tip_locator, _ = _FIELD_HELP.get("locator", ("", ""))
        tip_law, _ = _FIELD_HELP.get("law_text", ("", ""))
        rows.append(
            '<div class="card ref-block">'
            f'<h3 class="ref-heading"><code>{locator}</code>'
            f"{_info_tip(tip_locator) if tip_locator else ''}</h3>"
            f'<div class="ref-law-head muted">Law text'
            f"{_info_tip(tip_law) if tip_law else ''}</div>"
            f'<pre class="ref-law">{law_text}</pre>'
            "</div>"
        )
    rows.append("</div>")
    return "".join(rows)


def _reading_block(title: str, reading: dict | None) -> str:
    if not isinstance(reading, dict):
        return f"<p>{html.escape(title)}: no reading.</p>"
    who = str(reading.get("who") or "").strip()
    when = str(reading.get("when") or "").strip()
    reason = str(reading.get("reason") or "").strip()
    label = html.escape(title)
    if reading.get("verifiable") and who:
        when_bit = f" at {html.escape(when)}" if when else ""
        return (
            f'<p><strong>{label}</strong> · '
            f"Signed by {html.escape(who)}{when_bit}</p>"
        )
    if who:
        why = reason
        for noise in (
            "No signed block and no signed Git commit. The object is unsigned.",
            "The object is unsigned.",
        ):
            if why == noise:
                why = ""
                break
        suffix = f" — {html.escape(why)}" if why else " — not verifiable"
        return (
            f'<p class="err"><strong>{label}</strong> · '
            f"Signed by {html.escape(who)}{suffix}</p>"
        )
    return f'<p class="err"><strong>{label}</strong> · Unsigned</p>'


def _seal_status_badge(reading: dict | None) -> str:
    """Compact signed/unsigned control for the editor action row.

    Display only. Editing any field marks the form dirty; Save clears the seal.
    """
    wrap_open = '<span id="seal-status"'
    if not isinstance(reading, dict):
        return (
            f'{wrap_open} data-was-signed="0">'
            '<button type="button" class="sign-bad" disabled>unsigned</button></span>'
        )
    who = str(reading.get("who") or "").strip()
    when = str(reading.get("when") or "").strip()
    who_bit = f' <span class="muted">{html.escape(who)}</span>' if who else ""
    if reading.get("verifiable") and who:
        when_bit = f" at {when}" if when else ""
        tip = html.escape(f"Signed by {who}{when_bit}. Change a field and Save to clear the seal.")
        return (
            f'{wrap_open} data-was-signed="1">'
            f'<button type="button" class="sign-ok" disabled title="{tip}">signed</button>'
            f"{who_bit}</span>"
        )
    if who:
        tip = html.escape(str(reading.get("reason") or "not verifiable"))
        return (
            f'{wrap_open} data-was-signed="0">'
            f'<button type="button" class="sign-bad" disabled title="{tip}">not verified</button>'
            f"{who_bit}</span>"
        )
    return (
        f'{wrap_open} data-was-signed="0">'
        '<button type="button" class="sign-bad" disabled>unsigned</button></span>'
    )


def _sign_dialog(requirement: dict, model: dict) -> str:
    """Dialog + wiring only. The Sign button lives in the editor action row."""
    action = "Approve and sign" if "origin" in requirement else "Sign"
    return (
        '<dialog id="sign-dialog">'
        '<div class="head"><h2>Sign requirement</h2>'
        '<button type="button" id="sign-cancel" class="secondary">Cancel</button></div>'
        '<div class="body">'
        f'<form method="post" action="/requirements/requirement/{html.escape(str(requirement.get("id")))}/sign">'
        f'<input type="hidden" name="expected_digest" value="{html.escape(str(model.get("expected_digest") or ""))}">'
        f"{_bound_pack_fields(model)}"
        '<label>Name<input type="text" name="name" required></label>'
        f'<p><button type="submit">{action}</button></p></form>'
        "</div></dialog>"
        "<script>"
        'const signDialog = document.getElementById("sign-dialog");'
        'document.getElementById("sign-open").addEventListener("click", () => signDialog.showModal());'
        'document.getElementById("sign-cancel").addEventListener("click", () => signDialog.close());'
        'signDialog.addEventListener("cancel", (event) => { event.preventDefault(); signDialog.close(); });'
        "</script>"
    )
