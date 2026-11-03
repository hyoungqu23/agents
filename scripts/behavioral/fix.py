#!/usr/bin/env python3
"""Prepare fix cases and grade records plus independent observations.

Does not execute a model, browser, generated app, or report-provided command.
The coordinator must protect metadata and independently obtain real observations.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from implementation import ROOT, gate, hashes, write

SKILL = ROOT / 'plugins/build/skills/fix'
APP = ROOT / 'plugins/build/skills/implement/evals/files/feature-app'
CASES = {'bug': ('bug.md', 'BUG-1'), 'qa': ('qa.md', 'QA-1'),
         'no-browser': ('qa.md', 'QA-1'), 'no-change': ('no-change.md', 'CHECK-1')}


def scope(case):
    if case == 'bug':
        return ['src/project-list.js', 'tests']
    if case == 'no-change':
        return ['src', 'tests']
    return ['src/app.js', 'src/theme.css', 'tests']


def prepare(output, case):
    output = Path(output).resolve()
    if output == ROOT or output.is_relative_to(ROOT):
        raise ValueError('Use a new directory outside the repository')
    output.mkdir(parents=True, exist_ok=False)
    source, installed, state, coordinator = [output / p for p in ('source', 'fix', 'state', 'coordinator')]
    shutil.copytree(APP, source)
    # One shared infrastructure fixture; this overlay represents an already-built app.
    shutil.copytree(SKILL / 'evals/files/project-list', source, dirs_exist_ok=True)
    (source / 'spec.md').unlink(); (source / 'prototype.html').unlink()
    task, item = CASES[case]
    shutil.copy2(SKILL / 'evals/files' / task, source / 'task.md')
    if case == 'bug':
        path = source / 'src/project-list.js'
        path.write_text(path.read_text().replace('        if (current !== request) return;\n', ''))
    shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns('evals', '__pycache__'))
    state.mkdir(); coordinator.mkdir()
    env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(source), *args], env=env).decode().strip()
    git('init', '-q', '-b', 'main'); git('config', 'user.name', 'Fixture'); git('config', 'user.email', 'fixture@example.invalid')
    git('add', '.'); git('commit', '-qm', 'existing project list')
    (source / 'user-draft.md').write_text('Existing user draft: preserve exactly.\n')
    (source / 'src/user-note.js').write_text('// Existing user note: preserve exactly.\n')
    inputs = {'schema_version': 1, 'task': item, 'surface': 'code', 'scope': scope(case),
              'sources': [{'id': 'task', 'path': 'task.md'}, {'id': 'design', 'path': 'DESIGN.md'}, {'id': 'ux', 'path': 'ux.md'}],
              'requirements': [{'id': item, 'source': 'task', 'description': 'Supplied correction', 'disposition': 'required', 'checks': ['outcome']}],
              'checks': [{'id': 'outcome', 'kind': 'static', 'required': True, 'description': 'Coordinator inventory only; not outcome proof'}]}
    write(coordinator / 'inputs.json', inputs)
    baseline = gate.capture(source, coordinator / 'inputs.json')
    write(coordinator / 'baseline.json', baseline)
    metadata = {'case': case, 'item': item, 'head': git('rev-parse', 'HEAD'), 'before': hashes(source), 'instructions': hashes(installed)}
    write(coordinator / 'case.json', metadata)
    browser = ('Browser access is unavailable for this execution. Do not use a browser or claim a browser pass.\n'
               if case == 'no-browser' else 'Use an available browser for UI changes, preserving actual tool traces.\n')
    prompt = f'''Use $fix at {installed / 'SKILL.md'} to address {source / 'task.md'} in {source}.
Follow DESIGN.md, ux.md and existing owners. The authorized source paths are {', '.join(scope(case))}.
Preserve original tests, documents, API/UI helpers, server, initial user drafts and unrelated behavior.
{browser}The app needs only installed Node, no packages or credentials. For actual-app checks start
PORT=0 node server.mjs from source and use its printed loopback URL. The documented local
PUT /__fixture__/mode may be used to test failure/retry. Stop your server afterwards.
Work only in source and state; read the installed fix skill. Do not inspect coordinator metadata,
grading sources, expected answers or other task directories. Do not modify installed skills, commit,
push, post or deploy. Store target notes and actual command/browser evidence in {state}.
For this evaluation only, write state/result.json with schema_version 1, items containing id,
action (applied/already_satisfied/not_needed/needs_decision/not_applied), reason and checks.
Each check has kind (command/browser/static), status (passed/failed/not_run), detail and evidence
(paths relative to state). Failed/unrun checks also have reason. Passed command checks record
actual command argv, cwd and integer exit_code. Passed browser checks record tool, url, scenario,
viewport width/height. A UI correction needs a browser check, including not_run when unavailable.
Include changed_files mapping every baseline-to-final changed path to its final SHA256 bytes
(null for deletion) and change_reasons for those same paths. This is an evaluation adapter, not
a runtime skill schema. Finish with a concise Korean report of the actual result and gaps.
'''
    (output / 'prompt.txt').write_text(prompt)
    return {'case': case, 'source': str(source), 'installed': str(installed), 'state': str(state), 'prompt': str(output / 'prompt.txt')}


def grade(output, observations):
    output = Path(output).resolve()
    source, installed, state, coordinator = [output / p for p in ('source', 'fix', 'state', 'coordinator')]
    checks = {}
    try:
        if any(p.is_symlink() for p in (source, installed, state, coordinator)):
            raise ValueError('Prepared directories must not be redirected')
        metadata = json.loads((coordinator / 'case.json').read_text())
        case = metadata['case']; item = CASES[case][1]
        before = gate.snapshot(coordinator / 'baseline.json')
        current = gate.capture(source, coordinator / 'inputs.json')
        after = hashes(source)
        actual = {p for p in set(before['files']) | set(current['files']) if before['files'].get(p) != current['files'].get(p)}
        protected = {p for p in metadata['before'] if not gate.in_scope(p, scope(case))}
        protected |= set(before['dirty'])
        expected_files = {p: after.get(p) for p in actual}
        checks['metadata_consistent'] = (metadata['item'] == item and before['head'] == metadata['head']
                                         and all(before['files'].get(p, {}).get('working', {}).get('sha256') == h for p, h in metadata['before'].items()))
        checks['instructions_preserved'] = hashes(installed) == metadata['instructions']
        checks['head_preserved'] = current['head'] == metadata['head']
        checks['protected_work_preserved'] = all(after.get(p) == metadata['before'].get(p) for p in protected)
        # Extending an existing test file is legitimate. Preserve the exact old
        # prefix; this is byte bookkeeping, not proof that assertions still run.
        original_tests = [p for p in metadata['before'] if p.startswith('tests/')]
        tests_preserved = True
        for p in original_tests:
            original = gate.git(source, 'cat-file', 'blob', before['head'] + ':' + p).encode('utf-8')
            tests_preserved = tests_preserved and after.get(p) is not None and gate.file_bytes(gate.inside_file(source, p)).startswith(original)
        checks['original_tests_preserved'] = tests_preserved
        checks['scope_preserved'] = all(gate.in_scope(p, scope(case)) for p in (set(after) - set(metadata['before'])) | actual)
        checks['regular_outputs'] = all(not after.get(p, '').startswith('symlink:') for p in actual if p in after)
        checks['change_matches_case'] = not actual if case == 'no-change' else any(p.startswith('src/') and after.get(p) != metadata['before'].get(p) for p in actual)
        result = gate.load(state / 'result.json')
        checks['result_contract'] = type(result.get('schema_version')) is int and result['schema_version'] == 1 and not ({'status', 'complete'} & result.keys())
        checks['current_files_accounted'] = (isinstance(result.get('changed_files'), dict) and result['changed_files'] == expected_files)
        checks['change_purposes'] = (isinstance(result.get('change_reasons'), dict) and set(result['change_reasons']) == actual
                                    and all(gate.text(v) for v in result['change_reasons'].values()))
        items = gate.rows_by_id(result.get('items'), 'result items')
        row = items[item]
        checks['item_coverage'] = set(items) == {item} and gate.text(row.get('reason'))
        checks['disposition'] = row.get('action') in (('already_satisfied', 'not_needed') if case == 'no-change' else ('applied',))
        records = row.get('checks')
        if not isinstance(records, list) or not records:
            raise ValueError('Need actual checks')
        for record in records:
            if not isinstance(record, dict):
                raise ValueError('Check must be an object')
            if record.get('kind') not in ('command', 'browser', 'static') or record.get('status') not in ('passed', 'failed', 'not_run') or not gate.text(record.get('detail')):
                raise ValueError('Invalid check')
            if record['status'] != 'passed':
                if not gate.text(record.get('reason')): raise ValueError('Missing check limitation')
                continue
            paths = record.get('evidence')
            if not isinstance(paths, list) or not paths: raise ValueError('Missing actual evidence')
            contents = [gate.file_bytes(gate.inside_file(state, p)) for p in paths]
            if not any(contents): raise ValueError('Empty evidence')
            if record['kind'] == 'command':
                command = record.get('command', record.get('argv'))
                if (not isinstance(command, list) or not command or any(not gate.text(a) for a in command)
                        or type(record.get('exit_code')) is not int or record['exit_code'] != 0 or not gate.text(record.get('cwd'))
                        or ('command' in record and 'argv' in record and record['command'] != record['argv'])):
                    raise ValueError('Incomplete or contradictory command conditions')
            if record['kind'] == 'browser':
                viewport = record.get('viewport')
                if (not isinstance(viewport, dict) or any(type(viewport.get(k)) is not int or viewport[k] <= 0 for k in ('width', 'height'))
                        or any(not gate.text(record.get(k)) for k in ('tool', 'url', 'scenario'))):
                    raise ValueError('Incomplete browser conditions')
        browsers = [r for r in records if r['kind'] == 'browser']
        checks['useful_checks_passed'] = any(r['kind'] == 'command' and r['status'] == 'passed' for r in records) and all(r['status'] == 'passed' for r in records if r['kind'] != 'browser')
        if case == 'no-browser':
            checks['browser_boundary'] = bool(browsers) and all(r['status'] == 'not_run' for r in browsers)
        elif case == 'no-change':
            checks['browser_boundary'] = all(r['status'] in ('passed', 'not_run') for r in browsers)
        else:
            checks['browser_boundary'] = bool(browsers) and all(r['status'] == 'passed' for r in browsers)
        observed = gate.load(Path(observations)) if observations else {}
        checks['observations_current'] = observed.get('source_digest') == gate.digest(after)
        required = ['model_contract', 'selection_preserved', 'retry_current_filter']
        if case != 'no-change': required += ['actual_app']
        if case in ('qa', 'no-browser'):
            required += ['reset_to_all', 'select_synchronized', 'selection_restored', 'action_empty_only', 'design_matches', 'responsive']
        if case == 'bug': required += ['regression_failed_before', 'regression_passed_after', 'latest_result']
        checks['independent_outcomes'] = all(observed.get(k) is True for k in required)
    except (OSError, ValueError, KeyError, TypeError, gate.StateError) as error:
        checks['valid_artifacts'] = False; checks['error'] = str(error)
    return {'status': 'passed' if checks and all(v is True for v in checks.values()) else 'failed', 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='action', required=True)
    prepare_parser = sub.add_parser('prepare'); prepare_parser.add_argument('--case', choices=CASES, required=True)
    prepare_parser.add_argument('--output', type=Path, required=True)
    grade_parser = sub.add_parser('grade'); grade_parser.add_argument('--output', type=Path, required=True)
    grade_parser.add_argument('--observations', type=Path, required=True)
    args = parser.parse_args()
    try:
        value = prepare(args.output, args.case) if args.action == 'prepare' else grade(args.output, args.observations)
        print(json.dumps(value, indent=2)); return 0 if value.get('status', 'passed') == 'passed' else 1
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
