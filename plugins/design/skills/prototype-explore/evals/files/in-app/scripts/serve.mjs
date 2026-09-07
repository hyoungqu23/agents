import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, extname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const development = process.argv.includes('--dev');
const port = Number(process.argv.find(arg => arg.startsWith('--port='))?.split('=')[1] ?? 0);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };
const server = createServer(async (request, response) => {
  try {
    let path = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (path === '/' || path === '/activity') path = '/index.html';
    const devAsset = path.startsWith('/__dev/');
    if (devAsset && !development) { response.writeHead(404); response.end(); return; }
    const base = resolve(root, devAsset ? 'dev' : development ? 'src' : 'dist');
    const file = resolve(base, `.${devAsset ? path.slice('/__dev'.length) : path}`);
    const rel = relative(base, file);
    if (rel === '..' || rel.startsWith(`..${sep}`)) { response.writeHead(404); response.end(); return; }
    let content = await readFile(file);
    if (development && file === resolve(base, 'index.html') && !devAsset) {
      content = Buffer.from(content.toString().replace('<!-- development-entry -->', '<script type="module" src="/__dev/entry.js"></script>'));
    }
    response.writeHead(200, { 'Content-Type': types[extname(file)] ?? 'application/octet-stream' });
    response.end(content);
  } catch { response.writeHead(404); response.end(); }
});
server.listen(port, '127.0.0.1', () => console.log(`http://127.0.0.1:${server.address().port}/activity`));
