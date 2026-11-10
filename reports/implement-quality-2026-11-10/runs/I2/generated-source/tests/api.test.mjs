import assert from 'node:assert/strict';
import test from 'node:test';
import { projects } from '../src/api.js';

test('API client forwards status and rejects a failed response', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async url => { assert.equal(url, '/api/projects?status=archived'); return { ok: true, json: async () => [] }; };
    assert.deepEqual(await projects('archived'), []);
    globalThis.fetch = async () => ({ ok: false });
    await assert.rejects(() => projects('active'), /Could not load/);
  } finally { globalThis.fetch = original; }
});
