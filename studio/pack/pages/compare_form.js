/** Form Compare page. The browser fetches the comparison JSON and draws this document. */
const FIELDS = [
    { name: "references", read: (requirement) => requirement.references },
    { name: "note", read: (requirement) => requirement.note },
    { name: "remediation_hint", read: (requirement) => requirement.remediation_hint },
    { name: "strength", read: (requirement) => requirement.strength },
    { name: "responsible", read: (requirement) => requirement.responsible },
    { name: "applicability", read: (requirement) => requirement.applicability },
    { name: "exceptions", read: (requirement) => requirement.exceptions },
    { name: "scope", read: (requirement) => requirement.scope },
    { name: "source.framework", read: (requirement) => child(requirement, "source", "framework") },
    { name: "source.instrument", read: (requirement) => child(requirement, "source", "instrument") },
    { name: "source.identifier", read: (requirement) => child(requirement, "source", "identifier") },
    { name: "source.edition", read: (requirement) => child(requirement, "source", "edition") },
    { name: "source.language", read: (requirement) => child(requirement, "source", "language") },
    { name: "source.url", read: (requirement) => child(requirement, "source", "url") },
    { name: "discovery_hints.concepts", read: (requirement) => child(requirement, "discovery_hints", "concepts") },
    { name: "discovery_hints.expected_evidence", read: (requirement) => child(requirement, "discovery_hints", "expected_evidence") },
    { name: "discovery_hints.path_hints", read: (requirement) => child(requirement, "discovery_hints", "path_hints") },
    { name: "discovery_hints.sources", read: (requirement) => child(requirement, "discovery_hints", "sources") },
];
export function selectAll(names, side) {
    const selected = {};
    for (const name of names)
        selected[name] = side;
    return selected;
}
export function paint(root, choices) {
    for (const node of root.querySelectorAll("details[data-choice]")) {
        const field = node.parentElement?.getAttribute("data-field") || "";
        const side = choices[field] === "new" ? "new" : "old";
        node.setAttribute("data-choice", side);
        const current = node.querySelector("summary .choice-current");
        const source = node.querySelector(`button[data-side="${side}"] pre`);
        if (!current || !source)
            continue;
        current.textContent = source.textContent ?? "";
        current.className = `choice-current choice-${side}`;
    }
}
export function changeOne(state, name, side) {
    return { ...state, [name]: side };
}
const LABELS = {
    references: "References",
    note: "Note",
    remediation_hint: "Remediation hint",
    strength: "Strength",
    responsible: "Responsible",
    applicability: "Applicability",
    exceptions: "Exceptions",
    scope: "Scope",
    "source.framework": "Framework",
    "source.instrument": "Instrument",
    "source.identifier": "Identifier",
    "source.edition": "Edition",
    "source.language": "Language",
    "source.url": "URL",
    "discovery_hints.concepts": "Concepts",
    "discovery_hints.expected_evidence": "Expected evidence",
    "discovery_hints.path_hints": "Path hints",
    "discovery_hints.sources": "Sources",
};
export function renderCompareForm(model) {
    const controls = ('<p><button type="button" id="select-all-old">Select all old</button> '
        + '<button type="button" id="select-all-new">Select all new</button></p>');
    const style = ("<style>.choice-old{color:#991b1b;text-decoration:line-through}.choice-new{color:#15803d}"
        + 'details[data-choice="old"] button[data-side="old"]{outline:2px solid #991b1b}'
        + 'details[data-choice="new"] button[data-side="new"]{outline:2px solid #15803d}'
        + "#compare-form pre{white-space:pre-wrap;margin:0}"
        + "#compare-form .field-label{display:block;font-size:.78rem;color:#64748b;margin:.85rem 0 .2rem}"
        + "#compare-form .choice-caption{display:block;font-size:.75rem;font-weight:600;margin:0 0 .25rem;color:#64748b;text-decoration:none}"
        + "#compare-form button[data-side]{display:block;width:100%;margin:.35rem 0 0;padding:.55rem .7rem;background:#fff;color:inherit;border:1px solid #e2e8f0;border-radius:8px;text-align:left}"
        + "#compare-form details[open]>summary{display:none}"
        + "</style>");
    const current = model.current ?? {};
    const proposed = model.proposed ?? {};
    const blocks = FIELDS.map((field) => renderField(field, current, proposed));
    return style + heading(model) + controls + blocks.join("");
}
function heading(model) {
    const proposed = model.proposed ?? {};
    const current = model.current ?? {};
    const id = String(proposed.id || current.id || model.id || "");
    const title = id ? `<h1>${escapeHtml(id)}</h1>` : "";
    if (!model.addition)
        return title;
    return (title
        + '<p class="muted">This requirement is not in the current pack. '
        + "Select all new adds it. Select all old leaves it out.</p>");
}
function renderField(field, current, proposed) {
    const oldText = textOf(field.read(current));
    const newText = textOf(field.read(proposed));
    const label = `<span class="field-label">${escapeHtml(LABELS[field.name] || field.name)}</span>`;
    if (oldText === newText) {
        if (!oldText) {
            return `<section data-field="${escapeHtml(field.name)}" hidden></section>`;
        }
        const shown = `<pre class="field-value">${escapeHtml(oldText)}</pre>`;
        return `<section data-field="${escapeHtml(field.name)}">${label}${shown}</section>`;
    }
    return (`<section data-field="${escapeHtml(field.name)}">${label}`
        + renderDisclosure(shown(oldText), shown(newText))
        + "</section>");
}
function renderDisclosure(oldText, newText) {
    return ('<details open data-choice="old">'
        + `<summary><pre class="choice-current choice-old">${escapeHtml(oldText)}</pre></summary>`
        + `<button type="button" data-side="old"><span class="choice-caption">Old</span><pre class="choice-old">${escapeHtml(oldText)}</pre></button>`
        + `<button type="button" data-side="new"><span class="choice-caption">New</span><pre class="choice-new">${escapeHtml(newText)}</pre></button>`
        + "</details>");
}
function shown(value) {
    return value ? value : "(empty)";
}
function child(requirement, parent, key) {
    const value = requirement[parent];
    if (!value || typeof value !== "object" || Array.isArray(value))
        return undefined;
    return value[key];
}
function textOf(value) {
    if (value == null)
        return "";
    if (typeof value === "string")
        return value;
    if (Array.isArray(value)) {
        const parts = value.map((item) => textOfItem(item)).filter((item) => item);
        const gap = parts.some((item) => item.includes("\n")) ? "\n\n" : "\n";
        return parts.join(gap);
    }
    return textOfItem(value);
}
function textOfItem(value) {
    if (value == null)
        return "";
    if (typeof value === "string")
        return value;
    if (typeof value !== "object")
        return String(value);
    if ("law_text" in value || "locator" in value) {
        const locator = value.locator ? String(value.locator) : "";
        const law = value.law_text ? String(value.law_text) : "";
        return locator && law ? `${locator}\n${law}` : locator || law;
    }
    if (typeof value.source === "string" && Object.keys(value).length === 1)
        return value.source;
    return JSON.stringify(value, null, 2);
}
function escapeHtml(value) {
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}
function mount() {
    const root = document.getElementById("compare-form");
    if (!root)
        return;
    const params = new URLSearchParams(location.search);
    const query = new URLSearchParams();
    for (const key of ["requirement", "proposal", "destination", "pack", "repo"]) {
        const value = params.get(key);
        if (value)
            query.set(key, value);
    }
    fetch("/requirements/compare/form.json?" + query.toString())
        .then((response) => response.json())
        .then((model) => {
        root.innerHTML = renderCompareForm(model);
        const addition = Boolean(model.addition);
        const choices = {};
        root.querySelectorAll("details[data-choice]").forEach((node) => {
            const field = node.parentElement?.getAttribute("data-field");
            if (field)
                choices[field] = "old";
        });
        const paintChoices = (next) => {
            for (const [name, side] of Object.entries(next))
                choices[name] = side;
            paint(root, choices);
        };
        document.getElementById("select-all-old")?.addEventListener("click", () => {
            paintChoices(selectAll(Object.keys(choices), "old"));
        });
        document.getElementById("select-all-new")?.addEventListener("click", () => {
            paintChoices(selectAll(Object.keys(choices), "new"));
        });
        root.querySelectorAll("button[data-side]").forEach((button) => {
            button.addEventListener("click", () => {
                const field = button.closest("[data-field]")?.getAttribute("data-field") || "";
                const side = button.getAttribute("data-side") === "new" ? "new" : "old";
                paintChoices(changeOne(choices, field, side));
            });
        });
        const form = document.createElement("form");
        form.method = "post";
        form.action = "/requirements/compare/form/apply";
        const choice = document.createElement("input");
        choice.type = "hidden";
        choice.name = "choice";
        form.append(choice);
        for (const key of ["requirement", "proposal", "destination", "pack", "repo"]) {
            const value = params.get(key);
            if (!value)
                continue;
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = key;
            input.value = value;
            form.append(input);
        }
        const submit = document.createElement("button");
        submit.type = "submit";
        submit.textContent = "Apply";
        form.append(submit);
        form.addEventListener("submit", () => {
            const posted = { ...choices };
            if (addition) {
                const sides = Object.values(choices);
                posted.requirement = sides.length && sides.every((side) => side === "new") ? "new" : "old";
            }
            choice.value = JSON.stringify(posted);
        });
        root.append(form);
    });
}
if (typeof document !== "undefined") {
    mount();
}
