import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { once } from 'node:events';
import { cp, mkdtemp, readFile, rm, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import test from 'node:test';

const plugin = new URL('../../', import.meta.url);

test('each evaluation supplies regular files and a setup contract', async () => {
  for (const name of ['design-brief', 'prototype-explore', 'prototype-promote']) {
    const root = new URL(`skills/${name}/`, plugin);
    assert.ok((await stat(new URL('evals/SETUP.md', root))).isFile());
    const suite = JSON.parse(await readFile(new URL('evals/evals.json', root), 'utf8'));
    assert.equal(suite.skill_name, name);
    assert.equal(new Set(suite.evals.map(e => e.id)).size, suite.evals.length);
    for (const scenario of suite.evals) {
      for (const path of scenario.files) assert.ok((await stat(new URL(path, root))).isFile(), `${name}: ${path}`);
    }
  }
});

test('variant fixture supports button arrows while protecting editing and tab keys', async () => {
  const handlers = {};
  const nodes = Object.fromEntries(['previous', 'next', 'detail-toggle', 'details', 'variant-label'].map(id => [id, {
    hidden: true, addEventListener: (name, handler) => { handlers[`${id}:${name}`] = handler; },
  }]));
  const location = { href: 'file:///fixture/index.html?variant=B', search: '?variant=B' };
  const context = vm.createContext({ URL, URLSearchParams, location,
    history: { pushState: (_state, _title, url) => { location.href = String(url); } },
    document: { querySelector: selector => nodes[selector.slice(1)], querySelectorAll: () => [],
      addEventListener: (name, handler) => { handlers[name] = handler; } },
    window: { addEventListener: () => {} },
  });
  const source = await readFile(new URL('skills/prototype-promote/evals/files/variant-board/scratch/explore/scripts/ui.js', plugin), 'utf8');
  vm.runInContext(source, context);
  function target(tag, role) {
    return { closest: selectors => selectors.split(',').some(s => s === tag || (role && s === `[role="${role}"]`)) };
  }
  const press = element => handlers.keydown({ target: element, key: 'ArrowRight', preventDefault() {} });
  press(target('button'));
  assert.equal(new URL(location.href).searchParams.get('variant'), 'C');
  for (const element of [target('input'), target('textarea'), target('select'), target('button', 'tab'), target('div', 'slider')]) {
    press(element);
    assert.equal(new URL(location.href).searchParams.get('variant'), 'C');
  }
  press(target('button'));
  assert.equal(new URL(location.href).searchParams.get('variant'), 'A');
});

async function startServer(root, mode, t) {
  const child = spawn(process.execPath, ['scripts/serve.mjs', mode], { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
  t.after(async () => {
    if (child.exitCode === null && child.signalCode === null) { const exited = once(child, 'exit'); child.kill(); await exited; }
  });
  return await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Fixture server did not start')), 8000);
    child.once('error', error => { clearTimeout(timeout); reject(error); });
    child.once('exit', code => { clearTimeout(timeout); reject(new Error(`Fixture server exited: ${code}`)); });
    child.stdout.on('data', chunk => {
      const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+\/activity/);
      if (match) { clearTimeout(timeout); resolve(new URL(match[0])); }
    });
  });
}

test('real app fixture isolates development assets from its production build', { timeout: 20000 }, async t => {
  const directory = await mkdtemp(join(tmpdir(), 'hm2-in-app-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const root = join(directory, 'app');
  await cp(fileURLToPath(new URL('skills/prototype-explore/evals/files/in-app/', plugin)), root, { recursive: true });
  execFileSync(process.execPath, ['scripts/build.mjs'], { cwd: root });
  execFileSync(process.execPath, ['scripts/check-production.mjs'], { cwd: root });
  const development = await startServer(root, '--dev', t);
  const production = await startServer(root, '--production', t);
  assert.match(await (await fetch(development)).text(), /src="\/__dev\/entry\.js"/);
  assert.equal((await fetch(new URL('/__dev/entry.js', development))).status, 200);
  assert.equal((await fetch(new URL('/__dev/entry.js', production))).status, 404);
  const baseline = await (await fetch(production)).text();
  assert.equal(await (await fetch(new URL('?variant=B', production))).text(), baseline);
  assert.doesNotMatch(baseline, /\/__dev\//);
  assert.match(baseline, /id="note-tab"/);
});
