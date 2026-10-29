#!/usr/bin/env python3
"""Capture implementation inputs/source and assess recorded verification.

No target code, hooks, test commands or URLs are executed. This checks records and
bytes, not the truth of a model's reasoning or its claimed tool execution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys


class StateError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip())


def relative(value, *, dot=False):
    if not text(value) or '\\' in value or '\x00' in value:
        raise StateError('Expected a repository-relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or (str(path) == '.' and not dot):
        raise StateError('Path escapes its declared root')
    return str(path)


def inside_file(root, value):
    """Do not follow symlinks in untrusted source/evidence references."""
    path = root
    for part in PurePosixPath(relative(value)).parts:
        path = path / part
        if path.is_symlink():
            raise StateError('Referenced file traverses a symlink')
    if not path.is_file():
        raise StateError('Referenced file is missing or not regular')
    return path


def file_bytes(path):
    if path.is_symlink() or not path.is_file():
        raise StateError('Expected a regular file, not a symlink')
    no_follow = getattr(os, 'O_NOFOLLOW', None)
    if no_follow is None:
        raise StateError('Mechanical capture requires O_NOFOLLOW support (macOS/Linux); do not claim a computed pass')
    with os.fdopen(os.open(path, os.O_RDONLY | no_follow), 'rb') as stream:
        return stream.read()


def load(path):
    value = json.loads(file_bytes(path))
    if not isinstance(value, dict):
        raise StateError('Expected a JSON object')
    return value


def git(root, *args):
    result = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
                             '-C', str(root), *args], text=True, capture_output=True, timeout=60,
                            env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})
    if result.returncode:
        raise StateError('Git inspection failed: ' + result.stderr.strip())
    return result.stdout


def repo_root(path):
    return Path(git(Path(path).resolve(), 'rev-parse', '--show-toplevel').strip()).resolve()


def rows_by_id(rows, label):
    if not isinstance(rows, list):
        raise StateError(label + ' must be an array')
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not text(row.get('id')) or row['id'] in result:
            raise StateError(label + ' has missing or duplicate IDs')
        result[row['id']] = row
    return result


def validate_inputs(data):
    if not isinstance(data, dict):
        raise StateError('Inputs must be a JSON object')
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1 or not text(data.get('task')) or data.get('surface') not in ('ui', 'code'):
        raise StateError('Inputs need schema_version 1, task and surface ui/code')
    scope = data.get('scope')
    if not isinstance(scope, list) or not scope:
        raise StateError('Declare the authorized change scope')
    for path in scope:
        relative(path, dot=True)
    sources = rows_by_id(data.get('sources'), 'sources')
    checks = rows_by_id(data.get('checks'), 'checks')
    requirements = rows_by_id(data.get('requirements'), 'requirements')
    if not sources or not requirements or not checks:
        raise StateError('Sources, requirements and checks cannot be empty')
    for source in sources.values():
        if not text(source.get('path')):
            raise StateError('Source needs its actual local path')
    for check in checks.values():
        if check.get('kind') not in ('command', 'browser', 'static') or type(check.get('required')) is not bool:
            raise StateError('Check needs kind and explicit required boolean')
        if not text(check.get('description')):
            raise StateError('Check needs its observable purpose')
    for requirement in requirements.values():
        if requirement.get('source') not in sources or not text(requirement.get('description')):
            raise StateError('Requirement needs its source and actual outcome')
        if requirement.get('disposition') not in ('required', 'excluded'):
            raise StateError('Requirement disposition must be required/excluded')
        linked = requirement.get('checks')
        if not isinstance(linked, list) or any(c not in checks for c in linked) or len(set(linked)) != len(linked):
            raise StateError('Requirement references unknown or duplicate checks')
        if requirement['disposition'] == 'required' and not linked:
            raise StateError('Every in-scope requirement needs a meaningful check')
        if requirement['disposition'] == 'excluded' and not text(requirement.get('reason')):
            raise StateError('Excluded requirement needs its scope authority')
    if not any(r['disposition'] == 'required' for r in requirements.values()):
        raise StateError('No implementation scope declared')
    if data['surface'] == 'ui' and not any(c['kind'] == 'browser' and c['required'] for c in checks.values()):
        raise StateError('UI work needs a required actual-app browser check')
    for field in ('editable_dirty', 'preserve'):
        if not isinstance(data.get(field, []), list):
            raise StateError(field + ' must be an array')
        for path in data.get(field, []):
            relative(path, dot=field == 'preserve')
    roots = data.get('source_roots', [])
    if not isinstance(roots, list) or any(not text(p) or not Path(p).is_absolute() for p in roots):
        raise StateError('Additional source_roots must be explicit absolute directories')
    return {**data, 'scope': [relative(p, dot=True) for p in scope],
            'preserve': [relative(p, dot=True) for p in data.get('preserve', [])],
            'editable_dirty': [relative(p) for p in data.get('editable_dirty', [])]}


def in_scope(path, prefixes):
    return any(prefix == '.' or path == prefix or path.startswith(prefix.rstrip('/') + '/') for prefix in prefixes)


def source_state(root):
    for row in git(root, 'ls-files', '-v', '-z').split('\0'):
        if row and (row[0].islower() or row[0] == 'S'):
            raise StateError('assume-unchanged/skip-worktree index flags are outside v1 capture support')
    index = {}
    for item in git(root, 'ls-files', '--stage', '-z').split('\0'):
        if not item:
            continue
        metadata, path = item.split('\t', 1)
        mode, oid, stage = metadata.split()
        if stage != '0' or mode == '160000':
            raise StateError('Resolve index conflicts; submodule inspection is outside v1')
        index[path] = {'mode': mode, 'oid': oid}
    head_files = {row.split('\t', 1)[1] for row in git(root, 'ls-tree', '-r', '-z', 'HEAD').split('\0') if row}
    others = {p for p in git(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0') if p}
    result = {}
    for name in sorted(set(index) | head_files | others):
        relative(name)
        path = root / name
        # A tracked directory replaced by a symlink must not redirect child reads.
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise StateError('Source inventory traverses a symlink')
        if path.is_symlink():
            working = {'kind': 'symlink', 'sha256': hashlib.sha256(os.readlink(path).encode()).hexdigest()}
        elif not path.exists():
            working = {'kind': 'missing'}
        elif path.is_file():
            working = {'kind': 'file', 'sha256': hashlib.sha256(file_bytes(path)).hexdigest(),
                       'executable': bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))}
        else:
            raise StateError('Unsupported source file type')
        result[name] = {'index': index.get(name), 'working': working}
    return result


def dirty_paths(root, files):
    # git status can execute repository clean/process filters. Compare raw bytes
    # and Git object identities ourselves instead. Normalized/filtered working
    # files may conservatively count as dirty; never run filters to clear them.
    head = {}
    for row in git(root, 'ls-tree', '-r', '-z', 'HEAD').split('\0'):
        if row:
            metadata, name = row.split('\t', 1)
            mode, _, oid = metadata.split()
            head[name] = {'mode': mode, 'oid': oid}
    algorithm = git(root, 'rev-parse', '--show-object-format').strip()
    if algorithm not in ('sha1', 'sha256'):
        raise StateError('Unsupported Git object format')
    dirty = []
    for name, entry in files.items():
        index, working = entry['index'], entry['working']
        changed = index != head.get(name)
        if index is None:
            changed = changed or working['kind'] != 'missing'
        elif working['kind'] == 'missing':
            changed = True
        else:
            path = root / name
            raw = os.fsencode(os.readlink(path)) if working['kind'] == 'symlink' else file_bytes(path)
            oid = hashlib.new(algorithm, b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            mode = '120000' if working['kind'] == 'symlink' else ('100755' if working['executable'] else '100644')
            changed = changed or oid != index['oid'] or mode != index['mode']
        if changed:
            dirty.append(name)
    return sorted(dirty)


def capture(worktree, inputs):
    root = repo_root(worktree)
    # Reject before inspecting objects, including on older Git versions that do
    # not honor GIT_NO_LAZY_FETCH. Reading config itself does not fetch objects.
    for setting in git(root, 'config', '--null', '--list').split('\0'):
        key, _, value = setting.partition('\n')
        key = key.lower()
        if key == 'extensions.partialclone' or (key.startswith('remote.') and key.endswith('.promisor')
                and value.lower() not in ('false', 'no', 'off', '0')):
            raise StateError('Partial/promisor clones are outside v1 capture support; no automatic fetch allowed')
    inputs = Path(inputs).absolute()
    raw = file_bytes(inputs)
    data = validate_inputs(json.loads(raw))
    sources = {}
    for row in data['sources']:
        path = Path(row['path'])
        if not path.is_absolute():
            path = inside_file(root, row['path'])
        else:
            # Resolve the caller-selected root, then reject symlinks beneath it.
            # This permits OS aliases such as /tmp without trusting a symlink
            # inside an input/reference bundle to escape that bundle.
            roots = [root, inputs.parent, *map(Path, data.get('source_roots', []))]
            candidates = [r for r in roots if path.is_relative_to(r)]
            if not candidates:
                raise StateError('External source is outside the declared source_roots')
            selected = max(candidates, key=lambda r: len(r.parts))
            path = inside_file(selected.resolve(), str(path.relative_to(selected)))
        contents = file_bytes(path)
        sources[row['id']] = {'path': str(path.resolve()), 'sha256': hashlib.sha256(contents).hexdigest()}
    before = git(root, 'rev-parse', 'HEAD').strip()
    state = source_state(root)
    dirty = dirty_paths(root, state)
    if before != git(root, 'rev-parse', 'HEAD').strip() or state != source_state(root):
        raise StateError('Source changed during capture; capture a fresh snapshot')
    value = {'schema_version': 1, 'root': str(root), 'head': before,
             'inputs': {'path': str(inputs), 'sha256': hashlib.sha256(raw).hexdigest(), 'data': data},
             'sources': sources, 'files': state, 'dirty': dirty}
    return {**value, 'digest': digest(value)}


def snapshot(path):
    value = load(path)
    if value.get('schema_version') != 1 or value.get('digest') != digest({k: v for k, v in value.items() if k != 'digest'}):
        raise StateError('Snapshot structure or digest is invalid')
    for key in ('root', 'head', 'inputs', 'sources', 'files', 'dirty'):
        if key not in value:
            raise StateError('Incomplete snapshot')
    if (not text(value['root']) or not text(value['head']) or not isinstance(value['inputs'], dict)
            or not text(value['inputs'].get('path')) or not isinstance(value['sources'], dict)
            or not isinstance(value['files'], dict) or not isinstance(value['dirty'], list)):
        raise StateError('Invalid snapshot field types')
    for name, row in value['files'].items():
        relative(name)
        if (not isinstance(row, dict) or not isinstance(row.get('working'), dict)
                or row['working'].get('kind') not in ('file', 'missing', 'symlink')
                or (row.get('index') is not None and not isinstance(row['index'], dict))):
            raise StateError('Invalid snapshot file inventory')
    for name in value['dirty']:
        relative(name)
    validate_inputs(value['inputs']['data'])
    return value


def evidence_files(state_root, rows):
    if not isinstance(rows, list) or not rows:
        raise StateError('Passed checks need recorded evidence files')
    for row in rows:
        if not isinstance(row, dict):
            raise StateError('Invalid evidence entry')
        path = inside_file(state_root, row.get('path'))
        raw = file_bytes(path)
        if not raw or row.get('sha256') != hashlib.sha256(raw).hexdigest():
            raise StateError('Evidence is empty, changed or has an invalid hash')


def assess(worktree, baseline_path, verification_path, result_path):
    verdict = {'status': 'invalid', 'gaps': []}
    try:
        baseline, verified = snapshot(baseline_path), snapshot(verification_path)
        if baseline['root'] != str(repo_root(worktree)) or verified['root'] != baseline['root']:
            raise StateError('Snapshots belong to another repository')
        if baseline['head'] != verified['head'] or baseline['inputs'] != verified['inputs'] or baseline['sources'] != verified['sources']:
            raise StateError('HEAD or implementation inputs changed; start a fresh run')
        current = capture(worktree, verified['inputs']['path'])
        if current != verified:
            raise StateError('Source or inputs changed since verification capture')
        result = load(result_path)
        if result.get('schema_version') != 1 or 'status' in result or 'complete' in result or result.get('target') != verified['digest']:
            raise StateError('Result must reference the verification target without a self-assessed status')
        data = verified['inputs']['data']
        expected_req = rows_by_id(data['requirements'], 'input requirements')
        expected_checks = rows_by_id(data['checks'], 'input checks')
        requirements = rows_by_id(result.get('requirements'), 'result requirements')
        checks = rows_by_id(result.get('verification'), 'result verification')
        if set(requirements) - set(expected_req) or set(checks) - set(expected_checks):
            raise StateError('Result contains undeclared requirements or checks')
        changes = result.get('changes')
        if not isinstance(changes, list) or any(not isinstance(c, dict) or not text(c.get('reason')) for c in changes):
            raise StateError('Each changed path needs its implementation purpose')
        declared = [relative(c.get('path')) for c in changes]
        actual = {p for p in set(baseline['files']) | set(verified['files']) if baseline['files'].get(p) != verified['files'].get(p)}
        if len(set(declared)) != len(declared) or set(declared) != actual:
            raise StateError('Result changes do not match the actual baseline-to-verification changes')
        if any(not in_scope(p, data['scope']) for p in actual):
            raise StateError('Changes exceed the declared implementation scope')
        protected = set(baseline['dirty']) - set(data.get('editable_dirty', []))
        if actual & protected or any(in_scope(p, data.get('preserve', [])) for p in actual):
            raise StateError('Pre-existing or explicitly preserved work changed')
        gaps = verdict['gaps']
        for key, definition in expected_checks.items():
            check = checks.get(key)
            if check is None:
                if definition['required']:
                    gaps.append({'check': key, 'reason': 'missing_check'})
                continue
            status = check.get('status')
            if status not in ('passed', 'failed', 'not_run', 'not_applicable') or not text(check.get('detail')):
                raise StateError('Check needs a valid status and concrete detail')
            if status == 'passed':
                if check.get('target') != verified['digest']:
                    raise StateError('Check evidence targets stale source')
                evidence_files(Path(baseline_path).resolve().parent, check.get('evidence'))
                if definition['kind'] == 'command':
                    if (not isinstance(check.get('command'), list) or not check['command']
                            or any(not text(a) for a in check['command']) or check.get('exit_code') != 0
                            or type(check.get('exit_code')) is not int or not text(check.get('cwd'))):
                        raise StateError('Passed command needs actual argv, cwd and exit code 0')
                if definition['kind'] == 'browser':
                    viewport = check.get('viewport', {})
                    if (not isinstance(viewport, dict) or any(type(viewport.get(k)) is not int or viewport[k] <= 0 for k in ('width', 'height'))
                            or any(not text(check.get(k)) for k in ('tool', 'url', 'scenario'))):
                        raise StateError('Browser evidence needs actual tool, route, viewport and scenario')
            elif not text(check.get('reason')):
                raise StateError('Failed, skipped or inapplicable checks need a reason')
            if definition['required'] and status != 'passed':
                gaps.append({'check': key, 'reason': status})
        for key, definition in expected_req.items():
            row = requirements.get(key)
            if row is None:
                gaps.append({'requirement': key, 'reason': 'missing_requirement'})
                continue
            status = row.get('state')
            if status not in ('implemented', 'unimplemented', 'needs_decision', 'excluded') or not text(row.get('reason')):
                raise StateError('Requirement needs disposition and concrete reason')
            if definition['disposition'] == 'excluded':
                if status != 'excluded':
                    raise StateError('Result silently changes declared scope')
                continue
            if status == 'excluded':
                raise StateError('Cannot exclude an in-scope requirement after capture')
            if status != 'implemented':
                gaps.append({'requirement': key, 'reason': status})
                continue
            locations = row.get('code')
            if not isinstance(locations, list) or not locations:
                raise StateError('Implemented requirement needs actual source locations')
            for location in locations:
                if not isinstance(location, dict) or type(location.get('line')) is not int or location['line'] <= 0 or not text(location.get('quote')):
                    raise StateError('Code evidence needs path, positive line and exact quote')
                name = relative(location.get('path'))
                if verified['files'].get(name, {}).get('working', {}).get('kind') != 'file':
                    raise StateError('Code evidence must be a regular file in the verification inventory')
                path = inside_file(Path(verified['root']), name)
                lines = file_bytes(path).decode('utf-8').splitlines()
                if location['line'] > len(lines) or lines[location['line'] - 1].strip() != location['quote'].strip():
                    raise StateError('Code evidence does not match current source')
            for check in definition['checks']:
                if checks.get(check, {}).get('status') != 'passed':
                    gaps.append({'requirement': key, 'check': check, 'reason': 'outcome_unverified'})
        verdict['target'] = verified['digest']
        verdict['status'] = 'partial' if gaps else 'complete'
        required = [requirements.get(k, {}) for k, d in expected_req.items() if d['disposition'] == 'required']
        if gaps and not actual and required and all(r.get('state') == 'needs_decision' for r in required):
            verdict['status'] = 'blocked'
        return verdict
    except (StateError, OSError, ValueError, KeyError, TypeError, IndexError, UnicodeError) as error:
        verdict['gaps'].append({'reason': 'invalid_record', 'detail': str(error)})
        return verdict


def write_new(path, value, root):
    path = Path(path).absolute()
    destination = path.parent.resolve() / path.name
    if destination == root or destination.is_relative_to(root):
        raise StateError('Store snapshots, results and evidence outside the implementation checkout')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('capture', 'assess'):
        command = sub.add_parser(name)
        command.add_argument('--worktree', type=Path, required=True)
        command.add_argument('--output', type=Path, required=True)
        if name == 'capture':
            command.add_argument('--inputs', type=Path, required=True)
        else:
            command.add_argument('--target', type=Path, required=True)
            command.add_argument('--verification-target', type=Path, required=True)
            command.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    try:
        root = repo_root(args.worktree)
        if args.action == 'capture':
            value = capture(root, args.inputs)
        else:
            paths = [p.resolve() for p in (args.target, args.verification_target, args.result)]
            if any(p == root or p.is_relative_to(root) for p in paths):
                raise StateError('State files must be outside the implementation checkout')
            value = assess(root, *paths)
        write_new(args.output, value, root)
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0 if value.get('status') in (None, 'complete') else 2
    except (StateError, OSError, ValueError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
