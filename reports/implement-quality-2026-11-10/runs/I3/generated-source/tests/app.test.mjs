import assert from 'node:assert/strict';
import test from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { createDocument, Option } from './helpers/dom.mjs';

const tide = { id: 'tide', name: 'Tide', status: 'active' };
const forest = { id: 'forest', name: 'Forest', status: 'archived' };
const north = { id: 'north', name: 'North', status: 'active' };
const all = [tide, forest, north];
let scenario = 0;

async function mount(t) {
  const original = { document: globalThis.document, Option: globalThis.Option, fetch: globalThis.fetch };
  globalThis.document = createDocument();
  globalThis.Option = Option;
  const requests = [];
  globalThis.fetch = url => new Promise((resolve, reject) => requests.push({ url, resolve, reject }));
  t.after(() => {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }
  });
  await import(`../src/app.js?scenario=${++scenario}`);
  const rows = document.querySelector('#rows');
  const selection = document.querySelector('#selection');
  const toolbar = document.querySelector('#toolbar');
  const select = toolbar.children[0].children.find(child => child.tagName === 'select');
  const count = toolbar.children[1];
  return {
    rows, selection, select, count, requests,
    filter(status) { select.value = status; select.fire('change'); },
    async respond(index, result, ok = true) {
      requests[index].resolve({ ok, json: async () => result });
      await setImmediate();
    },
    async reject(index) {
      requests[index].reject(new Error('Network unavailable'));
      await setImmediate();
    }
  };
}

test('AC-1/2: filters request matching data/count, retain selection and distinguish empty success', async t => {
  const app = await mount(t);
  assert.equal(app.requests[0].url, '/api/projects?status=all');
  assert.equal(app.rows.textContent, 'Loading projects…');
  assert.equal(app.rows.getAttribute('aria-busy'), 'true');
  assert.deepEqual(app.select.children.map(option => [option.value, option.textContent]),
    [['all', 'All'], ['active', 'Active'], ['archived', 'Archived'], ['paused', 'Paused']]);
  await app.respond(0, all);
  assert.equal(app.count.textContent, '3 projects');
  assert.equal(app.rows.getAttribute('aria-busy'), 'false');
  app.rows.children[0].fire('click');
  assert.equal(app.selection.textContent, 'Tide');
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'true');

  app.filter('archived');
  assert.equal(app.requests[1].url, '/api/projects?status=archived');
  assert.equal(app.selection.textContent, 'Tide');
  await app.respond(1, [forest]);
  assert.equal(app.count.textContent, '1 project');
  assert.equal(app.rows.textContent, 'Forest — archived');
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'false');
  assert.equal(app.selection.textContent, 'Tide');

  app.filter('active');
  assert.equal(app.requests[2].url, '/api/projects?status=active');
  await app.respond(2, [tide, north]);
  assert.equal(app.count.textContent, '2 projects');
  assert.deepEqual(app.rows.children.map(row => row.textContent), ['Tide — active', 'North — active']);
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'true');

  app.filter('paused');
  assert.equal(app.requests[3].url, '/api/projects?status=paused');
  await app.respond(3, []);
  assert.equal(app.count.textContent, '0 projects');
  assert.equal(app.rows.textContent, 'No projects match this status.');
  assert.equal(app.selection.textContent, 'Tide');
});

test('AC-3: failed current filter retries through the existing problem helper without losing selection', async t => {
  const app = await mount(t);
  await app.respond(0, all);
  app.rows.children[0].fire('click');
  app.filter('active');
  await app.respond(1, null, false);
  assert.equal(app.count.textContent, 'Unavailable');
  assert.equal(app.rows.children[0].getAttribute('role'), 'alert');
  assert.equal(app.selection.textContent, 'Tide');
  const retry = app.rows.children[0].children.find(child => child.tagName === 'button');
  assert.equal(retry.textContent, 'Retry');
  retry.fire('click');
  assert.equal(app.requests[2].url, '/api/projects?status=active');
  assert.equal(app.rows.textContent, 'Loading projects…');
  assert.equal(app.selection.textContent, 'Tide');
  await app.respond(2, [tide, north]);
  assert.equal(app.count.textContent, '2 projects');
  assert.equal(app.rows.children[0].getAttribute('aria-pressed'), 'true');
});

test('AC-3: outdated success and error cannot replace the latest response, loading or error', async t => {
  const app = await mount(t);
  await app.respond(0, all);
  app.filter('active');
  app.filter('archived');
  await app.respond(2, [forest]);
  await app.respond(1, [tide, north]);
  assert.equal(app.count.textContent, '1 project');
  assert.equal(app.rows.textContent, 'Forest — archived');
  assert.equal(app.select.value, 'archived');

  app.filter('active');
  app.filter('paused');
  await app.reject(3);
  assert.equal(app.rows.textContent, 'Loading projects…');
  await app.respond(4, []);
  assert.equal(app.rows.textContent, 'No projects match this status.');

  app.filter('active');
  app.filter('archived');
  await app.respond(6, [forest]);
  await app.reject(5);
  assert.equal(app.count.textContent, '1 project');
  assert.equal(app.rows.textContent, 'Forest — archived');

  app.filter('active');
  app.filter('paused');
  await app.respond(8, null, false);
  await app.respond(7, [tide, north]);
  assert.equal(app.count.textContent, 'Unavailable');
  assert.equal(app.rows.children[0].getAttribute('role'), 'alert');
  assert.equal(app.select.value, 'paused');
});
