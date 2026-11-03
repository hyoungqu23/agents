import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { projects } from '../src/api.js';

test('API client reads filtered projects and the failure mode from the fixture server', async () => {
  const server = spawn(process.execPath, [fileURLToPath(new URL('../server.mjs', import.meta.url))], { env: { ...process.env, PORT: '0' } });
  const original = globalThis.fetch;
  try {
    const [line] = await once(server.stdout, 'data');
    const base = String(line).trim();
    globalThis.fetch = (url, options) => original(new URL(url, base), options);
    assert.deepEqual((await projects('archived')).map(row => row.id), ['forest']);
    assert.deepEqual((await projects('active')).map(row => row.id), ['tide', 'north']);
    assert.deepEqual(await projects('paused'), []);
    await fetch('/__fixture__/mode', { method: 'PUT', body: '{"fail":true}' });
    await assert.rejects(() => projects('archived'), /Could not load/);
    await fetch('/__fixture__/mode', { method: 'PUT', body: '{"fail":false}' });
    assert.equal((await projects('all')).length, 3);
  } finally { globalThis.fetch = original; server.kill(); }
});
