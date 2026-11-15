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
export function changeOne(state, name, side) {
    return { ...state, [name]: side };
}
export function renderCompareForm(model) {
    const current = model.current ?? {};
    const proposed = model.proposed ?? {};
    const blocks = FIELDS.map((field) => renderField(field, current, proposed));
    return ("<style>.choice-old{color:#991b1b;text-decoration:line-through}.choice-new{color:#15803d}</style>"
        + '<p><button type="button" id="select-all-old">Select all old</button> '
        + '<button type="button" id="select-all-new">Select all new</button></p>'
        + blocks.join(""));
}
function renderField(field, current, proposed) {
    const oldText = textOf(field.read(current));
    const newText = textOf(field.read(proposed));
    if (oldText === newText) {
        return `<section data-field="${escapeHtml(field.name)}"><p>${escapeHtml(oldText)}</p></section>`;
    }
    return (`<section data-field="${escapeHtml(field.name)}">`
        + '<details data-choice="old">'
        + `<button type="button" data-side="old"><pre class="choice-old">${escapeHtml(oldText)}</pre></button>`
        + `<button type="button" data-side="new"><pre class="choice-new">${escapeHtml(newText)}</pre></button>`
        + "</details></section>");
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
        return value.map((item) => (typeof item === "string" ? item : JSON.stringify(item))).join("\n");
    }
    return JSON.stringify(value);
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
        const choices = {};
        root.querySelectorAll("details[data-choice]").forEach((node) => {
            const field = node.parentElement?.getAttribute("data-field");
            if (field)
                choices[field] = "old";
        });
        const paint = (next) => {
            for (const [name, side] of Object.entries(next))
                choices[name] = side;
            root.querySelectorAll("details[data-choice]").forEach((node) => {
                const field = node.parentElement?.getAttribute("data-field") || "";
                node.setAttribute("data-choice", choices[field] || "old");
            });
        };
        document.getElementById("select-all-old")?.addEventListener("click", () => {
            paint(selectAll(Object.keys(choices), "old"));
        });
        document.getElementById("select-all-new")?.addEventListener("click", () => {
            paint(selectAll(Object.keys(choices), "new"));
        });
        root.querySelectorAll("button[data-side]").forEach((button) => {
            button.addEventListener("click", () => {
                const field = button.closest("[data-field]")?.getAttribute("data-field") || "";
                const side = button.getAttribute("data-side") === "new" ? "new" : "old";
                paint(changeOne(choices, field, side));
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
            choice.value = JSON.stringify(choices);
        });
        root.append(form);
    });
}
if (typeof document !== "undefined") {
    mount();
}
