#!/usr/bin/env python3
"""Capture a clean PR target and save one unsubmitted, commit-pinned review.

The only remote mutation is POST /pulls/N/reviews, without an event. The caller
must have authorization for the supplied comment text. Git checks are change
guards, not an OS sandbox or proof of the findings' correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


class ReviewError(RuntimeError):
    pass


def command(args, *, data=None, ok=(0,)):
    try:
        result = subprocess.run(args, input=data, text=True, capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ReviewError(f"Command did not complete; do not replay a possible write: {error}") from error
    if result.returncode not in ok:
        raise ReviewError(f"Command failed ({result.returncode}); inspect state before retrying: {result.stderr.strip()}")
    return result


def git(worktree, *args, ok=(0,)):
    return command(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(worktree), *args], ok=ok)


def api(host, endpoint, *, payload=None):
    args = ['gh', 'api', '--hostname', host, '-H', 'Accept: application/vnd.github+json',
            '--method', 'GET' if payload is None else 'POST', endpoint]
    if payload is not None:
        args += ['--input', '-']
    raw = command(args, data=None if payload is None else json.dumps(payload)).stdout
    try:
        return json.loads(raw)
    except ValueError as error:
        raise ReviewError('API returned invalid JSON; inspect pending reviews before retrying') from error


def outside(path, worktree):
    path = Path(path).resolve()
    if path == worktree or worktree in path.parents:
        raise ReviewError('Snapshot, payload and receipt must be outside the reviewed checkout')
    return path


def review_root(path):
    # A caller may supply a subdirectory. Output isolation must cover the actual
    # checkout, not just that subdirectory.
    return Path(git(Path(path).resolve(), 'rev-parse', '--show-toplevel').stdout.strip()).resolve()


def write_new(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def clean_head(worktree):
    if git(worktree, 'symbolic-ref', '-q', 'HEAD', ok=(0, 1)).returncode != 1:
        raise ReviewError('Use a detached reviewer checkout')
    if git(worktree, 'status', '--porcelain=v1', '--untracked-files=all').stdout.strip():
        raise ReviewError('Reviewed checkout has local changes; do not save comments')
    return git(worktree, 'rev-parse', 'HEAD').stdout.strip()


def pr_state(host, repo, number):
    result = api(host, f'repos/{repo}/pulls/{number}')
    if result.get('state') != 'open' or result.get('number') != number:
        raise ReviewError('PR is not open or its identity differs')
    if result.get('base', {}).get('repo', {}).get('full_name', '').lower() != repo.lower():
        raise ReviewError('PR repository differs from the requested target')
    if any(not re.fullmatch(r'[0-9a-f]{40}', result.get(side, {}).get('sha', '')) for side in ('base', 'head')):
        raise ReviewError('PR returned an invalid commit identity')
    return result


def same_target(pr, target):
    return pr['head']['sha'] == target['head_sha'] and pr['base']['sha'] == target['base_sha']


def diff_for(worktree, base, head):
    # Never execute configured external diff/textconv drivers from review context.
    return git(worktree, '-c', 'core.quotePath=false', 'diff', '--no-ext-diff',
               '--no-textconv', '--no-color', '--unified=3', f'{base}...{head}', '--').stdout


def changed_lines(diff):
    """Return added head-side lines. Unsupported quoted/control paths fail closed."""
    result, path, line_no = {}, None, None
    for line in diff.splitlines():
        if line.startswith('diff --git '):
            path, line_no = None, None
        elif line.startswith('+++ ') and line_no is None:
            value = line[4:]
            path = value[2:] if value.startswith('b/') and '\t' not in value else None
        elif line.startswith('@@ '):
            match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
            line_no = int(match.group(1)) if match else None
        elif path is not None and line_no is not None:
            if line.startswith('+'):
                result.setdefault(path, set()).add(line_no)
                line_no += 1
            elif line.startswith(' '):
                line_no += 1
    return result


def capture(args):
    worktree = review_root(args.worktree)
    output = outside(args.snapshot, worktree)
    head = clean_head(worktree)
    pr = pr_state(args.hostname, args.repo, args.pr)
    if head != pr['head']['sha']:
        raise ReviewError('Checkout does not match the current PR head')
    diff = diff_for(worktree, pr['base']['sha'], head)
    target = {'schema_version': 1, 'hostname': args.hostname, 'repo': args.repo,
              'pr': args.pr, 'worktree': str(worktree), 'head_sha': head,
              'base_sha': pr['base']['sha'], 'diff_sha256': hashlib.sha256(diff.encode()).hexdigest()}
    if not same_target(pr_state(args.hostname, args.repo, args.pr), target):
        raise ReviewError('PR changed during capture; capture again before reviewing')
    write_new(output, target)
    return target


def review_payload(value, target, anchors):
    if not isinstance(value, dict) or set(value) - {'body', 'comments'}:
        raise ReviewError('Draft accepts only body/comments; event and caller-supplied commit_id are forbidden')
    body, comments = value.get('body', ''), value.get('comments', [])
    if not isinstance(body, str) or not isinstance(comments, list) or (not body.strip() and not comments):
        raise ReviewError('Provide nonempty draft content')
    for comment in comments:
        if not isinstance(comment, dict) or set(comment) != {'path', 'line', 'side', 'body'}:
            raise ReviewError('Only single-line path/line/side/body comments are supported')
        path = comment['path']
        if not isinstance(path, str) or not path or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
            raise ReviewError('Invalid repository-relative comment path')
        if (type(comment['line']) is not int or comment['line'] < 1 or comment['side'] != 'RIGHT'
                or comment['line'] not in anchors.get(path, set())):
            raise ReviewError('Comment must anchor an added RIGHT-side line of the reviewed diff')
        if not isinstance(comment['body'], str) or not comment['body'].strip():
            raise ReviewError('Comment body must be nonempty')
    # event is intentionally absent; there is no submit option.
    return {'commit_id': target['head_sha'], 'body': body, 'comments': comments}


def own_pending(host, repo, number, login):
    for page in range(1, 101):
        rows = api(host, f'repos/{repo}/pulls/{number}/reviews?per_page=100&page={page}')
        if not isinstance(rows, list):
            raise ReviewError('Unexpected reviews response')
        for row in rows:
            if row.get('state') == 'PENDING' and row.get('user', {}).get('login', '').lower() == login.lower():
                return row['id']
        if len(rows) < 100:
            return None
    raise ReviewError('Review listing incomplete; no draft created')


def save(args):
    target = json.loads(Path(args.snapshot).read_text())
    if (target.get('schema_version'), target.get('hostname'), target.get('repo'), target.get('pr')) != (1, args.hostname, args.repo, args.pr):
        raise ReviewError('Snapshot does not match the requested host/repository/PR')
    if any(not isinstance(target.get(key), str) or not re.fullmatch(r'[0-9a-f]{40}', target[key]) for key in ('base_sha', 'head_sha')):
        raise ReviewError('Snapshot commit identities must be full SHAs')
    worktree = review_root(target['worktree'])
    outside(args.snapshot, worktree)
    payload_file = outside(args.payload, worktree)
    receipt = outside(args.receipt, worktree)
    if receipt.exists():
        raise ReviewError('Receipt already exists; inspect it and remote pending state instead of retrying')
    if clean_head(worktree) != target['head_sha']:
        raise ReviewError('Checkout moved since review')
    diff = diff_for(worktree, target['base_sha'], target['head_sha'])
    if hashlib.sha256(diff.encode()).hexdigest() != target['diff_sha256']:
        raise ReviewError('Diff differs from the reviewed snapshot')
    payload = review_payload(json.loads(payload_file.read_text()), target, changed_lines(diff))
    login = api(args.hostname, 'user')['login']
    existing = own_pending(args.hostname, args.repo, args.pr, login)
    if existing is not None:
        raise ReviewError(f'Pending review {existing} already exists; leave it untouched and inspect it before proceeding')
    endpoint = f'repos/{args.repo}/pulls/{args.pr}'
    if not same_target(pr_state(args.hostname, args.repo, args.pr), target):
        raise ReviewError('PR head/base changed since review; reassess affected findings before saving')
    if clean_head(worktree) != target['head_sha']:
        raise ReviewError('Checkout changed while preparing the draft')
    record = {'status': 'create_unconfirmed', 'repo': args.repo, 'pr': args.pr,
              'head_sha': target['head_sha'], 'payload_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()}
    # Persist the attempt before the write: a timeout cannot justify blind replay.
    write_new(receipt, record)
    review = api(args.hostname, endpoint + '/reviews', payload=payload)
    record['review_id'] = review.get('id')
    record['url'] = review.get('html_url')
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    if type(review.get('id')) is not int:
        raise ReviewError('Created review ID unavailable; inspect pending state, do not replay')
    review = api(args.hostname, endpoint + f'/reviews/{review["id"]}')
    if (review.get('state') != 'PENDING' or review.get('submitted_at') is not None
            or review.get('commit_id') != target['head_sha']
            or review.get('user', {}).get('login', '').lower() != login.lower()):
        raise ReviewError('Created review is not verified PENDING on the reviewed commit; inspect it without submitting')
    fresh = same_target(pr_state(args.hostname, args.repo, args.pr), target)
    try:
        fresh = clean_head(worktree) == target['head_sha'] and fresh
    except ReviewError:
        fresh = False
    record['status'] = 'pending' if fresh else 'pending_stale'
    record['state'] = 'PENDING'
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    if not fresh:
        raise ReviewError('Review target changed during creation; draft remains PENDING on the reviewed head, reassess before further action')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('capture', 'save'))
    parser.add_argument('--hostname', default='github.com')
    parser.add_argument('--repo', required=True)
    parser.add_argument('--pr', required=True, type=int)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--worktree')
    parser.add_argument('--payload')
    parser.add_argument('--receipt')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9.-]+', args.hostname) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo) or args.pr < 1:
        parser.error('Use an explicit hostname, owner/repo and positive PR number')
    if args.action == 'capture' and not args.worktree:
        parser.error('capture requires --worktree')
    if args.action == 'save' and not (args.payload and args.receipt):
        parser.error('save requires --payload and --receipt')
    try:
        print(json.dumps(capture(args) if args.action == 'capture' else save(args), ensure_ascii=False, indent=2))
    except (ReviewError, OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
