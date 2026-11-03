// Synthetic local API and static server. No external credentials or dependencies.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, relative, extname } from 'node:path';

const root = fileURLToPath(new URL('.', import.meta.url));
const rows = [{ id: 'tide', name: 'Tide', status: 'active' }, { id: 'forest', name: 'Forest', status: 'archived' }, { id: 'north', name: 'North', status: 'active' }];
let fail = false;
const server = createServer(async (request, response) => {
  const url = new URL(request.url, 'http://127.0.0.1');
  if (url.pathname === '/__fixture__/mode' && request.method === 'PUT') {
    let body = ''; for await (const chunk of request) body += chunk;
    try { fail = JSON.parse(body).fail === true; response.end('{}'); } catch { response.writeHead(400).end(); }
    return;
  }
  if (request.method !== 'GET') { response.writeHead(405).end(); return; }
  if (url.pathname === '/api/projects') {
    const status = url.searchParams.get('status') || 'all';
    if (!['all', 'active', 'archived', 'paused'].includes(status)) { response.writeHead(400).end(); return; }
    await new Promise(resolve => setTimeout(resolve, status === 'active' ? 150 : 20));
    response.setHeader('Content-Type', 'application/json');
    if (fail) { response.writeHead(503).end('{"error":"fixture failure"}'); return; }
    response.end(JSON.stringify(status === 'all' ? rows : rows.filter(row => row.status === status)));
    return;
  }
  const path = resolve(root, '.' + decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
  const name = relative(root, path);
  if (name.startsWith('..') || name.startsWith('.git') || name.includes('\0')) { response.writeHead(404).end(); return; }
  try {
    response.setHeader('Content-Type', ({ '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' })[extname(path)] || 'text/plain');
    response.end(await readFile(path));
  } catch { response.writeHead(404).end(); }
});
server.listen(Number(process.env.PORT || 0), '127.0.0.1', () => console.log(`http://127.0.0.1:${server.address().port}/`));
