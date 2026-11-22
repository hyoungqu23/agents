"""hstack seats: which CLI and model each pstack role runs on, and the one way to start a worker.

    seats      print every role's seats as JSON, from the seats file or the defaults
               (--defaults: the defaults alone)
    validate   check the seats file; setup-pstack runs this before it finishes
    preflight  check that the seats of the named roles can start now
    start      check one seat, record the request, then start it as an Orca worker

A seat is `<cli> [<model> [<effort>]]` with cli `claude`, `codex` or `agy`.
agy takes a Google model id that carries its own effort and nothing else.

`start` is the only place that calls `orca orchestration worker-start`. It runs
the preflight first and calls nothing when a check fails, and it writes the
request id to the run record before the call, so a lost response can be
looked up with `orca orchestration request-show` instead of starting a second
worker.

Exit codes: 0 done, 1 the worker did not start, 2 refused before starting,
3 the start's outcome is unknown.
"""
import argparse
import contextlib
import datetime
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

CLIS = {'claude': 'claude', 'codex': 'codex', 'agy': 'antigravity'}
EFFORTS = ('low', 'medium', 'high', 'xhigh')
SINGLE = ('feature, refactoring', 'bug-fix', 'perf-issue', 'hillclimb',
          'judgment and prose', 'swarm workers', 'agy fallback')
PANELS = ('arena runners', 'arena cross-judge pool', 'interrogate reviewers')
ROLES = SINGLE[:-2] + PANELS[:2] + ('swarm workers',) + PANELS[2:] + ('agy fallback',)
DEFAULTS = {
    'feature, refactoring': 'claude claude-opus-5-5 xhigh',
    'bug-fix': 'claude claude-opus-5-5 xhigh',
    'perf-issue': 'claude claude-opus-5-5 xhigh',
    'hillclimb': 'claude claude-opus-5-5 xhigh',
    'judgment and prose': 'claude claude-opus-5-5 xhigh',
    'arena runners': 'claude claude-fable-5-2 high, codex, agy gemini-4-neon-xhigh',
    'arena cross-judge pool': 'codex, agy gemini-4-neon-xhigh',
    'swarm workers': 'claude claude-opus-5-5 high',
    'interrogate reviewers': 'claude claude-fable-5-2 high, codex, agy gemini-4-neon-xhigh',
    'agy fallback': 'agy gemini-4-hydrogen-xhigh',
}
# The coordinator is a Claude Code session, so these need another vendor.
CROSS_VENDOR = PANELS
# Worktree names an arena judge reads must not say which seat wrote them.
NAMED_ROLES = ('arena runners',)
VENDOR_WORDS = re.compile(r'claude|codex|agy|gemini|gpt|openai|anthropic|google|opus|fable|sonnet'
                          r'|haiku|neon|argon|hydrogen|flash', re.I)
REPORT_RULES = ('command(orca orchestration send)', 'command(orca orchestration check)')


def home():
    return Path(os.environ.get('HOME') or Path.home())


def seats_file():
    return home() / '.config/hstack/seats.md'


def state_dir():
    return home() / '.local/state/hm2/hstack/runs'


def parse_seat(text):
    """A seat dict, or a string naming what is wrong with it."""
    tokens = text.split()
    if not tokens or tokens[0] not in CLIS:
        return f'"{text}": starts with one of {", ".join(CLIS)}'
    cli, rest = tokens[0], tokens[1:]
    if cli == 'agy':
        if len(rest) != 1:
            return f'"{text}": agy takes exactly one model id, which carries its effort'
        model = rest[0]
        if not model.startswith('gemini-') or 'orchestrator' in model:
            return f'"{text}": agy seats take a gemini-* id without "orchestrator"'
        return {'cli': cli, 'model': model, 'effort': None}
    if len(rest) > 2:
        return f'"{text}": at most a model and an effort'
    model = rest[0] if rest else None
    effort = rest[1] if len(rest) > 1 else None
    if model in EFFORTS:
        return f'"{text}": an effort needs a model before it'
    if effort is not None and effort not in EFFORTS:
        return f'"{text}": effort is one of {", ".join(EFFORTS)}'
    if cli == 'claude' and not (model or '').startswith('claude-'):
        return f'"{text}": a claude seat takes a claude-* model id'
    return {'cli': cli, 'model': model, 'effort': effort}


