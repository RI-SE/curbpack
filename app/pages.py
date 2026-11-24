"""Shared HTML chrome. Renders values it is given and does not decide them."""

from __future__ import annotations

import html
import json

CSS = """
:root{--bg:#eef2f7;--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--accent:#0f766e;--ok:#15803d;--bad:#b91c1c}
*{box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,sans-serif;margin:0;background:var(--bg);color:var(--ink);line-height:1.45}
main{max-width:1100px;margin:0 auto;padding:1.5rem 1.25rem 3rem}
h1{font-size:1.5rem;margin:0 0 .35rem}
a{color:var(--accent)}
.topbar{display:flex;flex-wrap:wrap;align-items:center;gap:.65rem 1rem;margin:0 0 1rem;padding:0 0 .85rem;border-bottom:1px solid var(--line)}
.topbar .brand{display:inline-flex;align-items:center;gap:.45rem;font-family:"Poppins",ui-sans-serif,system-ui,sans-serif;font-size:1.05rem;color:var(--ink);text-decoration:none;margin-right:.25rem}
.topbar .brand img{width:1.55rem;height:1.55rem;display:block}
.topbar .brand .name-curbpack{font-weight:700}
.topbar .brand .name-studio{font-weight:400}
.topbar nav{display:inline-flex;flex-wrap:wrap;align-items:center;gap:.55rem .85rem}
.topbar nav a{margin:0;text-decoration:none}
.topbar .crumbs{display:inline-flex;flex-wrap:wrap;align-items:center;gap:.35rem;color:var(--muted);font-size:.92rem}
.topbar .crumbs a{margin:0}
.topbar .crumbs .here{color:var(--ink)}
.repo-current{font-size:.92rem;margin-right:.5rem}
button.link{background:none;border:0;border-radius:0;padding:0;color:var(--accent);font-weight:600;text-decoration:underline;text-underline-offset:.12em}
button.link:hover{color:#115e59}
form.inline{display:inline}
button.secondary{background:#fff;color:var(--ink);border:1px solid #cbd5e1}
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
.req-identity .req-kind{margin:0;font-size:1rem}
.req-identity .req-id{margin:.15rem 0 0}
.req-identity .identity-bar{margin-bottom:.75rem}
.req-identity .identity-bar .field-grid{flex:1;margin:0;grid-template-columns:repeat(3,max-content);justify-content:start}
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
.name-with-namespace{display:flex;align-items:center;gap:.4rem;margin-top:.2rem}
.name-with-namespace .namespace-prefix{font-family:ui-monospace,Menlo,monospace;white-space:nowrap}
.name-with-namespace input[type=text]{width:auto;flex:1;min-width:0}
.url-with-open{display:flex;align-items:center;gap:.4rem;margin-top:.2rem}
.url-with-open input[type=text]{width:auto;flex:1;min-width:0}
.url-with-open button{white-space:nowrap}
input.conflict{border-color:var(--bad);background:#fef2f2}
p.name-conflict{color:var(--bad);font-size:.85rem;margin:.35rem 0 0}
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
.source-actions{margin:0 0 .75rem}
form.import-zip{margin:0}
form.import-zip input[type=file]{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.actions form{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center}
.editor-actions{margin-top:.85rem;align-items:center}
.editor-actions dialog{position:fixed}
.editor-actions button{padding:.45rem .75rem;font-size:inherit;line-height:1.2;border-radius:6px}
.editor-actions button.sign-ok,.editor-actions button.sign-bad{font-weight:600}
.pill{display:inline-block;font-size:.75rem;border:1px solid var(--line);border-radius:999px;padding:.05rem .45rem;margin-left:.25rem}
.pill-ok{background:#ecfdf5;color:#065f46}
.pill-bad{background:#fef2f2;color:#991b1b}
details.requirement > summary{list-style:none;pointer-events:none}
details.requirement > summary::-webkit-details-marker{display:none}
details.requirement > summary > a{display:block;pointer-events:auto;color:inherit;text-decoration:none}
dialog{border:1px solid var(--line);border-radius:12px;padding:0;max-width:36rem;width:calc(100% - 2rem)}
dialog.overlap{max-width:min(52rem,calc(100% - 2rem))}
dialog.overlap[open]{position:fixed;top:8vh;left:50%;transform:translateX(-50%);z-index:20;max-height:80vh;overflow:auto}
dialog.overlap table{width:100%;border-collapse:collapse}
dialog.overlap th,dialog.overlap td{text-align:left;vertical-align:top;padding:.4rem .55rem;border-bottom:1px solid var(--line);overflow-wrap:anywhere}
dialog.overlap th{font-size:.75rem;letter-spacing:.04em;text-transform:uppercase;color:#57534e}
dialog.overlap button.overlap-detail{background:none;border:0;padding:0;color:#0f766e;font:inherit;text-decoration:underline;cursor:pointer}
dialog.check-detail{white-space:normal}
dialog.check-detail dl{margin:0}
dialog.check-detail dt{font-size:.75rem;letter-spacing:.04em;text-transform:uppercase;color:#57534e}
dialog.check-detail dd{margin:0 0 .7rem;overflow-wrap:anywhere}
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
.config-panel .repo-row{margin:0}
.config-panel label{margin:.45rem 0 0}
.config-panel input[readonly]{background:#fff;color:var(--ink);cursor:text}
dialog.config-all{max-width:40rem;width:calc(100% - 2rem)}
dialog.config-all .config-panel{border:0;padding:0;margin:0}
.discover-wrap .repo-picker{margin:0 0 .75rem}
.discover-wrap table{width:100%}
.discover-wrap .path-cell{max-width:14rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.discover-wrap select.copy-select{max-width:16rem}
.discover-wrap th.num,.discover-wrap td.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.check-run{display:flex;align-items:stretch;gap:1.25rem}
.check-run > table{width:auto;flex:1 1 auto;margin:0}
.check-run > form{margin:0;flex:0 0 auto;display:flex;align-items:flex-end}
.check-run .actions{margin:0}
.discover-wrap th.num.wrap{white-space:normal;line-height:1.2;max-width:6.5rem}
body:has(.req-desk) main{max-width:min(1400px,100%)}
.req-head{display:flex;flex-wrap:wrap;gap:.75rem 1.25rem;align-items:center;justify-content:space-between;margin:0 0 .35rem}
.req-head h1{margin:0;flex:1;min-width:12rem}
.req-head #seal-status{flex-shrink:0}
.req-head #seal-status button{cursor:default}
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
.hits-table.show-suggestions tr.detail-row[hidden]{display:none}
.hits-table tr.hit-row.suggestion-row{background:#fffbeb}
.hits-table tr.hit-row.suggestion-row:hover,
.hits-table tr.hit-row.suggestion-row.open{background:#fef9c3}
.hits-table tr.detail-row.suggestion-row td{background:#fffbeb}
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
.review-board .brand{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.review-board h1{font-size:1.75rem;letter-spacing:-.02em}
.review-board h2{font-size:1.15rem;margin:1.4rem 0 .55rem}
.review-board h3{font-size:1rem;margin:0 0 .4rem;font-family:ui-sans-serif,system-ui,sans-serif}
.review-board .topline{border-left:4px solid var(--accent);font-size:1.05rem}
.review-board [data-selected="run"] h2{margin:.85rem 0 .35rem;font-size:1.05rem}
.review-board [data-selected="run"] .topline{border-left:0;padding:0;font-size:1rem}
.review-board [data-selected="run"] button.link code{font-size:1rem}
dialog.run-detail{max-width:min(52rem,calc(100% - 2rem))}
dialog.run-detail h3{font-size:1rem;margin:1rem 0 .35rem}
dialog.run-detail h4{font-size:.85rem;margin:.7rem 0 .2rem}
dialog.run-detail dl{display:grid;grid-template-columns:minmax(8rem,12rem) 1fr;gap:.15rem .75rem;margin:.25rem 0 .5rem}
dialog.run-detail dt{color:var(--muted);margin:0}
dialog.run-detail dd{margin:0;overflow-wrap:anywhere}
dialog.run-detail details{margin:.35rem 0}
dialog.run-detail pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.75rem}
.review-board .header{display:flex;flex-wrap:wrap;gap:.75rem 1.25rem;align-items:baseline;justify-content:space-between;margin-bottom:1.1rem}
.review-board .pill{display:inline-block;font-size:.75rem;padding:.15rem .45rem;border-radius:999px;background:var(--line);color:var(--ink);border:0;margin:0}
.review-board .pill-bad{background:#fee2e2;color:#991b1b}
.review-board .note{font-size:.88rem;color:var(--muted);margin:.35rem 0 .55rem}
.review-board .seal-facts{display:block;font-size:.72rem;color:var(--muted);margin-top:.35rem;line-height:1.3;max-height:2.7em;overflow:hidden}
.review-board .check{display:inline-flex;align-items:center;gap:.25rem;font-family:ui-monospace,Menlo,monospace;font-size:.75rem;padding:.12rem .4rem;border-radius:4px;margin:.1rem .2rem .1rem 0;border:1px solid transparent}
.review-board .check .mark{display:block;flex:none}
.review-board button.check{cursor:pointer;line-height:1.2}
.review-board .check.pass{background:#dcfce7;color:#166534;border-color:#86efac}
.review-board .check.fail{background:#fee2e2;color:#991b1b;border-color:#fca5a5}
.review-board .check.skipped{background:#fef3c7;color:#92400e;border-color:#fcd34d}
.review-board table.path-checks{width:100%;border-collapse:collapse;font-size:.92rem}
.review-board table.path-checks th{color:var(--muted);font-weight:600;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em}
.review-board table.path-checks th,.review-board table.path-checks td{text-align:left;padding:.55rem .4rem;border-bottom:1px solid var(--line);vertical-align:top}
.review-board .claim-card{margin:.65rem 0}
.review-board .actions{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.65rem}
.review-board a.btn,.review-board button.btn{cursor:pointer;padding:.4rem .7rem;border-radius:6px;border:1px solid var(--line);background:var(--card);font-size:.85rem;color:inherit;text-decoration:none;display:inline-block}
.review-board a.btn.primary,.review-board button.btn.primary,.review-board a.edit-review{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.review-board a.edit-review{padding:.4rem .7rem;border-radius:6px;text-decoration:none}
.review-board a.file-link{color:var(--accent);text-decoration:underline;text-underline-offset:2px}
.review-board details.requirement.card{padding:1rem 1.15rem}
.review-board details.requirement > summary{list-style:none;pointer-events:none}
.review-board details.requirement > summary::-webkit-details-marker{display:none}
.review-board details.requirement > summary > a{display:block;pointer-events:auto;color:inherit;text-decoration:none}
.review-board section.deviations-frame{border:1px solid var(--line);border-radius:10px;background:var(--card);padding:0 .9rem .9rem}
.review-board section.deviations-frame[data-resolved]{margin-top:1.2rem}
.review-board section.deviations-frame > h2{font-size:1rem;font-weight:600;margin:0;padding:.75rem 0}
.review-board details.passed-frame{margin-top:1.2rem;border:1px solid var(--line);border-radius:10px;background:var(--card);padding:0 .9rem .9rem}
.review-board details.passed-frame > summary{cursor:pointer;font-weight:600;padding:.75rem 0}
.review-board details.technical{margin:.35rem 0 0;font-size:.8rem;color:var(--muted)}
.review-board details.technical > summary{cursor:pointer;list-style:revert;font-weight:600;text-transform:uppercase;letter-spacing:.04em;font-size:.75rem}
.review-board details.technical code,.review-board details.technical pre{display:block;margin:.35rem 0 0;white-space:pre-wrap;word-break:break-word}
.review-board ul.review-check-list{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.review-board .path-mark{color:#b91c1c;font-weight:700}
.review-board .claim-technical{margin-top:.5rem}
.review-board .review-meta{color:var(--muted);margin:.15rem 0 .9rem}
.review-board table.review-queue{width:100%;border-collapse:collapse;background:var(--card);font-size:.92rem}
.review-board table.review-queue th{text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);padding:.4rem .45rem;border-bottom:1px solid var(--line)}
.review-board table.review-queue th.tips{cursor:help}
.review-board table.review-queue td{padding:.5rem .45rem;border-bottom:1px solid var(--line);vertical-align:top}
.review-board td.row-actions form,.review-board td.row-actions p{display:flex;flex-direction:column;align-items:flex-start;gap:.35rem;margin:.15rem 0}
.review-board td.row-actions input[name="remediation"]{width:9rem}
.review-board table.review-queue p{margin:.15rem 0}
.review-board select.verdict{font:inherit;max-width:11rem}
.review-board .remedy-icon{display:inline-block;vertical-align:-.2em;margin-right:.3rem;color:var(--muted)}
.review-board button.comment-mark{width:1.8rem;height:1.8rem;border:1px solid var(--line);border-radius:4px;background:#fff;cursor:pointer;padding:0;color:var(--ink)}
.review-board button.comment-mark.has-comment{border-color:transparent;background:transparent}
.review-board button.comment-mark .doc-icon{display:block;margin:auto}
.review-board dialog.comment-editor,.review-board dialog.binding-note,.review-board dialog.review-choice{border:1px solid var(--line);border-radius:10px;padding:1rem;max-width:32rem}
.review-board dialog.review-choice .btn, .review-board dialog.review-choice button{margin:0 .35rem .35rem 0}
.review-board dialog.review-choice .btn{margin:0 .35rem .35rem 0}
.review-board dialog.binding-note p{margin:.4rem 0}
.review-board dialog.comment-editor textarea{min-height:6rem;width:100%}
.review-board textarea::placeholder{color:var(--muted)}
.review-board .file-actions{margin-top:.25rem;font-size:.8rem}
"""


