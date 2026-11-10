import assert from 'node:assert/strict';
import test from 'node:test';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { projects } from '../src/api.js';

test('real GET contract supports all four filters, empty success and 503 recovery', { timeout: 10000 }, async t => {
  // Use a private instance, leaving any existing fixture server untouched.
  const server = spawn(process.execPath, ['server.mjs'], {
    cwd: new URL('..', import.meta.url), env: { ...process.env, PORT: '0' }, stdio: ['ignore', 'pipe', 'pipe']
  });
  const exited = once(server, 'exit');
  let stderr = '';
  server.stderr.on('data', chunk => { stderr += chunk; });
  const originalFetch = globalThis.fetch;
  t.after(async () => {
    globalThis.fetch = originalFetch;
    if (server.exitCode === null && server.signalCode === null) server.kill();
    await exited;
  });
  const base = await new Promise((resolve, reject) => {
    let output = '';
    server.stdout.on('data', chunk => {
      output += chunk;
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+\//);
      if (match) resolve(match[0]);
    });
    server.once('error', reject);
    server.once('exit', code => reject(new Error(`Server exited ${code}: ${stderr}`)));
  });
  globalThis.fetch = url => originalFetch(new URL(url, base));
  assert.deepEqual((await projects()).map(row => row.id), ['tide', 'forest', 'north']);
  assert.deepEqual((await projects('active')).map(row => row.id), ['tide', 'north']);
  assert.deepEqual((await projects('archived')).map(row => row.id), ['forest']);
  assert.deepEqual(await projects('paused'), []);
  try {
    await originalFetch(new URL('/__fixture__/mode', base), { method: 'PUT', body: JSON.stringify({ fail: true }) });
    await assert.rejects(() => projects('active'), /Could not load projects/);
  } finally {
    await originalFetch(new URL('/__fixture__/mode', base), { method: 'PUT', body: JSON.stringify({ fail: false }) });
  }
  assert.deepEqual((await projects('active')).map(row => row.id), ['tide', 'north']);
});
