import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {projects} from '../src/api.ts';

test('API owner uses all real server filters and distinguishes failure from empty success', async () => {
 const server = spawn(process.execPath, ['server.mjs'], {
  cwd: fileURLToPath(new URL('..', import.meta.url)),
  env: {...process.env, PORT: '0'},
  stdio: ['ignore', 'pipe', 'pipe'],
 });
 let errors = '';
 server.stderr.on('data', chunk => { errors += chunk; });
 try {
  const base = await new Promise<string>((resolve, reject) => {
   const timeout = setTimeout(() => reject(new Error(`Server startup timed out: ${errors}`)), 10000);
   server.once('error', error => { clearTimeout(timeout); reject(error); });
   server.once('exit', code => { clearTimeout(timeout); reject(new Error(`Server exited ${code}: ${errors}`)); });
   server.stdout.on('data', chunk => {
    const url = String(chunk).match(/http:\/\/127\.0\.0\.1:\d+/)?.[0];
    if (url) { clearTimeout(timeout); resolve(url); }
   });
  });
  const all = await projects('all', base);
  assert.deepEqual(all.map(row => row.id), ['tide', 'forest', 'north']);
  assert.deepEqual(await projects('active', base), all.filter(row => row.status === 'active'));
  assert.deepEqual(await projects('archived', base), all.filter(row => row.status === 'archived'));
  assert.deepEqual(await projects('paused', base), []);
  assert.equal((await fetch(`${base}/__fixture__/mode`, {method: 'PUT', body: JSON.stringify({fail: true})})).ok, true);
  await assert.rejects(projects('archived', base), /Could not load projects/);
  assert.equal((await fetch(`${base}/__fixture__/mode`, {method: 'PUT', body: JSON.stringify({fail: false})})).ok, true);
  assert.deepEqual(await projects('archived', base), [all[1]]);
 } finally {
  const exited = once(server, 'exit');
  server.kill('SIGINT');
  await exited;
 }
});