def parse_role(role, value):
    seats, problems = [], []
    for part in value.split(','):
        seat = parse_seat(part.strip())
        (problems if isinstance(seat, str) else seats).append(seat)
    problems = [f'{role}: {problem}' for problem in problems]
    if role in SINGLE and len(seats) + len(problems) != 1:
        problems.append(f'{role}: takes one seat')
    if role == 'agy fallback' and any(seat['cli'] != 'agy' for seat in seats):
        problems.append(f'{role}: takes an agy seat')
    if role in CROSS_VENDOR and seats and all(seat['cli'] == 'claude' for seat in seats):
        problems.append(f'{role}: needs a codex or agy seat; the coordinator is Claude')
    return seats, problems


def read_seats(path=None):
    """Return ({role: {'seats': [...], 'source': ...}}, problems)."""
    named = path is not None
    path = Path(path) if named else seats_file()
    lines = {}
    problems = []
    text = ''
    if path.exists() or path.is_symlink() or named:
        # Only the default file may be absent: a named one that is missing is a typo.
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as error:
            problems.append(f'{path}: cannot be read: {error}')
    if text:
        for number, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            role, colon, value = line.partition(':')
            role = role.strip()
            if not colon or role not in ROLES:
                problems.append(f'{path.name}:{number}: unknown role "{role}"')
            elif role in lines:
                problems.append(f'{path.name}:{number}: {role} is listed twice')
            else:
                lines[role] = value.strip()
    roles = {}
    for role in ROLES:
        value = lines.get(role, DEFAULTS[role])
        seats, found = parse_role(role, value)
        problems += found
        roles[role] = {'seats': seats, 'source': 'file' if role in lines else 'default'}
    return roles, problems


def run(*command, timeout=60):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def agy_models():
    """Model ids `agy models` lists, or None when it cannot be asked."""
    try:
        result = run('agy', 'models')
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return {line.split()[0] for line in result.stdout.splitlines()
            if line.strip() and not line.startswith('Fetching')}


def agy_rules():
    path = home() / '.gemini/antigravity-cli/settings.json'
    try:
        return json.loads(path.read_text(encoding='utf-8')).get('permissions', {}).get('allow', [])
    except (OSError, ValueError, AttributeError):
        return []


def orca_agents():
    """Agent ids this machine's Orca can start, or None when it cannot be asked."""
    try:
        listed = json.loads(run('orca', 'agent', 'installed', '--environment', 'local',
                                '--json').stdout)
        return {agent['id'] for agent in listed['result']['agents']}
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        return None


def covered(path, rules):
    """Whether a read_file rule opens path without asking."""
    target = Path(path).resolve()
    for rule in rules:
        found = re.fullmatch(r'read_file\((.+)\)', rule)
        if found:
            folder = Path(found.group(1)).resolve()
            if target == folder or folder in target.parents:
                return True
    return False


def preflight(seats, reads=()):
    """Everything that stops these seats from starting now, as sentences."""
    problems = []
    try:
        status = json.loads(run('orca', 'status', '--environment', 'local', '--json').stdout)
        runtime = status['result']['runtime']
        if not (status.get('ok') and runtime.get('reachable') and runtime.get('state') == 'ready'):
            problems.append(f'Orca runtime is not ready: {json.dumps(runtime)[:300]}')
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        problems.append(f'cannot reach Orca with `orca status --json`: {error}')
    if not os.environ.get('ORCA_TERMINAL_HANDLE'):
        problems.append('this session is not in an Orca terminal (no ORCA_TERMINAL_HANDLE), '
                        'so Orca has no one to wake with the workers\' reports')
    models = None
    agents = orca_agents() if seats else set()
    if agents is None:
        problems.append('`orca agent installed` failed, so the seats cannot be checked')
        agents = set(CLIS.values())
    for seat in seats:
        if shutil.which(seat['cli']) is None:
            problems.append(f'{seat["cli"]} is not installed on this computer')
            continue
        if CLIS[seat['cli']] not in agents:
            problems.append(f'Orca cannot start the {CLIS[seat["cli"]]} agent here; '
                            'enable it in Orca\'s agent settings')
            continue
        if seat['cli'] != 'agy':
            continue
        if models is None:
            models = agy_models()
        if models is None:
            problems.append('`agy models` failed, so the agy model cannot be checked')
        elif seat['model'] not in models:
            allowed = sorted(m for m in models
                             if m.startswith('gemini-') and 'orchestrator' not in m)
            problems.append(f'agy does not offer {seat["model"]}; it offers {", ".join(allowed)}')
    if any(seat['cli'] == 'agy' for seat in seats):
        rules = agy_rules()
        for rule in REPORT_RULES:
            if rule not in rules:
                problems.append(f'agy cannot report without asking: add "{rule}" to '
                                'permissions.allow in ~/.gemini/antigravity-cli/settings.json')
        for path in reads:
            if not covered(path, rules):
                problems.append(f'agy would ask before reading {path}: add a read_file rule '
                                'for a folder that holds it')
    return list(dict.fromkeys(problems))


