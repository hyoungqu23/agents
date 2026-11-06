#!/usr/bin/env python3
"""Read a complete author-response input snapshot. Never writes to GitHub or Git."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys


class CollectionError(ValueError):
    pass


def pending_helper():
    path = Path(__file__).resolve().parents[2] / 'review-pr/scripts/pending_review.py'
    spec = importlib.util.spec_from_file_location('author_collection_api', path)
    helper = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(helper)
    except OSError as error:
        raise CollectionError('Incomplete installation: install the four review skills together') from error
    return helper


METADATA = '''query AuthorResponseTarget($owner:String!,$repo:String!,$number:Int!) {
  viewer { login }
  repository(owner:$owner,name:$repo) { nameWithOwner
    pullRequest(number:$number) { id number url state viewerDidAuthor
      headRefName headRefOid reviewDecision isDraft }
  }
}'''
PAGE = 'totalCount pageInfo { hasNextPage endCursor }'
REVIEWS = '''query AuthorResponseReviews($id:ID!,$after:String) {
  node(id:$id) { id ... on PullRequest { reviews(first:100,after:$after) {
    ''' + PAGE + ''' nodes { id state body author { login } submittedAt url }
  } } }
}'''
THREADS = '''query AuthorResponseThreads($id:ID!,$after:String) {
  node(id:$id) { id ... on PullRequest { reviewThreads(first:100,after:$after) {
    ''' + PAGE + ''' nodes { id isResolved isOutdated viewerCanResolve viewerCanReply
      path line originalLine diffSide subjectType }
  } } }
}'''
COMMENTS = '''query AuthorResponseComments($id:ID!,$after:String) {
  node(id:$id) { id ... on PullRequestReviewThread { comments(first:100,after:$after) {
    ''' + PAGE + ''' nodes { id url body createdAt outdated author { login }
      authorAssociation replyTo { id } pullRequestReview { state } }
  } } }
}'''


def metadata(helper, host, repo, number):
    owner, name = repo.split('/')
    response = helper.api(host, 'graphql', payload={'query': METADATA,
                          'variables': {'owner': owner, 'repo': name, 'number': number}})
    if not isinstance(response, dict) or response.get('errors'):
        raise CollectionError('PR metadata read incomplete')
    data = response.get('data')
    if not isinstance(data, dict) or not isinstance(data.get('repository'), dict) or not isinstance(data.get('viewer'), dict):
        raise CollectionError('PR metadata fields unavailable')
    repository = data['repository']; pr = repository.get('pullRequest'); viewer = data['viewer'].get('login')
    if (not isinstance(pr, dict) or not isinstance(viewer, str) or not viewer
            or repository.get('nameWithOwner', '').lower() != repo.lower()
            or pr.get('number') != number or not isinstance(pr.get('id'), str) or not pr['id']
            or not isinstance(pr.get('headRefOid'), str) or not re.fullmatch(r'[0-9a-f]{40}', pr['headRefOid'])
            or not isinstance(pr.get('headRefName'), str) or not pr['headRefName']):
        raise CollectionError('PR identity or head is unavailable')
    if pr.get('viewerDidAuthor') is not True:
        raise CollectionError('The authenticated viewer did not author this PR')
    return {'viewer': viewer, 'pr': pr}


def collect(host, repo, number):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) or any(p in ('.', '..') for p in repo.split('/')):
        raise CollectionError('Expected owner/repository')
    if type(number) is not int or number <= 0:
        raise CollectionError('Expected a positive PR number')
    helper = pending_helper()
    try:
        target = metadata(helper, host, repo, number); pr_id = target['pr']['id']
        reviews = helper.graphql_nodes(host, REVIEWS, pr_id, ('reviews',))
        threads = helper.graphql_nodes(host, THREADS, pr_id, ('reviewThreads',))
        for thread in threads:
            thread['comments'] = helper.graphql_nodes(host, COMMENTS, thread['id'], ('comments',))
        conversation = helper.pages(host, f'repos/{repo}/issues/{number}/comments')
        ids = set()
        for row in conversation:
            if not isinstance(row, dict) or not helper.positive_id(row.get('id')) or row['id'] in ids:
                raise CollectionError('Conversation listing has missing or duplicate identities')
            ids.add(row['id'])
        for row in reviews + [comment for thread in threads for comment in thread['comments']] + conversation:
            if not isinstance(row.get('body'), str):
                raise CollectionError('Review/comment body unavailable; do not discard the item')
        if metadata(helper, host, repo, number) != target:
            raise CollectionError('PR target changed during collection; collect a fresh snapshot')
    except helper.ReviewError as error:
        raise CollectionError(str(error)) from error
    return {'schema_version': 1, 'hostname': host, 'repo': repo, 'number': number,
            **target, 'reviews': reviews, 'reviewThreads': threads, 'conversation': conversation,
            'counts': {'reviews': len(reviews), 'threads': len(threads),
                       'thread_comments': sum(len(t['comments']) for t in threads), 'conversation': len(conversation)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True); parser.add_argument('--pr', type=int, required=True)
    parser.add_argument('--hostname', default='github.com'); args = parser.parse_args()
    try:
        print(json.dumps(collect(args.hostname, args.repo, args.pr), ensure_ascii=False, indent=2))
        return 0
    except (CollectionError, OSError, ValueError, TypeError, KeyError) as error:
        print(str(error), file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
