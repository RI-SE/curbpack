"""HTML for the demo. Renders values it is given and does not decide them."""

from __future__ import annotations

import html
import json
import re
from urllib.parse import quote

from checks.labels import check_caption
from review.compile import NO_CRA_FIELD, NOT_A_LEGAL_CONCLUSION, worktree_sentence

CSS = """
:root{--bg:#eef2f7;--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--accent:#0f766e;--ok:#15803d;--bad:#b91c1c}
*{box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,sans-serif;margin:0;background:var(--bg);color:var(--ink);line-height:1.45}
main{max-width:1100px;margin:0 auto;padding:1.5rem 1.25rem 3rem}
h1{font-size:1.5rem;margin:0 0 .35rem}
a{color:var(--accent)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;margin:.75rem 0}
.muted{color:var(--muted)}
.err{background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:.6rem .75rem;border-radius:8px}
.ok{background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46;padding:.6rem .75rem;border-radius:8px}
.coverage-written{color:#065f46}
.coverage-excluded{color:#9a3412;background:#fff7ed;padding:.15rem .35rem;border-radius:4px}
.coverage-failed{color:#991b1b;background:#fef2f2;padding:.15rem .35rem;border-radius:4px}
label{display:block;font-size:.78rem;color:var(--muted);margin:.6rem 0 .2rem}
.field-info{position:relative;display:inline-block;margin-left:.25rem;color:var(--muted);cursor:help;font-size:.85em;line-height:1;vertical-align:middle}
.field-info:hover,.field-info:focus{color:var(--ink)}
.field-info .tip{display:none;position:absolute;z-index:20;left:0;top:1.25rem;width:min(22rem,70vw);padding:.75rem .85rem;background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:8px;font-size:.85rem;font-weight:400;line-height:1.4;white-space:normal;box-shadow:0 8px 24px rgba(0,0,0,.08)}
.field-info:hover .tip,.field-info:focus .tip{display:block}
.field-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(11rem,1fr));gap:.55rem .75rem;margin:.65rem 0}
.ro-field{font-size:.78rem;color:var(--muted)}
.ro-field strong,.ro-field a{display:block;margin-top:.15rem;font-size:1rem;font-weight:700;color:var(--ink)}
.ro-field a{font-weight:400;color:var(--accent);word-break:break-all}
.identity-bar{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem}
.req-identity .identity-bar .field-grid{flex:1;margin:0 0 .75rem;grid-template-columns:repeat(3,max-content);justify-content:start}
a.details{display:inline-block;background:#fff;color:var(--accent);border:1px solid var(--accent);border-radius:6px;padding:.45rem .75rem;text-decoration:none;white-space:nowrap}
a.details:hover{background:#ecfdf5}
.req-identity .ref-law{margin:0 0 .75rem}
.req-identity .law-flow{white-space:normal;font-family:inherit;font-size:1rem;line-height:1.35}
.field-grid label{margin:0}
.field-grid label.span-2{grid-column:span 2}
.hint-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
@media (max-width:900px){.hint-grid{grid-template-columns:1fr}}
@media (max-width:640px){.field-grid label.span-2{grid-column:span 1}}
.hint-grid textarea{min-height:7.5rem}
.ref-list{margin:.65rem 0 1rem}
.card.ref-block{background:#f8fafc;cursor:default}
.ref-heading{margin:0 0 .45rem;font-size:.95rem;font-weight:600;color:var(--ink)}
.ref-law-head{margin:0 0 .25rem;font-size:.78rem}
.ref-law{margin:0;white-space:pre-wrap;font-family:ui-monospace,Menlo,monospace;font-size:.85rem;line-height:1.4;color:var(--ink);background:transparent;border:0;padding:0}
input[type=text],textarea{width:100%;font:inherit;padding:.4rem .5rem;border:1px solid #cbd5e1;border-radius:6px}
input::placeholder,textarea::placeholder{color:#94a3b8;opacity:1}
textarea{min-height:6rem;font-family:ui-monospace,Menlo,monospace;font-size:.85rem}
button{font:inherit;background:#0f766e;color:#fff;border:0;border-radius:6px;padding:.45rem .75rem;cursor:pointer}
button.sign-ok,button.sign-bad{padding:.12rem .45rem;font-size:.75rem;line-height:1.2;border-radius:4px;font-weight:600;vertical-align:middle}
button.sign-ok{background:var(--ok);border-color:var(--ok);color:#fff}
button.sign-bad{background:var(--bad);border-color:var(--bad);color:#fff}
nav a{margin-right:.8rem}
table{width:100%;border-collapse:collapse;font-size:.92rem}
th,td{text-align:left;padding:.4rem;border-bottom:1px solid var(--line);vertical-align:top}
code{font-family:ui-monospace,Menlo,monospace;font-size:.86em}
button:disabled,button[disabled]{opacity:.45;cursor:not-allowed}
button.sign-ok:disabled,button.sign-bad:disabled{opacity:1;cursor:default}
button.secondary{background:#fff;color:var(--accent);border:1px solid var(--accent)}
button.secondary:hover{background:#ecfdf5}
.actions{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center}
.actions form{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center}
.editor-actions{margin-top:.85rem;align-items:center}
.editor-actions dialog{position:fixed}
.editor-actions button{padding:.45rem .75rem;font-size:inherit;line-height:1.2;border-radius:6px}
.editor-actions button.sign-ok,.editor-actions button.sign-bad{font-weight:600}
.pill{display:inline-block;font-size:.75rem;border:1px solid var(--line);border-radius:999px;padding:.05rem .45rem;margin-left:.25rem}
.pill-ok{background:#ecfdf5;color:#065f46}
.pill-bad{background:#fef2f2;color:#991b1b}
dialog{border:1px solid var(--line);border-radius:12px;padding:0;max-width:36rem;width:calc(100% - 2rem)}
dialog.try-discovery{max-width:min(56rem,calc(100% - 2rem))}
dialog.try-discovery .body{max-height:70vh;overflow:auto}
dialog.review-discover{max-width:min(72rem,calc(100% - 2rem));width:calc(100% - 2rem)}
dialog.review-discover iframe{width:100%;height:70vh;border:1px solid var(--line);border-radius:8px;background:#fff}
dialog.discover-job{max-width:42rem}
.progress{height:10px;background:#e2e8f0;border-radius:999px;overflow:hidden;margin:.75rem 0}
.progress>span{display:block;height:100%;background:#0f766e}
dialog::backdrop{background:rgba(15,23,42,.45)}
dialog .head,dialog .body{padding:1rem 1.1rem}
dialog .head{display:flex;justify-content:space-between;gap:1rem;align-items:center;border-bottom:1px solid var(--line)}
dialog h2{margin:0;font-size:1.05rem}
pre.log{max-height:16rem;overflow:auto;background:#0f172a;color:#e2e8f0;padding:.75rem;border-radius:8px;font-size:.78rem;white-space:pre-wrap}
select{font:inherit;max-width:18rem;padding:.35rem .4rem;border:1px solid #cbd5e1;border-radius:6px}
a.edit-review{display:inline-block;background:#16a34a;color:#fff;text-decoration:none;border-radius:6px;padding:.45rem .75rem;font-weight:600}
a.edit-review:hover{background:#15803d;color:#fff}
a.edit-review[hidden]{display:none}
.repo-row{display:flex;flex-wrap:wrap;align-items:center;gap:.75rem 1rem;margin:0 0 .75rem}
.repo-row .repo-picker{margin:0}
.repo-row .repo-picker label{display:flex;align-items:center;gap:.5rem;margin:0}
.repo-row .actions{margin:0}
.config-panel{background:transparent;border:1px solid #cbd5e1;border-radius:10px;padding:.85rem 1rem;margin:.25rem 0 .75rem}
.config-panel .repo-row{margin-bottom:.35rem}
.config-panel label{margin:.45rem 0 0}
.config-panel input[readonly]{background:#fff;color:var(--ink);cursor:text}
.discover-wrap .repo-picker{margin:0 0 .75rem}
.discover-wrap table{width:100%}
.discover-wrap .path-cell{max-width:14rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.discover-wrap select.copy-select{max-width:16rem}
.discover-wrap th.num,.discover-wrap td.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.discover-wrap th.num.wrap{white-space:normal;line-height:1.2;max-width:6.5rem}
body:has(.req-desk) main{max-width:min(1400px,100%)}
.req-head{display:flex;flex-wrap:wrap;gap:.75rem 1.25rem;align-items:center;justify-content:space-between;margin:0 0 .35rem}
.req-head h1{margin:0;flex:1;min-width:12rem}
.req-head #seal-status{flex-shrink:0}
.req-head #seal-status button{cursor:default}
.req-badges{display:flex;align-items:center;gap:.6rem}
.seal{display:inline-block;font-weight:600;border-radius:6px;padding:.35rem .75rem}
.seal-ok{background:#15803d;color:#fff}
.seal-open{background:#fff;color:#44403c;border:1px solid #d6d3d1}
.law{background:#fff;border-left:4px solid #1c1917;padding:.9rem 1.1rem;white-space:pre-wrap;border-radius:0 8px 8px 0}
.hits{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:auto;margin:.75rem 0}
.hits-table{width:100%;border-collapse:collapse;font-size:.92rem}
.hits-table thead th{background:#fafaf9;padding:.65rem .75rem;border-bottom:1px solid var(--line);font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.hits-table td{padding:.7rem .75rem;border-bottom:1px solid var(--line);vertical-align:middle}
.hits-table tr.hit-row{cursor:pointer}
.hits-table tr.hit-row:hover{background:#fafaf9}
.hits-table tr.hit-row.open{background:#f5f5f4}
.hits-table tr.hit-row.vote-useful{box-shadow:inset 3px 0 0 #15803d}
.hits-table tr.hit-row.vote-poor{box-shadow:inset 3px 0 0 #b91c1c}
.hits-table tr.hit-row.covered{color:#64748b;background:#f8fafc}
.hits-table tr.hit-row.covered a{color:#64748b}
.covered-note{margin:.25rem 0 0;font-size:.75rem;color:#64748b}
.hits-table .col-file{width:22%;word-break:break-all}
.hits-table .col-score{white-space:nowrap}
.score-help{position:relative;display:inline-block;text-transform:none;letter-spacing:0;font-weight:600;cursor:help;border-bottom:1px dotted var(--muted)}
.score-help .tip{display:none;position:absolute;z-index:5;left:0;top:1.4rem;width:22rem;padding:.75rem .85rem;background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:8px;font-size:.85rem;line-height:1.4;text-transform:none;letter-spacing:0;font-weight:400;white-space:normal;box-shadow:0 8px 24px rgba(0,0,0,.08)}
.score-help:hover .tip,.score-help:focus .tip{display:block}
.hits-table .col-why{width:42%}
.hits-table .col-vote{text-align:right;white-space:nowrap}
.hits-table .col-toggle{width:2rem;color:var(--muted);user-select:none}
.hits-table tr.detail-row td{padding:0;background:#fafaf9}
.hits-table tr.detail-row[hidden]{display:none}
.hits-table .detail-inner{padding:.85rem 1rem 1rem 2.4rem}
.hits-table .why-cell{line-height:1.35}
label.show-suggestions{display:flex;align-items:center;gap:.4rem;margin:.75rem 0 .35rem;font-size:.92rem}
.hits-table tr.suggestion-row,.hits-table .suggestion{display:none}
.hits-table.show-suggestions tr.suggestion-row{display:table-row}
.hits-table.show-suggestions .suggestion{display:block}
.hits-table.show-suggestions .motivation-current.has-suggestion{display:none}
form.motivation-pick{margin:0}
button.motivation-old,button.motivation-new{display:block;width:100%;margin:0;padding:0;background:none;border:0;font:inherit;line-height:1.35;text-align:left;cursor:pointer;white-space:normal}
button.motivation-old{margin-bottom:.35rem;color:#b91c1c;text-decoration:line-through}
button.motivation-new{color:#15803d}
button.motivation-old:hover{text-decoration:line-through underline}
button.motivation-new:hover{text-decoration:underline}
.rank-High{color:#15803d;font-weight:700}
.rank-Medium{color:#a16207;font-weight:700}
.rank-Low,.rank-None{color:#78716c}
.check-chip{display:inline-block;background:#e7e5e4;border-radius:4px;padding:.1rem .35rem;margin:.1rem .15rem .1rem 0;font-size:.78rem}
button.check-pick{background:#fff;color:#44403c;border:1px solid #d6d3d1;font-size:.8rem;padding:.3rem .55rem}
.hits-table tr.add-row td{border-bottom:0;padding:.55rem .75rem;background:#fafaf9}
button.add-open{background:#fff;color:var(--accent);border:1px dashed #99f6e4;font-size:1.1rem;line-height:1;padding:.25rem .7rem;font-weight:600}
button.add-open:hover{background:#ecfdf5}
dialog.checks [hidden]{display:none}
input.invalid,textarea.invalid{border:1px solid #b91c1c;background:#fef2f2}
dialog.checks input.invalid{border:1px solid #b91c1c;background:#fef2f2}
dialog.checks button.save-check{background:#15803d}
dialog.checks label.check-inline{display:flex;align-items:center;gap:.4rem;color:var(--ink)}
dialog.checks label.check-inline input{width:auto}
.votes form{display:inline}
button.up,button.down{background:#fff;font-weight:600}
button.up{border:1px solid #86efac;color:#166534}
button.down{border:1px solid #fca5a5;color:#991b1b}
button.up.selected{background:#15803d;border-color:#15803d;color:#fff}
button.down.selected{background:#b91c1c;border-color:#b91c1c;color:#fff}
pre.excerpt{background:#fafaf9;border:1px solid var(--line);padding:.85rem 1rem;overflow:auto;border-radius:8px;white-space:pre-wrap}
"""


