"""hstack's seats file and worker launcher, against stand-ins for orca, agy, codex and claude."""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'plugins/hstack/scripts/hstack_seats.py'
spec = importlib.util.spec_from_file_location('hstack_seats', SCRIPT)
seats = importlib.util.module_from_spec(spec)
# A __pycache__ folder in the plugin would be a file upstream.lock.json does not list.
writes_bytecode, sys.dont_write_bytecode = sys.dont_write_bytecode, True
try:
    spec.loader.exec_module(seats)
finally:
    sys.dont_write_bytecode = writes_bytecode

ORCA = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
with open(os.environ['FAKE_CALLS'], 'a') as log:
    log.write(json.dumps(sys.argv[1:]) + '\n')
args = sys.argv[1:]
if args != ['status', '--environment', 'local', '--json'] and args[:2] != ['agent', 'installed'] \
        and '--environment' not in args:
    print(json.dumps({'ok': False, 'error': {'message': 'not pinned to the local Orca'}}))
    sys.exit(1)
if args[:1] == ['status']:
    state = os.environ.get('FAKE_ORCA_STATE', 'ready')
    print(json.dumps({'ok': True, 'result': {'runtime': {'state': state, 'reachable': state == 'ready'}}}))
elif args[:2] == ['agent', 'installed']:
    if '--environment' not in args:
        sys.exit(1)
    ids = os.environ.get('FAKE_AGENTS', 'claude,codex,antigravity').split(',')
    print(json.dumps({'ok': True, 'result': {'agents': [{'id': i} for i in ids]}}))
elif args[:2] == ['orchestration', 'worker-start']:
    record = Path(os.environ['FAKE_RECORD'])
    # The launcher must have written the request before calling.
    request = sys.argv[sys.argv.index('--retry-request') + 1]
    if request not in record.read_text():
        print(json.dumps({'ok': False, 'error': {'message': 'request not recorded first'}}))
        sys.exit(1)
    mode = os.environ.get('FAKE_START', 'ready')
    if mode == 'garbled':
        print('connection reset')
        sys.exit(1)
    if mode == 'failed':
        print(json.dumps({'ok': False, 'result': {'state': 'failed', 'stage': 'agent_readiness'}}))
        sys.exit(1)
    if mode == 'outcome_unknown':
        print(json.dumps({'ok': False, 'result': {'state': 'outcome_unknown', 'taskId': 'task_1',
                                                   'dispatchId': 'ctx_1', 'stage': 'agent_readiness'}}))
        sys.exit(1)
    if mode == 'timeout':
        print(json.dumps({'ok': False, 'error': {'code': 'runtime_timeout', 'message': 'timed out',
                          'data': {'recovery': {'disposition': 'outcome_unknown'}}}}))
        sys.exit(1)
    if mode == 'keep_open_failed':
        print(json.dumps({'ok': False, 'result': {'state': 'ready', 'dispatchId': 'ctx_1',
                          'taskId': 'task_1', 'runId': 'run_1', 'terminal': 'term_1'},
                          'error': {'code': 'keep_open_failed', 'message': 'could not keep open'}}))
        print('recover with: orca terminal keep-open term_1', file=sys.stderr)
        sys.exit(1)
    if mode == 'error_code':
        print(json.dumps({'ok': False, 'error': {'code': 'outcome_unknown', 'message': 'lost'}}))
        sys.exit(1)
    if mode == 'null':
        print('null')
        sys.exit(1)
    print(json.dumps({'ok': True, 'result': {'dispatchId': 'ctx_1', 'taskId': 'task_1',
                                              'runId': 'run_1', 'state': 'ready',
                                              'terminal': 'term_1'}}))
