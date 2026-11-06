"""Real filtered clones with a local upload-pack marker, never a live remote."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


gate=load('no_fetch_gate',ROOT/'plugins/review/skills/review-code/scripts/review_result.py')
pending=load('no_fetch_pending',ROOT/'plugins/review/skills/review-pr/scripts/pending_review.py')


class ReviewGitNoFetchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.source=self.root/'origin';self.source.mkdir();self.clone=self.root/'review'
        self.env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull}
        self.git(self.source,'init','-q','-b','main');self.git(self.source,'config','user.name','Fixture');self.git(self.source,'config','user.email','fixture@example.invalid')
        (self.source/'app.py').write_text('before = True\n');self.git(self.source,'add','.');self.git(self.source,'commit','-qm','before')
        self.base=self.git(self.source,'rev-parse','HEAD');self.blob=self.git(self.source,'rev-parse','HEAD:app.py')
        (self.source/'app.py').write_text('after = True\n');self.git(self.source,'commit','-qam','after');self.head=self.git(self.source,'rev-parse','HEAD')
        self.git(self.source,'config','uploadpack.allowFilter','true')
        subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','-q','--filter=blob:none',self.source.as_uri(),str(self.clone)],env=self.env,check=True,capture_output=True)
        self.git(self.clone,'checkout','--detach','-q')
        self.assertIn('?'+self.blob,self.git(self.clone,'rev-list','--objects','--missing=print',self.base,self.head))
        self.assertEqual(self.git(self.clone,'status','--porcelain'),'')
        self.marker=self.root/'uploadpack-ran';script=self.root/'uploadpack.py'
        script.write_text(f'from pathlib import Path\nPath({str(self.marker)!r}).write_text("executed")\nraise SystemExit(1)\n')
        self.git(self.clone,'config','remote.origin.uploadpack',f'{sys.executable} {script}')

    def git(self,root,*args):
        return subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-C',str(root),*args],env=self.env).decode().strip()

    def test_capture_and_pending_diff_reject_before_remote_command(self):
        for label,callback,error_type in (
            ('review-code',lambda:gate.capture_scope(self.clone,self.base,self.head),gate.ResultError),
            ('review-pr',lambda:pending.diff_for(self.clone,self.base,self.head),pending.ReviewError)):
            with self.subTest(caller=label):
                if self.marker.exists():self.marker.unlink()
                with self.assertRaises(error_type) as failure:callback()
                self.assertFalse(self.marker.exists(),'Read-only inspection executed a remote command')
                self.assertIn('Partial/promisor',str(failure.exception))

    def test_partial_guard_also_works_when_git_ignores_environment_control(self):
        real_run=subprocess.run
        def old_git(args,**kwargs):
            if isinstance(args,list) and args and args[0]=='git':
                env=dict(kwargs.get('env',os.environ));env.pop('GIT_NO_LAZY_FETCH',None);kwargs['env']=env
            return real_run(args,**kwargs)
        with patch.object(subprocess,'run',side_effect=old_git):
            with self.assertRaisesRegex(gate.ResultError,'Partial/promisor'):
                gate.capture_scope(self.clone,self.base,self.head)
        self.assertFalse(self.marker.exists())

    def test_both_readers_force_no_lazy_fetch_and_keep_return_contracts(self):
        real_run=subprocess.run;controls=[]
        def spy(args,**kwargs):
            if isinstance(args,list) and args and args[0]=='git':controls.append(kwargs.get('env',{}).get('GIT_NO_LAZY_FETCH'))
            return real_run(args,**kwargs)
        with patch.dict(os.environ,{'GIT_NO_LAZY_FETCH':'0'}),patch.object(subprocess,'run',side_effect=spy):
            self.assertEqual(gate.git(self.source,'rev-parse','HEAD').decode().strip(),self.head)
            result=pending.git(self.source,'rev-parse','HEAD')
            self.assertIsInstance(result.stdout,str);self.assertEqual(result.stdout.strip(),self.head)
            result=pending.git(self.source,'symbolic-ref','-q','refs/heads/missing',ok=(0,1))
            self.assertEqual(result.returncode,1)
        self.assertTrue(controls);self.assertTrue(all(v=='1' for v in controls))

    def test_false_promisor_setting_does_not_reject_ordinary_checkout(self):
        self.git(self.source,'config','remote.unused.promisor','false')
        self.assertEqual(gate.capture_scope(self.source,self.base,self.head)['target']['head_sha'],self.head)


if __name__=='__main__':unittest.main()