@contextlib.contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(path.suffix + '.lock'), 'w') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def update_record(path, change):
    with locked(path):
        record = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {
            'created': now(), 'base_commit': base_commit(), 'run_id': None, 'seats': []}
        change(record)
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.record-')
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(record, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
        os.replace(temporary, path)
        return record


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def base_commit():
    try:
        result = run('git', 'rev-parse', 'HEAD')
        return result.stdout.strip() if result.returncode == 0 else None
    except OSError:
        return None


def find(data, *keys):
    """The first value under any of keys, anywhere in a nested receipt."""
    if isinstance(data, dict):
        for key in keys:
            if data.get(key) is not None:
                return data[key]
        values = data.values()
    elif isinstance(data, list):
        values = data
    else:
        return None
    for value in values:
        found = find(value, *keys)
        if found is not None:
            return found
    return None


def kickoff(seat, instructions, body):
    """The worker's spec. agy reads nothing outside its workspace without asking, so it gets the text."""
    if not instructions:
        return body
    if seat['cli'] == 'agy':
        text = Path(instructions).read_text(encoding='utf-8').strip()
        return f'{text}\n\n---\n\n{body}'
    return f'Read {Path(instructions).resolve()} before anything else.\n\n{body}'


def pick_seat(roles, args):
    """(index in the role, seat) to start, or a sentence saying why there is none.

    A fallback keeps the index of the seat it replaces.
    """
    seats = roles[args.role]['seats']
    index = args.index
    if index is None and args.fallback:
        # Only an agy seat falls back; with more than one, say which.
        agy = [number for number, seat in enumerate(seats) if seat['cli'] == 'agy']
        if len(agy) != 1:
            return f'{args.role} has {len(agy)} agy seats; give --index for the one that stopped'
        index = agy[0]
    if index is None:
        # Arena's judge is the first seat from a vendor other than the coordinator's.
        index = next((number for number, seat in enumerate(seats) if seat['cli'] != 'claude'), 0) \
            if args.role == 'arena cross-judge pool' else 0
    if not 0 <= index < len(seats):
        return f'{args.role} has {len(seats)} seats; there is no seat {index}'
    if args.role == 'arena cross-judge pool' and seats[index]['cli'] == 'claude':
        return 'a claude seat cannot judge for a Claude coordinator'
    if args.fallback:
        if seats[index]['cli'] != 'agy':
            return f'seat {index} of {args.role} is not an agy seat, so it has no fallback'
        return index, roles['agy fallback']['seats'][0]
    return index, seats[index]


def checked_arguments(args):
    """What is wrong with the arguments, before anything is written."""
    problems = []
    if args.timeout_ms is not None and args.timeout_ms <= 0:
        problems.append('--timeout-ms must be a positive number of milliseconds')
    for flag, value in (('--spec-file', args.spec_file), ('--instructions', args.instructions)):
        if value:
            try:
                Path(value).read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError) as error:
                problems.append(f'{flag} {value} cannot be read: {error}')
    if bool(args.task) != bool(args.retry_of):
        problems.append('--task and --retry-of go together: a retry continues the failed Task')
    if args.fallback and not args.task:
        problems.append('--fallback is another attempt at the failed Task; give --task and --retry-of')
    if args.task and (args.spec_file or args.instructions):
        problems.append('a retry reuses its Task\'s spec; leave out --spec-file and --instructions')
    if not args.task and not args.spec_file:
        problems.append('a new worker needs --spec-file')
    if args.role in NAMED_ROLES:
        # The judge reads candidates by path, so no name on the way may say who wrote one.
        kind, _, selector = args.worktree.partition(':')
        if kind == 'path':
            # The folders above the worktree belong to the project, not the candidate.
            selector = Path(selector).name
        for label in (args.name, args.display_name, selector):
            if label and VENDOR_WORDS.search(label):
                problems.append(f'"{label}" says which seat wrote the candidate; '
                                'name it like candidate-a')
    return problems


