#!/usr/bin/env python3
"""Loopback-only HTTP/SQLite evaluation app. DB must live outside this source tree."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import socket

PAGE = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>프로젝트 QA</title>
<style>body{font:17px system-ui,sans-serif;max-width:680px;margin:60px auto;padding:24px;background:#f5f7fa;color:#172334}form{display:flex;gap:12px;flex-wrap:wrap}input,button{font:inherit;padding:12px;border:1px solid #a0aec0;border-radius:6px}button{background:#1858d1;color:white}button:disabled{background:#bbc2cf}li{display:flex;align-items:center;gap:20px;padding:14px;background:white;margin:12px 0}.name{width:90px;overflow:hidden;white-space:nowrap}button:focus-visible,input:focus-visible{outline:3px solid #8f39cf;outline-offset:3px}</style>
<h1>프로젝트 목록</h1><p>프로젝트를 저장하고 다시 불러와 확인하세요.</p>
<form id="form"><label>프로젝트 이름 <input id="name" required></label><button>저장</button></form>
<p id="message" role="status"></p><button id="refresh">다시 불러오기</button> <button disabled>보관 (미지원)</button><ul id="items"></ul>
<script>
async function load(){const r=await fetch('/api/items');const data=await r.json();document.querySelector('#items').replaceChildren(...data.items.map(item=>{const row=document.createElement('li');row.dataset.id=item.id;const name=document.createElement('span');name.className='name';name.textContent=item.name;const remove=document.createElement('button');remove.textContent='삭제';remove.onclick=async()=>{await fetch('/api/items/'+item.id,{method:'DELETE'});await load()};row.append(name,remove);return row}))}
document.querySelector('#refresh').onclick=load;
document.querySelector('#form').onsubmit=async(event)=>{event.preventDefault();const name=document.querySelector('#name').value;try{const r=await fetch('/api/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});if(!r.ok)throw Error('HTTP '+r.status);await r.json();document.querySelector('#message').textContent='저장됨';await load()}catch(error){document.querySelector('#message').textContent='저장 결과 미확인. 다시 불러오기로 확인하세요.'}};load();
</script></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    database = args.db.resolve()
    if database.is_relative_to(Path(__file__).resolve().parent):
        raise SystemExit('Put the database outside the fixture source')
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body, content_type='application/json'):
            raw = body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status); self.send_header('Content-Type', content_type); self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)

        def do_GET(self):
            if self.path == '/':
                self.reply(200, PAGE, 'text/html; charset=utf-8')
            elif self.path == '/api/items':
                with sqlite3.connect(database) as connection:
                    data = [{'id': str(i), 'name': n} for i, n in connection.execute('SELECT id,name FROM items ORDER BY id')]
                self.reply(200, {'items': data})
            elif self.path == '/build':
                self.reply(200, {'build': 'dogfood-fixture-v1', 'backend': 'local-sqlite'})
            else:
                self.reply(404, {'error': 'not_found'})

        def do_POST(self):
            if self.path != '/api/items':
                self.reply(404, {'error': 'not_found'}); return
            try:
                data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
                name = data['name']
                if not isinstance(name, str) or not 1 <= len(name) <= 200:
                    raise ValueError('name')
            except (KeyError, ValueError, TypeError):
                self.reply(400, {'error': 'invalid_name'}); return
            with sqlite3.connect(database) as connection:
                cursor = connection.execute('INSERT INTO items(name) VALUES (?)', (name,))
                identifier = str(cursor.lastrowid)
            if name == 'lost-response':
                self.connection.shutdown(socket.SHUT_RDWR); self.connection.close(); return
            self.reply(201, {'id': identifier, 'name': name})

        def do_DELETE(self):
            identifier = self.path.removeprefix('/api/items/')
            if not self.path.startswith('/api/items/') or not identifier.isdigit():
                self.reply(404, {'error': 'not_found'}); return
            with sqlite3.connect(database) as connection:
                connection.execute('DELETE FROM items WHERE id=?', (int(identifier),))
            self.reply(200, {'deleted': identifier})

        def log_message(self, fmt, *values):
            print(fmt % values, flush=True)

    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print('http://127.0.0.1:' + str(server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
