#!/usr/bin/env python3
"""Focused cross-host experiment; immutable evidence, no expected answers to executor."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

REPO = Path('/Users/hyoungmin/.codex/worktrees/product-flow-spec/agents')
sys.path.insert(0, str(REPO / 'scripts/behavioral'))
import cases


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def digests(files):
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def run(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, output / 'harness.py')
    version = subprocess.check_output(['claude', '--version'], text=True).strip()
    summary = {'executor': 'claude', 'version': version, 'model': args.model,
               'effort': 'medium', 'started_at': datetime.now(timezone.utc).isoformat(),
               'runs': [], 'status': 'running', 'mode': args.mode}
    write(output / 'summary.json', summary)
    for case in args.case:
        directory = output / case
        workspace = directory / 'workspace'
        workspace.mkdir(parents=True)
        prompt, before, origin = cases.prepare(REPO, case, workspace)
        task = prompt.split('\n', 1)[1]
        if args.mode == 'baseline':
            shutil.rmtree(workspace / '.eval-plugins')
            before = cases.snapshot(workspace)
        prompt = ('/product:flow-spec ' if args.mode == 'explicit' else '') + task
        (directory / 'prompt.txt').write_text(prompt)
        write(directory / 'before.sha256.json', digests(before))
        for name, data in before.items():
            p = directory / 'before' / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        command = ['claude', '-p', '--model', args.model, '--effort', 'medium',
                   '--output-format', 'stream-json', '--verbose', '--no-session-persistence',
                   '--strict-mcp-config', '--setting-sources', 'project',
                   '--permission-mode', 'acceptEdits', '--permission-prompts', 'none',
                   '--tools', 'Read,Write,Edit,Bash,Skill', '--max-budget-usd', '2',
                   '--settings', json.dumps({'sandbox': {'enabled': True,
                       'autoAllowBashIfSandboxed': True, 'allowUnsandboxedCommands': False,
                       'network': {'allowedDomains': [], 'allowLocalBinding': False}}}),
                   '--disallowedTools', 'WebFetch', 'WebSearch', 'Bash(gh:*)', 'Bash(git push:*)']
        for plugin in sorted((workspace / '.eval-plugins').iterdir()) if args.mode != 'baseline' else []:
            command += ['--plugin-dir', str(plugin)]
        record = {'case': case, 'origin': origin, 'command': command, 'status': 'error'}
        summary['runs'].append(record)
        write(output / 'summary.json', summary)
        env = {k: v for k, v in os.environ.items() if k not in
               ('CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT', 'CLAUDE_CODE_SESSION_ID',
                'CLAUDE_CODE_CHILD_SESSION', 'CLAUDE_CODE_SESSION_ATTENDED', 'CLAUDE_PID',
                'CLAUDE_EFFORT', 'CLAUDE_CODE_MESSAGING_SOCKET', 'CLAUDE_CODE_MESSAGING_TOKEN')}
        start = time.monotonic()
        with (directory / 'events.jsonl').open('w') as out, (directory / 'stderr.log').open('w') as err:
            proc = subprocess.Popen(command, cwd=workspace, stdin=subprocess.PIPE,
                stdout=out, stderr=err, env=env, text=True, start_new_session=True)
            try:
                proc.communicate(prompt, timeout=600)
                record['returncode'] = proc.returncode
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                record['error'] = 'timeout after 600 seconds'
        events = []
        for line in (directory / 'events.jsonl').read_text().splitlines():
            try:
                event = json.loads(line)
                if isinstance(event, dict): events.append(event)
            except ValueError:
                pass
        result = next((e for e in reversed(events) if e.get('type') == 'result'), None)
        record['result'] = result
        record['skill_invocations'] = [c.get('input') for e in events if e.get('type') == 'assistant'
            for c in e.get('message', {}).get('content', []) if c.get('type') == 'tool_use' and c.get('name') == 'Skill']
        record['init'] = next((e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init'), None)
        after = cases.snapshot(workspace)
        write(directory / 'after.sha256.json', digests(after))
        record['checks'] = cases.grade(case, before, after)
        completed = record.get('returncode') == 0 and result and result.get('subtype') == 'success' and not result.get('is_error')
        if completed:
            record['status'] = 'passed' if all(c['passed'] for c in record['checks']) else 'failed'
        record['duration_seconds'] = round(time.monotonic() - start, 2)
        write(directory / 'result.json', record)
        write(output / 'summary.json', summary)
        print(case + ': ' + record['status'], flush=True)
        if not completed:
            # No retries for service, policy, quota or budget failures.
            break
    summary['finished_at'] = datetime.now(timezone.utc).isoformat()
    summary['status'] = 'passed' if len(summary['runs']) == len(args.case) and all(r['status'] == 'passed' for r in summary['runs']) else 'incomplete_or_failed'
    write(output / 'summary.json', summary)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--case', action='append', required=True, choices=cases.FLOW_CASES)
    p.add_argument('--mode', choices=('explicit', 'natural', 'baseline'), default='explicit')
    run(p.parse_args())