def page(title: str, body: str) -> bytes:
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body><main>
<p><a href="/">Home</a> <span class="muted">· Curbpack Studio. Turn law into checkable packs.</span></p>
{body}
</main></body></html>"""
    return doc.encode("utf-8")


def progress_dialog(
    job: dict,
    *,
    poll: str,
    dismiss: str,
    done_href: str = "",
    dialog_id: str = "job",
    note: str = "",
) -> str:
    """One black log + progress bar popup. Callers only supply dismiss and poll URL."""
    status = str(job.get("status") or "")
    title = str(job.get("title") or "Job")
    activity = str(job.get("activity") or "")
    error = str(job.get("error") or "")
    try:
        width = max(0, min(100, round(float(job.get("progress") or 0) * 100)))
    except (TypeError, ValueError):
        width = 0
    lines = "\n".join(html.escape(str(line)) for line in (job.get("log_tail") or []))
    error_html = (
        f'<p id="{html.escape(dialog_id)}-error" class="err">{html.escape(error)}</p>'
        if error
        else f'<p id="{html.escape(dialog_id)}-error"></p>'
    )
    done_attr = f' data-done="{html.escape(done_href)}"' if done_href else ""
    return f"""
<dialog id="{html.escape(dialog_id)}" class="discover-job" data-status="{html.escape(status)}"
 data-poll="{html.escape(poll)}"{done_attr}>
