"""Local Git + fake gh integration. No real GitHub writes or model calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'plugins/review/skills/review-pr/scripts/pending_review.py'
spec = importlib.util.spec_from_file_location('pending_review', SCRIPT)
pending = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pending)
fixture_spec = importlib.util.spec_from_file_location('result_fixtures', Path(__file__).with_name('review_result_fixtures.py'))
result_fixtures = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(result_fixtures)

GH_DOUBLE = r'''import json, os, sys, time
from pathlib import Path
p=Path(os.environ['PENDING_MOCK_STATE']);d=json.loads(p.read_text())
args=sys.argv[1:];method=args[args.index('--method')+1] if '--method' in args else 'GET'
endpoint=next(x.lstrip('/') for x in args if x.lstrip('/') in ('user','graphql') or x.lstrip('/').startswith('repos/'))
payload=json.loads(sys.stdin.read()) if '--input' in args else None
with Path(os.environ['PENDING_MOCK_CALLS']).open('a') as f:f.write(json.dumps({'method':method,'endpoint':endpoint,'payload':payload})+'\n')
prefix='repos/example/project/pulls/7'
def review(state='PENDING'):
 return {'id':91,'node_id':'PRR_91','state':state,'commit_id':d.get('created_head',d['head_sha']),
         'body':d.get('review_body','Manual summary'),'user':{'login':d.get('review_login','reviewer')},
         'html_url':'https://github.com/example/project/pull/7#pullrequestreview-91'}
def comment(c,index):
 return {**c,'id':index,'pull_request_review_id':91,'commit_id':d.get('created_head',d['head_sha']),
         'user':{'login':'reviewer'}}
def connection(rows,after=None):
 offset=int(after.split(':')[-1]) if after else 0
 page=rows[offset:offset+100];more=offset+len(page)<len(rows)
 cursor=f'cursor:{offset+len(page)}' if page else None
 if d.get('bad_graphql_cursor') and more:cursor=None
 return {'nodes':page,'totalCount':len(rows),'pageInfo':{'hasNextPage':more,'endCursor':cursor}}
if endpoint=='graphql' and payload.get('query','').lstrip().startswith('query'):
 if d.get('read_graphql_errors'):
  print(json.dumps({'data':None,'errors':[{'message':'incomplete read'}]}));sys.exit(0)
 variables=payload['variables'];after=variables.get('after');query=payload['query']
 r=review(d.get('readback_state','PENDING'))
 if d.get('wrong_review_commit') or d.get('wrong_commit_on_read')==d.get('review_reads'):r['commit_id']='e'*40
 node={'id':r['node_id'],'databaseId':r['id'],'state':r['state'],'submittedAt':'2026-10-14T00:00:00Z' if d.get('submitted_at') else None,
       'author':r['user'],'commit':{'oid':r['commit_id']},'body':r['body']}
 comments=d.get('review_comments',[])
 def graphql_comment(c):
  return {'id':f"PRRC_{c['id']}",'databaseId':c['id'],'path':c['path'],
          'line':c.get('line'),'originalLine':c.get('original_line',c.get('line')),
          'body':c['body'],'author':c.get('user',{'login':'reviewer'}),
          'commit':{'oid':c.get('commit_id',d.get('created_head',d['head_sha']))},
          'pullRequestReview':{'databaseId':c.get('pull_request_review_id',91)}}
 threads={}
 for c in comments:
  if c.get('missing_thread'):continue
  thread_id=c.get('thread_id',f"PRRT_{c['id']}")
  thread=threads.setdefault(thread_id,{'id':thread_id,'path':c['path'],'line':c.get('line'),
   'originalLine':c.get('original_line',c.get('line')),'diffSide':c.get('side','RIGHT'),
   'subjectType':c.get('subject_type','LINE'),'isOutdated':c.get('line') is None,'rows':[]})
  thread['rows'].append({'id':f"PRRC_{c['id']}",'databaseId':c['id'],
                         'pullRequestReview':{'databaseId':c.get('pull_request_review_id',91)}})
 if 'query ReviewComments' in query:
  node['comments']=connection([graphql_comment(c) for c in comments],after)
 elif 'query ReviewThreads' in query:
  rows=[{k:v for k,v in thread.items() if k!='rows'}|{'comments':connection(thread['rows'])} for thread in threads.values()]
  node['pullRequest']={'reviewThreads':connection(rows,after)}
 elif 'query ThreadComments' in query:
  node={'id':variables['id'],'comments':connection(threads[variables['id']]['rows'],after)}
 else:sys.exit(35)
 if d.get('missing_graphql_node'):node=None
 print(json.dumps({'data':{'node':node}}));sys.exit(0)
if method=='POST':
 if endpoint=='graphql':
  if d.get('submit_before_append'):d['readback_state']='COMMENTED';p.write_text(json.dumps(d));sys.exit(1)
  if d.get('readback_state','PENDING')!='PENDING':sys.exit(1)
  if 'addPullRequestReviewThread' not in payload.get('query',''):sys.exit(33)
  value=payload['variables']['input']
  if value.pop('pullRequestReviewId',None)!='PRR_91' or set(value)!={'body','path','line','side'}:sys.exit(33)
  if not d.get('drop_append'):
   comments=d.setdefault('review_comments',[]);comments.append(comment(value,max([c['id'] for c in comments]+[100])+1))
  if d.get('edit_on_append'):d['review_comments'][0]['body']='Edited while appending'
  concurrent=d.pop('concurrent_candidate',None)
  if concurrent:d['review_comments'].append(comment(concurrent,202))
  if d.get('advance_on_append'):d['head_sha']='f'*40
  p.write_text(json.dumps(d))
  if d.get('lost_append'):sys.exit(1)
  if d.get('graphql_errors'):print(json.dumps({'data':None,'errors':[{'message':'unknown result'}]}));sys.exit(0)
  print(json.dumps({'data':{'addPullRequestReviewThread':{'thread':{'id':'PRRT_1'}}}}));sys.exit(0)
 if endpoint!=prefix+'/reviews':sys.exit(33)
 if d.get('pause_create'):time.sleep(d['pause_create'])
 if d.get('drop_create'):sys.exit(1)
 d['created_head']=payload.get('commit_id');d['created']=True;d['review_body']=payload.get('body','')
 d['review_comments']=[comment(c,101+i) for i,c in enumerate(payload.get('comments',[]))];p.write_text(json.dumps(d))
 if d.get('dirty_on_post'):Path(d['worktree'],'app.py').write_text('changed during write\n')
 if d.get('lost_response'):sys.exit(1)
 print(json.dumps(review()));sys.exit(0)
if endpoint=='user':
 if d.get('dirty_on_user'):Path(d['worktree'],'app.py').write_text('changed during reads\n')
 result={'login':d.get('login','reviewer')}
elif endpoint==prefix:
 d['pr_reads']=d.get('pr_reads',0)+1;p.write_text(json.dumps(d))
 head=d['head_sha']
 if d.get('advance_on_read')==d['pr_reads']:head='f'*40
 if any('vnd.github.v3.diff' in a or 'vnd.github.diff' in a for a in args):print(d.get('diff',''));sys.exit(0)
 result={'number':7,'state':d.get('pr_state','open'),'title':'Simplify first-name lookup',
         'body':'Keep the existing first-name lookup behavior while simplifying its implementation.',
         'head':{'sha':head,'ref':'feature'},'base':{'sha':d['base_sha'],'ref':'main','repo':{'full_name':d.get('repo','example/project')}}}
elif endpoint==prefix+'/files':result=d.get('files',[])
elif endpoint==prefix+'/commits':result=[{'sha':d['head_sha'],'commit':{'message':'Simplify first-name lookup'}}]
elif endpoint in (prefix+'/comments','repos/example/project/issues/7/comments'):result=[]
elif endpoint.startswith(prefix+'/reviews?'):
 page=int(endpoint.split('page=')[-1])
 if d.get('pending_page_two') and page==1:
  result=[{'id':i,'state':'COMMENTED','user':{'login':'reviewer'}} for i in range(100)]
 else:result=[review(d.get('readback_state','PENDING'))] if d.get('existing_pending') or d.get('created') or d.get('pending_page_two') else []
elif endpoint.startswith(prefix+'/reviews/91/comments?'):
 page=int(endpoint.split('page=')[-1]);result=d.get('review_comments',[])[(page-1)*100:page*100]
 result=[{k:v for k,v in c.items() if k not in ('line','side')} for c in result]
elif endpoint.startswith('repos/example/project/pulls/comments/'):
 if d.get('readback_state','PENDING')=='PENDING':
  print('gh: Not Found (HTTP 404)',file=sys.stderr);sys.exit(1)
 comment_id=int(endpoint.rsplit('/',1)[1]);result=next(c for c in d['review_comments'] if c['id']==comment_id)
elif endpoint==prefix+'/reviews/91':
 if d.get('missing_review'):sys.exit(1)
 d['review_reads']=d.get('review_reads',0)+1
 if d.get('edit_on_review_read')==d['review_reads']:d['review_body']='Concurrent manual summary'
 p.write_text(json.dumps(d))
 result=review(d.get('readback_state','PENDING'))
 if d.get('submitted_at'):result['submitted_at']='2026-10-14T00:00:00Z'
 if d.get('wrong_review_commit') or d.get('wrong_commit_on_read')==d['review_reads']:result['commit_id']='e'*40
else:sys.exit(34)
print(json.dumps(result))
'''


class PendingReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.seed, self.bare, self.worktree = (self.root/n for n in ('seed','origin.git','reviewer'))
        self.env = {**os.environ, 'GIT_CONFIG_NOSYSTEM':'1', 'GIT_CONFIG_GLOBAL':os.devnull}
        self.g('init','--bare','-q',str(self.bare))
        self.g('init','-q','-b','main',str(self.seed))
        self.g('-C',str(self.seed),'config','user.name','Fixture')
        self.g('-C',str(self.seed),'config','user.email','fixture@example.invalid')
        (self.seed/'app.py').write_text('def first_name(rows):\n    return rows[0]["name"] if rows else None\n')
        self.g('-C',str(self.seed),'add','app.py')
        self.g('-C',str(self.seed),'commit','-qm','base')
        self.base = self.g('-C',str(self.seed),'rev-parse','HEAD').stdout.strip()
        self.g('-C',str(self.seed),'remote','add','origin',str(self.bare))
        self.g('-C',str(self.seed),'push','-q','origin','main')
        self.g('-C',str(self.seed),'switch','-qc','feature')
        (self.seed/'app.py').write_text('def first_name(rows):\n    return rows[0]["name"]\n')
        (self.seed/'limit.py').write_text('MAX_ROWS = 0\nMIN_ROWS = -1\n')
        self.g('-C',str(self.seed),'add','limit.py')
        self.g('-C',str(self.seed),'commit','-qam','unguarded access')
        self.head = self.g('-C',str(self.seed),'rev-parse','HEAD').stdout.strip()
        self.g('-C',str(self.seed),'push','-q','origin','feature')
        self.g('-C',str(self.seed),'worktree','add','-q','--detach',str(self.worktree),self.head)
        self.original = (self.worktree/'app.py').read_bytes()
        self.state, self.calls = self.root/'remote.json', self.root/'calls.jsonl'
        self.state.write_text(json.dumps({'base_sha':self.base,'head_sha':self.head,'worktree':str(self.worktree)}))
        binary=self.root/'bin';binary.mkdir()
        gh=binary/'gh';gh.write_text(f'#!{sys.executable}\n'+GH_DOUBLE);gh.chmod(0o755)
        self.env.update(PATH=f"{binary}{os.pathsep}{self.env['PATH']}",
                        PENDING_MOCK_STATE=str(self.state),PENDING_MOCK_CALLS=str(self.calls))
        self.snapshot,self.payload,self.receipt=(self.root/n for n in ('target.json','payload.json','receipt.json'))
        self.review_result = self.root/'review-result.json'
        self.auto_review_result = True
        self.payload.write_text(json.dumps({'body':'Reviewed draft','comments':[
            {'path':'app.py','line':2,'side':'RIGHT','body':'Empty rows raise IndexError; retain the guard.'}]}))
        self.assertEqual(self.invoke('capture','--worktree',str(self.worktree)).returncode,0)
        self.calls.write_text('')

    def g(self,*args):
        return subprocess.run(['git',*args],env=self.env,text=True,capture_output=True,check=True)

    def invoke(self,action,*extra):
        args=[sys.executable,str(SCRIPT),action,'--repo','example/project','--pr','7','--snapshot',str(self.snapshot)]
        if action=='save':
            if self.auto_review_result:self.prepare_result()
            args+=['--payload',str(self.payload),'--review-result',str(self.review_result)]
        if action in ('save','inspect'):args+=['--receipt',str(self.receipt)]
        result = subprocess.run([*args,*extra],env=self.env,text=True,capture_output=True,timeout=30)
        if action=='capture' and result.returncode==0:
            target=json.loads(result.stdout)
            self.review_scope=result_fixtures.gate.capture_scope(target['worktree'],target['base_sha'],target['head_sha'])
        return result

    def prepare_result(self):
        report=result_fixtures.report_for(self.review_scope)
        value=json.loads(self.payload.read_text())
        report['review_body']=value.get('body','')
        for comment in value.get('comments',[]):
            report['findings'].append(result_fixtures.finding_for(self.review_scope,comment.get('path'),
                comment.get('line'),comment.get('body'),pending.finding_key(comment)))
        self.review_result.write_text(json.dumps(report))

    def remote(self,**changes):
        d=json.loads(self.state.read_text());d.update(changes);self.state.write_text(json.dumps(d))

    def log(self):
        return [json.loads(x) for x in self.calls.read_text().splitlines() if x.strip()]

    def mutations(self):
        return [c for c in self.log() if c['method']!='GET' and not (
            c['endpoint']=='graphql' and c['payload'].get('query','').lstrip().startswith('query'))]

    def record(self):return json.loads(self.receipt.read_text())

    def draft(self):return json.loads(self.payload.read_text())

    def update_draft(self, value):self.payload.write_text(json.dumps(value))

    def append_candidate(self, line=1):
        value=self.draft()
        value['comments'].append({'key':f'limit-{line}','path':'limit.py','line':line,'side':'RIGHT','body':f'Check limit {line}.'})
        self.update_draft(value)

    def save_ok(self):
        result=self.invoke('save');self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        return self.record()

    def test_creates_only_pending_review_on_reviewed_commit(self):
        result=self.invoke('save');self.assertEqual(result.returncode,0,result.stderr)
        writes=self.mutations();self.assertEqual(len(writes),1)
        self.assertEqual(writes[0]['endpoint'],'repos/example/project/pulls/7/reviews')
        self.assertEqual(writes[0]['payload']['commit_id'],self.head)
        self.assertNotIn('event',writes[0]['payload'])
        self.assertEqual(json.loads(self.receipt.read_text())['state'],'PENDING')
        self.assertEqual((self.worktree/'app.py').read_bytes(),self.original)
        self.assertEqual(self.g('-C',str(self.worktree),'status','--porcelain').stdout,'')

    def test_all_event_values_and_override_commit_are_rejected(self):
        original=json.loads(self.payload.read_text())
        for key,value in [('event','COMMENT'),('event','APPROVE'),('event','REQUEST_CHANGES'),('event','PENDING'),('event',None),('commit_id',self.head)]:
            with self.subTest(key=key,value=value):
                self.payload.write_text(json.dumps({**original,key:value}))
                self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(self.mutations(),[])

    def test_head_or_base_change_before_create_blocks_write(self):
        for field in ('head_sha','base_sha'):
            with self.subTest(field=field):
                self.remote(**{field:'f'*40})
                self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(self.mutations(),[])
                self.remote(head_sha=self.head,base_sha=self.base)

    def test_dirty_or_moved_checkout_blocks_write(self):
        (self.worktree/'app.py').write_text('local change\n')
        self.assertNotEqual(self.invoke('save').returncode,0);self.assertEqual(self.mutations(),[])
        (self.worktree/'app.py').write_bytes(self.original)
        self.g('-C',str(self.worktree),'checkout','-q','--detach',self.base)
        self.assertNotEqual(self.invoke('save').returncode,0);self.assertEqual(self.mutations(),[])

    def test_change_during_preflight_blocks_write(self):
        self.remote(dirty_on_user=True)
        self.assertNotEqual(self.invoke('save').returncode,0);self.assertEqual(self.mutations(),[])

    def test_new_head_during_creation_leaves_stale_pending(self):
        self.remote(advance_on_read=4) # two capture reads, pre-create, post-create
        result=self.invoke('save');self.assertNotEqual(result.returncode,0)
        record=json.loads(self.receipt.read_text());self.assertEqual(record['status'],'pending_stale')
        self.assertEqual(record['state'],'PENDING');self.assertEqual(len(self.mutations()),1)
        self.assertEqual(self.mutations()[0]['payload']['commit_id'],self.head)

    def test_changed_checkout_after_create_is_not_reported_fresh(self):
        self.remote(dirty_on_post=True)
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual(json.loads(self.receipt.read_text())['status'],'pending_stale')

    def test_existing_pending_including_later_page_is_untouched(self):
        for option in ('existing_pending','pending_page_two'):
            with self.subTest(option=option):
                self.remote(**{'existing_pending':False,'pending_page_two':False,option:True})
                self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(self.mutations(),[])

    def test_readback_must_be_pending_unsubmitted_and_same_commit(self):
        for change in ({'readback_state':'COMMENTED'},{'submitted_at':True},{'wrong_review_commit':True}):
            with self.subTest(change=change):
                self.remote(readback_state='PENDING',submitted_at=False,wrong_review_commit=False,created=False)
                self.remote(**change)
                if self.receipt.exists():self.receipt.unlink()
                self.calls.write_text('')
                self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(len(self.mutations()),1)
                self.assertIn(json.loads(self.receipt.read_text())['status'],('create_unconfirmed','write_unconfirmed'))

    def test_lost_response_is_not_replayed(self):
        self.remote(lost_response=True)
        self.assertNotEqual(self.invoke('save').returncode,0)
        result=self.invoke('save');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(self.mutations()),1)
        self.assertEqual(json.loads(self.receipt.read_text())['status'],'pending')

    def test_context_line_or_left_or_malformed_anchor_is_rejected(self):
        original=json.loads(self.payload.read_text())
        for change in ({'line':1},{'line':True},{'line':200},{'side':'LEFT'},{'path':'../app.py'},{'path':'missing.py'}):
            with self.subTest(change=change):
                value=json.loads(json.dumps(original));value['comments'][0].update(change)
                self.payload.write_text(json.dumps(value));self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(self.mutations(),[])

    def test_body_only_draft_is_still_pending(self):
        self.payload.write_text(json.dumps({'body':'Finding has no valid inline anchor.'}))
        self.assertEqual(self.invoke('save').returncode,0)
        self.assertEqual(self.mutations()[0]['payload']['comments'],[])
        self.assertNotIn('event',self.mutations()[0]['payload'])

    def test_bad_snapshot_identity_and_inside_checkout_output_are_rejected(self):
        target=json.loads(self.snapshot.read_text())
        self.snapshot.write_text(json.dumps({**target,'repo':'other/project'}))
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.snapshot.write_text(json.dumps({**target,'base_sha':'--output=unwanted'}))
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.snapshot.write_text(json.dumps(target))
        result=self.invoke('save','--receipt',str(self.worktree/'receipt.json'))
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.worktree/'receipt.json').exists())
        self.assertEqual(self.mutations(),[])

    def test_diff_content_cannot_impersonate_a_file_header(self):
        diff='diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+++ b/spoof.py\n+real new line\n'
        self.assertEqual(pending.changed_lines(diff),{'app.py':{1,2}})

    def test_subdirectory_does_not_weaken_checkout_output_boundary(self):
        nested=self.worktree/'subdir';nested.mkdir()
        result=self.invoke('capture','--worktree',str(nested),'--snapshot',str(self.worktree/'target.json'))
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.worktree/'target.json').exists())
        target=json.loads(self.snapshot.read_text());target['worktree']=str(nested)
        self.snapshot.write_text(json.dumps(target))
        result=self.invoke('save','--receipt',str(self.worktree/'receipt.json'))
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.worktree/'receipt.json').exists())
        self.assertEqual(self.mutations(),[])

    def test_same_head_rerun_is_read_only(self):
        self.save_ok();self.calls.write_text('')
        record=self.save_ok()
        self.assertEqual(self.mutations(),[])
        self.assertEqual(len(record['plan']['unchanged']),1)
        self.assertEqual(record['review_head_sha'],self.head)

    def test_final_readback_cannot_report_a_different_commit_as_fresh(self):
        self.save_ok();reads=json.loads(self.state.read_text())['review_reads']
        self.remote(wrong_commit_on_read=reads+2);self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['status'],'pending_stale')
        self.assertEqual(self.mutations(),[])

    def test_new_finding_appends_to_existing_pending_and_rerun_deduplicates(self):
        self.save_ok();self.append_candidate();self.calls.write_text('')
        record=self.save_ok()
        self.assertEqual(len(self.mutations()),1)
        request=self.mutations()[0]
        self.assertEqual(request['endpoint'],'graphql')
        self.assertEqual(request['payload']['variables']['input']['pullRequestReviewId'],'PRR_91')
        self.assertNotIn('key',request['payload']['variables']['input'])
        self.assertEqual(len(record['managed']),2)
        self.calls.write_text('');self.save_ok();self.assertEqual(self.mutations(),[])

    def test_manual_edit_and_delete_are_preserved_and_block_batch(self):
        self.save_ok();self.append_candidate()
        original=json.loads(self.state.read_text())['review_comments']
        for remote in ([{**original[0],'body':'User wording'}],[]):
            with self.subTest(remote=remote):
                self.remote(review_comments=remote);self.calls.write_text('')
                self.assertEqual(self.invoke('save').returncode,2)
                record=self.record()
                self.assertEqual(record['status'],'pending_conflicts')
                self.assertIn(record['plan']['conflicts'][0]['reason'],('edited_remote','deleted_remote'))
                self.assertEqual(self.mutations(),[])
                self.assertEqual(json.loads(self.state.read_text())['review_comments'],remote)

    def test_stable_key_prevents_reworded_finding_from_becoming_new_comment(self):
        value=self.draft();value['comments'][0]['key']='empty-input';self.update_draft(value)
        self.save_ok();value['comments'][0]['body']='Reworded analysis';self.update_draft(value)
        self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['plan']['conflicts'][0]['reason'],'proposed_change')
        self.assertEqual(self.mutations(),[])

    def test_reworded_auto_key_collides_with_existing_anchor(self):
        self.save_ok();value=self.draft();value['comments'][0]['body']='Different wording';self.update_draft(value)
        self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertIn('occupied_anchor',[c['reason'] for c in self.record()['plan']['conflicts']])
        self.assertEqual(self.mutations(),[])

    def test_deleted_finding_with_regenerated_key_cannot_be_recreated(self):
        self.save_ok();self.remote(review_comments=[])
        value=self.draft();value['comments'][0].update(key='new-key',body='Reworded');self.update_draft(value)
        self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['plan']['conflicts'][0]['reason'],'deleted_remote')
        self.assertEqual(self.mutations(),[])

    def test_pending_comments_use_graphql_not_rest_detail_or_diff_position(self):
        record=self.save_ok();self.assertEqual(len(record['managed']),1)
        self.assertFalse(any(c['endpoint'].startswith('repos/example/project/pulls/comments/') for c in self.log()))
        self.assertTrue(any(c['endpoint']=='graphql' and 'query ReviewComments' in c['payload']['query'] for c in self.log()))
        self.calls.write_text('');self.save_ok();self.assertEqual(self.mutations(),[])

    def manual_comments(self, count=1, **changes):
        comments=[{**self.draft()['comments'][0], 'id':101+i,'pull_request_review_id':91,
                   'commit_id':self.head,'user':{'login':'reviewer'},**changes} for i in range(count)]
        self.remote(existing_pending=True,review_comments=comments)
        return comments

    def test_inspect_reads_manual_pending_with_inline_comments(self):
        self.manual_comments()
        result=self.invoke('inspect');self.assertEqual(result.returncode,0,result.stderr)
        observed=self.record()['observed']['comments']
        self.assertEqual((observed[0]['line'],observed[0]['side']),(2,'RIGHT'))
        self.assertEqual(self.mutations(),[])

    def test_inspect_paginates_review_comments_and_threads(self):
        self.manual_comments(count=101)
        result=self.invoke('inspect');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(self.record()['observed']['comments']),101)
        queries=[c['payload'] for c in self.log() if c['endpoint']=='graphql']
        for name in ('ReviewComments','ReviewThreads'):
            self.assertTrue(any(f'query {name}' in q['query'] and q['variables'].get('after') for q in queries))
        self.assertEqual(self.mutations(),[])

    def test_inspect_paginates_comments_within_one_thread(self):
        self.manual_comments(count=101,thread_id='PRRT_long')
        result=self.invoke('inspect');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(self.record()['observed']['comments']),101)
        self.assertTrue(any(c['endpoint']=='graphql' and 'query ThreadComments' in c['payload']['query'] for c in self.log()))
        self.assertEqual(self.mutations(),[])

    def test_incomplete_graphql_read_blocks_append(self):
        self.save_ok();self.append_candidate()
        for change in ({'read_graphql_errors':True},{'missing_graphql_node':True}):
            with self.subTest(change=change):
                self.remote(**{'read_graphql_errors':False,'missing_graphql_node':False,**change})
                self.calls.write_text('')
                self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(self.mutations(),[])

    def test_invalid_pagination_or_unmapped_comment_blocks_write(self):
        for change in ({'count':101},{'missing_thread':True}):
            with self.subTest(change=change):
                self.manual_comments(**change)
                self.remote(bad_graphql_cursor='count' in change)
                self.calls.write_text('')
                self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(self.mutations(),[])

    def test_graphql_read_recovers_unconfirmed_create_without_replay(self):
        self.remote(read_graphql_errors=True)
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual(self.record()['status'],'create_unconfirmed')
        self.remote(read_graphql_errors=False);self.calls.write_text('')
        result=self.invoke('inspect');self.assertEqual(result.returncode,0,result.stderr)
        self.assertIsNone(self.record()['operation']);self.assertEqual(len(self.record()['managed']),1)
        self.assertEqual(self.mutations(),[])

    def test_inspect_preserves_left_and_outdated_anchors(self):
        self.manual_comments(line=None,original_line=2,side='LEFT')
        result=self.invoke('inspect');self.assertEqual(result.returncode,0,result.stderr)
        comment=self.record()['observed']['comments'][0]
        self.assertIsNone(comment['line']);self.assertEqual(comment['side'],'LEFT')
        self.assertEqual(comment['original_line'],2)

    def test_api_error_identifies_method_and_endpoint_without_payload(self):
        self.remote(drop_create=True)
        result=self.invoke('save')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('[POST repos/example/project/pulls/7/reviews]',result.stderr)
        self.assertNotIn(self.draft()['comments'][0]['body'],result.stderr)

    def test_summary_is_preserved_and_omission_keeps_it(self):
        self.save_ok();self.remote(review_body='Manual summary edit');self.append_candidate()
        self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2);self.assertEqual(self.mutations(),[])
        value=self.draft();value.pop('body');self.update_draft(value)
        record=self.save_ok()
        self.assertEqual(record['observed']['body'],'Manual summary edit')
        self.assertEqual(len(self.mutations()),1)

    def test_omitted_finding_is_reported_without_deleting_remote(self):
        self.save_ok();self.update_draft({'comments':[]});self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['plan']['conflicts'][0]['reason'],'omitted_existing')
        self.assertEqual(self.mutations(),[])

    def test_empty_clean_review_creates_nothing(self):
        self.update_draft({'comments':[]});result=self.invoke('save')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'no_findings')
        self.assertEqual(self.mutations(),[])

    def test_empty_review_still_checks_current_target(self):
        self.update_draft({'comments':[]})
        for changes in ({'head_sha':'f'*40},{'base_sha':'f'*40},{'pr_state':'closed'}):
            with self.subTest(changes=changes):
                self.remote(head_sha=self.head,base_sha=self.base,pr_state='open');self.remote(**changes)
                self.assertNotEqual(self.invoke('save').returncode,0)
                self.assertEqual(self.mutations(),[])

    def test_lost_append_is_reconciled_before_remaining_batch(self):
        self.save_ok();self.append_candidate(1);self.append_candidate(2);self.calls.write_text('')
        self.remote(lost_append=True)
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual(self.record()['operation']['kind'],'append')
        self.remote(lost_append=False)
        record=self.save_ok()
        self.assertEqual(len(self.mutations()),2)
        self.assertEqual(len(record['observed']['comments']),3)
        self.assertIsNone(record['operation'])

    def test_absent_uncertain_append_is_never_replayed(self):
        self.save_ok();self.append_candidate();self.calls.write_text('')
        self.remote(lost_append=True,drop_append=True)
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.remote(lost_append=False,drop_append=False)
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['status'],'write_unconfirmed')
        self.assertEqual(len(self.mutations()),1)

    def test_absent_uncertain_create_is_never_replayed(self):
        self.remote(drop_create=True)
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.remote(drop_create=False)
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(len(self.mutations()),1)

    def test_graphql_partial_error_keeps_journal_until_positive_readback(self):
        self.save_ok();self.append_candidate();self.remote(graphql_errors=True)
        self.calls.write_text('')
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual(self.record()['operation']['kind'],'append')
        self.save_ok();self.assertEqual(len(self.mutations()),1)

    def test_inspect_recovers_lost_response_without_writing(self):
        self.remote(lost_response=True);self.assertNotEqual(self.invoke('save').returncode,0)
        self.calls.write_text('')
        result=self.invoke('inspect');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.record()['status'],'inspected')
        self.assertIsNone(self.record()['operation']);self.assertEqual(self.mutations(),[])
        self.assertFalse(self.record()['needs_reassessment'])

    def test_receipt_survives_recreated_worktree(self):
        self.save_ok()
        self.g('-C',str(self.seed),'worktree','remove',str(self.worktree))
        replacement=self.root/'replacement'
        self.g('-C',str(self.seed),'worktree','add','-q','--detach',str(replacement),self.head)
        self.snapshot=self.root/'new-target.json'
        self.assertEqual(self.invoke('capture','--worktree',str(replacement)).returncode,0)
        self.calls.write_text('');self.save_ok();self.assertEqual(self.mutations(),[])

    def test_missing_receipt_adopts_remote_exact_matches(self):
        self.save_ok();self.receipt.unlink();self.calls.write_text('')
        record=self.save_ok();self.assertEqual(len(record['managed']),1)
        self.assertEqual(self.mutations(),[])

    def test_unmanaged_drafts_are_preserved_when_adding_a_distinct_finding(self):
        self.remote(existing_pending=True)
        self.update_draft({'comments':[{'key':'limit','path':'limit.py','line':1,'side':'RIGHT','body':'Check limit.'}]})
        record=self.save_ok();self.assertEqual(record['observed']['body'],'Manual summary')
        self.assertEqual([c['endpoint'] for c in self.mutations()],['graphql'])

    def test_new_head_preserves_old_pending_and_returns_reassessment_plan(self):
        self.save_ok()
        (self.seed/'app.py').write_text('# shifted\ndef first_name(rows):\n    return rows[0]["name"]\n')
        self.g('-C',str(self.seed),'commit','-qam','shift lines')
        new_head=self.g('-C',str(self.seed),'rev-parse','HEAD').stdout.strip()
        self.g('-C',str(self.worktree),'checkout','-q','--detach',new_head)
        self.remote(head_sha=new_head)
        self.snapshot=self.root/'new-target.json'
        self.assertEqual(self.invoke('capture','--worktree',str(self.worktree)).returncode,0)
        value=self.draft();value['comments'][0]['line']=3;self.update_draft(value)
        self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        record=self.record();self.assertEqual(record['status'],'pending_stale')
        self.assertEqual(record['review_head_sha'],self.head)
        self.assertEqual(record['plan']['target']['head_sha'],new_head)
        self.assertEqual(self.mutations(),[])
        result=self.invoke('inspect');self.assertEqual(result.returncode,0)
        self.assertTrue(self.record()['needs_reassessment'])

    def test_base_change_after_recapture_requires_reassessment(self):
        self.save_ok()
        target=json.loads(self.snapshot.read_text())
        record=self.record();record['review_target']['base_sha']='a'*40;self.receipt.write_text(json.dumps(record))
        self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['status'],'pending_stale');self.assertEqual(self.mutations(),[])
        self.assertEqual(json.loads(self.snapshot.read_text()),target)

    def test_submitted_or_deleted_draft_is_not_replaced(self):
        self.save_ok();self.append_candidate()
        for change in ({'readback_state':'COMMENTED'},{'missing_review':True}):
            with self.subTest(change=change):
                self.remote(readback_state='PENDING',missing_review=False);self.remote(**change)
                self.calls.write_text('')
                self.assertNotEqual(self.invoke('save').returncode,0);self.assertEqual(self.mutations(),[])

    def test_submission_race_does_not_fall_back_to_published_comment(self):
        self.save_ok();self.append_candidate();self.remote(submit_before_append=True);self.calls.write_text('')
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual([c['endpoint'] for c in self.mutations()],['graphql'])
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual(len(self.mutations()),1)

    def test_remote_edit_between_plan_and_append_stops_write(self):
        self.save_ok();self.append_candidate()
        reads=json.loads(self.state.read_text())['review_reads']
        self.remote(edit_on_review_read=reads+2);self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['status'],'remote_changed');self.assertEqual(self.mutations(),[])

    def test_edit_during_append_is_reported_as_conflict(self):
        self.save_ok();self.append_candidate();self.remote(edit_on_append=True)
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['status'],'pending_conflicts')

    def test_edit_during_first_append_stops_remaining_batch(self):
        self.save_ok();self.append_candidate(1);self.append_candidate(2)
        self.remote(edit_on_append=True);self.calls.write_text('')
        self.assertEqual(self.invoke('save').returncode,2)
        self.assertEqual(self.record()['status'],'pending_conflicts')
        self.assertEqual(len(self.mutations()),1)

    def test_concurrent_exact_addition_is_removed_from_remaining_batch(self):
        self.save_ok();self.append_candidate(1);self.append_candidate(2)
        concurrent={k:v for k,v in self.draft()['comments'][-1].items() if k!='key'}
        self.remote(concurrent_candidate=concurrent);self.calls.write_text('')
        record=self.save_ok()
        self.assertEqual(len(self.mutations()),1)
        self.assertEqual(len(record['observed']['comments']),3)

    def test_head_race_during_append_keeps_original_pending(self):
        self.save_ok();self.append_candidate();self.remote(advance_on_append=True);self.calls.write_text('')
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual(self.record()['status'],'pending_stale')
        self.assertEqual(len(self.mutations()),1)

    def test_legacy_receipt_migrates_only_with_matching_original_payload(self):
        self.save_ok()
        payload={'commit_id':self.head,**self.draft()}
        legacy={'repo':'example/project','pr':7,'head_sha':self.head,'status':'pending',
                'review_id':91,'payload_sha256':pending.digest(payload)}
        self.receipt.write_text(json.dumps(legacy));self.calls.write_text('')
        self.assertEqual(self.invoke('inspect').returncode,2)
        record=self.save_ok();self.assertEqual(record['legacy_receipt'],legacy)
        self.assertEqual(self.mutations(),[])

    def test_receipt_account_and_target_binding(self):
        self.save_ok();original=self.record()
        for field,value in [('hostname','other.invalid'),('repo','other/project'),('pr',9),('login','another')]:
            with self.subTest(field=field):
                self.receipt.write_text(json.dumps({**original,field:value}));self.calls.write_text('')
                self.assertNotEqual(self.invoke('save').returncode,0);self.assertEqual(self.mutations(),[])

    def test_payload_and_receipt_cannot_alias(self):
        original=self.payload.read_bytes()
        self.assertNotEqual(self.invoke('save','--receipt',str(self.payload)).returncode,0)
        self.assertEqual(self.payload.read_bytes(),original);self.assertEqual(self.mutations(),[])

    def test_duplicate_keys_and_comments_are_rejected_before_writing(self):
        value=self.draft();comment=value['comments'][0]
        for comments in ([{**comment,'key':'same'},{**comment,'key':'same','body':'Other'}],
                         [{**comment,'key':'one'},{**comment,'key':'two'}]):
            self.update_draft({'comments':comments})
            self.assertNotEqual(self.invoke('save').returncode,0);self.assertEqual(self.mutations(),[])

    def test_comments_are_paginated_before_deduplication(self):
        self.save_ok();original=json.loads(self.state.read_text())['review_comments'][0]
        comments=[{**original,'id':200+i,'path':f'file-{i}.py','body':'Manual'} for i in range(100)]
        comments.append(original);self.remote(review_comments=comments)
        self.receipt.unlink();self.calls.write_text('')
        self.save_ok();self.assertEqual(self.mutations(),[])
        self.assertTrue(any(c['endpoint']=='graphql' and 'query ReviewComments' in c['payload']['query']
                            and c['payload']['variables'].get('after') for c in self.log()))

    def test_concurrent_saves_share_a_lock_and_create_once(self):
        self.remote(pause_create=1.5)
        self.prepare_result()
        args=[sys.executable,str(SCRIPT),'save','--repo','example/project','--pr','7',
              '--snapshot',str(self.snapshot),'--payload',str(self.payload),'--receipt',str(self.receipt),
              '--review-result',str(self.review_result)]
        first=subprocess.Popen(args,env=self.env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.addCleanup(lambda: first.kill() if first.poll() is None else None)
        for _ in range(100):
            if self.receipt.exists():break
            time.sleep(.02)
        second=self.invoke('save')
        self.assertNotEqual(second.returncode,0);self.assertIn('Another process',second.stderr)
        stdout,stderr=first.communicate(timeout=15)
        self.assertEqual(first.returncode,0,stderr+stdout)
        self.assertEqual(len(self.mutations()),1)

    def test_stale_or_unsupported_result_blocks_remote_writes(self):
        self.prepare_result();original=json.loads(self.review_result.read_text());self.auto_review_result=False
        stale=json.loads(json.dumps(original));stale['target']['head_sha']='f'*40
        unresolved=json.loads(json.dumps(original));unresolved['findings'][0].update(status='unresolved',reason='Missing evidence')
        quote=json.loads(json.dumps(original));quote['findings'][0]['evidence'][0]['quote']='fabricated source'
        for report in (stale,unresolved,quote):
            self.review_result.write_text(json.dumps(report))
            self.assertNotEqual(self.invoke('save').returncode,0)
            self.assertEqual(self.mutations(),[])

    def test_save_without_review_result_cannot_mutate_remote(self):
        args=[sys.executable,str(SCRIPT),'save','--repo','example/project','--pr','7',
              '--snapshot',str(self.snapshot),'--payload',str(self.payload),'--receipt',str(self.receipt)]
        result=subprocess.run(args,env=self.env,text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0);self.assertEqual(self.mutations(),[])

    def test_partial_scope_can_save_supported_finding_without_claiming_complete(self):
        self.prepare_result();report=json.loads(self.review_result.read_text());self.auto_review_result=False
        report['files']=[row for row in report['files'] if row['path']=='app.py']
        self.review_result.write_text(json.dumps(report))
        record=self.save_ok()
        self.assertEqual(record['status'],'pending')
        self.assertEqual(record['review_completion']['status'],'partial')
        self.assertIn('missing_file',[g['code'] for g in record['review_completion']['gaps']])

    def test_comment_text_cannot_drift_from_supported_result(self):
        self.prepare_result();self.auto_review_result=False
        value=self.draft();value['comments'][0]['body']='An unrelated accusation';self.update_draft(value)
        self.assertNotEqual(self.invoke('save').returncode,0);self.assertEqual(self.mutations(),[])


if __name__=='__main__':unittest.main()