def page(
    title: str,
    body: str,
    crumbs: list[tuple[str, str]] | None = None,
    *,
    banner: str = "",
) -> bytes:
    crumb_html = ""
    if crumbs:
        parts = []
        for index, (href, label) in enumerate(crumbs):
            if index:
                parts.append('<span class="muted">›</span>')
            if index == len(crumbs) - 1 or not href:
                parts.append(f'<span class="here">{html.escape(label)}</span>')
            else:
                parts.append(f'<a href="{html.escape(href)}">{html.escape(label)}</a>')
        crumb_html = f'<span class="crumbs">{"".join(parts)}</span>'
    topbar = f"""
<header class="topbar">
<a class="brand" href="/" title="Curbpack Studio">
<img src="/icons/curbpack-icon.svg" alt="" width="24" height="24">
<span><span class="name-curbpack">Curbpack</span> <span class="name-studio">Studio</span></span>
</a>
<nav>
<a href="/project">Change Project</a>
<a href="/home">Home</a>
<a href="/requirements">Pack Editor</a>
<a href="/discover">Discover</a>
<a href="/check">Check</a>
<a href="/review">Review</a>
{crumb_html}
</nav>
</header>
"""
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main>
{topbar}
{banner}
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


_PATH_FIELDS = (
    ("config", "Current Configuration", "curbpack_file"),
    ("packs", "Packs directory", "packs_dir_value"),
    ("claims", "Claims directory", "claims_dir_value"),
    ("results", "Results directory", "results_dir_value"),
    ("reports", "Reports directory", "reports_dir_value"),
)