<div class="head"><h2>{html.escape(title)}</h2>{dismiss}</div>
<div class="body">
<p id="{html.escape(dialog_id)}-activity">{html.escape(activity)}</p>
<div class="progress" aria-hidden="true"><span id="{html.escape(dialog_id)}-bar" style="width:{width}%"></span></div>
<pre id="{html.escape(dialog_id)}-log" class="log">{lines}</pre>
{error_html}
{note}
</div>
</dialog>
<script>
(function () {{
  const dialog = document.getElementById({json.dumps(dialog_id)});
  if (!dialog) return;
  dialog.showModal();
  dialog.addEventListener("cancel", (event) => {{
    if (dialog.dataset.status === "running") event.preventDefault();
  }});
  const prefix = {json.dumps(dialog_id)};
  function showJob(job) {{
    const wasRunning = dialog.dataset.status === "running";
    dialog.dataset.status = job.status || "";
    document.getElementById(prefix + "-activity").textContent = job.activity || "";
    document.getElementById(prefix + "-log").textContent = (job.log_tail || []).join("\\n");
    document.getElementById(prefix + "-bar").style.width =
      Math.max(0, Math.min(100, Math.round((job.progress || 0) * 100))) + "%";
    const error = document.getElementById(prefix + "-error");
    error.textContent = job.error || "";
    error.className = job.error ? "err" : "";
    if (wasRunning && job.status && job.status !== "running") {{
      if (dialog.dataset.done) location.href = dialog.dataset.done;
      else location.reload();
    }} else if (job.status === "running") {{
      setTimeout(pollJob, 400);
    }}
  }}
  async function pollJob() {{
    showJob(await (await fetch(dialog.dataset.poll)).json());
  }}
  if (dialog.dataset.status === "running") pollJob();
}})();
</script>
"""


def _flash(message: str, error: str) -> str:
    if error:
        return f'<p class="err">{html.escape(error)}</p>'
    if message:
        return f'<p class="ok">{html.escape(message)}</p>'
    return ""


def _reading(reading: dict | None) -> str:
    if not reading:
        return "<p class=\"muted\">No signature reading.</p>"
    who = reading.get("who") or "—"
    when = reading.get("when") or "—"
    verified = "yes" if reading.get("verifiable") else "no"
    reason = reading.get("reason") or ""
    text = (
        f"<p><strong>{html.escape(str(reading.get('what')))}</strong> · "
        f"who {html.escape(str(who))} · when {html.escape(str(when))} · "
        f"verifiable {verified}</p>"
        f"<p class=\"muted\">version <code>{html.escape(str(reading.get('version')))}</code></p>"
    )
    if reason:
        text += f"<p class=\"muted\">{html.escape(reason)}</p>"
    return text


def cover(_model: dict, message: str = "", error: str = "") -> bytes:
    body = f"""
