import assert from 'node:assert/strict';
import test from 'node:test';
import { simulatedDocument } from './dom.mjs';

const projects = [
  { id: 'tide', name: 'Tide', status: 'active' },
  { id: 'forest', name: 'Forest', status: 'archived' },
  { id: 'north', name: 'North', status: 'active' }
];
const settle = () => new Promise(resolve => setImmediate(resolve));
let run = 0;

async function startApp(t) {
  const original = { document: globalThis.document, Option: globalThis.Option, fetch: globalThis.fetch };
  const dom = simulatedDocument();
  const requests = [];
  globalThis.document = dom.document;
  globalThis.Option = dom.Option;
  globalThis.fetch = url => new Promise((resolve, reject) => {
    requests.push({ url, resolve, reject });
  });
  t.after(() => {
    for (const [name, value] of Object.entries(original)) {
      if (value === undefined) delete globalThis[name];
      else globalThis[name] = value;
    }
  });
  const ready = import(`../src/app.js?node-test=${++run}`);
  for (let attempt = 0; requests.length === 0 && attempt < 100; attempt++) await settle();
  assert.equal(requests.length, 1, 'actual app starts the initial API request');
  const { toolbar, rows, selection } = dom.elements;
  const label = toolbar.children[0];
  const select = label.children[0];
  const count = toolbar.children[1];
  async function respond(index, data, ok = true) {
    assert.ok(requests[index], `request ${index} exists`);
    requests[index].resolve({ ok, json: async () => data });
    await settle();
  }
  function change(value) {
    select.value = value;
    select.dispatch('change');
  }
  return { ready, label, select, count, rows, selection, requests, respond, change };
}

test('AC-1/AC-2: labelled filters, counts, persistent selection and successful empty state', async t => {
  const app = await startApp(t);
  assert.equal(app.label.tagName, 'label');
  assert.ok(app.label.textContent.startsWith('Status '));
  assert.deepEqual(app.select.children.map(option => [option.value, option.textContent]), [
    ['all', 'All'], ['active', 'Active'], ['archived', 'Archived'], ['paused', 'Paused']
  ]);
  assert.equal(app.requests[0].url, '/api/projects?status=all');
  assert.equal(app.rows.textContent, 'Loading projects…');
  assert.equal(app.rows.getAttribute('aria-busy'), 'true');
  await app.respond(0, projects);
  await app.ready;
  assert.equal(app.count.textContent, '3 projects');
  assert.equal(app.rows.children.length, 3);
  app.rows.children[0].click();
  assert.equal(app.selection.textContent, 'Tide');
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'true');

  app.change('archived');
  assert.equal(app.requests[1].url, '/api/projects?status=archived');
  assert.equal(app.selection.textContent, 'Tide', 'loading keeps the selection panel');
  await app.respond(1, [projects[1]]);
  assert.equal(app.rows.children[0].textContent, 'Forest — archived');
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'false');
  assert.equal(app.count.textContent, '1 project');
  assert.equal(app.selection.textContent, 'Tide', 'filtering keeps the hidden selection');

  app.change('active');
  assert.equal(app.requests[2].url, '/api/projects?status=active');
  await app.respond(2, [projects[0], projects[2]]);
  assert.equal(app.count.textContent, '2 projects');
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'true');
  app.change('paused');
  assert.equal(app.requests[3].url, '/api/projects?status=paused');
  await app.respond(3, []);
  assert.equal(app.count.textContent, '0 projects');
  assert.equal(app.rows.textContent, 'No projects found.');
  assert.equal(app.rows.getAttribute('aria-busy'), 'false');
  assert.equal(app.selection.textContent, 'Tide');
});

test('AC-3: initial failure and Retry recover using existing alert treatment', async t => {
  const app = await startApp(t);
  await app.respond(0, null, false);
  await app.ready;
  assert.equal(app.rows.children[0].getAttribute('role'), 'alert');
  assert.equal(app.rows.children[0].className, 'problem');
  assert.equal(app.rows.textContent, 'Could not load projects. Retry');
  assert.equal(app.count.textContent, '');
  app.rows.children[0].children[0].click();
  assert.equal(app.requests[1].url, '/api/projects?status=all');
  await app.respond(1, projects);
  assert.equal(app.count.textContent, '3 projects');
});

test('AC-3: failure and Retry retain hidden selection and retry the current filter', async t => {
  const app = await startApp(t);
  await app.respond(0, projects);
  await app.ready;
  app.rows.children[0].click();
  app.change('archived');
  app.requests[1].reject(new Error('Network offline'));
  await settle();
  assert.equal(app.rows.children[0].getAttribute('role'), 'alert');
  assert.equal(app.selection.textContent, 'Tide');
  assert.equal(app.rows.getAttribute('aria-busy'), 'false');
  app.rows.children[0].children[0].click();
  assert.equal(app.requests[2].url, '/api/projects?status=archived');
  assert.equal(app.rows.textContent, 'Loading projects…');
  assert.equal(app.selection.textContent, 'Tide');
  await app.respond(2, [projects[1]]);
  assert.equal(app.rows.children[0].textContent, 'Forest — archived');
  assert.equal(app.count.textContent, '1 project');
  assert.equal(app.selection.textContent, 'Tide');
  app.change('all');
  await app.respond(3, projects);
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'true');
});

test('UX: only latest filter response renders, including obsolete failures', async t => {
  const app = await startApp(t);
  await app.respond(0, projects);
  await app.ready;
  app.rows.children[0].click();
  app.change('active');
  app.change('archived');
  await app.respond(2, [projects[1]]);
  await app.respond(1, [projects[0], projects[2]]);
  assert.equal(app.rows.textContent, 'Forest — archived');
  assert.equal(app.count.textContent, '1 project');

  app.change('active');
  app.change('paused');
  await app.respond(4, []);
  await app.respond(3, null, false);
  assert.equal(app.rows.textContent, 'No projects found.');
  assert.equal(app.count.textContent, '0 projects');
  assert.equal(app.selection.textContent, 'Tide');

  app.change('active');
  app.change('archived');
  await app.respond(5, [projects[0], projects[2]]);
  assert.equal(app.rows.textContent, 'Loading projects…', 'stale success cannot end newer loading');
  assert.equal(app.rows.getAttribute('aria-busy'), 'true');
  await app.respond(6, [projects[1]]);
  assert.equal(app.rows.textContent, 'Forest — archived');
  assert.equal(app.rows.getAttribute('aria-busy'), 'false');
});
