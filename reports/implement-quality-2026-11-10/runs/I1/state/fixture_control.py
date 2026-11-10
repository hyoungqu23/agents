import json, time, urllib.request
from pathlib import Path
state = Path(__file__).parent
last = None
while True:
    try:
        command = json.loads((state / 'fixture-command.json').read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        time.sleep(0.005)
        continue
    if command['id'] == last:
        time.sleep(0.005)
        continue
    last = command['id']
    if command.get('stop'):
        break
    started = time.time()
    body = json.dumps(command['body']).encode() if 'body' in command else None
    request = urllib.request.Request('http://127.0.0.1:62963' + command['path'], data=body, method=command.get('method', 'GET'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = {'id': last, 'command': command, 'status': response.status, 'response': response.read().decode()}
    except Exception as error:
        result = {'id': last, 'command': command, 'error': str(error)}
    result['elapsed_ms'] = round((time.time() - started) * 1000)
    with (state / 'fixture-control-trace.jsonl').open('a') as log:
        log.write(json.dumps(result) + '\n')
    temp = state / 'fixture-response.tmp'
    temp.write_text(json.dumps(result))
    temp.replace(state / 'fixture-response.json')