<h1>Curbpack Studio</h1>
<p class="muted">Curbpack Studio turns law text into checkable requirements, grouped in packs.
The pilot workflow: author packs from law text → create claims in your product →
check regularly → review the result and fix what failed.</p>
{_flash(message, error)}
<div class="card">
<p><a href="/requirements">Pack Editor</a></p>
<p><a href="/discover">Discovery &amp; Claims — find candidates, configure checks, create Claims</a></p>
<p><a href="/check">Check — authoritative pack via curbpack.json</a></p>
<p><a href="/review">Review — compile and sign review</a></p>
</div>
"""
    return page("Curbpack Studio", body)


def _lines(values) -> str:
    if not values:
        return ""
    return "\n".join(str(item) for item in values)


def requirement_page(requirement: dict, reading: dict, message: str = "", error: str = "") -> bytes:
    source = requirement.get("source") or {}
    hints = requirement.get("discovery_hints") or {}
    law = ""
    locator = ""
    if requirement.get("references"):
        law = requirement["references"][0].get("law_text") or ""
        locator = requirement["references"][0].get("locator") or ""
    sources = "\n".join(item.get("source", "") for item in (hints.get("sources") or []) if isinstance(item, dict))
    body = f"""
<h1>{html.escape(requirement.get('id', 'Requirement'))}</h1>
{_flash(message, error)}
{_reading(reading)}
<div class="card">
<p>Locator <code>{html.escape(locator)}</code></p>
<pre>{html.escape(law)}</pre>
</div>
<form method="post" action="/requirement">
<label>Edition</label>
<input type="text" name="edition" value="{html.escape(source.get('edition', ''))}">
<label>Remediation hint</label>
<textarea name="remediation_hint">{html.escape(requirement.get('remediation_hint', ''))}</textarea>
<label>Note</label>
<textarea name="note">{html.escape(requirement.get('note', ''))}</textarea>
<label>Concepts</label>
<textarea name="concepts">{html.escape(_lines(hints.get('concepts')))}</textarea>
<label>Path hints</label>
<textarea name="path_hints">{html.escape(_lines(hints.get('path_hints')))}</textarea>
<label>Source ids (one per line, no args)</label>
<textarea name="sources">{html.escape(sources)}</textarea>
<label>Expected evidence</label>
<textarea name="expected_evidence">{html.escape(_lines(hints.get('expected_evidence')))}</textarea>
<button type="submit">Save draft</button>
</form>
<form method="post" action="/publish">
<label>Signer name</label>
<input type="text" name="name" placeholder="Ada Jurist">
<button type="submit">Publish and sign</button>
</form>
<form method="post" action="/seal-pack">
<label>Pack sealer name</label>
<input type="text" name="name" placeholder="Ada Jurist">
<button type="submit">Seal pack directory</button>
</form>
<p class="muted">Saving a change drops any previous signature. Publishing refuses a local working copy that already has origin.</p>
"""
    return page(requirement.get("id", "Requirement"), body)


def claims_page(model: dict, message: str = "", error: str = "") -> bytes:
    """Claims editor. Domain logic stays in claims.bind / server helpers."""
    blocks = []
    for item in model.get("claims") or []:
        claim = item.get("claim") or {}
        claim_id = str(claim.get("id") or "")
        requirement_id = str(claim.get("requirement_id") or "")
        args = json.dumps(claim.get("args") or {}, indent=2, ensure_ascii=False)
        checks = json.dumps(claim.get("checks") or [], indent=2, ensure_ascii=False)
        reading = item.get("reading") or {}
        seal_html = _claim_seal_html(reading)
        law_html = _passages_html(item.get("passages") or [])
        signed = isinstance(claim.get("signed"), dict)
        save_note = (
            '<p class="err">This Claim is sealed. Saving a changed payload clears the seal. '
            "It is then an unsigned draft until signed again.</p>"
            if signed
            else '<p class="muted">Unsigned draft. Selecting a Discovery path or saving does not approve evidence.</p>'
        )
        hidden = _claim_context(model)
        warning = str(item.get("retire_warning") or "")
        warning_html = f'<p class="err">{html.escape(warning)}</p>' if warning else ""
        confirm = "Retire this Claim? The file is removed."
        if warning:
            confirm = f"{warning} {confirm}"
        sign_form = ""
        if not signed:
            sign_form = f"""
<form method="post" action="/claims/{html.escape(claim_id)}/sign">
{hidden}
<label>Signer name</label>
<input type="text" name="name" placeholder="Ada Jurist" required>
<button type="submit">Sign claim</button>
</form>
"""
        blocks.append(
            f"""<div class="card" id="claim-{html.escape(claim_id)}">
{seal_html}
<p><code>{html.escape(claim_id)}</code> → <code>{html.escape(requirement_id)}</code></p>
{law_html}
{save_note}
<form method="post" action="/claims/{html.escape(claim_id)}">
{hidden}
<input type="hidden" name="requirement_id" value="{html.escape(requirement_id)}">
<label>Source</label>
<input type="text" name="source" value="{html.escape(claim.get('source', ''))}" required>
<label>Severity</label>
<input type="text" name="severity" value="{html.escape(claim.get('severity', ''))}">
<label>Description</label>
<input type="text" name="description" value="{html.escape(claim.get('description', ''))}" required>
<label>Source args JSON</label>
<textarea name="args">{html.escape(args)}</textarea>
<label>Checks JSON</label>
<textarea name="checks">{html.escape(checks)}</textarea>
<button type="submit">Save claim</button>
</form>
{sign_form}
{warning_html}
<form method="post" action="/claims/{html.escape(claim_id)}/retire"
 onsubmit="return confirm({html.escape(json.dumps(confirm))});">
{hidden}
<button type="submit">Retire</button>
</form>
</div>"""
        )
    empty = (
        '<p class="muted">No Claims yet. Create them from '
        '<a href="/discover">Discovery &amp; Claims</a> '
        "(add a check on a finding).</p>"
        if not blocks
        else ""
    )
    panel = repo_config_panel(
        model,
        action="/claims",
        show=("config", "packs", "claims"),
    )
    body = f"""
