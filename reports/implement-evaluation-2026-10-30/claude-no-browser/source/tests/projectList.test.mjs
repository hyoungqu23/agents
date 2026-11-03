import assert from 'node:assert/strict';
import test from 'node:test';
import { createProjectList } from '../src/projectList.js';

const tide = { id: 'tide', name: 'Tide', status: 'active' };
const forest = { id: 'forest', name: 'Forest', status: 'archived' };

function setup(load) {
  const views = [];
  const list = createProjectList({ load, view: state => views.push({ ...state }) });
  return { list, views };
}

test('filter passes the status to the loader and shows matching rows', async () => {
  const calls = [];
  const { list, views } = setup(async status => { calls.push(status); return status === 'archived' ? [forest] : [tide, forest]; });
  await list.refresh();
  await list.filter('archived');
  assert.deepEqual(calls, ['all', 'archived']);
  assert.equal(views.at(-2).phase, 'loading');
  assert.deepEqual(views.at(-1).rows, [forest]);
});

test('selection survives a filter that hides it and an empty success', async () => {
  const { list, views } = setup(async status => (status === 'all' ? [tide, forest] : status === 'archived' ? [forest] : []));
  await list.refresh();
  list.select(tide);
  await list.filter('archived');
  assert.equal(views.at(-1).selected, tide);
  await list.filter('paused');
  assert.equal(views.at(-1).phase, 'ready');
  assert.deepEqual(views.at(-1).rows, []);
  assert.equal(views.at(-1).selected, tide);
  await list.filter('all');
  assert.equal(views.at(-1).selected.id, 'tide');
});

test('failure is an error phase; retry uses the current filter and keeps the selection', async () => {
  let fail = false; const calls = [];
  const { list, views } = setup(async status => { calls.push(status); if (fail) throw new Error('Could not load projects'); return [forest]; });
  await list.refresh();
  list.select(forest);
  fail = true;
  await list.filter('archived');
  assert.equal(views.at(-1).phase, 'error');
  assert.equal(views.at(-1).selected, forest);
  fail = false;
  await list.refresh();
  assert.deepEqual(calls, ['all', 'archived', 'archived']);
  assert.equal(views.at(-1).phase, 'ready');
  assert.equal(views.at(-1).selected, forest);
});

test('only the latest filter response renders', async () => {
  const pending = {};
  const { list, views } = setup(status => new Promise(resolve => { pending[status] = resolve; }));
  const slow = list.filter('active');
  const fast = list.filter('archived');
  pending.archived([forest]); await fast;
  pending.active([tide]); await slow;
  assert.equal(views.at(-1).status, 'archived');
  assert.deepEqual(views.at(-1).rows, [forest]);
  assert.equal(views.filter(view => view.phase === 'ready').length, 1);
});
