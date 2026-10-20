#!/usr/bin/env python3
"""Check review bookkeeping against Git and quoted source, without executing code.

Complete means recorded scope/checks are accounted for, not that the model's
reasoning is correct or every defect was found. Semantic quality needs behavioral
evaluation and human inspection. This tool never writes to GitHub.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


class ResultError(ValueError):
    pass


QUALITY = ('cohesion', 'coupling', 'duplication', 'repository_fit', 'naming')
CLASSIFICATIONS = {'source', 'test', 'config', 'migration', 'generated', 'lock', 'fixture', 'docs', 'other'}


def git(root, *args):
    result = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
        '-c', 'core.quotePath=false', '-C', str(root), *args], capture_output=True, timeout=60)
    if result.returncode:
        raise ResultError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


def digest(value):
    return hashlib.sha256(value).hexdigest()


def path_ok(value):
    return (isinstance(value, str) and bool(value) and not PurePosixPath(value).is_absolute()
            and '..' not in PurePosixPath(value).parts and '\x00' not in value)


def sha(root, value):
    return git(root, 'rev-parse', '--verify', '--end-of-options', value + '^{commit}').decode().strip()


def inventory(raw):
    parts = raw.decode('utf-8').split('\x00')
    rows, i = [], 0
    while i < len(parts) and parts[i]:
        status, path = parts[i:i+2]
        i += 2
        row = {'path': path, 'change': status[0]}
        if status[0] in ('R', 'C'):
            row.update(old_path=path, path=parts[i])
            i += 1
        if not path_ok(row['path']):
            raise ResultError('Unsupported repository-relative filename')
        rows.append(row)
    return rows


def local_bytes(root, path):
    file = root / path
    if file.is_symlink():
        return os.readlink(file).encode()
    if not file.exists():
        return None
    if not file.is_file():
        raise ResultError(f'Cannot fingerprint changed directory/submodule: {path}')
    if root not in file.resolve().parents:
        raise ResultError('Source path escapes the checkout')
    return file.read_bytes()


def capture_scope(worktree, base=None, head=None, working_tree=False):
    root = Path(git(worktree, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    current = sha(root, 'HEAD')
    options = ['--no-ext-diff', '--no-textconv', '--ignore-submodules=none', '--no-color', '--unified=3']
    if working_tree:
        if base is not None or head is not None:
            raise ResultError('Working-tree capture uses HEAD; do not supply base/head')
        if git(root, 'ls-files', '--unmerged', '-z'):
            raise ResultError('Resolve the unmerged index before capturing a review target')
        staged = git(root, 'diff', '--cached', *options, 'HEAD', '--')
        unstaged = git(root, 'diff', *options, '--')
        rows = {}
        for args in (['--cached', 'HEAD'], []):
            for row in inventory(git(root, 'diff', '--no-ext-diff', '--no-textconv', '--ignore-submodules=none', '--name-status', '-z', '--find-renames', *args, '--')):
                rows.setdefault(row['path'], row)
        for path in git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode().split('\x00'):
            if path:
                rows[path] = {'path': path, 'change': '?'}
        files = sorted(rows.values(), key=lambda row: row['path'])
        blobs = {row['path']: local_bytes(root, row['path']) for row in files}
        fingerprints = {}
        for path, raw in blobs.items():
            if raw is None:
                fingerprints[path] = None
            else:
                mode = (root / path).lstat().st_mode
                fingerprints[path] = {'sha256': digest(raw), 'type': stat.S_IFMT(mode),
                                      'executable': bool(mode & stat.S_IXUSR)}
        content = json.dumps(fingerprints, sort_keys=True).encode()
        index = git(root, 'ls-files', '--stage', '-z')
        diff_hash = digest(staged + b'\x00' + unstaged + b'\x00' + index + b'\x00' + content)
        target = {'mode': 'working-tree', 'base_sha': current, 'head_sha': current, 'diff_sha256': diff_hash}
    else:
        if base is None:
            raise ResultError('Committed reviews require an explicit base')
        base_sha, head_sha = sha(root, base), sha(root, head or 'HEAD')
        if current != head_sha or git(root, 'status', '--ignore-submodules=none', '--porcelain=v1', '--untracked-files=all').strip():
            raise ResultError('Committed review requires a clean checkout at the reviewed head')
        span = base_sha + '...' + head_sha
        diff_hash = digest(git(root, 'diff', *options, span, '--'))
        files = inventory(git(root, 'diff', '--no-ext-diff', '--no-textconv', '--ignore-submodules=none', '--name-status', '-z', '--find-renames', span, '--'))
        target = {'mode': 'commits', 'base_sha': base_sha, 'head_sha': head_sha, 'diff_sha256': diff_hash}
    return {'schema_version': 1, 'worktree': str(root), 'target': target, 'files': files}


def source_lines(scope, reference):
    path, revision = reference.get('path'), reference.get('revision')
    if not path_ok(path) or revision not in ('base', 'head', 'index', 'working'):
        raise ResultError('Evidence requires a relative path and base/head/index/working revision')
    root, target = Path(scope['worktree']), scope['target']
    if revision in ('working', 'index') and target['mode'] != 'working-tree':
        raise ResultError('Committed review evidence must use base or head')
    if revision == 'working':
        raw = local_bytes(root, path)
        if raw is None:
            raise ResultError('Evidence source was deleted')
    elif revision == 'index':
        raw = git(root, 'show', ':' + path)
    else:
        raw = git(root, 'show', target[revision + '_sha'] + ':' + path)
    return raw.decode('utf-8').splitlines()


def check_evidence(scope, refs):
    if not isinstance(refs, list) or not refs:
        raise ResultError('At least one source quotation is required')
    for ref in refs:
        if not isinstance(ref, dict):
            raise ResultError('Malformed evidence reference')
        line, quote = ref.get('line'), ref.get('quote')
        if type(line) is not int or line < 1 or not isinstance(quote, str) or not quote.strip():
            raise ResultError('Evidence requires a positive line and nonempty exact line quote')
        lines = source_lines(scope, ref)
        if line > len(lines) or lines[line-1].strip() != quote.strip():
            raise ResultError(f'Evidence quote differs at {ref.get("path")}:{line}')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def assess(scope, report):
    """Return independent scope completion and eligible supported finding IDs."""
    result = {'status': 'invalid', 'target': scope['target'], 'gaps': [], 'eligible_findings': [], 'rejected_findings': []}
    gaps = result['gaps']
    if not isinstance(report, dict) or report.get('schema_version') != 1:
        gaps.append({'code': 'schema', 'detail': 'Expected review-result schema_version 1'})
        return result
    if report.get('target') != scope['target']:
        gaps.append({'code': 'stale_target', 'detail': 'Result does not describe the current SHA/diff/mode'})
        return result
    if 'status' in report or 'complete' in report:
        gaps.append({'code': 'self_assessed_status', 'detail': 'Completion is computed by the checker, not supplied by the model'})
        return result
    for name in ('files', 'findings', 'verification', 'limitations'):
        if not isinstance(report.get(name), list):
            gaps.append({'code': 'schema', 'detail': f'{name} must be an array'})
            return result
    expected = {row['path'] for row in scope['files']}
    covered, reviewed = set(), set()
    for row in report['files']:
        if not isinstance(row, dict) or row.get('path') not in expected or row['path'] in covered:
            gaps.append({'code': 'invalid_file', 'detail': 'Unknown or duplicate coverage file'})
            if isinstance(row, dict):
                reviewed.discard(row.get('path'))
            continue
        path = row['path'];covered.add(path)
        if (row.get('classification') not in CLASSIFICATIONS or row.get('risk') not in ('low', 'medium', 'high')
                or row.get('status') not in ('reviewed', 'unreviewed', 'unresolved') or not text(row.get('note'))):
            gaps.append({'code': 'file_record', 'detail': path})
        elif row['status'] != 'reviewed':
            gaps.append({'code': 'unreviewed_file', 'detail': path + ': ' + row['note']})
        else:
            reviewed.add(path)
        if row.get('risk') == 'high' and not text(row.get('trace')):
            gaps.append({'code': 'missing_trace', 'detail': path})
            reviewed.discard(path)
    for path in sorted(expected - covered):
        gaps.append({'code': 'missing_file', 'detail': path})
    for section, names in (('passes', ('standards', 'spec', 'runtime')), ('quality', QUALITY)):
        entries = report.get(section)
        if not isinstance(entries, dict):
            entries = {}
        for name in names:
            entry = entries.get(name, {})
            allowed = ('complete', 'unavailable') if name == 'spec' else (('checked', 'not_applicable') if section == 'quality' else ('complete',))
            if not isinstance(entry, dict) or entry.get('status') not in allowed or not text(entry.get('note')):
                gaps.append({'code': 'incomplete_check', 'detail': section + '.' + name})
            elif entry['status'] == 'unavailable':
                result['spec_conformance'] = 'unverified'
    if not report['verification']:
        gaps.append({'code': 'verification_missing', 'detail': 'Record static/command verification or an explicit not-run reason'})
    for check in report['verification']:
        if (not isinstance(check, dict) or check.get('kind') not in ('static', 'command')
                or check.get('status') not in ('passed', 'failed', 'not_run') or not text(check.get('detail'))):
            gaps.append({'code': 'verification_record', 'detail': 'Incomplete verification entry'})
        elif check['status'] != 'passed':
            if not text(check.get('reason')) or not text(check.get('risk')):
                gaps.append({'code': 'verification_gap', 'detail': 'Failed/not-run checks need reason and residual risk'})
    if any(not text(item) for item in report['limitations']):
        gaps.append({'code': 'limitations', 'detail': 'Limitations must be nonempty text entries'})
    seen = set()
    for finding in report['findings']:
        if not isinstance(finding, dict) or not isinstance(finding.get('id'), str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', finding['id']):
            gaps.append({'code': 'finding_identity', 'detail': 'Each finding/candidate needs a stable ID'})
            continue
        key = finding['id']
        if key in seen:
            result['eligible_findings'] = [item for item in result['eligible_findings'] if item != key]
            result['rejected_findings'].append({'id': key, 'reason': 'Duplicate finding ID'})
            gaps.append({'code': 'duplicate_finding', 'detail': key})
            continue
        seen.add(key)
        disposition = finding.get('status')
        if disposition in ('disproved', 'unresolved', 'duplicate', 'out_of_scope', 'not_worth_changing'):
            if not text(finding.get('reason')):
                gaps.append({'code': 'candidate_reason', 'detail': key})
            if disposition == 'unresolved':
                gaps.append({'code': 'unresolved_candidate', 'detail': key})
            continue
        try:
            if disposition != 'supported' or finding.get('severity') not in ('P1', 'P2', 'P3'):
                raise ResultError('Only supported P1-P3 findings can be promoted')
            if finding.get('path') not in reviewed:
                raise ResultError('Finding belongs to an unreviewed or unaccounted file')
            if any(not text(finding.get(k)) for k in ('trigger', 'effect', 'fix', 'refutation', 'comment')):
                raise ResultError('Supported finding needs trigger/effect/fix/refutation/comment')
            check_evidence(scope, finding.get('evidence'))
            line = finding.get('line')
            if type(line) is not int or line < 1:
                raise ResultError('Finding anchor needs a positive line')
            revision = finding.get('revision', 'head' if scope['target']['mode'] == 'commits' else 'working')
            lines = source_lines(scope, {'path': finding['path'], 'revision': revision})
            if line > len(lines):
                raise ResultError('Finding line is outside the source')
            if not any(ref['path'] == finding['path'] and ref['revision'] == revision and ref['line'] == line for ref in finding['evidence']):
                raise ResultError('Finding anchor must have a matching source quotation')
        except (ResultError, UnicodeError, OSError) as error:
            result['rejected_findings'].append({'id': key, 'reason': str(error)})
            gaps.append({'code': 'finding_evidence', 'detail': key})
        else:
            result['eligible_findings'].append(key)
    result['status'] = 'partial' if gaps else 'complete'
    result['limitations'] = report['limitations']
    result['scope_note'] = 'Recorded scope and source quotations checked; reasoning and defect absence are not certified.'
    return result


def outside(path, root):
    resolved = Path(path).resolve()
    if resolved == root or root in resolved.parents:
        raise ResultError('Review artifacts must be outside the reviewed checkout')
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('capture', 'validate'))
    parser.add_argument('--worktree', required=True)
    parser.add_argument('--base')
    parser.add_argument('--head')
    parser.add_argument('--working-tree', action='store_true')
    parser.add_argument('--result')
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.action == 'validate' and not args.result:
        parser.error('validate requires --result')
    try:
        scope = capture_scope(args.worktree, args.base, args.head, args.working_tree)
        if args.action == 'capture':
            result = scope
        else:
            path = outside(args.result, Path(scope['worktree']))
            result = assess(scope, json.loads(path.read_text()))
            if capture_scope(args.worktree, args.base, args.head, args.working_tree) != scope:
                raise ResultError('Review source changed during validation')
        output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            path = outside(args.output, Path(scope['worktree']))
            with path.open('x') as stream:
                stream.write(output)
        print(output, end='')
        return 0 if result.get('status') in (None, 'complete') else 2
    except (ResultError, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
