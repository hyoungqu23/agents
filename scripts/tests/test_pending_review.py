"""Local Git + fake gh integration. No real GitHub writes or model calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'plugins/review/skills/review-pr/scripts/pending_review.py'
spec = importlib.util.spec_from_file_location('pending_review', SCRIPT)
pending = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pending)

GH_DOUBLE = r'''import json, os, sys
from pathlib import Path
p=Path(os.environ['PENDING_MOCK_STATE']);d=json.loads(p.read_text())
args=sys.argv[1:];method=args[args.index('--method')+1] if '--method' in args else 'GET'
endpoint=next(x.lstrip('/') for x in args if x.lstrip('/')=='user' or x.lstrip('/').startswith('repos/'))
payload=json.loads(sys.stdin.read()) if '--input' in args else None
with Path(os.environ['PENDING_MOCK_CALLS']).open('a') as f:f.write(json.dumps({'method':method,'endpoint':endpoint,'payload':payload})+'\n')
prefix='repos/example/project/pulls/7'
def review(state='PENDING'):
 return {'id':91,'state':state,'commit_id':d.get('created_head',d['head_sha']),
         'user':{'login':'reviewer'},'html_url':'https://github.com/example/project/pull/7#pullrequestreview-91'}
if method=='POST':
 if endpoint!=prefix+'/reviews':sys.exit(33)
 d['created_head']=payload.get('commit_id');d['created']=True;p.write_text(json.dumps(d))
 if d.get('dirty_on_post'):Path(d['worktree'],'app.py').write_text('changed during write\n')
 if d.get('lost_response'):sys.exit(1)
 print(json.dumps(review()));sys.exit(0)
if endpoint=='user':
 if d.get('dirty_on_user'):Path(d['worktree'],'app.py').write_text('changed during reads\n')
 result={'login':'reviewer'}
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
 else:result=[review()] if d.get('existing_pending') or d.get('created') or d.get('pending_page_two') else []
elif endpoint==prefix+'/reviews/91':
 result=review(d.get('readback_state','PENDING'))
 if d.get('submitted_at'):result['submitted_at']='2026-10-14T00:00:00Z'
 if d.get('wrong_review_commit'):result['commit_id']='e'*40
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
        self.payload.write_text(json.dumps({'body':'Reviewed draft','comments':[
            {'path':'app.py','line':2,'side':'RIGHT','body':'Empty rows raise IndexError; retain the guard.'}]}))
        self.assertEqual(self.invoke('capture','--worktree',str(self.worktree)).returncode,0)
        self.calls.write_text('')

    def g(self,*args):
        return subprocess.run(['git',*args],env=self.env,text=True,capture_output=True,check=True)

    def invoke(self,action,*extra):
        args=[sys.executable,str(SCRIPT),action,'--repo','example/project','--pr','7','--snapshot',str(self.snapshot)]
        if action=='save':args+=['--payload',str(self.payload),'--receipt',str(self.receipt)]
        return subprocess.run([*args,*extra],env=self.env,text=True,capture_output=True,timeout=20)

    def remote(self,**changes):
        d=json.loads(self.state.read_text());d.update(changes);self.state.write_text(json.dumps(d))

    def log(self):
        return [json.loads(x) for x in self.calls.read_text().splitlines() if x.strip()]

    def mutations(self):return [c for c in self.log() if c['method']!='GET']

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
                self.assertEqual(json.loads(self.receipt.read_text())['status'],'create_unconfirmed')

    def test_lost_response_is_not_replayed(self):
        self.remote(lost_response=True)
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertNotEqual(self.invoke('save').returncode,0)
        self.assertEqual(len(self.mutations()),1)
        self.assertEqual(json.loads(self.receipt.read_text())['status'],'create_unconfirmed')

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


if __name__=='__main__':unittest.main()
