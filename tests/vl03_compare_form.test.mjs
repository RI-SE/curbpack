import assert from "node:assert/strict";
import test from "node:test";

import { changeOne, renderCompareForm, selectAll } from "../studio/pack/pages/compare_form.js";

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