<h1>Claim editor</h1>
<p class="muted">Edit, sign, or retire Claims already in the product repo.
New Claims come from <a href="/discover">Discovery &amp; Claims</a>.
Editing a sealed Claim clears its seal.</p>
{panel}
{_flash(message, error)}
{''.join(blocks) or empty}
"""
    return page("Claim editor", body)


def _claim_context(model: dict) -> str:
    fields = []
    for key in ("repo_id", "source_id", "timestamp"):
        value = str(model.get(key) or "")
        if value:
            fields.append(f'<input type="hidden" name="{key}" value="{html.escape(value)}">')
    return "".join(fields)


def _claim_seal_html(reading: dict) -> str:
    if reading.get("verifiable"):
        return (
            f'<p><strong>Signed · verifiable</strong> · who {html.escape(str(reading.get("who") or "—"))}'
            f' · when {html.escape(str(reading.get("when") or "—"))}</p>'
        )
    if isinstance(reading.get("who"), str) and reading.get("who"):
        reason = html.escape(str(reading.get("reason") or "signature does not verify"))
        return (
            f'<p class="err"><strong>Signed · not verifiable</strong> · who '
            f'{html.escape(str(reading.get("who")))} · {reason}</p>'
        )
    reason = html.escape(str(reading.get("reason") or "unsigned draft"))
    return f'<p class="muted"><strong>Unsigned draft</strong> · {reason}</p>'


def _passages_html(passages: list) -> str:
    if not passages:
        return '<p class="muted">No law_text available for this Requirement in the selected Pack.</p>'
    blocks = []
    for text in passages:
        blocks.append(f"<pre>{html.escape(str(text))}</pre>")
    return "<p>Requirement text</p>" + "".join(blocks)


def scaffold_page(message: str = "", error: str = "") -> bytes:
    body = f"""
<h1>Scaffold</h1>
<p class="muted">Writes a short stub and refuses to overwrite an existing file. The stub is not approved evidence.</p>
{_flash(message, error)}
<form method="post" action="/scaffold">
<label>Path</label>
<input type="text" name="path" value="docs/annex-vii/risk_assessment.md">
<button type="submit">Write stub</button>
</form>
"""
    return page("Scaffold", body)


def check_page(
    result: dict | None,
    exit_code: int | None,
    message: str = "",
    error: str = "",
    editor: dict | None = None,
) -> bytes:
    if result is None:
        shown = "<p>No run yet.</p>"
    else:
        git = ""
        if result.get("worktree") == "dirty":
            git = "<p class=\"err\">The worktree was dirty. This result is not verification of that commit's exact content.</p>"
        elif result.get("commit"):
            git = f"<p class=\"muted\">commit <code>{html.escape(result['commit'])}</code> · worktree {html.escape(result['worktree'])}</p>"
        rows = []
        for row in result.get("claims") or []:
            nested = row.get("checks") or []
            if not nested:
                rows.append(
                    "<tr>"
                    f"<td><code>{html.escape(row.get('id', ''))}</code></td>"
                    f"<td></td><td></td>"
                    f"<td>{html.escape(row.get('status', ''))}</td><td></td>"
                    "</tr>"
                )
            for item in nested:
                rows.append(
                    "<tr>"
                    f"<td><code>{html.escape(row.get('id', ''))}</code></td>"
                    f"<td>{item.get('index', '')}</td>"
                    f"<td>{html.escape(check_caption(item))}</td>"
                    f"<td>{html.escape(item.get('status', ''))}</td>"
                    f"<td>{html.escape(item.get('detail') or '')}</td>"
                    "</tr>"
                )
        table = "<p>No claim rows. This is not a successful verification.</p>" if not rows else (
            "<table><tr><th>Claim</th><th>Index</th><th>Check</th><th>Status</th><th>Detail</th></tr>"
            + "".join(rows)
            + "</table>"
        )
        shown = git + f"<p>exit {exit_code}</p>" + table
    door = editor or {}
    panel = repo_config_panel(
        door,
        action="/check",
        show=("config", "packs", "claims", "results", "reports"),
    )
    body = f"""
