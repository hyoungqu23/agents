"""Only Pending creation/addition; never publish, replace or resolve anything."""
from argparse import Namespace
import json
from pathlib import Path
import time
import uuid

from .github import fingerprint, public_comments
from .state import HarnessError, digest, read_json, save_json
from .trusted import module
from .policy import PolicyChanged, require_pending


class DeliveryError(HarnessError):
    def __init__(self, status, message):
        super().__init__(message); self.status = status


def inspect(config, gh, event, state_root):
    """Read-only positive reconciliation. Never replay a missing/ambiguous write."""
    login = gh.login(); helper = module('review-pr', 'pending_review.py')
    helper.api = lambda host, endpoint, payload=None: gh.api(endpoint, payload)
    directory = Path(state_root) / 'receipts' / digest({'host': event['hostname'], 'repo': event['repo'], 'pr': event['pr'], 'login': login.lower()})
    endpoint = f'repos/{event["repo"]}/pulls/{event["pr"]}'
    for path in (directory / 'code.json', directory / 'reply-review.json'):
        archive_submitted(gh, endpoint, path)
    code = directory / 'code.json'
    if code.exists():
        value = helper.run_session(Namespace(action='inspect', hostname=event['hostname'], repo=event['repo'], pr=event['pr'], receipt=str(code)))
        if value['status'] not in ('inspected', 'no_pending'):
            return {'status': 'write_unconfirmed', 'detail': 'Code journal cannot be positively reconciled'}
    creation = directory / 'reply-review.json'
    if (creation.exists() and not read_json(creation).get('review_id')
            and read_json(creation).get('status') != 'policy_blocked'):
        return {'status': 'write_unconfirmed', 'detail': 'Pending creation has no confirmed review identity'}
    snapshot = gh.snapshot(event['repo'], event['pr'])
    for path in directory.glob('reply-*.json'):
        if path.name == 'reply-review.json' or '-submitted-' in path.name:
            continue
        record = read_json(path)
        matches = [c for t in snapshot['threads'] if t['id'] == record['thread_id'] for c in t['comments']
                   if c.get('body') == record['body'] and (c.get('author') or {}).get('login', '').lower() == login.lower()
                   and (c.get('pullRequestReview') or {}).get('databaseId') == record['review_id']]
        if record['status'] == 'policy_blocked':
            if matches:
                return {'status': 'pending_conflict', 'detail': 'Unsent reply matches unmanaged remote content; preserve it'}
            continue
        if len(matches) != 1:
            return {'status': 'pending_conflict' if record['status'] == 'pending' else 'write_unconfirmed',
                    'detail': 'Reply is missing, edited or ambiguous; preserve it and reconcile in GitHub'}
        save_json(path, {**record, 'status': 'pending', 'comment_id': matches[0]['id']})
    return {'status': 'local_ready', 'detail': 'Journals reconciled read-only; explicit retry is now available'}


def archive_submitted(gh, endpoint, path):
    if not path.exists():
        return
    record = read_json(path)
    review_id = record.get('review_id')
    if not review_id:
        return
    review = gh.api(endpoint + f'/reviews/{review_id}')
    if review.get('id') != review_id:
        raise DeliveryError('write_unconfirmed', 'Recorded review identity is unavailable')
    if review['state'] != 'PENDING':
        # Keep the receipt; a submitted round must not block all future rounds.
        path.rename(path.with_name(path.stem + '-submitted-' + uuid.uuid4().hex + '.json'))


def fresh(gh, event, expected):
    latest = gh.snapshot(event['repo'], event['pr'])
    if latest['pr']['state'] != 'open' or fingerprint(latest) != fingerprint(expected):
        raise DeliveryError('superseded', 'Source or review conversation changed; reassess before saving')
    return latest


