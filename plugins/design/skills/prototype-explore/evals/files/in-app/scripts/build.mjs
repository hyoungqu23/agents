import { mkdir, readFile, writeFile, rm } from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const destination = new URL('dist/', root);
await rm(destination, { recursive: true, force: true });
await mkdir(destination);
for (const name of ['index.html', 'app.js', 'style.css']) {
  let content = await readFile(new URL(`src/${name}`, root), 'utf8');
  if (name === 'index.html') content = content.replace('<!-- development-entry -->', '');
  await writeFile(new URL(name, destination), content);
}
console.log('Built production activity assets.');