def repo_config_panel(
    model: dict,
    *,
    action: str = "",
    show: tuple[str, ...] = (),
    beside: str = "",
    title: str = "Current Project",
    blanks: bool = False,
) -> str:
    """Project name under the top bar. The name opens the path fields.

    show and blanks stay for call-site compatibility. The compact panel does not
    list path fields. A selected project name opens every field in the dialog.
    With no project, NONE links to Change Project. action is unused.
    """
    del action, show, blanks
    current = _current_project_label(model, title=title)
    dialog = _config_all_dialog(model) if model.get("repo_id") else ""
    return (
        '<section class="config-panel">'
        f'<div class="repo-row">{current}{beside}</div>'
        "</section>"
        f"{dialog}"
    )


def _path_inputs(model: dict, wanted: set[str], *, blanks: bool) -> list[str]:
    fields = []
    for key, label, source in _PATH_FIELDS:
        if key not in wanted:
            continue
        value = str(model.get(source) or "")
        if not value and not blanks:
            continue
        fields.append(
            f"<label>{html.escape(label)} "
            f'<input type="text" readonly value="{html.escape(value)}"></label>'
        )
    return fields


def _config_all_dialog(model: dict) -> str:
    """Full path panel. The project name (id config-all-open) opens it."""
    fields = _path_inputs(
        model,
        {key for key, _label, _source in _PATH_FIELDS},
        blanks=True,
    )
    return (
        '<dialog id="config-all" class="config-all">'
        '<div class="head"><h2>Current Project</h2>'
        '<button type="button" id="config-all-close">Close</button></div>'
        f'<div class="body"><div class="config-panel">{"".join(fields)}</div></div>'
        "</dialog>"
        "<script>"
        '(function(){var open=document.getElementById("config-all-open");'
        'var dialog=document.getElementById("config-all");'
        'if(!open||!dialog)return;'
        'open.addEventListener("click",function(){dialog.showModal();});'
        'document.getElementById("config-all-close").addEventListener("click",function(){dialog.close();});'
        "})();"
        "</script>"
    )


def _current_project_label(model: dict, title: str = "Project") -> str:
    repo_id = str(model.get("repo_id") or "")
    name = repo_id
    for repo in model.get("repos") or []:
        if isinstance(repo, dict) and str(repo.get("id") or "") == repo_id:
            name = str(repo.get("name") or repo_id)
            break
    label = html.escape(title)
    if not repo_id:
        return (
            f'<span class="repo-current">{label} '
            f'<a href="/project">NONE</a></span>'
        )
    return (
        f'<span class="repo-current">{label} '
        f'<button type="button" class="link" id="config-all-open">{html.escape(name)}</button>'
        "</span>"
    )
