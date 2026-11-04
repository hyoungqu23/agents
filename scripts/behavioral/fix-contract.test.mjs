// Coordinator-only behavioral probe. Inspect generated code before opting in.
import assert from 'node:assert/strict';
import test from 'node:test';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

if (!process.env.FIX_APP) throw new Error('Set FIX_APP to an inspected synthetic source checkout');
const { createProjectList } = await import(pathToFileURL(resolve(process.env.FIX_APP, 'src/project-list.js')));
const tide = { id: 'tide', name: 'Tide', status: 'active' };
const forest = { id: 'forest', name: 'Forest', status: 'archived' };
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };

for (const stale of ['success', 'failure']) {
  test(`latest filter survives an older ${stale}`, async () => {
    const slow = deferred(), fast = deferred();
    const list = createProjectList({ loadProjects: status => status === 'active' ? slow.promise : fast.promise, onChange() {} });
    list.select(tide);
    const old = list.load('active'), current = list.load('archived');
    fast.resolve([forest]); await current;
    if (stale === 'success') slow.resolve([tide]); else slow.reject(new Error('Old failure'));
    await old;
    assert.equal(list.getState().status, 'archived');
    assert.deepEqual(list.getState().projects, [forest]);
    assert.equal(list.getState().error, null);
    assert.equal(list.getState().selected, tide);
  });
}

test('empty success, error and Retry retain selection and the current filter', async () => {
  const calls = []; let fail = false;
  const list = createProjectList({ loadProjects: async status => {
    calls.push(status); if (fail) throw new Error('Failure');
    return status === 'all' ? [tide, forest] : status === 'archived' ? [forest] : [];
  }, onChange() {} });
  await list.load(); list.select(tide); await list.load('paused');
  assert.deepEqual(list.getState().projects, []); assert.equal(list.getState().error, null);
  fail = true; await list.load('archived'); assert.ok(list.getState().error);
  fail = false; await list.load();
  assert.deepEqual(calls, ['all', 'paused', 'archived', 'archived']);
  assert.deepEqual(list.getState().projects, [forest]); assert.equal(list.getState().selected, tide);
});
