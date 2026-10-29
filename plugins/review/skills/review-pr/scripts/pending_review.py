#!/usr/bin/env python3
"""Capture, inspect and resume an unsubmitted, commit-pinned review.

Writes are limited to creating a review without event and adding a thread to an
existing Pending review. Existing text is never edited, deleted or submitted.
Git checks are change guards, not a sandbox or proof of findings' correctness.
"""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile


class ReviewError(RuntimeError):
    pass


def command(args, *, data=None, ok=(0,)):
    context = ''
    if args[:2] == ['gh', 'api']:
        method = args[args.index('--method') + 1]
        endpoint = next(arg for arg in args if arg == 'graphql' or arg == 'user' or arg.startswith('repos/'))
        context = f' [{method} {endpoint}]'
    try:
        result = subprocess.run(args, input=data, text=True, capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ReviewError(f"Command{context} did not complete; do not replay a possible write: {error}") from error
    if result.returncode not in ok:
        raise ReviewError(f"Command{context} failed ({result.returncode}); inspect state before retrying: {result.stderr.strip()}")
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


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def persist(path, data):
    """Publish a complete journal before any possible remote write."""
    fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(receipt):
    # Advisory lock on a separate inode: replacing the journal cannot release it.
    # macOS/Linux CLI hosts; fail closed on a host without flock.
    try:
        import fcntl
    except ImportError as error:
        raise ReviewError('Resuming requires a host with fcntl.flock (macOS/Linux)') from error
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.with_name(receipt.name + '.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ReviewError('Another process is using this receipt; wait for it to finish') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def clean_head(worktree):
    if git(worktree, 'symbolic-ref', '-q', 'HEAD', ok=(0, 1)).returncode != 1:
        raise ReviewError('Use a detached reviewer checkout')
    if git(worktree, 'status', '--ignore-submodules=none', '--porcelain=v1', '--untracked-files=all').stdout.strip():
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
               '--no-textconv', '--ignore-submodules=none', '--no-color', '--unified=3', f'{base}...{head}', '--').stdout


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
    if not isinstance(body, str) or not isinstance(comments, list):
        raise ReviewError('Draft body must be a string and comments an array')
    keys = set()
    normalized = []
    for comment in comments:
        if (not isinstance(comment, dict) or set(comment) - {'path', 'line', 'side', 'body', 'key'}
                or not {'path', 'line', 'side', 'body'} <= set(comment)):
            raise ReviewError('Comments accept path/line/side/body and an optional stable finding key')
        if 'key' in comment and (not isinstance(comment['key'], str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', comment['key'])):
            raise ReviewError('Finding key must contain 1-100 ASCII letters, digits, _, ., :, or -')
        key = finding_key(comment)
        if key in keys:
            raise ReviewError('Duplicate finding key in draft')
        keys.add(key)
        path = comment['path']
        if not isinstance(path, str) or not path or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
            raise ReviewError('Invalid repository-relative comment path')
        if (type(comment['line']) is not int or comment['line'] < 1 or comment['side'] != 'RIGHT'
                or comment['line'] not in anchors.get(path, set())):
            raise ReviewError('Comment must anchor an added RIGHT-side line of the reviewed diff')
        if not isinstance(comment['body'], str) or not comment['body'].strip():
            raise ReviewError('Comment body must be nonempty')
        normalized.append(comment_draft(comment))
    if len({digest(c) for c in normalized}) != len(normalized):
        raise ReviewError('Duplicate comment in draft')
    # event is intentionally absent; there is no submit option.
    return {'commit_id': target['head_sha'], 'body': body, 'comments': normalized}


def pages(host, endpoint):
    result = []
    for page in range(1, 101):
        rows = api(host, f'{endpoint}?per_page=100&page={page}')
        if not isinstance(rows, list):
            raise ReviewError('Unexpected paginated response')
        result.extend(rows)
        if len(rows) < 100:
            return result
    raise ReviewError('Remote listing incomplete; no writes allowed')


def positive_id(value):
    return type(value) is int and value > 0


def comment_draft(comment):
    return {key: comment.get(key) for key in ('path', 'line', 'side', 'body')}


def finding_key(comment):
    return comment.get('key', 'auto:' + digest(comment_draft(comment)))


def anchor(comment):
    return tuple(comment.get(key) for key in ('path', 'line', 'side'))


def own_pending(host, endpoint, login):
    rows = [row for row in pages(host, endpoint + '/reviews')
            if row.get('state') == 'PENDING' and row.get('user', {}).get('login', '').lower() == login.lower()]
    if len(rows) > 1:
        raise ReviewError('Multiple own Pending reviews; reconcile manually without writing')
    return rows[0]['id'] if rows else None


REVIEW_FIELDS = 'id databaseId state submittedAt body author{login} commit{oid}'
PAGE_FIELDS = 'totalCount pageInfo{hasNextPage endCursor}'
COMMENT_FIELDS = '''id databaseId path line originalLine body author{login}
commit{oid} pullRequestReview{databaseId}'''
THREAD_COMMENT_FIELDS = 'id databaseId pullRequestReview{databaseId}'
REVIEW_COMMENTS = ('query ReviewComments($id:ID!,$after:String){node(id:$id){... on PullRequestReview{'
                   + REVIEW_FIELDS + ' comments(first:100,after:$after){nodes{' + COMMENT_FIELDS + '}'
                   + PAGE_FIELDS + '}}}}')
REVIEW_THREADS = ('query ReviewThreads($id:ID!,$after:String){node(id:$id){... on PullRequestReview{'
                  + REVIEW_FIELDS + ' pullRequest{reviewThreads(first:100,after:$after){nodes{'
                  'id path line originalLine diffSide subjectType isOutdated comments(first:100){nodes{'
                  + THREAD_COMMENT_FIELDS + '}' + PAGE_FIELDS + '}}' + PAGE_FIELDS + '}}}}}')
THREAD_COMMENTS = ('query ThreadComments($id:ID!,$after:String){node(id:$id){... on PullRequestReviewThread{'
                   'id comments(first:100,after:$after){nodes{' + THREAD_COMMENT_FIELDS + '}' + PAGE_FIELDS + '}}}}')


def graphql_nodes(host, query, node_id, path, *, review=None, initial=None):
    """Read a complete connection or block writes; never guess past a partial read."""
    result, identities, cursors = [], set(), set()
    after = total = None
    for _ in range(100):
        if initial is not None:
            connection, initial = initial, None
        else:
            response = api(host, 'graphql', payload={'query': query, 'variables': {'id': node_id, 'after': after}})
            if not isinstance(response, dict) or response.get('errors'):
                raise ReviewError('GraphQL read incomplete; no writes allowed')
            data = response.get('data')
            node = data.get('node') if isinstance(data, dict) else None
            if not isinstance(node, dict) or node.get('id') != node_id:
                raise ReviewError('GraphQL node unavailable or identity changed; no writes allowed')
            if review is not None and (
                    node.get('databaseId') != review['id'] or node.get('state') != 'PENDING'
                    or node.get('submittedAt') is not None or node.get('body') != review['body']
                    or (node.get('author') or {}).get('login', '').lower() != review['user']['login'].lower()
                    or node.get('commit') != {'oid': review['commit_id']}):
                raise ReviewError('Review changed during GraphQL read; no writes allowed')
            connection = node
            for key in path:
                connection = connection.get(key) if isinstance(connection, dict) else None
        if not isinstance(connection, dict) or not isinstance(connection.get('nodes'), list):
            raise ReviewError('GraphQL connection incomplete; no writes allowed')
        count, info = connection.get('totalCount'), connection.get('pageInfo')
        if type(count) is not int or count < 0 or (total is not None and count != total):
            raise ReviewError('GraphQL count unavailable or changed; no writes allowed')
        total = count
        for row in connection['nodes']:
            if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                    or not row['id'] or row['id'] in identities):
                raise ReviewError('GraphQL node missing or duplicated; no writes allowed')
            identities.add(row['id'])
            result.append(row)
        if not isinstance(info, dict) or type(info.get('hasNextPage')) is not bool:
            raise ReviewError('GraphQL pagination incomplete; no writes allowed')
        if not info['hasNextPage']:
            if len(result) != total:
                raise ReviewError('GraphQL listing incomplete; no writes allowed')
            return result
        after = info.get('endCursor')
        if not connection['nodes'] or not isinstance(after, str) or not after or after in cursors:
            raise ReviewError('GraphQL pagination did not advance; no writes allowed')
        cursors.add(after)
    raise ReviewError('GraphQL listing limit reached; no writes allowed')


def read_review(host, endpoint, review_id, login):
    if not positive_id(review_id):
        raise ReviewError('Invalid review ID')
    review = api(host, endpoint + f'/reviews/{review_id}')
    if (review.get('id') != review_id or review.get('state') != 'PENDING'
            or review.get('submitted_at') is not None
            or review.get('user', {}).get('login', '').lower() != login.lower()
            or not re.fullmatch(r'[0-9a-f]{40}', review.get('commit_id', ''))
            or not isinstance(review.get('body'), str)):
        raise ReviewError('Review is not verified own PENDING; do not modify or replace it')
    node_id = review.get('node_id')
    if not isinstance(node_id, str) or not node_id:
        raise ReviewError('Pending review node ID unavailable; no writes allowed')
    # Pending comments cannot be fetched through REST's comment detail endpoint.
    # GraphQL comments supply file lines; their threads supply the diff side.
    rows = graphql_nodes(host, REVIEW_COMMENTS, node_id, ('comments',), review=review)
    threads = graphql_nodes(host, REVIEW_THREADS, node_id, ('pullRequest', 'reviewThreads'), review=review) if rows else []
    locations = {}
    for thread in threads:
        members = graphql_nodes(host, THREAD_COMMENTS, thread['id'], ('comments',), initial=thread.get('comments'))
        for member in members:
            if (member.get('pullRequestReview') or {}).get('databaseId') != review_id:
                continue
            comment_id = member.get('databaseId')
            if not positive_id(comment_id) or comment_id in locations:
                raise ReviewError('Thread comment identity ambiguous; no writes allowed')
            locations[comment_id] = thread
    comments = []
    ids = set()
    for comment in rows:
        comment_id = comment.get('databaseId')
        thread = locations.get(comment_id)
        if (not positive_id(comment_id) or comment_id in ids
                or (comment.get('pullRequestReview') or {}).get('databaseId') != review_id
                or (comment.get('author') or {}).get('login', '').lower() != login.lower()
                or not re.fullmatch(r'[0-9a-f]{40}', (comment.get('commit') or {}).get('oid', ''))
                or not isinstance(comment.get('body'), str)):
            raise ReviewError('Comments have ambiguous ownership or identity; no writes allowed')
        if (thread is None or thread.get('path') != comment.get('path')
                or thread.get('diffSide') not in ('LEFT', 'RIGHT')
                or thread.get('subjectType') not in ('LINE', 'FILE')
                or 'line' not in comment
                or (comment['line'] is not None and not positive_id(comment['line']))):
            raise ReviewError('Comment thread location unavailable; no writes allowed')
        ids.add(comment_id)
        comments.append({'id': comment_id, 'path': comment['path'], 'line': comment['line'],
                         'original_line': comment.get('originalLine'), 'side': thread['diffSide'],
                         'body': comment['body'], 'user': {'login': comment['author']['login']},
                         'commit_id': comment['commit']['oid'], 'pull_request_review_id': review_id})
    if set(locations) != ids:
        raise ReviewError('Review comments changed during thread read; no writes allowed')
    return review, comments


def load_record(receipt, args, login):
    identity = {'hostname': args.hostname.lower(), 'repo': args.repo.lower(), 'pr': args.pr, 'login': login.lower()}
    record = {'schema_version': 2, **identity, 'managed': {}, 'operation': None}
    if not receipt.exists():
        return record
    previous = json.loads(receipt.read_text())
    if previous.get('schema_version') == 2:
        if any(previous.get(key) != value for key, value in identity.items()):
            raise ReviewError('Receipt belongs to another host/repository/PR/account')
        if not isinstance(previous.get('managed'), dict) or not isinstance(previous.get('operation'), (dict, type(None))):
            raise ReviewError('Invalid receipt structure; preserve it for recovery')
        if previous.get('review_id') is not None and not positive_id(previous['review_id']):
            raise ReviewError('Invalid receipt review ID')
        for entry in previous['managed'].values():
            if not isinstance(entry, dict) or not positive_id(entry.get('comment_id')) or not isinstance(entry.get('draft'), dict):
                raise ReviewError('Invalid managed finding in receipt')
        return previous
    # v0.5 receipts lack host/account/content. They can only be migrated after
    # matching the supplied original payload hash and a live own Pending review.
    if (previous.get('schema_version') is not None or previous.get('repo', '').lower() != args.repo.lower()
            or previous.get('pr') != args.pr or previous.get('status') not in ('pending', 'pending_stale', 'create_unconfirmed')
            or not re.fullmatch(r'[0-9a-f]{40}', previous.get('head_sha', ''))
            or not re.fullmatch(r'[0-9a-f]{64}', previous.get('payload_sha256', ''))):
        raise ReviewError('Unrecognized receipt; do not replace or replay it')
    record['legacy'] = previous
    if previous.get('review_id') is not None:
        record['review_id'] = previous['review_id']
    return record


def load_target(args):
    target = json.loads(Path(args.snapshot).read_text())
    if (target.get('schema_version'), target.get('hostname'), target.get('repo'), target.get('pr')) != (1, args.hostname, args.repo, args.pr):
        raise ReviewError('Snapshot does not match the requested host/repository/PR')
    if any(not isinstance(target.get(key), str) or not re.fullmatch(r'[0-9a-f]{40}', target[key]) for key in ('base_sha', 'head_sha')):
        raise ReviewError('Snapshot commit identities must be full SHAs')
    worktree = review_root(target['worktree'])
    outside(args.snapshot, worktree)
    if clean_head(worktree) != target['head_sha']:
        raise ReviewError('Checkout moved since review')
    diff = diff_for(worktree, target['base_sha'], target['head_sha'])
    if hashlib.sha256(diff.encode()).hexdigest() != target['diff_sha256']:
        raise ReviewError('Diff differs from the reviewed snapshot')
    return target, worktree, diff


def guard(args, target, worktree):
    if not same_target(pr_state(args.hostname, args.repo, args.pr), target):
        raise ReviewError('PR head/base changed since review; reassess affected findings before saving')
    if clean_head(worktree) != target['head_sha']:
        raise ReviewError('Checkout changed while preparing the draft')


def stamp(record, review, comments):
    record.update(review_id=review['id'], review_head_sha=review['commit_id'],
                  url=review.get('html_url'), state='PENDING')
    record['observed'] = {'body': review['body'], 'comments': comments}


def matches(comments, draft, head):
    return [c for c in comments if comment_draft(c) == draft and c.get('commit_id') == head]


def recover(record, review, comments):
    """Positive readback can confirm a write. Absence can never justify replay."""
    operation = record.get('operation')
    if not operation:
        return True
    if operation.get('kind') not in ('create', 'append'):
        raise ReviewError('Unknown journal operation; no replay allowed')
    if operation['head_sha'] != review['commit_id']:
        return False
    if operation['kind'] == 'create' and operation['body'] != review['body']:
        return False
    found = {}
    for key, draft in operation['findings'].items():
        candidates = matches(comments, draft, operation['head_sha'])
        if len(candidates) != 1:
            return False
        found[key] = {'draft': draft, 'comment_id': candidates[0]['id']}
    record['managed'].update(found)
    if operation['kind'] == 'create':
        record['review_target'] = operation['target']
        record['initial_body'] = operation['body']
    record['operation'] = None
    return True


def reconcile(record, review, comments, target, value):
    """Produce a local plan; never replace existing content, even our own text."""
    plan = {'add': [], 'unchanged': [], 'preserved': [], 'conflicts': []}
    candidates = {finding_key(c): comment_draft(c) for c in value.get('comments', [])}
    by_id = {c['id']: c for c in comments}
    used = set()
    for key, draft in candidates.items():
        entry = record['managed'].get(key)
        if entry:
            remote = by_id.get(entry['comment_id'])
            used.add(entry['comment_id'])
            if remote is None:
                reason = 'deleted_remote'
            elif comment_draft(remote) != entry['draft']:
                reason = 'edited_remote'
            elif draft != entry['draft']:
                reason = 'proposed_change'
            else:
                plan['unchanged'].append(key)
                continue
            plan['conflicts'].append({'key': key, 'reason': reason, 'proposed': draft,
                                      'remote': remote, 'comment_id': entry['comment_id']})
            continue
        exact = matches(comments, draft, target['head_sha'])
        previous = [entry for entry in record['managed'].values() if anchor(entry['draft']) == anchor(draft)]
        if any(entry['comment_id'] not in by_id for entry in previous):
            plan['conflicts'].append({'key': key, 'reason': 'deleted_remote', 'proposed': draft})
        elif len(exact) == 1:
            record['managed'][key] = {'draft': draft, 'comment_id': exact[0]['id']}
            used.add(exact[0]['id'])
            plan['unchanged'].append(key)
        elif exact or any(anchor(c) == anchor(draft) for c in comments):
            plan['conflicts'].append({'key': key, 'reason': 'occupied_anchor', 'proposed': draft})
        else:
            plan['add'].append({'key': key, 'draft': draft})
    for key, entry in record['managed'].items():
        if key not in candidates and entry['comment_id'] in by_id:
            plan['conflicts'].append({'key': key, 'reason': 'omitted_existing', 'comment_id': entry['comment_id']})
    plan['preserved'] = [c['id'] for c in comments if c['id'] not in used]
    if 'body' in value and value['body'] != review['body']:
        plan['conflicts'].append({'reason': 'summary_preserved', 'proposed': value['body'], 'remote': review['body']})
    previous = record.get('review_target')
    plan['needs_reassessment'] = (review['commit_id'] != target['head_sha'] or
        (previous is not None and any(previous.get(k) != target[k] for k in ('base_sha', 'head_sha', 'diff_sha256'))))
    plan['target'] = {k: target[k] for k in ('base_sha', 'head_sha', 'diff_sha256')}
    return plan


def plan_status(plan):
    if plan['needs_reassessment']:
        return 'pending_stale'
    return 'pending_conflicts' if plan['conflicts'] else 'pending'


def check_review_result(path, target, worktree, value):
    # Resolve only the trusted sibling in this installed plugin, never PR code.
    script = Path(__file__).resolve().parents[2] / 'review-code/scripts/review_result.py'
    spec = importlib.util.spec_from_file_location('review_result_gate', script)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    report = json.loads(path.read_text())
    scope = gate.capture_scope(worktree, target['base_sha'], target['head_sha'])
    verdict = gate.assess(scope, report)
    if verdict['status'] == 'invalid':
        raise ReviewError('Review result is invalid/stale: ' + json.dumps(verdict['gaps']))
    eligible = {f['id']: f for f in report['findings'] if isinstance(f, dict) and f.get('id') in verdict['eligible_findings']}
    for comment in value.get('comments', []):
        finding = eligible.get(finding_key(comment))
        if (finding is None or finding.get('path') != comment['path'] or finding.get('line') != comment['line']
                or finding.get('revision', 'head') != 'head' or finding.get('comment') != comment['body']):
            raise ReviewError('Draft comment must exactly match an eligible finding in the current review result')
    if 'body' in value and value['body'] != report.get('review_body', ''):
        raise ReviewError('Draft summary must match review_body in the review result')
    return {**verdict, 'result_sha256': digest(report)}


def add_thread(host, review, draft):
    if not isinstance(review.get('node_id'), str) or not review['node_id']:
        raise ReviewError('Pending review node ID unavailable; cannot add a draft thread')
    # This operation is specifically for a PENDING review. Never supply
    # pullRequestId (which could start another review), or use a comment endpoint.
    result = api(host, 'graphql', payload={
        'query': 'mutation($input:AddPullRequestReviewThreadInput!){addPullRequestReviewThread(input:$input){thread{id}}}',
        'variables': {'input': {'pullRequestReviewId': review['node_id'], **draft}}})
    if result.get('errors') or not result.get('data', {}).get('addPullRequestReviewThread', {}).get('thread', {}).get('id'):
        raise ReviewError('Thread write unconfirmed; inspect the receipt and remote review, do not replay')


def final_check(args, record, receipt, target, worktree):
    try:
        guard(args, target, worktree)
    except ReviewError:
        record['status'] = 'pending_stale'
        persist(receipt, record)
        raise ReviewError('Target changed during save; draft remains on its original commit; reassess before further action')


def run_session(args):
    target = worktree = value = payload = completion = None
    receipt = Path(args.receipt).resolve()
    if args.action == 'save':
        target, worktree, diff = load_target(args)
        paths = [outside(p, worktree) for p in (args.snapshot, args.payload, args.receipt, args.review_result,
                 str(receipt.with_name(receipt.name + '.lock')))]
        if len(set(paths)) != len(paths):
            raise ReviewError('Snapshot, payload, receipt, review result and lock must be distinct paths')
        value = json.loads(paths[1].read_text())
        payload = review_payload(value, target, changed_lines(diff))
        completion = check_review_result(paths[3], target, worktree, value)
    with locked(receipt):
        login = api(args.hostname, 'user')['login']
        if not isinstance(login, str) or not login:
            raise ReviewError('Authenticated login unavailable')
        record = load_record(receipt, args, login)
        if completion is not None:
            record['review_completion'] = completion
        endpoint = f'repos/{args.repo}/pulls/{args.pr}'
        review_id = record.get('review_id') or own_pending(args.hostname, endpoint, login)
        if review_id is None:
            if record.get('operation') or record.get('legacy'):
                record['status'] = 'write_unconfirmed'
                persist(receipt, record)
                return record
            if args.action == 'inspect':
                return {'status': 'no_pending', 'repo': args.repo, 'pr': args.pr}
            guard(args, target, worktree)
            if not payload['body'].strip() and not payload['comments']:
                return {'status': 'no_findings', 'repo': args.repo, 'pr': args.pr, 'review_completion': completion}
            findings = {finding_key(c): comment_draft(c) for c in value.get('comments', [])}
            record.update(status='create_unconfirmed', operation={'kind': 'create', 'head_sha': target['head_sha'],
                          'target': {k: target[k] for k in ('head_sha', 'base_sha', 'diff_sha256')},
                          'body': payload['body'], 'findings': findings})
            persist(receipt, record)
            result = api(args.hostname, endpoint + '/reviews', payload=payload)
            review_id = result.get('id')
            if not positive_id(review_id):
                raise ReviewError('Created review ID unavailable; inspect remote state without replaying')
            record['review_id'] = review_id
            persist(receipt, record)
        review, comments = read_review(args.hostname, endpoint, review_id, login)
        if record.get('review_head_sha') and record['review_head_sha'] != review['commit_id']:
            raise ReviewError('Review commit differs from saved identity')
        stamp(record, review, comments)
        if record.get('legacy'):
            legacy = record['legacy']
            if (payload is None or digest(payload) != legacy['payload_sha256']
                    or review['commit_id'] != legacy['head_sha']):
                record['status'] = 'legacy_needs_original_payload'
                persist(receipt, record)
                return record
            record['operation'] = {'kind': 'create', 'head_sha': legacy['head_sha'],
                'target': {k: target[k] for k in ('head_sha', 'base_sha', 'diff_sha256')},
                'body': payload['body'], 'findings': {finding_key(c): comment_draft(c) for c in value.get('comments', [])}}
            record['legacy_receipt'] = record.pop('legacy')
        if not recover(record, review, comments):
            record['status'] = 'write_unconfirmed'
            persist(receipt, record)
            return record
        if args.action == 'inspect':
            pr = pr_state(args.hostname, args.repo, args.pr)
            record.update(status='inspected', current_head_sha=pr['head']['sha'], current_base_sha=pr['base']['sha'])
            record['needs_reassessment'] = (review['commit_id'] != pr['head']['sha'] or
                record.get('review_target', {}).get('base_sha') != pr['base']['sha'])
            persist(receipt, record)
            return record
        final_check(args, record, receipt, target, worktree)
        plan = reconcile(record, review, comments, target, value)
        record['plan'] = plan
        record['status'] = plan_status(plan)
        persist(receipt, record)
        if record['status'] != 'pending':
            return record
        # Each addition has its own journal entry and fresh readback. An
        # interrupted batch resumes only after positive reconciliation.
        while record['plan']['add']:
            item = record['plan']['add'][0]
            guard(args, target, worktree)
            latest_review, latest_comments = read_review(args.hostname, endpoint, review_id, login)
            if (latest_review != review or latest_comments != comments):
                record['status'] = 'remote_changed'
                persist(receipt, record)
                return record
            record.update(status='append_unconfirmed', operation={'kind': 'append', 'head_sha': target['head_sha'],
                          'findings': {item['key']: item['draft']}})
            persist(receipt, record)
            add_thread(args.hostname, review, item['draft'])
            review, comments = read_review(args.hostname, endpoint, review_id, login)
            stamp(record, review, comments)
            if not recover(record, review, comments):
                record['status'] = 'write_unconfirmed'
                persist(receipt, record)
                return record
            record['status'] = 'pending'
            persist(receipt, record)
            final_check(args, record, receipt, target, worktree)
            record['plan'] = reconcile(record, review, comments, target, value)
            record['status'] = plan_status(record['plan'])
            if record['status'] != 'pending':
                persist(receipt, record)
                return record
        review, comments = read_review(args.hostname, endpoint, review_id, login)
        stamp(record, review, comments)
        final_check(args, record, receipt, target, worktree)
        record['plan'] = reconcile(record, review, comments, target, value)
        record['status'] = plan_status(record['plan'])
        persist(receipt, record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('capture', 'inspect', 'save'))
    parser.add_argument('--hostname', default='github.com')
    parser.add_argument('--repo', required=True)
    parser.add_argument('--pr', required=True, type=int)
    parser.add_argument('--snapshot')
    parser.add_argument('--worktree')
    parser.add_argument('--payload')
    parser.add_argument('--receipt')
    parser.add_argument('--review-result')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9.-]+', args.hostname) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo) or args.pr < 1:
        parser.error('Use an explicit hostname, owner/repo and positive PR number')
    if args.action == 'capture' and not (args.worktree and args.snapshot):
        parser.error('capture requires --worktree and --snapshot')
    if args.action == 'save' and not (args.snapshot and args.payload and args.receipt and args.review_result):
        parser.error('save requires --snapshot, --payload, --receipt and --review-result')
    if args.action == 'inspect' and not args.receipt:
        parser.error('inspect requires --receipt')
    try:
        result = capture(args) if args.action == 'capture' else run_session(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get('status') not in (None, 'pending', 'inspected', 'no_pending', 'no_findings'):
            return 2
    except (ReviewError, OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