'''
AGY = '''#!/bin/sh
echo "Fetching available models..."
printf 'gemini-4-neon-xhigh\\tGemini 4 Neon (XHigh)\\n'
printf 'gemini-4-hydrogen-xhigh\\tGemini 4 Hydrogen (XHigh)\\n'
printf 'gemini-pro-orchestrator-neon\\tOrchestrator (Neon)\\n'
printf 'claude-opus-5-5-high\\tClaude Opus 5.5 (High)\\n'
'''


class Fixture(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        for name, text in (('orca', ORCA), ('agy', AGY), ('codex', '#!/bin/sh\n'),
                           ('claude', '#!/bin/sh\n'), ('git', '#!/bin/sh\necho abc123\n')):
            (bin_dir / name).write_text(text)
            (bin_dir / name).chmod(0o755)
        self.home = self.root / 'home'
        self.calls = self.root / 'calls.jsonl'
        self.calls.touch()
        self.record = self.root / 'record.json'
        self.spec = self.root / 'spec.md'
        self.spec.write_text('Do the task.\n')
        self.instructions = self.root / 'worker.md'
        self.instructions.write_text('Worker rules.\n')
        self.workspaces = self.root / 'workspaces'
        self.settings({'permissions': {'allow': [
            *seats.REPORT_RULES, f'read_file({self.workspaces})']}})
        environment = {
            'HOME': str(self.home), 'PATH': f'{bin_dir}{os.pathsep}/usr/bin:/bin',
            'FAKE_CALLS': str(self.calls), 'FAKE_RECORD': str(self.record),
            'ORCA_TERMINAL_HANDLE': 'term_coordinator'}
        patcher = unittest.mock.patch.dict(os.environ, environment, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def settings(self, data):
        path = self.home / '.gemini/antigravity-cli/settings.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    def write_seats(self, text):
        path = self.home / '.config/hstack/seats.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def starts(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()
                if json.loads(line)[:2] == ['orchestration', 'worker-start']]

    def start(self, *extra, role='arena runners', index='0', spec=True):
        arguments = ['start', '--role', role, '--task-title', 'Review', '--worktree', 'current',
                     '--record', str(self.record)]
        arguments += ['--index', index] if index is not None else []
        arguments += ['--spec-file', str(self.spec)] if spec else []
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return seats.main(arguments + list(extra))



class SeatsFileTests(Fixture):
    def test_defaults_cover_every_role_and_pass(self):
        roles, problems = seats.read_seats()
        self.assertEqual(problems, [])
        self.assertEqual(set(roles), set(seats.ROLES))
        self.assertEqual([s['cli'] for s in roles['arena runners']['seats']],
                         ['claude', 'codex', 'agy'])
        self.assertEqual(roles['arena cross-judge pool']['seats'][0],
                         {'cli': 'codex', 'model': None, 'effort': None})
        self.assertEqual(seats.main(['validate']), 0)

    def test_file_lines_replace_their_role_only(self):
        self.write_seats('# comment\nswarm workers: agy gemini-4-hydrogen-xhigh\n\n'
                         'arena cross-judge pool: codex gpt-6.2-astra high\n')
        roles, problems = seats.read_seats()
        self.assertEqual(problems, [])
        self.assertEqual(roles['swarm workers'],
                         {'seats': [{'cli': 'agy', 'model': 'gemini-4-hydrogen-xhigh',
                                     'effort': None}], 'source': 'file'})
        self.assertEqual(roles['arena cross-judge pool']['seats'][0]['effort'], 'high')
        self.assertEqual(roles['bug-fix']['source'], 'default')

    def test_bad_seats_are_named(self):
        cases = {
            'swarm workers: agy claude-opus-5-5-high': 'gemini-* id',
            'swarm workers: agy gemini-pro-orchestrator-neon': 'orchestrator',
            'swarm workers: agy gemini-4-neon-xhigh high': 'exactly one model id',
            'bug-fix: codex high': 'effort needs a model',
            'bug-fix: claude claude-opus-5-5 max': 'effort is one of',
            'bug-fix: claude opus xhigh': 'claude-* model id',
            'bug-fix: claude': 'claude-* model id',
            'bug-fix: cursor composer': 'starts with one of',
            'bug-fix: codex, agy gemini-4-neon-xhigh': 'takes one seat',
            'arena runners: claude claude-opus-5-5 high, claude claude-fable-5-2 high':
                'needs a codex or agy seat',
            'interrogate reviewers: codex': 'takes at least two seats',
            'arena runners: agy gemini-4-neon-xhigh': 'takes at least two seats',
            'agy fallback: codex': 'takes an agy seat',
            'hardest tasks: codex': 'unknown role',
            'bug-fix: codex\nbug-fix: codex': 'listed twice',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.write_seats(text + '\n')
                _, problems = seats.read_seats()
                self.assertTrue(any(expected in p for p in problems), problems)
                self.assertEqual(seats.main(['validate', '--offline']), 1)

    def test_named_seats_file_must_exist_and_be_readable(self):
        self.assertEqual(seats.main(['--seats', str(self.root / 'typo.md'), 'validate']), 1)
        broken = self.root / 'broken.md'
        broken.write_bytes(b'bug-fix: codex \xff\n')
        _, problems = seats.read_seats(broken)
        self.assertTrue(any('cannot be read' in p for p in problems), problems)

    def test_validate_skips_agy_when_no_seat_uses_it(self):
        self.write_seats('arena runners: claude claude-opus-5-5 high, codex\n'
                         'arena cross-judge pool: codex\n'
                         'interrogate reviewers: claude claude-opus-5-5 high, codex\n')
        (self.root / 'bin/agy').unlink()
        self.assertEqual(seats.main(['validate']), 0)
        self.write_seats('arena cross-judge pool: codex\nagy fallback: agy gemini-4-neon-xhigh\n')
        self.assertEqual(seats.main(['validate']), 1)

    def test_defaults_are_listed_whatever_the_file_says(self):
        self.write_seats('bug-fix: codex\n')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(seats.main(['seats', '--defaults']), 0)
        listed = json.loads(output.getvalue())
        self.assertEqual(listed['bug-fix']['seats'],
                         [{'cli': 'claude', 'model': 'claude-opus-5-5', 'effort': 'xhigh'}])
        self.assertEqual(set(listed), set(seats.ROLES))

    def test_validate_asks_agy_for_its_models(self):
        self.write_seats('swarm workers: agy gemini-4-argon-high\n')
        self.assertEqual(seats.main(['validate', '--offline']), 0)
        self.assertEqual(seats.main(['validate']), 1)


class PreflightTests(Fixture):
    def problems(self, *roles, reads=()):
        roles_found, _ = seats.read_seats()
        return seats.preflight([s for r in roles for s in roles_found[r]['seats']], reads)

    def test_ready_machine_passes(self):
        self.assertEqual(self.problems('arena runners', reads=[self.workspaces / 'a/b']), [])

    def test_each_missing_piece_is_reported(self):
        os.environ['FAKE_ORCA_STATE'] = 'starting'
        del os.environ['ORCA_TERMINAL_HANDLE']
        (self.root / 'bin/codex').unlink()
        self.settings({'permissions': {'allow': ['command(orca orchestration send)']}})
        problems = self.problems('arena runners', reads=['/elsewhere/file'])
        for expected in ('Orca runtime is not ready', 'not in an Orca terminal',
                         'codex is not installed', 'command(orca orchestration check)',
                         'before reading /elsewhere/file'):
            self.assertTrue(any(expected in p for p in problems), (expected, problems))

    def test_judge_preflight_checks_only_the_judge_start_would_pick(self):
        os.environ['FAKE_AGENTS'] = 'claude,codex'
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(seats.main(['preflight', '--role', 'arena cross-judge pool']), 0)
            self.assertEqual(seats.main(['preflight', '--role', 'arena runners']), 2)

    def test_judge_preflight_can_check_a_later_seat_of_the_pool(self):
        os.environ['FAKE_AGENTS'] = 'claude,antigravity'
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(seats.main(['preflight', '--role', 'arena cross-judge pool']), 2)
            self.assertEqual(seats.main(['preflight', '--role', 'arena cross-judge pool',
                                         '--judge-index', '1']), 0)
            self.assertEqual(seats.main(['preflight', '--role', 'arena cross-judge pool',
                                         '--judge-index', '5']), 2)

    def test_agent_disabled_in_orca_is_reported(self):
        os.environ['FAKE_AGENTS'] = 'claude,antigravity'
        self.assertTrue(any('cannot start the codex agent' in p
                            for p in self.problems('arena runners')))

    def test_agy_model_must_be_offered(self):
        self.write_seats('arena runners: codex, agy gemini-4-argon-high\n')
        self.assertTrue(any('agy does not offer gemini-4-argon-high' in p
                            for p in self.problems('arena runners')))

    def test_claude_and_codex_seats_need_no_agy_rules(self):
        self.settings({})
        self.assertEqual(self.problems('feature, refactoring', 'bug-fix'), [])
        self.write_seats('arena cross-judge pool: codex\n')
        self.assertEqual(self.problems('arena cross-judge pool'), [])


class StartTests(Fixture):
    def test_start_records_the_request_first_and_maps_the_seat(self):
        self.assertEqual(self.start('--instructions', str(self.instructions), index='1'), 0)
        [call] = self.starts()
        self.assertEqual(call[call.index('--agent') + 1], 'codex')
        self.assertNotIn('--model', call)
        self.assertNotIn('--effort', call)
        request = call[call.index('--retry-request') + 1]
        record = json.loads(self.record.read_text())
        [entry] = record['seats']
        self.assertEqual(entry['request_id'], request)
        self.assertEqual((entry['status'], entry['task_id'], entry['dispatch_id'], entry['worker']),
                         ('started', 'task_1', 'ctx_1', 'term_1'))
        self.assertEqual(record['run_id'], 'run_1')
        self.assertTrue(entry['task_title'].startswith('Review · '))
        sent = Path(call[call.index('--spec-file') + 1]).read_text()
        self.assertEqual(sent, f'Read {self.instructions.resolve()} before anything else.\n\n'
                               'Do the task.\n')

    def test_claude_seat_passes_model_and_effort(self):
        self.assertEqual(self.start(index='0'), 0)
        [call] = self.starts()
        self.assertEqual(call[call.index('--model') + 1:call.index('--model') + 4:2],
                         ['claude-fable-5-2', 'high'])
        self.assertEqual(call[call.index('--agent') + 1], 'claude')

    def test_agy_seat_gets_the_instructions_inline_and_no_effort(self):
        self.assertEqual(self.start('--instructions', str(self.instructions), index='2'), 0)
        [call] = self.starts()
        self.assertEqual(call[call.index('--agent') + 1], 'antigravity')
        self.assertEqual(call[call.index('--model') + 1], 'gemini-4-neon-xhigh')
        self.assertNotIn('--effort', call)
        sent = Path(call[call.index('--spec-file') + 1]).read_text()
        self.assertEqual(sent, 'Worker rules.\n\n---\n\nDo the task.\n')

    def test_fallback_retries_the_same_task_on_the_agy_fallback_seat(self):
        self.assertEqual(self.start('--fallback', '--task', 'task_9', '--retry-of', 'ctx_9',
                                    index='2', spec=False), 0)
        [call] = self.starts()
        self.assertEqual(call[call.index('--model') + 1], 'gemini-4-hydrogen-xhigh')
        self.assertEqual(call[call.index('--task') + 1:call.index('--task') + 4:2],
                         ['task_9', 'ctx_9'])
        self.assertNotIn('--spec-file', call)
        self.assertNotIn('--task-title', call)
        [entry] = json.loads(self.record.read_text())['seats']
        self.assertEqual((entry['fallback'], entry['retry_of'], entry['index']), (True, 'ctx_9', 2))

    def test_fallback_replaces_only_the_agy_seat(self):
        retry = ('--fallback', '--task', 'task_9', '--retry-of', 'ctx_9')
        self.assertEqual(self.start(*retry, index=None, spec=False), 0)
        self.assertEqual(json.loads(self.record.read_text())['seats'][0]['index'], 2)
        self.assertEqual(self.start(*retry, role='arena cross-judge pool', index=None, spec=False), 0)
        self.assertEqual(json.loads(self.record.read_text())['seats'][1]['index'], 1)
        for index in ('0', '1'):
            with self.subTest(index=index):
                self.assertEqual(self.start(*retry, index=index, spec=False), 2)
        self.write_seats('arena runners: codex, agy gemini-4-neon-xhigh, agy gemini-4-hydrogen-xhigh\n')
        self.assertEqual(self.start(*retry, index=None, spec=False), 2)
        self.assertEqual(len(self.starts()), 2)

    def test_retry_arguments_go_together(self):
        self.assertEqual(self.start('--fallback', index='2'), 2)
        for extra in (['--task', 'task_9'], ['--retry-of', 'ctx_9'],
                      ['--task', 'task_9', '--retry-of', 'ctx_9', '--spec-file', 'x']):
            with self.subTest(extra=extra):
                self.assertEqual(self.start(*extra, index='1', spec=False), 2)
        self.assertEqual(self.start(index='1', spec=False), 2)
        self.assertEqual(self.starts(), [])

    def test_judge_is_the_first_seat_from_another_vendor(self):
        self.write_seats('arena cross-judge pool: claude claude-opus-5-5 high, codex\n')
        self.assertEqual(self.start(role='arena cross-judge pool', index=None), 0)
        [call] = self.starts()
        self.assertEqual(call[call.index('--agent') + 1], 'codex')
        self.assertEqual(json.loads(self.record.read_text())['seats'][0]['index'], 1)
        self.assertEqual(self.start(role='arena cross-judge pool', index='0'), 2)
        self.assertEqual(len(self.starts()), 1)

    def test_bad_arguments_write_nothing(self):
        for extra in (['--timeout-ms', '-5'], ['--instructions', '/nowhere/worker.md']):
            with self.subTest(extra=extra):
                self.assertEqual(self.start(*extra, index='1'), 2)
        self.assertEqual(self.start(index='1', spec=False) , 2)
        self.spec.write_bytes(b'\xff\xfe not text')
        self.assertEqual(self.start(index='1'), 2)
        self.spec.unlink()
        self.assertEqual(self.start(index='1'), 2)
        self.assertEqual(self.starts(), [])
        self.assertFalse(self.record.exists())

    def test_failed_preflight_starts_nothing_and_records_nothing(self):
        del os.environ['ORCA_TERMINAL_HANDLE']
        self.assertEqual(self.start(index='1'), 2)
        self.assertEqual(self.starts(), [])
        self.assertFalse(self.record.exists())

    def test_agy_reads_outside_its_rules_are_refused(self):
        self.assertEqual(self.start('--reads', '/elsewhere', index='2'), 2)
        self.assertEqual(self.start('--reads', str(self.workspaces / 'repo/candidate-a'),
                                    index='2'), 0)

    def test_arena_names_that_reveal_the_seat_are_refused(self):
        for name in ('hstack-codex', 'try-gemini', 'Opus-run'):
            with self.subTest(name=name):
                self.assertEqual(self.start('--name', name, index='1'), 2)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(seats.main(['start', '--role', 'arena runners', '--index', '1',
                                         '--spec-file', str(self.spec), '--record',
                                         str(self.record), '--worktree', 'path:/tmp/codex-try']), 2)
        self.assertEqual(self.starts(), [])
        self.assertEqual(self.start('--name', 'candidate-b', index='1'), 0)
        # Folders above the worktree belong to the project and may say anything.
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(seats.main(['start', '--role', 'arena runners', '--index', '1',
                                         '--spec-file', str(self.spec), '--record',
                                         str(self.record), '--worktree',
                                         'path:/work/neon-db/candidate-a']), 0)
        self.assertEqual(len(self.starts()), 2)
        # interrogate's adversaries are named the same way.
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(seats.main(['start', '--role', 'interrogate reviewers', '--index', '1',
                                         '--spec-file', str(self.spec), '--record',
                                         str(self.record), '--worktree',
                                         'path:/tmp/login-codex-adversary-b']), 2)
        self.assertEqual(len(self.starts()), 2)

    def test_bad_seats_file_refuses_every_start(self):
        self.write_seats('bug-fix: codex high\n')
        self.assertEqual(self.start(index='1'), 2)
        self.assertEqual(self.starts(), [])

    def test_missing_seat_index_is_refused(self):
        self.assertEqual(self.start(index='3'), 2)

    def test_lost_response_leaves_the_seat_unknown(self):
        os.environ['FAKE_START'] = 'garbled'
        self.assertEqual(self.start(index='1'), 3)
        [entry] = json.loads(self.record.read_text())['seats']
        self.assertEqual(entry['status'], 'unknown')
        self.assertIn('request_id', entry)

    def test_outcome_unknown_is_kept_unknown(self):
        for mode in ('outcome_unknown', 'null', 'error_code', 'timeout'):
            with self.subTest(mode=mode):
                os.environ['FAKE_START'] = mode
                self.record.unlink(missing_ok=True)
                self.assertEqual(self.start(index='1'), 3)
                [entry] = json.loads(self.record.read_text())['seats']
                self.assertEqual(entry['status'], 'unknown')
        self.assertEqual(entry['task_id'], None)

    def test_ready_worker_is_started_even_when_keep_open_fails(self):
        os.environ['FAKE_START'] = 'keep_open_failed'
        self.assertEqual(self.start('--keep-open', index='1'), 0)
        [entry] = json.loads(self.record.read_text())['seats']
        self.assertEqual((entry['status'], entry['dispatch_id']), ('started', 'ctx_1'))
        self.assertEqual(entry['warning'], 'could not keep open')
        self.assertIn('orca terminal keep-open term_1', entry['stderr'])

    def test_outcome_reads_every_value_and_only_the_workers_state(self):
        cases = [
            # An earlier code must not hide a later outcome_unknown.
            ({'ok': False, 'error': {'code': 'runtime_timeout', 'data': {
                'setup': {'status': 'skipped'}, 'recovery': {'disposition': 'outcome_unknown'}}}},
             'unknown'),
            # A nested step that is ready is not the worker.
            ({'ok': False, 'result': {'state': 'failed', 'setup': {'state': 'ready'}}}, 'failed'),
            ({'ok': False, 'error': {'code': 'bad', 'data': {'state': 'ready'}}}, 'failed'),
            # Values that are not strings are skipped, not a crash.
            ({'ok': False, 'result': {'state': {'phase': 'x'}, 'status': ['a']},
              'error': {'code': 'bad'}}, 'failed'),
            ({'ok': False, 'result': {'state': 'ready'}}, 'started'),
        ]
        for receipt, expected in cases:
            with self.subTest(receipt=receipt):
                self.assertEqual(seats.outcome(1, receipt), expected)

    def test_spec_given_to_orca_is_private(self):
        self.assertEqual(self.start(index='1'), 0)
        [call] = self.starts()
        self.assertEqual(Path(call[call.index('--spec-file') + 1]).stat().st_mode & 0o777, 0o600)

    def test_a_record_keeps_its_run(self):
        self.assertEqual(self.start('--run', 'run_a', index='0'), 0)
        # Without --run the next worker joins the record's Run, not the session's.
        self.assertEqual(self.start(index='1'), 0)
        second = self.starts()[1]
        self.assertEqual(second[second.index('--run') + 1], 'run_a')
        self.assertEqual(self.start('--run', 'run_b', index='1'), 2)
        self.assertEqual(len(self.starts()), 2)
        self.record.write_text('[]')
        self.assertEqual(self.start(index='1'), 2)
        self.assertEqual(len(self.starts()), 2)

    def test_given_run_survives_a_lost_response(self):
        os.environ['FAKE_START'] = 'garbled'
        self.assertEqual(self.start('--run', 'run_known', index='1'), 3)
        record = json.loads(self.record.read_text())
        self.assertEqual((record['run_id'], record['seats'][0]['run_id']), ('run_known', 'run_known'))

    def test_failed_start_is_recorded_with_its_stage(self):
        os.environ['FAKE_START'] = 'failed'
        self.assertEqual(self.start(index='1'), 1)
        [entry] = json.loads(self.record.read_text())['seats']
        self.assertEqual((entry['status'], entry['stage']), ('failed', 'agent_readiness'))

    def test_seats_share_one_record(self):
        self.assertEqual(self.start(index='0'), 0)
        self.assertEqual(self.start(index='1'), 0)
        record = json.loads(self.record.read_text())
        self.assertEqual([e['seat']['cli'] for e in record['seats']], ['claude', 'codex'])
        self.assertEqual(len({e['request_id'] for e in record['seats']}), 2)


class CommandLineTests(unittest.TestCase):
    def test_runs_as_a_script(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('start', result.stdout)


if __name__ == '__main__':
    unittest.main()
