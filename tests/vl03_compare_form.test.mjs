import assert from "node:assert/strict";
import test from "node:test";

import { changeOne, paint, renderCompareForm, selectAll } from "../studio/pack/pages/compare_form.js";

const model = {
  current: {
    note: "line one\nline two",
    strength: "must",
    remediation_hint: "keep this hint",
  },
  proposed: {
    note: "line one\nline three",
    strength: "must",
    remediation_hint: "take this hint",
  },
};

test("a changed multiline note shows both complete values", () => {
  const html = renderCompareForm(model);
  const fields = [...html.matchAll(/data-field="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(fields.slice(0, 4), [
    "references",
    "note",
    "remediation_hint",
    "strength",
  ]);
  assert.match(html, /\.choice-old\{[^}]*color:#991b1b/);
  assert.match(html, /\.choice-old\{[^}]*text-decoration:line-through/);
  assert.match(html, /\.choice-new\{[^}]*color:#15803d/);
  assert.match(html, /details\[data-choice="new"\] button\[data-side="new"\]\{outline:2px solid #15803d\}/);
  const note = html.split('data-field="note"')[1].split('data-field=')[0];
  assert.match(note, /<pre class="choice-old">line one\nline two<\/pre>/);
  assert.match(note, /<pre class="choice-new">line one\nline three<\/pre>/);
  assert.match(note, /data-choice="old"/);
  assert.match(note, /<summary><pre class="choice-current choice-old">line one\nline two<\/pre><\/summary>/);
  const strength = html.split('data-field="strength"')[1].split('data-field=')[0];
  assert.equal(strength.includes("<details"), false);
  assert.match(strength, /must/);
});

test("select all old, select all new, then one leaf", () => {
  const names = ["note", "remediation_hint"];
  const old = selectAll(names, "old");
  assert.deepEqual(old, { note: "old", remediation_hint: "old" });
  const fresh = selectAll(names, "new");
  assert.deepEqual(fresh, { note: "new", remediation_hint: "new" });
  const one = changeOne(fresh, "note", "old");
  assert.equal(one.note, "old");
  assert.equal(one.remediation_hint, "new");
});

test("select all updates the visible summary while the disclosure stays closed", () => {
  const root = formTree();
  paint(root, selectAll(["note", "remediation_hint"], "new"));
  assert.equal(summary(root, "note").textContent, "line one\nline three");
  assert.equal(summary(root, "note").className, "choice-current choice-new");
  assert.equal(summary(root, "remediation_hint").textContent, "take this hint");
  assert.equal(summary(root, "remediation_hint").className, "choice-current choice-new");
  paint(root, changeOne(selectAll(["note", "remediation_hint"], "new"), "note", "old"));
  assert.equal(summary(root, "note").textContent, "line one\nline two");
  assert.equal(summary(root, "note").className, "choice-current choice-old");
  assert.equal(summary(root, "remediation_hint").textContent, "take this hint");
});

class El {
  constructor(tag, attrs = {}, children = [], text = "") {
    this.tag = tag;
    this.attrs = { ...attrs };
    this.children = children;
    this.className = attrs.class || "";
    this._text = text;
    this.parentElement = null;
    for (const child of children) child.parentElement = this;
  }

  get textContent() {
    return this.children.length ? this.children.map((child) => child.textContent).join("") : this._text;
  }

  set textContent(value) {
    this._text = value;
    this.children = [];
  }

  setAttribute(name, value) {
    this.attrs[name] = value;
  }

  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  querySelectorAll(selector) {
    const found = [];
    const visit = (node) => {
      if (node !== this && matches(node, selector)) found.push(node);
      for (const child of node.children) visit(child);
    };
    visit(this);
    return found;
  }
}

function matches(node, selector) {
  if (selector === "details[data-choice]") {
    return node.tag === "details" && node.getAttribute("data-choice") !== null;
  }
  if (selector === "summary .choice-current") {
    return node.className.split(/\s+/).includes("choice-current") && hasAncestor(node, "summary");
  }
  const buttonPre = /^button\[data-side="(old|new)"\] pre$/.exec(selector);
  if (buttonPre) {
    const button = ancestor(node, "button");
    return node.tag === "pre" && button?.getAttribute("data-side") === buttonPre[1];
  }
  return false;
}

function ancestor(node, tag) {
  let current = node.parentElement;
  while (current) {
    if (current.tag === tag) return current;
    current = current.parentElement;
  }
  return null;
}

function hasAncestor(node, tag) {
  return ancestor(node, tag) !== null;
}

function summary(root, field) {
  return root.querySelectorAll("summary .choice-current").find((node) => {
    return ancestor(node, "section")?.getAttribute("data-field") === field;
  });
}

function choice(field, oldText, newText) {
  const oldPre = new El("pre", { class: "choice-old" }, [], oldText);
  const newPre = new El("pre", { class: "choice-new" }, [], newText);
  const current = new El("pre", { class: "choice-current choice-old" }, [], oldText);
  return new El("section", { "data-field": field }, [
    new El("details", { "data-choice": "old" }, [
      new El("summary", {}, [current]),
      new El("button", { "data-side": "old" }, [oldPre]),
      new El("button", { "data-side": "new" }, [newPre]),
    ]),
  ]);
}

function formTree() {
  return new El("div", {}, [
    choice("note", "line one\nline two", "line one\nline three"),
    choice("remediation_hint", "keep this hint", "take this hint"),
  ]);
}