<h1>Check</h1>
<p class="muted">Choose a repo. Check reads that repository's <code>curbpack.json</code>.
The file is not signed. A green check row is not a legal conclusion.</p>
{panel}
{_flash(message, error)}
{_curbpack_editor(door)}
<h2>Report</h2>
<div class="card">{shown}</div>
"""
    return page("Check", body)


_PATH_FIELDS = (
    ("config", "Current Configuration", "curbpack_file"),
    ("packs", "Packs directory", "directory"),
    ("claims", "Claims directory", "claims_dir"),
    ("results", "Results directory", "results_dir"),
    ("reports", "Reports directory", "reports_dir"),
)


def repo_config_panel(model: dict, *, action: str, show: tuple[str, ...] = (), beside: str = "") -> str:
    """Repo picker plus the path fields named in show.

    show is a subset of config, packs, claims, results, reports.
    """
    wanted = set(show)
    fields = []
    for key, label, source in _PATH_FIELDS:
        if key not in wanted:
            continue
        value = str(model.get(source) or "")
        if not value:
            continue
        fields.append(
            f"<label>{html.escape(label)} "
            f'<input type="text" readonly value="{html.escape(value)}"></label>'
        )
    picker = _product_repo_picker(model, action)
    return (
        '<section class="config-panel">'
        f'<div class="repo-row">{picker}{beside}</div>'
        f'{"".join(fields)}'
        "</section>"
    )


def _product_repo_picker(model: dict, action: str) -> str:
    repo_id = str(model.get("repo_id") or "")
    options = ['<option value="">Choose a repo</option>']
    for repo in model.get("repos") or []:
        if not isinstance(repo, dict):
            continue
        row_id = str(repo.get("id") or "")
        name = str(repo.get("name") or row_id)
        selected = " selected" if row_id == repo_id else ""
        options.append(
            f'<option value="{html.escape(row_id)}"{selected}>{html.escape(name)}</option>'
        )
    return (
        f'<form method="get" class="repo-picker" action="{html.escape(action)}">'
        '<label>Repo <select name="repo" onchange="this.form.submit()">'
        + "".join(options)
        + "</select></label></form>"
    )


def _curbpack_editor(editor: dict) -> str:
    repo_id = str(editor.get("repo_id") or "")
    if not repo_id:
        return '<div class="card discover-wrap"><p class="muted">Choose a repo to work with.</p></div>'
    rows = []
    for pack in editor.get("packs") or []:
        if not isinstance(pack, dict):
            continue
        pack_id = str(pack.get("id") or "")
        state = "present" if pack.get("present") else "missing"
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(pack_id)}</code></td>"
            f"<td>{html.escape(state)}</td>"
            f"<td><code>{html.escape(str(pack.get('pack_dir') or ''))}</code></td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="3" class="muted">No packs named in curbpack.json.</td></tr>')
    selection = str(editor.get("selection") or "")
    selection_html = (
        f"<p>Selection <code>{html.escape(selection)}</code></p>" if selection else ""
    )
    result_path = str(editor.get("run_result_path") or "")
    result_html = (
        f"<p>Run result <code>{html.escape(result_path)}</code></p>" if result_path else ""
    )
    return f"""
<div class="card discover-wrap">
{selection_html}
{result_html}
<table><thead><tr><th>Pack</th><th>Status</th><th>Path</th></tr></thead><tbody>
{"".join(rows)}
</tbody></table>
<form method="post" action="/check">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<label>packs_dir <input type="text" name="packs_dir" value="{html.escape(str(editor.get("packs_dir_value") or ""))}"></label>
<label>claims_dir <input type="text" name="claims_dir" value="{html.escape(str(editor.get("claims_dir_value") or ""))}"></label>
<label>results_dir <input type="text" name="results_dir" value="{html.escape(str(editor.get("results_dir_value") or ""))}"></label>
<label>reports_dir <input type="text" name="reports_dir" value="{html.escape(str(editor.get("reports_dir_value") or ""))}"></label>
<p class="actions">
<button type="submit" name="action" value="save">Save</button>
<button type="submit" name="action" value="check">Check</button>
</p>
</form>
</div>
"""


def review_page(
    report: dict | None,
    reading: dict | None,
    message: str = "",
    error: str = "",
    discovery: dict | None = None,
    *,
    saved: bool = False,
    report_exists: bool = False,
    same_run_value: bool | None = None,
    unchecked: list[str] | None = None,
    door: dict | None = None,
) -> bytes:
    dialogs = ""
    decision = ""
    if report is None:
        body_report = "<p>No run result to compile.</p>"
    else:
        decision = report.get("decision") or ""
        result = report.get("run_result") if isinstance(report.get("run_result"), dict) else {}
        note = worktree_sentence(result)
        limits = "".join(
            f"<li>{html.escape(item)}</li>" for item in (NOT_A_LEGAL_CONCLUSION, NO_CRA_FIELD)
        )
        if same_run_value is True:
            same_html = '<p data-same-run="yes">same run: yes</p>'
        elif same_run_value is False:
            same_html = '<p data-same-run="no">same run: no. This saved report is an older run.</p>'
        else:
            same_html = ""
        unchecked_html = ""
        if unchecked:
            codes = ", ".join(f"<code>{html.escape(item)}</code>" for item in unchecked)
            unchecked_html = f"<p>These selected Requirements were not checked: {codes}</p>"
        claims_by_id = {
            claim["id"]: claim
            for claim in (report.get("claims") or [])
            if isinstance(claim, dict) and isinstance(claim.get("id"), str)
        }
        claims_href = _claims_href(discovery or {})
        rows = []
        dialog_parts = []
        for row in result.get("claims") or []:
            if not isinstance(row, dict):
                continue
            claim = claims_by_id.get(row.get("id")) or {}
            rows.append(_review_claim_row(row, claim, claims_href))
            dialog = _review_discover_dialog(row, claim, discovery or {})
            if dialog:
                dialog_parts.append(dialog)
        appendix = []
        for item in report.get("appendix") or []:
            appendix.append(
                f"<li><code>{html.escape(item.get('id', ''))}</code> "
                f"requirement <code>{html.escape(item.get('requirement_id', ''))}</code> "
                f"{html.escape(item.get('reason', ''))}</li>"
            )
        appendix_html = (
            "<h2>Signature appendix</h2><ul>" + "".join(appendix) + "</ul>"
            if appendix
            else "<h2>Signature appendix</h2><p class=\"muted\">No unsigned or unverifiable Claims in this run.</p>"
        )
        dialogs = "".join(dialog_parts) + _review_discover_script(bool(dialog_parts))
        reading_html = _reading(reading) if saved else "<p>not saved</p>"
        body_report = f"""
{reading_html}
{same_html}
<p>{html.escape(note)}</p>
<ul>{limits}</ul>
{unchecked_html}
<h2>Check results</h2>
<ul>{''.join(rows)}</ul>
{appendix_html}
<pre>{html.escape(json.dumps(result, indent=2, ensure_ascii=False))}</pre>
"""
    door = door or {}
    panel = repo_config_panel(
        door,
        action="/review",
        show=("config", "results", "reports"),
    )
    repo_id = str(door.get("repo_id") or "")
    report_value = str((door or {}).get("report_path") or "")
    hidden = ""
    if repo_id:
        hidden += f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">'
    if report_value:
        hidden += f'<input type="hidden" name="report" value="{html.escape(report_value)}">'
    if saved:
        decision_forms = f"""
