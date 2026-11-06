"""Install once, configure scope, then run or inspect the local review service."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import time

from . import __version__, agent, delivery
from .engine import Engine
from .github import ApiError, GitHub
from .state import HarnessError, Store, defaults, device, home, instance_lock, load_config, read_json, save_json, validate_config
from .trusted import bundle_root


def setup(args, root):
    config = load_config(root) if (root / 'config.json').exists() else defaults()
    config['provider'] = args.provider or config['provider']
    for name, program in [('gh_path', 'gh'), ('git_path', 'git'), ('agent_path', config['provider'])]:
        path = shutil.which(program)
        if not path:
            raise HarnessError('Install and authenticate the required program: ' + program)
        config[name] = str(Path(path).resolve())
    agent.probe(config['provider'], config['agent_path']); bundle_root()
    config['login'] = GitHub(config, root).login()
    repository = args.repo
    if not repository and not config['repositories']:
        if not sys.stdin.isatty():
            raise HarnessError('First setup needs --repo owner/name (and optional --path checkout)')
        repository = input('GitHub repository (owner/name): ').strip()
    if repository:
        row = next((r for r in config['repositories'] if r['name'] == repository), None)
        if row is None:
            row = {'name': repository, 'teams': []}; config['repositories'].append(row)
        if args.path:
            row['path'] = str(Path(args.path).expanduser().resolve())
            subprocess.run([config['git_path'], '-C', row['path'], 'rev-parse', '--show-toplevel'], check=True, capture_output=True)
        if args.team:
            row['teams'] = sorted(set(args.team))
    if args.pending:
        if not args.single_writer:
            raise HarnessError('Use --single-writer after stopping other devices for this account/repository scope')
        config.update(pending_enabled=True, active_device=device(root))
    save_json(root / 'config.json', validate_config(config))
    print(f'Configured {config["login"]}; {len(config["repositories"])} repositories; Pending writes: {config["pending_enabled"]}')
    print('Next: hm2-review-harness doctor; brew services start hm2-review-harness')


def doctor(config, root):
    agent.probe(config['provider'], config['agent_path']); bundle_root()
    login = GitHub(config, root).login()
    print(json.dumps({'version': __version__, 'login': login, 'provider': config['provider'],
                      'tool_access': 'disabled', 'repositories': config['repositories'],
                      'pending_enabled': config['pending_enabled'],
                      'active_on_this_device': config['active_device'] == device(root),
                      'note': 'CLI capability/auth checks do not establish model quality or live Pending API compatibility.'}, ensure_ascii=False, indent=2))


def serve(root, once=False):
    stopping = False
    def stop(_signal, _frame):
        nonlocal stopping
        stopping = True
        raise KeyboardInterrupt
    old = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        with instance_lock(root):
            engine = Engine(load_config(root), root)
            engine.store.recover(); next_poll = 0
            try:
                while not stopping:
                    engine.configure(load_config(root))
                    if not engine.config['paused'] and time.monotonic() >= next_poll:
                        try:
                            engine.poll()
                        except (HarnessError, OSError, subprocess.SubprocessError) as error:
                            save_json(root / 'service-status.json', {'status': 'auth_required' if isinstance(error, ApiError) and error.status == 401 else 'collection_failed', 'error': str(error), 'at': time.time()})
                            print(str(error), file=sys.stderr, flush=True)
                        next_poll = time.monotonic() + engine.config['poll_seconds']
                    key = engine.run_one() if not stopping else None
                    if key:
                        row = next(r for r in engine.store.rows() if r['id'] == key)
                        print(f'{key[:12]} {row["scenario"]} {row["status"]}', flush=True)
                        if sys.platform == 'darwin' and shutil.which('osascript'):
                            subprocess.run(['/usr/bin/osascript', '-e', 'on run argv\ndisplay notification (item 1 of argv) with title "HM2 Review"\nend run',
                                            f'{row["scenario"]}: {row["status"]}'], capture_output=True, timeout=10)
                    if once:
                        return
                    if not key:
                        time.sleep(1)
            finally:
                engine.store.close()
    except KeyboardInterrupt:
        pass
    finally:
        for sig, handler in old.items():
            signal.signal(sig, handler)


def export(root, path, include_history):
    config = load_config(root)
    safe = {k: config[k] for k in ('schema_version', 'hostname', 'provider', 'poll_seconds', 'timeout_seconds', 'daily_runs', 'max_packet_bytes', 'retention_days', 'max_state_bytes')}
    safe['repositories'] = [{'name': r['name'], 'teams': r.get('teams', [])} for r in config['repositories']]
    payload = {'schema_version': 1, 'config': safe, 'history': [], 'receipts': {}}
    if include_history:
        store = Store(root)
        try:
            for row in store.db.execute('SELECT event,scenario,result FROM jobs WHERE result IS NOT NULL ORDER BY created'):
                event = json.loads(row['event'])
                if event.get('pr') and row['result']:
                    payload['history'].append({'scenario': row['scenario'], 'event': event, 'result': json.loads(row['result'])})
        finally:
            store.close()
        for receipt in (root / 'receipts').glob('*/*.json'):
            payload['receipts'][str(receipt.relative_to(root / 'receipts'))] = read_json(receipt)
    save_json(path, payload)
    print(f'Exported to {path}; authentication, machine paths and source/model logs excluded')


def import_config(root, path):
    value = read_json(path)
    if value.get('schema_version') != 1:
        raise HarnessError('Unsupported export version')
    if (root / 'config.json').exists() or (root / 'state.sqlite3').exists():
        raise HarnessError('Import into a new state directory; existing state is protected')
    config = defaults(); config.update(value['config'])
    config.update(login='', agent_path='', gh_path='', git_path='', pending_enabled=False, active_device=None, paused=True)
    for repo in config['repositories']:
        repo.pop('path', None)
    save_json(root / 'config.json', validate_config(config))
    store = Store(root)
    try:
        for item in value.get('history', []):
            key = store.enqueue(item['scenario'], item['event'])
            store.update(key, 'imported', result=item['result'])
        for name, data in value.get('receipts', {}).items():
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts or len(relative.parts) != 2 or relative.suffix != '.json':
                raise HarnessError('Invalid imported receipt path')
            save_json(root / 'receipts' / relative, data)
    finally:
        store.close()
    print('Imported with writes disabled and service paused. Run setup to authenticate and map local paths.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--state-home', type=Path)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('setup'); p.add_argument('--repo'); p.add_argument('--path'); p.add_argument('--team', action='append')
    p.add_argument('--provider', choices=('codex', 'claude')); p.add_argument('--pending', action='store_true'); p.add_argument('--single-writer', action='store_true')
    sub.add_parser('doctor'); sub.add_parser('serve'); sub.add_parser('run-once'); sub.add_parser('inbox'); sub.add_parser('status')
    sub.add_parser('pause'); sub.add_parser('resume'); sub.add_parser('disable-pending')
    p = sub.add_parser('enqueue-pr'); p.add_argument('--repo', required=True); p.add_argument('--pr', type=int, required=True)
    p = sub.add_parser('notify-implementation'); p.add_argument('--worktree', type=Path, required=True); p.add_argument('--assessment', type=Path, required=True); p.add_argument('--inputs', type=Path)
    p = sub.add_parser('show'); p.add_argument('job')
    p = sub.add_parser('retry'); p.add_argument('job')
    p = sub.add_parser('reconcile'); p.add_argument('job')
    p = sub.add_parser('export'); p.add_argument('path', type=Path); p.add_argument('--include-history', action='store_true')
    p = sub.add_parser('import'); p.add_argument('path', type=Path)
    p = sub.add_parser('prune'); p.add_argument('--days', type=int, default=14); p.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv); root = args.state_home.expanduser().resolve() if args.state_home else home()
    try:
        if args.action == 'setup':
            setup(args, root); return 0
        if args.action == 'import':
            import_config(root, args.path); return 0
        config = load_config(root)
        if args.action == 'export':
            export(root, args.path, args.include_history); return 0
        if args.action in ('pause', 'resume', 'disable-pending'):
            if args.action == 'disable-pending':
                config.update(pending_enabled=False, active_device=None)
            else:
                config['paused'] = args.action == 'pause'
            save_json(root / 'config.json', config); return 0
        if not config['login']:
            raise HarnessError('Run setup to authenticate this device first')
        if args.action == 'doctor':
            doctor(config, root); return 0
        if args.action in ('serve', 'run-once'):
            serve(root, args.action == 'run-once'); return 0
        if args.action == 'prune':
            with instance_lock(root):
                store = Store(root)
                try:
                    print(json.dumps(store.prune(args.days, args.apply), indent=2))
                finally:
                    store.close()
            return 0
        if args.action in ('enqueue-pr', 'notify-implementation'):
            engine = Engine(config, root)
            try:
                job = engine.enqueue_pr(args.repo, args.pr, force=True) if args.action == 'enqueue-pr' else engine.notify_implementation(args.worktree, read_json(args.assessment), read_json(args.inputs) if args.inputs else None)
                print(job or 'No new input')
            finally:
                engine.store.close()
            return 0
        store = Store(root)
        try:
            if args.action in ('inbox', 'status'):
                print(json.dumps(store.rows(), ensure_ascii=False, indent=2)); return 0
            row = next((r for r in store.rows() if r['id'].startswith(args.job)), None)
            if row is None:
                raise HarnessError('Job not found in the recent inbox')
            if args.action == 'show':
                report = Path(row['run_dir']) / 'report.md' if row['run_dir'] else None
                print(report.read_text() if report and report.is_file() else json.dumps(row)); return 0
            if args.action == 'reconcile':
                if row['status'] in ('collecting', 'snapshotting', 'reviewing', 'saving'):
                    raise HarnessError('Wait for the active job to stop before reconciling its journals')
                if not json.loads(row['event']).get('pr'):
                    raise HarnessError('Local S1 reviews have no remote receipts to reconcile')
                result = delivery.inspect(config, GitHub(config, root), json.loads(row['event']), root)
                store.update(row['id'], result['status'], error=result['detail'])
                print(json.dumps(result)); return 0 if result['status'] == 'local_ready' else 2
            if row['status'] in ('collecting', 'snapshotting', 'reviewing', 'saving', 'write_unconfirmed'):
                raise HarnessError('Inspect remote state and durable receipts before retrying an uncertain write')
            store.update(row['id'], 'queued'); return 0
        finally:
            store.close()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, sqlite3.Error, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
