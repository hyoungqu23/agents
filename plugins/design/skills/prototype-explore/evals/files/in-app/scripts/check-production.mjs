import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const expected = ['app.js', 'index.html', 'style.css'];
assert.deepEqual((await readdir(new URL('dist/', root))).sort(), expected);
for (const name of expected) {
  const source = await readFile(new URL(`src/${name}`, root), 'utf8');
  const output = await readFile(new URL(`dist/${name}`, root), 'utf8');
  assert.equal(output, name === 'index.html' ? source.replace('<!-- development-entry -->', '') : source);
  assert.ok(!output.includes('/__dev/'), `${name} includes a development entry`);
}
console.log('Production contains only the normal activity screen and assets.');