<form method="post" action="/review">
{hidden}
<label>Decision</label>
<textarea name="decision">{html.escape(decision)}</textarea>
<button type="submit">Save decision</button>
</form>
<form method="post" action="/review/sign">
{hidden}
<label>Signer name</label>
<input type="text" name="name" placeholder="External Reviewer">
<button type="submit">review-sign</button>
</form>
"""
    else:
        decision_forms = (
            '<p class="muted">Compile writes the report. Save decision and review-sign need that file.</p>'
        )
    compile_form = ""
    if repo_id:
        compile_form = f"""
<form method="post" action="/review/compile">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<p class="actions"><button type="submit">Compile</button></p>
</form>
"""
    if not repo_id and report is None:
        body_report = "<p>No repository is chosen.</p>"
        decision_forms = ""
        compile_form = ""
    chrome = _review_report_line(door)
    body = f"""
<h1>Review</h1>
<p class="muted">The decision is the reviewer's words. There is no field for meeting CRA.</p>
{panel}
{chrome}
{_flash(message, error)}
<div class="card">{body_report}</div>
{compile_form}
<p><a href="/check">Run checks</a></p>
{decision_forms}
{dialogs}
"""
    return page("Review", body)


def _review_report_line(door: dict) -> str:
    if not str(door.get("repo_id") or "") or not door.get("report_path"):
        return ""
    return f"<p>Review report <code>{html.escape(str(door.get('report_path') or ''))}</code></p>"


def _review_path_chrome(door: dict) -> str:
    if not str(door.get("repo_id") or ""):
        return ""
    parts = []
    if door.get("curbpack_file"):
        parts.append(f"<p>curbpack.json <code>{html.escape(str(door.get('curbpack_file') or ''))}</code></p>")
    if door.get("directory"):
        parts.append(
            f'<p class="muted">Packs directory <code>{html.escape(str(door.get("directory") or ""))}</code>.</p>'
        )
    if door.get("claims_dir"):
        parts.append(
            f'<p class="muted">Claims directory <code>{html.escape(str(door.get("claims_dir") or ""))}</code>.</p>'
        )
    if door.get("results_dir"):
        parts.append(
            f'<p class="muted">Results directory <code>{html.escape(str(door.get("results_dir") or ""))}</code>.</p>'
        )
    if door.get("reports_dir"):
        parts.append(
            f'<p class="muted">Reports directory <code>{html.escape(str(door.get("reports_dir") or ""))}</code>.</p>'
        )
    if door.get("report_path"):
        parts.append(f"<p>Review report <code>{html.escape(str(door.get('report_path') or ''))}</code></p>")
    return "".join(parts)


def studio_page(model: dict, message: str = "") -> bytes:
    door = model.get("door") or {}
    repo_id = str(door.get("repo_id") or "")
    picker = _product_repo_picker(door, "/studio")
    chrome = _review_path_chrome(door)
    if not repo_id:
        body = f"""
<h1>Studio config</h1>
{picker}
<p>No repository is chosen.</p>
"""
        return page("Studio config", body)
    values = model.get("values") or {}
    present = bool(model.get("present"))
    offer = (
        "<p>No curbpack-studio.json. Save writes one with the fields below.</p>"
        if not present
        else f"<p>curbpack-studio.json <code>{html.escape(str(model.get('path') or ''))}</code></p>"
    )
    paths = ""
    if present:
        paths = (
            f'<p class="muted">temp_dir <code>{html.escape(str(values.get("path_temp_dir") or ""))}</code></p>'
            f'<p class="muted">extract_work_dir <code>{html.escape(str(values.get("path_extract_work_dir") or ""))}</code></p>'
            f'<p class="muted">keys_file <code>{html.escape(str(values.get("path_keys_file") or "null"))}</code></p>'
        )
    body = f"""