def save(config, gh, event, snapshot, scope, result, code_assessment, run_dir, state_root):
    require_pending(config, state_root, event)
    helper = module('review-pr', 'pending_review.py')
    login = gh.login()
    identity = {'host': event['hostname'], 'repo': event['repo'], 'pr': event['pr'], 'login': login.lower()}
    directory = Path(state_root) / 'receipts' / digest(identity)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    endpoint = f'repos/{event["repo"]}/pulls/{event["pr"]}'
    code_receipt = directory / 'code.json'
    reply_receipt = directory / 'reply-review.json'
    def guarded_api(host, target, payload=None, journal=None):
        mutation = payload is not None and (target != 'graphql' or payload.get('query', '').lstrip().startswith('mutation'))
        if mutation:
            try:
                require_pending(config, state_root, event)
            except PolicyChanged:
                path = journal or code_receipt
                if path.exists():
                    record = read_json(path)
                    if record.get('operation'):
                        record.setdefault('blocked_operations', []).append(record['operation'])
                        record['operation'] = None
                    else:
                        record.setdefault('blocked_operations', []).append({'endpoint': target, 'payload_sha256': digest(payload)})
                    record['status'] = 'policy_blocked'
                    save_json(path, record)
                raise
        return gh.api(target, payload)
    # GitHub.api retains canonical fullDatabaseId normalization for helper reads.
    helper.api = guarded_api
    fresh(gh, event, snapshot)
    published_keys = set()
    for path in list(directory.glob('code*.json')) + list(directory.glob('round-*.json')):
        record = read_json(path)
        if record.get('review_id'):
            remote = gh.api(endpoint + f'/reviews/{record["review_id"]}')
            if remote.get('state') in ('APPROVED', 'COMMENTED', 'CHANGES_REQUESTED', 'DISMISSED'):
                published_keys.update(record.get('managed', {}))
                published_keys.update(record.get('finding_ids', []))
    archive_submitted(gh, endpoint, code_receipt)
    archive_submitted(gh, endpoint, reply_receipt)
    pending_id = helper.own_pending(event['hostname'], endpoint, login)
    records = [read_json(path) for path in (code_receipt, reply_receipt) if path.exists()]
    if pending_id and not any(record.get('review_id') == pending_id or record.get('operation') for record in records):
        raise DeliveryError('pending_conflict', 'Existing user Pending is protected; all new candidates remain local')
    code_saved = None
    existing_concerns = []
    if result['review'] is not None:
        report = result['review']
        eligible = set(code_assessment['eligible_findings'])
        candidates = [f for f in report['findings'] if f['id'] in eligible]
        existing_concerns = [f['id'] for f in candidates if f['id'] in published_keys]
        candidates = [f for f in candidates if f['id'] not in published_keys]
        target_path, payload_path, report_path = (Path(run_dir) / name for name in ('pending-target.json', 'draft.json', 'review-result.json'))
        args = Namespace(action='capture', hostname=event['hostname'], repo=event['repo'], pr=event['pr'],
                         worktree=scope['worktree'], snapshot=str(target_path))
        target = helper.capture(args)
        anchors = helper.changed_lines(helper.diff_for(Path(scope['worktree']), target['base_sha'], target['head_sha']))
        comments, body = [], []
        for finding in candidates:
            if finding.get('revision', 'head') == 'head' and finding['line'] in anchors.get(finding['path'], set()):
                comments.append({'key': finding['id'], 'path': finding['path'], 'line': finding['line'],
                                 'side': 'RIGHT', 'body': finding['comment']})
            else:
                body.append(finding['comment'] + f'\n\n{finding["path"]}:{finding["line"]}')
        payload = {'comments': comments}
        if body:
            payload['body'] = '\n\n'.join(body); report['review_body'] = payload['body']
        save_json(payload_path, payload); save_json(report_path, report)
        if candidates or code_receipt.exists():
            args = Namespace(action='save', hostname=event['hostname'], repo=event['repo'], pr=event['pr'],
                             snapshot=str(target_path), payload=str(payload_path), receipt=str(code_receipt), review_result=str(report_path))
            code_saved = helper.run_session(args)
            if code_saved['status'] not in ('pending', 'no_findings'):
                raise DeliveryError('pending_conflict', 'Existing Pending needs reconciliation; candidate retained locally')
            if code_saved.get('review_id'):
                metadata = directory / f'round-{code_saved["review_id"]}.json'
                previous = read_json(metadata).get('finding_ids', []) if metadata.exists() else []
                save_json(metadata, {'review_id': code_saved['review_id'], 'finding_ids': sorted(set(previous) | {f['id'] for f in candidates})})
            fresh(gh, event, snapshot)
    replies = [(claim, row) for row in result['claims'] if row.get('reply')
               for claim in [next(c for c in event['claims'] if c['id'] == row['id'])] if claim['source'] == 'inline']
    if not replies:
        return {'status': 'pending_saved' if code_saved and code_saved['status'] == 'pending' else 'local_ready', 'code': code_saved, 'existing_concerns': existing_concerns}
    latest = fresh(gh, event, snapshot)
    pending_id = helper.own_pending(event['hostname'], endpoint, login)
    known_ids = {read_json(p).get('review_id') for p in (code_receipt, reply_receipt) if p.exists()}
    if pending_id and pending_id not in known_ids:
        raise DeliveryError('pending_conflict', 'An existing user Pending is protected; replies remain local')
    if not pending_id:
        if reply_receipt.exists() and read_json(reply_receipt).get('status') != 'policy_blocked':
            raise DeliveryError('write_unconfirmed', 'Reconcile the prior Pending creation before another write')
        blocked_operations = read_json(reply_receipt).get('blocked_operations', []) if reply_receipt.exists() else []
        save_json(reply_receipt, {**identity, 'status': 'create_unconfirmed', 'head_sha': latest['pr']['head']['sha'], 'blocked_operations': blocked_operations})
        created = guarded_api(event['hostname'], endpoint + '/reviews', {'commit_id': latest['pr']['head']['sha'], 'body': ''}, reply_receipt)
        pending_id = created.get('id')
        if type(pending_id) is not int:
            raise DeliveryError('write_unconfirmed', 'Pending creation returned no ID; do not replay')
        save_json(reply_receipt, {**read_json(reply_receipt), 'review_id': pending_id, 'status': 'created'})
    review, _ = helper.read_review(event['hostname'], endpoint, pending_id, login)
    if review['commit_id'] != latest['pr']['head']['sha']:
        raise DeliveryError('pending_conflict', 'Existing Pending is pinned to an older head')
    for claim, row in replies:
        latest = fresh(gh, event, snapshot)
        thread = next((t for t in latest['threads'] if t['id'] == claim['thread_id']), None)
        if thread is None or digest(public_comments(thread)) != claim['thread_digest']:
            raise DeliveryError('superseded', 'The reply thread changed during review')
        body = row['reply']['body']
        key = digest({'review_id': pending_id, 'claim': claim['id'], 'conversation': claim['thread_digest']})
        receipt = directory / ('reply-' + key + '.json')
        matches = [c for c in thread['comments'] if c['body'] == body
                   and (c.get('author') or {}).get('login', '').lower() == login.lower()
                   and (c.get('pullRequestReview') or {}).get('databaseId') == pending_id
                   and (c.get('pullRequestReview') or {}).get('state') == 'PENDING']
        blocked = receipt.exists() and read_json(receipt).get('status') == 'policy_blocked' and not matches
        if receipt.exists() and not blocked:
            if read_json(receipt)['body'] != body:
                raise DeliveryError('pending_conflict', 'A reply wording change remains local; preserve the prior draft')
            if len(matches) != 1:
                raise DeliveryError('write_unconfirmed', 'Prior reply write cannot be positively reconciled')
            save_json(receipt, {**read_json(receipt), 'status': 'pending', 'comment_id': matches[0]['id']})
            continue
        if matches:
            raise DeliveryError('pending_conflict', 'Matching unmanaged draft reply exists; preserve it')
        blocked_operations = read_json(receipt).get('blocked_operations', []) if receipt.exists() else []
        save_json(receipt, {'status': 'attempted', **identity, 'review_id': pending_id, 'blocked_operations': blocked_operations,
                            'thread_id': claim['thread_id'], 'body': body, 'head_sha': review['commit_id']})
        output = guarded_api(event['hostname'], 'graphql', {'query': '''mutation($input:AddPullRequestReviewThreadReplyInput!){addPullRequestReviewThreadReply(input:$input){comment{id body author{login} pullRequestReview{databaseId:fullDatabaseId state}}}}''',
                                   'variables': {'input': {'pullRequestReviewId': review['node_id'],
                                                          'pullRequestReviewThreadId': claim['thread_id'], 'body': body}}}, receipt)
        comment = output.get('data', {}).get('addPullRequestReviewThreadReply', {}).get('comment', {})
        if (not comment.get('id') or comment.get('body') != body
                or (comment.get('author') or {}).get('login', '').lower() != login.lower()
                or comment.get('pullRequestReview') != {'databaseId': pending_id, 'state': 'PENDING'}):
            raise DeliveryError('write_unconfirmed', 'Reply not verified as own Pending; inspect before retry')
        save_json(receipt, {**read_json(receipt), 'status': 'pending', 'comment_id': comment['id']})
        helper.read_review(event['hostname'], endpoint, pending_id, login)
        fresh(gh, event, snapshot)
        time.sleep(1)  # Serialize mutations to avoid secondary rate limits.
    return {'status': 'pending_saved', 'review_id': pending_id, 'url': review.get('html_url'), 'code': code_saved, 'existing_concerns': existing_concerns}
