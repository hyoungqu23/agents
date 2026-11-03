import assert from 'node:assert/strict';
import test from 'node:test';
import { createProjectList } from '../src/project-list.js';

const tide = { id: 'tide', name: 'Tide', status: 'active' };
const forest = { id: 'forest', name: 'Forest', status: 'archived' };
const north = { id: 'north', name: 'North', status: 'active' };
const all = [tide, forest, north];

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test('filters fetch matching results and selection survives hidden and empty results', async () => {
  const calls = [];
  const list = createProjectList({
    loadProjects: async status => {
      calls.push(status);
      return status === 'all' ? all : all.filter(project => project.status === status);
    },
    onChange: () => {},
  });
  await list.load();
  assert.equal(list.getState().projects.length, 3);
  list.select(tide);
  await list.load('archived');
  assert.deepEqual(list.getState().projects, [forest]);
  assert.equal(list.getState().selected, tide);
  await list.load('paused');
  assert.deepEqual(list.getState().projects, []);
  assert.equal(list.getState().error, null);
  assert.equal(list.getState().loading, false);
  assert.equal(list.getState().selected, tide);
  await list.load('active');
  assert.deepEqual(list.getState().projects, [tide, north]);
  assert.equal(list.getState().selected.id, 'tide');
  assert.deepEqual(calls, ['all', 'archived', 'paused', 'active']);
});

test('loading and errors keep the selection; retry fetches the current filter', async () => {
  let fail = true;
  const calls = [];
  const states = [];
  const list = createProjectList({
    loadProjects: async status => {
      calls.push(status);
      if (fail) throw new Error('Could not load projects');
      return [forest];
    },
    onChange: state => states.push(state),
  });
  list.select(tide);
  const pending = list.load('archived');
  assert.equal(list.getState().loading, true);
  assert.equal(list.getState().error, null);
  assert.equal(list.getState().selected, tide);
  await pending;
  assert.match(list.getState().error.message, /Could not load/);
  assert.equal(list.getState().loading, false);
  assert.equal(list.getState().selected, tide);
  fail = false;
  await list.load();
  assert.deepEqual(calls, ['archived', 'archived']);
  assert.deepEqual(list.getState().projects, [forest]);
  assert.equal(list.getState().error, null);
  assert.equal(list.getState().selected, tide);
  assert.equal(states.filter(state => state.loading).length, 2);
});

for (const stale of ['success', 'failure']) {
  test(`stale ${stale} cannot replace the latest filter result`, async () => {
    const slow = deferred();
    const fast = deferred();
    const list = createProjectList({
      loadProjects: status => status === 'active' ? slow.promise : fast.promise,
      onChange: () => {},
    });
    list.select(tide);
    const active = list.load('active');
    const archived = list.load('archived');
    fast.resolve([forest]);
    await archived;
    if (stale === 'success') slow.resolve([tide, north]);
    else slow.reject(new Error('Old request failed'));
    await active;
    assert.equal(list.getState().status, 'archived');
    assert.deepEqual(list.getState().projects, [forest]);
    assert.equal(list.getState().error, null);
    assert.equal(list.getState().loading, false);
    assert.equal(list.getState().selected, tide);
  });
}