<h1>Studio config</h1>
<p class="muted">Operator settings for this product repository. Absent file keeps today's bind/model/temp wiring.</p>
{picker}
{chrome}
{offer}
{paths}
{_flash(message, "")}
<form method="post" action="/studio">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="save">
<label>bind.host <input type="text" name="bind_host" value="{html.escape(str(values.get("bind_host") or ""))}" required autocomplete="off"></label>
<label>bind.port <input type="text" name="bind_port" value="{html.escape(str(values.get("bind_port") or ""))}" required autocomplete="off"></label>
<label>model.endpoint <input type="text" name="model_endpoint" value="{html.escape(str(values.get("model_endpoint") or ""))}" required autocomplete="off"></label>
<label>model.api_key <input type="text" name="model_api_key" value="{html.escape(str(values.get("model_api_key") or ""))}" required autocomplete="off"></label>
<label>model.name <input type="text" name="model_name" value="{html.escape(str(values.get("model_name") or ""))}" required autocomplete="off"></label>
<label>model.temperature <input type="text" name="model_temperature" value="{html.escape(str(values.get("model_temperature") or ""))}" required autocomplete="off"></label>
<label>prompts.interpret <input type="text" name="prompt_interpret" value="{html.escape(str(values.get("prompt_interpret") or ""))}" autocomplete="off"></label>
<label>prompts.discovery_hints <input type="text" name="prompt_discovery_hints" value="{html.escape(str(values.get("prompt_discovery_hints") or ""))}" autocomplete="off"></label>
<label>paths.temp_dir <input type="text" name="path_temp_dir" value="{html.escape(str(values.get("path_temp_dir") or ""))}" required autocomplete="off"></label>
<label>paths.extract_work_dir <input type="text" name="path_extract_work_dir" value="{html.escape(str(values.get("path_extract_work_dir") or ""))}" required autocomplete="off"></label>
<label>paths.keys_file <input type="text" name="path_keys_file" value="{html.escape(str(values.get("path_keys_file") or ""))}" autocomplete="off"></label>
<p class="actions">
<button type="submit" form="studio-cancel" class="secondary">Cancel</button>
<button type="submit">Save</button>
</p>
</form>
<form method="post" action="/studio" id="studio-cancel">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="cancel">
</form>
"""
    return page("Studio config", body)


def _claims_href(discovery: dict) -> str:
    parts = []
    for key in ("repo_id", "source_id", "timestamp"):
        value = str(discovery.get(key) or "")
        if value:
            parts.append(f"{key}={quote(value)}")
    if not parts:
        return "/claims"
    return "/claims?" + "&".join(parts)


def _review_claim_row(row: dict, claim: dict, claims_href: str) -> str:
    claim_id = str(row.get("id") or "")
    status = str(row.get("status") or "")
    checks = _review_checks(row)
    if status not in {"fail", "skipped"}:
        return (
            f'<li data-claim="{html.escape(claim_id)}" data-status="{html.escape(status)}">'
            f"<code>{html.escape(claim_id)}</code> {html.escape(status)} "
            f"<ul>{checks}</ul>"
            f'<p><a href="{html.escape(claims_href)}">Open the Claim</a></p></li>'
        )
    requirement_id = str(claim.get("requirement_id") or "")
    args = claim.get("args") if isinstance(claim.get("args"), dict) else {}
    source_path = str(args.get("path") or "")
    button = ""
    if requirement_id:
        button = (
            f'<button type="button" class="discover-again" data-dialog="{html.escape(_dialog_id(claim_id))}">'
            "Discover again</button>"
        )
    return (
        f'<li class="review-failed" data-claim="{html.escape(claim_id)}" '
        f'data-status="{html.escape(status)}" data-requirement="{html.escape(requirement_id)}">'
        f"<code>{html.escape(claim_id)}</code> {html.escape(status)}"
        f"<p>Requirement <code>{html.escape(requirement_id)}</code></p>"
        f"<p>Source path <code>{html.escape(source_path)}</code></p>"
        f"<p class=\"muted\">Source args <code>{html.escape(json.dumps(args, ensure_ascii=False))}</code></p>"
        f"<ul>{checks}</ul>"
        f"{button}"
        f'<p><a href="{html.escape(claims_href)}">Open the Claim</a></p></li>'
    )


def _review_checks(row: dict) -> str:
    parts = []
    for item in row.get("checks") or []:
        if not isinstance(item, dict):
            continue
        detail = str(item.get("detail") or "")
        detail_html = f" — {html.escape(detail)}" if detail else ""
        args = item.get("args") if isinstance(item.get("args"), dict) else {}
        parts.append(
            "<li "
            f'data-check="{html.escape(str(item.get("check") or ""))}" '
            f'data-status="{html.escape(str(item.get("status") or ""))}">'
            f"{html.escape(str(item.get('index')))}: {html.escape(check_caption(item))} "
            f"{html.escape(str(item.get('status') or ''))}{detail_html} "
            f"<code>{html.escape(json.dumps(args, ensure_ascii=False))}</code></li>"
        )
    return "".join(parts)


def _review_discover_dialog(row: dict, claim: dict, discovery: dict) -> str:
    if str(row.get("status") or "") not in {"fail", "skipped"}:
        return ""
    requirement_id = str(claim.get("requirement_id") or "")
    if not requirement_id:
        return ""
    claim_id = str(row.get("id") or "")
    repo_id = str(discovery.get("repo_id") or "")
    source_id = str(discovery.get("source_id") or "")
    timestamp = str(discovery.get("timestamp") or "")
    if repo_id and source_id and timestamp:
        src = (
            f"/discover/claims/{quote(requirement_id)}"
            f"?repo={quote(repo_id)}&source={quote(source_id)}&timestamp={quote(timestamp)}&from=review"
        )
        frame = (
            f'<iframe title="Discovery for {html.escape(requirement_id)}" src="{html.escape(src)}"></iframe>'
        )
    else:
        frame = (
            "<p class=\"muted\">Choose the repository, source, and working copy on Discover "
            "before this popup can open that Requirement.</p>"
        )
    return f"""
<dialog id="{html.escape(_dialog_id(claim_id))}" class="review-discover" data-requirement="{html.escape(requirement_id)}">
  <div class="head">
    <h2>Discover again — <code>{html.escape(requirement_id)}</code></h2>
    <button type="button" class="secondary" data-close>Close</button>
  </div>
  <div class="body">
    <p>Find equivalent evidence for this Requirement and configure suitable Checks. Closing this leaves the failed Claim and its Checks unchanged.</p>
    {frame}
  </div>
</dialog>
"""


def _review_discover_script(enabled: bool) -> str:
    if not enabled:
        return ""
    return """
<script>
document.querySelectorAll("button.discover-again").forEach((button) => {
  button.addEventListener("click", () => {
    const dialog = document.getElementById(button.dataset.dialog);
    if (dialog && dialog.showModal) dialog.showModal();
  });
});
document.querySelectorAll("dialog.review-discover [data-close]").forEach((button) => {
  button.addEventListener("click", () => {
    const dialog = button.closest("dialog");
    if (dialog) dialog.close();
  });
});
</script>
"""


def _dialog_id(claim_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", claim_id).strip("-") or "claim"
    return f"review-discover-{slug}"
