"""GitHub reads and draft-only writes through the user's configured gh CLI."""
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import quote

from .state import HarnessError, digest, read_json, save_json


class ApiError(HarnessError):
    def __init__(self, message, status=0, retry_at=None):
        super().__init__(message); self.status = status; self.retry_at = retry_at


THREADS = '''query($owner:String!,$name:String!,$pr:Int!,$after:String){repository(owner:$owner,name:$name){pullRequest(number:$pr){reviewThreads(first:100,after:$after){totalCount pageInfo{hasNextPage endCursor} nodes{id path line originalLine diffSide isResolved isOutdated comments(first:100){totalCount pageInfo{hasNextPage endCursor} nodes{id databaseId body createdAt updatedAt author{login} commit{oid} pullRequestReview{databaseId state}}}}}}}}'''
COMMENTS = '''query($id:ID!,$after:String){node(id:$id){... on PullRequestReviewThread{comments(first:100,after:$after){totalCount pageInfo{hasNextPage endCursor} nodes{id databaseId body createdAt updatedAt author{login} commit{oid} pullRequestReview{databaseId state}}}}}'''


class GitHub:
    def __init__(self, config, root):
        self.config = config; self.host = config['hostname']; self.cache = Path(root) / 'http-cache'
        self.next_request = 0

    def api(self, endpoint, payload=None, *, cached=False):
        cache_path = self.cache / (digest({'host': self.host, 'endpoint': endpoint}) + '.json')
        previous = read_json(cache_path) if cached and cache_path.exists() else None
        args = [self.config['gh_path'], 'api', '--hostname', self.host, '--include',
                '--method', 'GET' if payload is None else 'POST', '-H', 'Accept: application/vnd.github+json', endpoint]
        if previous and previous.get('etag'):
            args += ['-H', 'If-None-Match: ' + previous['etag']]
        if payload is not None:
            args += ['--input', '-']
        if time.time() < self.next_request:
            raise ApiError('GitHub rate-limit backoff is active', 429, self.next_request)
        result = subprocess.run(args, input=None if payload is None else json.dumps(payload),
                                text=True, capture_output=True, timeout=90)
        chunks = re.split(r'\r?\n\r?\n', result.stdout, maxsplit=1)
        status, headers, body = 0, {}, ''
        if len(chunks) == 2 and chunks[0].startswith('HTTP/'):
            lines = chunks[0].splitlines(); status = int(lines[0].split()[1]); body = chunks[1]
            headers = {k.lower(): v.strip() for line in lines[1:] if ':' in line for k, v in [line.split(':', 1)]}
        else:
            body = result.stdout
        if status == 304 and previous:
            return previous['body']
        if result.returncode or status >= 400:
            retry_at = None
            if headers.get('retry-after', '').isdigit():
                retry_at = time.time() + int(headers['retry-after'])
            elif headers.get('x-ratelimit-remaining') == '0':
                retry_at = float(headers.get('x-ratelimit-reset', time.time() + 120))
            if retry_at:
                self.next_request = retry_at
            raise ApiError(f'GitHub request failed ({status or result.returncode}): {endpoint}', status, retry_at)
        try:
            value = json.loads(body)
        except ValueError as error:
            raise ApiError('GitHub returned malformed JSON: ' + endpoint) from error
        if isinstance(value, dict) and value.get('errors'):
            raise ApiError('GraphQL request incomplete; no write is authorized')
        if cached:
            save_json(cache_path, {'etag': headers.get('etag'), 'body': value})
        return value

    def pages(self, endpoint, *, cached=False):
        rows = []
        for page in range(1, 101):
            separator = '&' if '?' in endpoint else '?'
            batch = self.api(f'{endpoint}{separator}per_page=100&page={page}', cached=cached)
            if not isinstance(batch, list):
                raise ApiError('Incomplete REST collection')
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        raise ApiError('REST page limit reached; collection is incomplete')

    def connection(self, query, variables, path):
        rows, cursor, total, seen = [], None, None, set()
        for _ in range(100):
            value = self.api('graphql', {'query': query, 'variables': {**variables, 'after': cursor}})
            try:
                connection = value['data']
                for key in path:
                    connection = connection[key]
                count, batch, info = connection['totalCount'], connection['nodes'], connection['pageInfo']
                if type(count) is not int or count < 0 or (total is not None and total != count):
                    raise ValueError('Changed connection count')
                total = count
                for row in batch:
                    if not isinstance(row, dict) or not row.get('id') or row['id'] in seen:
                        raise ValueError('Missing/duplicate node')
                    seen.add(row['id']); rows.append(row)
                if type(info['hasNextPage']) is not bool:
                    raise ValueError('Unknown pagination state')
                if not info['hasNextPage']:
                    if len(rows) != total:
                        raise ValueError('Incomplete connection')
                    return rows
                next_cursor = info['endCursor']
                if not batch or not next_cursor or cursor == next_cursor:
                    raise ValueError('Cursor did not advance')
                cursor = next_cursor
            except (KeyError, TypeError, ValueError) as error:
                raise ApiError('GraphQL collection incomplete; no write is authorized') from error
        raise ApiError('GraphQL page limit reached')

    def login(self):
        login = self.api('user').get('login')
        if not isinstance(login, str) or not login:
            raise ApiError('Authenticated GitHub user is unavailable', 401)
        if self.config.get('login') and login.lower() != self.config['login'].lower():
            raise ApiError('GitHub account changed; run setup for this account', 401)
        return login

    def snapshot(self, repo, number):
        endpoint = f'repos/{repo}/pulls/{number}'
        pr = self.api(endpoint)
        if pr.get('base', {}).get('repo', {}).get('full_name', '').lower() != repo.lower():
            raise ApiError('PR identity differs from the configured repository')
        owner, name = repo.split('/')
        threads = self.connection(THREADS, {'owner': owner, 'name': name, 'pr': number},
                                  ('repository', 'pullRequest', 'reviewThreads'))
        for thread in threads:
            thread['comments'] = self.connection(COMMENTS, {'id': thread['id']}, ('node', 'comments'))
        reviews = self.pages(endpoint + '/reviews')
        conversation = self.pages(f'repos/{repo}/issues/{number}/comments')
        return {'pr': pr, 'threads': threads, 'reviews': reviews, 'conversation': conversation}

    def reviewed(self, repo, login):
        rows = []
        query = quote(f'repo:{repo} is:pr is:open reviewed-by:{login}', safe='')
        for page in range(1, 11):
            value = self.api(f'search/issues?q={query}&per_page=100&page={page}', cached=True)
            if value.get('incomplete_results') or not isinstance(value.get('items'), list):
                raise ApiError('Previously reviewed PR discovery is incomplete')
            rows.extend(row['number'] for row in value['items'])
            if len(rows) >= value['total_count']:
                return rows
        raise ApiError('Previously reviewed PR discovery exceeds the search limit')