def strings(data, keys):
    """Every string under any of keys, anywhere in a nested receipt."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, str):
                yield value
            yield from strings(value, keys)
    elif isinstance(data, list):
        for value in data:
            yield from strings(value, keys)


def outcome(returncode, receipt):
    """started, failed (Orca says nothing ran) or unknown."""
    if not isinstance(receipt, dict):
        return 'unknown'
    # Every value, not the first: a timed-out request says so in its recovery
    # advice, after an ordinary error code.
    states = set(strings(receipt, {'disposition', 'state', 'outcome', 'status', 'code'}))
    if 'outcome_unknown' in states:
        return 'unknown'
    # A worker that reached ready has started, even if a later step such as
    # --keep-open failed and made the command exit 1. Only the worker's own
    # state counts, not a nested step's.
    result = receipt.get('result')
    state = result.get('state') if isinstance(result, dict) else receipt.get('state')
    if (returncode == 0 and receipt.get('ok', True)) or state == 'ready':
        return 'started'
    # Refused before acting, such as a bad argument, or a start Orca saw fail.
    if receipt.get('error') or 'failed' in states:
        return 'failed'
    return 'unknown'


def start(args):
    roles, problems = read_seats(args.seats)
    if args.role not in roles:
        problems.append(f'unknown role "{args.role}"')
    if problems:
        return refuse(problems)
    picked = pick_seat(roles, args)
    if isinstance(picked, str):
        return refuse([picked])
    index, seat = picked
    refused = checked_arguments(args) + preflight([seat], args.reads)
    if refused:
        return refuse(refused)

    # Orca takes only a UUID here.
    request = str(uuid.uuid4())
    record = Path(args.record) if args.record else state_dir() / f'hstack-{request}.json'
    # A record belongs to one Run. Without --run Orca uses the session's, which
    # may be another one when an earlier run is resumed.
    try:
        known = (json.loads(record.read_text(encoding='utf-8')).get('run_id')
                 if record.is_file() else None)
    except (OSError, ValueError, AttributeError) as error:
        return refuse([f'{record} cannot be read: {error}'])
    if args.run and known and args.run != known:
        return refuse([f'{record} belongs to Run {known}, not {args.run}'])
    args.run = args.run or known
    command = ['orca', 'orchestration', 'worker-start', '--environment', 'local',
               '--agent', CLIS[seat['cli']], '--worktree', args.worktree,
               '--retry-request', request, '--json']
    entry = {'request_id': request, 'role': args.role, 'index': index, 'seat': seat,
             'fallback': args.fallback, 'worktree': args.worktree, 'name': args.name,
             'run_id': args.run, 'requested': now(), 'status': 'unknown'}
    if args.task:
        # Another attempt at the same Task keeps Orca's retry chain and its breaker.
        command += ['--task', args.task, '--retry-of', args.retry_of]
        entry.update(task_id=args.task, retry_of=args.retry_of)
    else:
        title = f'{args.task_title} · {request[-8:]}'
        spec = record.with_name(f'{record.stem}.{request[-8:]}.spec.md')
        spec.parent.mkdir(parents=True, exist_ok=True)
        # Private from the start, like the record: it holds the task and worker.md.
        fd = os.open(spec, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(kickoff(seat, args.instructions,
                                 Path(args.spec_file).read_text(encoding='utf-8')))
        command += ['--spec-file', str(spec), '--task-title', title]
        entry.update(task_title=title, spec=str(spec))
    if seat['model']:
        command += ['--model', seat['model']]
    if seat['effort']:
        command += ['--effort', seat['effort']]
    for flag, value in (('--name', args.name), ('--repo', args.repo),
                        ('--base-branch', args.base_branch), ('--display-name', args.display_name),
                        ('--timeout-ms', args.timeout_ms), ('--run', args.run)):
        if value:
            command += [flag, str(value)]
    if args.keep_open:
        command.append('--keep-open')

    # Written before the call: if the response is lost, these ids are how to ask.
    def request_first(data):
        data['seats'].append(entry)
        data['run_id'] = data.get('run_id') or args.run
    update_record(record, request_first)

    wait = args.timeout_ms / 1000 + 120 if args.timeout_ms else 900
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=wait)
    except (subprocess.TimeoutExpired, OSError) as error:
        print(json.dumps({'record': str(record), 'request_id': request, 'status': 'unknown',
                          'error': str(error)}, ensure_ascii=False))
        return 3
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError:
        receipt = None
    status = outcome(result.returncode, receipt)
    found = {'status': status, 'answered': now(),
             'run_id': find(receipt, 'runId', 'run_id') or args.run,
             'task_id': find(receipt, 'taskId', 'task_id') or args.task,
             'dispatch_id': find(receipt, 'dispatchId', 'dispatch_id'),
             'worker': find(receipt, 'terminal'),
             'stage': find(receipt, 'failedStage', 'stage') if status != 'started' else None}
    if status == 'started' and result.returncode != 0:
        found['warning'] = (find(receipt, 'message', 'lastError')
                            or 'the worker started but the command reported an error')
        # Orca writes why and how to recover there.
        if result.stderr.strip():
            found['stderr'] = result.stderr.strip()[-2000:]

    def answer(data):
        for seen in data['seats']:
            if seen['request_id'] == request:
                seen.update(found)
        data['run_id'] = data.get('run_id') or found['run_id']
    update_record(record, answer)
    print(json.dumps({'record': str(record), 'request_id': request, **found,
                      'receipt': receipt if receipt is not None else result.stdout[-2000:]},
                     ensure_ascii=False, indent=2))
    return {'started': 0, 'failed': 1}.get(status, 3)


def refuse(problems):
    print('refused before starting anything:', file=sys.stderr)
    for problem in problems:
        print(f'- {problem}', file=sys.stderr)
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--seats', type=Path, help='seats file (default ~/.config/hstack/seats.md)')
    commands = parser.add_subparsers(dest='command', required=True)
    listed = commands.add_parser('seats')
    listed.add_argument('--defaults', action='store_true',
                        help="hstack's defaults, whatever the seats file says")
    check = commands.add_parser('validate')
    check.add_argument('--offline', action='store_true',
                       help='skip asking agy which models it offers')
    ready = commands.add_parser('preflight')
    ready.add_argument('--role', action='append', required=True)
    ready.add_argument('--reads', nargs='*', default=[], help='paths agy seats will read')
    begin = commands.add_parser('start')
    begin.add_argument('--role', required=True)
    begin.add_argument('--index', type=int,
                       help="the seat's place in the role's list; the judge pool skips claude seats")
    begin.add_argument('--fallback', action='store_true', help='use the agy fallback seat')
    begin.add_argument('--task-title', default='hstack worker')
    begin.add_argument('--spec-file')
    begin.add_argument('--task', help='retry: the Task whose attempt failed')
    begin.add_argument('--retry-of', help='retry: the failed Dispatch')
    begin.add_argument('--run', help='the Orca Run, when this session is bound to another')
    begin.add_argument('--instructions', help='worker.md, prepended to the spec')
    begin.add_argument('--worktree', required=True,
                       help='Orca selector: current, new-top-level, path:<path>, ...')
    begin.add_argument('--name')
    begin.add_argument('--repo')
    begin.add_argument('--base-branch')
    begin.add_argument('--display-name')
    begin.add_argument('--timeout-ms', type=int)
    begin.add_argument('--keep-open', action='store_true')
    begin.add_argument('--reads', nargs='*', default=[], help='paths an agy seat will read')
    begin.add_argument('--record', help='run record file; one is created when omitted')
    args = parser.parse_args(argv)

    if args.command == 'start':
        return start(args)
    if args.command == 'seats' and args.defaults:
        # setup-pstack needs them again after its first run wrote every role.
        print(json.dumps({role: {'seats': parse_role(role, DEFAULTS[role])[0],
                                 'source': 'default'} for role in ROLES}, indent=2))
        return 0
    roles, problems = read_seats(args.seats)
    if args.command == 'seats':
        print(json.dumps(roles, indent=2))
        return 1 if problems else 0
    if args.command == 'validate':
        if not args.offline and not problems:
            used = [s for name, r in roles.items() if name != 'agy fallback'
                    for s in r['seats'] if s['cli'] == 'agy']
            # The fallback matters only when an agy seat can fall back, or the file names it.
            if used or roles['agy fallback']['source'] == 'file':
                used += roles['agy fallback']['seats']
            agy = used
            if agy:
                models = agy_models()
                if models is None:
                    problems.append('`agy models` failed; run again, or with --offline')
                else:
                    problems += [f'agy does not offer {s["model"]}'
                                 for s in agy if s['model'] not in models]
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0
    seats = []
    for role in args.role:
        if role == 'arena cross-judge pool' and role in roles:
            # One judge runs, chosen as start chooses it; the rest of the pool is not used.
            picked = pick_seat(roles, argparse.Namespace(role=role, index=None, fallback=False))
            seats += [picked[1]] if not isinstance(picked, str) else []
        else:
            seats += roles.get(role, {'seats': []})['seats']
    unknown = [role for role in args.role if role not in roles]
    found = problems + [f'unknown role "{role}"' for role in unknown] + preflight(seats, args.reads)
    for problem in found:
        print(problem, file=sys.stderr)
    return 2 if found else 0


if __name__ == '__main__':
    sys.exit(main())
