"""Complete read-only author collection with a paginating API double, no posts."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('author_collector', ROOT/'plugins/review/skills/review-respond/scripts/collect_review.py')
collector = importlib.util.module_from_spec(spec); spec.loader.exec_module(collector)


class ResponseCollectionTests(unittest.TestCase):
    def setUp(self):
        self.helper = collector.pending_helper(); self.calls = []; self.metadata_reads = 0
        self.head = 'a'*40; self.author = True; self.change_head = False
        self.reviews = [{'id':f'R{i}', 'state':'CHANGES_REQUESTED', 'body':f'Review {i}'} for i in range(151)]
        self.threads = [{'id':f'T{i}'} for i in range(101)]
        self.comments = {t['id']:[{'id':t['id']+'-C0', 'body':'Comment', 'author':{'login':'reviewer'}}] for t in self.threads}
        self.comments['T0'] = [{'id':f'T0-C{i}', 'body':f'Comment {i}', 'author':{'login':'reviewer' if i==150 else 'author'}} for i in range(151)]
        self.conversation = [{'id':i+1, 'body':f'Conversation {i}'} for i in range(101)]
        self.bad_page = None; self.graphql_error = False

    def connection(self, rows, after):
        offset=int(after) if after else 0; nodes=copy.deepcopy(rows[offset:offset+100]); more=offset+len(nodes)<len(rows)
        value={'totalCount':len(rows),'nodes':nodes,'pageInfo':{'hasNextPage':more,'endCursor':str(offset+len(nodes)) if nodes else None}}
        return value

    def api(self, host, endpoint, *, payload=None):
        self.calls.append((endpoint,copy.deepcopy(payload)))
        if endpoint=='graphql':
            self.assertTrue(payload['query'].lstrip().startswith('query'),'Only read queries permitted')
            query,variables=payload['query'],payload['variables']
            if 'AuthorResponseTarget' in query:
                self.metadata_reads+=1
                return {'data':{'viewer':{'login':'author'},'repository':{'nameWithOwner':'example/repo','pullRequest':{
                    'id':'PR1','number':7,'headRefOid':'b'*40 if self.change_head and self.metadata_reads>1 else self.head,
                    'headRefName':'feature','viewerDidAuthor':self.author,'reviewDecision':'CHANGES_REQUESTED','isDraft':False}}}}
            if self.graphql_error:return {'errors':[{'message':'incomplete'}]}
            ident=variables['id'];after=variables.get('after')
            if 'AuthorResponseReviews' in query:key,rows='reviews',self.reviews
            elif 'AuthorResponseThreads' in query:key,rows='reviewThreads',self.threads
            elif 'AuthorResponseComments' in query:key,rows='comments',self.comments[ident]
            else:self.fail('Unknown query')
            value=self.connection(rows,after)
            if self.bad_page==key:value['pageInfo'].pop('hasNextPage')
            return {'data':{'node':{'id':ident,key:value}}}
        self.assertIsNone(payload,'REST requests must be GET')
        self.assertTrue(endpoint.startswith('repos/example/repo/issues/7/comments?'))
        page=int(endpoint.rsplit('page=',1)[1])
        return copy.deepcopy(self.conversation[(page-1)*100:page*100])

    def collect(self):
        with patch.object(collector,'pending_helper',return_value=self.helper),patch.object(self.helper,'api',side_effect=self.api):
            return collector.collect('github.com','example/repo',7)

    def test_all_connections_and_nested_comments_are_complete(self):
        result=self.collect()
        self.assertEqual(result['counts'],{'reviews':151,'threads':101,'thread_comments':251,'conversation':101})
        self.assertEqual(result['reviews'][0]['id'],'R0')
        self.assertEqual(result['reviewThreads'][0]['comments'][-1]['author']['login'],'reviewer')
        self.assertEqual(self.metadata_reads,2)
        for name in ('Reviews','Threads','Comments'):
            self.assertTrue(any(p and 'AuthorResponse'+name in p['query'] and p['variables'].get('after') for _,p in self.calls))

    def test_original_51_item_boundary_keeps_review_body_and_last_reply(self):
        self.reviews=self.reviews[:51];self.threads=self.threads[:1]
        self.comments['T0']=self.comments['T0'][:51];self.comments['T0'][-1]['author']['login']='reviewer'
        result=self.collect()
        self.assertEqual(len(result['reviews']),51)
        self.assertEqual(result['reviews'][0]['id'],'R0')
        self.assertEqual(result['reviewThreads'][0]['comments'][-1]['id'],'T0-C50')
        self.assertEqual(result['reviewThreads'][0]['comments'][-1]['author']['login'],'reviewer')

    def test_missing_nested_page_info_fails_closed(self):
        for key in ('reviews','reviewThreads','comments'):
            with self.subTest(key=key):
                self.bad_page=key
                with self.assertRaises(collector.CollectionError):self.collect()

    def test_graphql_errors_do_not_return_partial_success(self):
        self.graphql_error=True
        with self.assertRaises(collector.CollectionError):self.collect()

    def test_head_change_during_collection_is_rejected(self):
        self.change_head=True
        with self.assertRaisesRegex(collector.CollectionError,'target changed'):self.collect()

    def test_other_authors_pr_is_rejected_before_comment_collection(self):
        self.author=False
        with self.assertRaisesRegex(collector.CollectionError,'did not author'):self.collect()
        self.assertEqual(len(self.calls),1)

    def test_duplicate_comment_identity_is_rejected(self):
        self.comments['T0'][100]['id']=self.comments['T0'][0]['id']
        with self.assertRaises(collector.CollectionError):self.collect()

    def test_missing_body_cannot_be_silently_dropped(self):
        self.reviews[0].pop('body')
        with self.assertRaisesRegex(collector.CollectionError,'body unavailable'):self.collect()


if __name__=='__main__':unittest.main()