def public_comments(thread):
    return [c for c in thread['comments'] if (c.get('pullRequestReview') or {}).get('state') != 'PENDING']


def fingerprint(snapshot, login=None):
    pr = snapshot['pr']
    threads = [{k: v for k, v in thread.items() if k != 'comments'} | {'comments': public_comments(thread)}
               for thread in snapshot['threads'] if public_comments(thread)]
    reviews = [r for r in snapshot['reviews'] if r['state'] != 'PENDING']
    conversation = snapshot['conversation']
    if login:
        # Own submission/answers update the baseline but must not cause a new review loop.
        login = login.lower()
        threads = [{'id': thread['id'], 'comments': [c for c in public_comments(thread)
                    if (c.get('author') or {}).get('login', '').lower() != login]}
                   for thread in snapshot['threads']]
        threads = [t for t in threads if t['comments']]
        reviews = [r for r in reviews if (r.get('user') or {}).get('login', '').lower() != login]
        conversation = [r for r in conversation if (r.get('user') or {}).get('login', '').lower() != login]
    return digest({'head': pr['head']['sha'], 'base': pr['base']['sha'], 'title': pr['title'],
                   'body': pr.get('body'), 'draft': pr.get('draft'), 'state': pr['state'],
                   'threads': threads, 'reviews': reviews, 'conversation': conversation,
                   'reviewers': [] if login else [x['login'] for x in pr.get('requested_reviewers', [])],
                   'teams': [] if login else [x['slug'] for x in pr.get('requested_teams', [])]})


def claims(snapshot, scenario, login):
    result = []
    for thread in snapshot['threads']:
        comments = public_comments(thread)
        if not comments:
            continue
        first, last = comments[0], comments[-1]
        author = (first.get('author') or {}).get('login', '').lower()
        last_author = (last.get('author') or {}).get('login', '').lower()
        if scenario == 'S2' and (thread['isResolved'] or last_author == login.lower()):
            continue
        if scenario == 'S4' and author != login.lower():
            continue
        if scenario not in ('S2', 'S4'):
            continue
        result.append({'id': 'inline:' + first['id'], 'body': first['body'], 'source': 'inline',
                       'review_ref': (first.get('commit') or {}).get('oid'), 'thread_id': thread['id'],
                       'last_comment_id': last['id'], 'discussion': comments,
                       'thread_digest': digest(comments), 'path': thread['path'],
                       'line': thread.get('line') or thread.get('originalLine')})
    if scenario in ('S2', 'S4'):
        for source, rows in [('review_body', snapshot['reviews']), ('conversation', snapshot['conversation'])]:
            for row in rows:
                own = (row.get('user') or {}).get('login', '').lower() == login.lower()
                if own != (scenario == 'S4') or not (row.get('body') or '').strip():
                    continue
                if row.get('state') == 'PENDING':
                    continue
                result.append({'id': source + ':' + str(row['id']), 'body': row['body'], 'source': source,
                               'review_ref': row.get('commit_id'), 'updated_at': row.get('updated_at') or row.get('submitted_at')})
    return result
