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
}): string {
  const current = model.current ?? {};
  const proposed = model.proposed ?? {};
  const blocks = FIELDS.map((field) => renderField(field, current, proposed));
  return (
    "<style>.choice-old{color:#991b1b;text-decoration:line-through}.choice-new{color:#15803d}</style>"
    + '<p><button type="button" id="select-all-old">Select all old</button> '
    + '<button type="button" id="select-all-new">Select all new</button></p>'
    + blocks.join("")
  );
}

function renderField(field: Field, current: Requirement, proposed: Requirement): string {
  const oldText = textOf(field.read(current));
  const newText = textOf(field.read(proposed));
  if (oldText === newText) {
    return `<section data-field="${escapeHtml(field.name)}"><p>${escapeHtml(oldText)}</p></section>`;
  }
  return (
    `<section data-field="${escapeHtml(field.name)}">`
    + '<details data-choice="old">'
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
