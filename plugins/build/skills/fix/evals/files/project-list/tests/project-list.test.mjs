import assert from 'node:assert/strict';
import test from 'node:test';
import { createProjectList } from '../src/project-list.js';

test('filter and empty success preserve the selected project', async () => {
  const tide = { id: 'tide', name: 'Tide', status: 'active' };
  const list = createProjectList({ loadProjects: async status => status === 'all' ? [tide] : [], onChange() {} });
  await list.load(); list.select(tide);
  await list.load('paused');
  assert.deepEqual(list.getState().projects, []);
  assert.equal(list.getState().selected, tide);
  assert.equal(list.getState().error, null);
});
