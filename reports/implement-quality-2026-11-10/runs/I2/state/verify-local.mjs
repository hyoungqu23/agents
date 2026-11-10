import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { pathToFileURL } from 'node:url';
import { simulatedDocument } from '../source/tests/dom.mjs';

const source = '/private/tmp/skill-quality-20261110/implement/runs/I2-no-browser/source';
const server = spawn(process.execPath, ['server.mjs'], {
  cwd: source, env: { ...process.env, PORT: '0' }, stdio: ['ignore', 'pipe', 'pipe']
});
const nativeFetch = globalThis.fetch;
let url;
try {
  url = await new Promise((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('server URL timeout')), 5000);
    server.stdout.on('data', chunk => {
      output += chunk;
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+\//);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
    server.on('error', error => { clearTimeout(timeout); reject(error); });
    server.on('exit', code => { clearTimeout(timeout); reject(new Error(`server exited ${code}`)); });
    server.stderr.on('data', chunk => process.stderr.write(chunk));
  });
  console.log(`SERVER PRINTED ${url} (PORT=0)`);
  for (const [status, ids] of [
    ['all', ['tide', 'forest', 'north']], ['active', ['tide', 'north']],
    ['archived', ['forest']], ['paused', []]
  ]) {
    const response = await nativeFetch(new URL(`api/projects?status=${status}`, url));
    assert.equal(response.status, 200);
    const result = await response.json();
    assert.deepEqual(result.map(row => row.id), ids);
    console.log(`API ${status}: ${response.status}, ${JSON.stringify(ids)}`);
  }
  for (const path of ['', 'src/app.js', 'src/theme.css', 'src/ui.js', 'src/api.js']) {
    const response = await nativeFetch(new URL(path, url));
    assert.equal(response.status, 200);
    assert.ok((await response.text()).length > 0);
    console.log(`STATIC ${new URL(path, url)}: 200, nonempty`);
  }
  console.log('App scenarios below execute actual app/api/ui modules with a simulated Node DOM. No browser/layout verification.');
  const dom = simulatedDocument();
  globalThis.document = dom.document;
  globalThis.Option = dom.Option;
  const requests = [];
  globalThis.fetch = input => {
    const requestUrl = new URL(input, url);
    const request = nativeFetch(requestUrl).then(async response => {
      await response.clone().text();
      console.log(`APP REQUEST ${requestUrl}: ${response.status}`);
      return response;
    });
    requests.push({ url: requestUrl.href, promise: request });
    return request;
  };
  await import(pathToFileURL(`${source}/src/app.js`).href);
  const { toolbar, rows, selection } = dom.elements;
  const select = toolbar.children[0].children[0];
  const count = toolbar.children[1];
  async function until(predicate) {
    const deadline = Date.now() + 3000;
    while (!predicate()) {
      assert.ok(Date.now() < deadline, 'app outcome timeout');
      await new Promise(resolve => setTimeout(resolve, 5));
    }
  }
  function change(status) { select.value = status; select.dispatch('change'); }
  assert.equal(count.textContent, '3 projects');
  rows.children[0].click();
  assert.equal(selection.textContent, 'Tide');
  change('archived');
  await until(() => rows.textContent === 'Forest — archived');
  assert.equal(count.textContent, '1 project');
  assert.equal(selection.textContent, 'Tide');
  change('active');
  await until(() => count.textContent === '2 projects');
  assert.equal(rows.children[0].getAttribute('aria-pressed'), 'true');
  change('paused');
  await until(() => count.textContent === '0 projects');
  assert.equal(rows.textContent, 'No projects found.');
  assert.equal(selection.textContent, 'Tide');
  console.log('PASS real API: filter/count, hidden selection, restored highlight, empty success');

  async function mode(fail) {
    const response = await nativeFetch(new URL('__fixture__/mode', url), {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fail })
    });
    assert.equal(response.status, 200);
    console.log(`FIXTURE mode fail=${fail}: ${response.status}`);
  }
  await mode(true);
  change('archived');
  await until(() => rows.children[0]?.getAttribute('role') === 'alert');
  assert.equal(rows.textContent, 'Could not load projects. Retry');
  assert.equal(count.textContent, '');
  assert.equal(selection.textContent, 'Tide');
  await mode(false);
  rows.children[0].children[0].click();
  assert.ok(requests.at(-1).url.endsWith('status=archived'));
  await until(() => rows.textContent === 'Forest — archived');
  assert.equal(count.textContent, '1 project');
  assert.equal(selection.textContent, 'Tide');
  console.log('PASS real API: 503 alert distinct from empty, current-filter Retry, retained selection');

  change('active');
  change('archived');
  await until(() => rows.textContent === 'Forest — archived');
  await Promise.all(requests.map(request => request.promise));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(rows.textContent, 'Forest — archived');
  assert.equal(count.textContent, '1 project');
  assert.equal(selection.textContent, 'Tide');
  console.log('PASS real API: slow active response cannot overwrite newer archived response');
  console.log('PASS all local integration assertions; no browser was opened');
} finally {
  globalThis.fetch = nativeFetch;
  delete globalThis.document;
  delete globalThis.Option;
  if (server.exitCode === null) {
    server.kill('SIGTERM');
    await once(server, 'exit');
  }
  console.log('SERVER stopped');
}
