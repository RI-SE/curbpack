/** Form Compare page. The browser fetches the comparison JSON and draws this document. */

export type Side = "old" | "new";

type Requirement = Record<string, unknown>;

interface Field {
  name: string;
  read: (requirement: Requirement) => unknown;
}

const FIELDS: Field[] = [
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

export function selectAll(names: string[], side: Side): Record<string, Side> {
  const selected: Record<string, Side> = {};
  for (const name of names) selected[name] = side;
  return selected;
}

export function paint(root: {
  querySelectorAll(selector: string): Iterable<{
    parentElement: { getAttribute(name: string): string | null } | null;
    setAttribute(name: string, value: string): void;
    querySelector(selector: string): { textContent: string | null; className: string } | null;
  }>;
}, choices: Record<string, Side>): void {
  for (const node of root.querySelectorAll("details[data-choice]")) {
    const field = node.parentElement?.getAttribute("data-field") || "";
    const side: Side = choices[field] === "new" ? "new" : "old";
    node.setAttribute("data-choice", side);
    const current = node.querySelector("summary .choice-current");
    const source = node.querySelector(`button[data-side="${side}"] pre`);
    if (!current || !source) continue;
    current.textContent = source.textContent ?? "";
    current.className = `choice-current choice-${side}`;
  }
}

export function changeOne(
  state: Record<string, Side>,
  name: string,
  side: Side,
): Record<string, Side> {
  return { ...state, [name]: side };
}

export function renderCompareForm(model: {
  current?: Requirement;
  proposed?: Requirement;
  addition?: boolean;
}): string {
  const controls = (
    '<p><button type="button" id="select-all-old">Select all old</button> '
    + '<button type="button" id="select-all-new">Select all new</button></p>'
  );
  const style = (
    "<style>.choice-old{color:#991b1b;text-decoration:line-through}.choice-new{color:#15803d}"
    + 'details[data-choice="old"] button[data-side="old"]{outline:2px solid #991b1b}'
    + 'details[data-choice="new"] button[data-side="new"]{outline:2px solid #15803d}</style>'
  );
  if (model.addition) {
    return style + controls + renderDisclosure("requirement", "", textOf(model.proposed ?? {}));
  }
  const current = model.current ?? {};
  const proposed = model.proposed ?? {};
  const blocks = FIELDS.map((field) => renderField(field, current, proposed));
  return style + controls + blocks.join("");
}

function renderField(field: Field, current: Requirement, proposed: Requirement): string {
  const oldText = textOf(field.read(current));
  const newText = textOf(field.read(proposed));
  if (oldText === newText) {
    return `<section data-field="${escapeHtml(field.name)}"><p>${escapeHtml(oldText)}</p></section>`;
  }
  return renderDisclosure(field.name, oldText, newText);
}

function renderDisclosure(name: string, oldText: string, newText: string): string {
  return (
    `<section data-field="${escapeHtml(name)}">`
    + '<details data-choice="old">'
    + `<summary><pre class="choice-current choice-old">${escapeHtml(oldText)}</pre></summary>`
    + `<button type="button" data-side="old"><pre class="choice-old">${escapeHtml(oldText)}</pre></button>`
    + `<button type="button" data-side="new"><pre class="choice-new">${escapeHtml(newText)}</pre></button>`
    + "</details></section>"
  );
}

function child(requirement: Requirement, parent: string, key: string): unknown {
  const value = requirement[parent];
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  return (value as Requirement)[key];
}

function textOf(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === "string" ? item : JSON.stringify(item))).join("\n");
  }
  return JSON.stringify(value);
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function mount(): void {
  const root = document.getElementById("compare-form");
  if (!root) return;
  const params = new URLSearchParams(location.search);
  const query = new URLSearchParams();
  for (const key of ["requirement", "proposal", "destination", "pack", "repo", "section"]) {
    const value = params.get(key);
    if (value) query.set(key, value);
  }
  fetch("/requirements/compare/form.json?" + query.toString())
    .then((response) => response.json())
    .then((model: { current?: Requirement; proposed?: Requirement }) => {
      root.innerHTML = renderCompareForm(model);
      const choices: Record<string, Side> = {};
      root.querySelectorAll("details[data-choice]").forEach((node) => {
        const field = node.parentElement?.getAttribute("data-field");
        if (field) choices[field] = "old";
      });
      const paintChoices = (next: Record<string, Side>): void => {
        for (const [name, side] of Object.entries(next)) choices[name] = side;
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
      for (const key of ["requirement", "proposal", "destination", "pack", "repo", "section"]) {
        const value = params.get(key);
        if (!value) continue;
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
